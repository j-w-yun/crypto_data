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