import time

from gdax_data import Gdax
from kraken_data import Kraken
import matplotlib.pyplot as plt
from poloniex_data import Poloniex
import test_gdax_data
import test_kraken_data
import test_poloniex_data


if __name__ == '__main__':
    # figure settings
    fig, axarr = plt.subplots(3, 2, sharex=True, figsize=(14, 10))
    fig.subplots_adjust(hspace=0, wspace=0,
                        left=0.05, right=0.95,
                        top=0.95, bottom=0.15)
    axarr = axarr.flatten()

    end = int(time.time())
    end = end - (end % 60) + 60  # test boundary handling
    start = int(end - 60 * 60 * 3)

    # download data and get chart
    gdax = Gdax(savedir='test')
    gdax_pair = 'ETH-USD'
    gdax.download_data(pair=gdax_pair, start=start, end=end)
    gdax_data = gdax.get_charts(
        pair=gdax_pair, start=start, end=end, interval=60)
    test_gdax_data.plot(axarr[0], gdax_data, gdax_pair, True)

    gdax = Gdax(savedir='test')
    gdax_pair = 'BTC-USD'
    gdax.download_data(pair=gdax_pair, start=start, end=end)
    gdax_data = gdax.get_charts(
        pair=gdax_pair, start=start, end=end, interval=60)
    test_gdax_data.plot(axarr[1], gdax_data, gdax_pair, False)

    krak = Kraken(savedir='test')
    krak_pair = 'XETHZUSD'
    krak.download_data(pair=krak_pair, start=start, end=end)
    krak_data = krak.get_charts(
        pair=krak_pair, start=start, end=end, interval=60)
    test_kraken_data.plot(axarr[2], krak_data, krak_pair, False)

    krak = Kraken(savedir='test')
    krak_pair = 'XXBTZUSD'
    krak.download_data(pair=krak_pair, start=start, end=end)
    krak_data = krak.get_charts(
        pair=krak_pair, start=start, end=end, interval=60)
    test_kraken_data.plot(axarr[3], krak_data, krak_pair, False)

    polo = Poloniex(savedir='test')
    polo_pair = 'USDT_ETH'
    polo.download_data(pair=polo_pair, start=start, end=end)
    polo_data = polo.get_charts(
        pair=polo_pair, start=start, end=end, interval=60)
    test_poloniex_data.plot(axarr[4], polo_data, polo_pair, False)

    polo = Poloniex(savedir='test')
    polo_pair = 'USDT_BTC'
    polo.download_data(pair=polo_pair, start=start, end=end)
    polo_data = polo.get_charts(
        pair=polo_pair, start=start, end=end, interval=60)
    test_poloniex_data.plot(axarr[5], polo_data, polo_pair, False)

    # draw fig
    fig.canvas.draw()
    plt.pause(1e9)
