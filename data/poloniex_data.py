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
    __MAX_LIMIT = 50000  # API limit on maximum trades returned
    __MAX_RANGE = 100000  # must be less than 1 month

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
                    print('Poloniex| Retries : {}'.format(retries))
                    r = requests.get(self._base_url + path,
                                     params=payload,
                                     timeout=self._timeout)
                    retries += 1
            except Exception as e:
                print('Poloniex| {}'.format(e))
                time.sleep(10)
                continue
            break
        return r.json()

    def __get_slice(self, pair, start):
        """Makes a call to the API that fetches trade data.

        Example call:
            https://poloniex.com/public?command=returnTradeHistory&currencyPair=BTC_NXT&start=1410158341&end=1410499372

        Args:
            pair (str): Currency pair.
            start (int): UNIX of oldest trade data (inclusive).

        Returns:
            Trade data from time `start`, up to time `end`.
        """
        params = {'currencyPair': pair,
                  'start': start,
                  'end': start + self.__MAX_RANGE}
        # new -> old
        r = self.__get('/public?command=returnTradeHistory', params)

        if len(r) >= self.__MAX_LIMIT:
            oldest_date = r[-1]['date']
            oldest_date = util.iso_to_unix(oldest_date)
            r.extend(self.__get_slice(pair, start, oldest_date))
        return r

    def __find_last_trade_time(self, pair):
        """Find the latest time of trade for a given pair.

        Args:
            pair (str): Currency pair.

        Returns:
            UNIX of last trade for `pair`.
        """
        params = {'currencyPair': pair}
        # new -> old
        r = self.__get('/public?command=returnTradeHistory', params)
        return util.iso_to_unix(r[0]['date'])

    def download_data(self, pair, start, end):
        """Download trade data and store as .csv file.

        Args:
            pair (str): Currency pair.
            start (int): Start UNIX of trade data to download.
            end (int): End UNIX of trade data to download.
        """
        dataio = DataIO(savedir=self._savedir, fieldnames=self.FIELDNAMES)
        last_row = None
        if dataio.csv_check(pair):
            last_row = dataio.csv_get_last(pair)
            newest_t = int(last_row['time'])
        else:
            newest_t = start

        # break condition
        last_trade_time = self.__find_last_trade_time(pair)

        while newest_t < end:
            # new -> old
            r = self.__get_slice(pair, newest_t)

            # old -> new; remove duplicate data by trade ID
            new_r = []
            for row in reversed(r):
                if last_row is not None:
                    if int(last_row['tradeID']) >= row['tradeID']:
                        continue  # remove duplicates
                last_row = row
                row['time'] = util.iso_to_unix(row['date'])
                new_r.append(row)

            if newest_t > last_trade_time:
                break

            # save to file
            dataio.csv_append(pair, new_r)

            # prepare next iteration
            newest_t += self.__MAX_RANGE
            print('Poloniex| {} : {}'.format(util.unix_to_iso(newest_t), pair))

        print('Poloniex| Download complete : {}'.format(pair))

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
                'Poloniex| No trades downloaded: {}'.format(pair))

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
            start (int): Start UNIX of chart data to fetch.
            end (int): End UNIX of chart data to fetch.
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
