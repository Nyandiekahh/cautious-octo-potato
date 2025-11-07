from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from .models import Payment, PaymentMethod


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['reference', 'user', 'amount_display', 'payment_method', 
                    'status_display', 'created_at', 'completed_at']
    list_filter = ['status', 'payment_method', 'created_at', 'completed_at']
    search_fields = ['reference', 'user__username', 'user__email', 
                    'user__meter_number', 'transaction_id']
    readonly_fields = ['reference', 'created_at', 'updated_at', 'completed_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Payment Details', {
            'fields': ('reference', 'amount', 'payment_method', 'status', 
                      'transaction_id', 'description')
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def amount_display(self, obj):
        """Display amount with formatting"""
        color = '#2E7D32' if obj.status == 'success' else '#757575'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, f'${obj.amount:.2f}'
        )
    amount_display.short_description = 'Amount'
    amount_display.admin_order_field = 'amount'
    
    def status_display(self, obj):
        """Display status with color coding"""
        status_colors = {
            'pending': '#FF9800',
            'processing': '#2196F3',
            'success': '#4CAF50',
            'failed': '#F44336',
            'cancelled': '#9E9E9E',
            'refunded': '#9C27B0',
        }
        color = status_colors.get(obj.status, '#757575')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_status_display().upper()
        )
    status_display.short_description = 'Status'
    status_display.admin_order_field = 'status'
    
    actions = ['mark_as_success', 'mark_as_failed', 'export_payments']
    
    def mark_as_success(self, request, queryset):
        """Mark selected payments as successful"""
        count = 0
        for payment in queryset.filter(status__in=['pending', 'processing']):
            payment.mark_as_success()
            count += 1
        self.message_user(request, f'{count} payment(s) marked as successful.')
    mark_as_success.short_description = "Mark as successful"
    
    def mark_as_failed(self, request, queryset):
        """Mark selected payments as failed"""
        count = 0
        for payment in queryset.filter(status__in=['pending', 'processing']):
            payment.mark_as_failed('Manually marked as failed by admin')
            count += 1
        self.message_user(request, f'{count} payment(s) marked as failed.')
    mark_as_failed.short_description = "Mark as failed"
    
    def export_payments(self, request, queryset):
        """Export selected payments"""
        count = queryset.count()
        total = queryset.aggregate(Sum('amount'))['amount__sum'] or 0
        self.message_user(
            request,
            f'{count} payment(s) ready for export. Total: ${total:.2f}'
        )
    export_payments.short_description = "Export selected payments"
    
    def changelist_view(self, request, extra_context=None):
        """Add summary statistics to the changelist view"""
        extra_context = extra_context or {}
        
        # Calculate statistics
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        today_payments = Payment.objects.filter(created_at__date=today)
        week_payments = Payment.objects.filter(created_at__date__gte=week_ago)
        month_payments = Payment.objects.filter(created_at__date__gte=month_ago)
        
        extra_context['today_count'] = today_payments.count()
        extra_context['today_total'] = today_payments.filter(
            status='success'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        extra_context['week_count'] = week_payments.count()
        extra_context['week_total'] = week_payments.filter(
            status='success'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        extra_context['month_count'] = month_payments.count()
        extra_context['month_total'] = month_payments.filter(
            status='success'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['user', 'method_type_display', 'details_display', 
                    'is_default', 'is_active', 'created_at']
    list_filter = ['method_type', 'is_default', 'is_active', 'created_at']
    search_fields = ['user__username', 'user__email', 'card_last_four', 
                    'bank_name', 'mobile_number']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Method Information', {
            'fields': ('method_type', 'is_default', 'is_active', 'external_id')
        }),
        ('Card Details', {
            'fields': ('card_brand', 'card_last_four', 'card_expiry'),
            'classes': ('collapse',)
        }),
        ('Bank Details', {
            'fields': ('bank_name', 'account_number_last_four'),
            'classes': ('collapse',)
        }),
        ('Mobile Money Details', {
            'fields': ('mobile_provider', 'mobile_number'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def method_type_display(self, obj):
        """Display method type with icon"""
        icons = {
            'card': '💳',
            'bank': '🏦',
            'mobile': '📱',
        }
        icon = icons.get(obj.method_type, '💰')
        return format_html(
            '{} {}',
            icon, obj.get_method_type_display()
        )
    method_type_display.short_description = 'Method Type'
    
    def details_display(self, obj):
        """Display payment method details"""
        return str(obj)
    details_display.short_description = 'Details'
    
    actions = ['set_as_default', 'deactivate_methods']
    
    def set_as_default(self, request, queryset):
        """Set selected method as default"""
        if queryset.count() > 1:
            self.message_user(
                request,
                'Please select only one payment method to set as default.',
                level='warning'
            )
            return
        
        method = queryset.first()
        method.is_default = True
        method.save()
        self.message_user(request, f'Payment method set as default for {method.user.username}')
    set_as_default.short_description = "Set as default"
    
    def deactivate_methods(self, request, queryset):
        """Deactivate selected payment methods"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} payment method(s) deactivated.')
    deactivate_methods.short_description = "Deactivate selected methods"