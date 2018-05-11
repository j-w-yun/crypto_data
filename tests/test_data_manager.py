from matplotlib.finance import candlestick2_ohlc

from data_manager import DataManager
import datalist
import matplotlib.pyplot as plt
import util


if __name__ == '__main__':
    # DataManager instance will download and fetch trade and chart data
    dm = DataManager(datalist.EXCHANGE_CLIENTS, datalist.EXCHANGE_PAIRS)

    # start UNIX of data
    date_dict = {'year': 2018, 'month': 5, 'day': 1, 'hour': 0, 'minute': 0}
    start = util.local_date_to_unix(util.dict_to_local_date(date_dict))
    print('Start UNIX: {}'.format(start))

    # end UNIX of data
    date_dict = {'year': 2018, 'month': 5, 'day': 2, 'hour': 0, 'minute': 0}
    end = util.local_date_to_unix(util.dict_to_local_date(date_dict))
    print('End UNIX: {}\n'.format(end))

    # download if not present on disk and fetch charts
    # both trade and chart data fetched through DataManager is a list of dict,
    # ordered from oldest data to newest data
    gdax_btc_data = dm.get_charts('gdax', 'BTC-USD', start, end, 900)
    krak_btc_data = dm.get_charts('kraken', 'XXBTZUSD', start, end, 900)
    polo_btc_data = dm.get_charts('poloniex', 'USDT_BTC', start, end, 900)

    # plot chart data as OHLC
    data = {
        'GDAX': gdax_btc_data,
        'Kraken': krak_btc_data,
        'Poloniex': polo_btc_data
    }
    fig, axarr = plt.subplots(len(data), 1, figsize=(10, 8))
    axarr = axarr.flatten()
    for ax, datum_key in zip(axarr, data):
        ax.set_title(datum_key)
        opens, highs, lows, closes = [], [], [], []
        for row in data[datum_key]:
            opens.append(row['open'])
            highs.append(row['high'])
            lows.append(row['low'])
            closes.append(row['close'])
        candlestick2_ohlc(ax=ax,
                          opens=opens[2:],
                          highs=highs[2:],
                          lows=lows[2:],
                          closes=closes[2:],
                          width=0.6, colorup='green', colordown='red')
    fig.canvas.draw()
    plt.pause(1e9)
