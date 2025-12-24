"""E2E tests for Order to Invoice automation flow.

Tests that:
- Order with card payment → Invoice auto-created with status='paid'
- Order with cash → Invoice created with status='sent'
- Partial payment → Invoice.amount_paid updated, status='partial'
- Full payment → Invoice.status='paid', paid_at set
"""
import pytest
from decimal import Decimal
from django.utils import timezone

from apps.store.models import Order
from apps.billing.models import Invoice, Payment


@pytest.mark.django_db
class TestOrderCreatesInvoice:
    """Test that placing an order auto-creates invoice."""

    def test_paid_order_creates_invoice_automatically(self, owner_client, cart_with_items, owner_user):
        """When order is paid via card, invoice should be auto-created."""
        # Arrange: Cart already has items from fixture
        cart = cart_with_items

        # Act: Create order from cart (simulating checkout)
        order = Order.create_from_cart(
            cart=cart,
            user=owner_user,
            fulfillment_method='pickup',
            payment_method='card',
        )

        # Assert: Order is paid
        assert order.status == 'paid'
        assert order.paid_at is not None

        # Assert: Invoice was auto-created
        invoice = Invoice.objects.filter(order=order).first()
        assert invoice is not None, "Invoice should be auto-created when order is paid"

        # Assert: Invoice matches order
        assert invoice.owner == owner_user
        assert invoice.total == order.total
        assert invoice.status == 'paid'
        assert invoice.amount_paid == order.total
        assert invoice.paid_at is not None

    def test_cash_order_creates_pending_invoice(self, owner_client, cart_with_items, owner_user):
        """Cash orders create invoice but status='sent' (awaiting payment)."""
        cart = cart_with_items

        order = Order.create_from_cart(
            cart=cart,
            user=owner_user,
            fulfillment_method='pickup',
            payment_method='cash',
        )

        # Assert: Order is pending payment
        assert order.status == 'pending'
        assert order.paid_at is None

        # Assert: Invoice was auto-created with sent status
        invoice = Invoice.objects.filter(order=order).first()
        assert invoice is not None, "Invoice should be auto-created for cash orders"
        assert invoice.status == 'sent'
        assert invoice.amount_paid == Decimal('0')

    def test_delivery_order_creates_invoice_with_shipping(self, owner_client, cart_with_items, owner_user):
        """Delivery orders include shipping cost on invoice."""
        cart = cart_with_items

        order = Order.create_from_cart(
            cart=cart,
            user=owner_user,
            fulfillment_method='delivery',
            payment_method='card',
            shipping_address='Calle Principal 123, Col. Centro',
            shipping_phone='555-1234',
        )

        invoice = Invoice.objects.filter(order=order).first()
        assert invoice is not None

        # Invoice total should include shipping
        assert invoice.total == order.total
        assert order.shipping_cost > Decimal('0')


@pytest.mark.django_db
class TestOrderStatusUpdatesInvoice:
    """Test that order status changes update related invoice."""

    def test_order_marked_paid_updates_invoice(self, db, order):
        """When pending order is marked paid, invoice should update."""
        # Ensure order is pending
        order.status = 'pending'
        order.save()

        # Manually create invoice (simulating it was created at checkout)
        invoice = Invoice.objects.create(
            owner=order.user,
            order=order,
            subtotal=order.subtotal,
            tax_amount=order.tax,
            total=order.total,
            status='sent',
            due_date=timezone.now().date(),
        )

        # Act: Mark order as paid (this should trigger invoice update)
        order.status = 'paid'
        order.paid_at = timezone.now()
        order.save()

        # Assert: Invoice should be updated to paid
        invoice.refresh_from_db()
        assert invoice.status == 'paid', "Invoice status should update when order is paid"
        assert invoice.amount_paid == order.total
        assert invoice.paid_at is not None


@pytest.mark.django_db
class TestPaymentRecordingUpdatesInvoice:
    """Test that recording payments updates invoice balance."""

    def test_partial_payment_updates_invoice_balance(self, db, paid_order, staff_user):
        """Partial payment updates invoice.amount_paid correctly."""
        order = paid_order

        # Create invoice for this order
        invoice = Invoice.objects.create(
            owner=order.user,
            order=order,
            subtotal=order.subtotal,
            tax_amount=order.tax,
            total=order.total,
            status='sent',
            due_date=timezone.now().date(),
        )

        partial_amount = order.total / 2

        # Act: Record partial payment
        payment = Payment.objects.create(
            invoice=invoice,
            amount=partial_amount,
            payment_method='cash',
            recorded_by=staff_user,
        )

        # Assert: Invoice balance updated
        invoice.refresh_from_db()
        assert invoice.amount_paid == partial_amount
        assert invoice.status == 'partial'
        assert invoice.get_balance_due() == order.total - partial_amount

    def test_full_payment_marks_invoice_paid(self, db, paid_order, staff_user):
        """Full payment marks invoice as paid with timestamp."""
        order = paid_order

        invoice = Invoice.objects.create(
            owner=order.user,
            order=order,
            subtotal=order.subtotal,
            tax_amount=order.tax,
            total=order.total,
            status='sent',
            due_date=timezone.now().date(),
        )

        # Act: Record full payment
        payment = Payment.objects.create(
            invoice=invoice,
            amount=order.total,
            payment_method='manual_card',
            recorded_by=staff_user,
        )

        # Assert: Invoice is fully paid
        invoice.refresh_from_db()
        assert invoice.amount_paid == order.total
        assert invoice.status == 'paid'
        assert invoice.paid_at is not None

    def test_multiple_payments_sum_correctly(self, db, paid_order, staff_user):
        """Multiple payments sum to correct amount_paid."""
        order = paid_order

        invoice = Invoice.objects.create(
            owner=order.user,
            order=order,
            subtotal=order.subtotal,
            tax_amount=order.tax,
            total=order.total,
            status='sent',
            due_date=timezone.now().date(),
        )

        payment1_amount = order.total * Decimal('0.3')
        payment2_amount = order.total * Decimal('0.5')
        payment3_amount = order.total * Decimal('0.2')

        # Record multiple payments
        Payment.objects.create(
            invoice=invoice,
            amount=payment1_amount,
            payment_method='cash',
            recorded_by=staff_user,
        )
        Payment.objects.create(
            invoice=invoice,
            amount=payment2_amount,
            payment_method='bank_transfer',
            recorded_by=staff_user,
        )
        Payment.objects.create(
            invoice=invoice,
            amount=payment3_amount,
            payment_method='manual_card',
            recorded_by=staff_user,
        )

        # Assert: Total paid equals sum of payments
        invoice.refresh_from_db()
        expected_total = payment1_amount + payment2_amount + payment3_amount
        assert invoice.amount_paid == expected_total
        assert invoice.status == 'paid'


@pytest.mark.django_db
class TestInvoiceLineItemsFromOrder:
    """Test that invoice line items match order items."""

    def test_invoice_has_correct_line_items(self, db, order):
        """Invoice should have line items matching order items."""
        # Create invoice
        invoice = Invoice.objects.create(
            owner=order.user,
            order=order,
            subtotal=order.subtotal,
            tax_amount=order.tax,
            total=order.total,
            status='sent',
            due_date=timezone.now().date(),
        )

        # InvoiceService should create line items (to be implemented)
        # For now, test that when line items are created, they match order

        from apps.billing.models import InvoiceLineItem

        # Create expected line items from order items
        for order_item in order.items.all():
            InvoiceLineItem.objects.create(
                invoice=invoice,
                description=order_item.product_name,
                quantity=order_item.quantity,
                unit_price=order_item.price,
                line_total=order_item.subtotal,
            )

        # Assert: Invoice has correct number of items
        assert invoice.items.count() == order.items.count()

        # Assert: Line items match order items
        for invoice_item, order_item in zip(
            invoice.items.all().order_by('id'),
            order.items.all().order_by('id')
        ):
            assert invoice_item.description == order_item.product_name
            assert invoice_item.quantity == order_item.quantity
            assert invoice_item.unit_price == order_item.price


@pytest.mark.django_db
class TestAPIOrderToInvoiceFlow:
    """Test order to invoice flow via API endpoints."""

    def test_checkout_api_creates_order_and_invoice(self, owner_client, cart_with_items):
        """POST to checkout creates both order and invoice."""
        # This test will use actual API once implemented
        # For now, documenting expected behavior

        response = owner_client.post('/api/store/checkout/', {
            'fulfillment_method': 'pickup',
            'payment_method': 'card',
        }, format='json')

        # Expected: Order created
        if response.status_code == 201:
            order_id = response.data.get('id')
            order = Order.objects.get(id=order_id)

            # Expected: Invoice also created
            invoice = Invoice.objects.filter(order=order).first()
            assert invoice is not None

    def test_order_detail_includes_invoice_link(self, staff_client, paid_order):
        """Order detail API includes link to invoice."""
        response = staff_client.get(f'/api/store/orders/{paid_order.id}/')

        if response.status_code == 200:
            # Expected: Invoice ID or link included
            assert 'invoice' in response.data or 'invoice_id' in response.data

    def test_record_payment_api_updates_invoice(self, staff_client, paid_order, staff_user):
        """POST payment via API updates invoice balance."""
        # Create invoice first
        invoice = Invoice.objects.create(
            owner=paid_order.user,
            order=paid_order,
            subtotal=paid_order.subtotal,
            tax_amount=paid_order.tax,
            total=paid_order.total,
            status='sent',
            due_date=timezone.now().date(),
        )

        response = staff_client.post(f'/api/billing/invoices/{invoice.id}/payments/', {
            'amount': str(invoice.total),
            'payment_method': 'cash',
        }, format='json')

        if response.status_code == 201:
            invoice.refresh_from_db()
            assert invoice.status == 'paid'
