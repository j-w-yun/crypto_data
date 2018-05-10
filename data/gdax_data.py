import time

import requests

from dataio import DataIO
import numpy as np
import util


class Gdax:

    FIELDNAMES = ['date',
                  'time',
                  'trade_id',
                  'size',
                  'price',
                  'side']

    def __init__(self, savedir='exchange_data\\gdax', timeout=600):
        self._base_url = 'https://api.gdax.com'
        self._timeout = timeout
        self._savedir = savedir

    def __get(self, path, payload, max_retries=100):
        r = None
        for retries in range(1, max_retries + 1):
            try:
                r = requests.get(self._base_url + path,
                                 params=payload,
                                 timeout=self._timeout)
                # HTTP not OK or Gdax error
                while not r.ok or 'error' in r.json():
                    time.sleep(3 * retries)
                    print('Gdax\t| Retries : {}'.format(retries))
                    r = requests.get(self._base_url + path,
                                     params=payload,
                                     timeout=self._timeout)
                    retries += 1
            except Exception as e:
                print('Gdax\t| {}'.format(e))
                time.sleep(10)
                continue
            break
        return r.json()

    def _get_slice(self, pair, end_trade_id, limit=100):
        params = {'after': end_trade_id,  # exclusive
                  'limit': limit}
        # new -> old
        r = self.__get('/products/{}/trades'.format(pair), params)
        return r

    def download_data(self, **kwargs):
        pair = kwargs['pair']
        end = kwargs['end']

        MAX_RANGE = 100  # do not change

        dataio = DataIO(savedir=self._savedir, fieldnames=self.FIELDNAMES)
        if dataio.csv_check(pair):
            newest_id = int(dataio.csv_get_last(pair)['trade_id']) + 1
            newest_t = int(dataio.csv_get_last(pair)['time'])
        else:
            newest_id = 1
            newest_t = 0

        while newest_t < end:
            r = self._get_slice(pair, newest_id + MAX_RANGE, MAX_RANGE)
            if r[0]['trade_id'] != (newest_id + MAX_RANGE - 1):
                correct_r = []
                for row in r:
                    if row['trade_id'] > newest_id:
                        correct_r.append(row)
                if len(correct_r) == 0:
                    break
                else:
                    r = correct_r
            newest_id = r[0]['trade_id']
            newest_t = util.iso_to_unix(r[0]['time'])

            # old -> new, add unix timestamp
            new_r = []
            for row in reversed(r):
                row['date'] = row['time']
                row['time'] = util.iso_to_unix(row['time'])
                new_r.append(row)
            dataio.csv_append(pair, new_r)
            print('Gdax\t| {} : {}'.format(newest_id, pair))

    def get_trades(self, pair, start, end):
        """Download or fetch trade data from disk.

        Args:
            pair (str): Currency pair.
            start (int): UNIX start timestamp of trade data.
            end (int): UNIX end timestamp of trade data.

        Returns:
            List of trade events, from old to new data.
        """
        dataio = DataIO(savedir=self._savedir, fieldnames=self.FIELDNAMES)
        if dataio.csv_check(pair):
            data = dataio.csv_get(pair)
        else:
            raise ValueError(
                'Gdax\t| No trades downloaded: {}'.format(pair))

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
