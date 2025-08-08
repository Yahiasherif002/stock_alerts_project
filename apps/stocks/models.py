from django.db import models
from decimal import Decimal

class Stock(models.Model):
    """
    Model to represent a stock that we're tracking
    """
    symbol = models.CharField(
        max_length=10, 
        unique=True,
        help_text="Stock ticker symbol (e.g., AAPL, GOOGL)"
    )
    name = models.CharField(
        max_length=100,
        help_text="Company name (e.g., Apple Inc.)"
    )
    current_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Current stock price in USD"
    )
    last_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Whether we're actively tracking this stock"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['symbol']

    def __str__(self):
        return f"{self.symbol} - ${self.current_price}"
