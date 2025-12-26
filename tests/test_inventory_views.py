"""Tests for inventory views (TDD - Phase 2).

Tests written FIRST before implementation per 23-step TDD cycle.
"""
import pytest
from decimal import Decimal
from django.test import Client, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware

from apps.inventory.models import (
    StockLocation, StockLevel, StockBatch, StockMovement,
    Supplier, PurchaseOrder, PurchaseOrderLine, StockCount, LocationType
)
from apps.store.models import Product, Category


User = get_user_model()


@pytest.fixture
def staff_user(db):
    """Create a staff user for tests."""
    return User.objects.create_user(
        username='inventory_view_staff',
        email='viewstaff@test.com',
        password='testpass123',
        is_staff=True,
    )


@pytest.fixture
def authenticated_client(staff_user):
    """Return a client logged in as staff user with staff token."""
    client = Client()
    client.login(username='inventory_view_staff', password='testpass123')
    # Access staff hub to generate token
    client.get('/staff/')
    return client


def get_staff_url(client, path):
    """Build staff token URL for a path like 'operations/inventory/movements/add/'."""
    session = client.session
    token = session.get('staff_token')
    if token:
        return f'/staff-{token}/{path}'
    return f'/{path}'


@pytest.fixture
def location(db):
    """Create a stock location."""
    warehouse_type, _ = LocationType.objects.get_or_create(
        code='warehouse',
        defaults={'name': 'Warehouse', 'is_active': True},
    )
    return StockLocation.objects.create(
        name='Main Warehouse',
        location_type=warehouse_type,
        is_active=True
    )


@pytest.fixture
def second_location(db):
    """Create a second stock location."""
    pharmacy_type, _ = LocationType.objects.get_or_create(
        code='pharmacy',
        defaults={'name': 'Pharmacy', 'is_active': True},
    )
    return StockLocation.objects.create(
        name='Pharmacy Storage',
        location_type=pharmacy_type,
        is_active=True
    )


@pytest.fixture
def category(db):
    """Create a product category."""
    return Category.objects.create(
        name='Pet Food',
        slug='pet-food'
    )


@pytest.fixture
def product(db, category):
    """Create a product for testing."""
    return Product.objects.create(
        name='Dog Food Premium',
        slug='dog-food-premium',
        sku='DF-001',
        price=Decimal('49.99'),
        category=category,
        is_active=True
    )


@pytest.fixture
def supplier(db):
    """Create a supplier."""
    return Supplier.objects.create(
        name='Pet Supplies Inc',
        email='orders@petsupplies.com',
        is_active=True
    )


@pytest.fixture
def stock_level(db, product, location):
    """Create initial stock level."""
    return StockLevel.objects.create(
        product=product,
        location=location,
        quantity=Decimal('100'),
        reserved_quantity=Decimal('0')
    )


@pytest.fixture
def stock_batch(db, product, location, supplier):
    """Create a stock batch."""
    from django.utils import timezone
    return StockBatch.objects.create(
        product=product,
        location=location,
        batch_number='BATCH-001',
        lot_number='LOT-001',
        initial_quantity=Decimal('100'),
        current_quantity=Decimal('100'),
        received_date=timezone.now().date(),
        unit_cost=Decimal('35.00'),
        supplier=supplier,
        status='available'
    )


# =============================================================================
# VIEW TESTS - Movement Add
# =============================================================================

@pytest.mark.django_db
class TestMovementAddView:
    """Tests for movement_add view."""

    def test_movement_add_get_returns_form(self, authenticated_client):
        """Test GET request returns form page."""
        url = get_staff_url(authenticated_client, 'operations/inventory/movements/add/')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert 'form' in response.context

    def test_movement_add_post_creates_movement(
        self, authenticated_client, product, location, stock_level
    ):
        """Test POST creates movement and updates stock."""
        url = get_staff_url(authenticated_client, 'operations/inventory/movements/add/')
        data = {
            'movement_type': 'receive',
            'product': product.id,
            'to_location': location.id,
            'quantity': '50',
            'reason': 'Test receive',
        }
        response = authenticated_client.post(url, data)

        # Should redirect after success
        assert response.status_code == 302

        # Movement should be created
        assert StockMovement.objects.filter(
            product=product,
            movement_type='receive',
            quantity=Decimal('50')
        ).exists()

        # Stock level should be updated
        stock_level.refresh_from_db()
        assert stock_level.quantity == Decimal('150')  # 100 + 50

    def test_movement_add_requires_staff(self, client, product, location):
        """Test that movement_add requires staff login."""
        # Unauthenticated access to /operations/inventory/ is blocked
        url = '/operations/inventory/movements/add/'
        response = client.get(url)
        # Should get 404 (blocked by middleware) or redirect to login
        assert response.status_code in [302, 404]

    def test_movement_add_sale_decreases_stock(
        self, authenticated_client, product, location, stock_level, stock_batch
    ):
        """Test sale movement decreases stock."""
        url = get_staff_url(authenticated_client, 'operations/inventory/movements/add/')
        data = {
            'movement_type': 'sale',
            'product': product.id,
            'from_location': location.id,
            'batch': stock_batch.id,
            'quantity': '10',
            'reason': 'Customer sale',
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == 302

        stock_level.refresh_from_db()
        assert stock_level.quantity == Decimal('90')  # 100 - 10

        stock_batch.refresh_from_db()
        assert stock_batch.current_quantity == Decimal('90')


# =============================================================================
# VIEW TESTS - Purchase Order Create
# =============================================================================

@pytest.mark.django_db
class TestPurchaseOrderCreateView:
    """Tests for purchase_order_create view."""

    def test_po_create_get_returns_form(self, authenticated_client):
        """Test GET request returns form page."""
        url = get_staff_url(authenticated_client, 'operations/inventory/purchase-orders/create/')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert 'form' in response.context

    def test_po_create_post_creates_order(
        self, authenticated_client, supplier, location
    ):
        """Test POST creates purchase order."""
        from django.utils import timezone
        url = get_staff_url(authenticated_client, 'operations/inventory/purchase-orders/create/')
        data = {
            'supplier': supplier.id,
            'expected_date': timezone.now().date().isoformat(),
            'delivery_location': location.id,
            'notes': 'Test order',
        }
        response = authenticated_client.post(url, data)

        # Should redirect to PO detail or list
        assert response.status_code == 302

        # PO should be created with generated number
        po = PurchaseOrder.objects.filter(supplier=supplier).first()
        assert po is not None
        assert po.po_number.startswith('PO-')


# =============================================================================
# VIEW TESTS - Purchase Order Receive
# =============================================================================

@pytest.mark.django_db
class TestPurchaseOrderReceiveView:
    """Tests for purchase_order_receive view."""

    def test_po_receive_get_shows_lines(
        self, authenticated_client, supplier, location, product
    ):
        """Test GET shows PO lines to receive."""
        po = PurchaseOrder.objects.create(
            po_number='PO-TEST-VIEW-001',
            supplier=supplier,
            delivery_location=location,
            status='confirmed'
        )
        PurchaseOrderLine.objects.create(
            purchase_order=po,
            product=product,
            quantity_ordered=Decimal('50'),
            unit_cost=Decimal('35.00'),
            line_total=Decimal('1750.00')
        )

        url = get_staff_url(authenticated_client, f'operations/inventory/purchase-orders/{po.pk}/receive/')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_po_receive_post_receives_items(
        self, authenticated_client, supplier, location, product
    ):
        """Test POST receives items and creates batch."""
        from django.utils import timezone

        po = PurchaseOrder.objects.create(
            po_number='PO-TEST-VIEW-002',
            supplier=supplier,
            delivery_location=location,
            status='confirmed'
        )
        line = PurchaseOrderLine.objects.create(
            purchase_order=po,
            product=product,
            quantity_ordered=Decimal('50'),
            unit_cost=Decimal('35.00'),
            line_total=Decimal('1750.00')
        )

        url = get_staff_url(authenticated_client, f'operations/inventory/purchase-orders/{po.pk}/receive/')
        data = {
            f'line_{line.id}_quantity': '50',
            f'line_{line.id}_batch_number': 'BATCH-RCV-001',
            f'line_{line.id}_lot_number': 'LOT-001',
        }
        response = authenticated_client.post(url, data)

        # Should redirect after success
        assert response.status_code == 302

        # Batch should be created
        assert StockBatch.objects.filter(batch_number='BATCH-RCV-001').exists()

        # PO should be marked as received
        po.refresh_from_db()
        assert po.status == 'received'


# =============================================================================
# VIEW TESTS - Stock Count Create
# =============================================================================

@pytest.mark.django_db
class TestStockCountCreateView:
    """Tests for stock_count_create view."""

    def test_count_create_get_returns_form(self, authenticated_client, location):
        """Test GET request returns form page."""
        url = get_staff_url(authenticated_client, 'operations/inventory/stock-counts/create/')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert 'form' in response.context

    def test_count_create_post_creates_count(
        self, authenticated_client, location, stock_level
    ):
        """Test POST creates stock count with lines."""
        from django.utils import timezone
        url = get_staff_url(authenticated_client, 'operations/inventory/stock-counts/create/')
        data = {
            'location': location.id,
            'count_type': 'full',
            'count_date': timezone.now().date().isoformat(),
        }
        response = authenticated_client.post(url, data)

        # Should redirect to count entry
        assert response.status_code == 302

        # Count should be created with lines
        count = StockCount.objects.filter(location=location).first()
        assert count is not None
        assert count.lines.count() >= 1


# =============================================================================
# VIEW TESTS - Stock Count Entry
# =============================================================================

@pytest.mark.django_db
class TestStockCountEntryView:
    """Tests for stock_count_entry view."""

    def test_count_entry_get_shows_lines(
        self, authenticated_client, location, stock_level, staff_user
    ):
        """Test GET shows count lines to fill."""
        from django.utils import timezone
        count = StockCount.objects.create(
            location=location,
            count_type='full',
            count_date=timezone.now().date(),
            counted_by=staff_user,
            status='draft'
        )
        line = count.lines.create(
            product=stock_level.product,
            system_quantity=stock_level.quantity
        )

        url = get_staff_url(authenticated_client, f'operations/inventory/stock-counts/{count.pk}/entry/')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_count_entry_post_saves_counts(
        self, authenticated_client, location, stock_level, staff_user
    ):
        """Test POST saves counted quantities."""
        from django.utils import timezone
        count = StockCount.objects.create(
            location=location,
            count_type='full',
            count_date=timezone.now().date(),
            counted_by=staff_user,
            status='draft'
        )
        line = count.lines.create(
            product=stock_level.product,
            system_quantity=Decimal('100')
        )

        url = get_staff_url(authenticated_client, f'operations/inventory/stock-counts/{count.pk}/entry/')
        data = {
            f'line_{line.id}_counted': '95',
            f'line_{line.id}_reason': 'Found 5 damaged',
        }
        response = authenticated_client.post(url, data)

        line.refresh_from_db()
        assert line.counted_quantity == Decimal('95')


# =============================================================================
# VIEW TESTS - Transfer Create
# =============================================================================

@pytest.mark.django_db
class TestTransferCreateView:
    """Tests for transfer_create view."""

    def test_transfer_create_get_returns_form(self, authenticated_client):
        """Test GET request returns form page."""
        url = get_staff_url(authenticated_client, 'operations/inventory/transfers/create/')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert 'form' in response.context

    def test_transfer_create_post_transfers_stock(
        self, authenticated_client, product, location, second_location,
        stock_level, stock_batch
    ):
        """Test POST creates transfer movements."""
        url = get_staff_url(authenticated_client, 'operations/inventory/transfers/create/')
        data = {
            'product': product.id,
            'batch': stock_batch.id,
            'from_location': location.id,
            'to_location': second_location.id,
            'quantity': '25',
            'reason': 'Restocking pharmacy',
        }
        response = authenticated_client.post(url, data)

        # Should redirect after success
        assert response.status_code == 302

        # Source stock should decrease
        stock_level.refresh_from_db()
        assert stock_level.quantity == Decimal('75')  # 100 - 25

        # Destination stock should increase
        dest_stock = StockLevel.objects.get(
            product=product,
            location=second_location
        )
        assert dest_stock.quantity == Decimal('25')
