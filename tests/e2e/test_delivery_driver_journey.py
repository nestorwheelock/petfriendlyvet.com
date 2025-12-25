"""E2E test for delivery driver journey.

Simulates the complete delivery workflow from driver perspective:
1. Driver is registered and onboarded
2. Driver clocks in and becomes available
3. Delivery is assigned to driver
4. Driver picks up order from clinic
5. Driver updates real-time location
6. Driver arrives at destination
7. Driver captures proof of delivery (photo + GPS)
8. Delivery is marked complete
9. Customer rates the delivery
10. Driver performance metrics updated

Tests the complete delivery driver lifecycle.
"""
import pytest
from decimal import Decimal
from datetime import date, time, timedelta

from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db(transaction=True)
class TestDeliveryDriverJourney:
    """Complete delivery driver journey."""

    @pytest.fixture
    def delivery_zone(self, db):
        """Create a delivery zone."""
        from apps.delivery.models import DeliveryZone

        return DeliveryZone.objects.create(
            code='CDMX-ROMA',
            name='Roma/Condesa',
            name_es='Roma/Condesa',
            delivery_fee=Decimal('45.00'),
            estimated_time_minutes=30,
            is_active=True,
        )

    @pytest.fixture
    def delivery_slot(self, db, delivery_zone):
        """Create a delivery slot."""
        from apps.delivery.models import DeliverySlot

        return DeliverySlot.objects.create(
            zone=delivery_zone,
            date=date.today(),
            start_time=time(9, 0),
            end_time=time(12, 0),
            capacity=10,
            booked_count=0,
            is_active=True,
        )

    @pytest.fixture
    def driver_user(self, db):
        """Create a driver user."""
        return User.objects.create_user(
            username='driver@petfriendlyvet.com',
            email='driver@petfriendlyvet.com',
            password='driver123',
            first_name='Pedro',
            last_name='Conductor',
            role='staff',
        )

    @pytest.fixture
    def customer(self, db):
        """Create a customer."""
        return User.objects.create_user(
            username='customer@example.com',
            email='customer@example.com',
            password='customer123',
            first_name='Ana',
            last_name='Cliente',
            role='owner',
            phone_number='555-987-6543',
        )

    @pytest.fixture
    def product(self, db):
        """Create a product."""
        from apps.store.models import Category, Product

        category = Category.objects.create(
            name='Alimentos',
            slug='alimentos',
            is_active=True,
        )
        return Product.objects.create(
            name='Royal Canin 15kg',
            slug='royal-canin-15kg',
            category=category,
            price=Decimal('1850.00'),
            stock_quantity=50,
            sku='SKU-RC-001',
            is_active=True,
        )

    def test_complete_driver_delivery_journey(
        self, db, delivery_zone, delivery_slot, driver_user, customer, product
    ):
        """
        Test complete driver journey from assignment to completion.

        Driver assigned → Picks up → Delivers → Proof captured → Rated
        """
        from apps.delivery.models import (
            DeliveryDriver, Delivery, DeliveryStatusHistory,
            DeliveryProof, DeliveryRating, DeliveryNotification
        )
        from apps.store.models import Order, OrderItem

        # =========================================================================
        # STEP 1: Driver Registration and Onboarding
        # =========================================================================
        driver = DeliveryDriver.objects.create(
            user=driver_user,
            driver_type='employee',
            phone='555-DRIVER-1',
            vehicle_type='motorcycle',
            license_plate='ABC-123',
            is_active=True,
            is_available=False,  # Not yet available
            max_deliveries_per_day=10,
            contract_signed=True,
            onboarding_status='approved',
        )
        driver.zones.add(delivery_zone)

        assert driver.pk is not None
        assert driver.is_employee is True
        assert driver.is_available is False

        # =========================================================================
        # STEP 2: Driver Clocks In and Becomes Available
        # =========================================================================
        driver.is_available = True
        driver.current_latitude = Decimal('19.4326')
        driver.current_longitude = Decimal('-99.1332')
        driver.location_updated_at = timezone.now()
        driver.save()

        driver.refresh_from_db()
        assert driver.is_available is True
        assert driver.current_latitude is not None

        # =========================================================================
        # STEP 3: Customer Places Order
        # =========================================================================
        order = Order.objects.create(
            user=customer,
            order_number=Order.generate_order_number(),
            status='paid',
            fulfillment_method='delivery',
            payment_method='card',
            shipping_address='Calle Roma 123, Col. Roma, CDMX, CP 06700',
            shipping_phone='555-987-6543',
            subtotal=product.price,
            shipping_cost=delivery_zone.delivery_fee,
            tax=product.price * Decimal('0.16'),
            total=product.price + delivery_zone.delivery_fee + (product.price * Decimal('0.16')),
            paid_at=timezone.now(),
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            product_sku=product.sku,
            price=product.price,
            quantity=1,
        )

        assert order.pk is not None
        assert order.status == 'paid'

        # =========================================================================
        # STEP 4: Delivery Created and Assigned to Driver
        # =========================================================================
        delivery = Delivery.objects.create(
            order=order,
            zone=delivery_zone,
            slot=delivery_slot,
            status='pending',
            address=order.shipping_address,
            latitude=Decimal('19.4200'),
            longitude=Decimal('-99.1500'),
            scheduled_date=delivery_slot.date,
            scheduled_time_start=delivery_slot.start_time,
            scheduled_time_end=delivery_slot.end_time,
        )

        assert delivery.pk is not None
        assert delivery.delivery_number is not None
        assert delivery.status == 'pending'

        # Assign driver
        delivery.driver = driver
        delivery.status = 'assigned'
        delivery.assigned_at = timezone.now()
        delivery.save()

        # Create status history
        DeliveryStatusHistory.objects.create(
            delivery=delivery,
            from_status='pending',
            to_status='assigned',
            changed_by=driver_user,
        )

        delivery.refresh_from_db()
        assert delivery.status == 'assigned'
        assert delivery.driver == driver

        # =========================================================================
        # STEP 5: Driver Notified
        # =========================================================================
        notification = DeliveryNotification.objects.create(
            delivery=delivery,
            notification_type='whatsapp',
            recipient=driver.phone,
            message=f'Nueva entrega asignada: {delivery.delivery_number}. '
                    f'Dirección: {delivery.address}',
            status='sent',
            sent_at=timezone.now(),
        )

        assert notification.pk is not None
        assert notification.status == 'sent'

        # =========================================================================
        # STEP 6: Driver Picks Up Order
        # =========================================================================
        delivery.status = 'picked_up'
        delivery.picked_up_at = timezone.now()
        delivery.save()

        DeliveryStatusHistory.objects.create(
            delivery=delivery,
            from_status='assigned',
            to_status='picked_up',
            changed_by=driver_user,
            latitude=Decimal('19.4326'),
            longitude=Decimal('-99.1332'),
        )

        # Update order status
        order.status = 'preparing'
        order.save()

        # =========================================================================
        # STEP 7: Driver Out for Delivery with Real-time Location Updates
        # =========================================================================
        delivery.status = 'out_for_delivery'
        delivery.out_for_delivery_at = timezone.now()
        delivery.save()

        DeliveryStatusHistory.objects.create(
            delivery=delivery,
            from_status='picked_up',
            to_status='out_for_delivery',
            changed_by=driver_user,
            latitude=Decimal('19.4300'),
            longitude=Decimal('-99.1400'),
        )

        # Simulate location updates during delivery
        location_updates = [
            (Decimal('19.4280'), Decimal('-99.1420')),
            (Decimal('19.4250'), Decimal('-99.1450')),
            (Decimal('19.4220'), Decimal('-99.1480')),
        ]

        for lat, lng in location_updates:
            driver.current_latitude = lat
            driver.current_longitude = lng
            driver.location_updated_at = timezone.now()
            driver.save()

        # =========================================================================
        # STEP 8: Driver Arrives at Destination
        # =========================================================================
        delivery.status = 'arrived'
        delivery.arrived_at = timezone.now()
        delivery.save()

        DeliveryStatusHistory.objects.create(
            delivery=delivery,
            from_status='out_for_delivery',
            to_status='arrived',
            changed_by=driver_user,
            latitude=Decimal('19.4200'),
            longitude=Decimal('-99.1500'),
        )

        # Notify customer
        DeliveryNotification.objects.create(
            delivery=delivery,
            notification_type='sms',
            recipient=order.shipping_phone,
            message=f'Su pedido ha llegado. El repartidor está en su ubicación.',
            status='sent',
            sent_at=timezone.now(),
        )

        # =========================================================================
        # STEP 9: Proof of Delivery Captured
        # =========================================================================
        # Photo proof with GPS
        photo_proof = DeliveryProof.objects.create(
            delivery=delivery,
            proof_type='photo',
            recipient_name='Ana Cliente',
            latitude=Decimal('19.4200'),
            longitude=Decimal('-99.1500'),
            gps_accuracy=Decimal('5.5'),  # 5.5 meters accuracy
        )

        assert photo_proof.pk is not None
        assert photo_proof.recipient_name == 'Ana Cliente'

        # Signature proof
        signature_proof = DeliveryProof.objects.create(
            delivery=delivery,
            proof_type='signature',
            signature_data='base64_encoded_signature_data_here',
            recipient_name='Ana Cliente',
            latitude=Decimal('19.4200'),
            longitude=Decimal('-99.1500'),
            gps_accuracy=Decimal('5.5'),
        )

        assert signature_proof.pk is not None

        # =========================================================================
        # STEP 10: Delivery Marked Complete
        # =========================================================================
        delivery.status = 'delivered'
        delivery.delivered_at = timezone.now()
        delivery.delivered_distance_km = Decimal('3.5')
        delivery.save()

        DeliveryStatusHistory.objects.create(
            delivery=delivery,
            from_status='arrived',
            to_status='delivered',
            changed_by=driver_user,
            latitude=Decimal('19.4200'),
            longitude=Decimal('-99.1500'),
        )

        # Update order status
        order.status = 'delivered'
        order.save()

        # Update driver stats
        driver.total_deliveries += 1
        driver.successful_deliveries += 1
        driver.save()

        # =========================================================================
        # STEP 11: Customer Rates Delivery
        # =========================================================================
        rating = DeliveryRating.objects.create(
            delivery=delivery,
            rating=5,
            comment='Excelente servicio, muy rápido y amable.',
        )

        assert rating.pk is not None
        assert rating.rating == 5

        # Update driver average rating
        all_ratings = DeliveryRating.objects.filter(delivery__driver=driver)
        if all_ratings.exists():
            avg_rating = sum(r.rating for r in all_ratings) / all_ratings.count()
            driver.average_rating = Decimal(str(round(avg_rating, 2)))
            driver.save()

        # =========================================================================
        # VERIFICATION: Complete Journey
        # =========================================================================
        delivery.refresh_from_db()
        driver.refresh_from_db()
        order.refresh_from_db()

        # Delivery completed
        assert delivery.status == 'delivered'
        assert delivery.delivered_at is not None
        assert delivery.proofs.count() == 2

        # Order delivered
        assert order.status == 'delivered'

        # Driver stats updated
        assert driver.total_deliveries >= 1
        assert driver.successful_deliveries >= 1
        assert driver.average_rating == Decimal('5.00')

        # Status history complete
        history = delivery.status_history.all()
        assert history.count() >= 4  # assigned, picked_up, out_for_delivery, arrived, delivered

        # Notifications sent
        assert delivery.notifications.count() >= 2


@pytest.mark.django_db(transaction=True)
class TestDriverContractorWorkflow:
    """Test contractor driver onboarding and payment."""

    def test_contractor_driver_onboarding(self, db):
        """Contractor driver goes through onboarding process."""
        from apps.delivery.models import DeliveryDriver, DeliveryZone

        # Create zone
        zone = DeliveryZone.objects.create(
            code='CDMX-SUR',
            name='Sur de la Ciudad',
            delivery_fee=Decimal('60.00'),
            is_active=True,
        )

        # Create contractor user
        contractor_user = User.objects.create_user(
            username='contractor@example.com',
            email='contractor@example.com',
            password='contractor123',
            first_name='Carlos',
            last_name='Independiente',
            role='staff',
        )

        # Create contractor driver profile
        contractor = DeliveryDriver.objects.create(
            user=contractor_user,
            driver_type='contractor',
            phone='555-CONTRACT',
            vehicle_type='car',
            license_plate='XYZ-789',
            rfc='XAXX010101000',  # Mexican tax ID
            curp='XEXX010101HDFXXX00',  # Mexican personal ID
            rate_per_delivery=Decimal('50.00'),
            rate_per_km=Decimal('5.00'),
            contract_signed=False,
            onboarding_status='pending',
            is_active=False,  # Not active until approved
        )
        contractor.zones.add(zone)

        assert contractor.is_contractor is True
        assert contractor.onboarding_status == 'pending'
        assert contractor.is_active is False

        # Contractor submits documents
        contractor.onboarding_status = 'documents_submitted'
        contractor.save()

        # Admin reviews
        contractor.onboarding_status = 'under_review'
        contractor.save()

        # Admin approves
        contractor.onboarding_status = 'approved'
        contractor.contract_signed = True
        contractor.is_active = True
        contractor.save()

        contractor.refresh_from_db()
        assert contractor.onboarding_status == 'approved'
        assert contractor.is_active is True
        assert contractor.has_complete_payment_info is True


@pytest.mark.django_db(transaction=True)
class TestDeliveryFailureScenarios:
    """Test delivery failure and retry scenarios."""

    @pytest.fixture
    def setup_delivery(self, db):
        """Setup delivery for failure tests."""
        from apps.delivery.models import DeliveryZone, DeliveryDriver, Delivery
        from apps.store.models import Category, Product, Order

        zone = DeliveryZone.objects.create(
            code='CDMX-NORTE',
            name='Norte',
            delivery_fee=Decimal('55.00'),
            is_active=True,
        )

        driver_user = User.objects.create_user(
            username='fail.driver@example.com',
            email='fail.driver@example.com',
            password='driver123',
            role='staff',
        )

        driver = DeliveryDriver.objects.create(
            user=driver_user,
            driver_type='employee',
            is_active=True,
            is_available=True,
        )
        driver.zones.add(zone)

        customer = User.objects.create_user(
            username='fail.customer@example.com',
            email='fail.customer@example.com',
            password='customer123',
            role='owner',
        )

        category = Category.objects.create(name='Test', slug='test', is_active=True)
        product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            category=category,
            price=Decimal('100.00'),
            stock_quantity=10,
            sku='TEST-001',
            is_active=True,
        )

        order = Order.objects.create(
            user=customer,
            order_number=Order.generate_order_number(),
            status='paid',
            fulfillment_method='delivery',
            payment_method='card',
            shipping_address='Dirección de prueba',
            subtotal=Decimal('100.00'),
            shipping_cost=Decimal('55.00'),
            tax=Decimal('16.00'),
            total=Decimal('171.00'),
            paid_at=timezone.now(),
        )

        delivery = Delivery.objects.create(
            order=order,
            zone=zone,
            driver=driver,
            status='assigned',
            address=order.shipping_address,
            assigned_at=timezone.now(),
        )

        return {
            'zone': zone,
            'driver': driver,
            'driver_user': driver_user,
            'customer': customer,
            'order': order,
            'delivery': delivery,
        }

    def test_delivery_failed_customer_not_home(self, setup_delivery):
        """Delivery fails because customer not home."""
        from apps.delivery.models import DeliveryStatusHistory

        data = setup_delivery
        delivery = data['delivery']
        driver_user = data['driver_user']

        # Driver picks up and goes to location
        delivery.status = 'picked_up'
        delivery.picked_up_at = timezone.now()
        delivery.save()

        delivery.status = 'out_for_delivery'
        delivery.out_for_delivery_at = timezone.now()
        delivery.save()

        delivery.status = 'arrived'
        delivery.arrived_at = timezone.now()
        delivery.save()

        # Customer not home - delivery fails
        delivery.status = 'failed'
        delivery.failed_at = timezone.now()
        delivery.failure_reason = 'Cliente no se encuentra en casa. Se intentó 3 veces.'
        delivery.save()

        DeliveryStatusHistory.objects.create(
            delivery=delivery,
            from_status='arrived',
            to_status='failed',
            changed_by=driver_user,
        )

        delivery.refresh_from_db()
        assert delivery.status == 'failed'
        assert 'Cliente no se encuentra' in delivery.failure_reason

    def test_delivery_rescheduled_after_failure(self, setup_delivery):
        """Failed delivery is rescheduled."""
        from apps.delivery.models import DeliveryStatusHistory, DeliverySlot

        data = setup_delivery
        delivery = data['delivery']
        zone = data['zone']

        # Mark as failed
        delivery.status = 'failed'
        delivery.failed_at = timezone.now()
        delivery.failure_reason = 'Dirección incorrecta'
        delivery.save()

        # Create new slot for tomorrow
        tomorrow_slot = DeliverySlot.objects.create(
            zone=zone,
            date=date.today() + timedelta(days=1),
            start_time=time(14, 0),
            end_time=time(17, 0),
            capacity=5,
            is_active=True,
        )

        # Reschedule delivery
        delivery.status = 'assigned'  # Back to assigned
        delivery.slot = tomorrow_slot
        delivery.scheduled_date = tomorrow_slot.date
        delivery.scheduled_time_start = tomorrow_slot.start_time
        delivery.scheduled_time_end = tomorrow_slot.end_time
        delivery.driver_notes = 'Reintento después de falla. Verificar dirección con cliente.'
        delivery.save()

        DeliveryStatusHistory.objects.create(
            delivery=delivery,
            from_status='failed',
            to_status='assigned',
        )

        delivery.refresh_from_db()
        assert delivery.status == 'assigned'
        assert delivery.slot == tomorrow_slot
        assert delivery.scheduled_date == date.today() + timedelta(days=1)
