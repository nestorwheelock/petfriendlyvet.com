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
