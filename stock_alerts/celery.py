import os
from celery import Celery

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_alerts.settings')

app = Celery('stock_alerts')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Discover tasks from all registered Django apps
app.autodiscover_tasks()

broker_connection_retry_on_startup = True


app.conf.beat_schedule = {
    # Fetch stock prices every 3 minutes
    'fetch-stock-prices': {
        'task': 'apps.stocks.tasks.fetch_all_stock_prices',
        'schedule': 180.0,  # 3 minutes
    },
    # Process alerts every 2 minutes
    'process-alerts': {
        'task': 'apps.alerts.tasks.process_all_alerts',
        'schedule': 120.0,  # 2 minutes
    },
    # Cleanup old triggered alerts daily at midnight
    'cleanup-old-alerts': {
        'task': 'apps.alerts.tasks.cleanup_old_triggered_alerts',
        'schedule': 86400.0,  # 24 hours
        'options': {'countdown': 0}  
    },
}

app.conf.timezone = 'UTC'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')