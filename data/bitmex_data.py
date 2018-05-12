import time

import requests

import base_data
from dataio import DataIO
import numpy as np
import timeutil


class Bitmex(base_data.BaseExchange):

    # Fieldnames are used as header in saved CSV file. All headers should
    # have both date (ISO) and time (UNIX) fieldnames.
    FIELDNAMES = [
        'date',  # renamed from native 'timestamp'
        'time',  # engineered from ISO
        'size',  # native
        'price',  # native
        'side',  # native
        'tickDirection',  # native
        'grossValue',  # native
        'homeNotional',  # native
        'foreignNotional',  # native
        'trdMatchID',  # native
        'trade_id'  # engineered from pagination
    ]
    __MAX_LIMIT = 500  # API limit on maximum trades returned
    __BASE_URL = 'https://www.bitmex.com/api/v1'  # base API url

    def __init__(self, savedir='exchange_data\\bitmex', timeout=600):
        self._timeout = timeout
        self._savedir = savedir

    def __get(self, path, payload, max_retries=100):
        r = None
        for retries in range(1, max_retries + 1):
            try:
                r = requests.get(self.__BASE_URL + path,
                                 params=payload,
                                 timeout=self._timeout)
                # HTTP not OK or Bitmex error
                while not r.ok or 'error' in r.json():
                    time.sleep(10 * retries)
                    print('Bitmex\t| Retries : {}'.format(retries))
                    r = requests.get(self.__BASE_URL + path,
                                     params=payload,
                                     timeout=self._timeout)
                    retries += 1
            except Exception as e:
                print('Bitmex\t| {}'.format(e))
                time.sleep(10)
                continue
            break
        return r.json()

    def __get_slice(self, pair, start_trade_id):
        """Makes a call to the API that fetches trade data.

        Example call:
            https://www.bitmex.com/api/v1/trade?symbol=XBTUSD&count=500&start=0

        Args:
            pair (str): Currency pair.
            start_trade_id (int): The start ID of trade data (inclusive).

        Returns:
            Trade data starting from `start_trade_id` (inclusive) up to
            `start_trade_id+self.__MAX_LIMIT`, in the order of increasing UNIX.
        """
        params = {'symbol': pair,
                  'start': start_trade_id,  # inclusive
                  'count': self.__MAX_LIMIT}
        # old -> new
        return self.__get('/trade', params)

    def __find_start_trade_id(self, pair, start_unix):
        """Find starting trade ID given start UNIX.

        Args:
            pair (str): Currency pair.
            start_unix (int): Start UNIX to map to a start trade ID (inclusive).

        Returns:
            Earliest trade ID after time `start_unix`.
        """
        # check if no pair trades exist before start_unix
        r = self.__get_slice(pair, 0)
        oldest_t = timeutil.iso_to_unix(r[0]['timestamp'])
        if oldest_t > start_unix:
            print('Bitmex\t| No trades exist for {} before {}'.format(
                pair, start_unix))
            return 0

        # incrementally search start trade ID
        current_id = 0
        increment = 10000000

        while True:
            current_id += increment
            # old -> new
            r = self.__get_slice(pair, current_id)

            print(current_id)

            if len(r) == 0:
                current_id -= increment
                increment = increment // 2
                continue

            oldest_t = timeutil.iso_to_unix(r[0]['timestamp'])
            newest_t = timeutil.iso_to_unix(r[-1]['timestamp'])

            if start_unix > oldest_t and start_unix < newest_t:
                # answer is in this page
                for row in r:
                    if timeutil.iso_to_unix(row['timestamp']) >= start_unix:
                        return current_id
                    current_id += 1
            elif start_unix > newest_t:
                pass
            elif start_unix < oldest_t:
                current_id -= increment
                increment = increment // 2
            elif start_unix > oldest_t and len(r) < self.__MAX_LIMIT:
                # last page
                for row in r:
                    if timeutil.iso_to_unix(row['timestamp']) >= start_unix:
                        return current_id
                    current_id += 1
                return current_id  # starting at this id will return empty list

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

        while newest_t < end:
            # new -> old
            r = self.__get_slice(pair, newest_id)

            # old -> new, add unix timestamp
            new_r = []
            for i, row in enumerate(r):
                row['time'] = timeutil.iso_to_unix(row['timestamp'])
                row['date'] = row['timestamp']
                row['trade_id'] = newest_id + i
                row['side'] = row['side'].lower()
                row.pop('timestamp', None)
                row.pop('symbol', None)
                new_r.append(row)

            # save to file
            dataio.csv_append(pair, new_r)

            # break condition
            if len(r) < self.__MAX_LIMIT:
                break

            # prepare next iteration
            newest_id = new_r[-1]['trade_id'] + 1
            newest_t = new_r[-1]['time']
            print('Bitmex\t| {} : {}'.format(
                timeutil.unix_to_iso(newest_t), pair))

        print('Bitmex\t| Download complete : {}'.format(pair))

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
                'Bitmex\t| No trades downloaded: {}'.format(pair))

        # look for start and end row indices
        start_index = 0
        end_index = len(data['time']) - 1
        for i, timestamp in enumerate(data['time']):
            if float(timestamp) <= float(start):
                start_index = i
            if float(timestamp) <= float(end):
                end_index = i

        # filter by requested date range
        new_data = {}
        for col_name in data:
            new_data[col_name] = data[col_name][start_index: (end_index + 1)]
        return new_data

    def get_charts(self, pair, start, end, interval=60):
        """Convert trade data to OHLC format.

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
        chart_data = {
            'time': [],
            'open': [],
            'high': [],
            'low': [],
            'close': [],
            'volume': [],
            'weighted_average': [],
            'n_trades': [],
            'n_sells': [],
            'sell_volume': [],
            'sell_weighted_average': [],
            'n_buys': [],
            'buy_volume': [],
            'buy_weighted_average': [],
        }

        # bucket trade data into intervals
        timepoints = np.arange(start + interval, end, interval)
        index = 0
        for t in timepoints:
            lower_t = t - interval + 1  # exclusive
            upper_t = t  # inclusive

            # collect all trade data between lower_t and upper_t
            bucket = {label: [] for label in self.FIELDNAMES}
            while (index < len(trade_data['time']) and
                   float(trade_data['time'][index]) <= float(upper_t)):
                if float(trade_data['time'][index]) >= float(lower_t):
                    for label in trade_data:
                        bucket[label].append(trade_data[label][index])
                index += 1

            # process trades into tick
            tick = {}
            tick['time'] = upper_t

            if len(bucket['time']) > 0:
                # collect OHLC data from trades
                prices = np.asarray(bucket['price'], dtype=np.float32)
                sizes = np.asarray(bucket['size'], dtype=np.float32)

                # set current opening price to last closing price
                if len(chart_data['close']) > 0:
                    carry_forward_price = chart_data['close'][-1]
                else:
                    carry_forward_price = prices[0]

                # calculate chart OHLC
                tick['open'] = carry_forward_price
                tick['high'] = np.max(prices)
                tick['low'] = np.min(prices)
                tick['close'] = prices[-1]
                tick['volume'] = np.sum(sizes)
                tick['weighted_average'] = (np.sum(prices * sizes) /
                                            tick['volume'])

                # collect trade sell/buy volume and prices
                buy_sizes = np.asarray(
                    [size for size, side in
                     zip(bucket['size'],
                         bucket['side']) if side == 'buy' or side == 'b'],
                    dtype=np.float32)
                buy_prices = np.asarray(
                    [price for price, side in
                     zip(bucket['price'],
                         bucket['side']) if side == 'buy' or side == 'b'],
                    dtype=np.float32)
                sell_prices = np.asarray(
                    [price for price, side in
                     zip(bucket['price'],
                         bucket['side']) if side == 'sell' or side == 's'],
                    dtype=np.float32)
                sell_sizes = np.asarray(
                    [size for size, side in
                     zip(bucket['size'],
                         bucket['side']) if side == 'sell' or side == 's'],
                    dtype=np.float32)

                # calculate chart sell/buy volume and weighted average
                if len(buy_sizes) > 0:
                    tick['buy_volume'] = np.sum(buy_sizes)
                    tick['buy_weighted_average'] = (np.sum(buy_prices * buy_sizes) /
                                                    tick['buy_volume'])
                else:
                    tick['buy_volume'] = 0
                    tick['buy_weighted_average'] = carry_forward_price
                if len(sell_sizes) > 0:
                    tick['sell_volume'] = np.sum(sell_sizes)
                    tick['sell_weighted_average'] = (np.sum(sell_prices * sell_sizes) /
                                                     tick['sell_volume'])
                else:
                    tick['sell_volume'] = 0
                    tick['sell_weighted_average'] = carry_forward_price

                # total number of trades
                tick['n_buys'] = len(buy_sizes)
                tick['n_sells'] = len(sell_sizes)
                tick['n_trades'] = tick['n_sells'] + tick['n_buys']

            # carry forward relevant info if no trades within the interval
            else:
                if len(chart_data['close']) > 0:
                    carry_forward_price = chart_data['close'][-1]
                else:
                    carry_forward_price = 0

                tick['low'] = carry_forward_price
                tick['high'] = carry_forward_price
                tick['open'] = carry_forward_price
                tick['close'] = carry_forward_price
                tick['volume'] = 0
                tick['weighted_average'] = carry_forward_price
                tick['sell_volume'] = 0
                tick['sell_weighted_average'] = carry_forward_price
                tick['buy_volume'] = 0
                tick['buy_weighted_average'] = carry_forward_price
                tick['n_sells'] = 0
                tick['n_buys'] = 0
                tick['n_trades'] = 0

            # collect tick data
            for label in tick:
                chart_data[label].append(tick[label])

        return chart_data

    def get_pairs(self):
        """Returns all currency pairs supported by the exchange.

        Returns:
            A list of currency pair strings.
        """
        return ['XBTUSD', 'ADAM18', 'BCHM18', 'ETHM18', 'LTCM18', 'XRPM18']
