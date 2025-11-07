from rest_framework import serializers
from .models import Payment, PaymentMethod


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'reference', 'user', 'user_name', 'amount', 
            'payment_method', 'payment_method_display', 'status', 
            'status_display', 'transaction_id', 'description',
            'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'reference', 'user', 'status', 'transaction_id',
            'created_at', 'updated_at', 'completed_at'
        ]


class PaymentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating payments"""
    
    class Meta:
        model = Payment
        fields = ['amount', 'payment_method', 'description']
    
    def validate_amount(self, value):
        """Validate payment amount"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        if value > 1000:
            raise serializers.ValidationError("Amount cannot exceed $1000 per transaction")
        return value
    
    def create(self, validated_data):
        """Create payment with user from context"""
        validated_data['user'] = self.context['request'].user
        
        # Get IP address from request
        request = self.context['request']
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            validated_data['ip_address'] = x_forwarded_for.split(',')[0]
        else:
            validated_data['ip_address'] = request.META.get('REMOTE_ADDR')
        
        # Get user agent
        validated_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
        
        return super().create(validated_data)


class PaymentMethodSerializer(serializers.ModelSerializer):
    """Serializer for PaymentMethod model"""
    
    method_type_display = serializers.CharField(source='get_method_type_display', read_only=True)
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'method_type', 'method_type_display', 'is_default',
            'is_active', 'display_name', 'card_last_four', 'card_brand',
            'card_expiry', 'bank_name', 'account_number_last_four',
            'mobile_number', 'mobile_provider', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_display_name(self, obj):
        """Get display name for the payment method"""
        return str(obj)


class PaymentMethodCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating payment methods"""
    
    class Meta:
        model = PaymentMethod
        fields = [
            'method_type', 'is_default', 'card_last_four', 'card_brand',
            'card_expiry', 'bank_name', 'account_number_last_four',
            'mobile_number', 'mobile_provider', 'external_id'
        ]
    
    def create(self, validated_data):
        """Create payment method with user from context"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class PaymentStatsSerializer(serializers.Serializer):
    """Serializer for payment statistics"""
    total_payments = serializers.IntegerField()
    successful_payments = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_payment = serializers.DecimalField(max_digits=10, decimal_places=2)
    last_payment = PaymentSerializer(allow_null=True)