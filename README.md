# cdata


## Dependencies

    requests
    numpy
    matplotlib
    mpl_finance

## Usage

Data is stored in `/exchange/{exchange_name}/{currency_pair_name}.csv` separately for each currency pair.

Currently supports five exchanges:

Binance exchange:

	import binance_data
	client = binance_data.Binance()

Bitmex exchange:
	
	import bitmex_data
	client = bitmex_data.Bitmex()

GDAX exchange:
	
	import gdax_data
	client = gdax_data.Gdax()

Kraken exchange:

	import kraken_data
	client = kraken_data.Kraken()

Poloniex exchange:

	import poloniex_data
	client = poloniex_data.Poloniex()

---

Code for each exchange share four universal public methods:

	client.download_data(currency_pair_name, start_unix, end_unix)

Downloads trade data for `currency_pair_name` for specified UNIX timestamp range.
As long as `start_unix` is fixed, this method can resume download from the last saved trade.
To change `start_unix` to a point further back in time, you must delete all `/exchange/{exchange_name}/{currency_pair_name}.csv` files associated with your download scope.

	client.get_trades(currency_pair_name, start_unix, end_unix)

Fetches downloaded trade data as a list of python dict, in the order of increasing UNIX.

	client.get_charts(currency_pair_name, start_unix, end_unix, interval)

Fetches downloaded trade data and builds OHLC + additional information from trade data as a list of python dict, in the order of increasing UNIX.

	client.get_pairs()

Fetches all currency pairs currently supported by the exchange.

---

These exchange clients and their methods are incorporated in the `DataManager` class:

	import data_manager
	dm = data_manager.DataManager()

`DataManager` offers the following methods:

	dm.get_trades(exchange_name, currency_pair_name, start_unix, end_unix)

Downloads and returns trade data as a list of python dicts, in the order of increasing UNIX.

	dm.get_charts(exchange_name, currency_pair_name, start_unix, end_unix)

Downloads trade data and returns OHLC data as a list of python dicts, in the order of increasing UNIX.

	dm.download_all(start_unix, end_unix)

Concurrently downloads all pairs from each exchange.

	dm.all_clients()
	dm.all_pairs()

Fetches all suppoerted exchange client instances and list of currency pairs for each exchange, respectively.


## Tests

The following test file downloads most recent trades of BTC and ETH currencies paired with USD/USDT and plots OHLC:

	/tests/test_plot.py

![alt tag](https://github.com/Jaewan-Yun/cdata/blob/master/figures/test_plot.png)

---

The following test file downloads currency pairs from each exchange and plots OHLC:

	/tests/test_exchange_data.py

![alt tag](https://github.com/Jaewan-Yun/cdata/blob/master/figures/test_gdax_data.png)
![alt tag](https://github.com/Jaewan-Yun/cdata/blob/master/figures/test_kraken_data.png)
![alt tag](https://github.com/Jaewan-Yun/cdata/blob/master/figures/test_poloniex_data.png)

