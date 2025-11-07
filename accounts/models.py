from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Custom User model for the energy logging system"""
    
    email = models.EmailField(_('email address'), unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    meter_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    
    # Account balance
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Settings
    notifications_enabled = models.BooleanField(default=True)
    low_balance_alert = models.BooleanField(default=True)
    usage_alert = models.BooleanField(default=True)
    low_balance_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=10.00)
    usage_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=5.0)
    
    # Device information
    device_id = models.CharField(max_length=100, blank=True, null=True)
    firmware_version = models.CharField(max_length=20, default='v2.1.0')
    device_status = models.CharField(
        max_length=20,
        choices=[
            ('online', 'Online'),
            ('offline', 'Offline'),
            ('maintenance', 'Maintenance'),
        ],
        default='online'
    )
    last_online = models.DateTimeField(auto_now=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} - {self.meter_number}"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    def update_balance(self, amount):
        """Update user balance"""
        self.balance += amount
        self.save(update_fields=['balance'])
        return self.balance
    
    def has_sufficient_balance(self):
        """Check if user has sufficient balance"""
        return self.balance > 0