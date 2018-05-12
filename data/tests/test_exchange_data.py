import time

from binance_data import Binance
from bitmex_data import Bitmex
from gdax_data import Gdax
from kraken_data import Kraken
import matplotlib.pyplot as plt
from poloniex_data import Poloniex
from test_plot import plot


def test_binance_data(pair, start, end, interval):
    client = Binance(savedir='test')
    client.download_data(pair=pair, start=(start - interval), end=end)
    trades = client.get_trades(pair, start, end)
    charts = client.get_charts(pair, start, end, interval=interval)
    return trades, charts, pair


def test_bitmex_data(pair, start, end, interval):
    client = Bitmex(savedir='test')
    client.download_data(pair=pair, start=(start - interval), end=end)
    trades = client.get_trades(pair, start, end)
    charts = client.get_charts(pair, start, end, interval=interval)
    return trades, charts, pair


def test_gdax_data(pair, start, end, interval):
    client = Gdax(savedir='test')
    client.download_data(pair=pair, start=(start - interval), end=end)
    trades = client.get_trades(pair, start, end)
    charts = client.get_charts(pair, start, end, interval=interval)
    return trades, charts, pair


def test_kraken_data(pair, start, end, interval):
    client = Kraken(savedir='test')
    client.download_data(pair=pair, start=(start - interval), end=end)
    trades = client.get_trades(pair, start, end)
    charts = client.get_charts(pair, start, end, interval=interval)
    return trades, charts, pair


def test_poloniex_data(pair, start, end, interval):
    client = Poloniex(savedir='test')
    client.download_data(pair=pair, start=(start - interval), end=end)
    trades = client.get_trades(pair, start, end)
    charts = client.get_charts(pair, start, end, interval=interval)
    return trades, charts, pair


if __name__ == '__main__':
    interval = 60

    end = int(time.time())
    end = end - (end % 60) + interval
    start = int(end - interval * 60 * 5)

#     start = 1451640280
#     end = start + 3000

    trd, cht, pair = test_binance_data('ETHBTC', start, end, interval)
#     trd, cht, pair = test_bitmex_data('XBTUSD', start, end, interval)
#     trd, cht, pair = test_gdax_data('ETH-USD', start, end, interval)
#     trd, cht, pair = test_kraken_data('XETHZUSD', start, end, interval)
#     trd, cht, pair = test_poloniex_data('USDT_ETH', start, end, interval)

    # print trade samples
    for i in range(0, 10):
        print([(label + ':' + str(trd[label][i])) for label in sorted(trd)])
    print('...')
    for i in range(len(trd['time']) - 10, len(trd['time'])):
        print([(label + ':' + str(trd[label][i])) for label in sorted(trd)])
    print('End Trade Data', end='\n\n')

    # print chart samples
    for i in range(0, 10):
        print([(label + ':' + str(cht[label][i])) for label in sorted(cht)])
    print('...')
    for i in range(len(cht['time']) - 10, len(cht['time'])):
        print([(label + ':' + str(cht[label][i])) for label in sorted(cht)])
    print('End Chart Data', end='\n\n')

    # figure settings
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    fig.subplots_adjust(hspace=0, wspace=0,
                        left=0.05, right=0.95,
                        top=0.95, bottom=0.15)

    plot(ax, cht, pair, True)

    # draw fig
    fig.canvas.draw()
    plt.pause(1e9)
