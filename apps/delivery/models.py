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
