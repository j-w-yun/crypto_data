import time

from gdax_data import Gdax
import matplotlib.pyplot as plt
from test_plot import plot


if __name__ == '__main__':

    client = Gdax(savedir='test')
    pair = 'ETH-USD'

    end = int(time.time())
    end = end - (end % 60) + 60  # test boundary handling
    start = int(end - 60 * 60 * 5)

    # download data
    client.download_data(pair=pair, start=start, end=end)

    # print trade samples
    r = client.get_trades(pair, start, end)
    for row in r[:10]:
        print(row)
    print('...')
    for row in r[-10:]:
        print(row)
    print('Number of trade data: {}'.format(len(r)))
    print('End Trade Data', end='\n\n')

    # print chart samples
    r = client.get_charts(pair=pair, start=start, end=end, interval=60)
    for row in r[:10]:
        print(row)
    print('...')
    for row in r[-10:]:
        print(row)
    print('Number of chart ticks: {}'.format(len(r)))
    print('End Chart Data', end='\n\n')

    # figure settings
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    fig.subplots_adjust(hspace=0, wspace=0,
                        left=0.05, right=0.95,
                        top=0.95, bottom=0.15)

    plot(ax, r, pair, True)

    # draw fig
    fig.canvas.draw()
    plt.pause(1e9)
