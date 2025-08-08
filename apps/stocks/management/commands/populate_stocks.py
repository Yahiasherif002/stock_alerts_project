from django.core.management.base import BaseCommand
from apps.stocks.models import Stock

class Command(BaseCommand):
    help = 'Populate database with initial stock data'

    def handle(self, *args, **options):
        stocks_data = [
            {'symbol': 'AAPL', 'name': 'Apple Inc.'},
            {'symbol': 'GOOGL', 'name': 'Alphabet Inc.'},
            {'symbol': 'MSFT', 'name': 'Microsoft Corporation'},
            {'symbol': 'TSLA', 'name': 'Tesla Inc.'},
            {'symbol': 'AMZN', 'name': 'Amazon.com Inc.'},
            {'symbol': 'META', 'name': 'Meta Platforms Inc.'},
            {'symbol': 'NVDA', 'name': 'NVIDIA Corporation'},
            {'symbol': 'NFLX', 'name': 'Netflix Inc.'},
            {'symbol': 'AMD', 'name': 'Advanced Micro Devices Inc.'},
            {'symbol': 'UBER', 'name': 'Uber Technologies Inc.'},
        ]
        
        created_count = 0
        for stock_data in stocks_data:
            stock, created = Stock.objects.get_or_create(
                symbol=stock_data['symbol'],
                defaults={'name': stock_data['name']}
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created stock: {stock.symbol} - {stock.name}')
                )
            else:
                self.stdout.write(f'Stock {stock.symbol} already exists')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} new stocks')
        )