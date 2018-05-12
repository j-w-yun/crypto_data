import time

import requests

from dataio import DataIO
import numpy as np
import timeutil


class Gdax:

    FIELDNAMES = ['date',
                  'time',
                  'trade_id',
                  'size',
                  'price',
                  'side']
    __MAX_LIMIT = 100  # API limit on maximum trades returned

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
                # HTTP not OK or GDAX error
                while not r.ok or 'error' in r.json():
                    time.sleep(3 * retries)
                    print('GDAX\t| Retries : {}'.format(retries))
                    r = requests.get(self._base_url + path,
                                     params=payload,
                                     timeout=self._timeout)
                    retries += 1
            except Exception as e:
                print('GDAX\t| {}'.format(e))
                time.sleep(10)
                continue
            break
        return r.json()

    def __get_slice(self, pair, end_trade_id):
        """Makes a call to the API that fetches trade data.

        Example call:
            https://api.gdax.com/products/BTC-USD/trades?after=100&limit=100

        Args:
            pair (str): Currency pair.
            end_trade_id (int): The last trade ID in trade data (exclusive).

        Returns:
            Trade data up to `trade ID==(end_trade_id - 1)`, in the order of
            newer data to older data.
        """
        params = {'after': end_trade_id,  # exclusive
                  'limit': self.__MAX_LIMIT}
        # new -> old
        return self.__get('/products/{}/trades'.format(pair), params)

    def __find_last_trade_id(self, pair):
        """Find the latest trade for a given pair.

        Example call of trades returned for maximum valid trade ID: 
            https://api.gdax.com/products/BTC-USD/trades?after=2147483647&limit=100

        Args:
            pair (str): Currency pair.

        Returns:
            Trade ID of the last trade for `pair`.
        """
        MAX_VALID_TRADE_ID = 2147483647  # max int32 val
        return self.__get_slice(pair, MAX_VALID_TRADE_ID)[0]['trade_id']

    def __find_start_trade_id(self, pair, start_unix):
        """Find starting trade ID given start UNIX.

        Args:
            pair (str): Currency pair.
            start_unix (int): Start UNIX to map to a start trade ID (inclusive).

        Returns:
            Earliest trade ID after time `start_unix`.
        """
        # check if no pair trades exist before start_unix
        r = self.__get_slice(pair, 1 + self.__MAX_LIMIT)
        oldest_t = timeutil.iso_to_unix(r[-1]['time'])
        if oldest_t > start_unix:
            print('GDAX\t| No trades exist for {} before {}'.format(
                pair, start_unix))
            return 1

        # binary search start trade ID
        start, end = 1, self.__find_last_trade_id(pair)
        while start <= end:
            mid = (start + end) // 2
            r = self.__get_slice(pair, mid + 1)
            newest_t = timeutil.iso_to_unix(r[0]['time'])
            oldest_t = timeutil.iso_to_unix(r[-1]['time'])
            if start_unix < oldest_t:
                end = mid
            elif start_unix > newest_t:
                start = mid
            else:
                # find trade start ID in the returned list
                for row in r:
                    current_t = timeutil.iso_to_unix(row['time'])
                    if start_unix > current_t:
                        return row['trade_id'] + 1

    def download_data(self, pair, start, end):
        """Download trade data and store as .csv file.

        Args:
            pair (str): Currency pair.
            start (int): Start UNIX of trade data to download.
            end (int): End UNIX of trade data to download.
        """
        dataio = DataIO(savedir=self._savedir, fieldnames=self.FIELDNAMES)
        if dataio.csv_check(pair):
            last_row = dataio.csv_get_last(pair)
            newest_id = int(last_row['trade_id']) + 1
            newest_t = int(last_row['time'])
        else:
            newest_id = self.__find_start_trade_id(pair, start)
            newest_t = 0

        last_trade_id = self.__find_last_trade_id(pair)

        while newest_t < end:
            # new -> old
            r = self.__get_slice(pair, newest_id + self.__MAX_LIMIT)

            # break condition
            to_break = False

            # old -> new, add unix timestamp
            new_r = []
            for row in reversed(r):
                if row['trade_id'] > newest_id:
                    row['date'] = row['time']
                    row['time'] = timeutil.iso_to_unix(row['time'])
                    new_r.append(row)
                if row['trade_id'] == last_trade_id:
                    to_break = True

            # save to file
            dataio.csv_append(pair, new_r)

            # break condition
            if to_break:
                break

            # prepare next iteration
            newest_id = new_r[-1]['trade_id']
            newest_t = new_r[-1]['time']
            print('GDAX\t| {} : {}'.format(
                timeutil.unix_to_iso(newest_t), pair))

        print('GDAX\t| Download complete : {}'.format(pair))

    def get_trades(self, pair, start, end):
        """Get trade data from .csv file.

        Args:
            pair (str): Currency pair.
            start (int): Start UNIX of trade data to fetch.
            end (int): End UNIX of trade data to fetch.

        Returns:
            List of trade events, from old to new data.
        """
        dataio = DataIO(savedir=self._savedir, fieldnames=self.FIELDNAMES)
        if dataio.csv_check(pair):
            data = dataio.csv_get(pair)
        else:
            raise ValueError(
                'GDAX\t| No trades downloaded: {}'.format(pair))

        # filter by requested date range
        new_data = []
        for row in data:
            if float(row['time']) >= float(start) and float(row['time']) <= float(end):
                new_data.append(row)
        return new_data

    def get_charts(self, pair, start, end, interval=60):
        """Convert trade data to OHLC format.
        *Uses slightly inefficient code for easy transfer to other API

        Args:
            pair (str): Currency pair.
            start (int): Start UNIX of chart data to fetch.
            end (int): End UNIX of chart data to fetch.
            interval (int): Interval, in seconds.

        Returns:
            List of ticks, from old to new data.
        """
        # get trade data, from oldest to newest trades
        trade_data = self.get_trades(pair, start, end)

        # bucket trade data into intervals
        timepoints = np.arange(start + interval, end, interval)
        chart_data = []
        index = 0
        for t in timepoints:
            lower_t = t - interval + 1  # exclusive
            upper_t = t  # inclusive

            # collect relevant trades for the bucket
            bucket = []
            while (len(trade_data) > index and
                   float(trade_data[index]['time']) <= float(upper_t)):
                if float(trade_data[index]['time']) >= float(lower_t):
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
                         label_list['side']) if side == 'sell'],
                    dtype=np.float32)
                buy_sizes = np.asarray(
                    [size for size, side in
                     zip(label_list['size'],
                         label_list['side']) if side == 'buy'],
                    dtype=np.float32)
                sell_prices = np.asarray(
                    [price for price, side in
                     zip(label_list['price'],
                         label_list['side']) if side == 'sell'],
                    dtype=np.float32)
                buy_prices = np.asarray(
                    [price for price, side in
                     zip(label_list['price'],
                         label_list['side']) if side == 'buy'],
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
