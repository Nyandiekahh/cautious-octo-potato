from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Avg, Count
from django.utils import timezone
from datetime import timedelta
from .models import Payment, PaymentMethod
from .serializers import (
    PaymentSerializer, PaymentCreateSerializer,
    PaymentMethodSerializer, PaymentMethodCreateSerializer,
    PaymentStatsSerializer
)


class PaymentViewSet(viewsets.ModelViewSet):
    """ViewSet for Payment operations"""
    queryset = Payment.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PaymentCreateSerializer
        return PaymentSerializer
    
    def get_queryset(self):
        """Filter payments by current user"""
        queryset = Payment.objects.filter(user=self.request.user)
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Create a new payment"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()
        
        # In a real application, you would integrate with a payment gateway here
        # For now, we'll simulate payment processing
        
        # Simulate successful payment (in production, this would be async)
        payment.status = 'processing'
        payment.transaction_id = f"TXN-{payment.reference}"
        payment.save()
        
        # Simulate immediate success (in production, this would be a webhook callback)
        # Comment this out to keep payments in 'processing' state
        payment.mark_as_success()
        
        response_serializer = PaymentSerializer(payment)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a pending payment"""
        payment = self.get_object()
        
        if payment.status not in ['pending', 'processing']:
            return Response(
                {'error': 'Only pending or processing payments can be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payment.status = 'cancelled'
        payment.save()
        
        serializer = self.get_serializer(payment)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get payment statistics"""
        queryset = self.get_queryset()
        
        stats = queryset.aggregate(
            total_payments=Count('id'),
            successful_payments=Count('id', filter=models.Q(status='success')),
            total_amount=Sum('amount', filter=models.Q(status='success')),
            average_payment=Avg('amount', filter=models.Q(status='success'))
        )
        
        # Get last successful payment
        last_payment = queryset.filter(status='success').order_by('-completed_at').first()
        
        data = {
            'total_payments': stats['total_payments'] or 0,
            'successful_payments': stats['successful_payments'] or 0,
            'total_amount': stats['total_amount'] or 0,
            'average_payment': stats['average_payment'] or 0,
            'last_payment': PaymentSerializer(last_payment).data if last_payment else None,
        }
        
        serializer = PaymentStatsSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get payment history with pagination"""
        queryset = self.get_queryset()
        
        # Get query parameters
        page_size = int(request.query_params.get('page_size', 10))
        page = int(request.query_params.get('page', 1))
        
        # Paginate
        start = (page - 1) * page_size
        end = start + page_size
        
        payments = queryset[start:end]
        total_count = queryset.count()
        
        serializer = self.get_serializer(payments, many=True)
        
        return Response({
            'count': total_count,
            'next': page + 1 if end < total_count else None,
            'previous': page - 1 if page > 1 else None,
            'results': serializer.data
        })


class PaymentMethodViewSet(viewsets.ModelViewSet):
    """ViewSet for PaymentMethod operations"""
    queryset = PaymentMethod.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PaymentMethodCreateSerializer
        return PaymentMethodSerializer
    
    def get_queryset(self):
        """Filter payment methods by current user"""
        return PaymentMethod.objects.filter(
            user=self.request.user,
            is_active=True
        )
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Set payment method as default"""
        payment_method = self.get_object()
        payment_method.is_default = True
        payment_method.save()
        
        serializer = self.get_serializer(payment_method)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a payment method"""
        payment_method = self.get_object()
        
        if payment_method.is_default:
            return Response(
                {'error': 'Cannot deactivate default payment method. Set another as default first.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payment_method.is_active = False
        payment_method.save()
        
        return Response({'message': 'Payment method deactivated successfully'})


# Import models for the stats action
from django.db import models