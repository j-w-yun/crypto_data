from multiprocessing.pool import ThreadPool

from gdax_data import Gdax
from kraken_data import Kraken
from poloniex_data import Poloniex


EXCHANGE_CLIENTS = {
    'gdax': Gdax,
    'kraken': Kraken,
    'poloniex': Poloniex
}

# since Aug 2016
EXCHANGE_PAIRS = {
    'gdax': ['BTC-EUR', 'BTC-USD', 'ETH-BTC', 'ETH-USD', 'LTC-USD'],
    'kraken': ['XETCXETH', 'XETHXXBT', 'XETHZCAD', 'XETHZEUR', 'XETHZGBP',
               'XETHZJPY', 'XETHZUSD', 'XLTCXXBT', 'XLTCZEUR', 'XLTCZUSD',
               'XXBTZCAD', 'XXBTZEUR', 'XXBTZGBP', 'XXBTZJPY', 'XXBTZUSD',
               'XXRPXXBT'],
    'poloniex': ['BTC_ETH', 'BTC_XRP', 'ETH_ETC', 'ETH_LSK', 'ETH_STEEM',
                 'USDT_BTC', 'USDT_DASH', 'USDT_ETH', 'USDT_LTC', 'USDT_XMR',
                 'USDT_XRP']
}


class DataManager:

    def __init__(self, exchange_clients, exchange_pairs):
        self._exchange_clients = exchange_clients
        self._exchange_pairs = exchange_pairs

    def download(self,
                 start_unix,
                 end_unix,
                 n_proc=None):
        """Concurrently download data."""
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

        print('Download complete\n')

    def get_trades(self, exchange_str, pair_str, start_unix, end_unix):
        if exchange_str not in self._exchange_clients:
            raise ValueError('Exchange {} not found'.format(exchange_str))
        if pair_str not in self._exchange_pairs[exchange_str]:
            raise ValueError('Currency pair {} not found in exchange {}'.format(
                pair_str, exchange_str))

        # download data
        self.download(start_unix, end_unix)

        # get trades from client
        client = self._exchange_clients[exchange_str]()
        return client.get_trades(pair_str, start_unix, end_unix)

    def get_charts(self, exchange_str, pair_str, start_unix, end_unix, interval):
        if exchange_str not in self._exchange_clients:
            raise ValueError('Exchange {} not found'.format(exchange_str))
        if pair_str not in self._exchange_pairs[exchange_str]:
            raise ValueError('Currency pair {} not found in exchange {}'.format(
                pair_str, exchange_str))

        # download data
        self.download(start_unix, end_unix)

        # get charts from client
        client = self._exchange_clients[exchange_str]()
        return client.get_charts(pair_str, start_unix, end_unix, interval)
