from django.core.management.base import BaseCommand
from apps.notifications.services import NotificationService

class Command(BaseCommand):
    help = 'Send test email to verify email configuration'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email address to send test to')

    def handle(self, *args, **options):
        service = NotificationService()
        success = service.send_test_email(options['email'])
        
        if success:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Test email sent successfully to {options["email"]}')
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to send test email to {options["email"]}')
            )
