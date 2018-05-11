# cdata


## Dependencies

    requests
    numpy
    matplotlib

## Usage

Data is stored in /exchange/{exchange_name}/{currency_pair_name}.csv separately for each currency pair.

Code for each exchange share three universal public methods:

	download_data(currency_pair_name, start_unix, end_unix)

which downloads trade data for currency_pair_name for specified UNIX timestamp range.
As long as `start_unix` is fixed, this method can resume download from the last saved trade.
To change `start_unix` to a point further back in time, you must delete all /exchange/{exchange_name}/{currency_pair_name}.csv files associated with your download scope.

	get_trades(currency_pair_name, start_unix, end_unix)

which fetches downloaded trade data as a list of python dict, in the order of increasing UNIX.

	get_charts(currency_pair_name, start_unix, end_unix, interval)

which fetches downloaded trade data and builds OHLC + additional information from trade data as a list of python dict, in the order of increasing UNIX.

---

These exchange clients and their methods are incorporated in DataManager class, which offers:

	get_trades(exchange_name, currency_pair_name, start_unix, end_unix)

which downloads and returns trade data as a list of python dicts, in the order of increasing UNIX.

	get_charts(exchange_name, currency_pair_name, start_unix, end_unix)

which downloads trade data and returns OHLC data as a list of python dicts, in the order of increasing UNIX.

	download_all(start_unix, end_unix)

which concurrently downloads all pairs from each exchange specified in datalist.EXCHANGE_PAIRS and datalist.EXCHANGE_CLIENTS.


## Tests

Following test files downloads BTC-USD pairs from three exchanges and plots OHLC:

	/test/test_data_manager.py

![alt tag](https://github.com/Jaewan-Yun/cdata/blob/master/figures/test_data_manager.png)

---

Following test files downloads ETH-USD pairs from each exchange and plots OHLC:

	/test/test_gdax_data.py

![alt tag](https://github.com/Jaewan-Yun/cdata/blob/master/figures/test_gdax_data.png)

	/test/test_kraken_data.py

![alt tag](https://github.com/Jaewan-Yun/cdata/blob/master/figures/test_kraken_data.png)

	/test/test_poloniex_data.py

![alt tag](https://github.com/Jaewan-Yun/cdata/blob/master/figures/test_poloniex_data.png)

