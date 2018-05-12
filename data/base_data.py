from abc import ABCMeta, abstractmethod


class BaseExchange(object, metaclass=ABCMeta):
    """Abstract base class for all exchange clients that fetch historical
    trade data. All trade-data fetching clients should implement the following
    abstract methods:

        download_data(pair, start, end)
        get_trades(pair, start, end)
        get_charts(pair, start, end)
        get_pairs()

    where pair is a str representing a currency pair supported by the exchange
    and start and end are integer UNIX timestamps.
    """
    @abstractmethod
    def download_data(self, pair, start, end):
        pass

    @abstractmethod
    def get_trades(self, pair, start, end):
        pass

    @abstractmethod
    def get_charts(self, pair, start, end, interval):
        pass

    @abstractmethod
    def get_pairs(self):
        pass