from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.alerts.models import Alert
from apps.stocks.models import Stock

class Command(BaseCommand):
    help = 'Create sample alerts for testing'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to create alerts for')

    def handle(self, *args, **options):
        try:
            user = User.objects.get(username=options['username'])
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User {options["username"]} not found')
            )
            return

        # Sample alerts data
        sample_alerts = [
            {
                'stock_symbol': 'AAPL',
                'alert_type': 'THRESHOLD',
                'condition': '>',
                'threshold_price': '200.00'
            },
            {
                'stock_symbol': 'TSLA', 
                'alert_type': 'THRESHOLD',
                'condition': '<',
                'threshold_price': '150.00'
            },
            {
                'stock_symbol': 'GOOGL',
                'alert_type': 'DURATION',
                'condition': '>',
                'threshold_price': '180.00',
                'duration_minutes': 30
            }
        ]

        created_count = 0
        for alert_data in sample_alerts:
            try:
                stock = Stock.objects.get(symbol=alert_data['stock_symbol'])
                
                alert, created = Alert.objects.get_or_create(
                    user=user,
                    stock=stock,
                    alert_type=alert_data['alert_type'],
                    condition=alert_data['condition'],
                    threshold_price=alert_data['threshold_price'],
                    defaults={
                        'duration_minutes': alert_data.get('duration_minutes')
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Created alert: {alert}')
                    )
                else:
                    self.stdout.write(f'Alert already exists: {alert}')
                    
            except Stock.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'Stock {alert_data["stock_symbol"]} not found')
                )

        self.stdout.write(
            self.style.SUCCESS(f'✅ Created {created_count} new sample alerts')
        )
