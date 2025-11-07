from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'meter_number', 'balance_display', 
                    'device_status_display', 'is_active', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'device_status', 'created_at']
    search_fields = ['username', 'email', 'meter_number', 'first_name', 'last_name']
    readonly_fields = ['date_joined', 'last_login', 'created_at', 'updated_at', 'last_online']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'address', 'city', 'country')
        }),
        ('Meter Information', {
            'fields': ('meter_number', 'balance', 'device_id', 'firmware_version', 
                      'device_status', 'last_online')
        }),
        ('Settings', {
            'fields': ('notifications_enabled', 'low_balance_alert', 'usage_alert',
                      'low_balance_threshold', 'usage_threshold'),
            'classes': ('collapse',)
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'meter_number', 'password1', 'password2'),
        }),
    )
    
    def balance_display(self, obj):
        """Display balance with color coding"""
        color = 'green' if obj.balance > 20 else 'orange' if obj.balance > 10 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, f'${obj.balance:.2f}'
        )
    balance_display.short_description = 'Balance'
    
    def device_status_display(self, obj):
        """Display device status with color coding"""
        color_map = {
            'online': 'green',
            'offline': 'red',
            'maintenance': 'orange'
        }
        color = color_map.get(obj.device_status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            color, obj.get_device_status_display()
        )
    device_status_display.short_description = 'Device Status'
    
    actions = ['activate_users', 'deactivate_users', 'reset_device_status']
    
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} user(s) successfully activated.')
    activate_users.short_description = "Activate selected users"
    
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} user(s) successfully deactivated.')
    deactivate_users.short_description = "Deactivate selected users"
    
    def reset_device_status(self, request, queryset):
        updated = queryset.update(device_status='online')
        self.message_user(request, f'{updated} device(s) status reset to online.')
    reset_device_status.short_description = "Reset device status to online"