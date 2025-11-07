from rest_framework import generics, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from .models import User
from .serializers import (
    UserSerializer, UserRegistrationSerializer, 
    LoginSerializer, SettingsSerializer
)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User operations"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Users can only see their own data"""
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user data"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """Update current user profile"""
        serializer = self.get_serializer(
            request.user, 
            data=request.data, 
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def settings(self, request):
        """Get or update user settings"""
        if request.method == 'GET':
            serializer = SettingsSerializer(request.user)
            return Response(serializer.data)
        else:
            serializer = SettingsSerializer(
                request.user,
                data=request.data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """User registration endpoint"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key,
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """User login endpoint"""
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        login(request, user)
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key,
            'message': 'Login successful'
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """User logout endpoint"""
    try:
        request.user.auth_token.delete()
    except:
        pass
    logout(request)
    return Response({'message': 'Logout successful'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics for current user"""
    user = request.user
    
    # Import here to avoid circular imports
    from energy_usage.models import EnergyReading
    from payments.models import Payment
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Sum
    
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    # Today's usage
    today_usage = EnergyReading.objects.filter(
        user=user,
        timestamp__date=today
    ).aggregate(total=Sum('energy_kwh'))['total'] or 0
    
    # Yesterday's usage
    yesterday_usage = EnergyReading.objects.filter(
        user=user,
        timestamp__date=yesterday
    ).aggregate(total=Sum('energy_kwh'))['total'] or 0
    
    # Current power draw (latest reading)
    latest_reading = EnergyReading.objects.filter(user=user).order_by('-timestamp').first()
    current_power = latest_reading.power_kw if latest_reading else 0
    
    # Last payment
    last_payment = Payment.objects.filter(user=user, status='success').order_by('-created_at').first()
    
    # Calculate estimated days left
    avg_daily_usage = EnergyReading.objects.filter(
        user=user,
        timestamp__gte=today - timedelta(days=7)
    ).aggregate(total=Sum('energy_kwh'))['total'] or 0
    avg_daily_usage = avg_daily_usage / 7 if avg_daily_usage > 0 else 1
    
    from django.conf import settings
    daily_cost = avg_daily_usage * settings.ENERGY_RATE_PER_KWH
    estimated_days = int(user.balance / daily_cost) if daily_cost > 0 else 0
    
    return Response({
        'current_power': round(current_power, 2),
        'balance': float(user.balance),
        'estimated_days': estimated_days,
        'today_usage': round(today_usage, 2),
        'yesterday_usage': round(yesterday_usage, 2),
        'usage_change_percent': round(
            ((today_usage - yesterday_usage) / yesterday_usage * 100) if yesterday_usage > 0 else 0,
            1
        ),
        'device_status': user.device_status,
        'last_payment': {
            'amount': float(last_payment.amount) if last_payment else 0,
            'date': last_payment.created_at if last_payment else None
        } if last_payment else None,
    })