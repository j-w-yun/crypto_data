import time

import requests

from dataio import DataIO
import numpy as np
import timeutil


class Kraken:

    FIELDNAMES = ['date',
                  'time',
                  'size',
                  'price',
                  'side',
                  'order_type']
    __MAX_LIMIT = 1000  # API limit on maximum trades returned

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

    def __get_slice(self, pair, since):
        """Makes a call to the API that fetches trade data.

        Example call:
            https://api.kraken.com/0/public/Trades?pair=XXBTZUSD&since=1526008794000000000

        Args:
            pair (str): Currency pair.
            since (int): UNIX of oldest trade data (inclusive).

        Returns:
            Trade data since time `since`, up to maximum trade list size
            `self.__MAX_LIMIT==1000`, in the order of older data to newer data.
        """
        params = {'pair': pair,
                  'since': int(since * 1e9)}
        # old -> new
        return self.__get('/public/Trades', params)['result'][pair]

    def __to_dict(self, data):
        """Convert API trade data response into a list of dict.

        Args:
            data (list of list): API trade data response.

        Returns:
            A properly formatted list of dict.
        """
        new_data = []
        for row in data:
            row_dict = {'date': timeutil.unix_to_iso(row[2]),
                        'time': row[2],
                        'size': row[1],
                        'price': row[0],
                        'side': row[3],
                        'order_type': row[4]}
            new_data.append(row_dict)
        return new_data

    def __find_start_trade_time(self, pair, start_unix):
        """Find a valid start UNIX, given arbitrary start UNIX.

        Args:
            pair (str): Currency pair.
            start (int): Start UNIX of trade data check if valid.

        Returns:
            A valid start UNIX, either `start_unix` or UNIX of first trade
            ever made for `pair`.

        """
        # check if no pair trades exist before start_unix
        r = self.__get_slice(pair, 0)
        oldest_t = r[-1][2]
        if oldest_t > start_unix:
            print('Kraken\t| No trades exist for {} before {}'.format(
                pair, start_unix))
            return oldest_t
        return start_unix

    def download_data(self, pair, start, end):
        """Download trade data and store as .csv file.

        Args:
            pair (str): Currency pair.
            start (int): Start UNIX of trade data to download.
            end (int): End UNIX of trade data to download.
        """
        dataio = DataIO(savedir=self._savedir, fieldnames=self.FIELDNAMES)
        if dataio.csv_check(pair):
            newest_t = float(dataio.csv_get_last(pair)['time'])
        else:
            newest_t = self.__find_start_trade_time(pair, start)

        while newest_t < end:
            # old -> new
            r = self.__get_slice(pair, newest_t + 1e-4)

            # list to dict
            r = self.__to_dict(r)

            # save to file
            dataio.csv_append(pair, r)

            # break condition
            if len(r) < self.__MAX_LIMIT:
                break

            # prepare next iteration
            newest_t = float(r[-1]['time'])
            print('Kraken\t| {} : {}'.format(
                timeutil.unix_to_iso(newest_t), pair))

        print('Kraken\t| Download complete : {}'.format(pair))

    def get_trades(self, pair, start, end):
        """Download or fetch trade data from disk.

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
                'Kraken\t| No trades downloaded: {}'.format(pair))

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
