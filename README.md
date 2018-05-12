# cdata


## Dependencies

    requests
    numpy
    matplotlib

## Usage

Data is stored in `/exchange/{exchange_name}/{currency_pair_name}.csv` separately for each currency pair.

Currently supports three exchanges:

GDAX exchange:
	
	from gdax_data import Gdax
	client = Gdax()

Kraken exchange:

	from kraken_data import Kraken
	client = Kraken()

Poloniex exchange:

	from poloniex_data import Poloniex
	client = Poloniex()

---

Code for each exchange share three universal public methods:

	client.download_data(currency_pair_name, start_unix, end_unix)

Downloads trade data for `currency_pair_name` for specified UNIX timestamp range.
As long as `start_unix` is fixed, this method can resume download from the last saved trade.
To change `start_unix` to a point further back in time, you must delete all `/exchange/{exchange_name}/{currency_pair_name}.csv` files associated with your download scope.

	client.get_trades(currency_pair_name, start_unix, end_unix)

Fetches downloaded trade data as a list of python dict, in the order of increasing UNIX.

	client.get_charts(currency_pair_name, start_unix, end_unix, interval)

Fetches downloaded trade data and builds OHLC + additional information from trade data as a list of python dict, in the order of increasing UNIX.

---

These exchange clients and their methods are incorporated in the `DataManager` class, which offers:

	get_trades(exchange_name, currency_pair_name, start_unix, end_unix)

Downloads and returns trade data as a list of python dicts, in the order of increasing UNIX.

	get_charts(exchange_name, currency_pair_name, start_unix, end_unix)

Downloads trade data and returns OHLC data as a list of python dicts, in the order of increasing UNIX.

	download_all(start_unix, end_unix)

Concurrently downloads all pairs from each exchange specified in `datalist.EXCHANGE_PAIRS` and `datalist.EXCHANGE_CLIENTS`.


## Tests

The following test file downloads most recent trades of BTC and ETH currencies paired with USD/USDT and plots OHLC:

	/tests/test_plot.py

![alt tag](https://github.com/Jaewan-Yun/cdata/blob/master/figures/test_plot.png)

---

Following test files downloads ETH-USD pairs from each exchange and plots OHLC:

	/tests/test_gdax_data.py

![alt tag](https://github.com/Jaewan-Yun/cdata/blob/master/figures/test_gdax_data.png)

	/tests/test_kraken_data.py

![alt tag](https://github.com/Jaewan-Yun/cdata/blob/master/figures/test_kraken_data.png)

	/tests/test_poloniex_data.py

![alt tag](https://github.com/Jaewan-Yun/cdata/blob/master/figures/test_poloniex_data.png)

