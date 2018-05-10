import time

import requests

from dataio import DataIO
import numpy as np
import util


class Poloniex:

    FIELDNAMES = ['date',
                  'time',
                  'globalTradeID',
                  'tradeID',
                  'total',
                  'rate',
                  'type',
                  'amount']

    def __init__(self, savedir='exchange_data\\poloniex', timeout=600):
        self._base_url = 'https://poloniex.com'
        self._timeout = timeout
        self._savedir = savedir

    def __get(self, path, payload, max_retries=100):
        r = None
        for retries in range(1, max_retries + 1):
            try:
                r = requests.get(self._base_url + path,
                                 params=payload,
                                 timeout=self._timeout)
                # HTTP not OK or Poloniex error
                while not r.ok or 'error' in r.json():
                    time.sleep(3 * retries)
                    print('Poloniex\t| Retries : {}'.format(retries))
                    r = requests.get(self._base_url + path,
                                     params=payload,
                                     timeout=self._timeout)
                    retries += 1
            except Exception as e:
                print('Poloniex\t| {}'.format(e))
                time.sleep(10)
                continue
            break
        return r.json()

    def _get_slice(self, pair, start, end):
        params = {'currencyPair': pair,
                  'start': start,  # inclusive
                  'end': end}
        # new -> old
        r = self.__get('/public?command=returnTradeHistory', params)
        if len(r) == 0:
            return []

        latest_date = r[0]['date']
        latest_date = util.iso_to_unix(latest_date)
        if len(r) >= 50000:
            oldest_date = r[-1]['date']
            oldest_date = util.iso_to_unix(oldest_date)
            r.extend(self._get_slice(pair, start, oldest_date))
        return r

    def download_data(self, **kwargs):
        pair = kwargs['pair']
        start = kwargs['start']
        end = kwargs['end']

        MAX_SLICE_RANGE = 2500000  # must be less than 1 month

        dataio = DataIO(savedir=self._savedir, fieldnames=self.FIELDNAMES)
        last_row = None
        if dataio.csv_check(pair):
            last_row = dataio.csv_get_last(pair)
            newest_t = int(last_row['time'])
        else:
            newest_t = start

        while newest_t < end:
            # new -> old
            r = self._get_slice(pair, newest_t, newest_t + MAX_SLICE_RANGE)
            if len(r) == 0:
                break

            # old -> new
            newest_t = r[0]['date']
            new_r = []
            for row in reversed(r):
                if last_row is not None:
                    if last_row['tradeID'] >= row['tradeID']:
                        continue  # remove duplicates
                last_row = row
                row['time'] = util.iso_to_unix(row['date'])
                new_r.append(row)
            # save to file
            dataio.csv_append(pair, new_r)
            print('Poloniex\t| {} : {}'.format(newest_t, pair))
            newest_t = util.iso_to_unix(newest_t)

        print('Poloniex\t| Download complete : {}'.format(pair))

    def get_trades(self, pair, start, end):
        dataio = DataIO(savedir=self._savedir, fieldnames=self.FIELDNAMES)
        if dataio.csv_check(pair):
            data = dataio.csv_get(pair)
        else:
            raise ValueError(
                'Poloniex\t| No trades downloaded: {}'.format(pair))

        # filter by requested date range
        new_data = []
        for row in data:
            if int(row['time']) >= start and int(row['time']) <= end:
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
                # ['date', 'time', 'globalTradeID', 'tradeID', 'total', 'rate', 'type', 'amount']

                # standard OHLC, volume, weighted average
                prices = np.asarray(label_list['rate'], dtype=np.float32)
                sizes = np.asarray(label_list['total'], dtype=np.float32)

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
                     zip(label_list['total'],
                         label_list['type']) if side == 'sell'],
                    dtype=np.float32)
                buy_sizes = np.asarray(
                    [size for size, side in
                     zip(label_list['total'],
                         label_list['type']) if side == 'buy'],
                    dtype=np.float32)
                sell_prices = np.asarray(
                    [price for price, side in
                     zip(label_list['rate'],
                         label_list['type']) if side == 'sell'],
                    dtype=np.float32)
                buy_prices = np.asarray(
                    [price for price, side in
                     zip(label_list['rate'],
                         label_list['type']) if side == 'buy'],
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
