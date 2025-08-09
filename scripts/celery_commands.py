import os
import sys
import django
from django.conf import settings

def setup_django():
    """Setup Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_alerts.settings')
    django.setup()

def start_celery_worker():
    """Start Celery worker"""
    setup_django()
    from celery import current_app
    current_app.worker_main(['worker', '--loglevel=info'])

def start_celery_beat():
    """Start Celery beat scheduler"""
    setup_django()
    from celery import current_app
    current_app.control.beat(['beat', '--loglevel=info'])

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'worker':
            start_celery_worker()
        elif sys.argv[1] == 'beat':
            start_celery_beat()
        else:
            print("Usage: python celery_commands.py [worker|beat]")
    else:
        print("Usage: python celery_commands.py [worker|beat]")