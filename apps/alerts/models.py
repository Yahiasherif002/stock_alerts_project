from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from django.utils import timezone

class Alert(models.Model):
    """
    Model for user-created stock price alerts
    """
    ALERT_TYPES = [
        ('THRESHOLD', 'Threshold Alert'),  # Simple price threshold
        ('DURATION', 'Duration Alert'),    # Price condition for X minutes
    ]
    
    CONDITIONS = [
        ('>', 'Greater than'),
        ('<', 'Less than'),
        ('>=', 'Greater than or equal to'),
        ('<=', 'Less than or equal to'),
    ]
    
    # Basic alert info
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stock = models.ForeignKey('stocks.Stock', on_delete=models.CASCADE)
    
    # Alert configuration
    alert_type = models.CharField(max_length=10, choices=ALERT_TYPES)
    condition = models.CharField(max_length=2, choices=CONDITIONS)
    threshold_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # For duration alerts only
    duration_minutes = models.IntegerField(
        null=True, 
        blank=True,
        help_text="How long condition must be met (duration alerts only)"
    )
    
    # Status tracking
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Internal tracking for duration alerts
    condition_met_since = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        duration_text = f" for {self.duration_minutes} min" if self.duration_minutes else ""
        return f"{self.user.username}: {self.stock.symbol} {self.condition} ${self.threshold_price}{duration_text}"
    
    def check_condition(self, current_price):
        """
        Check if alert condition is met
        Returns True if condition is satisfied
        """
        if self.condition == '>':
            return current_price > self.threshold_price
        elif self.condition == '<':
            return current_price < self.threshold_price
        elif self.condition == '>=':
            return current_price >= self.threshold_price
        elif self.condition == '<=':
            return current_price <= self.threshold_price
        return False
    
    def should_trigger(self, current_price):
        """
        Determine if alert should be triggered based on type and duration
        """
        condition_met = self.check_condition(current_price)
        
        if self.alert_type == 'THRESHOLD':
            # Simple threshold - trigger immediately if condition is met
            return condition_met
        
        elif self.alert_type == 'DURATION':
            if condition_met:
                # Start tracking when condition was first met
                if not self.condition_met_since:
                    self.condition_met_since = timezone.now()
                    self.save()
                    return False  # Don't trigger yet
                
                # Check if enough time has passed
                time_elapsed = (timezone.now() - self.condition_met_since).total_seconds() / 60
                return time_elapsed >= self.duration_minutes
            else:
                # Condition not met - reset tracking
                if self.condition_met_since:
                    self.condition_met_since = None 
                    self.save()
                return False
        
        return False


class TriggeredAlert(models.Model):
    """
    Record of alerts that have been triggered
    """
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE)
    triggered_at = models.DateTimeField(auto_now_add=True)
    stock_price = models.DecimalField(max_digits=10, decimal_places=2)
    notification_sent = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-triggered_at']

    def __str__(self):
        return f"Alert triggered: {self.alert.stock.symbol} at ${self.stock_price}"