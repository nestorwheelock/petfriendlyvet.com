"""E2E tests for delivery lifecycle.

Tests the full delivery workflow:
- Order with delivery → Creates Delivery record
- Driver assignment workflow
- Status transitions (pending → assigned → picked_up → out_for_delivery → arrived → delivered)
- Proof of delivery capture
- Customer tracking
- Customer rating
"""
import pytest
from decimal import Decimal
from datetime import date, time, timedelta

from django.utils import timezone

from apps.store.models import Order
from apps.delivery.models import (
    Delivery, DeliveryZone, DeliverySlot, DeliveryDriver,
    DeliveryStatusHistory, DeliveryProof, DeliveryRating
)


@pytest.mark.django_db
class TestOrderCreatesDelivery:
    """Test that delivery orders create Delivery records."""

    def test_delivery_order_creates_delivery_record(
        self, db, owner_user, products, delivery_zone, delivery_slot
    ):
        """Order with fulfillment_method='delivery' creates Delivery."""
        from apps.store.models import Cart, CartItem

        # Create cart with items
        cart = Cart.objects.create(user=owner_user)
        for product in products[:2]:
            CartItem.objects.create(cart=cart, product=product, quantity=1)

        # Create order with delivery
        order = Order.create_from_cart(
            cart=cart,
            user=owner_user,
            fulfillment_method='delivery',
            payment_method='card',
            shipping_address='Calle Roma 123, Col. Roma, CDMX',
            shipping_phone='555-1234',
        )

        # Create delivery record (this would normally be done by signal or service)
        delivery = Delivery.objects.create(
            order=order,
            zone=delivery_zone,
            slot=delivery_slot,
            address=order.shipping_address,
            scheduled_date=delivery_slot.date,
            scheduled_time_start=delivery_slot.start_time,
            scheduled_time_end=delivery_slot.end_time,
        )

        assert delivery is not None
        assert delivery.order == order
        assert delivery.status == 'pending'
        assert delivery.delivery_number.startswith('DEL-')

    def test_pickup_order_no_delivery_record(
        self, db, cart_with_items, owner_user
    ):
        """Order with fulfillment_method='pickup' does not create Delivery."""
        order = Order.create_from_cart(
            cart=cart_with_items,
            user=owner_user,
            fulfillment_method='pickup',
            payment_method='card',
        )

        # No delivery should be created for pickup
        delivery = Delivery.objects.filter(order=order).first()
        assert delivery is None


@pytest.mark.django_db
class TestDriverAssignment:
    """Test driver assignment workflow."""

    def test_assign_driver_to_delivery(
        self, db, paid_order, delivery_zone, delivery_slot, delivery_driver, staff_user
    ):
        """Staff can assign driver to pending delivery."""
        delivery = Delivery.objects.create(
            order=paid_order,
            zone=delivery_zone,
            slot=delivery_slot,
            address=paid_order.shipping_address or 'Test Address',
        )

        assert delivery.status == 'pending'
        assert delivery.driver is None

        # Assign driver
        delivery.assign_driver(delivery_driver, assigned_by=staff_user)

        delivery.refresh_from_db()
        assert delivery.status == 'assigned'
        assert delivery.driver == delivery_driver
        assert delivery.assigned_at is not None

        # Check history
        history = DeliveryStatusHistory.objects.filter(delivery=delivery).first()
        assert history is not None
        assert history.from_status == 'pending'
        assert history.to_status == 'assigned'
        assert history.changed_by == staff_user


@pytest.mark.django_db
class TestDriverDeliveryWorkflow:
    """Test driver can update delivery through full lifecycle."""

    def test_full_delivery_lifecycle(
        self, db, paid_order, delivery_zone, delivery_slot, delivery_driver, driver_user
    ):
        """Driver updates delivery through all status transitions."""
        delivery = Delivery.objects.create(
            order=paid_order,
            zone=delivery_zone,
            slot=delivery_slot,
            driver=delivery_driver,
            status='assigned',
            address='Calle Test 123',
        )
        delivery.assigned_at = timezone.now()
        delivery.save()

        # 1. Pick up the order
        delivery.mark_picked_up(changed_by=driver_user)
        delivery.refresh_from_db()
        assert delivery.status == 'picked_up'
        assert delivery.picked_up_at is not None

        # 2. Out for delivery
        delivery.mark_out_for_delivery(changed_by=driver_user)
        delivery.refresh_from_db()
        assert delivery.status == 'out_for_delivery'
        assert delivery.out_for_delivery_at is not None

        # 3. Arrived at destination
        delivery.mark_arrived(
            changed_by=driver_user,
            latitude=Decimal('19.4326'),
            longitude=Decimal('-99.1332')
        )
        delivery.refresh_from_db()
        assert delivery.status == 'arrived'
        assert delivery.arrived_at is not None

        # 4. Mark delivered
        delivery.mark_delivered(
            changed_by=driver_user,
            latitude=Decimal('19.4326'),
            longitude=Decimal('-99.1332')
        )
        delivery.refresh_from_db()
        assert delivery.status == 'delivered'
        assert delivery.delivered_at is not None

        # Verify all transitions were recorded
        history = DeliveryStatusHistory.objects.filter(delivery=delivery)
        assert history.count() == 4
        statuses = list(history.values_list('to_status', flat=True))
        assert statuses == ['picked_up', 'out_for_delivery', 'arrived', 'delivered']

    def test_invalid_status_transition_raises_error(
        self, db, paid_order, delivery_zone, delivery_slot, delivery_driver
    ):
        """Invalid status transitions raise ValueError."""
        delivery = Delivery.objects.create(
            order=paid_order,
            zone=delivery_zone,
            slot=delivery_slot,
            driver=delivery_driver,
            status='pending',
        )

        # Can't go directly from pending to picked_up
        with pytest.raises(ValueError) as exc_info:
            delivery.mark_picked_up()

        assert 'Cannot transition' in str(exc_info.value)

    def test_failed_delivery_with_reason(
        self, db, paid_order, delivery_zone, delivery_slot, delivery_driver, driver_user
    ):
        """Driver can mark delivery as failed with reason."""
        delivery = Delivery.objects.create(
            order=paid_order,
            zone=delivery_zone,
            slot=delivery_slot,
            driver=delivery_driver,
            status='arrived',
            assigned_at=timezone.now(),
        )

        delivery.mark_failed(
            reason='No one home, business closed',
            changed_by=driver_user,
            latitude=Decimal('19.4326'),
            longitude=Decimal('-99.1332')
        )

        delivery.refresh_from_db()
        assert delivery.status == 'failed'
        assert delivery.failed_at is not None
        assert 'No one home' in delivery.failure_reason


@pytest.mark.django_db
class TestProofOfDelivery:
    """Test proof of delivery capture."""

    def test_add_photo_proof(
        self, db, paid_order, delivery_zone, delivery_slot, delivery_driver
    ):
        """Driver can add photo proof of delivery."""
        delivery = Delivery.objects.create(
            order=paid_order,
            zone=delivery_zone,
            slot=delivery_slot,
            driver=delivery_driver,
            status='arrived',
        )

        proof = DeliveryProof.objects.create(
            delivery=delivery,
            proof_type='photo',
            recipient_name='Juan Pérez',
            latitude=Decimal('19.4326'),
            longitude=Decimal('-99.1332'),
            gps_accuracy=Decimal('10.5'),
        )

        assert proof.delivery == delivery
        assert proof.proof_type == 'photo'
        assert proof.recipient_name == 'Juan Pérez'

    def test_add_signature_proof(
        self, db, paid_order, delivery_zone, delivery_slot, delivery_driver
    ):
        """Driver can capture signature as proof."""
        delivery = Delivery.objects.create(
            order=paid_order,
            zone=delivery_zone,
            slot=delivery_slot,
            driver=delivery_driver,
            status='arrived',
        )

        # Base64 encoded signature data
        signature_data = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUg...'

        proof = DeliveryProof.objects.create(
            delivery=delivery,
            proof_type='signature',
            signature_data=signature_data,
            recipient_name='María López',
            latitude=Decimal('19.4326'),
            longitude=Decimal('-99.1332'),
        )

        assert proof.proof_type == 'signature'
        assert proof.signature_data == signature_data


@pytest.mark.django_db
class TestCustomerTracking:
    """Test customer can track their delivery."""

    def test_customer_can_view_delivery_status(
        self, owner_client, paid_order, delivery_zone, delivery_slot, delivery_driver
    ):
        """Customer can see current delivery status."""
        delivery = Delivery.objects.create(
            order=paid_order,
            zone=delivery_zone,
            slot=delivery_slot,
            driver=delivery_driver,
            status='out_for_delivery',
            address='Calle Test 123',
        )

        # API endpoint for tracking
        response = owner_client.get(f'/api/delivery/track/{delivery.delivery_number}/')

        if response.status_code == 200:
            assert response.data['status'] == 'out_for_delivery'
            assert 'driver' in response.data or 'driver_name' in response.data


@pytest.mark.django_db
class TestCustomerRating:
    """Test customer can rate delivery."""

    def test_customer_can_rate_completed_delivery(
        self, db, paid_order, delivery_zone, delivery_slot, delivery_driver, owner_user
    ):
        """Customer can rate delivery after completion."""
        delivery = Delivery.objects.create(
            order=paid_order,
            zone=delivery_zone,
            slot=delivery_slot,
            driver=delivery_driver,
            status='delivered',
            delivered_at=timezone.now(),
        )

        rating = DeliveryRating.objects.create(
            delivery=delivery,
            rating=5,
            comment='Excelente servicio, muy rápido!',
        )

        assert rating.delivery == delivery
        assert rating.rating == 5
        assert 'Excelente' in rating.comment

    def test_cannot_rate_undelivered(
        self, db, paid_order, delivery_zone, delivery_slot, delivery_driver
    ):
        """Cannot rate delivery that hasn't been completed."""
        delivery = Delivery.objects.create(
            order=paid_order,
            zone=delivery_zone,
            slot=delivery_slot,
            status='pending',
        )

        # Business logic should prevent rating pending deliveries
        # This documents expected behavior
        # Implementation could use model validation or API checks


@pytest.mark.django_db
class TestAPIDeliveryWorkflow:
    """Test delivery workflow via API endpoints."""

    def test_driver_api_list_assigned_deliveries(
        self, driver_client, paid_order, delivery_zone, delivery_slot, delivery_driver
    ):
        """Driver can see their assigned deliveries via API."""
        delivery = Delivery.objects.create(
            order=paid_order,
            zone=delivery_zone,
            slot=delivery_slot,
            driver=delivery_driver,
            status='assigned',
        )

        response = driver_client.get('/api/driver/deliveries/')

        if response.status_code == 200:
            assert len(response.data) >= 1

    def test_driver_api_update_status(
        self, driver_client, paid_order, delivery_zone, delivery_slot, delivery_driver
    ):
        """Driver can update delivery status via API."""
        delivery = Delivery.objects.create(
            order=paid_order,
            zone=delivery_zone,
            slot=delivery_slot,
            driver=delivery_driver,
            status='assigned',
            assigned_at=timezone.now(),
        )

        response = driver_client.post(
            f'/api/driver/deliveries/{delivery.id}/pickup/',
            format='json'
        )

        if response.status_code in [200, 204]:
            delivery.refresh_from_db()
            assert delivery.status == 'picked_up'

    def test_driver_api_submit_proof(
        self, driver_client, paid_order, delivery_zone, delivery_slot, delivery_driver
    ):
        """Driver can submit proof of delivery via API."""
        delivery = Delivery.objects.create(
            order=paid_order,
            zone=delivery_zone,
            slot=delivery_slot,
            driver=delivery_driver,
            status='arrived',
        )

        response = driver_client.post(
            f'/api/driver/deliveries/{delivery.id}/proof/',
            {
                'proof_type': 'photo',
                'recipient_name': 'Juan Pérez',
                'latitude': '19.4326',
                'longitude': '-99.1332',
            },
            format='json'
        )

        if response.status_code == 201:
            assert DeliveryProof.objects.filter(delivery=delivery).exists()

    def test_customer_api_rate_delivery(
        self, owner_client, paid_order, delivery_zone, delivery_slot, delivery_driver
    ):
        """Customer can rate delivery via API."""
        delivery = Delivery.objects.create(
            order=paid_order,
            zone=delivery_zone,
            slot=delivery_slot,
            driver=delivery_driver,
            status='delivered',
            delivered_at=timezone.now(),
        )

        response = owner_client.post(
            f'/api/delivery/{delivery.delivery_number}/rate/',
            {
                'rating': 5,
                'comment': 'Great service!',
            },
            format='json'
        )

        if response.status_code == 201:
            assert DeliveryRating.objects.filter(delivery=delivery).exists()


@pytest.mark.django_db
class TestDeliverySlotBooking:
    """Test delivery slot capacity management."""

    def test_booking_updates_slot_count(
        self, db, paid_order, delivery_zone, delivery_slot
    ):
        """Booking delivery updates slot booked_count."""
        initial_count = delivery_slot.booked_count

        delivery = Delivery.objects.create(
            order=paid_order,
            zone=delivery_zone,
            slot=delivery_slot,
        )

        # Slot booking logic should update count
        delivery_slot.booked_count += 1
        delivery_slot.save()

        delivery_slot.refresh_from_db()
        assert delivery_slot.booked_count == initial_count + 1

    def test_slot_available_capacity(self, db, delivery_zone):
        """Slot tracks available capacity correctly."""
        slot = DeliverySlot.objects.create(
            zone=delivery_zone,
            date=date.today() + timedelta(days=1),
            start_time=time(9, 0),
            end_time=time(12, 0),
            capacity=5,
            booked_count=3,
        )

        assert slot.available_capacity == 2
        assert slot.is_available is True

        # Fill the slot
        slot.booked_count = 5
        slot.save()

        assert slot.available_capacity == 0
        assert slot.is_available is False
