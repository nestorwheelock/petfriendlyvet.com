# Delivery Module

The `apps.delivery` module manages order delivery logistics including zones, time slots, drivers (employee or contractor), real-time tracking, proof of delivery, and customer ratings.

## Table of Contents

- [Overview](#overview)
- [Models](#models)
  - [DeliveryZone](#deliveryzone)
  - [DeliverySlot](#deliveryslot)
  - [DeliveryDriver](#deliverydriver)
  - [Delivery](#delivery)
  - [DeliveryStatusHistory](#deliverystatushistory)
  - [DeliveryProof](#deliveryproof)
  - [DeliveryRating](#deliveryrating)
  - [DeliveryNotification](#deliverynotification)
- [Views](#views)
- [URL Patterns](#url-patterns)
- [Workflows](#workflows)
  - [Delivery Lifecycle](#delivery-lifecycle)
  - [Driver Assignment](#driver-assignment)
  - [Status Transitions](#status-transitions)
  - [Proof of Delivery](#proof-of-delivery)
- [Driver Types](#driver-types)
- [Status Flow](#status-flow)
- [Integration Points](#integration-points)
- [Query Examples](#query-examples)
- [Testing](#testing)

## Overview

The delivery module provides comprehensive delivery management:

- **Delivery Zones** - Geographic areas with fees and ETAs
- **Time Slots** - Capacity-managed delivery windows
- **Driver Management** - Employee and contractor drivers
- **Real-Time Tracking** - GPS location updates
- **Proof of Delivery** - Photos, signatures, GPS verification
- **Customer Ratings** - Post-delivery feedback

```
┌─────────────────────────────────────────────────────────────┐
│                   DELIVERY LIFECYCLE                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌───────────┐    ┌───────────┐    ┌───────────┐          │
│   │  Order    │───>│  Pending  │───>│ Assigned  │          │
│   │  Created  │    │           │    │           │          │
│   └───────────┘    └───────────┘    └─────┬─────┘          │
│                                           │                 │
│                                           ▼                 │
│   ┌───────────┐    ┌───────────┐    ┌───────────┐          │
│   │ Delivered │<───│  Arrived  │<───│ Picked Up │          │
│   │           │    │           │    │           │          │
│   └───────────┘    └───────────┘    └───────────┘          │
│        │                                                    │
│        ▼                                                    │
│   ┌───────────┐    ┌───────────┐                           │
│   │  Rating   │    │   Proof   │                           │
│   │ Feedback  │    │   Photo   │                           │
│   └───────────┘    └───────────┘                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Models

Location: `apps/delivery/models.py`

### DeliveryZone

Geographic delivery zones with specific fees and ETAs.

```python
class DeliveryZone(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    name_es = models.CharField(max_length=100, blank=True)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('50.00'))
    estimated_time_minutes = models.PositiveIntegerField(default=45)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `code` | CharField | Unique zone identifier (e.g., "CDMX-NORTE") |
| `delivery_fee` | Decimal | Delivery charge in MXN |
| `estimated_time_minutes` | Integer | Expected delivery time |

### DeliverySlot

Time slots for delivery scheduling with capacity management.

```python
class DeliverySlot(models.Model):
    zone = models.ForeignKey(DeliveryZone, on_delete=models.CASCADE, related_name='slots')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    capacity = models.PositiveIntegerField(default=5)
    booked_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    @property
    def available_capacity(self):
        return max(0, self.capacity - self.booked_count)

    @property
    def is_available(self):
        return self.is_active and self.available_capacity > 0
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `capacity` | Integer | Max deliveries in this slot |
| `booked_count` | Integer | Current bookings |
| `available_capacity` | Property | Remaining capacity |

### DeliveryDriver

Driver profiles supporting both employees and contractors.

```python
DRIVER_TYPES = [
    ('employee', 'Clinic Employee'),
    ('contractor', 'Independent Contractor'),
]

VEHICLE_TYPES = [
    ('motorcycle', 'Motorcycle'),
    ('car', 'Car'),
    ('bicycle', 'Bicycle'),
    ('walk', 'On Foot'),
]

class DeliveryDriver(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='delivery_driver')
    driver_type = models.CharField(max_length=20, choices=DRIVER_TYPES, default='employee')
    phone = models.CharField(max_length=20, blank=True)

    # Mexican tax IDs (required for contractors)
    rfc = models.CharField(max_length=13, blank=True)
    curp = models.CharField(max_length=18, blank=True)

    # Payment rates for contractors
    rate_per_delivery = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    rate_per_km = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    # Contractor onboarding
    contract_signed = models.BooleanField(default=False)
    contract_document = models.FileField(upload_to='driver_contracts/', null=True)
    id_document = models.FileField(upload_to='driver_ids/', null=True)
    onboarding_status = models.CharField(max_length=20, choices=[...], default='pending')

    # Vehicle info
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES, default='motorcycle')
    license_plate = models.CharField(max_length=20, blank=True)

    # Zones covered
    zones = models.ManyToManyField(DeliveryZone, blank=True, related_name='drivers')

    # Status
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=False)

    # Real-time location
    current_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    current_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    location_updated_at = models.DateTimeField(null=True)

    # Capacity and performance
    max_deliveries_per_day = models.PositiveIntegerField(default=10)
    total_deliveries = models.PositiveIntegerField(default=0)
    successful_deliveries = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('5.00'))
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `driver_type` | CharField | Employee or contractor |
| `rfc` / `curp` | CharField | Mexican tax IDs for contractors |
| `rate_per_delivery` | Decimal | Contractor payment rate |
| `onboarding_status` | CharField | Contractor approval status |
| `current_latitude/longitude` | Decimal | Real-time GPS location |
| `average_rating` | Decimal | Customer rating average |

### Delivery

Main delivery record linking order to execution.

```python
DELIVERY_STATUSES = [
    ('pending', 'Pending'),
    ('assigned', 'Assigned'),
    ('picked_up', 'Picked Up'),
    ('out_for_delivery', 'Out for Delivery'),
    ('arrived', 'Arrived'),
    ('delivered', 'Delivered'),
    ('failed', 'Failed'),
    ('returned', 'Returned'),
]

class Delivery(models.Model):
    delivery_number = models.CharField(max_length=20, unique=True, editable=False)
    order = models.OneToOneField('store.Order', on_delete=models.CASCADE, related_name='delivery')
    driver = models.ForeignKey(DeliveryDriver, on_delete=models.SET_NULL, null=True, related_name='deliveries')
    slot = models.ForeignKey(DeliverySlot, on_delete=models.SET_NULL, null=True)
    zone = models.ForeignKey(DeliveryZone, on_delete=models.SET_NULL, null=True)

    status = models.CharField(max_length=20, choices=DELIVERY_STATUSES, default='pending')

    # Address and coordinates
    address = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)

    # Scheduling
    scheduled_date = models.DateField(null=True)
    scheduled_time_start = models.TimeField(null=True)
    scheduled_time_end = models.TimeField(null=True)

    # Status timestamps
    assigned_at = models.DateTimeField(null=True)
    picked_up_at = models.DateTimeField(null=True)
    out_for_delivery_at = models.DateTimeField(null=True)
    arrived_at = models.DateTimeField(null=True)
    delivered_at = models.DateTimeField(null=True)
    failed_at = models.DateTimeField(null=True)

    # Failure info
    failure_reason = models.TextField(blank=True)

    # Distance for contractor payment
    delivered_distance_km = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    # Notes
    notes = models.TextField(blank=True)
    driver_notes = models.TextField(blank=True)
```

**Key Methods:**

```python
def _generate_delivery_number(self):
    """Generate unique delivery number: DEL-2025-12-00001"""

def _change_status(self, new_status, changed_by=None, latitude=None, longitude=None):
    """Change status with validation and history tracking."""

def assign_driver(self, driver, assigned_by=None):
    """Assign driver to delivery."""

def mark_picked_up(self, changed_by=None, latitude=None, longitude=None):
def mark_out_for_delivery(self, changed_by=None, latitude=None, longitude=None):
def mark_arrived(self, changed_by=None, latitude=None, longitude=None):
def mark_delivered(self, changed_by=None, latitude=None, longitude=None):
def mark_failed(self, reason, changed_by=None, latitude=None, longitude=None):
```

### DeliveryStatusHistory

Audit trail for delivery status changes.

```python
class DeliveryStatusHistory(models.Model):
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='status_history')
    from_status = models.CharField(max_length=20, choices=DELIVERY_STATUSES)
    to_status = models.CharField(max_length=20, choices=DELIVERY_STATUSES)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### DeliveryProof

Proof of delivery (photo or signature with GPS verification).

```python
PROOF_TYPES = [
    ('photo', 'Photo'),
    ('signature', 'Signature'),
]

class DeliveryProof(models.Model):
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='proofs')
    proof_type = models.CharField(max_length=20, choices=PROOF_TYPES)
    image = models.ImageField(upload_to='delivery_proofs/', null=True)
    signature_data = models.TextField(blank=True)  # Base64 encoded
    recipient_name = models.CharField(max_length=100, blank=True)

    # GPS verification
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    gps_accuracy = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
```

### DeliveryRating

Customer rating for a delivery.

```python
class DeliveryRating(models.Model):
    delivery = models.OneToOneField(Delivery, on_delete=models.CASCADE, related_name='rating')
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### DeliveryNotification

Track notifications sent for deliveries.

```python
NOTIFICATION_TYPES = [
    ('sms', 'SMS'),
    ('whatsapp', 'WhatsApp'),
    ('email', 'Email'),
    ('push', 'Push Notification'),
]

class DeliveryNotification(models.Model):
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    recipient = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=[...], default='pending')
    external_id = models.CharField(max_length=100, blank=True)
    sent_at = models.DateTimeField(null=True)
    delivered_at = models.DateTimeField(null=True)
    error_message = models.TextField(blank=True)
```

## Views

Location: `apps/delivery/views.py`

### DriverRequiredMixin

Ensures user is an active driver.

```python
class DriverRequiredMixin(LoginRequiredMixin):
    """Mixin to ensure user is an active driver."""

    def dispatch(self, request, *args, **kwargs):
        try:
            self.driver = request.user.delivery_driver
            if not self.driver.is_active:
                return HttpResponseForbidden("Driver account is inactive")
        except DeliveryDriver.DoesNotExist:
            return HttpResponseForbidden("User is not a driver")
        return super().dispatch(request, *args, **kwargs)
```

### DriverDashboardView

Driver mobile dashboard.

```python
class DriverDashboardView(DriverRequiredMixin, View):
    """Driver mobile dashboard showing assigned deliveries."""

    def get(self, request):
        deliveries = Delivery.objects.filter(
            driver=self.driver
        ).exclude(
            status__in=['delivered', 'returned']
        ).order_by('scheduled_date', 'scheduled_time_start')

        return render(request, 'delivery/driver/dashboard.html', {...})
```

### DeliveryTrackingView

Customer-facing delivery tracking.

```python
class DeliveryTrackingView(LoginRequiredMixin, View):
    """Customer-facing delivery tracking page."""

    def get(self, request, delivery_number):
        delivery = get_object_or_404(Delivery, delivery_number=delivery_number)

        # Ensure user owns this delivery
        if delivery.order.user != request.user:
            raise Http404("Delivery not found")

        # Build timeline for status display
        timeline = [...]

        return render(request, 'delivery/tracking.html', {...})
```

## URL Patterns

Location: `apps/delivery/urls.py`

```python
app_name = 'delivery'

urlpatterns = [
    # Driver-facing
    path('driver/dashboard/', DriverDashboardView.as_view(), name='driver_dashboard'),

    # Customer-facing
    path('track/<str:delivery_number>/', DeliveryTrackingView.as_view(), name='tracking'),

    # Admin
    path('admin/', include('apps.delivery.admin_urls')),
]
```

## Workflows

### Delivery Lifecycle

```python
from apps.delivery.models import Delivery, DeliveryDriver

# 1. Order placed - delivery created
delivery = Delivery.objects.create(
    order=order,
    zone=zone,
    address=order.shipping_address,
    scheduled_date=selected_date,
    scheduled_time_start=slot.start_time,
    scheduled_time_end=slot.end_time,
)
# delivery_number auto-generated: DEL-2025-12-00001

# 2. Assign driver
driver = DeliveryDriver.objects.filter(
    is_active=True,
    is_available=True,
    zones=zone
).first()

delivery.assign_driver(driver, assigned_by=admin_user)
# Status: pending → assigned
# assigned_at set
# History record created

# 3. Driver picks up order
delivery.mark_picked_up(
    changed_by=driver.user,
    latitude=19.4326,
    longitude=-99.1332
)
# Status: assigned → picked_up

# 4. Driver leaves for delivery
delivery.mark_out_for_delivery(changed_by=driver.user, latitude=..., longitude=...)

# 5. Driver arrives
delivery.mark_arrived(changed_by=driver.user, latitude=..., longitude=...)

# 6. Delivery completed
delivery.mark_delivered(changed_by=driver.user, latitude=..., longitude=...)

# OR 6b. Delivery failed
delivery.mark_failed(
    reason="Customer not home, no safe place to leave package",
    changed_by=driver.user,
    latitude=...,
    longitude=...
)
```

### Driver Assignment

```python
from apps.delivery.models import DeliveryDriver, Delivery

# Find available drivers for a zone
available_drivers = DeliveryDriver.objects.filter(
    is_active=True,
    is_available=True,
    zones=delivery.zone,
    onboarding_status='approved',  # For contractors
).exclude(
    # Exclude drivers at capacity
    deliveries__status__in=['assigned', 'picked_up', 'out_for_delivery', 'arrived']
)

# Sort by rating
driver = available_drivers.order_by('-average_rating').first()

# Assign
delivery.assign_driver(driver, assigned_by=admin_user)
```

### Status Transitions

Valid status transitions are enforced:

```python
VALID_TRANSITIONS = {
    'pending': ['assigned'],
    'assigned': ['picked_up', 'pending'],  # Can unassign
    'picked_up': ['out_for_delivery'],
    'out_for_delivery': ['arrived', 'failed'],
    'arrived': ['delivered', 'failed'],
    'failed': ['returned', 'assigned'],  # Can retry
    'returned': [],  # Terminal
    'delivered': [],  # Terminal
}
```

### Proof of Delivery

```python
from apps.delivery.models import DeliveryProof

# Photo proof
proof = DeliveryProof.objects.create(
    delivery=delivery,
    proof_type='photo',
    image=uploaded_photo,
    latitude=19.4326,
    longitude=-99.1332,
    gps_accuracy=10.5,  # meters
)

# Signature proof
proof = DeliveryProof.objects.create(
    delivery=delivery,
    proof_type='signature',
    signature_data=base64_signature,
    recipient_name='Juan García',
    latitude=19.4326,
    longitude=-99.1332,
)
```

## Driver Types

| Type | Description | Payment | Requirements |
|------|-------------|---------|--------------|
| `employee` | Clinic staff member | Salary | Staff profile |
| `contractor` | Independent contractor | Per delivery + km | RFC, CURP, contract |

### Contractor Onboarding

```python
ONBOARDING_STATUS = [
    ('pending', 'Pending'),
    ('documents_submitted', 'Documents Submitted'),
    ('under_review', 'Under Review'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
]

# Contractor must have:
# - RFC (Tax ID)
# - CURP (Personal ID)
# - Signed contract
# - ID document
# - Approved onboarding status
```

## Status Flow

```
                    ┌─────────────┐
                    │   pending   │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
        ┌──────────│  assigned   │
        │          └──────┬──────┘
        │                 │
        │ (unassign)      ▼
        │          ┌─────────────┐
        │          │  picked_up  │
        │          └──────┬──────┘
        │                 │
        │                 ▼
        │          ┌─────────────────┐
        │          │ out_for_delivery│
        │          └────────┬────────┘
        │                   │
        │         ┌─────────┴─────────┐
        │         ▼                   ▼
        │   ┌──────────┐        ┌──────────┐
        │   │  arrived │        │  failed  │───────┐
        │   └────┬─────┘        └────┬─────┘       │
        │        │                   │             │
        │        ▼                   ▼             ▼
        │   ┌──────────┐        ┌──────────┐  ┌──────────┐
        └───│ delivered│        │ returned │  │(reassign)│
            └──────────┘        └──────────┘  └──────────┘
```

## Integration Points

### With Store Module

```python
from apps.store.models import Order
from apps.delivery.models import Delivery

# Create delivery when order is placed
def on_order_placed(order):
    if order.requires_delivery:
        delivery = Delivery.objects.create(
            order=order,
            zone=determine_zone(order.shipping_address),
            address=order.shipping_address,
        )

# Access delivery from order
order = Order.objects.get(pk=order_id)
if hasattr(order, 'delivery'):
    print(f"Delivery status: {order.delivery.status}")
```

### With Notifications Module

```python
from apps.delivery.models import Delivery, DeliveryNotification
from apps.notifications.services import NotificationService

# Send delivery update
def notify_customer_status_change(delivery, new_status):
    message = f"Tu pedido {delivery.delivery_number} está: {new_status}"

    # In-app notification
    NotificationService.create_notification(
        user=delivery.order.user,
        notification_type='system',
        title='Actualización de Entrega',
        message=message,
    )

    # Track SMS/WhatsApp
    DeliveryNotification.objects.create(
        delivery=delivery,
        notification_type='whatsapp',
        recipient=delivery.order.user.phone_number,
        message=message,
    )
```

### With Billing Module

```python
from apps.delivery.models import Delivery, DeliveryDriver
from apps.billing.models import Invoice

# Calculate contractor payment
def calculate_driver_payment(driver, period_start, period_end):
    deliveries = Delivery.objects.filter(
        driver=driver,
        status='delivered',
        delivered_at__date__range=[period_start, period_end],
    )

    total = Decimal('0')
    for d in deliveries:
        # Base rate per delivery
        total += driver.rate_per_delivery or Decimal('0')
        # Plus distance rate
        if d.delivered_distance_km and driver.rate_per_km:
            total += d.delivered_distance_km * driver.rate_per_km

    return total
```

## Query Examples

### Delivery Queries

```python
from apps.delivery.models import Delivery
from django.utils import timezone
from datetime import date

# Today's pending deliveries
pending_today = Delivery.objects.filter(
    status='pending',
    scheduled_date=date.today()
)

# Active deliveries (in progress)
active = Delivery.objects.filter(
    status__in=['assigned', 'picked_up', 'out_for_delivery', 'arrived']
).select_related('driver', 'order')

# Failed deliveries needing attention
failed = Delivery.objects.filter(
    status='failed'
).order_by('-failed_at')

# Deliveries by driver
driver_deliveries = Delivery.objects.filter(
    driver=driver,
    status='delivered',
    delivered_at__date=date.today()
)
```

### Driver Queries

```python
from apps.delivery.models import DeliveryDriver
from django.db.models import Count, Avg

# Available drivers for zone
available = DeliveryDriver.objects.filter(
    is_active=True,
    is_available=True,
    zones=zone,
)

# Top-rated drivers
top_rated = DeliveryDriver.objects.filter(
    is_active=True,
    total_deliveries__gte=10,  # Minimum deliveries
).order_by('-average_rating')[:10]

# Contractors pending approval
pending_contractors = DeliveryDriver.objects.filter(
    driver_type='contractor',
    onboarding_status__in=['pending', 'documents_submitted', 'under_review'],
)

# Driver performance
performance = DeliveryDriver.objects.annotate(
    success_rate=Count('deliveries', filter=Q(deliveries__status='delivered')) * 100.0 /
                 Count('deliveries', filter=Q(deliveries__status__in=['delivered', 'failed']))
).order_by('-success_rate')
```

### Slot Queries

```python
from apps.delivery.models import DeliverySlot
from datetime import date, timedelta

# Available slots for next 7 days
available_slots = DeliverySlot.objects.filter(
    zone=zone,
    is_active=True,
    date__gte=date.today(),
    date__lte=date.today() + timedelta(days=7),
    booked_count__lt=F('capacity'),
).order_by('date', 'start_time')

# Fully booked slots today
full_slots = DeliverySlot.objects.filter(
    date=date.today(),
    booked_count__gte=F('capacity'),
)
```

## Testing

### Unit Tests

Location: `tests/test_delivery.py`

```bash
# Run delivery unit tests
python -m pytest tests/test_delivery.py -v
```

### Browser Tests

Location: `tests/e2e/browser/test_delivery.py`

```bash
# Run delivery browser tests
python -m pytest tests/e2e/browser/test_delivery.py -v

# Run with visible browser
python -m pytest tests/e2e/browser/test_delivery.py -v --headed --slowmo=500
```

### Key Test Scenarios

1. **Delivery Creation**
   - Auto-generate delivery number
   - Link to order correctly
   - Set initial status to pending

2. **Status Transitions**
   - Valid transitions work
   - Invalid transitions rejected
   - Timestamps updated correctly
   - History records created

3. **Driver Assignment**
   - Assign available driver
   - Update driver availability
   - Track assignment history

4. **Proof of Delivery**
   - Upload photo proof
   - Capture signature
   - GPS coordinates stored

5. **Customer Tracking**
   - View delivery status
   - Timeline displays correctly
   - Only own deliveries visible

6. **Driver Dashboard**
   - Shows assigned deliveries
   - Excludes completed deliveries
   - Driver authentication required
