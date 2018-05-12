import time

from mpl_finance import candlestick2_ohlc

from binance_data import Binance
from bitmex_data import Bitmex
import datautil
from gdax_data import Gdax
from kraken_data import Kraken
import matplotlib.pyplot as plt
from poloniex_data import Poloniex
import timeutil


def plot(ax, r, plot_title, show_legend=False):
    # format OHLC data
    dates = [timeutil.unix_to_iso(unix) for unix in r['time']]
    opens = r['open']
    highs = r['high']
    lows = r['low']
    closes = r['close']
    volumes = r['volume']
    sell_volumes = r['sell_volume']
    sell_weighted_avgs = r['sell_weighted_average']
    buy_weighted_avgs = r['buy_weighted_average']

    n_clip = 40

    ax.grid()
    ax.set_title(plot_title)
    ax.set_xticks([x for x in range(len(dates) - n_clip)[::10]])
    ax.set_xticklabels(dates[n_clip::10])
    for tick in ax.get_xticklabels():
        tick.set_rotation(45)

    # plot chart OHLC
    candlestick2_ohlc(ax=ax,
                      opens=opens[n_clip:],
                      highs=highs[n_clip:],
                      lows=lows[n_clip:],
                      closes=closes[n_clip:],
                      width=0.6, colorup='green', colordown='red')

    # legend
    lines, labels = [], []

    # close
    l, = ax.plot(closes[n_clip:], color='black', linewidth=0.5)
    lines.append(l)
    labels.append('Close')

    # weighted averages
    l, = ax.plot(sell_weighted_avgs[n_clip:], color='pink', linewidth=1.5)
    lines.append(l)
    labels.append('Weighted Sell Average')
    l, = ax.plot(buy_weighted_avgs[n_clip:], color='cyan', linewidth=1.5)
    lines.append(l)
    labels.append('Weighted Buy Average')

    # volume
    ax_twin = ax.twinx()
    ax_twin.yaxis.set_visible(False)
    ind = [x for x in range(len(volumes) - n_clip)]
    ax_twin.bar(ind, volumes[n_clip:], alpha=0.2)
    ax_twin.bar(ind, sell_volumes[n_clip:], color='red', alpha=0.2)

    # SMA
    n = 20
    ma = datautil.ma(closes, n)
    l, = ax.plot(ma[n_clip:], color='blue', linewidth=1.5)
    lines.append(l)
    labels.append('SMA(n={})'.format(n))
    # BB
    n = 20
    k = 2
    vol_std = datautil.vol(closes, n)
    std_upper = ma + vol_std * k
    std_lower = ma - vol_std * k
    ax.plot(std_upper[n_clip:], color='blue', linewidth=0.5)
    l, = ax.plot(std_lower[n_clip:], color='blue', linewidth=0.5)
    lines.append(l)
    labels.append('BB(k={},n={})'.format(k, n))

    # EMA
    n = 20
    ema = datautil.ema(closes, n)
    l, = ax.plot(ema[n_clip:], color='red')
    lines.append(l)
    labels.append('EMA(n={})'.format(n))
    # EMA
    n = 30
    ema = datautil.ema(closes, n)
    l, = ax.plot(ema[n_clip:], color='red', dashes=[3, 2])
    lines.append(l)
    labels.append('EMA(n={})'.format(n))

    # DEMA
    n = 20
    dema = datautil.dema(closes, n)
    l, = ax.plot(dema[n_clip:], color='green')
    lines.append(l)
    labels.append('DEMA(n={})'.format(n))
    # DEMA
    n = 30
    dema = datautil.dema(closes, n)
    l, = ax.plot(dema[n_clip:], color='green', dashes=[3, 2])
    lines.append(l)
    labels.append('DEMA(n={})'.format(n))

    # TEMA
    n = 20
    tema = datautil.tema(closes, n)
    l, = ax.plot(tema[n_clip:], color='orange')
    lines.append(l)
    labels.append('TEMA(n={})'.format(n))
    # TEMA
    n = 30
    tema = datautil.tema(closes, n)
    l, = ax.plot(tema[n_clip:], color='orange', dashes=[3, 2])
    lines.append(l)
    labels.append('TEMA(n={})'.format(n))

    # RSI
    n = 30
    rsi = datautil.rsi(closes, n)
    ax_twin = ax.twinx()
    ax_twin.yaxis.set_visible(False)
    l, = ax_twin.plot(rsi[n_clip:], color='orange', alpha=0.5)
    lines.append(l)
    labels.append('RSI(n={})'.format(n))

    # draw legend
    if show_legend:
        ax.legend(lines, labels, loc=2)


if __name__ == '__main__':
    # figure settings
    fig, axarr = plt.subplots(5, 2, sharex=True, figsize=(14, 12))
    fig.subplots_adjust(hspace=0.1, wspace=0.05,
                        left=0.05, right=0.95,
                        top=0.95, bottom=0.15)
    axarr = axarr.flatten()

    end = int(time.time())
    end = end - (end % 60) + 60  # test boundary handling
    start = int(end - 60 * 60 * 3)

    axarr_i = 0

    # download data and get chart
    bina = Binance(savedir='test_directory')
    bina_pair = 'ETHUSDT'
    bina.download_data(bina_pair, start, end)
    bina_data = bina.get_charts(bina_pair, start, end, interval=60)
    plot(axarr[axarr_i], bina_data, 'Binance ' + bina_pair, True)
    axarr_i += 1

    bina = Binance(savedir='test_directory')
    bina_pair = 'BTCUSDT'
    bina.download_data(bina_pair, start, end)
    bina_data = bina.get_charts(bina_pair, start, end, interval=60)
    plot(axarr[axarr_i], bina_data, 'Binance ' + bina_pair)
    axarr_i += 1

    bitm = Bitmex(savedir='test_directory')
    bitm_pair = 'ETHM18'
    bitm.download_data(bitm_pair, start, end)
    bitm_data = bitm.get_charts(bitm_pair, start, end, interval=60)
    plot(axarr[axarr_i], bitm_data, 'Bitmex ' + bitm_pair)
    axarr_i += 1

    bitm = Bitmex(savedir='test_directory')
    bitm_pair = 'XBTUSD'
    bitm.download_data(bitm_pair, start, end)
    bitm_data = bitm.get_charts(bitm_pair, start, end, interval=60)
    plot(axarr[axarr_i], bitm_data, 'Bitmex ' + bitm_pair)
    axarr_i += 1

    gdax = Gdax(savedir='test_directory')
    gdax_pair = 'ETH-USD'
    gdax.download_data(gdax_pair, start, end)
    gdax_data = gdax.get_charts(gdax_pair, start, end, interval=60)
    plot(axarr[axarr_i], gdax_data, 'GDAX ' + gdax_pair)
    axarr_i += 1

    gdax = Gdax(savedir='test_directory')
    gdax_pair = 'BTC-USD'
    gdax.download_data(gdax_pair, start, end)
    gdax_data = gdax.get_charts(gdax_pair, start, end, interval=60)
    plot(axarr[axarr_i], gdax_data, 'GDAX ' + gdax_pair)
    axarr_i += 1

    krak = Kraken(savedir='test_directory')
    krak_pair = 'XETHZUSD'
    krak.download_data(krak_pair, start, end)
    krak_data = krak.get_charts(krak_pair, start, end, interval=60)
    plot(axarr[axarr_i], krak_data, 'Kraken ' + krak_pair)
    axarr_i += 1

    krak = Kraken(savedir='test_directory')
    krak_pair = 'XXBTZUSD'
    krak.download_data(krak_pair, start, end)
    krak_data = krak.get_charts(krak_pair, start, end, interval=60)
    plot(axarr[axarr_i], krak_data, 'Kraken ' + krak_pair)
    axarr_i += 1

    polo = Poloniex(savedir='test_directory')
    polo_pair = 'USDT_ETH'
    polo.download_data(polo_pair, start, end)
    polo_data = polo.get_charts(polo_pair, start, end, interval=60)
    plot(axarr[axarr_i], polo_data, 'Poloniex ' + polo_pair)
    axarr_i += 1

    polo = Poloniex(savedir='test_directory')
    polo_pair = 'USDT_BTC'
    polo.download_data(polo_pair, start, end)
    polo_data = polo.get_charts(polo_pair, start, end, interval=60)
    plot(axarr[axarr_i], polo_data, 'Poloniex ' + polo_pair)
    axarr_i += 1

    # draw fig
    fig.canvas.draw()
    plt.pause(1e9)
