from django.db import models
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
class Stock(models.Model):
    """Enhanced Stock model with validation"""
    symbol = models.CharField(
        max_length=10, 
        unique=True, 
        help_text="Stock symbol (e.g., AAPL, GOOGL)"
    )
    name = models.CharField(
        max_length=200, 
        help_text="Full company name"
    )
    current_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Current stock price (must be positive)"
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        help_text="When the price was last updated"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this stock is actively being tracked"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['symbol']
        indexes = [
            models.Index(fields=['symbol']),
            models.Index(fields=['is_active']),
            models.Index(fields=['last_updated']),
        ]

    def clean(self):
        """Validate stock data"""
        super().clean()
        
        if self.current_price is not None and self.current_price <= 0:
            raise ValidationError({
                'current_price': 'Stock price must be positive.'
            })
        
        if self.symbol:
            self.symbol = self.symbol.upper().strip()
            if len(self.symbol) < 1:
                raise ValidationError({
                    'symbol': 'Stock symbol cannot be empty.'
                })

    def save(self, *args, **kwargs):
        """Override save to run validation"""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.symbol} - {self.name} (${self.current_price})"