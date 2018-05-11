from matplotlib.finance import candlestick2_ohlc

from data_manager import DataManager
import datalist
import matplotlib.pyplot as plt
import util


if __name__ == '__main__':
    # DataManager instance will download and fetch trade and chart data
    dm = DataManager(exchange_clients=datalist.EXCHANGE_CLIENTS,
                     exchange_pairs=datalist.EXCHANGE_PAIRS)

    # start date of data
    date_dict = {'year': 2016, 'month': 8, 'day': 1, 'hour': 0, 'minute': 0}
    start_date = util.dict_to_utc_date(date_dict)
    start_unix = util.utc_date_to_unix(start_date)
    # end date of data
    date_dict = {'year': 2016, 'month': 8, 'day': 1, 'hour': 3, 'minute': 0}
    end_date = util.dict_to_utc_date(date_dict)
    end_unix = util.utc_date_to_unix(end_date)
    # show start and end unix of data to fetch
    print('Start UNIX: {}'.format(start_unix))
    print('End UNIX: {}\n'.format(end_unix))

    # download if not present on disk and fetch charts
    # both trade and chart data fetched through DataManager is a list of dict,
    # ordered from oldest data to newest data
    gdax_data = dm.get_charts('gdax', 'BTC-USD', start_unix, end_unix, 60)
    krak_data = dm.get_charts('kraken', 'XXBTZUSD', start_unix, end_unix, 60)
    polo_data = dm.get_charts('poloniex', 'USDT_BTC', start_unix, end_unix, 60)

    # plot chart data as OHLC
    data = {
        'GDAX': gdax_data,
        'Kraken': krak_data,
        'Poloniex': polo_data
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
                          opens=opens[5:],
                          highs=highs[5:],
                          lows=lows[5:],
                          closes=closes[5:],
                          width=0.6, colorup='green', colordown='red')
    fig.canvas.draw()
    plt.pause(1e9)
