# apps/notifications/services.py
import logging
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from typing import Optional

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Service for sending alert notifications via email or console
    """

    def send_alert_notification(self, alert, current_price, triggered_alert) -> bool:
        """
        Send notification for triggered alert
        Try email first, fallback to console logging
        """
        try:
            # Try email notification first
            if self.send_email_notification(alert, current_price, triggered_alert):
                return True
            
            # Fallback to console notification
            return self.send_console_notification(alert, current_price, triggered_alert)
            
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return False

    def send_email_notification(self, alert, current_price, triggered_alert) -> bool:
        """
        Send email notification for triggered alert
        """
        try:
            # Check if email is configured
            if not settings.EMAIL_HOST_USER:
                logger.warning("Email not configured, skipping email notification")
                return False
            
            # Prepare email content
            subject = f"🚨 Stock Alert: {alert.stock.symbol} {alert.condition} ${alert.threshold_price}"
            
            # Create email body
            alert_type_text = "Threshold Alert" if alert.alert_type == 'THRESHOLD' else f"Duration Alert ({alert.duration_minutes} min)"
            
            message = f"""
Stock Alert Triggered!

Alert Details:
- Stock: {alert.stock.symbol} ({alert.stock.name})
- Type: {alert_type_text}
- Condition: {alert.stock.symbol} {alert.condition} ${alert.threshold_price}
- Current Price: ${current_price}
- Triggered At: {triggered_alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S UTC')}

This alert has been {"deactivated" if alert.alert_type == 'THRESHOLD' else "reset"} automatically.

You can manage your alerts by logging into the system.

---
Stock Alert System
            """.strip()
            
            # Send email
            success = send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER,
                recipient_list=[alert.user.email],
                fail_silently=False,
            )
            
            if success:
                logger.info(f"Email notification sent to {alert.user.email} for alert {alert.id}")
                return True
            else:
                logger.error(f"Failed to send email to {alert.user.email} for alert {alert.id}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
            return False

    def send_console_notification(self, alert, current_price, triggered_alert) -> bool:
        """
        Log alert notification to console (fallback method)
        """
        try:
            alert_info = {
                'alert_id': alert.id,
                'user': alert.user.username,
                'stock': alert.stock.symbol,
                'alert_type': alert.alert_type,
                'condition': f"{alert.condition} ${alert.threshold_price}",
                'current_price': f"${current_price}",
                'triggered_at': triggered_alert.triggered_at.isoformat(),
            }
            
            logger.info(f"🚨 STOCK ALERT TRIGGERED: {alert_info}")
            
            # Also print to console for visibility during development
            print(f"\n{'='*50}")
            print(f"🚨 STOCK ALERT TRIGGERED")
            print(f"{'='*50}")
            print(f"User: {alert.user.username}")
            print(f"Stock: {alert.stock.symbol} ({alert.stock.name})")
            print(f"Alert: {alert.stock.symbol} {alert.condition} ${alert.threshold_price}")
            print(f"Current Price: ${current_price}")
            print(f"Type: {alert.alert_type}")
            if alert.alert_type == 'DURATION':
                print(f"Duration: {alert.duration_minutes} minutes")
            print(f"Triggered: {triggered_alert.triggered_at}")
            print(f"{'='*50}\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending console notification: {str(e)}")
            return False

    def send_test_email(self, email: str) -> bool:
        """
        Send test email to verify email configuration
        """
        try:
            subject = "Stock Alert System - Test Email"
            message = """
This is a test email from your Stock Alert System.

If you received this email, your email configuration is working correctly!

Test Details:
- Sent At: {}
- System: Stock Alert System

You can now create stock alerts and receive notifications.
            """.format(timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC'))
            
            success = send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending test email: {str(e)}")
            return False