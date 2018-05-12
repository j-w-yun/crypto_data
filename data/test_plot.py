import time

from mpl_finance import candlestick2_ohlc

from data_manager import DataProcessor
from gdax_data import Gdax
from kraken_data import Kraken
import matplotlib.pyplot as plt
from poloniex_data import Poloniex
import timeutil


def plot(ax, r, pair, show_legend):
    # format OHLC data
    times = []
    opens, highs, lows, closes = [], [], [], []
    sell_weighted_avgs, buy_weighted_avgs = [], []
    volumes, sell_volumes = [], []

    for row in r:
        times.append(timeutil.unix_to_iso(row['time']))
        opens.append(row['open'])
        highs.append(row['high'])
        lows.append(row['low'])
        closes.append(row['close'])
        if row['sell_weighted_average'] == 0 and len(sell_weighted_avgs) > 0:
            sell_weighted_avgs.append(sell_weighted_avgs[-1])
        else:
            sell_weighted_avgs.append(row['sell_weighted_average'])
        if row['buy_weighted_average'] == 0 and len(buy_weighted_avgs) > 0:
            buy_weighted_avgs.append(buy_weighted_avgs[-1])
        else:
            buy_weighted_avgs.append(row['buy_weighted_average'])
        volumes.append(row['volume'])
        sell_volumes.append(row['sell_volume'])

    n_clip = 40

    ax.grid()
    ax.set_title(pair)
    ax.set_xticks([x for x in range(len(times) - n_clip)[::10]])
    ax.set_xticklabels(times[n_clip::10])
    for tick in ax.get_xticklabels():
        tick.set_rotation(45)

    # plot chart OHLC
    candlestick2_ohlc(ax=ax,
                      opens=opens[n_clip:],
                      highs=highs[n_clip:],
                      lows=lows[n_clip:],
                      closes=closes[n_clip:],
                      width=0.6, colorup='green', colordown='red')

    dp = DataProcessor()

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
    ma = dp.process_chart(r, {'close': ['ma', n]})['close']
    l, = ax.plot(ma[n_clip:], color='blue', linewidth=1.5)
    lines.append(l)
    labels.append('SMA(n={})'.format(n))
    # BB
    n = 20
    k = 2
    vol_std = dp.process_chart(r, {'close': ['vol', n]})['close']
    std_upper = ma + vol_std * k
    std_lower = ma - vol_std * k
    ax.plot(std_upper[n_clip:], color='blue', linewidth=0.5)
    l, = ax.plot(std_lower[n_clip:], color='blue', linewidth=0.5)
    lines.append(l)
    labels.append('BB(k={},n={})'.format(k, n))

    # EMA
    n = 20
    ema = dp.process_chart(r, {'close': ['ema', n]})['close']
    l, = ax.plot(ema[n_clip:], color='red')
    lines.append(l)
    labels.append('EMA(n={})'.format(n))
    # EMA
    n = 30
    ema = dp.process_chart(r, {'close': ['ema', n]})['close']
    l, = ax.plot(ema[n_clip:], color='red', dashes=[3, 2])
    lines.append(l)
    labels.append('EMA(n={})'.format(n))

    # DEMA
    n = 20
    dema = dp.process_chart(r, {'close': ['dema', n]})['close']
    l, = ax.plot(dema[n_clip:], color='green')
    lines.append(l)
    labels.append('DEMA(n={})'.format(n))
    # DEMA
    n = 30
    dema = dp.process_chart(r, {'close': ['dema', n]})['close']
    l, = ax.plot(dema[n_clip:], color='green', dashes=[3, 2])
    lines.append(l)
    labels.append('DEMA(n={})'.format(n))

    # TEMA
    n = 20
    tema = dp.process_chart(r, {'close': ['tema', n]})['close']
    l, = ax.plot(tema[n_clip:], color='orange')
    lines.append(l)
    labels.append('TEMA(n={})'.format(n))
    # TEMA
    n = 30
    tema = dp.process_chart(r, {'close': ['tema', n]})['close']
    l, = ax.plot(tema[n_clip:], color='orange', dashes=[3, 2])
    lines.append(l)
    labels.append('TEMA(n={})'.format(n))

    # RSI
    n = 30
    rsi = dp.process_chart(r, {'close': ['rsi', n]})['close']
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
    plot(axarr[0], gdax_data, gdax_pair, True)

    gdax = Gdax(savedir='test')
    gdax_pair = 'BTC-USD'
    gdax.download_data(pair=gdax_pair, start=start, end=end)
    gdax_data = gdax.get_charts(
        pair=gdax_pair, start=start, end=end, interval=60)
    plot(axarr[1], gdax_data, gdax_pair, False)

    krak = Kraken(savedir='test')
    krak_pair = 'XETHZUSD'
    krak.download_data(pair=krak_pair, start=start, end=end)
    krak_data = krak.get_charts(
        pair=krak_pair, start=start, end=end, interval=60)
    plot(axarr[2], krak_data, krak_pair, False)

    krak = Kraken(savedir='test')
    krak_pair = 'XXBTZUSD'
    krak.download_data(pair=krak_pair, start=start, end=end)
    krak_data = krak.get_charts(
        pair=krak_pair, start=start, end=end, interval=60)
    plot(axarr[3], krak_data, krak_pair, False)

    polo = Poloniex(savedir='test')
    polo_pair = 'USDT_ETH'
    polo.download_data(pair=polo_pair, start=start, end=end)
    polo_data = polo.get_charts(
        pair=polo_pair, start=start, end=end, interval=60)
    plot(axarr[4], polo_data, polo_pair, False)

    polo = Poloniex(savedir='test')
    polo_pair = 'USDT_BTC'
    polo.download_data(pair=polo_pair, start=start, end=end)
    polo_data = polo.get_charts(
        pair=polo_pair, start=start, end=end, interval=60)
    plot(axarr[5], polo_data, polo_pair, False)

    # draw fig
    fig.canvas.draw()
    plt.pause(1e9)
