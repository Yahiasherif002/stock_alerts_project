from celery import shared_task
from apps.alerts.services import AlertProcessor
import logging

@shared_task
def process_all_alerts():
    """Process all alerts in the system."""
    processor = AlertProcessor()
    try:
        result = processor.process_all_alerts()
        logging.info("All alerts processed successfully.")
        return result
    except Exception as e:
        logging.error(f"Error processing alerts: {e}")
        
        
@shared_task
def cleanup_old_triggered_alerts(days=30):
    """Cleanup triggered alerts older than a specified number of days."""
    processor = AlertProcessor()
    try:
        result = processor.cleanup_old_triggered_alerts(days)
        logging.info(f"Old triggered alerts cleaned up successfully. {result} records deleted.")
        return result
    except Exception as e:
        logging.error(f"Error cleaning up old triggered alerts: {e}")
            

@shared_task
def send_test_notification(user_id, alert_id):
    """
    Celery task to send test notification
    """
    from django.contrib.auth.models import User
    from .models import Alert
    from apps.notifications.services import NotificationService
    
    try:
        user = User.objects.get(id=user_id)
        alert = Alert.objects.get(id=alert_id, user=user)
        
        notification_service = NotificationService()
        success = notification_service.send_test_email(user.email)
        
        return {'success': success, 'email': user.email}
    except (User.DoesNotExist, Alert.DoesNotExist) as e:
        logging.error(f"Test notification failed: {str(e)}")
        return {'success': False, 'error': str(e)}            