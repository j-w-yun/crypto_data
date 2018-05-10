import time

import requests

from dataio import DataIO
import numpy as np
import util


class Kraken:

    FIELDNAMES = ['date',
                  'time',
                  'size',
                  'price',
                  'side',
                  'order_type']

    def __init__(self, savedir='exchange_data\\kraken', timeout=600):
        self._base_url = 'https://api.kraken.com/0'
        self._timeout = timeout
        self._savedir = savedir

    def __get(self, path, payload, max_retries=100):
        r = None
        for retries in range(1, max_retries + 1):
            try:
                r = requests.get(self._base_url + path,
                                 params=payload,
                                 timeout=self._timeout)
                # HTTP not OK or Kraken error
                while not r.ok or len(r.json()['error']) > 0:
                    time.sleep(3 * retries)
                    print('Kraken\t| Retries : {}'.format(retries))
                    r = requests.get(self._base_url + path,
                                     params=payload,
                                     timeout=self._timeout)
                    retries += 1
            except Exception as e:
                print('Kraken\t| {}'.format(e))
                time.sleep(10)
                continue
            break
        return r.json()

    def __to_dict(self, data):
        new_data = []
        for row in data:
            row_dict = {'date': util.unix_to_iso(row[2]),
                        'time': row[2],
                        'size': row[1],
                        'price': row[0],
                        'side': row[3],
                        'order_type': row[4]}
            new_data.append(row_dict)
        return new_data

    def _get_slice(self, pair, start, end):
        # old -> new
        params = {'pair': pair,
                  'since': int(start * 1000000000)}
        r = self.__get('/public/Trades', params)

        new_r = []
        new_r.extend(r['result'][pair])
        last = int(r['result']['last']) / 1000000000

        while last < end:
            params = {'pair': pair,
                      'since': int(last * 1000000000)}
            r = self.__get('/public/Trades', params)
            last_ = int(r['result']['last']) / 1000000000
            if last_ == last:
                print('Krak Trade {}\t| No future trades after {}'.format(
                    pair, last))
                return []
            last = last_
            new_r.extend(r['result'][pair])

        index = 0  # find last one to include
        for trade in new_r:
            timestamp = trade[2]
            if timestamp > end:
                break
            index += 1
        return new_r[:index]

    def download_data(self, **kwargs):
        pair = kwargs['pair']
        start = kwargs['start']
        end = kwargs['end']

        MAX_SLICE_RANGE = 2500000  # preference

        dataio = DataIO(savedir=self._savedir, fieldnames=self.FIELDNAMES)
        last_row = None
        if dataio.csv_check(pair):
            last_row = dataio.csv_get_last(pair)
            newest_t = float(last_row['time'])
        else:
            newest_t = start

        while newest_t < end:
            # old -> new
            r = self._get_slice(pair, newest_t, newest_t + MAX_SLICE_RANGE)
            if len(r) == 0:
                break
            r = self.__to_dict(r)

            # save to file
            dataio.csv_append(pair, r)
            print('Kraken\t| {} : {}'.format(
                util.unix_to_iso(r[-1]['time']), pair))
            newest_t = float(r[-1]['time'])

        print('Kraken\t| Download complete : {}'.format(pair))

    def get_trades(self, pair, start, end):
        dataio = DataIO(savedir=self._savedir, fieldnames=self.FIELDNAMES)
        if dataio.csv_check(pair):
            data = dataio.csv_get(pair)
        else:
            raise ValueError('Kraken\t| No trades downloaded: {}'.format(pair))

        # filter by requested date range
        new_data = []
        for row in data:
            if float(row['time']) >= start and float(row['time']) <= end:
                new_data.append(row)
        return new_data

    def get_charts(self, pair, start, end, interval=60):
        """Convert trade data to OHLC format.
        *Uses slightly inefficient code for easy transfer to other API

        Args:
            pair (str): Currency pair.
            start (int): UNIX start timestamp of chart data.
            end (int): UNIX end timestamp of chart data.
            interval (int): Interval, in seconds.

        Returns:
            List of ticks, from old to new data.
        """
        # get trade data, from oldest to newest trades
        trade_data = self.get_trades(pair, (start - interval), end)

        # bucket trade data into intervals
        timepoints = np.arange(start, end, interval)
        chart_data = []
        index = 0
        for t in timepoints:
            lower_t = t - interval + 1  # exclusive
            upper_t = t  # inclusive

            # collect relevant trades for the bucket
            bucket = []
            while (len(trade_data) > index and
                   (float(trade_data[index]['time']) // 1) >= lower_t and
                   (float(trade_data[index]['time']) // 1) <= upper_t):
                bucket.append(trade_data[index])
                index += 1

            tick = {}
            tick['time'] = upper_t

            if len(bucket) > 0:
                # process trades into tick
                label_list = {label: [] for label in self.FIELDNAMES}
                for trade in bucket:
                    for label in trade:
                        label_list[label].append(trade[label])

                # API specific code below
                # ['date', 'time', 'size', 'price', 'side', 'order_type']

                # standard OHLC, volume, weighted average
                prices = np.asarray(label_list['price'], dtype=np.float32)
                sizes = np.asarray(label_list['size'], dtype=np.float32)

                if len(chart_data) > 0:
                    tick['open'] = chart_data[-1]['close']
                else:
                    tick['open'] = prices[0]
                tick['high'] = np.max(prices)
                tick['low'] = np.min(prices)
                tick['close'] = prices[-1]
                tick['volume'] = np.sum(sizes)
                tick['weighted_average'] = (np.sum(prices * sizes) /
                                            tick['volume'])

                # feature extraction
                sell_sizes = np.asarray(
                    [size for size, side in
                     zip(label_list['size'],
                         label_list['side']) if side == 's'],
                    dtype=np.float32)
                buy_sizes = np.asarray(
                    [size for size, side in
                     zip(label_list['size'],
                         label_list['side']) if side == 'b'],
                    dtype=np.float32)
                sell_prices = np.asarray(
                    [price for price, side in
                     zip(label_list['price'],
                         label_list['side']) if side == 's'],
                    dtype=np.float32)
                buy_prices = np.asarray(
                    [price for price, side in
                     zip(label_list['price'],
                         label_list['side']) if side == 'b'],
                    dtype=np.float32)

                tick['n_sells'] = len(sell_sizes)
                if len(sell_sizes) > 0:
                    tick['sell_volume'] = np.sum(sell_sizes)
                    tick['sell_weighted_average'] = (np.sum(sell_prices * sell_sizes) /
                                                     tick['sell_volume'])
                else:
                    tick['sell_volume'] = 0
                    tick['sell_weighted_average'] = 0
                tick['n_buys'] = len(buy_sizes)
                if len(buy_sizes) > 0:
                    tick['buy_volume'] = np.sum(buy_sizes)
                    tick['buy_weighted_average'] = (np.sum(buy_prices * buy_sizes) /
                                                    tick['buy_volume'])
                else:
                    tick['buy_volume'] = 0
                    tick['buy_weighted_average'] = 0
                tick['n_trades'] = tick['n_sells'] + tick['n_buys']

                # collect tick data
                chart_data.append(tick)

            else:
                # carry forward relevant info if no trades within the interval
                if len(chart_data) > 0:
                    carry_forward_price = chart_data[-1]['close']
                else:
                    carry_forward_price = 0
                tick['low'] = carry_forward_price
                tick['high'] = carry_forward_price
                tick['open'] = carry_forward_price
                tick['close'] = carry_forward_price
                tick['volume'] = 0
                tick['weighted_average'] = carry_forward_price
                tick['sell_volume'] = 0
                tick['sell_weighted_average'] = 0
                tick['buy_volume'] = 0
                tick['buy_weighted_average'] = 0
                tick['n_sells'] = 0
                tick['n_buys'] = 0
                tick['n_trades'] = 0

                # collect tick data
                chart_data.append(tick)

        return chart_data
