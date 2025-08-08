# apps/stocks/services.py
import requests
import logging
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from typing import Dict, Optional
from .models import Stock

logger = logging.getLogger(__name__)

class StockDataService:
    """
    Service for fetching live stock prices from multiple APIs with failover
    """

    def __init__(self):
        self.session = requests.Session()
        self.api_priority = [
        "fetch_price_twelvedata",
        "fetch_price_fmp"
        ]

        self.twelve_data_key = settings.TWELVE_DATA_API_KEY 
        self.fmp_key = settings.FMP_API_KEY
        self.alpha_vantage_key = settings.ALPHA_VANTAGE_API_KEY

    # ------------------------------
    # Individual API fetch functions
    # ------------------------------

    def fetch_price_twelvedata(self, symbol: str) -> Optional[Dict]:
        """Fetch stock price from Twelve Data API"""
        try:
            url = "https://api.twelvedata.com/price"
            params = {"symbol": symbol, "apikey": self.twelve_data_key}
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "error":
                logger.error(f"TwelveData API error for {symbol}: {data.get('message')}")
                return None

            if "price" in data:
                return {
                    "symbol": symbol,
                    "price": Decimal(str(data["price"])),
                    "source": "TwelveData"
                }

        except Exception as e:
            logger.error(f"TwelveData request failed for {symbol}: {e}")
        return None


    def fetch_price_fmp(self, symbol: str) -> Optional[Dict]:
        """Fetch stock price from Financial Modeling Prep"""
        try:
            url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}"
            params = {"apikey": self.fmp_key}
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data and isinstance(data, list) and len(data) > 0:
                stock_data = data[0]
                if "price" in stock_data:
                    return {
                        "symbol": symbol,
                        "price": Decimal(str(stock_data["price"])),
                        "source": "FMP"
                    }

        except Exception as e:
            logger.error(f"FMP request failed for {symbol}: {e}")
        return None


    # ------------------------------
    # Failover logic
    # ------------------------------

    def _update_api_priority(self, func_name: str):
        """Move successful API to the top of the priority list"""
        if func_name in self.api_priority:
            self.api_priority.remove(func_name)
        self.api_priority.insert(0, func_name)


    def fetch_stock_price(self, symbol: str) -> Optional[Dict]:
        """
        Try APIs in priority order until one succeeds.
        On success, move that API to the front for next time.
        """
        for api_name in list(self.api_priority):
            api_func = getattr(self, api_name)
            try:
                result = api_func(symbol)
                if result:
                    self._update_api_priority(api_name)
                    logger.info(f"Fetched {symbol} from {result['source']} at ${result['price']}")
                    return result
            except Exception as e:
                logger.error(f"{api_name} failed for {symbol}: {e}")
        logger.error(f"All APIs failed for symbol: {symbol}")
        return None

    # ------------------------------
    # Stock update methods
    # ------------------------------

    def update_stock_price(self, stock: Stock) -> bool:
        """Update a single stock's price in the database"""
        try:
            price_data = self.fetch_stock_price(stock.symbol)
            if price_data:
                stock.current_price = price_data["price"]
                stock.last_updated = timezone.now()
                stock.save()
                logger.info(f"Updated {stock.symbol} price to ${stock.current_price}")
                return True
            else:
                logger.warning(f"Failed to fetch price for {stock.symbol}")
                return False
        except Exception as e:
            logger.error(f"Error updating {stock.symbol}: {e}")
            return False

    def update_all_active_stocks(self) -> Dict[str, int]:
        """
        Update prices for all active stocks with failover.
        Returns a summary of results.
        """
        results = {"updated": 0, "failed": 0, "total": 0}
        active_stocks = Stock.objects.filter(is_active=True)
        results["total"] = active_stocks.count()

        logger.info(f"Starting price update for {results['total']} stocks...")

        for stock in active_stocks:
            if self.update_stock_price(stock):
                results["updated"] += 1
            else:
                results["failed"] += 1

        logger.info(f"Price update completed: {results['updated']} updated, {results['failed']} failed")
        return results

    def get_current_prices(self) -> Dict[str, Decimal]:
        """Get current prices for all active stocks"""
        stocks = Stock.objects.filter(is_active=True)
        return {stock.symbol: stock.current_price for stock in stocks}
