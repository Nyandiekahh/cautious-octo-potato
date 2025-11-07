from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class EnergyReading(models.Model):
    """Model to store energy readings from the meter"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='energy_readings'
    )
    timestamp = models.DateTimeField(default=timezone.now)
    
    # Energy metrics
    energy_kwh = models.DecimalField(max_digits=10, decimal_places=3, help_text="Energy consumed in kWh")
    power_kw = models.DecimalField(max_digits=10, decimal_places=3, help_text="Current power draw in kW")
    voltage = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    current = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    # Cost calculation
    cost = models.DecimalField(max_digits=10, decimal_places=2, help_text="Cost in KES")
    
    # Battery status (if applicable)
    battery_percentage = models.IntegerField(null=True, blank=True)
    battery_status = models.CharField(
        max_length=20,
        choices=[
            ('charging', 'Charging'),
            ('discharging', 'Discharging'),
            ('idle', 'Idle'),
            ('full', 'Full'),
        ],
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Energy Reading'
        verbose_name_plural = 'Energy Readings'
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.timestamp.strftime('%Y-%m-%d %H:%M')} - {self.energy_kwh}kWh"
    
    def save(self, *args, **kwargs):
        # Auto-calculate cost if not provided
        if not self.cost:
            from django.conf import settings
            self.cost = self.energy_kwh * Decimal(str(settings.ENERGY_RATE_PER_KWH))
        super().save(*args, **kwargs)


class UsageSummary(models.Model):
    """Model to store daily/weekly/monthly usage summaries"""
    
    PERIOD_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='usage_summaries'
    )
    period_type = models.CharField(max_length=10, choices=PERIOD_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Summary metrics
    total_energy_kwh = models.DecimalField(max_digits=10, decimal_places=3)
    average_power_kw = models.DecimalField(max_digits=10, decimal_places=3)
    peak_power_kw = models.DecimalField(max_digits=10, decimal_places=3)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Additional metrics
    reading_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Usage Summary'
        verbose_name_plural = 'Usage Summaries'
        unique_together = ['user', 'period_type', 'start_date']
    
    def __str__(self):
        return f"{self.user.username} - {self.period_type} - {self.start_date}"
