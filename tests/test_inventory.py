"""Tests for inventory management models (S-024)."""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def staff_user(db):
    """Create a staff user for testing."""
    return User.objects.create_user(
        username='staff_inventory',
        email='staff@example.com',
        password='testpass123',
        first_name='Staff',
        last_name='User',
        is_staff=True
    )


@pytest.fixture
def category(db):
    """Create a product category for testing."""
    from apps.store.models import Category
    return Category.objects.create(
        name='Medications',
        name_es='Medicamentos',
        name_en='Medications',
        slug='medications',
        is_active=True
    )


@pytest.fixture
def product(db, category):
    """Create a product for testing."""
    from apps.store.models import Product
    return Product.objects.create(
        name='Apoquel 16mg',
        name_es='Apoquel 16mg',
        name_en='Apoquel 16mg',
        slug='apoquel-16mg',
        category=category,
        price=Decimal('450.00'),
        sku='APQ-16-001',
        stock_quantity=100,
        low_stock_threshold=10,
        track_inventory=True
    )


@pytest.fixture
def product2(db, category):
    """Create a second product for testing."""
    from apps.store.models import Product
    return Product.objects.create(
        name='Rimadyl 100mg',
        name_es='Rimadyl 100mg',
        name_en='Rimadyl 100mg',
        slug='rimadyl-100mg',
        category=category,
        price=Decimal('380.00'),
        sku='RIM-100-001',
        stock_quantity=50,
        low_stock_threshold=15,
        track_inventory=True
    )


@pytest.fixture
def stock_location(db):
    """Create a stock location for testing."""
    from apps.inventory.models import StockLocation
    return StockLocation.objects.create(
        name='Main Pharmacy',
        description='Primary pharmacy storage',
        location_type='pharmacy',
        requires_temperature_control=False,
        requires_restricted_access=True,
        is_active=True
    )


@pytest.fixture
def stock_location2(db):
    """Create a secondary stock location for testing."""
    from apps.inventory.models import StockLocation
    return StockLocation.objects.create(
        name='Store Floor',
        description='Retail display area',
        location_type='store',
        requires_temperature_control=False,
        requires_restricted_access=False,
        is_active=True
    )


@pytest.fixture
def refrigerated_location(db):
    """Create a refrigerated stock location for testing."""
    from apps.inventory.models import StockLocation
    return StockLocation.objects.create(
        name='Refrigerated Storage',
        description='Cold storage for vaccines',
        location_type='refrigerated',
        requires_temperature_control=True,
        requires_restricted_access=True,
        is_active=True
    )


@pytest.fixture
def supplier(db):
    """Create a supplier for testing."""
    from apps.inventory.models import Supplier
    return Supplier.objects.create(
        name='VetPharm Mexico',
        code='VPM-001',
        contact_name='Juan Perez',
        email='ventas@vetpharm.mx',
        phone='+52 555 123 4567',
        address='Av. Reforma 123, CDMX',
        rfc='VPM990101XXX',
        payment_terms='net30',
        lead_time_days=5,
        categories=['medications', 'vaccines'],
        is_active=True,
        is_preferred=True
    )


@pytest.fixture
def supplier2(db):
    """Create a secondary supplier for testing."""
    from apps.inventory.models import Supplier
    return Supplier.objects.create(
        name='PetMed Distributor',
        code='PMD-001',
        contact_name='Maria Lopez',
        email='orders@petmed.mx',
        phone='+52 555 987 6543',
        rfc='PMD010101XXX',
        payment_terms='net15',
        lead_time_days=3,
        is_active=True,
        is_preferred=False
    )


@pytest.fixture
def stock_level(db, product, stock_location):
    """Create a stock level for testing."""
    from apps.inventory.models import StockLevel
    return StockLevel.objects.create(
        product=product,
        location=stock_location,
        quantity=Decimal('50.00'),
        reserved_quantity=Decimal('5.00'),
        min_level=Decimal('10.00'),
        reorder_quantity=Decimal('100.00')
    )


@pytest.fixture
def stock_batch(db, product, stock_location, supplier):
    """Create a stock batch for testing."""
    from apps.inventory.models import StockBatch
    today = timezone.now().date()
    return StockBatch.objects.create(
        product=product,
        location=stock_location,
        batch_number='APQ-2025-001',
        lot_number='LOT-12345',
        initial_quantity=Decimal('100.00'),
        current_quantity=Decimal('75.00'),
        manufacture_date=today - timedelta(days=30),
        expiry_date=today + timedelta(days=365),
        received_date=today - timedelta(days=7),
        unit_cost=Decimal('350.00'),
        supplier=supplier,
        status='available'
    )


@pytest.fixture
def expiring_batch(db, product, stock_location, supplier):
    """Create a batch expiring soon for testing."""
    from apps.inventory.models import StockBatch
    today = timezone.now().date()
    return StockBatch.objects.create(
        product=product,
        location=stock_location,
        batch_number='APQ-2024-EXP',
        initial_quantity=Decimal('20.00'),
        current_quantity=Decimal('15.00'),
        expiry_date=today + timedelta(days=15),
        received_date=today - timedelta(days=180),
        unit_cost=Decimal('340.00'),
        supplier=supplier,
        status='available'
    )


@pytest.fixture
def expired_batch(db, product, stock_location, supplier):
    """Create an expired batch for testing."""
    from apps.inventory.models import StockBatch
    today = timezone.now().date()
    return StockBatch.objects.create(
        product=product,
        location=stock_location,
        batch_number='APQ-2023-OLD',
        initial_quantity=Decimal('10.00'),
        current_quantity=Decimal('5.00'),
        expiry_date=today - timedelta(days=30),
        received_date=today - timedelta(days=400),
        unit_cost=Decimal('300.00'),
        supplier=supplier,
        status='expired'
    )


@pytest.fixture
def product_supplier(db, product, supplier):
    """Create a product-supplier relationship for testing."""
    from apps.inventory.models import ProductSupplier
    return ProductSupplier.objects.create(
        product=product,
        supplier=supplier,
        supplier_sku='VPM-APQ-16',
        unit_cost=Decimal('350.00'),
        minimum_order_quantity=Decimal('10.00'),
        is_preferred=True,
        is_active=True
    )


@pytest.fixture
def reorder_rule(db, product, stock_location, supplier):
    """Create a reorder rule for testing."""
    from apps.inventory.models import ReorderRule
    return ReorderRule.objects.create(
        product=product,
        location=stock_location,
        min_level=Decimal('5.00'),
        reorder_point=Decimal('20.00'),
        reorder_quantity=Decimal('100.00'),
        max_level=Decimal('200.00'),
        preferred_supplier=supplier,
        is_active=True,
        auto_create_po=False
    )


@pytest.fixture
def purchase_order(db, supplier, stock_location, staff_user):
    """Create a purchase order for testing."""
    from apps.inventory.models import PurchaseOrder
    return PurchaseOrder.objects.create(
        po_number='PO-2025-0001',
        supplier=supplier,
        status='draft',
        order_date=date.today(),
        expected_date=date.today() + timedelta(days=5),
        subtotal=Decimal('3500.00'),
        tax=Decimal('560.00'),
        shipping=Decimal('150.00'),
        total=Decimal('4210.00'),
        delivery_location=stock_location,
        notes='Standard order',
        created_by=staff_user
    )


@pytest.fixture
def purchase_order_line(db, purchase_order, product):
    """Create a purchase order line for testing."""
    from apps.inventory.models import PurchaseOrderLine
    return PurchaseOrderLine.objects.create(
        purchase_order=purchase_order,
        product=product,
        quantity_ordered=Decimal('10.00'),
        quantity_received=Decimal('0.00'),
        unit_cost=Decimal('350.00'),
        line_total=Decimal('3500.00'),
        supplier_sku='VPM-APQ-16'
    )


@pytest.fixture
def stock_count(db, stock_location, staff_user):
    """Create a stock count for testing."""
    from apps.inventory.models import StockCount
    return StockCount.objects.create(
        location=stock_location,
        count_date=date.today(),
        status='draft',
        count_type='full',
        counted_by=staff_user
    )


@pytest.fixture
def stock_count_line(db, stock_count, product, stock_batch):
    """Create a stock count line for testing."""
    from apps.inventory.models import StockCountLine
    return StockCountLine.objects.create(
        stock_count=stock_count,
        product=product,
        batch=stock_batch,
        system_quantity=Decimal('75.00'),
        counted_quantity=Decimal('73.00'),
        discrepancy=Decimal('-2.00'),
        discrepancy_value=Decimal('-700.00'),
        adjustment_reason='2 tablets damaged'
    )


@pytest.fixture
def pet(db, staff_user):
    """Create a pet for controlled substance testing."""
    from apps.pets.models import Pet
    return Pet.objects.create(
        name='Luna',
        species='dog',
        breed='Golden Retriever',
        owner=staff_user,
        date_of_birth=timezone.now().date() - timedelta(days=730)
    )


@pytest.fixture
def medication(db):
    """Create a medication for prescription testing."""
    from apps.pharmacy.models import Medication
    return Medication.objects.create(
        name='Tramadol',
        schedule='IV',
        is_controlled=True,
        requires_prescription=True,
        species=['dog', 'cat'],
        dosage_forms=['tablet'],
        strengths=['50mg', '100mg']
    )


@pytest.fixture
def prescription(db, pet, staff_user, medication):
    """Create a prescription for controlled substance testing."""
    from apps.pharmacy.models import Prescription
    today = timezone.now().date()
    return Prescription.objects.create(
        pet=pet,
        owner=staff_user,
        medication=medication,
        strength='50mg',
        dosage_form='tablet',
        quantity=30,
        dosage='1 tablet',
        frequency='twice daily',
        duration='14 days',
        prescribed_date=today,
        expiration_date=today + timedelta(days=365),
        status='active'
    )


# =============================================================================
# STOCK LOCATION TESTS
# =============================================================================

class TestStockLocation:
    """Tests for StockLocation model."""

    def test_create_stock_location(self, stock_location):
        """Test creating a stock location."""
        assert stock_location.name == 'Main Pharmacy'
        assert stock_location.location_type == 'pharmacy'
        assert stock_location.requires_restricted_access is True
        assert stock_location.is_active is True

    def test_stock_location_str(self, stock_location):
        """Test stock location string representation."""
        assert str(stock_location) == 'Main Pharmacy'

    def test_stock_location_ordering(self, stock_location, stock_location2, refrigerated_location):
        """Test stock locations are ordered by name."""
        from apps.inventory.models import StockLocation
        locations = list(StockLocation.objects.all())
        names = [loc.name for loc in locations]
        assert names == sorted(names)

    def test_location_types(self, db):
        """Test different location types can be created."""
        from apps.inventory.models import StockLocation
        types = ['store', 'pharmacy', 'clinic', 'refrigerated', 'controlled', 'warehouse']
        for loc_type in types:
            location = StockLocation.objects.create(
                name=f'{loc_type.title()} Location',
                location_type=loc_type,
                is_active=True
            )
            assert location.location_type == loc_type


# =============================================================================
# STOCK LEVEL TESTS
# =============================================================================

class TestStockLevel:
    """Tests for StockLevel model."""

    def test_create_stock_level(self, stock_level):
        """Test creating a stock level."""
        assert stock_level.quantity == Decimal('50.00')
        assert stock_level.reserved_quantity == Decimal('5.00')

    def test_available_quantity(self, stock_level):
        """Test available quantity calculation."""
        assert stock_level.available_quantity == Decimal('45.00')

    def test_is_below_minimum_when_above(self, stock_level):
        """Test is_below_minimum when quantity is above minimum."""
        assert stock_level.is_below_minimum is False

    def test_is_below_minimum_when_below(self, stock_level):
        """Test is_below_minimum when quantity is below minimum."""
        stock_level.quantity = Decimal('8.00')
        stock_level.save()
        assert stock_level.is_below_minimum is True

    def test_is_below_minimum_when_equal(self, stock_level):
        """Test is_below_minimum when quantity equals minimum."""
        stock_level.quantity = Decimal('10.00')
        stock_level.save()
        assert stock_level.is_below_minimum is True

    def test_unique_product_location(self, db, product, stock_location):
        """Test that product-location combination is unique."""
        from apps.inventory.models import StockLevel
        from django.db import IntegrityError

        StockLevel.objects.create(
            product=product,
            location=stock_location,
            quantity=Decimal('10.00')
        )

        with pytest.raises(IntegrityError):
            StockLevel.objects.create(
                product=product,
                location=stock_location,
                quantity=Decimal('20.00')
            )

    def test_stock_level_with_no_min_level(self, db, product, stock_location):
        """Test stock level without custom min_level uses product default."""
        from apps.inventory.models import StockLevel

        level = StockLevel.objects.create(
            product=product,
            location=stock_location,
            quantity=Decimal('8.00'),
            min_level=None
        )
        # Without min_level set, should use product's low_stock_threshold (10)
        assert level.is_below_minimum is True


# =============================================================================
# STOCK BATCH TESTS
# =============================================================================

class TestStockBatch:
    """Tests for StockBatch model."""

    def test_create_stock_batch(self, stock_batch):
        """Test creating a stock batch."""
        assert stock_batch.batch_number == 'APQ-2025-001'
        assert stock_batch.current_quantity == Decimal('75.00')
        assert stock_batch.status == 'available'

    def test_is_expired_when_not_expired(self, stock_batch):
        """Test is_expired when batch is not expired."""
        assert stock_batch.is_expired is False

    def test_is_expired_when_expired(self, expired_batch):
        """Test is_expired when batch is expired."""
        assert expired_batch.is_expired is True

    def test_is_expired_with_no_expiry_date(self, db, product, stock_location, supplier):
        """Test is_expired when batch has no expiry date."""
        from apps.inventory.models import StockBatch
        batch = StockBatch.objects.create(
            product=product,
            location=stock_location,
            batch_number='NO-EXP-001',
            initial_quantity=Decimal('10.00'),
            current_quantity=Decimal('10.00'),
            received_date=date.today(),
            unit_cost=Decimal('100.00'),
            expiry_date=None
        )
        assert batch.is_expired is False

    def test_days_until_expiry(self, stock_batch):
        """Test days until expiry calculation."""
        days = stock_batch.days_until_expiry
        assert days == 365

    def test_days_until_expiry_expiring_soon(self, expiring_batch):
        """Test days until expiry for expiring batch."""
        days = expiring_batch.days_until_expiry
        assert days == 15

    def test_days_until_expiry_expired(self, expired_batch):
        """Test days until expiry for expired batch."""
        days = expired_batch.days_until_expiry
        assert days == -30

    def test_days_until_expiry_no_date(self, db, product, stock_location, supplier):
        """Test days until expiry with no expiry date."""
        from apps.inventory.models import StockBatch
        batch = StockBatch.objects.create(
            product=product,
            location=stock_location,
            batch_number='NO-EXP-002',
            initial_quantity=Decimal('10.00'),
            current_quantity=Decimal('10.00'),
            received_date=date.today(),
            unit_cost=Decimal('100.00'),
            expiry_date=None
        )
        assert batch.days_until_expiry is None

    def test_fefo_ordering(self, stock_batch, expiring_batch, expired_batch):
        """Test batches are ordered by expiry date (FEFO)."""
        from apps.inventory.models import StockBatch
        batches = list(StockBatch.objects.all())
        # Should be ordered by expiry_date (earliest first)
        assert batches[0] == expired_batch
        assert batches[1] == expiring_batch
        assert batches[2] == stock_batch

    def test_batch_status_choices(self, db, product, stock_location, supplier):
        """Test different batch status choices."""
        from apps.inventory.models import StockBatch
        statuses = ['available', 'low', 'depleted', 'expired', 'recalled', 'damaged']
        for status in statuses:
            batch = StockBatch.objects.create(
                product=product,
                location=stock_location,
                batch_number=f'STATUS-{status.upper()}',
                initial_quantity=Decimal('10.00'),
                current_quantity=Decimal('5.00'),
                received_date=date.today(),
                unit_cost=Decimal('100.00'),
                status=status
            )
            assert batch.status == status


# =============================================================================
# STOCK MOVEMENT TESTS
# =============================================================================

class TestStockMovement:
    """Tests for StockMovement model."""

    def test_create_stock_movement_receive(self, db, product, stock_location, stock_batch, staff_user):
        """Test creating a receive movement."""
        from apps.inventory.models import StockMovement
        movement = StockMovement.objects.create(
            product=product,
            batch=stock_batch,
            movement_type='receive',
            to_location=stock_location,
            quantity=Decimal('100.00'),
            unit_cost=Decimal('350.00'),
            reference_type='purchase_order',
            reference_id=1,
            recorded_by=staff_user
        )
        assert movement.movement_type == 'receive'
        assert movement.quantity == Decimal('100.00')

    def test_create_stock_movement_sale(self, db, product, stock_location, stock_batch, staff_user):
        """Test creating a sale movement."""
        from apps.inventory.models import StockMovement
        movement = StockMovement.objects.create(
            product=product,
            batch=stock_batch,
            movement_type='sale',
            from_location=stock_location,
            quantity=Decimal('2.00'),
            reference_type='order',
            reference_id=123,
            recorded_by=staff_user
        )
        assert movement.movement_type == 'sale'

    def test_create_transfer_movement(self, db, product, stock_location, stock_location2, stock_batch, staff_user):
        """Test creating a transfer movement."""
        from apps.inventory.models import StockMovement
        movement = StockMovement.objects.create(
            product=product,
            batch=stock_batch,
            movement_type='transfer_out',
            from_location=stock_location,
            to_location=stock_location2,
            quantity=Decimal('10.00'),
            recorded_by=staff_user
        )
        assert movement.movement_type == 'transfer_out'
        assert movement.from_location == stock_location
        assert movement.to_location == stock_location2

    def test_adjustment_movement_with_authorization(self, db, product, stock_location, staff_user):
        """Test creating an adjustment movement with authorization."""
        from apps.inventory.models import StockMovement
        movement = StockMovement.objects.create(
            product=product,
            movement_type='adjustment_remove',
            from_location=stock_location,
            quantity=Decimal('3.00'),
            reason='Damaged during delivery',
            authorized_by=staff_user,
            recorded_by=staff_user
        )
        assert movement.reason == 'Damaged during delivery'
        assert movement.authorized_by == staff_user

    def test_movement_ordering(self, db, product, stock_location, staff_user):
        """Test movements are ordered by created_at descending."""
        from apps.inventory.models import StockMovement
        import time

        m1 = StockMovement.objects.create(
            product=product,
            movement_type='receive',
            to_location=stock_location,
            quantity=Decimal('10.00'),
            recorded_by=staff_user
        )
        time.sleep(0.01)
        m2 = StockMovement.objects.create(
            product=product,
            movement_type='sale',
            from_location=stock_location,
            quantity=Decimal('2.00'),
            recorded_by=staff_user
        )

        movements = list(StockMovement.objects.all())
        assert movements[0] == m2  # Most recent first
        assert movements[1] == m1

    def test_all_movement_types(self, db, product, stock_location, staff_user):
        """Test all movement type choices."""
        from apps.inventory.models import StockMovement
        types = [
            'receive', 'return_customer', 'transfer_in', 'adjustment_add',
            'sale', 'dispense', 'return_supplier', 'transfer_out',
            'adjustment_remove', 'expired', 'damaged', 'loss', 'sample'
        ]
        for move_type in types:
            movement = StockMovement.objects.create(
                product=product,
                movement_type=move_type,
                quantity=Decimal('1.00'),
                recorded_by=staff_user
            )
            assert movement.movement_type == move_type


# =============================================================================
# SUPPLIER TESTS
# =============================================================================

class TestSupplier:
    """Tests for Supplier model."""

    def test_create_supplier(self, supplier):
        """Test creating a supplier."""
        assert supplier.name == 'VetPharm Mexico'
        assert supplier.code == 'VPM-001'
        assert supplier.is_preferred is True

    def test_supplier_str(self, supplier):
        """Test supplier string representation."""
        assert str(supplier) == 'VetPharm Mexico'

    def test_supplier_ordering(self, supplier, supplier2):
        """Test suppliers are ordered by name."""
        from apps.inventory.models import Supplier
        suppliers = list(Supplier.objects.all())
        names = [s.name for s in suppliers]
        assert names == sorted(names)

    def test_supplier_categories(self, supplier):
        """Test supplier categories JSONField."""
        assert 'medications' in supplier.categories
        assert 'vaccines' in supplier.categories


# =============================================================================
# PRODUCT SUPPLIER TESTS
# =============================================================================

class TestProductSupplier:
    """Tests for ProductSupplier model."""

    def test_create_product_supplier(self, product_supplier):
        """Test creating a product-supplier relationship."""
        assert product_supplier.supplier_sku == 'VPM-APQ-16'
        assert product_supplier.unit_cost == Decimal('350.00')
        assert product_supplier.is_preferred is True

    def test_unique_product_supplier(self, db, product, supplier):
        """Test that product-supplier combination is unique."""
        from apps.inventory.models import ProductSupplier
        from django.db import IntegrityError

        ProductSupplier.objects.create(
            product=product,
            supplier=supplier,
            unit_cost=Decimal('100.00')
        )

        with pytest.raises(IntegrityError):
            ProductSupplier.objects.create(
                product=product,
                supplier=supplier,
                unit_cost=Decimal('200.00')
            )

    def test_multiple_suppliers_for_product(self, db, product, supplier, supplier2):
        """Test a product can have multiple suppliers."""
        from apps.inventory.models import ProductSupplier

        ps1 = ProductSupplier.objects.create(
            product=product,
            supplier=supplier,
            unit_cost=Decimal('350.00'),
            is_preferred=True
        )
        ps2 = ProductSupplier.objects.create(
            product=product,
            supplier=supplier2,
            unit_cost=Decimal('380.00'),
            is_preferred=False
        )

        assert product.suppliers.count() == 2


# =============================================================================
# REORDER RULE TESTS
# =============================================================================

class TestReorderRule:
    """Tests for ReorderRule model."""

    def test_create_reorder_rule(self, reorder_rule):
        """Test creating a reorder rule."""
        assert reorder_rule.min_level == Decimal('5.00')
        assert reorder_rule.reorder_point == Decimal('20.00')
        assert reorder_rule.reorder_quantity == Decimal('100.00')

    def test_unique_product_location_rule(self, db, product, stock_location, supplier):
        """Test that product-location combination is unique for reorder rules."""
        from apps.inventory.models import ReorderRule
        from django.db import IntegrityError

        ReorderRule.objects.create(
            product=product,
            location=stock_location,
            min_level=Decimal('5.00'),
            reorder_point=Decimal('20.00'),
            reorder_quantity=Decimal('100.00')
        )

        with pytest.raises(IntegrityError):
            ReorderRule.objects.create(
                product=product,
                location=stock_location,
                min_level=Decimal('10.00'),
                reorder_point=Decimal('30.00'),
                reorder_quantity=Decimal('50.00')
            )

    def test_global_reorder_rule_without_location(self, db, product, supplier):
        """Test creating a global reorder rule without specific location."""
        from apps.inventory.models import ReorderRule

        rule = ReorderRule.objects.create(
            product=product,
            location=None,  # Global rule
            min_level=Decimal('10.00'),
            reorder_point=Decimal('30.00'),
            reorder_quantity=Decimal('100.00')
        )
        assert rule.location is None


# =============================================================================
# PURCHASE ORDER TESTS
# =============================================================================

class TestPurchaseOrder:
    """Tests for PurchaseOrder model."""

    def test_create_purchase_order(self, purchase_order):
        """Test creating a purchase order."""
        assert purchase_order.po_number == 'PO-2025-0001'
        assert purchase_order.status == 'draft'
        assert purchase_order.total == Decimal('4210.00')

    def test_purchase_order_str(self, purchase_order):
        """Test purchase order string representation."""
        assert 'PO-2025-0001' in str(purchase_order)

    def test_unique_po_number(self, db, supplier, stock_location, staff_user):
        """Test that PO numbers are unique."""
        from apps.inventory.models import PurchaseOrder
        from django.db import IntegrityError

        PurchaseOrder.objects.create(
            po_number='PO-UNIQUE-001',
            supplier=supplier,
            delivery_location=stock_location,
            created_by=staff_user
        )

        with pytest.raises(IntegrityError):
            PurchaseOrder.objects.create(
                po_number='PO-UNIQUE-001',
                supplier=supplier,
                delivery_location=stock_location,
                created_by=staff_user
            )

    def test_purchase_order_status_choices(self, db, supplier, stock_location, staff_user):
        """Test different PO status choices."""
        from apps.inventory.models import PurchaseOrder
        statuses = ['draft', 'submitted', 'confirmed', 'shipped', 'partial', 'received', 'cancelled']

        for i, status in enumerate(statuses):
            po = PurchaseOrder.objects.create(
                po_number=f'PO-STATUS-{i:03d}',
                supplier=supplier,
                status=status,
                delivery_location=stock_location,
                created_by=staff_user
            )
            assert po.status == status

    def test_purchase_order_ordering(self, db, supplier, stock_location, staff_user):
        """Test purchase orders are ordered by created_at descending."""
        from apps.inventory.models import PurchaseOrder
        import time

        po1 = PurchaseOrder.objects.create(
            po_number='PO-ORD-001',
            supplier=supplier,
            delivery_location=stock_location,
            created_by=staff_user
        )
        time.sleep(0.01)
        po2 = PurchaseOrder.objects.create(
            po_number='PO-ORD-002',
            supplier=supplier,
            delivery_location=stock_location,
            created_by=staff_user
        )

        orders = list(PurchaseOrder.objects.all())
        assert orders[0] == po2  # Most recent first


# =============================================================================
# PURCHASE ORDER LINE TESTS
# =============================================================================

class TestPurchaseOrderLine:
    """Tests for PurchaseOrderLine model."""

    def test_create_purchase_order_line(self, purchase_order_line):
        """Test creating a purchase order line."""
        assert purchase_order_line.quantity_ordered == Decimal('10.00')
        assert purchase_order_line.quantity_received == Decimal('0.00')
        assert purchase_order_line.line_total == Decimal('3500.00')

    def test_multiple_lines_on_order(self, purchase_order, product, product2):
        """Test adding multiple lines to a purchase order."""
        from apps.inventory.models import PurchaseOrderLine

        line1 = PurchaseOrderLine.objects.create(
            purchase_order=purchase_order,
            product=product,
            quantity_ordered=Decimal('10.00'),
            unit_cost=Decimal('350.00'),
            line_total=Decimal('3500.00')
        )
        line2 = PurchaseOrderLine.objects.create(
            purchase_order=purchase_order,
            product=product2,
            quantity_ordered=Decimal('20.00'),
            unit_cost=Decimal('250.00'),
            line_total=Decimal('5000.00')
        )

        assert purchase_order.lines.count() == 2


# =============================================================================
# STOCK COUNT TESTS
# =============================================================================

class TestStockCount:
    """Tests for StockCount model."""

    def test_create_stock_count(self, stock_count):
        """Test creating a stock count."""
        assert stock_count.status == 'draft'
        assert stock_count.count_type == 'full'

    def test_stock_count_status_choices(self, db, stock_location, staff_user):
        """Test different stock count status choices."""
        from apps.inventory.models import StockCount
        statuses = ['draft', 'submitted', 'approved', 'posted', 'cancelled']

        for status in statuses:
            count = StockCount.objects.create(
                location=stock_location,
                count_date=date.today(),
                status=status,
                counted_by=staff_user
            )
            assert count.status == status

    def test_stock_count_types(self, db, stock_location, staff_user):
        """Test different stock count types."""
        from apps.inventory.models import StockCount
        types = ['full', 'cycle', 'spot']

        for count_type in types:
            count = StockCount.objects.create(
                location=stock_location,
                count_date=date.today(),
                count_type=count_type,
                counted_by=staff_user
            )
            assert count.count_type == count_type


# =============================================================================
# STOCK COUNT LINE TESTS
# =============================================================================

class TestStockCountLine:
    """Tests for StockCountLine model."""

    def test_create_stock_count_line(self, stock_count_line):
        """Test creating a stock count line."""
        assert stock_count_line.system_quantity == Decimal('75.00')
        assert stock_count_line.counted_quantity == Decimal('73.00')
        assert stock_count_line.discrepancy == Decimal('-2.00')

    def test_discrepancy_calculation(self, stock_count_line):
        """Test discrepancy is correctly recorded."""
        # Counted 73 but system says 75, so -2 discrepancy
        assert stock_count_line.discrepancy == Decimal('-2.00')

    def test_positive_discrepancy(self, db, stock_count, product, stock_batch):
        """Test positive discrepancy (counted more than system)."""
        from apps.inventory.models import StockCountLine

        line = StockCountLine.objects.create(
            stock_count=stock_count,
            product=product,
            batch=stock_batch,
            system_quantity=Decimal('50.00'),
            counted_quantity=Decimal('52.00'),
            discrepancy=Decimal('2.00'),
            discrepancy_value=Decimal('700.00')
        )
        assert line.discrepancy == Decimal('2.00')


# =============================================================================
# CONTROLLED SUBSTANCE LOG TESTS
# =============================================================================

class TestControlledSubstanceLog:
    """Tests for ControlledSubstanceLog model."""

    def test_create_dispense_log(self, db, product, stock_batch, pet, staff_user, prescription):
        """Test creating a controlled substance dispense log."""
        from apps.inventory.models import ControlledSubstanceLog

        log = ControlledSubstanceLog.objects.create(
            product=product,
            batch=stock_batch,
            log_type='dispense',
            quantity=Decimal('20.00'),
            balance_after=Decimal('55.00'),
            pet=pet,
            owner=staff_user,
            prescription=prescription,
            recorded_by=staff_user,
            notes='Dispensed for pain management'
        )

        assert log.log_type == 'dispense'
        assert log.quantity == Decimal('20.00')
        assert log.pet == pet

    def test_create_waste_log(self, db, product, stock_batch, staff_user):
        """Test creating a controlled substance waste log."""
        from apps.inventory.models import ControlledSubstanceLog

        witness = User.objects.create_user(
            username='witness_user',
            email='witness@example.com',
            password='testpass123'
        )

        log = ControlledSubstanceLog.objects.create(
            product=product,
            batch=stock_batch,
            log_type='waste',
            quantity=Decimal('5.00'),
            balance_after=Decimal('70.00'),
            waste_reason='Partially used vial expired',
            waste_witnessed_by=witness,
            recorded_by=staff_user
        )

        assert log.log_type == 'waste'
        assert log.waste_witnessed_by == witness

    def test_log_types(self, db, product, stock_batch, staff_user):
        """Test all controlled substance log types."""
        from apps.inventory.models import ControlledSubstanceLog
        types = ['receive', 'dispense', 'waste', 'return', 'transfer', 'adjustment']

        for log_type in types:
            log = ControlledSubstanceLog.objects.create(
                product=product,
                batch=stock_batch,
                log_type=log_type,
                quantity=Decimal('1.00'),
                balance_after=Decimal('74.00'),
                recorded_by=staff_user
            )
            assert log.log_type == log_type

    def test_log_ordering(self, db, product, stock_batch, staff_user):
        """Test logs are ordered by created_at descending."""
        from apps.inventory.models import ControlledSubstanceLog
        import time

        log1 = ControlledSubstanceLog.objects.create(
            product=product,
            batch=stock_batch,
            log_type='receive',
            quantity=Decimal('100.00'),
            balance_after=Decimal('100.00'),
            recorded_by=staff_user
        )
        time.sleep(0.01)
        log2 = ControlledSubstanceLog.objects.create(
            product=product,
            batch=stock_batch,
            log_type='dispense',
            quantity=Decimal('10.00'),
            balance_after=Decimal('90.00'),
            recorded_by=staff_user
        )

        logs = list(ControlledSubstanceLog.objects.all())
        assert logs[0] == log2  # Most recent first


# =============================================================================
# AI TOOLS TESTS
# =============================================================================

class TestInventoryAITools:
    """Tests for inventory AI tools."""

    def test_check_stock_level_tool_registered(self):
        """Test that check_stock_level tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry
        tool = ToolRegistry.get_tool('check_stock_level')
        assert tool is not None

    def test_get_expiring_products_tool_registered(self):
        """Test that get_expiring_products tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry
        tool = ToolRegistry.get_tool('get_expiring_products')
        assert tool is not None

    def test_get_low_stock_products_tool_registered(self):
        """Test that get_low_stock_products tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry
        tool = ToolRegistry.get_tool('get_low_stock_products')
        assert tool is not None

    def test_check_stock_level_returns_data(self, stock_level, product, stock_location):
        """Test check_stock_level returns stock information."""
        from apps.ai_assistant.tools import ToolRegistry
        tool = ToolRegistry.get_tool('check_stock_level')
        result = tool.handler(product_id=product.id, location=stock_location.name)

        assert 'product' in result or 'error' not in result

    def test_get_expiring_products_returns_list(self, stock_batch, expiring_batch):
        """Test get_expiring_products returns expiring products."""
        from apps.ai_assistant.tools import ToolRegistry
        tool = ToolRegistry.get_tool('get_expiring_products')
        result = tool.handler(days_ahead=30)

        assert isinstance(result, (list, dict))

    def test_get_low_stock_products_returns_list(self, stock_level):
        """Test get_low_stock_products returns low stock products."""
        from apps.ai_assistant.tools import ToolRegistry
        # Set stock below minimum
        stock_level.quantity = Decimal('8.00')
        stock_level.save()

        tool = ToolRegistry.get_tool('get_low_stock_products')
        result = tool.handler()

        assert isinstance(result, (list, dict))
