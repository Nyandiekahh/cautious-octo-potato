from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title_display', 'notification_type_display', 
                    'is_read', 'delivery_status', 'created_at']
    list_filter = ['notification_type', 'is_read', 'email_sent', 
                   'sms_sent', 'push_sent', 'created_at']
    search_fields = ['user__username', 'user__email', 'title', 'message']
    readonly_fields = ['read_at', 'created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Notification Details', {
            'fields': ('notification_type', 'title', 'message', 'data')
        }),
        ('Status', {
            'fields': ('is_read', 'read_at')
        }),
        ('Delivery Status', {
            'fields': ('email_sent', 'sms_sent', 'push_sent'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def title_display(self, obj):
        """Display title with read status"""
        if obj.is_read:
            return format_html(
                '<span style="color: #757575;">{}</span>',
                obj.title
            )
        return format_html(
            '<span style="font-weight: bold;">{}</span>',
            obj.title
        )
    title_display.short_description = 'Title'
    
    def notification_type_display(self, obj):
        """Display notification type with color coding"""
        type_colors = {
            'low_balance': '#FF9800',
            'high_usage': '#F44336',
            'payment_success': '#4CAF50',
            'payment_failed': '#F44336',
            'device_offline': '#F44336',
            'device_online': '#4CAF50',
            'system': '#2196F3',
            'general': '#9E9E9E',
        }
        color = type_colors.get(obj.notification_type, '#757575')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 3px; font-size: 10px;">{}</span>',
            color, obj.get_notification_type_display()
        )
    notification_type_display.short_description = 'Type'
    
    def delivery_status(self, obj):
        """Display delivery status icons"""
        icons = []
        if obj.email_sent:
            icons.append('📧')
        if obj.sms_sent:
            icons.append('📱')
        if obj.push_sent:
            icons.append('🔔')
        
        return ' '.join(icons) if icons else '-'
    delivery_status.short_description = 'Delivered'
    
    actions = ['mark_as_read', 'mark_as_unread', 'send_email_notification', 'delete_old_notifications']
    
    def mark_as_read(self, request, queryset):
        """Mark selected notifications as read"""
        count = 0
        for notification in queryset.filter(is_read=False):
            notification.mark_as_read()
            count += 1
        self.message_user(request, f'{count} notification(s) marked as read.')
    mark_as_read.short_description = "Mark as read"
    
    def mark_as_unread(self, request, queryset):
        """Mark selected notifications as unread"""
        updated = queryset.update(is_read=False, read_at=None)
        self.message_user(request, f'{updated} notification(s) marked as unread.')
    mark_as_unread.short_description = "Mark as unread"
    
    def send_email_notification(self, request, queryset):
        """Send email for selected notifications"""
        count = 0
        for notification in queryset.filter(email_sent=False):
            notification.send_email()
            count += 1
        self.message_user(request, f'{count} email(s) sent.')
    send_email_notification.short_description = "Send email notifications"
    
    def delete_old_notifications(self, request, queryset):
        """Delete notifications older than 30 days"""
        cutoff_date = timezone.now() - timedelta(days=30)
        deleted = queryset.filter(created_at__lt=cutoff_date).delete()
        self.message_user(request, f'{deleted[0]} old notification(s) deleted.')
    delete_old_notifications.short_description = "Delete old notifications (30+ days)"


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'email_status', 'sms_status', 'push_status', 'updated_at']
    list_filter = ['email_enabled', 'sms_enabled', 'push_enabled', 'updated_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Email Notifications', {
            'fields': ('email_enabled', 'email_low_balance', 'email_high_usage',
                      'email_payment', 'email_device')
        }),
        ('SMS Notifications', {
            'fields': ('sms_enabled', 'sms_low_balance', 'sms_high_usage', 'sms_payment'),
            'classes': ('collapse',)
        }),
        ('Push Notifications', {
            'fields': ('push_enabled', 'push_low_balance', 'push_high_usage',
                      'push_payment', 'push_device'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def email_status(self, obj):
        """Display email notification status"""
        if obj.email_enabled:
            return format_html('<span style="color: green;">✓ Enabled</span>')
        return format_html('<span style="color: red;">✗ Disabled</span>')
    email_status.short_description = 'Email'
    
    def sms_status(self, obj):
        """Display SMS notification status"""
        if obj.sms_enabled:
            return format_html('<span style="color: green;">✓ Enabled</span>')
        return format_html('<span style="color: red;">✗ Disabled</span>')
    sms_status.short_description = 'SMS'
    
    def push_status(self, obj):
        """Display push notification status"""
        if obj.push_enabled:
            return format_html('<span style="color: green;">✓ Enabled</span>')
        return format_html('<span style="color: red;">✗ Disabled</span>')
    push_status.short_description = 'Push'
    
    actions = ['enable_all_notifications', 'disable_all_notifications']
    
    def enable_all_notifications(self, request, queryset):
        """Enable all notification channels"""
        updated = queryset.update(
            email_enabled=True,
            sms_enabled=True,
            push_enabled=True
        )
        self.message_user(request, f'{updated} user(s) notification preferences updated.')
    enable_all_notifications.short_description = "Enable all notification channels"
    
    def disable_all_notifications(self, request, queryset):
        """Disable all notification channels"""
        updated = queryset.update(
            email_enabled=False,
            sms_enabled=False,
            push_enabled=False
        )
        self.message_user(request, f'{updated} user(s) notification preferences updated.')
    disable_all_notifications.short_description = "Disable all notification channels"