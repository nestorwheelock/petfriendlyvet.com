"""Tests for the delivery app."""
import json
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


class DriverAPITests(TestCase):
    """Tests for Driver API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.driver_user = User.objects.create_user(
            'driver', 'driver@test.com', 'driverpass'
        )
        self.driver = DeliveryDriver.objects.create(
            user=self.driver_user,
            driver_type='employee',
            is_active=True,
            is_available=True
        )
        self.customer = User.objects.create_user(
            'customer', 'customer@test.com', 'customerpass'
        )
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
        self.cart = Cart.objects.create(user=self.customer)
        self.cart.add_item(self.product, 1)
        self.order = Order.create_from_cart(
            cart=self.cart,
            user=self.customer,
            fulfillment_method='delivery',
            shipping_address='Test Address'
        )
        self.zone = DeliveryZone.objects.create(code='CENTRO', name='Centro')
        self.delivery = Delivery.objects.create(
            order=self.order,
            zone=self.zone,
            address=self.order.shipping_address
        )

    def test_driver_deliveries_list_requires_auth(self):
        """Driver deliveries endpoint requires authentication."""
        response = self.client.get('/api/driver/deliveries/')
        self.assertEqual(response.status_code, 403)

    def test_driver_deliveries_list_returns_assigned(self):
        """Driver can list their assigned deliveries."""
        self.client.force_login(self.driver_user)
        self.delivery.assign_driver(self.driver)

        response = self.client.get('/api/driver/deliveries/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['deliveries']), 1)
        self.assertEqual(data['deliveries'][0]['delivery_number'], self.delivery.delivery_number)

    def test_driver_deliveries_excludes_others(self):
        """Driver only sees their own deliveries."""
        self.client.force_login(self.driver_user)
        # Delivery not assigned to this driver

        response = self.client.get('/api/driver/deliveries/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['deliveries']), 0)

    def test_driver_update_status_picked_up(self):
        """Driver can update delivery status to picked_up."""
        self.client.force_login(self.driver_user)
        self.delivery.assign_driver(self.driver)

        response = self.client.post(
            f'/api/driver/deliveries/{self.delivery.id}/status/',
            data={'status': 'picked_up'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.delivery.refresh_from_db()
        self.assertEqual(self.delivery.status, 'picked_up')

    def test_driver_update_status_with_gps(self):
        """Driver can update status with GPS coordinates."""
        self.client.force_login(self.driver_user)
        self.delivery.assign_driver(self.driver)

        response = self.client.post(
            f'/api/driver/deliveries/{self.delivery.id}/status/',
            data={
                'status': 'picked_up',
                'latitude': '19.432608',
                'longitude': '-99.133209'
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        history = self.delivery.status_history.last()
        self.assertEqual(str(history.latitude), '19.432608')
        self.assertEqual(str(history.longitude), '-99.133209')

    def test_driver_cannot_update_others_delivery(self):
        """Driver cannot update delivery assigned to another driver."""
        self.client.force_login(self.driver_user)
        other_driver_user = User.objects.create_user('other', 'other@test.com', 'pass')
        other_driver = DeliveryDriver.objects.create(user=other_driver_user)
        self.delivery.assign_driver(other_driver)

        response = self.client.post(
            f'/api/driver/deliveries/{self.delivery.id}/status/',
            data={'status': 'picked_up'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

    def test_driver_invalid_status_transition(self):
        """Invalid status transitions return error."""
        self.client.force_login(self.driver_user)
        self.delivery.assign_driver(self.driver)

        response = self.client.post(
            f'/api/driver/deliveries/{self.delivery.id}/status/',
            data={'status': 'delivered'},  # Can't go from assigned to delivered
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_driver_delivery_detail(self):
        """Driver can get delivery details."""
        self.client.force_login(self.driver_user)
        self.delivery.assign_driver(self.driver)

        response = self.client.get(f'/api/driver/deliveries/{self.delivery.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['delivery_number'], self.delivery.delivery_number)
        self.assertEqual(data['address'], self.delivery.address)


class DriverDashboardTests(TestCase):
    """Tests for Driver mobile dashboard view."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user('customer', 'c@test.com', 'pass')
        self.driver_user = User.objects.create_user('driver', 'driver@test.com', 'pass')
        self.driver = DeliveryDriver.objects.create(
            user=self.driver_user,
            driver_type='employee',
            is_active=True,
            is_available=True
        )
        self.zone = DeliveryZone.objects.create(code='CENTRO', name='Centro')
        self.category = Category.objects.create(
            name='Food', name_es='Comida', name_en='Food', slug='food'
        )
        self.product = Product.objects.create(
            name='Pet Food', name_es='Comida', name_en='Pet Food',
            slug='pet-food', category=self.category, price=Decimal('100.00'),
            sku='FOOD-001'
        )
        self.cart = Cart.objects.create(user=self.user)
        self.cart.add_item(self.product, 2)
        self.order = Order.create_from_cart(
            cart=self.cart,
            user=self.user,
            fulfillment_method='delivery',
            shipping_address='Av. Reforma 123, Centro'
        )
        self.delivery = Delivery.objects.create(
            order=self.order,
            zone=self.zone,
            address=self.order.shipping_address,
            scheduled_date=date.today()
        )

    def test_dashboard_requires_authentication(self):
        """Dashboard requires user to be logged in."""
        response = self.client.get('/delivery/driver/dashboard/')
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_dashboard_requires_driver(self):
        """Dashboard requires user to be a driver."""
        non_driver = User.objects.create_user('notdriver', 'not@test.com', 'pass')
        self.client.force_login(non_driver)
        response = self.client.get('/delivery/driver/dashboard/')
        self.assertEqual(response.status_code, 403)

    def test_dashboard_shows_assigned_deliveries(self):
        """Dashboard shows deliveries assigned to the driver."""
        self.client.force_login(self.driver_user)
        self.delivery.assign_driver(self.driver)

        response = self.client.get('/delivery/driver/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.delivery.delivery_number)
        self.assertContains(response, self.delivery.address)

    def test_dashboard_excludes_completed_deliveries(self):
        """Dashboard excludes delivered/returned deliveries."""
        self.client.force_login(self.driver_user)
        self.delivery.assign_driver(self.driver)
        self.delivery.mark_picked_up(changed_by=self.driver_user)
        self.delivery.mark_out_for_delivery(changed_by=self.driver_user)
        self.delivery.mark_arrived(changed_by=self.driver_user)
        self.delivery.mark_delivered(changed_by=self.driver_user)

        response = self.client.get('/delivery/driver/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.delivery.delivery_number)

    def test_dashboard_shows_navigation_links(self):
        """Dashboard shows navigation links to Google Maps."""
        self.client.force_login(self.driver_user)
        self.delivery.assign_driver(self.driver)
        self.delivery.latitude = Decimal('19.432608')
        self.delivery.longitude = Decimal('-99.133209')
        self.delivery.save()

        response = self.client.get('/delivery/driver/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'maps.google.com')

    def test_dashboard_uses_correct_template(self):
        """Dashboard uses the driver dashboard template."""
        self.client.force_login(self.driver_user)
        response = self.client.get('/delivery/driver/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'delivery/driver/dashboard.html')

    def test_inactive_driver_cannot_access(self):
        """Inactive driver cannot access dashboard."""
        self.driver.is_active = False
        self.driver.save()
        self.client.force_login(self.driver_user)
        response = self.client.get('/delivery/driver/dashboard/')
        self.assertEqual(response.status_code, 403)


class DriverLocationAPITests(TestCase):
    """Tests for Driver location tracking API."""

    def setUp(self):
        """Set up test data."""
        self.driver_user = User.objects.create_user('driver', 'driver@test.com', 'pass')
        self.driver = DeliveryDriver.objects.create(
            user=self.driver_user,
            driver_type='employee',
            is_active=True,
            is_available=True
        )

    def test_location_update_requires_auth(self):
        """Location update requires authentication."""
        response = self.client.post(
            '/api/driver/location/',
            data={'latitude': '19.432608', 'longitude': '-99.133209'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

    def test_location_update_success(self):
        """Driver can update their location."""
        self.client.force_login(self.driver_user)
        response = self.client.post(
            '/api/driver/location/',
            data={'latitude': '19.432608', 'longitude': '-99.133209'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        self.driver.refresh_from_db()
        self.assertEqual(str(self.driver.current_latitude), '19.432608')
        self.assertEqual(str(self.driver.current_longitude), '-99.133209')
        self.assertIsNotNone(self.driver.location_updated_at)

    def test_location_update_requires_coordinates(self):
        """Location update requires both coordinates."""
        self.client.force_login(self.driver_user)
        response = self.client.post(
            '/api/driver/location/',
            data={'latitude': '19.432608'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('required', response.json()['error'].lower())

    def test_non_driver_cannot_update_location(self):
        """Non-driver user cannot update location."""
        user = User.objects.create_user('notdriver', 'not@test.com', 'pass')
        self.client.force_login(user)
        response = self.client.post(
            '/api/driver/location/',
            data={'latitude': '19.432608', 'longitude': '-99.133209'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)


class ProofOfDeliveryAPITests(TestCase):
    """Tests for Proof of Delivery API."""

    def setUp(self):
        """Set up test data."""
        self.customer = User.objects.create_user('customer', 'c@test.com', 'pass')
        self.driver_user = User.objects.create_user('driver', 'driver@test.com', 'pass')
        self.driver = DeliveryDriver.objects.create(
            user=self.driver_user,
            driver_type='employee',
            is_active=True
        )
        self.zone = DeliveryZone.objects.create(code='CENTRO', name='Centro')
        self.category = Category.objects.create(
            name='Test', name_es='Test', name_en='Test', slug='test'
        )
        self.product = Product.objects.create(
            name='Test Product', name_es='Producto', name_en='Product',
            slug='test-product', category=self.category,
            price=Decimal('100.00'), sku='TEST-001'
        )
        self.cart = Cart.objects.create(user=self.customer)
        self.cart.add_item(self.product, 1)
        self.order = Order.create_from_cart(
            cart=self.cart,
            user=self.customer,
            fulfillment_method='delivery',
            shipping_address='Test Address'
        )
        self.delivery = Delivery.objects.create(
            order=self.order,
            zone=self.zone,
            address=self.order.shipping_address
        )
        self.delivery.assign_driver(self.driver)
        self.delivery.mark_picked_up(changed_by=self.driver_user)
        self.delivery.mark_out_for_delivery(changed_by=self.driver_user)
        self.delivery.mark_arrived(changed_by=self.driver_user)

    def test_proof_submission_requires_auth(self):
        """Proof submission requires authentication."""
        response = self.client.post(
            f'/api/driver/deliveries/{self.delivery.id}/proof/',
            data={'proof_type': 'signature', 'recipient_name': 'John Doe'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

    def test_proof_signature_submission(self):
        """Driver can submit signature proof."""
        self.client.force_login(self.driver_user)
        response = self.client.post(
            f'/api/driver/deliveries/{self.delivery.id}/proof/',
            data={
                'proof_type': 'signature',
                'signature_data': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUg...',
                'recipient_name': 'Juan Garcia',
                'latitude': '19.432608',
                'longitude': '-99.133209'
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)

        proof = DeliveryProof.objects.get(delivery=self.delivery)
        self.assertEqual(proof.proof_type, 'signature')
        self.assertEqual(proof.recipient_name, 'Juan Garcia')
        self.assertEqual(str(proof.latitude), '19.432608')

    def test_proof_photo_submission(self):
        """Driver can submit photo proof with GPS."""
        self.client.force_login(self.driver_user)
        response = self.client.post(
            f'/api/driver/deliveries/{self.delivery.id}/proof/',
            data={
                'proof_type': 'photo',
                'photo_data': 'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD...',
                'latitude': '19.432608',
                'longitude': '-99.133209',
                'gps_accuracy': '10.5'
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)

        proof = DeliveryProof.objects.get(delivery=self.delivery)
        self.assertEqual(proof.proof_type, 'photo')
        self.assertEqual(str(proof.gps_accuracy), '10.50')

    def test_proof_requires_valid_type(self):
        """Proof submission requires valid proof type."""
        self.client.force_login(self.driver_user)
        response = self.client.post(
            f'/api/driver/deliveries/{self.delivery.id}/proof/',
            data={'proof_type': 'invalid'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_driver_cannot_submit_proof_for_others(self):
        """Driver cannot submit proof for another driver's delivery."""
        other_driver_user = User.objects.create_user('other', 'other@test.com', 'pass')
        other_driver = DeliveryDriver.objects.create(user=other_driver_user)

        # Reassign to other driver
        self.delivery.driver = other_driver
        self.delivery.save()

        self.client.force_login(self.driver_user)
        response = self.client.post(
            f'/api/driver/deliveries/{self.delivery.id}/proof/',
            data={'proof_type': 'signature', 'recipient_name': 'John'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)


class DeliverySlotAPITests(TestCase):
    """Tests for Delivery slot selection API."""

    def setUp(self):
        """Set up test data."""
        self.zone = DeliveryZone.objects.create(code='CENTRO', name='Centro')
        self.today = date.today()
        self.tomorrow = self.today + timedelta(days=1)
        # Create slots for tomorrow
        self.slot1 = DeliverySlot.objects.create(
            zone=self.zone,
            date=self.tomorrow,
            start_time=time(9, 0),
            end_time=time(12, 0),
            capacity=5,
            booked_count=0
        )
        self.slot2 = DeliverySlot.objects.create(
            zone=self.zone,
            date=self.tomorrow,
            start_time=time(14, 0),
            end_time=time(17, 0),
            capacity=5,
            booked_count=5  # Full
        )
        self.slot3 = DeliverySlot.objects.create(
            zone=self.zone,
            date=self.tomorrow,
            start_time=time(17, 0),
            end_time=time(20, 0),
            capacity=5,
            booked_count=0,
            is_active=False  # Inactive
        )

    def test_get_available_slots_for_date(self):
        """Can get available slots for a specific date."""
        response = self.client.get(
            f'/api/delivery/slots/?date={self.tomorrow}'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Should only return slot1 (slot2 is full, slot3 is inactive)
        self.assertEqual(len(data['slots']), 1)
        self.assertEqual(data['slots'][0]['id'], self.slot1.id)

    def test_get_slots_includes_time_display(self):
        """Slot data includes formatted time display."""
        response = self.client.get(
            f'/api/delivery/slots/?date={self.tomorrow}'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('time_display', data['slots'][0])
        self.assertIn('09:00', data['slots'][0]['time_display'])

    def test_get_slots_for_zone(self):
        """Can filter slots by zone."""
        other_zone = DeliveryZone.objects.create(code='NORTE', name='Norte')
        DeliverySlot.objects.create(
            zone=other_zone,
            date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(13, 0),
            capacity=5
        )

        response = self.client.get(
            f'/api/delivery/slots/?date={self.tomorrow}&zone={self.zone.code}'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Should only return slots for CENTRO zone
        self.assertEqual(len(data['slots']), 1)

    def test_get_available_dates(self):
        """Can get dates with available slots."""
        response = self.client.get('/api/delivery/slots/dates/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(str(self.tomorrow), data['dates'])

    def test_no_slots_for_past_dates(self):
        """Past dates return no slots."""
        yesterday = self.today - timedelta(days=1)
        DeliverySlot.objects.create(
            zone=self.zone,
            date=yesterday,
            start_time=time(9, 0),
            end_time=time(12, 0),
            capacity=5
        )
        response = self.client.get(f'/api/delivery/slots/?date={yesterday}')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['slots']), 0)


class DriverAvailabilityAPITests(TestCase):
    """Tests for Driver availability toggle API."""

    def setUp(self):
        """Set up test data."""
        self.driver_user = User.objects.create_user('driver', 'driver@test.com', 'pass')
        self.driver = DeliveryDriver.objects.create(
            user=self.driver_user,
            driver_type='employee',
            is_active=True,
            is_available=False
        )

    def test_availability_toggle_requires_auth(self):
        """Availability toggle requires authentication."""
        response = self.client.post(
            '/api/driver/availability/',
            data={'is_available': True},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

    def test_availability_toggle_on(self):
        """Driver can toggle availability on."""
        self.client.force_login(self.driver_user)
        self.assertFalse(self.driver.is_available)

        response = self.client.post(
            '/api/driver/availability/',
            data={'is_available': True},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        self.driver.refresh_from_db()
        self.assertTrue(self.driver.is_available)

    def test_availability_toggle_off(self):
        """Driver can toggle availability off."""
        self.driver.is_available = True
        self.driver.save()
        self.client.force_login(self.driver_user)

        response = self.client.post(
            '/api/driver/availability/',
            data={'is_available': False},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        self.driver.refresh_from_db()
        self.assertFalse(self.driver.is_available)

    def test_get_current_availability(self):
        """Driver can get their current availability."""
        self.client.force_login(self.driver_user)

        response = self.client.get('/api/driver/availability/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['is_available'])

    def test_non_driver_cannot_toggle(self):
        """Non-driver user cannot toggle availability."""
        user = User.objects.create_user('notdriver', 'not@test.com', 'pass')
        self.client.force_login(user)

        response = self.client.post(
            '/api/driver/availability/',
            data={'is_available': True},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)


class CheckoutDeliveryIntegrationTests(TestCase):
    """Tests for checkout creating Delivery records with slot selection."""

    def setUp(self):
        """Set up test data for checkout."""
        self.user = User.objects.create_user('customer', 'customer@test.com', 'pass')
        self.client = Client()
        self.client.force_login(self.user)

        # Create zone and slot
        self.zone = DeliveryZone.objects.create(
            code='CENTRO',
            name='Centro',
            delivery_fee=Decimal('50.00')
        )
        self.tomorrow = date.today() + timedelta(days=1)
        self.slot = DeliverySlot.objects.create(
            zone=self.zone,
            date=self.tomorrow,
            start_time=time(9, 0),
            end_time=time(12, 0),
            capacity=5
        )

        # Create product and cart
        category = Category.objects.create(name='Food', slug='food')
        self.product = Product.objects.create(
            name='Dog Food',
            slug='dog-food',
            category=category,
            price=Decimal('100.00'),
            sku='FOOD-001'
        )
        self.cart = Cart.objects.create(user=self.user)
        self.cart.add_item(self.product, 2)

    def test_checkout_with_delivery_creates_delivery_record(self):
        """Checkout with delivery fulfillment creates a Delivery record."""
        response = self.client.post('/en/store/checkout/process/', {
            'fulfillment_method': 'delivery',
            'payment_method': 'cash',
            'shipping_name': 'John Doe',
            'shipping_address': '123 Main St',
            'shipping_phone': '555-1234',
            'delivery_slot': self.slot.id,
        })

        # Should redirect to order detail
        self.assertEqual(response.status_code, 302)

        # Order should be created
        order = Order.objects.filter(user=self.user).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.fulfillment_method, 'delivery')

        # Delivery record should be created with slot
        self.assertTrue(hasattr(order, 'delivery'))
        delivery = order.delivery
        self.assertEqual(delivery.slot, self.slot)
        self.assertEqual(delivery.zone, self.zone)
        self.assertEqual(delivery.scheduled_date, self.tomorrow)
        self.assertEqual(delivery.scheduled_time_start, time(9, 0))
        self.assertEqual(delivery.scheduled_time_end, time(12, 0))
        self.assertEqual(delivery.address, '123 Main St')
        self.assertEqual(delivery.status, 'pending')

    def test_checkout_with_delivery_increments_slot_booked_count(self):
        """Booking a delivery slot increments the booked_count."""
        initial_booked = self.slot.booked_count

        self.client.post('/en/store/checkout/process/', {
            'fulfillment_method': 'delivery',
            'payment_method': 'cash',
            'shipping_name': 'John Doe',
            'shipping_address': '123 Main St',
            'shipping_phone': '555-1234',
            'delivery_slot': self.slot.id,
        })

        self.slot.refresh_from_db()
        self.assertEqual(self.slot.booked_count, initial_booked + 1)

    def test_checkout_pickup_does_not_create_delivery(self):
        """Checkout with pickup fulfillment does not create Delivery."""
        response = self.client.post('/en/store/checkout/process/', {
            'fulfillment_method': 'pickup',
            'payment_method': 'cash',
        })

        self.assertEqual(response.status_code, 302)
        order = Order.objects.filter(user=self.user).first()
        self.assertIsNotNone(order)
        self.assertFalse(hasattr(order, 'delivery') and order.delivery is not None)

    def test_checkout_delivery_without_slot_creates_delivery_no_slot(self):
        """Checkout with delivery but no slot still creates Delivery."""
        response = self.client.post('/en/store/checkout/process/', {
            'fulfillment_method': 'delivery',
            'payment_method': 'cash',
            'shipping_name': 'Jane Doe',
            'shipping_address': '456 Oak Ave',
            'shipping_phone': '555-5678',
        })

        self.assertEqual(response.status_code, 302)
        order = Order.objects.filter(user=self.user).first()
        self.assertIsNotNone(order)
        self.assertTrue(hasattr(order, 'delivery'))
        delivery = order.delivery
        self.assertIsNone(delivery.slot)
        self.assertEqual(delivery.address, '456 Oak Ave')
        self.assertEqual(delivery.status, 'pending')


class DeliveryTrackingPageTests(TestCase):
    """Tests for customer delivery tracking page."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user('customer', 'customer@test.com', 'pass')
        self.other_user = User.objects.create_user('other', 'other@test.com', 'pass')
        self.client = Client()

        # Create zone and slot
        self.zone = DeliveryZone.objects.create(
            code='CENTRO',
            name='Centro',
            delivery_fee=Decimal('50.00')
        )
        self.slot = DeliverySlot.objects.create(
            zone=self.zone,
            date=date.today() + timedelta(days=1),
            start_time=time(9, 0),
            end_time=time(12, 0),
            capacity=5
        )

        # Create category, product, cart, and order
        category = Category.objects.create(name='Food', slug='food')
        product = Product.objects.create(
            name='Dog Food',
            slug='dog-food',
            category=category,
            price=Decimal('100.00'),
            sku='FOOD-001'
        )
        cart = Cart.objects.create(user=self.user)
        cart.add_item(product, 2)
        self.order = Order.create_from_cart(
            cart=cart,
            user=self.user,
            fulfillment_method='delivery',
            payment_method='cash',
            shipping_address='123 Main St',
            shipping_name='John Doe',
            shipping_phone='555-1234'
        )

        # Create delivery for the order
        self.delivery = Delivery.objects.create(
            order=self.order,
            slot=self.slot,
            zone=self.zone,
            address='123 Main St',
            scheduled_date=self.slot.date,
            scheduled_time_start=self.slot.start_time,
            scheduled_time_end=self.slot.end_time,
            status='pending'
        )

    def test_tracking_page_requires_auth(self):
        """Tracking page requires authentication."""
        response = self.client.get(f'/delivery/track/{self.delivery.delivery_number}/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_tracking_page_returns_200(self):
        """Tracking page returns 200 for owner."""
        self.client.force_login(self.user)
        response = self.client.get(f'/delivery/track/{self.delivery.delivery_number}/')
        self.assertEqual(response.status_code, 200)

    def test_tracking_page_uses_correct_template(self):
        """Tracking page uses correct template."""
        self.client.force_login(self.user)
        response = self.client.get(f'/delivery/track/{self.delivery.delivery_number}/')
        self.assertTemplateUsed(response, 'delivery/tracking.html')

    def test_tracking_page_shows_delivery_info(self):
        """Tracking page shows delivery information."""
        self.client.force_login(self.user)
        response = self.client.get(f'/delivery/track/{self.delivery.delivery_number}/')
        content = response.content.decode()
        self.assertIn(self.delivery.delivery_number, content)
        self.assertIn('123 Main St', content)
        self.assertIn('09:00', content)  # Start time

    def test_other_user_cannot_view_tracking(self):
        """Other users cannot view someone else's tracking page."""
        self.client.force_login(self.other_user)
        response = self.client.get(f'/delivery/track/{self.delivery.delivery_number}/')
        self.assertEqual(response.status_code, 404)

    def test_tracking_shows_status_timeline(self):
        """Tracking page shows status timeline."""
        self.client.force_login(self.user)
        response = self.client.get(f'/delivery/track/{self.delivery.delivery_number}/')
        content = response.content.decode()
        # Check for status indicators
        self.assertIn('pending', content.lower())

    def test_tracking_api_returns_current_status(self):
        """Tracking API returns current delivery status."""
        self.client.force_login(self.user)
        response = self.client.get(f'/api/delivery/track/{self.delivery.delivery_number}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'pending')
        self.assertEqual(data['delivery_number'], self.delivery.delivery_number)

    def test_tracking_api_requires_auth(self):
        """Tracking API requires authentication."""
        response = self.client.get(f'/api/delivery/track/{self.delivery.delivery_number}/')
        self.assertEqual(response.status_code, 403)

    def test_tracking_api_other_user_denied(self):
        """Tracking API denies access to other users."""
        self.client.force_login(self.other_user)
        response = self.client.get(f'/api/delivery/track/{self.delivery.delivery_number}/')
        self.assertEqual(response.status_code, 404)


class DeliveryNotificationServiceTests(TestCase):
    """Tests for delivery notification service."""

    def setUp(self):
        """Set up test data."""
        from apps.communications.models import MessageTemplate

        self.user = User.objects.create_user(
            'customer', 'customer@test.com', 'pass',
            first_name='John', last_name='Doe'
        )

        # Create zone and slot
        self.zone = DeliveryZone.objects.create(
            code='CENTRO', name='Centro', delivery_fee=Decimal('50.00')
        )
        self.slot = DeliverySlot.objects.create(
            zone=self.zone,
            date=date.today() + timedelta(days=1),
            start_time=time(9, 0),
            end_time=time(12, 0),
            capacity=5
        )

        # Create order
        category = Category.objects.create(name='Food', slug='food')
        product = Product.objects.create(
            name='Dog Food', slug='dog-food', category=category,
            price=Decimal('100.00'), sku='FOOD-001'
        )
        cart = Cart.objects.create(user=self.user)
        cart.add_item(product, 1)
        self.order = Order.create_from_cart(
            cart=cart, user=self.user, fulfillment_method='delivery',
            payment_method='cash', shipping_address='123 Main St',
            shipping_phone='555-1234'
        )

        # Create delivery
        self.delivery = Delivery.objects.create(
            order=self.order, slot=self.slot, zone=self.zone,
            address='123 Main St', scheduled_date=self.slot.date,
            scheduled_time_start=self.slot.start_time,
            scheduled_time_end=self.slot.end_time, status='pending'
        )

        # Create message templates for delivery notifications
        MessageTemplate.objects.create(
            name='Delivery Assigned',
            template_type='delivery_assigned',
            body_es='Hola {{customer_name}}, tu pedido {{delivery_number}} ha sido asignado. Conductor: {{driver_name}}',
            body_en='Hello {{customer_name}}, your order {{delivery_number}} has been assigned. Driver: {{driver_name}}',
            channels=['sms', 'whatsapp']
        )
        MessageTemplate.objects.create(
            name='Delivery Out for Delivery',
            template_type='delivery_out_for_delivery',
            body_es='Tu pedido {{delivery_number}} esta en camino. ETA: {{eta}}',
            body_en='Your order {{delivery_number}} is on the way. ETA: {{eta}}',
            channels=['sms', 'whatsapp']
        )
        MessageTemplate.objects.create(
            name='Delivery Arrived',
            template_type='delivery_arrived',
            body_es='El conductor ha llegado con tu pedido {{delivery_number}}',
            body_en='The driver has arrived with your order {{delivery_number}}',
            channels=['sms', 'whatsapp']
        )
        MessageTemplate.objects.create(
            name='Delivery Completed',
            template_type='delivery_delivered',
            body_es='Tu pedido {{delivery_number}} ha sido entregado. Gracias!',
            body_en='Your order {{delivery_number}} has been delivered. Thank you!',
            channels=['sms', 'whatsapp']
        )

    def test_get_notification_template(self):
        """Can get notification template for status."""
        from apps.delivery.services import DeliveryNotificationService

        template = DeliveryNotificationService.get_template_for_status('assigned')
        self.assertIsNotNone(template)
        self.assertEqual(template.template_type, 'delivery_assigned')

    def test_render_notification_message(self):
        """Can render notification message with context."""
        from apps.delivery.services import DeliveryNotificationService

        message = DeliveryNotificationService.render_message(
            template_type='delivery_delivered',
            context={'delivery_number': 'DEL-001', 'customer_name': 'John'},
            language='es'
        )
        self.assertIn('DEL-001', message)
        self.assertIn('entregado', message)

    def test_create_notification_record(self):
        """Creates notification record when sending."""
        from apps.delivery.services import DeliveryNotificationService

        notification = DeliveryNotificationService.create_notification(
            delivery=self.delivery,
            notification_type='sms',
            status='out_for_delivery'
        )

        self.assertIsNotNone(notification)
        self.assertEqual(notification.delivery, self.delivery)
        self.assertEqual(notification.notification_type, 'sms')
        self.assertIn(self.delivery.delivery_number, notification.message)

    def test_send_status_notifications(self):
        """Sends notifications when status changes."""
        from apps.delivery.services import DeliveryNotificationService

        notifications = DeliveryNotificationService.send_status_notifications(
            self.delivery, 'out_for_delivery'
        )

        # Should create notification records
        self.assertGreater(len(notifications), 0)
        self.assertEqual(
            DeliveryNotification.objects.filter(delivery=self.delivery).count(),
            len(notifications)
        )

    def test_notification_uses_customer_phone(self):
        """Notification uses customer phone from order."""
        from apps.delivery.services import DeliveryNotificationService

        notification = DeliveryNotificationService.create_notification(
            delivery=self.delivery,
            notification_type='sms',
            status='delivered'
        )

        self.assertEqual(notification.recipient, '555-1234')


class DeliveryRatingTests(TestCase):
    """Tests for customer delivery rating system."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user('customer', 'customer@test.com', 'pass')
        self.other_user = User.objects.create_user('other', 'other@test.com', 'pass')
        self.client = Client()

        # Create zone
        zone = DeliveryZone.objects.create(code='CENTRO', name='Centro')

        # Create order
        category = Category.objects.create(name='Food', slug='food')
        product = Product.objects.create(
            name='Dog Food', slug='dog-food', category=category,
            price=Decimal('100.00'), sku='FOOD-001'
        )
        cart = Cart.objects.create(user=self.user)
        cart.add_item(product, 1)
        self.order = Order.create_from_cart(
            cart=cart, user=self.user, fulfillment_method='delivery',
            payment_method='cash', shipping_address='123 Main St'
        )

        # Create delivery (delivered status)
        self.delivery = Delivery.objects.create(
            order=self.order, zone=zone, address='123 Main St', status='delivered'
        )

    def test_rating_api_requires_auth(self):
        """Rating API requires authentication."""
        response = self.client.post(
            f'/api/delivery/rate/{self.delivery.delivery_number}/',
            data={'rating': 5},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

    def test_submit_rating_success(self):
        """Customer can submit rating for their delivery."""
        self.client.force_login(self.user)
        response = self.client.post(
            f'/api/delivery/rate/{self.delivery.delivery_number}/',
            data={'rating': 5, 'comment': 'Great service!'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

        # Verify rating was created
        self.delivery.refresh_from_db()
        self.assertTrue(hasattr(self.delivery, 'rating'))
        self.assertEqual(self.delivery.rating.rating, 5)
        self.assertEqual(self.delivery.rating.comment, 'Great service!')

    def test_rating_validates_range(self):
        """Rating must be 1-5."""
        self.client.force_login(self.user)

        # Rating too low
        response = self.client.post(
            f'/api/delivery/rate/{self.delivery.delivery_number}/',
            data={'rating': 0},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

        # Rating too high
        response = self.client.post(
            f'/api/delivery/rate/{self.delivery.delivery_number}/',
            data={'rating': 6},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_other_user_cannot_rate(self):
        """Other users cannot rate someone else's delivery."""
        self.client.force_login(self.other_user)
        response = self.client.post(
            f'/api/delivery/rate/{self.delivery.delivery_number}/',
            data={'rating': 5},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)

    def test_cannot_rate_undelivered(self):
        """Cannot rate a delivery that hasn't been completed."""
        self.delivery.status = 'pending'
        self.delivery.save()

        self.client.force_login(self.user)
        response = self.client.post(
            f'/api/delivery/rate/{self.delivery.delivery_number}/',
            data={'rating': 5},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('not yet delivered', response.json()['error'])

    def test_cannot_rate_twice(self):
        """Cannot submit rating twice for same delivery."""
        self.client.force_login(self.user)

        # First rating
        self.client.post(
            f'/api/delivery/rate/{self.delivery.delivery_number}/',
            data={'rating': 5},
            content_type='application/json'
        )

        # Second rating should fail
        response = self.client.post(
            f'/api/delivery/rate/{self.delivery.delivery_number}/',
            data={'rating': 3},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('already rated', response.json()['error'])

    def test_get_existing_rating(self):
        """Can get existing rating for delivery."""
        from apps.delivery.models import DeliveryRating
        DeliveryRating.objects.create(
            delivery=self.delivery, rating=4, comment='Good service'
        )

        self.client.force_login(self.user)
        response = self.client.get(
            f'/api/delivery/rate/{self.delivery.delivery_number}/'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['rating'], 4)
        self.assertEqual(data['comment'], 'Good service')


class AdminDashboardTests(TestCase):
    """Tests for admin delivery dashboard."""

    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_superuser(
            'admin', 'admin@test.com', 'adminpass'
        )
        self.staff_user = User.objects.create_user(
            'staff', 'staff@test.com', 'pass', is_staff=True
        )
        self.regular_user = User.objects.create_user(
            'customer', 'customer@test.com', 'pass'
        )
        self.client = Client()

        # Create zone and driver
        self.zone = DeliveryZone.objects.create(
            code='CENTRO', name='Centro', delivery_fee=Decimal('50.00')
        )
        self.driver = DeliveryDriver.objects.create(
            user=User.objects.create_user('driver', 'driver@test.com', 'pass'),
            driver_type='employee',
            is_active=True,
            is_available=True
        )

        # Create some deliveries
        category = Category.objects.create(name='Food', slug='food')
        product = Product.objects.create(
            name='Dog Food', slug='dog-food', category=category,
            price=Decimal('100.00'), sku='FOOD-001'
        )

        for i, status in enumerate(['pending', 'assigned', 'out_for_delivery', 'delivered']):
            user = User.objects.create_user(f'cust{i}', f'cust{i}@test.com', 'pass')
            cart = Cart.objects.create(user=user)
            cart.add_item(product, 1)
            order = Order.create_from_cart(
                cart=cart, user=user, fulfillment_method='delivery',
                payment_method='cash', shipping_address=f'{i} Main St'
            )
            Delivery.objects.create(
                order=order, zone=self.zone, address=f'{i} Main St',
                status=status, scheduled_date=date.today(),
                driver=self.driver if status != 'pending' else None
            )

    def test_dashboard_requires_staff(self):
        """Dashboard requires staff permission."""
        # Anonymous user
        response = self.client.get('/delivery/admin/dashboard/')
        self.assertEqual(response.status_code, 302)

        # Regular user
        self.client.force_login(self.regular_user)
        response = self.client.get('/delivery/admin/dashboard/')
        self.assertEqual(response.status_code, 403)

    def test_dashboard_accessible_to_staff(self):
        """Staff user can access dashboard."""
        self.client.force_login(self.staff_user)
        response = self.client.get('/delivery/admin/dashboard/')
        self.assertEqual(response.status_code, 200)

    def test_dashboard_uses_correct_template(self):
        """Dashboard uses correct template."""
        self.client.force_login(self.admin_user)
        response = self.client.get('/delivery/admin/dashboard/')
        self.assertTemplateUsed(response, 'delivery/admin/dashboard.html')

    def test_dashboard_shows_delivery_stats(self):
        """Dashboard shows delivery statistics."""
        self.client.force_login(self.admin_user)
        response = self.client.get('/delivery/admin/dashboard/')
        content = response.content.decode()

        # Should show stats
        self.assertIn('pending', content.lower())
        self.assertIn('delivered', content.lower())

    def test_dashboard_shows_todays_deliveries(self):
        """Dashboard shows today's deliveries."""
        self.client.force_login(self.admin_user)
        response = self.client.get('/delivery/admin/dashboard/')

        # Context should have deliveries
        self.assertIn('deliveries', response.context)
        self.assertEqual(len(response.context['deliveries']), 4)

    def test_dashboard_api_returns_delivery_data(self):
        """Dashboard API returns delivery data for map."""
        self.client.force_login(self.admin_user)
        response = self.client.get('/api/delivery/admin/deliveries/')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('deliveries', data)
        self.assertEqual(len(data['deliveries']), 4)

    def test_dashboard_api_returns_driver_locations(self):
        """Dashboard API returns driver locations."""
        # Update driver location
        self.driver.current_latitude = Decimal('19.4326')
        self.driver.current_longitude = Decimal('-99.1332')
        self.driver.location_updated_at = timezone.now()
        self.driver.save()

        self.client.force_login(self.admin_user)
        response = self.client.get('/api/delivery/admin/drivers/')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('drivers', data)
        self.assertEqual(len(data['drivers']), 1)
        self.assertIsNotNone(data['drivers'][0]['latitude'])

    def test_dashboard_api_requires_staff(self):
        """Dashboard API requires staff permission."""
        # Anonymous user gets 403 (API returns JSON error)
        response = self.client.get('/api/delivery/admin/deliveries/')
        self.assertIn(response.status_code, [302, 403])

        # Regular user gets 403
        self.client.force_login(self.regular_user)
        response = self.client.get('/api/delivery/admin/deliveries/')
        self.assertEqual(response.status_code, 403)


class AutoAssignmentTests(TestCase):
    """Tests for delivery auto-assignment logic."""

    def setUp(self):
        """Set up test data."""
        # Create zones
        self.zone1 = DeliveryZone.objects.create(code='CENTRO', name='Centro')
        self.zone2 = DeliveryZone.objects.create(code='NORTE', name='Norte')

        # Create drivers
        self.driver1 = DeliveryDriver.objects.create(
            user=User.objects.create_user('driver1', 'driver1@test.com', 'pass'),
            driver_type='employee',
            is_active=True,
            is_available=True,
            max_deliveries_per_day=5
        )
        self.driver1.zones.add(self.zone1)

        self.driver2 = DeliveryDriver.objects.create(
            user=User.objects.create_user('driver2', 'driver2@test.com', 'pass'),
            driver_type='employee',
            is_active=True,
            is_available=True,
            max_deliveries_per_day=5
        )
        self.driver2.zones.add(self.zone1, self.zone2)

        # Create orders and deliveries
        category = Category.objects.create(name='Food', slug='food')
        product = Product.objects.create(
            name='Dog Food', slug='dog-food', category=category,
            price=Decimal('100.00'), sku='FOOD-001'
        )

        for i in range(3):
            user = User.objects.create_user(f'cust{i}', f'cust{i}@test.com', 'pass')
            cart = Cart.objects.create(user=user)
            cart.add_item(product, 1)
            order = Order.create_from_cart(
                cart=cart, user=user, fulfillment_method='delivery',
                payment_method='cash', shipping_address=f'{i} Main St'
            )
            Delivery.objects.create(
                order=order, zone=self.zone1, address=f'{i} Main St',
                status='pending', scheduled_date=date.today()
            )

    def test_auto_assign_assigns_to_available_driver(self):
        """Auto-assign assigns deliveries to available drivers."""
        from apps.delivery.services import DeliveryAssignmentService

        assigned = DeliveryAssignmentService.auto_assign_pending()

        # Should assign deliveries
        self.assertGreater(len(assigned), 0)

        # Check that deliveries are assigned
        for delivery in assigned:
            self.assertIsNotNone(delivery.driver)
            self.assertEqual(delivery.status, 'assigned')

    def test_auto_assign_respects_zone(self):
        """Auto-assign only assigns drivers to their zones."""
        from apps.delivery.services import DeliveryAssignmentService

        # Create a delivery in zone2 (only driver2 covers it)
        user = User.objects.create_user('custz2', 'custz2@test.com', 'pass')
        cart = Cart.objects.create(user=user)
        category = Category.objects.get(slug='food')
        product = Product.objects.get(slug='dog-food')
        cart.add_item(product, 1)
        order = Order.create_from_cart(
            cart=cart, user=user, fulfillment_method='delivery',
            payment_method='cash', shipping_address='Zone2 Address'
        )
        zone2_delivery = Delivery.objects.create(
            order=order, zone=self.zone2, address='Zone2 Address',
            status='pending', scheduled_date=date.today()
        )

        assigned = DeliveryAssignmentService.auto_assign_pending()

        # Zone2 delivery should be assigned to driver2
        zone2_delivery.refresh_from_db()
        if zone2_delivery.driver:
            self.assertEqual(zone2_delivery.driver, self.driver2)

    def test_auto_assign_respects_daily_limit(self):
        """Auto-assign respects driver's daily delivery limit."""
        from apps.delivery.services import DeliveryAssignmentService

        # Set driver1's limit to 1
        self.driver1.max_deliveries_per_day = 1
        self.driver1.save()

        # Assign existing delivery to driver1
        delivery = Delivery.objects.filter(status='pending').first()
        delivery.driver = self.driver1
        delivery.status = 'assigned'
        delivery.save()

        # Try to auto-assign remaining deliveries
        assigned = DeliveryAssignmentService.auto_assign_pending()

        # Driver1 should not get more deliveries (at limit)
        driver1_deliveries = [d for d in assigned if d.driver == self.driver1]
        self.assertEqual(len(driver1_deliveries), 0)

    def test_auto_assign_skips_unavailable_drivers(self):
        """Auto-assign skips unavailable drivers."""
        from apps.delivery.services import DeliveryAssignmentService

        # Make driver1 unavailable
        self.driver1.is_available = False
        self.driver1.save()

        assigned = DeliveryAssignmentService.auto_assign_pending()

        # All should go to driver2
        for delivery in assigned:
            self.assertEqual(delivery.driver, self.driver2)

    def test_get_available_drivers_for_zone(self):
        """Can get available drivers for a specific zone."""
        from apps.delivery.services import DeliveryAssignmentService

        drivers = DeliveryAssignmentService.get_available_drivers_for_zone(self.zone1)
        self.assertEqual(len(drivers), 2)  # Both drivers cover zone1

        drivers = DeliveryAssignmentService.get_available_drivers_for_zone(self.zone2)
        self.assertEqual(len(drivers), 1)  # Only driver2 covers zone2


class DeliveryReportsTests(TestCase):
    """Tests for delivery reports and analytics."""

    def setUp(self):
        """Set up test data."""
        self.staff_user = User.objects.create_user(
            'staff', 'staff@test.com', 'staffpass', is_staff=True
        )
        self.client = Client()
        self.client.login(username='staff', password='staffpass')

        # Create zone
        self.zone = DeliveryZone.objects.create(code='CENTRO', name='Centro')

        # Create driver
        self.driver = DeliveryDriver.objects.create(
            user=User.objects.create_user('driver', 'driver@test.com', 'pass'),
            driver_type='employee',
            is_active=True,
            is_available=True
        )
        self.driver.zones.add(self.zone)

        # Create orders and deliveries with various statuses
        category = Category.objects.create(name='Food', slug='food')
        product = Product.objects.create(
            name='Dog Food', slug='dog-food', category=category,
            price=Decimal('100.00'), sku='FOOD-001'
        )

        # Create 10 deliveries with different statuses
        for i in range(10):
            user = User.objects.create_user(f'cust{i}', f'cust{i}@test.com', 'pass')
            cart = Cart.objects.create(user=user)
            cart.add_item(product, 1)
            order = Order.create_from_cart(
                cart=cart, user=user, fulfillment_method='delivery',
                payment_method='cash', shipping_address=f'{i} Main St'
            )

            # Vary statuses
            if i < 5:
                status = 'delivered'
            elif i < 7:
                status = 'pending'
            elif i < 9:
                status = 'out_for_delivery'
            else:
                status = 'failed'

            delivery = Delivery.objects.create(
                order=order, zone=self.zone, address=f'{i} Main St',
                status=status, scheduled_date=date.today(),
                driver=self.driver if status != 'pending' else None
            )

            if status == 'delivered':
                delivery.delivered_at = timezone.now()
                delivery.save()
                # Add rating for some
                if i < 3:
                    DeliveryRating.objects.create(
                        delivery=delivery, rating=5 if i < 2 else 4
                    )

    def test_reports_page_requires_staff(self):
        """Reports page requires staff access."""
        self.client.logout()
        response = self.client.get('/delivery/admin/reports/')
        self.assertEqual(response.status_code, 302)

    def test_reports_page_accessible_to_staff(self):
        """Staff can access reports page."""
        response = self.client.get('/delivery/admin/reports/')
        self.assertEqual(response.status_code, 200)

    def test_reports_api_returns_stats(self):
        """Reports API returns delivery statistics."""
        response = self.client.get('/api/delivery/admin/reports/')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('stats', data)
        self.assertIn('total', data['stats'])
        self.assertIn('delivered', data['stats'])
        self.assertIn('on_time_rate', data['stats'])

    def test_reports_api_returns_driver_performance(self):
        """Reports API returns driver performance data."""
        response = self.client.get('/api/delivery/admin/reports/')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('driver_performance', data)
        self.assertIsInstance(data['driver_performance'], list)

        if data['driver_performance']:
            driver_data = data['driver_performance'][0]
            self.assertIn('name', driver_data)
            self.assertIn('total_deliveries', driver_data)
            self.assertIn('delivered', driver_data)
            self.assertIn('average_rating', driver_data)

    def test_reports_api_returns_zone_stats(self):
        """Reports API returns zone-based statistics."""
        response = self.client.get('/api/delivery/admin/reports/')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('zone_stats', data)
        self.assertIsInstance(data['zone_stats'], list)

    def test_reports_api_supports_date_range(self):
        """Reports API filters by date range."""
        today = date.today()
        response = self.client.get(
            f'/api/delivery/admin/reports/?start_date={today}&end_date={today}'
        )
        self.assertEqual(response.status_code, 200)

    def test_driver_report_api(self):
        """Driver-specific report endpoint works."""
        response = self.client.get(f'/api/delivery/admin/reports/driver/{self.driver.id}/')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('driver', data)
        self.assertIn('stats', data)
        self.assertEqual(data['driver']['id'], self.driver.id)


class ZoneManagementTests(TestCase):
    """Tests for zone management UI."""

    def setUp(self):
        """Set up test data."""
        self.staff_user = User.objects.create_user(
            'staff', 'staff@test.com', 'staffpass', is_staff=True
        )
        self.client = Client()
        self.client.login(username='staff', password='staffpass')

        # Create test zone
        self.zone = DeliveryZone.objects.create(
            code='CENTRO',
            name='Centro',
            delivery_fee=Decimal('50.00'),
            estimated_time_minutes=45
        )

    def test_zones_page_requires_staff(self):
        """Zones page requires staff access."""
        self.client.logout()
        response = self.client.get('/delivery/admin/zones/')
        self.assertEqual(response.status_code, 302)

    def test_zones_page_accessible_to_staff(self):
        """Staff can access zones page."""
        response = self.client.get('/delivery/admin/zones/')
        self.assertEqual(response.status_code, 200)

    def test_zones_api_list(self):
        """API returns list of zones."""
        response = self.client.get('/api/delivery/admin/zones/')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('zones', data)
        self.assertEqual(len(data['zones']), 1)

    def test_zones_api_create(self):
        """API can create a new zone."""
        response = self.client.post(
            '/api/delivery/admin/zones/',
            data=json.dumps({
                'code': 'NORTE',
                'name': 'Norte',
                'delivery_fee': '60.00',
                'estimated_time_minutes': 30
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)

        data = response.json()
        self.assertEqual(data['zone']['code'], 'NORTE')

    def test_zones_api_update(self):
        """API can update a zone."""
        response = self.client.put(
            f'/api/delivery/admin/zones/{self.zone.id}/',
            data=json.dumps({
                'delivery_fee': '75.00',
                'estimated_time_minutes': 60
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        self.zone.refresh_from_db()
        self.assertEqual(self.zone.delivery_fee, Decimal('75.00'))

    def test_zones_api_delete(self):
        """API can deactivate a zone."""
        response = self.client.delete(f'/api/delivery/admin/zones/{self.zone.id}/')
        self.assertEqual(response.status_code, 200)

        self.zone.refresh_from_db()
        self.assertFalse(self.zone.is_active)


class SlotManagementTests(TestCase):
    """Tests for slot management UI."""

    def setUp(self):
        """Set up test data."""
        self.staff_user = User.objects.create_user(
            'staff', 'staff@test.com', 'staffpass', is_staff=True
        )
        self.client = Client()
        self.client.login(username='staff', password='staffpass')

        # Create zone and slot
        self.zone = DeliveryZone.objects.create(
            code='CENTRO', name='Centro'
        )
        self.slot = DeliverySlot.objects.create(
            zone=self.zone,
            date=date.today(),
            start_time=time(9, 0),
            end_time=time(12, 0),
            capacity=10
        )

    def test_slots_page_requires_staff(self):
        """Slots page requires staff access."""
        self.client.logout()
        response = self.client.get('/delivery/admin/slots/')
        self.assertEqual(response.status_code, 302)

    def test_slots_page_accessible_to_staff(self):
        """Staff can access slots page."""
        response = self.client.get('/delivery/admin/slots/')
        self.assertEqual(response.status_code, 200)

    def test_slots_api_list(self):
        """API returns list of slots."""
        response = self.client.get('/api/delivery/admin/slots/')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('slots', data)

    def test_slots_api_create(self):
        """API can create a new slot."""
        tomorrow = date.today() + timedelta(days=1)
        response = self.client.post(
            '/api/delivery/admin/slots/',
            data=json.dumps({
                'zone_id': self.zone.id,
                'date': str(tomorrow),
                'start_time': '14:00',
                'end_time': '17:00',
                'capacity': 8
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)

        data = response.json()
        self.assertEqual(data['slot']['capacity'], 8)

    def test_slots_api_update(self):
        """API can update a slot."""
        response = self.client.put(
            f'/api/delivery/admin/slots/{self.slot.id}/',
            data=json.dumps({'capacity': 15}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        self.slot.refresh_from_db()
        self.assertEqual(self.slot.capacity, 15)

    def test_slots_api_delete(self):
        """API can deactivate a slot."""
        response = self.client.delete(f'/api/delivery/admin/slots/{self.slot.id}/')
        self.assertEqual(response.status_code, 200)

        self.slot.refresh_from_db()
        self.assertFalse(self.slot.is_active)

    def test_slots_api_bulk_create(self):
        """API can create slots for multiple days."""
        start_date = date.today() + timedelta(days=7)
        response = self.client.post(
            '/api/delivery/admin/slots/bulk/',
            data=json.dumps({
                'zone_id': self.zone.id,
                'start_date': str(start_date),
                'days': 5,
                'slots': [
                    {'start_time': '09:00', 'end_time': '12:00', 'capacity': 5},
                    {'start_time': '14:00', 'end_time': '18:00', 'capacity': 5}
                ]
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)

        data = response.json()
        self.assertEqual(data['created_count'], 10)  # 5 days * 2 slots per day


class ContractorOnboardingTests(TestCase):
    """Tests for contractor onboarding flow."""

    def setUp(self):
        """Set up test data."""
        self.staff_user = User.objects.create_user(
            'staff', 'staff@test.com', 'staffpass', is_staff=True
        )
        self.client = Client()
        self.client.login(username='staff', password='staffpass')

        # Create zone
        self.zone = DeliveryZone.objects.create(code='CENTRO', name='Centro')

        # Create contractor driver
        self.contractor = DeliveryDriver.objects.create(
            user=User.objects.create_user('contractor', 'contractor@test.com', 'pass'),
            driver_type='contractor',
            is_active=True,
            rfc='XAXX010101000',
            curp='XEXX010101HNEXXXA4'
        )
        self.contractor.zones.add(self.zone)

    def test_contractors_page_requires_staff(self):
        """Contractors page requires staff access."""
        self.client.logout()
        response = self.client.get('/delivery/admin/contractors/')
        self.assertEqual(response.status_code, 302)

    def test_contractors_page_accessible_to_staff(self):
        """Staff can access contractors page."""
        response = self.client.get('/delivery/admin/contractors/')
        self.assertEqual(response.status_code, 200)

    def test_contractors_api_list(self):
        """API returns list of contractors."""
        response = self.client.get('/api/delivery/admin/contractors/')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('contractors', data)
        self.assertEqual(len(data['contractors']), 1)
        self.assertEqual(data['contractors'][0]['driver_type'], 'contractor')

    def test_contractors_api_create(self):
        """API can create a new contractor."""
        new_user = User.objects.create_user('newcontractor', 'new@test.com', 'pass')
        response = self.client.post(
            '/api/delivery/admin/contractors/',
            data=json.dumps({
                'user_id': new_user.id,
                'phone': '5551234567',
                'rfc': 'XAXX010101001',
                'curp': 'XEXX010101HNEXXXA5',
                'vehicle_type': 'motorcycle',
                'rate_per_delivery': '50.00',
                'rate_per_km': '5.00',
                'zone_ids': [self.zone.id]
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)

        data = response.json()
        self.assertEqual(data['contractor']['driver_type'], 'contractor')
        self.assertEqual(data['contractor']['onboarding_status'], 'pending')

    def test_contractors_api_update_onboarding_status(self):
        """API can update contractor onboarding status."""
        response = self.client.put(
            f'/api/delivery/admin/contractors/{self.contractor.id}/',
            data=json.dumps({
                'onboarding_status': 'approved',
                'onboarding_notes': 'All documents verified'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        self.contractor.refresh_from_db()
        self.assertEqual(self.contractor.onboarding_status, 'approved')

    def test_validate_rfc_format(self):
        """RFC validation works correctly."""
        # Valid RFC for persona moral (12 chars)
        response = self.client.post(
            '/api/delivery/admin/contractors/validate-rfc/',
            data=json.dumps({'rfc': 'ABC123456AB1'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['valid'])

        # Valid RFC for persona fisica (13 chars)
        response = self.client.post(
            '/api/delivery/admin/contractors/validate-rfc/',
            data=json.dumps({'rfc': 'XAXX010101000'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['valid'])

        # Invalid RFC
        response = self.client.post(
            '/api/delivery/admin/contractors/validate-rfc/',
            data=json.dumps({'rfc': 'INVALID'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['valid'])

    def test_validate_curp_format(self):
        """CURP validation works correctly."""
        # Valid CURP (18 chars)
        response = self.client.post(
            '/api/delivery/admin/contractors/validate-curp/',
            data=json.dumps({'curp': 'XEXX010101HNEXXXA4'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['valid'])

        # Invalid CURP
        response = self.client.post(
            '/api/delivery/admin/contractors/validate-curp/',
            data=json.dumps({'curp': 'INVALID'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['valid'])


class ContractorRatesTests(TestCase):
    """Tests for contractor rate configuration."""

    def setUp(self):
        """Set up test data."""
        self.staff_user = User.objects.create_user(
            'staff', 'staff@test.com', 'staffpass', is_staff=True
        )
        self.client = Client()
        self.client.login(username='staff', password='staffpass')

        # Create contractor
        self.contractor = DeliveryDriver.objects.create(
            user=User.objects.create_user('contractor', 'contractor@test.com', 'pass'),
            driver_type='contractor',
            is_active=True,
            rate_per_delivery=Decimal('50.00'),
            rate_per_km=Decimal('5.00')
        )

    def test_update_contractor_rates(self):
        """Can update contractor payment rates."""
        response = self.client.put(
            f'/api/delivery/admin/contractors/{self.contractor.id}/',
            data=json.dumps({
                'rate_per_delivery': '75.00',
                'rate_per_km': '8.00'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        self.contractor.refresh_from_db()
        self.assertEqual(self.contractor.rate_per_delivery, Decimal('75.00'))
        self.assertEqual(self.contractor.rate_per_km, Decimal('8.00'))

    def test_get_contractor_with_rates(self):
        """API returns contractor with rate information."""
        response = self.client.get(f'/api/delivery/admin/contractors/{self.contractor.id}/')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('rate_per_delivery', data['contractor'])
        self.assertIn('rate_per_km', data['contractor'])


class DeliveryPaymentTests(TestCase):
    """Tests for delivery payment calculation."""

    def setUp(self):
        """Set up test data."""
        # Create customer
        self.customer = User.objects.create_user(
            'customer', 'customer@test.com', 'pass'
        )

        # Create contractor with rates
        self.contractor = DeliveryDriver.objects.create(
            user=User.objects.create_user('driver', 'driver@test.com', 'pass'),
            driver_type='contractor',
            is_active=True,
            rate_per_delivery=Decimal('50.00'),
            rate_per_km=Decimal('5.00')
        )

        # Create zone
        self.zone = DeliveryZone.objects.create(
            name='Test Zone',
            code='TZ',
            delivery_fee=Decimal('50.00')
        )

        # Create product and order
        category = Category.objects.create(name='Test', slug='test-pay')
        product = Product.objects.create(
            name='Test Product',
            slug='test-product-pay',
            category=category,
            price=Decimal('100.00'),
            sku='TEST-PAY-001'
        )

        cart = Cart.objects.create(user=self.customer)
        cart.add_item(product, 1)
        self.order = Order.create_from_cart(
            cart=cart,
            user=self.customer,
            fulfillment_method='delivery',
            payment_method='cash',
            shipping_address='Test Delivery Address'
        )

        # Create delivery
        self.delivery = Delivery.objects.create(
            order=self.order,
            zone=self.zone,
            driver=self.contractor,
            address='Test Delivery Address',
            status='delivered',
            delivered_distance_km=Decimal('10.5')
        )

    def test_calculate_payment_with_flat_rate_only(self):
        """Payment calculates correctly with flat rate only."""
        from apps.delivery.services import DeliveryPaymentService

        # Driver with only flat rate
        self.contractor.rate_per_km = None
        self.contractor.save()

        payment = DeliveryPaymentService.calculate_payment(self.delivery)

        self.assertEqual(payment['flat_rate'], Decimal('50.00'))
        self.assertEqual(payment['distance_payment'], Decimal('0.00'))
        self.assertEqual(payment['total'], Decimal('50.00'))

    def test_calculate_payment_with_distance_rate(self):
        """Payment calculates correctly with distance rate."""
        from apps.delivery.services import DeliveryPaymentService

        payment = DeliveryPaymentService.calculate_payment(self.delivery)

        # 50.00 flat + (5.00 * 10.5 km) = 50 + 52.50 = 102.50
        self.assertEqual(payment['flat_rate'], Decimal('50.00'))
        self.assertEqual(payment['distance_payment'], Decimal('52.50'))
        self.assertEqual(payment['total'], Decimal('102.50'))

    def test_calculate_payment_no_distance(self):
        """Payment calculates correctly when no distance recorded."""
        from apps.delivery.services import DeliveryPaymentService

        self.delivery.delivered_distance_km = None
        self.delivery.save()

        payment = DeliveryPaymentService.calculate_payment(self.delivery)

        self.assertEqual(payment['flat_rate'], Decimal('50.00'))
        self.assertEqual(payment['distance_payment'], Decimal('0.00'))
        self.assertEqual(payment['total'], Decimal('50.00'))

    def test_calculate_payment_employee_no_payment(self):
        """Employee drivers return zero payment."""
        from apps.delivery.services import DeliveryPaymentService

        self.contractor.driver_type = 'employee'
        self.contractor.save()

        payment = DeliveryPaymentService.calculate_payment(self.delivery)

        self.assertEqual(payment['flat_rate'], Decimal('0.00'))
        self.assertEqual(payment['distance_payment'], Decimal('0.00'))
        self.assertEqual(payment['total'], Decimal('0.00'))

    def test_calculate_payment_no_driver(self):
        """Returns None when delivery has no driver."""
        from apps.delivery.services import DeliveryPaymentService

        self.delivery.driver = None
        self.delivery.save()

        payment = DeliveryPaymentService.calculate_payment(self.delivery)

        self.assertIsNone(payment)

    def test_calculate_driver_earnings_period(self):
        """Calculates total earnings for a driver over a period."""
        from apps.delivery.services import DeliveryPaymentService

        # Create additional deliveries
        for i in range(3):
            user = User.objects.create_user(f'pcust{i}', f'pcust{i}@test.com', 'pass')
            category = Category.objects.get(slug='test-pay')
            product = Product.objects.get(slug='test-product-pay')
            cart = Cart.objects.create(user=user)
            cart.add_item(product, 1)
            order = Order.create_from_cart(
                cart=cart,
                user=user,
                fulfillment_method='delivery',
                payment_method='cash',
                shipping_address=f'Delivery Address {i}'
            )
            Delivery.objects.create(
                order=order,
                zone=self.zone,
                driver=self.contractor,
                address=f'Delivery Address {i}',
                status='delivered',
                delivered_distance_km=Decimal('5.0'),
                delivered_at=timezone.now()
            )

        # Calculate earnings (4 deliveries total)
        start_date = date.today() - timedelta(days=1)
        end_date = date.today() + timedelta(days=1)

        earnings = DeliveryPaymentService.calculate_driver_earnings(
            self.contractor, start_date, end_date
        )

        # Original delivery: 50 + (5*10.5) = 102.50
        # 3 new deliveries: 3 * (50 + (5*5)) = 3 * 75 = 225
        # Total: 102.50 + 225 = 327.50
        self.assertEqual(earnings['total_deliveries'], 4)
        self.assertEqual(earnings['total_earnings'], Decimal('327.50'))
        self.assertEqual(earnings['total_flat_rate'], Decimal('200.00'))
        self.assertEqual(earnings['total_distance_payment'], Decimal('127.50'))


class ContractorPaymentReportsTests(TestCase):
    """Tests for contractor payment reports."""

    def setUp(self):
        """Set up test data."""
        self.staff_user = User.objects.create_user(
            'staff', 'staff@test.com', 'staffpass', is_staff=True
        )
        self.client = Client()
        self.client.login(username='staff', password='staffpass')

        # Create zone
        self.zone = DeliveryZone.objects.create(
            name='Test Zone',
            code='TZ',
            delivery_fee=Decimal('50.00')
        )

        # Create contractors with rates
        self.contractor1 = DeliveryDriver.objects.create(
            user=User.objects.create_user('contractor1', 'c1@test.com', 'pass'),
            driver_type='contractor',
            is_active=True,
            rate_per_delivery=Decimal('50.00'),
            rate_per_km=Decimal('5.00'),
            rfc='ABC123456AB1',
            curp='XEXX010101HNEXXXA4'
        )

        self.contractor2 = DeliveryDriver.objects.create(
            user=User.objects.create_user('contractor2', 'c2@test.com', 'pass'),
            driver_type='contractor',
            is_active=True,
            rate_per_delivery=Decimal('60.00'),
            rate_per_km=Decimal('6.00')
        )

        # Create employee (should not appear in contractor reports)
        self.employee = DeliveryDriver.objects.create(
            user=User.objects.create_user('employee', 'emp@test.com', 'pass'),
            driver_type='employee',
            is_active=True
        )

        # Create products and orders
        category = Category.objects.create(name='Food', slug='food-report')
        product = Product.objects.create(
            name='Dog Food', slug='dog-food-report', category=category,
            price=Decimal('100.00'), sku='FOOD-RPT-001'
        )

        # Create deliveries for contractor1
        for i in range(3):
            user = User.objects.create_user(f'custrpt{i}', f'custrpt{i}@test.com', 'pass')
            cart = Cart.objects.create(user=user)
            cart.add_item(product, 1)
            order = Order.create_from_cart(
                cart=cart, user=user, fulfillment_method='delivery',
                payment_method='cash', shipping_address=f'Address {i}'
            )
            Delivery.objects.create(
                order=order, zone=self.zone, driver=self.contractor1,
                address=f'Address {i}', status='delivered',
                delivered_distance_km=Decimal('10.0'),
                delivered_at=timezone.now()
            )

        # Create deliveries for contractor2
        for i in range(2):
            user = User.objects.create_user(f'custrpt2_{i}', f'custrpt2_{i}@test.com', 'pass')
            cart = Cart.objects.create(user=user)
            cart.add_item(product, 1)
            order = Order.create_from_cart(
                cart=cart, user=user, fulfillment_method='delivery',
                payment_method='cash', shipping_address=f'Address 2-{i}'
            )
            Delivery.objects.create(
                order=order, zone=self.zone, driver=self.contractor2,
                address=f'Address 2-{i}', status='delivered',
                delivered_distance_km=Decimal('8.0'),
                delivered_at=timezone.now()
            )

    def test_contractor_payments_api_requires_staff(self):
        """Contractor payments API requires staff access."""
        self.client.logout()
        response = self.client.get('/api/delivery/admin/contractors/payments/')
        self.assertEqual(response.status_code, 302)

    def test_contractor_payments_api_returns_summary(self):
        """Contractor payments API returns payment summary."""
        response = self.client.get('/api/delivery/admin/contractors/payments/')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('contractors', data)
        self.assertIn('totals', data)

    def test_contractor_payments_excludes_employees(self):
        """Contractor payments excludes employee drivers."""
        response = self.client.get('/api/delivery/admin/contractors/payments/')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        contractor_ids = [c['id'] for c in data['contractors']]
        self.assertNotIn(self.employee.id, contractor_ids)

    def test_contractor_payments_calculates_correctly(self):
        """Contractor payments calculates earnings correctly."""
        response = self.client.get('/api/delivery/admin/contractors/payments/')
        self.assertEqual(response.status_code, 200)

        data = response.json()

        # Find contractor1's payment data
        c1_data = next((c for c in data['contractors'] if c['id'] == self.contractor1.id), None)
        self.assertIsNotNone(c1_data)

        # 3 deliveries: 3 * (50 + (5*10)) = 3 * 100 = 300
        self.assertEqual(c1_data['total_deliveries'], 3)
        self.assertEqual(Decimal(c1_data['total_earnings']), Decimal('300.00'))

    def test_contractor_payments_supports_date_filter(self):
        """Contractor payments API supports date range filter."""
        today = date.today()
        response = self.client.get(
            f'/api/delivery/admin/contractors/payments/?start_date={today}&end_date={today}'
        )
        self.assertEqual(response.status_code, 200)

    def test_individual_contractor_payment_report(self):
        """Can get payment report for individual contractor."""
        response = self.client.get(
            f'/api/delivery/admin/contractors/{self.contractor1.id}/payments/'
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('contractor', data)
        self.assertIn('deliveries', data)
        self.assertIn('totals', data)
        self.assertEqual(data['contractor']['id'], self.contractor1.id)

    def test_individual_contractor_payment_lists_deliveries(self):
        """Individual contractor payment report lists deliveries with payment details."""
        response = self.client.get(
            f'/api/delivery/admin/contractors/{self.contractor1.id}/payments/'
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data['deliveries']), 3)

        # Check each delivery has payment breakdown
        for delivery in data['deliveries']:
            self.assertIn('delivery_number', delivery)
            self.assertIn('flat_rate', delivery)
            self.assertIn('distance_payment', delivery)
            self.assertIn('total_payment', delivery)
