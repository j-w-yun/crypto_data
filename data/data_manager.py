from multiprocessing.pool import ThreadPool


class DataManager:

    def __init__(self, exchange_clients, exchange_pairs):
        self._exchange_clients = exchange_clients
        self._exchange_pairs = exchange_pairs

    def get_trades(self, exchange, pair, start_unix, end_unix):
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

    def get_charts(self, exchange, pair, start_unix, end_unix, interval):
        """Get chart data from specified exchange and currency pair.

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

    def get_all_trades(self, start_unix, end_unix):
        # TODO: finish
        self.download_all(start_unix, end_unix)
        pass

    def get_all_charts(self, start_unix, end_unix):
        # TODO: finish
        self.download_all(start_unix, end_unix)
        pass
