"""Tests for InventoryItem model (TDD).

Tests for:
- InventoryItem model creation with different item types
- SAT compliance fields
- Accounting integration fields
- Item type specific validation
"""
import pytest
from decimal import Decimal

from django.db import IntegrityError


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
def resale_item(db, iva_16, sat_product_code, sat_unit_code):
    """Create a resale inventory item."""
    from apps.inventory.models import InventoryItem
    return InventoryItem.objects.create(
        sku='PF-001',
        name='Premium Dog Food',
        item_type='resale',
        sat_product_code=sat_product_code,
        sat_unit_code=sat_unit_code,
        tax_rate=iva_16,
        cost_price=Decimal('150.00'),
        sale_price=Decimal('250.00'),
    )


@pytest.fixture
def supply_item(db, iva_16, sat_product_code, sat_unit_code):
    """Create a supply inventory item."""
    from apps.inventory.models import InventoryItem
    return InventoryItem.objects.create(
        sku='SUP-001',
        name='Toilet Paper',
        item_type='supply',
        sat_product_code=sat_product_code,
        sat_unit_code=sat_unit_code,
        tax_rate=iva_16,
        cost_price=Decimal('50.00'),
    )


@pytest.fixture
def consumable_item(db, iva_16, sat_product_code, sat_unit_code):
    """Create a consumable inventory item."""
    from apps.inventory.models import InventoryItem
    return InventoryItem.objects.create(
        sku='CON-001',
        name='Sterile Syringe 5ml',
        item_type='consumable',
        sat_product_code=sat_product_code,
        sat_unit_code=sat_unit_code,
        tax_rate=iva_16,
        cost_price=Decimal('5.00'),
    )


@pytest.fixture
def equipment_item(db, iva_16, sat_product_code, sat_unit_code):
    """Create an equipment inventory item."""
    from apps.inventory.models import InventoryItem
    return InventoryItem.objects.create(
        sku='EQP-001',
        name='Stethoscope',
        item_type='equipment',
        sat_product_code=sat_product_code,
        sat_unit_code=sat_unit_code,
        tax_rate=iva_16,
        cost_price=Decimal('2500.00'),
        is_depreciable=True,
        useful_life_months=60,
    )


class TestInventoryItemModel:
    """Tests for InventoryItem model."""

    def test_inventoryitem_create_resale(self, resale_item):
        """Can create a resale inventory item."""
        assert resale_item.pk is not None
        assert resale_item.sku == 'PF-001'
        assert resale_item.item_type == 'resale'
        assert resale_item.sale_price == Decimal('250.00')
        assert resale_item.is_active is True  # default

    def test_inventoryitem_create_supply(self, supply_item):
        """Can create a supply inventory item."""
        assert supply_item.pk is not None
        assert supply_item.item_type == 'supply'
        assert supply_item.sale_price is None  # Supplies not for sale

    def test_inventoryitem_create_consumable(self, consumable_item):
        """Can create a consumable inventory item."""
        assert consumable_item.pk is not None
        assert consumable_item.item_type == 'consumable'

    def test_inventoryitem_create_equipment(self, equipment_item):
        """Can create an equipment inventory item."""
        assert equipment_item.pk is not None
        assert equipment_item.item_type == 'equipment'
        assert equipment_item.is_depreciable is True
        assert equipment_item.useful_life_months == 60

    def test_inventoryitem_str(self, resale_item):
        """String representation shows SKU and name."""
        result = str(resale_item)
        assert 'PF-001' in result or 'Premium Dog Food' in result

    def test_inventoryitem_sku_unique(self, db, resale_item, iva_16, sat_product_code, sat_unit_code):
        """SKU must be unique."""
        from apps.inventory.models import InventoryItem
        with pytest.raises(IntegrityError):
            InventoryItem.objects.create(
                sku='PF-001',  # Duplicate
                name='Duplicate Item',
                item_type='resale',
                sat_product_code=sat_product_code,
                sat_unit_code=sat_unit_code,
                tax_rate=iva_16,
                cost_price=Decimal('100.00'),
            )

    def test_inventoryitem_sat_compliance(self, resale_item, sat_product_code, sat_unit_code):
        """Item has SAT compliance fields."""
        assert resale_item.sat_product_code == sat_product_code
        assert resale_item.sat_unit_code == sat_unit_code
        assert resale_item.sat_product_code.code == '50112001'
        assert resale_item.sat_unit_code.code == 'H87'

    def test_inventoryitem_tax_rate(self, resale_item, iva_16):
        """Item has tax rate."""
        assert resale_item.tax_rate == iva_16
        assert resale_item.tax_rate.rate == Decimal('0.1600')

    def test_inventoryitem_defaults(self, db, iva_16, sat_product_code, sat_unit_code):
        """Default values are set correctly."""
        from apps.inventory.models import InventoryItem
        item = InventoryItem.objects.create(
            sku='TEST',
            name='Test Item',
            item_type='resale',
            sat_product_code=sat_product_code,
            sat_unit_code=sat_unit_code,
            tax_rate=iva_16,
        )
        assert item.track_inventory is True
        assert item.reorder_point == 0
        assert item.reorder_quantity == 0
        assert item.is_depreciable is False
        assert item.is_active is True

    def test_inventoryitem_ordering(self, db, iva_16, sat_product_code, sat_unit_code):
        """Items are ordered by name."""
        from apps.inventory.models import InventoryItem
        InventoryItem.objects.create(sku='Z', name='Zebra', item_type='supply', sat_product_code=sat_product_code, sat_unit_code=sat_unit_code, tax_rate=iva_16)
        InventoryItem.objects.create(sku='A', name='Apple', item_type='supply', sat_product_code=sat_product_code, sat_unit_code=sat_unit_code, tax_rate=iva_16)
        InventoryItem.objects.create(sku='M', name='Mango', item_type='supply', sat_product_code=sat_product_code, sat_unit_code=sat_unit_code, tax_rate=iva_16)

        items = list(InventoryItem.objects.all())
        names = [i.name for i in items]
        assert names == sorted(names)


class TestInventoryItemTypes:
    """Tests for item type specific behavior."""

    def test_resale_item_has_sale_price(self, resale_item):
        """Resale items have sale price."""
        assert resale_item.sale_price is not None

    def test_supply_item_no_sale_price(self, supply_item):
        """Supply items typically don't have sale price."""
        assert supply_item.sale_price is None

    def test_equipment_depreciable(self, equipment_item):
        """Equipment can be depreciable."""
        assert equipment_item.is_depreciable is True
        assert equipment_item.useful_life_months > 0

    def test_item_type_choices(self, db):
        """All item type choices are valid."""
        from apps.inventory.models import InventoryItem
        valid_types = ['resale', 'supply', 'consumable', 'equipment', 'raw_material']
        for item_type in valid_types:
            assert item_type in dict(InventoryItem.ITEM_TYPE_CHOICES)


class TestInventoryItemRelationships:
    """Tests for InventoryItem relationships."""

    def test_sat_product_code_protected(self, db, resale_item, sat_product_code):
        """Cannot delete SAT product code if in use."""
        with pytest.raises(Exception):  # ProtectedError
            sat_product_code.delete()

    def test_sat_unit_code_protected(self, db, resale_item, sat_unit_code):
        """Cannot delete SAT unit code if in use."""
        with pytest.raises(Exception):  # ProtectedError
            sat_unit_code.delete()

    def test_tax_rate_protected(self, db, resale_item, iva_16):
        """Cannot delete tax rate if in use."""
        with pytest.raises(Exception):  # ProtectedError
            iva_16.delete()


class TestInventoryItemFiltering:
    """Tests for filtering inventory items."""

    def test_filter_by_item_type(self, db, resale_item, supply_item, consumable_item):
        """Can filter items by type."""
        from apps.inventory.models import InventoryItem

        resale_items = InventoryItem.objects.filter(item_type='resale')
        supply_items = InventoryItem.objects.filter(item_type='supply')
        consumable_items = InventoryItem.objects.filter(item_type='consumable')

        assert resale_items.count() == 1
        assert supply_items.count() == 1
        assert consumable_items.count() == 1

    def test_filter_active(self, db, resale_item):
        """Can filter active items."""
        from apps.inventory.models import InventoryItem

        resale_item.is_active = False
        resale_item.save()

        active_items = InventoryItem.objects.filter(is_active=True)
        inactive_items = InventoryItem.objects.filter(is_active=False)

        assert inactive_items.count() == 1
        assert resale_item not in active_items

    def test_filter_track_inventory(self, db, resale_item, supply_item):
        """Can filter items that track inventory."""
        from apps.inventory.models import InventoryItem

        supply_item.track_inventory = False
        supply_item.save()

        tracked = InventoryItem.objects.filter(track_inventory=True)
        untracked = InventoryItem.objects.filter(track_inventory=False)

        assert tracked.count() == 1
        assert untracked.count() == 1
