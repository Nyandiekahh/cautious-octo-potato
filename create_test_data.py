"""
Script to create test data for the Smart Energy Logger system (Kenyan context)
Run with: python manage.py shell < create_test_data.py
"""

from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random
from decimal import Decimal

User = get_user_model()
from energy_usage.models import EnergyReading, UsageSummary
from payments.models import Payment, PaymentMethod
from notifications.models import Notification

# Create test user if doesn't exist
username = 'wanjiku'
email = 'wanjiku@example.co.ke'

if not User.objects.filter(username=username).exists():
    user = User.objects.create_user(
        username=username,
        email=email,
        password='testpass123',
        first_name='Wanjiku',
        last_name='Mwangi',
        phone='+254712345678',
        address='Riverside Drive, Westlands',
        city='Nairobi',
        country='Kenya',
        meter_number='KPLC-2025-001',
        device_id='DEV-KPLC-2025-001',
        balance=Decimal('5520.00')  # KES 5,520 (approx $45 at 123 KES/USD)
    )
    print(f"Created test user: {username}")
else:
    user = User.objects.get(username=username)
    print(f"Using existing user: {username}")

# Create energy readings for the past 30 days
print("Creating energy readings...")
now = timezone.now()
for days_ago in range(30):
    date = now - timedelta(days=days_ago)
    
    # Create 24 hourly readings for each day
    for hour in range(24):
        timestamp = date.replace(hour=hour, minute=0, second=0, microsecond=0)
        
        # Vary power based on time of day (Kenya peak hours: 6-10am, 6-11pm)
        if (6 <= hour <= 10) or (18 <= hour <= 23):
            # Peak hours - higher usage (cooking, heating, appliances)
            base_power = random.uniform(2.0, 3.5)
        elif 11 <= hour <= 17:
            # Day hours - moderate usage (lights off, some appliances)
            base_power = random.uniform(0.8, 1.8)
        else:
            # Night hours - low usage
            base_power = random.uniform(0.3, 0.8)
        
        energy_kwh = Decimal(str(round(base_power, 3)))
        power_kw = Decimal(str(round(base_power, 3)))
        voltage = Decimal('240.0')  # Kenya uses 240V
        
        # Fix: Convert power_kw to float for division
        current = Decimal(str(round(float(power_kw) / float(voltage) * 1000, 2)))
        
        EnergyReading.objects.create(
            user=user,
            timestamp=timestamp,
            energy_kwh=energy_kwh,
            power_kw=power_kw,
            voltage=voltage,
            current=current,
            battery_percentage=random.randint(60, 100),
            battery_status=random.choice(['charging', 'idle', 'full'])
        )

print(f"Created {EnergyReading.objects.filter(user=user).count()} energy readings")

# Create payment history (in KES)
print("Creating payment history...")
payment_data = [
    {'amount': 2460.00, 'method': 'mobile', 'days_ago': 5, 'desc': 'M-PESA top-up'},  # ~$20
    {'amount': 1845.00, 'method': 'mobile', 'days_ago': 10, 'desc': 'M-PESA top-up'},  # ~$15
    {'amount': 3075.00, 'method': 'mobile', 'days_ago': 15, 'desc': 'M-PESA top-up'},  # ~$25
    {'amount': 3690.00, 'method': 'card', 'days_ago': 20, 'desc': 'Card payment'},  # ~$30
    {'amount': 1230.00, 'method': 'mobile', 'days_ago': 25, 'desc': 'M-PESA top-up'},  # ~$10
]

for data in payment_data:
    created_at = now - timedelta(days=data['days_ago'])
    payment = Payment.objects.create(
        user=user,
        amount=Decimal(str(data['amount'])),
        payment_method=data['method'],
        status='success',
        transaction_id=f"MPESA-{random.randint(100000, 999999)}" if data['method'] == 'mobile' else f"CARD-{random.randint(10000, 99999)}",
        description=data['desc'],
        created_at=created_at,
        completed_at=created_at
    )

print(f"Created {Payment.objects.filter(user=user).count()} payments")

# Create payment methods
print("Creating payment methods...")
if not PaymentMethod.objects.filter(user=user).exists():
    # M-PESA payment method
    PaymentMethod.objects.create(
        user=user,
        method_type='mobile',
        is_default=True,
        mobile_number='+254712345678',
        mobile_provider='M-PESA (Safaricom)'
    )
    
    # Card payment method
    PaymentMethod.objects.create(
        user=user,
        method_type='card',
        is_default=False,
        card_last_four='5678',
        card_brand='Visa',
        card_expiry='12/2028'
    )
    print("Created 2 payment methods (M-PESA and Visa)")

# Create some notifications
print("Creating notifications...")
notification_data = [
    {
        'type': 'payment_success',
        'title': 'Payment Successful',
        'message': 'Your M-PESA payment of KES 2,460 has been processed successfully.',
        'days_ago': 5
    },
    {
        'type': 'low_balance',
        'title': 'Low Balance Alert',
        'message': 'Your current balance of KES 1,230 is below your threshold. Please top up soon to avoid power interruption.',
        'days_ago': 2
    },
    {
        'type': 'high_usage',
        'title': 'High Usage Alert',
        'message': 'Your energy usage during peak hours today exceeds your daily threshold. Consider using appliances during off-peak hours (11pm-6am) for lower rates.',
        'days_ago': 1
    },
    {
        'type': 'system',
        'title': 'KPLC Token Update',
        'message': 'Your prepaid electricity token has been updated. Current units: 87.5 kWh remaining.',
        'days_ago': 6
    },
]

for data in notification_data:
    created_at = now - timedelta(days=data['days_ago'])
    Notification.objects.create(
        user=user,
        notification_type=data['type'],
        title=data['title'],
        message=data['message'],
        created_at=created_at,
        is_read=data['days_ago'] > 2
    )

print(f"Created {Notification.objects.filter(user=user).count()} notifications")

print("\n" + "="*50)
print("Test data creation completed!")
print("="*50)
print(f"\nLogin credentials:")
print(f"Username: {username}")
print(f"Password: testpass123")
print(f"Email: {email}")
print(f"Phone: +254712345678")
print(f"Meter Number: KPLC-2025-001")
print(f"Current Balance: KES 5,520.00")
print(f"\nAccess the admin at: http://127.0.0.1:8000/admin/")
print(f"Access the API at: http://127.0.0.1:8000/api/")
print(f"\nNote: All amounts are in Kenyan Shillings (KES)")
print("Peak hours in Kenya: 6-10am and 6-11pm")
