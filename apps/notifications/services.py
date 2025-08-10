# apps/notifications/services.py
import logging
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from typing import Optional
from decimal import Decimal
from django.contrib.humanize.templatetags.humanize import naturaltime

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

    def _get_alert_emoji(self, alert, current_price):
        """Get appropriate emoji based on alert condition and price movement"""
        if alert.condition == 'ABOVE':
            return "📈" if float(current_price) > float(alert.threshold_price) else "⚠️"
        elif alert.condition == 'BELOW':
            return "📉" if float(current_price) < float(alert.threshold_price) else "⚠️"
        return "🔔"

    def _format_price(self, price):
        """Format price with proper currency symbol and decimals"""
        return f"${float(price):,.2f}"

    def _get_price_change_direction(self, alert, current_price):
        """Determine if price went up or down relative to threshold"""
        current = float(current_price)
        threshold = float(alert.threshold_price)
        
        if alert.condition == 'ABOVE' and current > threshold:
            return "increased above"
        elif alert.condition == 'BELOW' and current < threshold:
            return "dropped below"
        else:
            return "reached"

    def send_email_notification(self, alert, current_price, triggered_alert) -> bool:
        """
        Send beautifully formatted email notification for triggered alert
        """
        try:
            # Check if email is configured
            if not settings.EMAIL_HOST_USER:
                logger.warning("Email not configured, skipping email notification")
                return False
            
            # Get user's first name or fallback to username
            user_name = getattr(alert.user, 'first_name', '') or alert.user.username or 'Valued User'
            
            # Prepare email content
            emoji = self._get_alert_emoji(alert, current_price)
            price_direction = self._get_price_change_direction(alert, current_price)
            
            subject = f"{emoji} Yahya's Stock Alert: {alert.stock.symbol} {price_direction} {self._format_price(alert.threshold_price)}"
            
            # Create rich HTML email body
            html_content = self._create_html_email_body(alert, current_price, triggered_alert, user_name, emoji)
            
            # Create plain text version
            plain_text_content = self._create_plain_text_email_body(alert, current_price, triggered_alert, user_name)
            
            # Create email with both HTML and plain text
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_text_content,
                from_email=f"Yahya's Stock Alert System <{settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER}>",
                to=[alert.user.email]
            )
            email.attach_alternative(html_content, "text/html")
            
            # Send email
            success = email.send(fail_silently=False)
            
            if success:
                logger.info(f"Email notification sent to {alert.user.email} for alert {alert.id}")
                return True
            else:
                logger.error(f"Failed to send email to {alert.user.email} for alert {alert.id}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
            return False

    def _create_html_email_body(self, alert, current_price, triggered_alert, user_name, emoji):
        """Create beautiful HTML email template"""
        alert_type_text = "Threshold Alert" if alert.alert_type == 'THRESHOLD' else f"Duration Alert ({alert.duration_minutes} min)"
        price_direction = self._get_price_change_direction(alert, current_price)
        from django.utils import timezone
        import pytz

        local_tz = pytz.timezone('Africa/Cairo')
        local_triggered_time = timezone.localtime(triggered_alert.triggered_at, local_tz)

        # Format times for display
        triggered_time_humanized = naturaltime(local_triggered_time)
        triggered_time_formatted = local_triggered_time.strftime('%b %d, %Y at %I:%M %p')

        # Determine color scheme based on alert condition
        if alert.condition == 'ABOVE':
            accent_color = "#10B981"  # Green for bullish
            bg_color = "#ECFDF5"
        else:
            accent_color = "#EF4444"  # Red for bearish
            bg_color = "#FEF2F2"
            
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Stock Alert Notification</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                    line-height: 1.6;
                    color: #374151;
                    background-color: #F9FAFB;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: white;
                    border-radius: 12px;
                    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, {accent_color} 0%, #1F2937 100%);
                    color: white;
                    padding: 30px 40px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                    font-weight: 700;
                }}
                .header p {{
                    margin: 10px 0 0 0;
                    opacity: 0.9;
                    font-size: 16px;
                }}
                .alert-badge {{
                    background-color: {bg_color};
                    border-left: 4px solid {accent_color};
                    padding: 20px;
                    margin: 30px 40px;
                    border-radius: 8px;
                }}
                .alert-title {{
                    font-size: 20px;
                    font-weight: 600;
                    color: {accent_color};
                    margin: 0 0 15px 0;
                }}
                .content {{
                    padding: 0 40px 40px;
                }}
                .details-grid {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                    margin: 30px 0;
                }}
                .detail-item {{
                    background-color: #F9FAFB;
                    padding: 20px;
                    border-radius: 8px;
                    border: 1px solid #E5E7EB;
                }}
                .detail-label {{
                    font-size: 12px;
                    font-weight: 600;
                    color: #6B7280;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    margin-bottom: 5px;
                }}
                .detail-value {{
                    font-size: 18px;
                    font-weight: 700;
                    color: #1F2937;
                }}
                .price-highlight {{
                    font-size: 32px;
                    font-weight: 800;
                    color: {accent_color};
                    text-align: center;
                    margin: 20px 0;
                }}
                .status-message {{
                    background-color: #FEF3C7;
                    border-left: 4px solid #F59E0B;
                    padding: 15px 20px;
                    margin: 20px 0;
                    border-radius: 6px;
                }}
                .footer {{
                    background-color: #F9FAFB;
                    padding: 30px 40px;
                    text-align: center;
                    border-top: 1px solid #E5E7EB;
                }}
                .footer-text {{
                    color: #6B7280;
                    font-size: 14px;
                    margin: 0;
                }}
                .signature {{
                    margin-top: 20px;
                    font-style: italic;
                    color: {accent_color};
                    font-weight: 600;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{emoji} Stock Alert Triggered!</h1>
                    <p>Hello {user_name}, your stock alert has been activated</p>
                </div>
                
                <div class="alert-badge">
                    <div class="alert-title">{alert.stock.symbol} has {price_direction} your target price!</div>
                    <p><strong>{alert.stock.name}</strong> ({alert.stock.symbol}) {alert.condition.lower()} {self._format_price(alert.threshold_price)}</p>
                </div>
                
                <div class="content">
                    <div class="price-highlight">
                        Current Price: {self._format_price(current_price)}
                    </div>
                    
                    <div class="details-grid">
                        <div class="detail-item">
                            <div class="detail-label">Alert Type</div>
                            <div class="detail-value">{alert_type_text}</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">Condition</div>
                            <div class="detail-value">{alert.condition} {self._format_price(alert.threshold_price)}</div>
                        </div>
                       <div class="detail-item">
                           <div class="detail-label">Triggered At</div>
                           <div class="detail-value">{local_triggered_time.strftime('%b %d, %Y at %I:%M %p %Z')}</div>
                       </div>
                       
                        <div class="detail-item">
                            <div class="detail-label">Status</div>
                            <div class="detail-value">{"Deactivated" if alert.alert_type == 'THRESHOLD' else "Reset"}</div>
                        </div>
                    </div>
                    
                    <div class="status-message">
                        <strong>Note:</strong> This alert has been automatically {"deactivated" if alert.alert_type == 'THRESHOLD' else "reset"}. 
                        You can create new alerts or modify existing ones through your dashboard.
                    </div>
                </div>
                
                <div class="footer">
                    <p class="footer-text">
                        Stay informed with real-time stock monitoring<br>
                        Manage your alerts anytime through the dashboard
                    </p>
                    <p class="signature">
                        — Yahya's Stock Alert System 📊
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        return html_content

    def _create_plain_text_email_body(self, alert, current_price, triggered_alert, user_name):
        """Create plain text version of the email"""
        alert_type_text = "Threshold Alert" if alert.alert_type == 'THRESHOLD' else f"Duration Alert ({alert.duration_minutes} min)"
        price_direction = self._get_price_change_direction(alert, current_price)
        
        return f"""
🚨 STOCK ALERT TRIGGERED!

Hello {user_name},

Your stock alert for {alert.stock.symbol} has been triggered!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ALERT DETAILS:
• Stock: {alert.stock.symbol} ({alert.stock.name})
• Type: {alert_type_text}
• Condition: {alert.stock.symbol} {alert.condition} {self._format_price(alert.threshold_price)}
• Current Price: {self._format_price(current_price)}
• Triggered At: {triggered_alert.triggered_at.strftime('%B %d, %Y at %I:%M %p UTC')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{alert.stock.symbol} has {price_direction} your target price of {self._format_price(alert.threshold_price)}!

⚡ STATUS UPDATE:
This alert has been automatically {"deactivated" if alert.alert_type == 'THRESHOLD' else "reset"}. 
You can create new alerts or modify existing ones through your dashboard.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Stay informed with real-time stock monitoring 📊
Manage your alerts anytime through the dashboard

— Yahya's Stock Alert System

        """.strip()

    def send_console_notification(self, alert, current_price, triggered_alert) -> bool:
        """
        Enhanced console notification with better formatting
        """
        try:
            emoji = self._get_alert_emoji(alert, current_price)
            price_direction = self._get_price_change_direction(alert, current_price)
            
            alert_info = {
                'alert_id': alert.id,
                'user': alert.user.username,
                'stock': alert.stock.symbol,
                'alert_type': alert.alert_type,
                'condition': f"{alert.condition} {self._format_price(alert.threshold_price)}",
                'current_price': self._format_price(current_price),
                'triggered_at': triggered_alert.triggered_at.isoformat(),
            }
            
            logger.info(f"{emoji} YAHYA'S STOCK ALERT TRIGGERED: {alert_info}")
            
            print(f"\n{'='*60}")
            print(f"{emoji} YAHYA'S STOCK ALERT SYSTEM")
            print(f"{'='*60}")
            print(f"📋 User: {alert.user.username}")
            print(f"📈 Stock: {alert.stock.symbol} ({alert.stock.name})")
            print(f"🎯 Alert: {alert.stock.symbol} {alert.condition} {self._format_price(alert.threshold_price)}")
            print(f"💰 Current Price: {self._format_price(current_price)} ({price_direction})")
            print(f"🏷️  Type: {alert.alert_type}")
            if alert.alert_type == 'DURATION':
                print(f"⏱️  Duration: {alert.duration_minutes} minutes")
            print(f"🕐 Triggered: {triggered_alert.triggered_at.strftime('%B %d, %Y at %I:%M %p UTC')}")
            print(f"✅ Status: {'Deactivated' if alert.alert_type == 'THRESHOLD' else 'Reset'}")
            print(f"{'='*60}\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending console notification: {str(e)}")
            return False

    def send_test_email(self, email: str) -> bool:
        """
        Send beautifully formatted test email
        """
        try:
            subject = "📊 Yahya's Stock Alert System - Test Email"
            
            # HTML version
            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Test Email</title>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        background-color: #F9FAFB;
                        padding: 20px;
                        margin: 0;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background: white;
                        border-radius: 12px;
                        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
                        overflow: hidden;
                    }}
                    .header {{
                        background: linear-gradient(135deg, #10B981 0%, #1F2937 100%);
                        color: white;
                        padding: 40px;
                        text-align: center;
                    }}
                    .content {{
                        padding: 40px;
                        text-align: center;
                    }}
                    .success-badge {{
                        background: #ECFDF5;
                        color: #10B981;
                        padding: 20px;
                        border-radius: 8px;
                        border: 2px solid #10B981;
                        margin: 20px 0;
                        font-weight: 600;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎉 Test Email Success!</h1>
                        <p>Your email configuration is working perfectly</p>
                    </div>
                    <div class="content">
                        <div class="success-badge">
                            ✅ Email system is ready for stock alerts!
                        </div>
                        <p><strong>Test Details:</strong></p>
                        <p>📅 Sent At: {timezone.now().strftime('%B %d, %Y at %I:%M %p UTC')}</p>
                        <p>🚀 System: Yahya's Stock Alert System</p>
                        <p>You're all set to receive stock alert notifications!</p>
                        <p style="margin-top: 30px; color: #6B7280;">
                            — Yahya's Stock Alert System 📊
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Plain text version
            plain_text = f"""
🎉 TEST EMAIL SUCCESS!

Your email configuration is working perfectly with Yahya's Stock Alert System!

✅ Email system is ready for stock alerts!

Test Details:
📅 Sent At: {timezone.now().strftime('%B %d, %Y at %I:%M %p UTC')}
🚀 System: Yahya's Stock Alert System

You're all set to receive stock alert notifications!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

— Yahya's Stock Alert System 📊
            """.strip()
            
            # Create email with both HTML and plain text
            email_msg = EmailMultiAlternatives(
                subject=subject,
                body=plain_text,
                from_email=f"Yahya's Stock Alert System <{settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER}>",
                to=[email]
            )
            email_msg.attach_alternative(html_content, "text/html")
            
            success = email_msg.send(fail_silently=False)
            
            if success:
                logger.info(f"Test email sent successfully to {email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending test email: {str(e)}")
            return False