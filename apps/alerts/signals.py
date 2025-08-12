# Signal handlers for additional validation
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Alert, TriggeredAlert
import logging


logger = logging.getLogger(__name__)
@receiver(pre_save, sender=Alert)
def alert_pre_save(sender, instance, **kwargs):
    """Additional pre-save validation and processing"""
    # Reset condition_met_since if alert is deactivated
    if not instance.is_active and instance.condition_met_since:
        instance.condition_met_since = None
        logger.info(f"Reset condition_met_since for deactivated alert {instance.pk}")

@receiver(post_save, sender=TriggeredAlert)
def triggered_alert_post_save(sender, instance, created, **kwargs):
    """Post-save processing for triggered alerts"""
    if created:
        # Automatically deactivate threshold alerts after triggering
        if instance.alert.alert_type == 'THRESHOLD' and instance.alert.is_active:
            instance.alert.is_active = False
            instance.alert.save(update_fields=['is_active'])
            logger.info(f"Deactivated threshold alert {instance.alert.pk} after triggering")
        
        # Reset condition_met_since for duration alerts after triggering
        elif instance.alert.alert_type == 'DURATION' and instance.alert.condition_met_since:
            instance.alert.condition_met_since = None
            instance.alert.save(update_fields=['condition_met_since'])
            logger.info(f"Reset condition_met_since for duration alert {instance.alert.pk} after triggering")