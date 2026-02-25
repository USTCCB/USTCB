from abc import ABC, abstractmethod

class StockFetcher(ABC):
    """Abstract base class for stock fetchers."""

    @abstractmethod
    def fetch_data(self, stock_symbol: str):
        """Fetch stock data for a given symbol.""" 
        pass

    @abstractmethod
    def get_data(self):
        """Get the fetched stock data.""" 
        pass

    @abstractmethod
    def get_source(self) -> str:
        """Get the source of the data."""
        pass
