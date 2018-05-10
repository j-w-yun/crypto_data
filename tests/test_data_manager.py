from datetime import datetime
import data_manager as dm
import util

if __name__ == '__main__':
    # set start date of data
    date = {'year': 2016, 'month': 8, 'day': 1}
    start_date = datetime(date['year'], date['month'], date['day'])
    start = util.date_to_unix(start_date)
    # set end date of data
    date = {'year': 2016, 'month': 8, 'day': 2}
    end_date = datetime(date['year'], date['month'], date['day'])
    end = util.date_to_unix(end_date)

    print('Start UNIX: {}'.format(start))
    print('End UNIX: {}'.format(end))

    dm = dm.DataManager(exchange_clients=dm.EXCHANGE_CLIENTS,
                        exchange_pairs=dm.EXCHANGE_PAIRS)

    gdax_btc = dm.get_charts('gdax', 'BTC-USD', start, end, 60)
    kraken_btc = dm.get_charts('kraken', 'XXBTZUSD', start, end, 60)
    poloniex_btc = dm.get_charts('poloniex', 'USDT_BTC', start, end, 60)

    data = [gdax_btc, kraken_btc, poloniex_btc]

    # plot chart OHLC
    import matplotlib.pyplot as plt
    from matplotlib.finance import candlestick2_ohlc
    fig, axarr = plt.subplots(len(data), 1)
    axarr = axarr.flatten()
    for ax, datum in zip(axarr, data):
        opens, highs, lows, closes = [], [], [], []
        for row in datum:
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
