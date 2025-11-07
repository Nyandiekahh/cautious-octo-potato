from rest_framework import serializers
from .models import EnergyReading, UsageSummary


class EnergyReadingSerializer(serializers.ModelSerializer):
    """Serializer for EnergyReading model"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = EnergyReading
        fields = [
            'id', 'user', 'user_name', 'timestamp', 'energy_kwh', 
            'power_kw', 'voltage', 'current', 'cost', 
            'battery_percentage', 'battery_status', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'cost', 'created_at']
    
    def create(self, validated_data):
        # Set user from request context
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class EnergyReadingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating energy readings (simplified)"""
    
    class Meta:
        model = EnergyReading
        fields = ['energy_kwh', 'power_kw', 'voltage', 'current', 
                 'battery_percentage', 'battery_status', 'timestamp']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class UsageSummarySerializer(serializers.ModelSerializer):
    """Serializer for UsageSummary model"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = UsageSummary
        fields = [
            'id', 'user', 'user_name', 'period_type', 'start_date', 
            'end_date', 'total_energy_kwh', 'average_power_kw', 
            'peak_power_kw', 'total_cost', 'reading_count', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class ChartDataSerializer(serializers.Serializer):
    """Serializer for chart data"""
    labels = serializers.ListField(child=serializers.CharField())
    datasets = serializers.ListField()


class UsageStatsSerializer(serializers.Serializer):
    """Serializer for usage statistics"""
    today = serializers.DecimalField(max_digits=10, decimal_places=2)
    yesterday = serializers.DecimalField(max_digits=10, decimal_places=2)
    this_week = serializers.DecimalField(max_digits=10, decimal_places=2)
    this_month = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_daily = serializers.DecimalField(max_digits=10, decimal_places=2)
    peak_power = serializers.DecimalField(max_digits=10, decimal_places=2)