from django.core.management.base import BaseCommand
from apps.alerts.services import AlertProcessor

class Command(BaseCommand):
    help = 'Process all active alerts'

    def handle(self, *args, **options):
        processor = AlertProcessor()
        results = processor.process_all_alerts()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Alert processing completed: '
                f'{results["triggered"]} triggered, '
                f'{results["errors"]} errors out of '
                f'{results["processed"]} processed'
            )
        )
