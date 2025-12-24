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
