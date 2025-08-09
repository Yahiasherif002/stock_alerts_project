from celery import shared_task
import logging
from apps.stocks.services import StockDataService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@shared_task
def fetch_all_stock_prices():
    """Fetch all stock prices from the database.
    """
    service = StockDataService()
    result = service.fetch_all_stock_prices()
    logger.info("Fetched all stock prices successfully.")
    return result

@shared_task
def fetch_stock_price_by_symbol(symbol):
    """Fetch stock price by symbol.
    
    Args:
        symbol (str): The stock symbol to fetch the price for.
    
    Returns:
        dict: Stock price data for the given symbol.
    """
    from .models import Stock
    
    try:
        stock = Stock.objects.get(symbol=symbol, is_active=True)
        service = StockDataService()
        success = service.update_stock_price(stock)
        
        return {
            'symbol': symbol,
            'success': success,
            'price': str(stock.current_price) if success else None
        }
    except Stock.DoesNotExist:
        logger.error(f"Stock {symbol} not found")
        return {'symbol': symbol, 'success': False, 'error': 'Stock not found'}
