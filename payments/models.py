from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class Payment(models.Model):
    """Model to store payment transactions"""
    
    PAYMENT_METHOD_CHOICES = [
        ('card', 'Credit/Debit Card'),
        ('bank', 'Bank Transfer'),
        ('mobile', 'Mobile Money'),
        ('cash', 'Cash'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    
    # Payment details
    reference = models.CharField(max_length=100, unique=True, editable=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Transaction details
    transaction_id = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['reference']),
        ]
    
    def __str__(self):
        return f"{self.reference} - {self.user.username} - ${self.amount}"
    
    def save(self, *args, **kwargs):
        # Generate reference if not exists
        if not self.reference:
            self.reference = f"PAY-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)
    
    def mark_as_success(self):
        """Mark payment as successful and update user balance"""
        if self.status != 'success':
            self.status = 'success'
            self.completed_at = timezone.now()
            self.save()
            
            # Update user balance
            self.user.update_balance(self.amount)
            
            # Create notification
            from notifications.models import Notification
            Notification.objects.create(
                user=self.user,
                notification_type='payment_success',
                title='Payment Successful',
                message=f'Your payment of ${self.amount} has been processed successfully.',
                data={'payment_id': self.id, 'reference': self.reference}
            )
    
    def mark_as_failed(self, reason=''):
        """Mark payment as failed"""
        self.status = 'failed'
        if reason:
            self.description = reason
        self.save()
        
        # Create notification
        from notifications.models import Notification
        Notification.objects.create(
            user=self.user,
            notification_type='payment_failed',
            title='Payment Failed',
            message=f'Your payment of ${self.amount} could not be processed. {reason}',
            data={'payment_id': self.id, 'reference': self.reference}
        )


class PaymentMethod(models.Model):
    """Model to store saved payment methods"""
    
    METHOD_TYPE_CHOICES = [
        ('card', 'Card'),
        ('bank', 'Bank Account'),
        ('mobile', 'Mobile Money'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payment_methods'
    )
    
    method_type = models.CharField(max_length=20, choices=METHOD_TYPE_CHOICES)
    is_default = models.BooleanField(default=False)
    
    # Card details (encrypted in production)
    card_last_four = models.CharField(max_length=4, blank=True, null=True)
    card_brand = models.CharField(max_length=50, blank=True, null=True)
    card_expiry = models.CharField(max_length=7, blank=True, null=True)  # MM/YYYY
    
    # Bank details
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    account_number_last_four = models.CharField(max_length=4, blank=True, null=True)
    
    # Mobile money details
    mobile_number = models.CharField(max_length=20, blank=True, null=True)
    mobile_provider = models.CharField(max_length=50, blank=True, null=True)
    
    # External reference (from payment gateway)
    external_id = models.CharField(max_length=200, blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_default', '-created_at']
        verbose_name = 'Payment Method'
        verbose_name_plural = 'Payment Methods'
    
    def __str__(self):
        if self.method_type == 'card' and self.card_last_four:
            return f"{self.card_brand} •••• {self.card_last_four}"
        elif self.method_type == 'bank' and self.bank_name:
            return f"{self.bank_name} •••• {self.account_number_last_four}"
        elif self.method_type == 'mobile' and self.mobile_number:
            return f"{self.mobile_provider} - {self.mobile_number}"
        return f"{self.get_method_type_display()}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default payment method per user
        if self.is_default:
            PaymentMethod.objects.filter(
                user=self.user,
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)