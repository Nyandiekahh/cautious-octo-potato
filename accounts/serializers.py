from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'address', 'city', 'country', 'meter_number',
            'balance', 'device_id', 'firmware_version', 'device_status',
            'notifications_enabled', 'low_balance_alert', 'usage_alert',
            'low_balance_threshold', 'usage_threshold', 'last_online',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'meter_number', 'balance', 'device_id', 
                           'firmware_version', 'last_online', 'created_at', 'updated_at']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 
                 'first_name', 'last_name', 'phone']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords don't match"})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        
        # Generate meter number
        user_count = User.objects.count()
        meter_number = f"SELP-2025-{str(user_count + 1).zfill(4)}"
        
        user = User.objects.create(
            **validated_data,
            meter_number=meter_number,
            device_id=f"DEV-{meter_number}"
        )
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include username and password')


class SettingsSerializer(serializers.ModelSerializer):
    """Serializer for user settings"""
    
    class Meta:
        model = User
        fields = [
            'notifications_enabled', 'low_balance_alert', 'usage_alert',
            'low_balance_threshold', 'usage_threshold', 'email', 'phone'
        ]