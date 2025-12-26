"""Tests for inventory CRUD operations (TDD - written first).

Tests for Supplier, Stock Location, PO Lines, Reorder Rules, Product-Supplier links,
StockBatch, and StockLevel.
"""
from decimal import Decimal
from datetime import date, timedelta

import pytest
from django.test import Client
from django.contrib.auth import get_user_model

from apps.inventory.models import (
    LocationType, Supplier, StockLocation, PurchaseOrder, PurchaseOrderLine,
    ReorderRule, ProductSupplier, StockBatch, StockLevel
)
from apps.store.models import Product, Category


User = get_user_model()


@pytest.fixture
def warehouse_type(db):
    """Create or get a warehouse location type."""
    lt, _ = LocationType.objects.get_or_create(
        code='crud_warehouse',
        defaults={
            'name': 'CRUD Test Warehouse',
            'is_active': True
        }
    )
    return lt


@pytest.fixture
def pharmacy_type(db):
    """Create or get a pharmacy location type."""
    lt, _ = LocationType.objects.get_or_create(
        code='crud_pharmacy',
        defaults={
            'name': 'CRUD Test Pharmacy',
            'requires_restricted_access': True,
            'is_active': True
        }
    )
    return lt


@pytest.fixture
def staff_user(db):
    """Create a staff user for tests."""
    return User.objects.create_user(
        username='inventory_crud_staff',
        email='crudstaff@test.com',
        password='testpass123',
        is_staff=True,
    )


@pytest.fixture
def authenticated_client(staff_user):
    """Return a client logged in as staff user with staff token."""
    client = Client()
    client.login(username='inventory_crud_staff', password='testpass123')
    # Access staff hub to generate token
    client.get('/staff/')
    return client


def get_staff_url(client, path):
    """Build staff token URL for a path."""
    session = client.session
    token = session.get('staff_token')
    if token:
        return f'/staff-{token}/{path}'
    return f'/{path}'


# =============================================================================
# SUPPLIER CRUD TESTS
# =============================================================================

@pytest.mark.django_db
class TestSupplierCreate:
    """Tests for supplier_create view."""

    def test_supplier_create_get_returns_form(self, authenticated_client):
        """Test GET request returns form page."""
        url = get_staff_url(authenticated_client, 'operations/inventory/suppliers/add/')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert 'form' in response.context

    def test_supplier_create_post_creates_supplier(self, authenticated_client):
        """Test POST creates supplier and redirects."""
        url = get_staff_url(authenticated_client, 'operations/inventory/suppliers/add/')
        data = {
            'name': 'Test Supplier Inc',
            'code': 'TSI-001',
            'email': 'orders@testsupplier.com',
            'phone': '555-1234',
            'contact_name': 'John Doe',
            'address': '123 Main St\nTest City, TC 12345',
            'payment_terms': 'net30',
            'lead_time_days': 7,
            'is_active': True,
        }
        response = authenticated_client.post(url, data)

        # Should redirect after success
        assert response.status_code == 302

        # Supplier should be created
        supplier = Supplier.objects.filter(name='Test Supplier Inc').first()
        assert supplier is not None
        assert supplier.code == 'TSI-001'
        assert supplier.email == 'orders@testsupplier.com'

    def test_supplier_create_requires_name(self, authenticated_client):
        """Test that name is required."""
        url = get_staff_url(authenticated_client, 'operations/inventory/suppliers/add/')
        data = {
            'email': 'test@example.com',
        }
        response = authenticated_client.post(url, data)

        # Should stay on form with errors
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].errors


@pytest.mark.django_db
class TestSupplierEdit:
    """Tests for supplier_edit view."""

    @pytest.fixture
    def supplier(self, db):
        """Create a supplier for editing."""
        return Supplier.objects.create(
            name='Edit Test Supplier',
            code='ETS-001',
            email='edit@test.com',
            is_active=True
        )

    def test_supplier_edit_get_returns_form(self, authenticated_client, supplier):
        """Test GET request returns form with supplier data."""
        url = get_staff_url(authenticated_client, f'operations/inventory/suppliers/{supplier.pk}/edit/')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].instance == supplier

    def test_supplier_edit_post_updates_supplier(self, authenticated_client, supplier):
        """Test POST updates supplier."""
        url = get_staff_url(authenticated_client, f'operations/inventory/suppliers/{supplier.pk}/edit/')
        data = {
            'name': 'Updated Supplier Name',
            'code': 'UPD-001',
            'email': 'updated@test.com',
            'is_active': True,
        }
        response = authenticated_client.post(url, data)

        # Should redirect after success
        assert response.status_code == 302

        # Supplier should be updated
        supplier.refresh_from_db()
        assert supplier.name == 'Updated Supplier Name'
        assert supplier.code == 'UPD-001'


# =============================================================================
# STOCK LOCATION CRUD TESTS
# =============================================================================

@pytest.mark.django_db
class TestLocationList:
    """Tests for stock_location_list view."""

    def test_location_list_returns_locations(self, authenticated_client, warehouse_type, pharmacy_type):
        """Test list view returns locations."""
        # Create some locations
        StockLocation.objects.create(name='Main Warehouse', location_type=warehouse_type, is_active=True)
        StockLocation.objects.create(name='Pharmacy', location_type=pharmacy_type, is_active=True)

        url = get_staff_url(authenticated_client, 'operations/inventory/locations/')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert 'locations' in response.context
        assert len(response.context['locations']) == 2


@pytest.mark.django_db
class TestLocationCreate:
    """Tests for stock_location_create view."""

    def test_location_create_get_returns_form(self, authenticated_client, warehouse_type):
        """Test GET request returns form page."""
        url = get_staff_url(authenticated_client, 'operations/inventory/locations/add/')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert 'form' in response.context

    def test_location_create_post_creates_location(self, authenticated_client, pharmacy_type):
        """Test POST creates location."""
        url = get_staff_url(authenticated_client, 'operations/inventory/locations/add/')
        data = {
            'name': 'New Pharmacy Storage',
            'location_type': pharmacy_type.pk,
            'description': 'Pharmacy medication storage area',
            'requires_restricted_access': True,
            'is_active': True,
        }
        response = authenticated_client.post(url, data)

        # Should redirect after success
        assert response.status_code == 302

        # Location should be created
        location = StockLocation.objects.filter(name='New Pharmacy Storage').first()
        assert location is not None
        assert location.location_type == pharmacy_type
        assert location.requires_restricted_access is True


@pytest.mark.django_db
class TestLocationEdit:
    """Tests for stock_location_edit view."""

    @pytest.fixture
    def refrigerated_type(self, db):
        """Create or get a refrigerated location type."""
        lt, _ = LocationType.objects.get_or_create(
            code='crud_refrigerated',
            defaults={
                'name': 'CRUD Test Refrigerated',
                'requires_temperature_control': True,
                'is_active': True
            }
        )
        return lt

    def test_location_edit_get_returns_form(self, authenticated_client, warehouse_type):
        """Test GET request returns form with location data."""
        location = StockLocation.objects.create(
            name='Test Location',
            location_type=warehouse_type,
            is_active=True
        )
        url = get_staff_url(authenticated_client, f'operations/inventory/locations/{location.pk}/edit/')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert 'form' in response.context

    def test_location_edit_post_updates_location(self, authenticated_client, warehouse_type, refrigerated_type):
        """Test POST updates location."""
        location = StockLocation.objects.create(
            name='Test Location',
            location_type=warehouse_type,
            is_active=True
        )
        url = get_staff_url(authenticated_client, f'operations/inventory/locations/{location.pk}/edit/')
        data = {
            'name': 'Updated Location Name',
            'location_type': refrigerated_type.pk,
            'requires_temperature_control': True,
            'is_active': True,
        }
        response = authenticated_client.post(url, data)

        # Should redirect after success
        assert response.status_code == 302

        # Location should be updated
        location.refresh_from_db()
        assert location.name == 'Updated Location Name'
        assert location.location_type == refrigerated_type


# =============================================================================
# PURCHASE ORDER LINE CRUD TESTS
# =============================================================================

@pytest.fixture
def category(db):
    """Create a category for products."""
    return Category.objects.create(
        name='Test Category',
        slug='test-category'
    )


@pytest.fixture
def product(db, category):
    """Create a product for tests."""
    return Product.objects.create(
        name='Test Product',
        sku='TEST-001',
        price=Decimal('10.00'),
        category=category,
        is_active=True
    )


@pytest.fixture
def supplier(db):
    """Create a supplier for tests."""
    return Supplier.objects.create(
        name='Test Supplier',
        code='SUP-001',
        is_active=True
    )


@pytest.fixture
def purchase_order(db, supplier):
    """Create a purchase order for tests."""
    return PurchaseOrder.objects.create(
        supplier=supplier,
        po_number='PO-TEST-001',
        status='draft'
    )


@pytest.mark.django_db
class TestPOLineAdd:
    """Tests for adding lines to purchase orders."""

    def test_po_line_add_get_returns_form(self, authenticated_client, purchase_order):
        """Test GET request returns form page."""
        url = get_staff_url(authenticated_client, f'operations/inventory/purchase-orders/{purchase_order.pk}/lines/add/')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert 'form' in response.context

    def test_po_line_add_post_creates_line(self, authenticated_client, purchase_order, product):
        """Test POST creates line item."""
        url = get_staff_url(authenticated_client, f'operations/inventory/purchase-orders/{purchase_order.pk}/lines/add/')
        data = {
            'product': product.pk,
            'quantity_ordered': '10',
            'unit_cost': '5.00',
        }
        response = authenticated_client.post(url, data)

        # Should redirect after success
        assert response.status_code == 302

        # Line should be created
        line = PurchaseOrderLine.objects.filter(purchase_order=purchase_order).first()
        assert line is not None
        assert line.product == product
        assert line.quantity_ordered == Decimal('10')


@pytest.mark.django_db
class TestPOLineEdit:
    """Tests for editing PO lines."""

    @pytest.fixture
    def po_line(self, db, purchase_order, product):
        """Create a PO line for editing."""
        return PurchaseOrderLine.objects.create(
            purchase_order=purchase_order,
            product=product,
            quantity_ordered=Decimal('5'),
            unit_cost=Decimal('10.00'),
            line_total=Decimal('50.00')
        )

    def test_po_line_edit_get_returns_form(self, authenticated_client, purchase_order, po_line):
        """Test GET request returns form with line data."""
        url = get_staff_url(authenticated_client, f'operations/inventory/purchase-orders/{purchase_order.pk}/lines/{po_line.pk}/edit/')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert 'form' in response.context

    def test_po_line_edit_post_updates_line(self, authenticated_client, purchase_order, po_line):
        """Test POST updates line item."""
        url = get_staff_url(authenticated_client, f'operations/inventory/purchase-orders/{purchase_order.pk}/lines/{po_line.pk}/edit/')
        data = {
            'product': po_line.product.pk,
            'quantity_ordered': '20',
            'unit_cost': '8.00',
        }
        response = authenticated_client.post(url, data)

        # Should redirect after success
        assert response.status_code == 302

        # Line should be updated
        po_line.refresh_from_db()
        assert po_line.quantity_ordered == Decimal('20')
        assert po_line.unit_cost == Decimal('8.00')


@pytest.mark.django_db
class TestPOLineDelete:
    """Tests for deleting PO lines."""

    @pytest.fixture
    def po_line(self, db, purchase_order, product):
        """Create a PO line for deletion."""
        return PurchaseOrderLine.objects.create(
            purchase_order=purchase_order,
            product=product,
            quantity_ordered=Decimal('5'),
            unit_cost=Decimal('10.00'),
            line_total=Decimal('50.00')
        )

    def test_po_line_delete_post_removes_line(self, authenticated_client, purchase_order, po_line):
        """Test POST deletes line item."""
        url = get_staff_url(authenticated_client, f'operations/inventory/purchase-orders/{purchase_order.pk}/lines/{po_line.pk}/delete/')
        response = authenticated_client.post(url)

        # Should redirect after success
        assert response.status_code == 302

        # Line should be deleted
        assert not PurchaseOrderLine.objects.filter(pk=po_line.pk).exists()


# =============================================================================
# REORDER RULE CRUD TESTS
# =============================================================================

@pytest.mark.django_db
class TestReorderRuleList:
    """Tests for reorder rule list view."""

    def test_reorder_rule_list_returns_rules(self, authenticated_client, product):
        """Test list view returns reorder rules."""
        ReorderRule.objects.create(
            product=product,
            min_level=Decimal('5'),
            reorder_point=Decimal('10'),
            reorder_quantity=Decimal('50'),
            is_active=True
        )

        url = get_staff_url(authenticated_client, 'operations/inventory/reorder-rules/')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert 'rules' in response.context


@pytest.mark.django_db
class TestReorderRuleCreate:
    """Tests for creating reorder rules."""

    def test_reorder_rule_create_get_returns_form(self, authenticated_client):
        """Test GET request returns form page."""
        url = get_staff_url(authenticated_client, 'operations/inventory/reorder-rules/add/')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert 'form' in response.context

    def test_reorder_rule_create_post_creates_rule(self, authenticated_client, product):
        """Test POST creates reorder rule."""
        url = get_staff_url(authenticated_client, 'operations/inventory/reorder-rules/add/')
        data = {
            'product': product.pk,
            'min_level': '5',
            'reorder_point': '10',
            'reorder_quantity': '50',
            'is_active': True,
        }
        response = authenticated_client.post(url, data)

        # Should redirect after success
        assert response.status_code == 302

        # Rule should be created
        rule = ReorderRule.objects.filter(product=product).first()
        assert rule is not None
        assert rule.min_level == Decimal('5')


@pytest.mark.django_db
class TestReorderRuleEdit:
    """Tests for editing reorder rules."""

    @pytest.fixture
    def reorder_rule(self, db, product):
        """Create a reorder rule for editing."""
        return ReorderRule.objects.create(
            product=product,
            min_level=Decimal('5'),
            reorder_point=Decimal('10'),
            reorder_quantity=Decimal('50'),
            is_active=True
        )

    def test_reorder_rule_edit_get_returns_form(self, authenticated_client, reorder_rule):
        """Test GET request returns form with rule data."""
        url = get_staff_url(authenticated_client, f'operations/inventory/reorder-rules/{reorder_rule.pk}/edit/')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert 'form' in response.context

    def test_reorder_rule_edit_post_updates_rule(self, authenticated_client, reorder_rule):
        """Test POST updates reorder rule."""
        url = get_staff_url(authenticated_client, f'operations/inventory/reorder-rules/{reorder_rule.pk}/edit/')
        data = {
            'product': reorder_rule.product.pk,
            'min_level': '10',
            'reorder_point': '20',
            'reorder_quantity': '100',
            'is_active': True,
        }
        response = authenticated_client.post(url, data)

        # Should redirect after success
        assert response.status_code == 302

        # Rule should be updated
        reorder_rule.refresh_from_db()
        assert reorder_rule.min_level == Decimal('10')
        assert reorder_rule.reorder_quantity == Decimal('100')


# =============================================================================
# PRODUCT-SUPPLIER LINK CRUD TESTS
# =============================================================================

@pytest.mark.django_db
class TestProductSupplierList:
    """Tests for product-supplier link list view."""

    def test_product_supplier_list_returns_links(self, authenticated_client, product, supplier):
        """Test list view returns product-supplier links."""
        ProductSupplier.objects.create(
            product=product,
            supplier=supplier,
            unit_cost=Decimal('5.00'),
            is_active=True
        )

        url = get_staff_url(authenticated_client, 'operations/inventory/product-suppliers/')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert 'links' in response.context


@pytest.mark.django_db
class TestProductSupplierCreate:
    """Tests for creating product-supplier links."""

    def test_product_supplier_create_get_returns_form(self, authenticated_client):
        """Test GET request returns form page."""
        url = get_staff_url(authenticated_client, 'operations/inventory/product-suppliers/add/')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert 'form' in response.context

    def test_product_supplier_create_post_creates_link(self, authenticated_client, product, supplier):
        """Test POST creates product-supplier link."""
        url = get_staff_url(authenticated_client, 'operations/inventory/product-suppliers/add/')
        data = {
            'product': product.pk,
            'supplier': supplier.pk,
            'unit_cost': '5.00',
            'minimum_order_quantity': '1',
            'is_active': True,
        }
        response = authenticated_client.post(url, data)

        # Should redirect after success
        assert response.status_code == 302

        # Link should be created
        link = ProductSupplier.objects.filter(product=product, supplier=supplier).first()
        assert link is not None
        assert link.unit_cost == Decimal('5.00')


@pytest.mark.django_db
class TestProductSupplierEdit:
    """Tests for editing product-supplier links."""

    @pytest.fixture
    def product_supplier(self, db, product, supplier):
        """Create a product-supplier link for editing."""
        return ProductSupplier.objects.create(
            product=product,
            supplier=supplier,
            unit_cost=Decimal('5.00'),
            minimum_order_quantity=Decimal('1'),
            is_active=True
        )

    def test_product_supplier_edit_get_returns_form(self, authenticated_client, product_supplier):
        """Test GET request returns form with link data."""
        url = get_staff_url(authenticated_client, f'operations/inventory/product-suppliers/{product_supplier.pk}/edit/')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert 'form' in response.context

    def test_product_supplier_edit_post_updates_link(self, authenticated_client, product_supplier):
        """Test POST updates product-supplier link."""
        url = get_staff_url(authenticated_client, f'operations/inventory/product-suppliers/{product_supplier.pk}/edit/')
        data = {
            'product': product_supplier.product.pk,
            'supplier': product_supplier.supplier.pk,
            'unit_cost': '7.50',
            'minimum_order_quantity': '5',
            'is_preferred': True,
            'is_active': True,
        }
        response = authenticated_client.post(url, data)

        # Should redirect after success
        assert response.status_code == 302

        # Link should be updated
        product_supplier.refresh_from_db()
        assert product_supplier.unit_cost == Decimal('7.50')
        assert product_supplier.is_preferred is True


# =============================================================================
# STOCK BATCH CRUD TESTS
# =============================================================================

@pytest.fixture
def location(db, warehouse_type):
    """Create a location for batch tests."""
    return StockLocation.objects.create(
        name='Test Warehouse',
        location_type=warehouse_type,
        is_active=True
    )


@pytest.mark.django_db
class TestBatchList:
    """Tests for batch list view."""

    def test_batch_list_returns_batches(self, authenticated_client, product, location):
        """Test list view returns batches."""
        StockBatch.objects.create(
            product=product,
            location=location,
            batch_number='BATCH-001',
            initial_quantity=Decimal('100'),
            current_quantity=Decimal('100'),
            status='available',
            received_date=date.today(),
            unit_cost=Decimal('10.00')
        )

        url = get_staff_url(authenticated_client, 'operations/inventory/batches/')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert 'batches' in response.context


@pytest.mark.django_db
class TestBatchCreate:
    """Tests for creating batches."""

    def test_batch_create_get_returns_form(self, authenticated_client):
        """Test GET request returns form page."""
        url = get_staff_url(authenticated_client, 'operations/inventory/batches/add/')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert 'form' in response.context

    def test_batch_create_post_creates_batch(self, authenticated_client, product, location):
        """Test POST creates batch."""
        url = get_staff_url(authenticated_client, 'operations/inventory/batches/add/')
        data = {
            'product': product.pk,
            'location': location.pk,
            'batch_number': 'NEW-BATCH-001',
            'lot_number': 'LOT-123',
            'initial_quantity': '50',
            'current_quantity': '50',
            'unit_cost': '10.00',
            'received_date': date.today().isoformat(),
            'expiry_date': (date.today() + timedelta(days=365)).isoformat(),
            'status': 'available',
        }
        response = authenticated_client.post(url, data)

        # Should redirect after success
        assert response.status_code == 302

        # Batch should be created
        batch = StockBatch.objects.filter(batch_number='NEW-BATCH-001').first()
        assert batch is not None
        assert batch.product == product
        assert batch.initial_quantity == Decimal('50')


@pytest.mark.django_db
class TestBatchEdit:
    """Tests for editing batches."""

    @pytest.fixture
    def batch(self, db, product, location):
        """Create a batch for editing."""
        return StockBatch.objects.create(
            product=product,
            location=location,
            batch_number='EDIT-BATCH',
            initial_quantity=Decimal('100'),
            current_quantity=Decimal('80'),
            status='available',
            received_date=date.today(),
            unit_cost=Decimal('10.00')
        )

    def test_batch_edit_get_returns_form(self, authenticated_client, batch):
        """Test GET request returns form with batch data."""
        url = get_staff_url(authenticated_client, f'operations/inventory/batches/{batch.pk}/edit/')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert 'form' in response.context

    def test_batch_edit_post_updates_batch(self, authenticated_client, batch):
        """Test POST updates batch."""
        url = get_staff_url(authenticated_client, f'operations/inventory/batches/{batch.pk}/edit/')
        data = {
            'product': batch.product.pk,
            'location': batch.location.pk,
            'batch_number': 'UPDATED-BATCH',
            'lot_number': 'UPDATED-LOT',
            'initial_quantity': str(batch.initial_quantity),
            'current_quantity': '60',
            'unit_cost': '10.00',
            'received_date': date.today().isoformat(),
            'status': 'low',
        }
        response = authenticated_client.post(url, data)

        # Should redirect after success
        assert response.status_code == 302

        # Batch should be updated
        batch.refresh_from_db()
        assert batch.batch_number == 'UPDATED-BATCH'
        assert batch.current_quantity == Decimal('60')
        assert batch.status == 'low'


# =============================================================================
# STOCK LEVEL CRUD TESTS
# =============================================================================

@pytest.mark.django_db
class TestStockLevelList:
    """Tests for stock level list view."""

    def test_stock_level_list_returns_levels(self, authenticated_client, product, location):
        """Test list view returns stock levels."""
        StockLevel.objects.create(
            product=product,
            location=location,
            quantity=Decimal('100')
        )

        url = get_staff_url(authenticated_client, 'operations/inventory/stock/')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        # The existing stock view uses low_stock and normal_stock context vars
        assert 'normal_stock' in response.context or 'low_stock' in response.context


@pytest.mark.django_db
class TestStockLevelCreate:
    """Tests for creating stock levels."""

    def test_stock_level_create_get_returns_form(self, authenticated_client):
        """Test GET request returns form page."""
        url = get_staff_url(authenticated_client, 'operations/inventory/stock/add/')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert 'form' in response.context

    def test_stock_level_create_post_creates_level(self, authenticated_client, product, location):
        """Test POST creates stock level."""
        url = get_staff_url(authenticated_client, 'operations/inventory/stock/add/')
        data = {
            'product': product.pk,
            'location': location.pk,
            'quantity': '100',
            'min_level': '10',
            'reorder_quantity': '50',
        }
        response = authenticated_client.post(url, data)

        # Should redirect after success
        assert response.status_code == 302

        # Stock level should be created
        level = StockLevel.objects.filter(product=product, location=location).first()
        assert level is not None
        assert level.quantity == Decimal('100')


@pytest.mark.django_db
class TestStockLevelEdit:
    """Tests for editing stock levels."""

    @pytest.fixture
    def stock_level(self, db, product, location):
        """Create a stock level for editing."""
        return StockLevel.objects.create(
            product=product,
            location=location,
            quantity=Decimal('50'),
            min_level=Decimal('10'),
            reorder_quantity=Decimal('50')
        )

    def test_stock_level_edit_get_returns_form(self, authenticated_client, stock_level):
        """Test GET request returns form with stock level data."""
        url = get_staff_url(authenticated_client, f'operations/inventory/stock/{stock_level.pk}/edit/')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert 'form' in response.context

    def test_stock_level_edit_post_updates_level(self, authenticated_client, stock_level):
        """Test POST updates stock level."""
        url = get_staff_url(authenticated_client, f'operations/inventory/stock/{stock_level.pk}/edit/')
        data = {
            'product': stock_level.product.pk,
            'location': stock_level.location.pk,
            'quantity': '75',
            'min_level': '15',
            'reorder_quantity': '100',
        }
        response = authenticated_client.post(url, data)

        # Should redirect after success
        assert response.status_code == 302

        # Stock level should be updated
        stock_level.refresh_from_db()
        assert stock_level.quantity == Decimal('75')
        assert stock_level.min_level == Decimal('15')


@pytest.mark.django_db
class TestStockLevelAdjust:
    """Tests for stock level adjustment view."""

    @pytest.fixture
    def stock_level(self, db, product, location):
        """Create a stock level for adjustment."""
        return StockLevel.objects.create(
            product=product,
            location=location,
            quantity=Decimal('50')
        )

    def test_stock_level_adjust_get_returns_form(self, authenticated_client, stock_level):
        """Test GET request returns adjustment form."""
        url = get_staff_url(authenticated_client, f'operations/inventory/stock/{stock_level.pk}/adjust/')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert 'stock_level' in response.context

    def test_stock_level_adjust_post_adjusts_quantity(self, authenticated_client, stock_level):
        """Test POST adjusts stock level quantity."""
        url = get_staff_url(authenticated_client, f'operations/inventory/stock/{stock_level.pk}/adjust/')
        data = {
            'adjustment': '-10',
            'reason': 'Damaged items removed',
        }
        response = authenticated_client.post(url, data)

        # Should redirect after success
        assert response.status_code == 302

        # Stock level should be adjusted
        stock_level.refresh_from_db()
        assert stock_level.quantity == Decimal('40')
