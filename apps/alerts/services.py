# apps/alerts/services.py
import logging
from django.utils import timezone
from django.db.models import Q
from typing import List, Dict
from .models import Alert, TriggeredAlert
from apps.stocks.models import Stock
from apps.notifications.services import NotificationService

logger = logging.getLogger(__name__)

class AlertProcessor:
    """
    Service for processing and triggering stock alerts
    """
    
    def __init__(self):
        self.notification_service = NotificationService()

    def process_all_alerts(self) -> Dict[str, int]:
        """
        Process all active alerts and trigger notifications
        Returns summary of processing results
        """
        results = {
            'processed': 0,
            'triggered': 0,
            'errors': 0
        }
        
        # Get all active alerts
        active_alerts = Alert.objects.filter(is_active=True).select_related('user', 'stock')
        results['processed'] = active_alerts.count()
        
        logger.info(f"Processing {results['processed']} active alerts")
        
        for alert in active_alerts:
            try:
                if self.process_alert(alert):
                    results['triggered'] += 1
            except Exception as e:
                results['errors'] += 1
                logger.error(f"Error processing alert {alert.id}: {str(e)}")
        
        logger.info(f"Alert processing complete: {results['triggered']} triggered, {results['errors']} errors")
        return results

    def process_alert(self, alert: Alert) -> bool:
        """
        Process a single alert and trigger if conditions are met
        Returns True if alert was triggered
        """
        try:
            current_price = alert.stock.current_price
            
            # Check if alert should trigger
            if alert.should_trigger(current_price):
                return self.trigger_alert(alert, current_price)
            
            return False
            
        except Exception as e:
            logger.error(f"Error processing alert {alert.id}: {str(e)}")
            return False

    def trigger_alert(self, alert: Alert, current_price) -> bool:
        """
        Trigger an alert and send notification
        """
        try:
            triggered_alert = TriggeredAlert.objects.create(
                alert=alert,
                stock_price=current_price,
                notification_sent=False
            )
            
            # Send notification
            success = self.notification_service.send_alert_notification(
                alert, current_price, triggered_alert
            )
            
            # Update notification status
            triggered_alert.notification_sent = success
            triggered_alert.save()
            
            # For threshold alerts, deactivate after triggering
            if alert.alert_type == 'THRESHOLD':
                alert.is_active = False
                alert.save()
                logger.info(f"Deactivated threshold alert {alert.id} after triggering")
            
            # For duration alerts, reset the condition tracking
            elif alert.alert_type == 'DURATION':
                alert.condition_met_since = None
                alert.save()
                logger.info(f"Reset duration tracking for alert {alert.id}")
            
            logger.info(f"Alert {alert.id} triggered successfully for {alert.stock.symbol} at ${current_price}")
            return True
            
        except Exception as e:
            logger.error(f"Error triggering alert {alert.id}: {str(e)}")
            return False

    def check_threshold_alerts(self) -> List[Alert]:
        """
        Get all threshold alerts that should be triggered
        """
        triggered_alerts = []
        
        threshold_alerts = Alert.objects.filter(
            is_active=True,
            alert_type='THRESHOLD'
        ).select_related('stock')
        
        for alert in threshold_alerts:
            if alert.check_condition(alert.stock.current_price):
                triggered_alerts.append(alert)
        
        return triggered_alerts

    def check_duration_alerts(self) -> List[Alert]:
        """
        Get all duration alerts that should be triggered
        """
        triggered_alerts = []
        now = timezone.now()
        
        duration_alerts = Alert.objects.filter(
            is_active=True,
            alert_type='DURATION',
            condition_met_since__isnull=False
        ).select_related('stock')
        
        for alert in duration_alerts:
            # Check if condition is still met
            if alert.check_condition(alert.stock.current_price):
                # Check if enough time has passed
                time_elapsed = (now - alert.condition_met_since).total_seconds() / 60
                if time_elapsed >= alert.duration_minutes:
                    triggered_alerts.append(alert)
            else:
                # Condition no longer met, reset tracking
                alert.condition_met_since = None
                alert.save()
        
        return triggered_alerts

    def get_user_alerts_summary(self, user) -> Dict:
        """
        Get summary of alerts for a specific user
        """
        alerts = Alert.objects.filter(user=user)
        
        return {
            'total_alerts': alerts.count(),
            'active_alerts': alerts.filter(is_active=True).count(),
            'threshold_alerts': alerts.filter(alert_type='THRESHOLD', is_active=True).count(),
            'duration_alerts': alerts.filter(alert_type='DURATION', is_active=True).count(),
            'triggered_today': TriggeredAlert.objects.filter(
                alert__user=user,
                triggered_at__date=timezone.now().date()
            ).count()
        }

    def cleanup_old_triggered_alerts(self, days_to_keep: int = 30):
        """
        Clean up old triggered alert records
        """
        cutoff_date = timezone.now() - timezone.timedelta(days=days_to_keep)
        deleted_count = TriggeredAlert.objects.filter(
            triggered_at__lt=cutoff_date
        ).delete()[0]
        
        logger.info(f"Cleaned up {deleted_count} old triggered alert records")
        return deleted_count

    def get_all_triggered_alerts_summary(self) -> Dict:
        """
        Get a summary of all triggered alerts
        """
        triggered_alerts = self.get_all_triggered_alerts()
        return {
            'total_triggered_alerts': len(triggered_alerts),
            'triggered_alerts': [alert.id for alert in triggered_alerts]
        }

    def get_all_triggered_alerts(self) -> List[TriggeredAlert]:
        """
        Get all triggered alerts
        """
        return list(TriggeredAlert.objects.all().select_related('alert'))
