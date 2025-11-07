from rest_framework import serializers
from .models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model"""
    
    notification_type_display = serializers.CharField(
        source='get_notification_type_display', 
        read_only=True
    )
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'notification_type_display',
            'title', 'message', 'data', 'is_read', 'read_at',
            'email_sent', 'sms_sent', 'push_sent',
            'created_at', 'time_ago'
        ]
        read_only_fields = [
            'id', 'notification_type', 'title', 'message', 'data',
            'email_sent', 'sms_sent', 'push_sent', 'created_at', 'read_at'
        ]
    
    def get_time_ago(self, obj):
        """Get human-readable time since notification was created"""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff < timedelta(minutes=1):
            return 'just now'
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f'{minutes} minute{"s" if minutes > 1 else ""} ago'
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f'{hours} hour{"s" if hours > 1 else ""} ago'
        elif diff < timedelta(days=7):
            days = diff.days
            return f'{days} day{"s" if days > 1 else ""} ago'
        elif diff < timedelta(days=30):
            weeks = int(diff.days / 7)
            return f'{weeks} week{"s" if weeks > 1 else ""} ago'
        else:
            return obj.created_at.strftime('%B %d, %Y')


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for NotificationPreference model"""
    
    class Meta:
        model = NotificationPreference
        fields = [
            'id', 'email_enabled', 'email_low_balance', 'email_high_usage',
            'email_payment', 'email_device', 'sms_enabled', 'sms_low_balance',
            'sms_high_usage', 'sms_payment', 'push_enabled', 'push_low_balance',
            'push_high_usage', 'push_payment', 'push_device',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NotificationStatsSerializer(serializers.Serializer):
    """Serializer for notification statistics"""
    total_notifications = serializers.IntegerField()
    unread_count = serializers.IntegerField()
    read_count = serializers.IntegerField()
    today_count = serializers.IntegerField()
    by_type = serializers.DictField()