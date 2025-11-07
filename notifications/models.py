from django.db import models
from django.conf import settings
from django.utils import timezone


class Notification(models.Model):
    """Model to store user notifications"""
    
    NOTIFICATION_TYPES = [
        ('low_balance', 'Low Balance Alert'),
        ('high_usage', 'High Usage Alert'),
        ('payment_success', 'Payment Successful'),
        ('payment_failed', 'Payment Failed'),
        ('device_offline', 'Device Offline'),
        ('device_online', 'Device Online'),
        ('system', 'System Notification'),
        ('general', 'General'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Additional data (JSON)
    data = models.JSONField(blank=True, null=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(blank=True, null=True)
    
    # Delivery status
    email_sent = models.BooleanField(default=False)
    sms_sent = models.BooleanField(default=False)
    push_sent = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['is_read']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def send_email(self):
        """Send notification via email"""
        if not self.email_sent and self.user.email and self.user.notifications_enabled:
            from django.core.mail import send_mail
            from django.conf import settings
            
            try:
                send_mail(
                    subject=self.title,
                    message=self.message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[self.user.email],
                    fail_silently=False,
                )
                self.email_sent = True
                self.save(update_fields=['email_sent'])
            except Exception as e:
                print(f"Failed to send email: {e}")


class NotificationPreference(models.Model):
    """Model to store user notification preferences"""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    
    # Email notifications
    email_enabled = models.BooleanField(default=True)
    email_low_balance = models.BooleanField(default=True)
    email_high_usage = models.BooleanField(default=True)
    email_payment = models.BooleanField(default=True)
    email_device = models.BooleanField(default=True)
    
    # SMS notifications
    sms_enabled = models.BooleanField(default=False)
    sms_low_balance = models.BooleanField(default=False)
    sms_high_usage = models.BooleanField(default=False)
    sms_payment = models.BooleanField(default=False)
    
    # Push notifications
    push_enabled = models.BooleanField(default=True)
    push_low_balance = models.BooleanField(default=True)
    push_high_usage = models.BooleanField(default=True)
    push_payment = models.BooleanField(default=True)
    push_device = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'
    
    def __str__(self):
        return f"{self.user.username} - Notification Preferences"