"""Tests for InventoryItem CRUD views (TDD).

Tests for:
- InventoryItem list view
- InventoryItem create view
- InventoryItem edit view
- InventoryItem detail view
"""
import pytest
from decimal import Decimal

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def staff_user(db):
    """Create a staff user."""
    return User.objects.create_user(
        username='inv_staff',
        email='invstaff@test.com',
        password='testpass123',
        is_staff=True,
        is_active=True
    )


@pytest.fixture
def authenticated_client(staff_user):
    """Return a logged-in client with staff token."""
    client = Client()
    client.login(username='inv_staff', password='testpass123')
    # Access staff hub to generate token
    client.get('/staff/')
    return client


def get_staff_url(client, path):
    """Build staff token URL for a path."""
    session = client.session
    token = session.get('staff_token')
    if token:
        return f'/staff-{token}/operations/inventory/{path}'
    return f'/operations/inventory/{path}'


@pytest.fixture
def iva_16(db):
    """Create IVA 16% tax rate."""
    from apps.billing.models import TaxRate
    return TaxRate.objects.create(
        code='IVA16',
        name='IVA 16%',
        tax_type='iva',
        rate=Decimal('0.1600'),
        sat_impuesto_code='002',
        sat_tipo_factor='Tasa',
        is_default=True,
    )


@pytest.fixture
def sat_product_code(db):
    """Create a SAT product code."""
    from apps.billing.models import SATProductCode
    return SATProductCode.objects.create(
        code='50112001',
        description='Alimentos para animales'
    )


@pytest.fixture
def sat_unit_code(db):
    """Create a SAT unit code."""
    from apps.billing.models import SATUnitCode
    return SATUnitCode.objects.create(
        code='H87',
        name='Pieza'
    )


@pytest.fixture
def inventory_item(db, iva_16, sat_product_code, sat_unit_code):
    """Create an inventory item."""
    from apps.inventory.models import InventoryItem
    return InventoryItem.objects.create(
        sku='TEST-001',
        name='Test Item',
        item_type='resale',
        sat_product_code=sat_product_code,
        sat_unit_code=sat_unit_code,
        tax_rate=iva_16,
        cost_price=Decimal('100.00'),
        sale_price=Decimal('150.00'),
    )


@pytest.mark.django_db
class TestInventoryItemList:
    """Tests for inventory item list view."""

    def test_list_requires_auth(self, client, db):
        """List view requires authentication."""
        response = client.get('/staff/')
        assert response.status_code in [302, 403]

    def test_list_shows_items(self, authenticated_client, inventory_item):
        """List view shows inventory items."""
        url = get_staff_url(authenticated_client, 'items/')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert b'Test Item' in response.content

    def test_list_filters_by_type(self, authenticated_client, inventory_item):
        """List view can filter by item type."""
        url = get_staff_url(authenticated_client, 'items/?item_type=resale')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert b'Test Item' in response.content

    def test_list_shows_item_type_badge(self, authenticated_client, inventory_item):
        """List view shows item type badge."""
        url = get_staff_url(authenticated_client, 'items/')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        # Should show resale type
        assert b'resale' in response.content.lower() or b'Resale' in response.content


@pytest.mark.django_db
class TestInventoryItemCreate:
    """Tests for inventory item create view."""

    def test_create_get(self, authenticated_client, iva_16, sat_product_code, sat_unit_code):
        """Create form loads correctly."""
        url = get_staff_url(authenticated_client, 'items/add/')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_create_post(self, authenticated_client, iva_16, sat_product_code, sat_unit_code):
        """Can create an inventory item via POST."""
        from apps.inventory.models import InventoryItem

        url = get_staff_url(authenticated_client, 'items/add/')
        data = {
            'sku': 'NEW-001',
            'name': 'New Item',
            'item_type': 'supply',
            'sat_product_code': sat_product_code.code,
            'sat_unit_code': sat_unit_code.code,
            'tax_rate': iva_16.pk,
            'cost_price': '50.00',
            'track_inventory': 'on',
            'is_active': 'on',
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == 302  # Redirect on success

        item = InventoryItem.objects.get(sku='NEW-001')
        assert item.name == 'New Item'
        assert item.item_type == 'supply'

    def test_create_duplicate_sku_error(self, authenticated_client, inventory_item, iva_16, sat_product_code, sat_unit_code):
        """Cannot create with duplicate SKU."""
        url = get_staff_url(authenticated_client, 'items/add/')
        data = {
            'sku': 'TEST-001',  # Already exists
            'name': 'Duplicate',
            'item_type': 'supply',
            'sat_product_code': sat_product_code.code,
            'sat_unit_code': sat_unit_code.code,
            'tax_rate': iva_16.pk,
            'cost_price': '50.00',
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == 200  # Form re-rendered with error


@pytest.mark.django_db
class TestInventoryItemEdit:
    """Tests for inventory item edit view."""

    def test_edit_get(self, authenticated_client, inventory_item):
        """Edit form loads with existing data."""
        url = get_staff_url(authenticated_client, f'items/{inventory_item.pk}/edit/')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert b'Test Item' in response.content

    def test_edit_post(self, authenticated_client, inventory_item, iva_16, sat_product_code, sat_unit_code):
        """Can update inventory item via POST."""
        url = get_staff_url(authenticated_client, f'items/{inventory_item.pk}/edit/')
        data = {
            'sku': 'TEST-001',
            'name': 'Updated Item',
            'item_type': 'resale',
            'sat_product_code': sat_product_code.code,
            'sat_unit_code': sat_unit_code.code,
            'tax_rate': iva_16.pk,
            'cost_price': '100.00',
            'sale_price': '200.00',
            'track_inventory': 'on',
            'is_active': 'on',
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == 302  # Redirect on success

        inventory_item.refresh_from_db()
        assert inventory_item.name == 'Updated Item'
        assert inventory_item.sale_price == Decimal('200.00')


@pytest.mark.django_db
class TestInventoryItemDetail:
    """Tests for inventory item detail view."""

    def test_detail_view(self, authenticated_client, inventory_item):
        """Detail view shows item information."""
        url = get_staff_url(authenticated_client, f'items/{inventory_item.pk}/')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert b'Test Item' in response.content
        assert b'TEST-001' in response.content
