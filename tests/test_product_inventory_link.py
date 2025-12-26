"""Tests for Product-InventoryItem integration (TDD).

Tests for:
- Product.inventory_item FK link
- Product.tax_rate_override
- Product.get_tax_rate() method
"""
import pytest
from decimal import Decimal


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
def iva_0(db):
    """Create IVA 0% tax rate."""
    from apps.billing.models import TaxRate
    return TaxRate.objects.create(
        code='IVA0',
        name='IVA 0%',
        tax_type='iva',
        rate=Decimal('0.0000'),
        sat_impuesto_code='002',
        sat_tipo_factor='Tasa',
        is_default=False,
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
        sku='INV-001',
        name='Test Inventory Item',
        item_type='resale',
        sat_product_code=sat_product_code,
        sat_unit_code=sat_unit_code,
        tax_rate=iva_16,
        cost_price=Decimal('100.00'),
        sale_price=Decimal('150.00'),
    )


@pytest.fixture
def category(db):
    """Create a product category."""
    from apps.store.models import Category
    return Category.objects.create(
        name='Pet Food',
        name_es='Alimento para Mascotas',
        name_en='Pet Food',
        slug='pet-food'
    )


@pytest.fixture
def product(db, category):
    """Create a product without inventory item link."""
    from apps.store.models import Product
    return Product.objects.create(
        name='Test Product',
        name_es='Producto de Prueba',
        name_en='Test Product',
        slug='test-product',
        category=category,
        price=Decimal('199.99'),
        sku='PROD-001',
    )


@pytest.fixture
def linked_product(db, category, inventory_item):
    """Create a product linked to inventory item."""
    from apps.store.models import Product
    return Product.objects.create(
        name='Linked Product',
        name_es='Producto Vinculado',
        name_en='Linked Product',
        slug='linked-product',
        category=category,
        price=Decimal('150.00'),
        sku='PROD-002',
        inventory_item=inventory_item,
    )


class TestProductInventoryItemLink:
    """Tests for Product-InventoryItem relationship."""

    def test_product_without_inventory_item(self, product):
        """Product can exist without inventory item link."""
        assert product.inventory_item is None

    def test_product_with_inventory_item(self, linked_product, inventory_item):
        """Product can be linked to inventory item."""
        assert linked_product.inventory_item == inventory_item
        assert linked_product.inventory_item.sku == 'INV-001'

    def test_inventory_item_has_store_product(self, linked_product, inventory_item):
        """InventoryItem can access its store product."""
        assert inventory_item.store_product == linked_product

    def test_one_to_one_relationship(self, db, category, inventory_item):
        """Only one product can link to an inventory item."""
        from apps.store.models import Product
        from django.db import IntegrityError

        # First product links successfully
        Product.objects.create(
            name='First Product',
            name_es='Primer Producto',
            name_en='First Product',
            slug='first-product',
            category=category,
            price=Decimal('100.00'),
            sku='FIRST-001',
            inventory_item=inventory_item,
        )

        # Second product cannot link to same inventory item
        with pytest.raises(IntegrityError):
            Product.objects.create(
                name='Second Product',
                name_es='Segundo Producto',
                name_en='Second Product',
                slug='second-product',
                category=category,
                price=Decimal('100.00'),
                sku='SECOND-001',
                inventory_item=inventory_item,
            )


class TestProductTaxRateOverride:
    """Tests for Product tax rate override."""

    def test_product_without_tax_override(self, product):
        """Product can exist without tax rate override."""
        assert product.tax_rate_override is None

    def test_product_with_tax_override(self, db, product, iva_0):
        """Product can have tax rate override."""
        product.tax_rate_override = iva_0
        product.save()
        product.refresh_from_db()
        assert product.tax_rate_override == iva_0


class TestProductGetTaxRate:
    """Tests for Product.get_tax_rate() method."""

    def test_get_tax_rate_no_links(self, db, product, iva_16):
        """Product without links returns default tax rate."""
        tax_rate = product.get_tax_rate()
        assert tax_rate == iva_16  # Default rate

    def test_get_tax_rate_from_inventory_item(self, linked_product, iva_16):
        """Product with inventory item returns item's tax rate."""
        tax_rate = linked_product.get_tax_rate()
        assert tax_rate == iva_16
        assert tax_rate == linked_product.inventory_item.tax_rate

    def test_get_tax_rate_override_takes_precedence(self, db, linked_product, iva_0):
        """Tax rate override takes precedence over inventory item rate."""
        linked_product.tax_rate_override = iva_0
        linked_product.save()

        tax_rate = linked_product.get_tax_rate()
        assert tax_rate == iva_0
        assert tax_rate != linked_product.inventory_item.tax_rate

    def test_get_tax_rate_fallback_to_default(self, db, product, iva_16):
        """Product without inventory item or override uses default."""
        # Product has no inventory_item and no tax_rate_override
        tax_rate = product.get_tax_rate()
        assert tax_rate.is_default is True
        assert tax_rate.code == 'IVA16'
