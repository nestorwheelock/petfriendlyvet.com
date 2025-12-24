"""Tests for the delivery app."""
from decimal import Decimal
from datetime import date, time, timedelta

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.apps import apps
from django.utils import timezone
from django.db import IntegrityError

from .models import DeliveryZone, DeliverySlot

User = get_user_model()


class DeliveryAppConfigTests(TestCase):
    """Tests for delivery app configuration."""

    def test_app_is_installed(self):
        """Delivery app should be in installed apps."""
        self.assertTrue(apps.is_installed('apps.delivery'))

    def test_app_name_correct(self):
        """App config should have correct name."""
        app_config = apps.get_app_config('delivery')
        self.assertEqual(app_config.name, 'apps.delivery')
        self.assertEqual(app_config.verbose_name, 'Delivery Management')


class DeliveryZoneTests(TestCase):
    """Tests for DeliveryZone model."""

    def test_create_zone(self):
        """Can create a delivery zone."""
        zone = DeliveryZone.objects.create(
            code='CENTRO',
            name='Centro Historico',
            delivery_fee=Decimal('50.00'),
            estimated_time_minutes=30
        )
        self.assertEqual(zone.code, 'CENTRO')
        self.assertTrue(zone.is_active)

    def test_zone_str(self):
        """Zone string representation."""
        zone = DeliveryZone.objects.create(code='NORTE', name='Zona Norte')
        self.assertEqual(str(zone), 'NORTE - Zona Norte')

    def test_zone_unique_code(self):
        """Zone codes must be unique."""
        DeliveryZone.objects.create(code='CENTRO', name='Centro')
        with self.assertRaises(IntegrityError):
            DeliveryZone.objects.create(code='CENTRO', name='Centro 2')

    def test_zone_default_values(self):
        """Zone default values are set correctly."""
        zone = DeliveryZone.objects.create(code='TEST', name='Test Zone')
        self.assertEqual(zone.delivery_fee, Decimal('50.00'))
        self.assertEqual(zone.estimated_time_minutes, 45)
        self.assertTrue(zone.is_active)


class DeliverySlotTests(TestCase):
    """Tests for DeliverySlot model."""

    def setUp(self):
        self.zone = DeliveryZone.objects.create(
            code='CENTRO',
            name='Centro',
            delivery_fee=Decimal('50.00')
        )

    def test_create_slot(self):
        """Can create a delivery slot."""
        slot = DeliverySlot.objects.create(
            zone=self.zone,
            date=date.today(),
            start_time=time(9, 0),
            end_time=time(12, 0),
            capacity=5
        )
        self.assertEqual(slot.booked_count, 0)
        self.assertEqual(slot.available_capacity, 5)

    def test_slot_availability(self):
        """Slot reports correct availability."""
        slot = DeliverySlot.objects.create(
            zone=self.zone,
            date=date.today(),
            start_time=time(9, 0),
            end_time=time(12, 0),
            capacity=2,
            booked_count=1
        )
        self.assertEqual(slot.available_capacity, 1)
        self.assertTrue(slot.is_available)

    def test_slot_full(self):
        """Full slot reports not available."""
        slot = DeliverySlot.objects.create(
            zone=self.zone,
            date=date.today(),
            start_time=time(9, 0),
            end_time=time(12, 0),
            capacity=2,
            booked_count=2
        )
        self.assertFalse(slot.is_available)

    def test_slot_str(self):
        """Slot string representation."""
        slot = DeliverySlot.objects.create(
            zone=self.zone,
            date=date(2024, 12, 25),
            start_time=time(9, 0),
            end_time=time(12, 0),
            capacity=5
        )
        self.assertIn('2024-12-25', str(slot))
        self.assertIn('09:00', str(slot))

    def test_slot_inactive_not_available(self):
        """Inactive slot reports not available."""
        slot = DeliverySlot.objects.create(
            zone=self.zone,
            date=date.today(),
            start_time=time(9, 0),
            end_time=time(12, 0),
            capacity=5,
            is_active=False
        )
        self.assertFalse(slot.is_available)
