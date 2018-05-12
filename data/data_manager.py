from multiprocessing.pool import ThreadPool

import numpy


class DataManager:

    def __init__(self, exchange_clients, exchange_pairs):
        self._exchange_clients = exchange_clients
        self._exchange_pairs = exchange_pairs

    def get_trades(self,
                   exchange,
                   pair,
                   start_unix,
                   end_unix):
        """Get trade data from specified exchange and currency pair.

        Args:
            exchange (str): Name of exchange.
            pair (str): Name of currency pair.
            start_unix (int): Start UNIX of trade data.
            end_unit (int): End UNIX of trade data.

        Returns:
            Trade data in the range `start_unix` to `end_unix` from the
            specified exchange and currency pair.
        """
        if exchange not in self._exchange_clients:
            raise ValueError('Exchange {} not found'.format(exchange))
        if pair not in self._exchange_pairs[exchange]:
            raise ValueError('Currency pair {} not found in exchange {}'.format(
                pair, exchange))

        # download relevant data
        client = self._exchange_clients[exchange]()
        client.download_data(pair=pair, start=start_unix, end=end_unix)

        # get trades from client
        client = self._exchange_clients[exchange]()
        return client.get_trades(pair, start_unix, end_unix)

    def get_charts(self,
                   exchange,
                   pair,
                   start_unix,
                   end_unix,
                   interval=60):
        """Get chart data from specified exchange and currency pair.

        keys: {
            'low', 'high', 'open', 'close',
            'volume', 'weighted_average',
            'sell_volume', 'sell_weighted_average',
            'buy_volume', 'buy_weighted_average',
            'n_sells', 'n_buys', 'n_trades'
        }

        Args:
            exchange (str): Name of exchange.
            pair (str): Name of currency pair.
            start_unix (int): Start UNIX of chart data.
            end_unit (int): End UNIX of chart data.

        Returns:
            Chart data in the range `start_unix` to `end_unix` from the
            specified exchange and currency pair.
        """
        if exchange not in self._exchange_clients:
            raise ValueError('Exchange {} not found'.format(exchange))
        if pair not in self._exchange_pairs[exchange]:
            raise ValueError('Currency pair {} not found in exchange {}'.format(
                pair, exchange))

        # download relevant data
        client = self._exchange_clients[exchange]()
        client.download_data(pair=pair, start=start_unix, end=end_unix)

        # get charts from client
        client = self._exchange_clients[exchange]()
        return client.get_charts(pair, start_unix, end_unix, interval)

    def download_all(self,
                     start_unix,
                     end_unix,
                     n_proc=None):
        """Concurrently download all data in dataset.

        Args:
            start_unix (int): Start UNIX of trade data to download.
            end_unit (int): End UNIX of trade data to download.
            n_proc (int, optional): Number of processors to use in thread pool.
        """
        # concurrent workers
        tp = ThreadPool(processes=n_proc)

        # define concurrent ops
        async_ops = []
        for ex_name in sorted(self._exchange_clients):
            for pair in self._exchange_pairs[ex_name]:
                client = self._exchange_clients[ex_name]()
                dl_op = getattr(client, 'download_data')
                async_ops.append(tp.apply_async(
                    func=dl_op,
                    kwds={'pair': pair,
                          'start': start_unix,
                          'end': end_unix}))

        # execute concurrent ops
        for async_op in async_ops:
            async_op.get()
        tp.close()
        tp.join()


class DataProcessor:

    def __init__(self):
        self._default_rule = {
            'low': ['z_score'],
            'high': ['z_score'],
            'open': ['z_score'],
            'close': ['z_score'],
            'volume': ['z_score'],
            'weighted_average': ['z_score'],
            'sell_volume': ['z_score'],
            'sell_weighted_average': ['z_score'],
            'buy_volume': ['z_score'],
            'buy_weighted_average': ['z_score'],
            'n_sells': ['z_score'],
            'n_buys': ['z_score'],
            'n_trades': ['z_score']
        }

    def process_chart(self, chart_data, rules=None):
        if rules is None:
            rules = self._default_rule

        labels_to_process = [label for label in rules]

        # collect columns to process
        data_to_process = {}
        for label in labels_to_process:
            col_data = []
            for row in chart_data:
                col_data.append(row[label])
            data_to_process[label] = col_data

        # process selected columns
        processed_data = {}
        for label in data_to_process:
            rule = rules[label]
            op = getattr(self, rule[0])
            x = data_to_process[label]
            if len(rule) > 1:
                args = rule[1:]
                y = op(x, *args)
            else:
                y = op(x)
            processed_data[label] = y

        return processed_data

    def truncate(self, x, factor, mean=None, std=None):
        x = numpy.reshape(x, [-1])
        if mean is None:
            mean = numpy.mean(x)
        if std is None:
            std = numpy.std(x)
        clip_min = mean - factor * std
        clip_max = mean + factor * std
        y = numpy.clip(x, clip_min, clip_max)
        return y, mean, std

    def z_score(self, x, mean=None, std=None):
        x = numpy.reshape(x, [-1])
        if mean is None:
            mean = numpy.mean(x)
        if std is None:
            std = numpy.std(x)
        y = (x - mean) / std
        return y, mean, std

    def log_ratio(self, x, scale):
        x = numpy.reshape(x, [-1])
        y = x[1:]  # t+1
        y_ = x[:-1]  # t
        y = numpy.log(y / y_) * scale
        return y

    def ma(self, x, window):
        vals = []
        for i in range(len(x)):
            start = i - window + 1
            end = i + 1
            if start < 0:
                vals.append(numpy.mean(x[:window]))
            else:
                vals.append(numpy.mean(x[start:end]))
        return numpy.array(vals)

    def ema(self, x, window):
        x = numpy.reshape(x, [-1])
        weights = numpy.exp(numpy.linspace(-1.0, 0.0, window))
        weights /= weights.sum()
        vals = []
        for i in range(len(x)):
            start = i - window + 1
            end = i + 1
            if start < 0:
                vals.append(x[i])
            else:
                vals.append(numpy.sum(x[start:end] * weights))
        return numpy.array(vals)

    def dema(self, x, window):
        ema = self.ema(x, window)
        dema = self.ema(ema, window)
        return 2 * ema - dema

    def tema(self, x, window):
        ema = self.ema(x, window)
        dema = self.ema(ema, window)
        tema = self.ema(dema, window)
        return 3 * ema - 3 * dema + tema

    def vol(self, x, window):
        vals = []
        for i in range(len(x)):
            start = i - window + 1
            end = i + 1
            if start < 0:
                a = x[:window]
                vals.append(numpy.std(a))
            else:
                a = x[start:end]
                vals.append(numpy.std(a))
        return numpy.array(vals)

    def rsi(self, x, window):
        x = numpy.reshape(x, [-1])
        delta = numpy.diff(x)
        d_up, d_down = delta[1:].copy(), delta[1:].copy()
        d_up[d_up < 0] = 0
        d_down[d_down > 0] = 0
        roll_rp = self.ma(d_up, window)
        roll_down = self.ma(d_down, window)
        return roll_rp / numpy.abs(roll_down)
