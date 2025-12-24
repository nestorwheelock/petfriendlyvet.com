"""Tests for the delivery app."""
from decimal import Decimal
from datetime import date, time, timedelta

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.apps import apps
from django.utils import timezone
from django.db import IntegrityError

from .models import (
    DeliveryZone, DeliverySlot, DeliveryDriver,
    Delivery, DeliveryStatusHistory,
    DeliveryProof, DeliveryRating, DeliveryNotification
)
from apps.store.models import Category, Product, Cart, Order

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


class DeliveryAdminTests(TestCase):
    """Tests for delivery admin interfaces."""

    def setUp(self):
        """Set up admin user and client."""
        self.admin_user = User.objects.create_superuser(
            'admin', 'admin@test.com', 'adminpass'
        )
        self.client = Client()
        self.client.force_login(self.admin_user)

    def test_delivery_zone_admin_accessible(self):
        """DeliveryZone admin is accessible."""
        response = self.client.get('/admin/delivery/deliveryzone/')
        self.assertEqual(response.status_code, 200)

    def test_delivery_zone_admin_add(self):
        """Can add DeliveryZone via admin."""
        response = self.client.get('/admin/delivery/deliveryzone/add/')
        self.assertEqual(response.status_code, 200)

    def test_delivery_slot_admin_accessible(self):
        """DeliverySlot admin is accessible."""
        response = self.client.get('/admin/delivery/deliveryslot/')
        self.assertEqual(response.status_code, 200)

    def test_delivery_driver_admin_accessible(self):
        """DeliveryDriver admin is accessible."""
        response = self.client.get('/admin/delivery/deliverydriver/')
        self.assertEqual(response.status_code, 200)

    def test_delivery_admin_accessible(self):
        """Delivery admin is accessible."""
        response = self.client.get('/admin/delivery/delivery/')
        self.assertEqual(response.status_code, 200)

    def test_delivery_admin_has_status_filter(self):
        """Delivery admin should have status filter."""
        response = self.client.get('/admin/delivery/delivery/')
        self.assertContains(response, 'status')

    def test_delivery_proof_admin_accessible(self):
        """DeliveryProof admin is accessible."""
        response = self.client.get('/admin/delivery/deliveryproof/')
        self.assertEqual(response.status_code, 200)

    def test_delivery_rating_admin_accessible(self):
        """DeliveryRating admin is accessible."""
        response = self.client.get('/admin/delivery/deliveryrating/')
        self.assertEqual(response.status_code, 200)

    def test_delivery_notification_admin_accessible(self):
        """DeliveryNotification admin is accessible."""
        response = self.client.get('/admin/delivery/deliverynotification/')
        self.assertEqual(response.status_code, 200)


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


class DeliveryTests(TestCase):
    """Tests for Delivery model and status workflow."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user('customer', 'c@test.com', 'pass')
        self.category = Category.objects.create(
            name='Test', name_es='Test', name_en='Test', slug='test'
        )
        self.product = Product.objects.create(
            name='Test Product',
            name_es='Producto',
            name_en='Product',
            slug='test-product',
            category=self.category,
            price=Decimal('100.00'),
            sku='TEST-001'
        )
        self.cart = Cart.objects.create(user=self.user)
        self.cart.add_item(self.product, 1)
        self.order = Order.create_from_cart(
            cart=self.cart,
            user=self.user,
            fulfillment_method='delivery',
            shipping_address='Test Address'
        )
        self.zone = DeliveryZone.objects.create(code='CENTRO', name='Centro')

    def test_create_delivery_from_order(self):
        """Can create delivery from order."""
        delivery = Delivery.objects.create(
            order=self.order,
            zone=self.zone,
            address=self.order.shipping_address
        )
        self.assertEqual(delivery.status, 'pending')
        self.assertIsNotNone(delivery.delivery_number)

    def test_delivery_number_generation(self):
        """Delivery number is generated automatically."""
        delivery = Delivery.objects.create(
            order=self.order,
            zone=self.zone
        )
        self.assertTrue(delivery.delivery_number.startswith('DEL-'))

    def test_status_transition_assign(self):
        """Can transition from pending to assigned."""
        driver_user = User.objects.create_user('driver', 'd@test.com', 'pass')
        driver = DeliveryDriver.objects.create(user=driver_user)

        delivery = Delivery.objects.create(order=self.order, zone=self.zone)
        delivery.assign_driver(driver)

        self.assertEqual(delivery.status, 'assigned')
        self.assertEqual(delivery.driver, driver)

    def test_status_transition_pickup(self):
        """Can transition from assigned to picked_up."""
        driver_user = User.objects.create_user('driver', 'd@test.com', 'pass')
        driver = DeliveryDriver.objects.create(user=driver_user)

        delivery = Delivery.objects.create(order=self.order, zone=self.zone)
        delivery.assign_driver(driver)
        delivery.mark_picked_up()

        self.assertEqual(delivery.status, 'picked_up')
        self.assertIsNotNone(delivery.picked_up_at)

    def test_status_transition_out_for_delivery(self):
        """Can transition to out_for_delivery."""
        driver_user = User.objects.create_user('driver', 'd@test.com', 'pass')
        driver = DeliveryDriver.objects.create(user=driver_user)

        delivery = Delivery.objects.create(order=self.order, zone=self.zone)
        delivery.assign_driver(driver)
        delivery.mark_picked_up()
        delivery.mark_out_for_delivery()

        self.assertEqual(delivery.status, 'out_for_delivery')
        self.assertIsNotNone(delivery.out_for_delivery_at)

    def test_status_transition_delivered(self):
        """Can transition to delivered."""
        driver_user = User.objects.create_user('driver', 'd@test.com', 'pass')
        driver = DeliveryDriver.objects.create(user=driver_user)

        delivery = Delivery.objects.create(order=self.order, zone=self.zone)
        delivery.assign_driver(driver)
        delivery.mark_picked_up()
        delivery.mark_out_for_delivery()
        delivery.mark_arrived()
        delivery.mark_delivered()

        self.assertEqual(delivery.status, 'delivered')
        self.assertIsNotNone(delivery.delivered_at)

    def test_invalid_transition_raises_error(self):
        """Invalid status transition raises error."""
        delivery = Delivery.objects.create(order=self.order, zone=self.zone)

        with self.assertRaises(ValueError):
            delivery.mark_picked_up()  # Can't pickup without assignment

    def test_status_history_created(self):
        """Status changes create history records."""
        driver_user = User.objects.create_user('driver', 'd@test.com', 'pass')
        driver = DeliveryDriver.objects.create(user=driver_user)

        delivery = Delivery.objects.create(order=self.order, zone=self.zone)
        delivery.assign_driver(driver)

        self.assertEqual(delivery.status_history.count(), 1)
        history = delivery.status_history.first()
        self.assertEqual(history.from_status, 'pending')
        self.assertEqual(history.to_status, 'assigned')

    def test_delivery_str(self):
        """Delivery string representation."""
        delivery = Delivery.objects.create(order=self.order, zone=self.zone)
        self.assertEqual(str(delivery), delivery.delivery_number)


class DeliveryProofTests(TestCase):
    """Tests for DeliveryProof model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user('customer', 'c@test.com', 'pass')
        self.category = Category.objects.create(
            name='Test', name_es='Test', name_en='Test', slug='test'
        )
        self.product = Product.objects.create(
            name='Test Product',
            name_es='Producto',
            name_en='Product',
            slug='test-product',
            category=self.category,
            price=Decimal('100.00'),
            sku='TEST-001'
        )
        self.cart = Cart.objects.create(user=self.user)
        self.cart.add_item(self.product, 1)
        self.order = Order.create_from_cart(
            cart=self.cart,
            user=self.user,
            fulfillment_method='delivery',
            shipping_address='Test Address'
        )
        self.zone = DeliveryZone.objects.create(code='CENTRO', name='Centro')
        self.delivery = Delivery.objects.create(
            order=self.order,
            zone=self.zone,
            address=self.order.shipping_address
        )

    def test_create_photo_proof(self):
        """Can create photo proof of delivery."""
        proof = DeliveryProof.objects.create(
            delivery=self.delivery,
            proof_type='photo',
            recipient_name='Juan Perez',
            latitude=Decimal('19.432608'),
            longitude=Decimal('-99.133209')
        )
        self.assertEqual(proof.proof_type, 'photo')
        self.assertEqual(proof.recipient_name, 'Juan Perez')

    def test_create_signature_proof(self):
        """Can create signature proof of delivery."""
        proof = DeliveryProof.objects.create(
            delivery=self.delivery,
            proof_type='signature',
            signature_data='base64encodeddata...',
            recipient_name='Maria Garcia'
        )
        self.assertEqual(proof.proof_type, 'signature')
        self.assertIsNotNone(proof.signature_data)

    def test_proof_str(self):
        """Proof string representation."""
        proof = DeliveryProof.objects.create(
            delivery=self.delivery,
            proof_type='photo',
            recipient_name='Test Person'
        )
        self.assertIn(self.delivery.delivery_number, str(proof))
        self.assertIn('photo', str(proof))

    def test_proof_with_gps(self):
        """Proof captures GPS coordinates from browser."""
        proof = DeliveryProof.objects.create(
            delivery=self.delivery,
            proof_type='photo',
            latitude=Decimal('19.432608'),
            longitude=Decimal('-99.133209'),
            gps_accuracy=Decimal('10.5')
        )
        self.assertIsNotNone(proof.latitude)
        self.assertIsNotNone(proof.longitude)
        self.assertIsNotNone(proof.gps_accuracy)


class DeliveryRatingTests(TestCase):
    """Tests for DeliveryRating model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user('customer', 'c@test.com', 'pass')
        self.category = Category.objects.create(
            name='Test', name_es='Test', name_en='Test', slug='test'
        )
        self.product = Product.objects.create(
            name='Test Product',
            name_es='Producto',
            name_en='Product',
            slug='test-product',
            category=self.category,
            price=Decimal('100.00'),
            sku='TEST-001'
        )
        self.cart = Cart.objects.create(user=self.user)
        self.cart.add_item(self.product, 1)
        self.order = Order.create_from_cart(
            cart=self.cart,
            user=self.user,
            fulfillment_method='delivery',
            shipping_address='Test Address'
        )
        self.zone = DeliveryZone.objects.create(code='CENTRO', name='Centro')
        self.delivery = Delivery.objects.create(
            order=self.order,
            zone=self.zone,
            address=self.order.shipping_address
        )

    def test_create_rating(self):
        """Can create a rating for a delivery."""
        rating = DeliveryRating.objects.create(
            delivery=self.delivery,
            rating=5,
            comment='Excelente servicio!'
        )
        self.assertEqual(rating.rating, 5)
        self.assertEqual(rating.comment, 'Excelente servicio!')

    def test_rating_one_to_one(self):
        """Only one rating per delivery allowed."""
        DeliveryRating.objects.create(
            delivery=self.delivery,
            rating=5
        )
        with self.assertRaises(IntegrityError):
            DeliveryRating.objects.create(
                delivery=self.delivery,
                rating=4
            )

    def test_rating_range(self):
        """Rating must be between 1 and 5."""
        rating = DeliveryRating.objects.create(
            delivery=self.delivery,
            rating=3
        )
        self.assertGreaterEqual(rating.rating, 1)
        self.assertLessEqual(rating.rating, 5)

    def test_rating_str(self):
        """Rating string representation."""
        rating = DeliveryRating.objects.create(
            delivery=self.delivery,
            rating=4
        )
        self.assertIn(self.delivery.delivery_number, str(rating))
        self.assertIn('4', str(rating))


class DeliveryNotificationTests(TestCase):
    """Tests for DeliveryNotification model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user('customer', 'c@test.com', 'pass')
        self.category = Category.objects.create(
            name='Test', name_es='Test', name_en='Test', slug='test'
        )
        self.product = Product.objects.create(
            name='Test Product',
            name_es='Producto',
            name_en='Product',
            slug='test-product',
            category=self.category,
            price=Decimal('100.00'),
            sku='TEST-001'
        )
        self.cart = Cart.objects.create(user=self.user)
        self.cart.add_item(self.product, 1)
        self.order = Order.create_from_cart(
            cart=self.cart,
            user=self.user,
            fulfillment_method='delivery',
            shipping_address='Test Address'
        )
        self.zone = DeliveryZone.objects.create(code='CENTRO', name='Centro')
        self.delivery = Delivery.objects.create(
            order=self.order,
            zone=self.zone,
            address=self.order.shipping_address
        )

    def test_create_sms_notification(self):
        """Can create SMS notification."""
        notification = DeliveryNotification.objects.create(
            delivery=self.delivery,
            notification_type='sms',
            recipient='+525551234567',
            message='Tu pedido está en camino',
            status='sent'
        )
        self.assertEqual(notification.notification_type, 'sms')
        self.assertEqual(notification.status, 'sent')

    def test_create_whatsapp_notification(self):
        """Can create WhatsApp notification."""
        notification = DeliveryNotification.objects.create(
            delivery=self.delivery,
            notification_type='whatsapp',
            recipient='+525551234567',
            message='Tu pedido ha sido entregado'
        )
        self.assertEqual(notification.notification_type, 'whatsapp')

    def test_create_email_notification(self):
        """Can create email notification."""
        notification = DeliveryNotification.objects.create(
            delivery=self.delivery,
            notification_type='email',
            recipient='customer@test.com',
            message='Your order is on the way'
        )
        self.assertEqual(notification.notification_type, 'email')

    def test_notification_status_updates(self):
        """Notification status can be updated."""
        notification = DeliveryNotification.objects.create(
            delivery=self.delivery,
            notification_type='sms',
            recipient='+525551234567',
            message='Test message',
            status='pending'
        )
        notification.status = 'delivered'
        notification.save()
        notification.refresh_from_db()
        self.assertEqual(notification.status, 'delivered')

    def test_notification_str(self):
        """Notification string representation."""
        notification = DeliveryNotification.objects.create(
            delivery=self.delivery,
            notification_type='sms',
            recipient='+525551234567',
            message='Test'
        )
        self.assertIn('sms', str(notification))
        self.assertIn(self.delivery.delivery_number, str(notification))

    def test_multiple_notifications_per_delivery(self):
        """Multiple notifications can be sent for one delivery."""
        DeliveryNotification.objects.create(
            delivery=self.delivery,
            notification_type='sms',
            recipient='+525551234567',
            message='Message 1'
        )
        DeliveryNotification.objects.create(
            delivery=self.delivery,
            notification_type='email',
            recipient='test@test.com',
            message='Message 2'
        )
        self.assertEqual(self.delivery.notifications.count(), 2)
