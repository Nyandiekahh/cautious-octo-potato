from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Avg, Max, Min, Count
from django.utils import timezone
from datetime import timedelta, datetime
from .models import EnergyReading, UsageSummary
from .serializers import (
    EnergyReadingSerializer, EnergyReadingCreateSerializer,
    UsageSummarySerializer, ChartDataSerializer, UsageStatsSerializer
)


class EnergyReadingViewSet(viewsets.ModelViewSet):
    """ViewSet for EnergyReading operations"""
    queryset = EnergyReading.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return EnergyReadingCreateSerializer
        return EnergyReadingSerializer
    
    def get_queryset(self):
        """Filter readings by current user"""
        queryset = EnergyReading.objects.filter(user=self.request.user)
        
        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(timestamp__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__date__lte=end_date)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest energy reading"""
        reading = self.get_queryset().first()
        if reading:
            serializer = self.get_serializer(reading)
            return Response(serializer.data)
        return Response({'message': 'No readings found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get usage statistics"""
        now = timezone.now()
        today = now.date()
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        queryset = self.get_queryset()
        
        # Today's usage
        today_usage = queryset.filter(
            timestamp__date=today
        ).aggregate(total=Sum('energy_kwh'))['total'] or 0
        
        # Yesterday's usage
        yesterday_usage = queryset.filter(
            timestamp__date=yesterday
        ).aggregate(total=Sum('energy_kwh'))['total'] or 0
        
        # This week's usage
        week_usage = queryset.filter(
            timestamp__date__gte=week_ago
        ).aggregate(total=Sum('energy_kwh'))['total'] or 0
        
        # This month's usage
        month_usage = queryset.filter(
            timestamp__date__gte=month_ago
        ).aggregate(total=Sum('energy_kwh'))['total'] or 0
        
        # Average daily usage (last 30 days)
        avg_daily = month_usage / 30 if month_usage > 0 else 0
        
        # Peak power
        peak_power = queryset.filter(
            timestamp__date__gte=month_ago
        ).aggregate(peak=Max('power_kw'))['peak'] or 0
        
        data = {
            'today': round(today_usage, 2),
            'yesterday': round(yesterday_usage, 2),
            'this_week': round(week_usage, 2),
            'this_month': round(month_usage, 2),
            'average_daily': round(avg_daily, 2),
            'peak_power': round(peak_power, 2),
        }
        
        serializer = UsageStatsSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def chart_data(self, request):
        """Get data for charts"""
        period = request.query_params.get('period', 'day')  # day, week, month
        now = timezone.now()
        
        if period == 'day':
            # Hourly data for last 24 hours
            start_time = now - timedelta(hours=24)
            readings = self.get_queryset().filter(timestamp__gte=start_time)
            
            # Group by hour
            hourly_data = {}
            for reading in readings:
                hour = reading.timestamp.hour
                if hour not in hourly_data:
                    hourly_data[hour] = []
                hourly_data[hour].append(float(reading.energy_kwh))
            
            labels = [f"{h:02d}:00" for h in range(24)]
            data = [sum(hourly_data.get(h, [0])) for h in range(24)]
            
        elif period == 'week':
            # Daily data for last 7 days
            start_date = now.date() - timedelta(days=7)
            readings = self.get_queryset().filter(timestamp__date__gte=start_date)
            
            # Group by day
            daily_data = {}
            for reading in readings:
                day = reading.timestamp.date()
                if day not in daily_data:
                    daily_data[day] = []
                daily_data[day].append(float(reading.energy_kwh))
            
            labels = []
            data = []
            for i in range(7):
                date = (now.date() - timedelta(days=6-i))
                labels.append(date.strftime('%a'))
                data.append(sum(daily_data.get(date, [0])))
        
        elif period == 'month':
            # Daily data for last 30 days
            start_date = now.date() - timedelta(days=30)
            readings = self.get_queryset().filter(timestamp__date__gte=start_date)
            
            # Group by day
            daily_data = {}
            for reading in readings:
                day = reading.timestamp.date()
                if day not in daily_data:
                    daily_data[day] = []
                daily_data[day].append(float(reading.energy_kwh))
            
            labels = []
            data = []
            for i in range(30):
                date = (now.date() - timedelta(days=29-i))
                labels.append(date.strftime('%m/%d'))
                data.append(sum(daily_data.get(date, [0])))
        
        else:
            return Response({'error': 'Invalid period'}, status=status.HTTP_400_BAD_REQUEST)
        
        chart_data = {
            'labels': labels,
            'datasets': [{
                'label': 'Energy Usage (kWh)',
                'data': [round(d, 2) for d in data],
                'borderColor': 'rgb(46, 125, 50)',
                'backgroundColor': 'rgba(46, 125, 50, 0.1)',
            }]
        }
        
        return Response(chart_data)
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Create multiple readings at once"""
        if not isinstance(request.data, list):
            return Response(
                {'error': 'Data must be a list'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = EnergyReadingCreateSerializer(
            data=request.data,
            many=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': f'{len(serializer.data)} readings created successfully'},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UsageSummaryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for UsageSummary (read-only)"""
    queryset = UsageSummary.objects.all()
    serializer_class = UsageSummarySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter summaries by current user"""
        queryset = UsageSummary.objects.filter(user=self.request.user)
        
        # Filter by period type
        period_type = self.request.query_params.get('period_type')
        if period_type:
            queryset = queryset.filter(period_type=period_type)
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate usage summary for a period"""
        period_type = request.data.get('period_type', 'daily')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {'error': 'start_date and end_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse dates
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get readings for the period
        readings = EnergyReading.objects.filter(
            user=request.user,
            timestamp__date__gte=start_date,
            timestamp__date__lte=end_date
        )
        
        if not readings.exists():
            return Response(
                {'error': 'No readings found for this period'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Calculate summary
        stats = readings.aggregate(
            total_energy=Sum('energy_kwh'),
            avg_power=Avg('power_kw'),
            peak_power=Max('power_kw'),
            total_cost=Sum('cost'),
            count=Count('id')
        )
        
        # Create or update summary
        summary, created = UsageSummary.objects.update_or_create(
            user=request.user,
            period_type=period_type,
            start_date=start_date,
            defaults={
                'end_date': end_date,
                'total_energy_kwh': stats['total_energy'] or 0,
                'average_power_kw': stats['avg_power'] or 0,
                'peak_power_kw': stats['peak_power'] or 0,
                'total_cost': stats['total_cost'] or 0,
                'reading_count': stats['count'] or 0,
            }
        )
        
        serializer = self.get_serializer(summary)
        return Response(
            {
                'message': 'Summary generated successfully' if created else 'Summary updated',
                'data': serializer.data
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )