from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from accounts.models import User
from energy_usage.models import EnergyReading
from payments.models import Payment
from .models import Notification, NotificationPreference


@receiver(post_save, sender=User)
def create_notification_preferences(sender, instance, created, **kwargs):
    """Create notification preferences for new users"""
    if created:
        NotificationPreference.objects.create(user=instance)


@receiver(post_save, sender=EnergyReading)
def check_usage_alerts(sender, instance, created, **kwargs):
    """Check for high usage and create alerts"""
    if created and instance.user.usage_alert:
        # Check if usage exceeds threshold
        if instance.energy_kwh >= instance.user.usage_threshold:
            Notification.objects.create(
                user=instance.user,
                notification_type='high_usage',
                title='High Energy Usage Alert',
                message=f'Your energy usage of {instance.energy_kwh}kWh exceeds your threshold of {instance.user.usage_threshold}kWh.',
                data={
                    'reading_id': instance.id,
                    'energy_kwh': float(instance.energy_kwh),
                    'threshold': float(instance.user.usage_threshold)
                }
            )


@receiver(post_save, sender=Payment)
def check_balance_alerts(sender, instance, created, **kwargs):
    """Check for low balance and create alerts"""
    if instance.status == 'success' and instance.user.low_balance_alert:
        # Check if balance is below threshold
        if instance.user.balance <= instance.user.low_balance_threshold:
            Notification.objects.create(
                user=instance.user,
                notification_type='low_balance',
                title='Low Balance Alert',
                message=f'Your current balance of ${instance.user.balance} is below your threshold of ${instance.user.low_balance_threshold}. Please top up soon.',
                data={
                    'balance': float(instance.user.balance),
                    'threshold': float(instance.user.low_balance_threshold)
                }
            )