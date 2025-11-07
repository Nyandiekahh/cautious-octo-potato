from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import Notification, NotificationPreference
from .serializers import (
    NotificationSerializer, NotificationPreferenceSerializer,
    NotificationStatsSerializer
)


class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet for Notification operations"""
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter notifications by current user"""
        queryset = Notification.objects.filter(user=self.request.user)
        
        # Filter by read status
        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            is_read = is_read.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_read=is_read)
        
        # Filter by notification type
        notification_type = self.request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get all unread notifications"""
        queryset = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'count': count})
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a notification as read"""
        notification = self.get_object()
        notification.mark_as_read()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        queryset = self.get_queryset().filter(is_read=False)
        count = 0
        for notification in queryset:
            notification.mark_as_read()
            count += 1
        return Response({
            'message': f'{count} notification(s) marked as read',
            'count': count
        })
    
    @action(detail=False, methods=['post'])
    def clear_all(self, request):
        """Delete all read notifications"""
        deleted = self.get_queryset().filter(is_read=True).delete()
        return Response({
            'message': f'{deleted[0]} notification(s) deleted',
            'count': deleted[0]
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get notification statistics"""
        queryset = self.get_queryset()
        today = timezone.now().date()
        
        # Count by status
        total_count = queryset.count()
        unread_count = queryset.filter(is_read=False).count()
        read_count = queryset.filter(is_read=True).count()
        today_count = queryset.filter(created_at__date=today).count()
        
        # Count by type
        by_type = {}
        type_counts = queryset.values('notification_type').annotate(
            count=Count('id')
        )
        for item in type_counts:
            by_type[item['notification_type']] = item['count']
        
        data = {
            'total_notifications': total_count,
            'unread_count': unread_count,
            'read_count': read_count,
            'today_count': today_count,
            'by_type': by_type,
        }
        
        serializer = NotificationStatsSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent notifications (last 24 hours)"""
        cutoff = timezone.now() - timedelta(hours=24)
        queryset = self.get_queryset().filter(created_at__gte=cutoff)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    """ViewSet for NotificationPreference operations"""
    queryset = NotificationPreference.objects.all()
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter preferences by current user"""
        return NotificationPreference.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def my_preferences(self, request):
        """Get or update current user's notification preferences"""
        # Get or create preferences for current user
        preferences, created = NotificationPreference.objects.get_or_create(
            user=request.user
        )
        
        if request.method == 'GET':
            serializer = self.get_serializer(preferences)
            return Response(serializer.data)
        else:
            serializer = self.get_serializer(
                preferences,
                data=request.data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def enable_all(self, request):
        """Enable all notification channels"""
        preferences, created = NotificationPreference.objects.get_or_create(
            user=request.user
        )
        
        preferences.email_enabled = True
        preferences.sms_enabled = True
        preferences.push_enabled = True
        preferences.save()
        
        serializer = self.get_serializer(preferences)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def disable_all(self, request):
        """Disable all notification channels"""
        preferences, created = NotificationPreference.objects.get_or_create(
            user=request.user
        )
        
        preferences.email_enabled = False
        preferences.sms_enabled = False
        preferences.push_enabled = False
        preferences.save()
        
        serializer = self.get_serializer(preferences)
        return Response(serializer.data)