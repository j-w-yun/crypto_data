from multiprocessing.pool import ThreadPool

from binance_data import Binance
from bitmex_data import Bitmex
from gdax_data import Gdax
from kraken_data import Kraken
from poloniex_data import Poloniex


class DataManager:

    def __init__(self):
        self._all_clients = {
            'binance': Binance,
            'bitmex': Bitmex,
            'gdax': Gdax,
            'kraken': Kraken,
            'poloniex': Poloniex,
        }
        self._all_pairs = {
            exchange_name: self._all_clients[exchange_name]().get_pairs()
            for exchange_name in self._all_clients
        }

    @property
    def all_clients(self):
        return self._all_clients

    @property
    def all_pairs(self):
        return self._all_pairs

    def get_client(self, exchange_name):
        """Return an instance of exchange client.

        Args:
            exchange_name (str): Name of exchange.
        """
        return self.all_clients[exchange_name]()

    def get_pairs(self, exchange_name):
        """Return a list of currency pairs supported by an exchange.

        Args:
            exchange_name (str): Name of exchange.
        """
        return self.all_pairs[exchange_name]

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
        if exchange not in self._all_clients:
            raise ValueError('Exchange {} not found'.format(exchange))
        if pair not in self._all_pairs[exchange]:
            raise ValueError('Currency pair {} not found in exchange {}'.format(
                pair, exchange))

        # download relevant data
        client = self._all_clients[exchange]()
        client.download_data(pair=pair, start=start_unix, end=end_unix)

        # get trades from client
        client = self._all_clients[exchange]()
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
        if exchange not in self._all_clients:
            raise ValueError('Exchange {} not found'.format(exchange))
        if pair not in self._all_pairs[exchange]:
            raise ValueError('Currency pair {} not found in exchange {}'.format(
                pair, exchange))

        # download relevant data
        client = self._all_clients[exchange]()
        client.download_data(pair=pair, start=start_unix, end=end_unix)

        # get charts from client
        client = self._all_clients[exchange]()
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
        for ex_name in sorted(self._all_clients):
            for pair in self._all_pairs[ex_name]:
                client = self._all_clients[ex_name]()
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
