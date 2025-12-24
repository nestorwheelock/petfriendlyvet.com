"""Delivery management models.

Provides:
- DeliveryZone: Geographic delivery zones with fees
- DeliverySlot: Time slots for delivery scheduling
- DeliveryDriver: Driver profiles (employee/contractor)
- Delivery: Main delivery record linking order to execution
- DeliveryStatusHistory: Audit trail for status changes
- DeliveryProof: Photos, signatures, GPS verification
- DeliveryRating: Customer ratings and feedback
- DeliveryNotification: Track sent notifications
"""
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class DeliveryZone(models.Model):
    """Geographic delivery zone with specific fees and ETAs."""

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    name_es = models.CharField(max_length=100, blank=True)
    delivery_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('50.00')
    )
    estimated_time_minutes = models.PositiveIntegerField(
        default=45,
        help_text="Estimated delivery time in minutes"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class DeliverySlot(models.Model):
    """Time slot for delivery scheduling."""

    zone = models.ForeignKey(
        DeliveryZone,
        on_delete=models.CASCADE,
        related_name='slots'
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    capacity = models.PositiveIntegerField(default=5)
    booked_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'start_time']
        unique_together = ['zone', 'date', 'start_time']

    def __str__(self):
        return f"{self.date} {self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')} ({self.zone.code})"

    @property
    def available_capacity(self):
        return max(0, self.capacity - self.booked_count)

    @property
    def is_available(self):
        return self.is_active and self.available_capacity > 0


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
    """Driver profile for deliveries (employee or contractor)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='delivery_driver'
    )
    driver_type = models.CharField(
        max_length=20,
        choices=DRIVER_TYPES,
        default='employee'
    )
    phone = models.CharField(max_length=20, blank=True)

    # Employee fields - link to staff profile (optional)
    # staff_profile = models.ForeignKey(
    #     'practice.StaffProfile',
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True,
    #     related_name='delivery_driver'
    # )

    # Contractor fields (A/P integration) - link to vendor (optional)
    # vendor = models.ForeignKey(
    #     'accounting.Vendor',
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True,
    #     related_name='delivery_drivers'
    # )

    # Mexican tax IDs (required for contractors)
    rfc = models.CharField(max_length=13, blank=True, help_text="RFC (Tax ID)")
    curp = models.CharField(max_length=18, blank=True, help_text="CURP (Personal ID)")

    # Payment rates for contractors
    rate_per_delivery = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    rate_per_km = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Contractor onboarding
    contract_signed = models.BooleanField(default=False)
    contract_document = models.FileField(
        upload_to='driver_contracts/',
        null=True,
        blank=True
    )
    id_document = models.FileField(
        upload_to='driver_ids/',
        null=True,
        blank=True
    )

    # Vehicle info
    vehicle_type = models.CharField(
        max_length=20,
        choices=VEHICLE_TYPES,
        default='motorcycle'
    )
    license_plate = models.CharField(max_length=20, blank=True)

    # Zones this driver covers
    zones = models.ManyToManyField(
        DeliveryZone,
        blank=True,
        related_name='drivers'
    )

    # Status
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=False)

    # Current location (real-time tracking)
    current_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    current_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    location_updated_at = models.DateTimeField(null=True, blank=True)

    # Performance metrics
    total_deliveries = models.PositiveIntegerField(default=0)
    successful_deliveries = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal('5.00')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_available', 'user__first_name']

    def __str__(self):
        name = self.user.get_full_name() or self.user.username
        return f"{name} ({self.get_driver_type_display()})"

    @property
    def is_employee(self):
        return self.driver_type == 'employee'

    @property
    def is_contractor(self):
        return self.driver_type == 'contractor'

    @property
    def has_complete_payment_info(self):
        """Check if contractor has complete payment info."""
        if self.is_employee:
            return True
        return bool(self.rfc and self.rate_per_delivery)


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

VALID_TRANSITIONS = {
    'pending': ['assigned'],
    'assigned': ['picked_up', 'pending'],
    'picked_up': ['out_for_delivery'],
    'out_for_delivery': ['arrived', 'failed'],
    'arrived': ['delivered', 'failed'],
    'failed': ['returned', 'assigned'],
    'returned': [],
    'delivered': [],
}


class Delivery(models.Model):
    """Main delivery record linking order to execution."""

    delivery_number = models.CharField(max_length=20, unique=True, editable=False)
    order = models.OneToOneField(
        'store.Order',
        on_delete=models.CASCADE,
        related_name='delivery'
    )
    driver = models.ForeignKey(
        DeliveryDriver,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deliveries'
    )
    slot = models.ForeignKey(
        DeliverySlot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deliveries'
    )
    zone = models.ForeignKey(
        DeliveryZone,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deliveries'
    )

    status = models.CharField(
        max_length=20,
        choices=DELIVERY_STATUSES,
        default='pending'
    )

    # Address
    address = models.TextField(blank=True)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )

    # Scheduling
    scheduled_date = models.DateField(null=True, blank=True)
    scheduled_time_start = models.TimeField(null=True, blank=True)
    scheduled_time_end = models.TimeField(null=True, blank=True)

    # Status timestamps
    assigned_at = models.DateTimeField(null=True, blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    out_for_delivery_at = models.DateTimeField(null=True, blank=True)
    arrived_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)

    # Failure info
    failure_reason = models.TextField(blank=True)

    # Notes
    notes = models.TextField(blank=True)
    driver_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.delivery_number

    def save(self, *args, **kwargs):
        if not self.delivery_number:
            self.delivery_number = self._generate_delivery_number()
        super().save(*args, **kwargs)

    def _generate_delivery_number(self):
        """Generate unique delivery number."""
        from datetime import datetime
        prefix = datetime.now().strftime('DEL-%Y-%m')
        last = Delivery.objects.filter(
            delivery_number__startswith=prefix
        ).order_by('-delivery_number').first()

        if last:
            last_num = int(last.delivery_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        return f"{prefix}-{new_num:05d}"

    def _change_status(self, new_status, changed_by=None, latitude=None, longitude=None):
        """Change status with validation and history."""
        if new_status not in VALID_TRANSITIONS.get(self.status, []):
            raise ValueError(
                f"Cannot transition from {self.status} to {new_status}"
            )

        old_status = self.status
        self.status = new_status

        # Update timestamp
        now = timezone.now()
        timestamp_field = f"{new_status}_at"
        if hasattr(self, timestamp_field):
            setattr(self, timestamp_field, now)

        self.save()

        # Create history
        DeliveryStatusHistory.objects.create(
            delivery=self,
            from_status=old_status,
            to_status=new_status,
            changed_by=changed_by,
            latitude=latitude,
            longitude=longitude
        )

    def assign_driver(self, driver, assigned_by=None):
        """Assign driver to delivery."""
        self.driver = driver
        self._change_status('assigned', assigned_by)

    def mark_picked_up(self, changed_by=None, latitude=None, longitude=None):
        self._change_status('picked_up', changed_by, latitude, longitude)

    def mark_out_for_delivery(self, changed_by=None, latitude=None, longitude=None):
        self._change_status('out_for_delivery', changed_by, latitude, longitude)

    def mark_arrived(self, changed_by=None, latitude=None, longitude=None):
        self._change_status('arrived', changed_by, latitude, longitude)

    def mark_delivered(self, changed_by=None, latitude=None, longitude=None):
        self._change_status('delivered', changed_by, latitude, longitude)

    def mark_failed(self, reason, changed_by=None, latitude=None, longitude=None):
        self.failure_reason = reason
        self._change_status('failed', changed_by, latitude, longitude)


class DeliveryStatusHistory(models.Model):
    """Audit trail for delivery status changes."""

    delivery = models.ForeignKey(
        Delivery,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    from_status = models.CharField(max_length=20, choices=DELIVERY_STATUSES)
    to_status = models.CharField(max_length=20, choices=DELIVERY_STATUSES)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name_plural = "Delivery status histories"

    def __str__(self):
        return f"{self.delivery}: {self.from_status} → {self.to_status}"


PROOF_TYPES = [
    ('photo', 'Photo'),
    ('signature', 'Signature'),
]


class DeliveryProof(models.Model):
    """Proof of delivery (photo or signature with GPS)."""

    delivery = models.ForeignKey(
        Delivery,
        on_delete=models.CASCADE,
        related_name='proofs'
    )
    proof_type = models.CharField(max_length=20, choices=PROOF_TYPES)
    image = models.ImageField(
        upload_to='delivery_proofs/',
        null=True,
        blank=True
    )
    signature_data = models.TextField(blank=True, help_text="Base64 encoded signature")
    recipient_name = models.CharField(max_length=100, blank=True)

    # GPS from browser Geolocation API
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    gps_accuracy = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="GPS accuracy in meters"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.delivery.delivery_number} - {self.proof_type}"


class DeliveryRating(models.Model):
    """Customer rating for a delivery."""

    delivery = models.OneToOneField(
        Delivery,
        on_delete=models.CASCADE,
        related_name='rating'
    )
    rating = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.delivery.delivery_number}: {self.rating} stars"


NOTIFICATION_TYPES = [
    ('sms', 'SMS'),
    ('whatsapp', 'WhatsApp'),
    ('email', 'Email'),
    ('push', 'Push Notification'),
]

NOTIFICATION_STATUSES = [
    ('pending', 'Pending'),
    ('sent', 'Sent'),
    ('delivered', 'Delivered'),
    ('failed', 'Failed'),
]


class DeliveryNotification(models.Model):
    """Track notifications sent for a delivery."""

    delivery = models.ForeignKey(
        Delivery,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    recipient = models.CharField(max_length=200, help_text="Phone number or email")
    message = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=NOTIFICATION_STATUSES,
        default='pending'
    )
    external_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="ID from SMS/WhatsApp provider"
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.delivery.delivery_number} - {self.notification_type}"
