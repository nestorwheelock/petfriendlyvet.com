"""Tests for the delivery app."""
from decimal import Decimal
from datetime import date, time, timedelta

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.apps import apps
from django.utils import timezone
from django.db import IntegrityError

from .models import DeliveryZone, DeliverySlot, DeliveryDriver

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


class DeliveryDriverTests(TestCase):
    """Tests for DeliveryDriver model."""

    def test_create_employee_driver(self):
        """Can create an employee driver."""
        user = User.objects.create_user('driver1', 'driver1@test.com', 'pass')
        driver = DeliveryDriver.objects.create(
            user=user,
            driver_type='employee',
            phone='+525551234567'
        )
        self.assertEqual(driver.driver_type, 'employee')
        self.assertTrue(driver.is_employee)
        self.assertFalse(driver.is_contractor)

    def test_create_contractor_driver(self):
        """Can create a contractor driver with RFC/CURP."""
        user = User.objects.create_user('driver2', 'driver2@test.com', 'pass')
        driver = DeliveryDriver.objects.create(
            user=user,
            driver_type='contractor',
            phone='+525551234567',
            rfc='XAXX010101000',
            curp='XEXX010101HNEXXXA4',
            rate_per_delivery=Decimal('35.00')
        )
        self.assertEqual(driver.driver_type, 'contractor')
        self.assertTrue(driver.is_contractor)
        self.assertFalse(driver.is_employee)
        self.assertEqual(driver.rfc, 'XAXX010101000')

    def test_driver_zones_relationship(self):
        """Driver can be assigned to multiple zones."""
        user = User.objects.create_user('driver3', 'driver3@test.com', 'pass')
        driver = DeliveryDriver.objects.create(user=user, driver_type='employee')

        zone1 = DeliveryZone.objects.create(code='CENTRO', name='Centro')
        zone2 = DeliveryZone.objects.create(code='NORTE', name='Norte')

        driver.zones.add(zone1, zone2)
        self.assertEqual(driver.zones.count(), 2)

    def test_driver_availability(self):
        """Driver availability status."""
        user = User.objects.create_user('driver4', 'driver4@test.com', 'pass')
        driver = DeliveryDriver.objects.create(
            user=user,
            driver_type='employee',
            is_active=True,
            is_available=True
        )
        self.assertTrue(driver.is_active)
        self.assertTrue(driver.is_available)

    def test_contractor_payment_info_incomplete(self):
        """Contractor without payment info reports incomplete."""
        user = User.objects.create_user('driver5', 'driver5@test.com', 'pass')
        driver = DeliveryDriver.objects.create(
            user=user,
            driver_type='contractor'
        )
        self.assertFalse(driver.has_complete_payment_info)

    def test_contractor_payment_info_complete(self):
        """Contractor with payment info reports complete."""
        user = User.objects.create_user('driver6', 'driver6@test.com', 'pass')
        driver = DeliveryDriver.objects.create(
            user=user,
            driver_type='contractor',
            rfc='XAXX010101000',
            rate_per_delivery=Decimal('35.00')
        )
        self.assertTrue(driver.has_complete_payment_info)

    def test_employee_always_has_complete_payment_info(self):
        """Employee always reports complete payment info."""
        user = User.objects.create_user('driver7', 'driver7@test.com', 'pass')
        driver = DeliveryDriver.objects.create(
            user=user,
            driver_type='employee'
        )
        self.assertTrue(driver.has_complete_payment_info)

    def test_driver_str(self):
        """Driver string representation."""
        user = User.objects.create_user(
            'driver8', 'driver8@test.com', 'pass',
            first_name='Juan', last_name='Garcia'
        )
        driver = DeliveryDriver.objects.create(user=user, driver_type='employee')
        self.assertIn('Juan Garcia', str(driver))
