"""Tests for inventory forms and services (TDD - Phase 1).

Tests written FIRST before implementation per 23-step TDD cycle.
"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model

from apps.inventory.models import (
    StockLocation, StockLevel, StockBatch, StockMovement,
    Supplier, PurchaseOrder, PurchaseOrderLine, StockCount, StockCountLine,
    LocationType
)
from apps.store.models import Product, Category


User = get_user_model()


@pytest.fixture
def staff_user(db):
    """Create a staff user for tests."""
    return User.objects.create_user(
        username='inventory_staff',
        email='invstaff@test.com',
        password='testpass123',
        is_staff=True,
    )


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
    """Create a second stock location for transfers."""
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
# FORM TESTS - StockMovementForm
# =============================================================================

@pytest.mark.django_db
class TestStockMovementForm:
    """Tests for StockMovementForm."""

    def test_form_exists(self):
        """Test that StockMovementForm exists."""
        from apps.inventory.forms import StockMovementForm
        assert StockMovementForm is not None

    def test_form_valid_receive_movement(self, product, location):
        """Test form validates receive movement correctly."""
        from apps.inventory.forms import StockMovementForm
        data = {
            'movement_type': 'receive',
            'product': product.id,
            'to_location': location.id,
            'quantity': Decimal('50'),
            'reason': 'Received from supplier',
        }
        form = StockMovementForm(data=data)
        assert form.is_valid(), f"Form errors: {form.errors}"

    def test_form_valid_sale_movement(self, product, location, stock_batch):
        """Test form validates sale movement correctly."""
        from apps.inventory.forms import StockMovementForm
        data = {
            'movement_type': 'sale',
            'product': product.id,
            'from_location': location.id,
            'batch': stock_batch.id,
            'quantity': Decimal('10'),
            'reason': 'Customer purchase',
        }
        form = StockMovementForm(data=data)
        assert form.is_valid(), f"Form errors: {form.errors}"

    def test_form_requires_from_location_for_outbound(self, product, location):
        """Test that outbound movements require from_location."""
        from apps.inventory.forms import StockMovementForm
        data = {
            'movement_type': 'sale',
            'product': product.id,
            'quantity': Decimal('10'),
            'reason': 'Sale',
        }
        form = StockMovementForm(data=data)
        assert not form.is_valid()
        assert 'from_location' in form.errors or '__all__' in form.errors

    def test_form_requires_to_location_for_inbound(self, product, location):
        """Test that inbound movements require to_location."""
        from apps.inventory.forms import StockMovementForm
        data = {
            'movement_type': 'receive',
            'product': product.id,
            'quantity': Decimal('50'),
            'reason': 'Receive',
        }
        form = StockMovementForm(data=data)
        assert not form.is_valid()
        assert 'to_location' in form.errors or '__all__' in form.errors

    def test_form_quantity_must_be_positive(self, product, location):
        """Test that quantity must be positive."""
        from apps.inventory.forms import StockMovementForm
        data = {
            'movement_type': 'receive',
            'product': product.id,
            'to_location': location.id,
            'quantity': Decimal('-10'),
            'reason': 'Test',
        }
        form = StockMovementForm(data=data)
        assert not form.is_valid()
        assert 'quantity' in form.errors


# =============================================================================
# FORM TESTS - PurchaseOrderForm
# =============================================================================

@pytest.mark.django_db
class TestPurchaseOrderForm:
    """Tests for PurchaseOrderForm."""

    def test_form_exists(self):
        """Test that PurchaseOrderForm exists."""
        from apps.inventory.forms import PurchaseOrderForm
        assert PurchaseOrderForm is not None

    def test_form_valid_data(self, supplier, location):
        """Test form with valid data."""
        from apps.inventory.forms import PurchaseOrderForm
        from django.utils import timezone
        data = {
            'supplier': supplier.id,
            'expected_date': (timezone.now().date()),
            'delivery_location': location.id,
            'notes': 'Urgent order',
        }
        form = PurchaseOrderForm(data=data)
        assert form.is_valid(), f"Form errors: {form.errors}"

    def test_form_auto_generates_po_number(self, supplier, location):
        """Test that PO number is auto-generated on save."""
        from apps.inventory.forms import PurchaseOrderForm
        from django.utils import timezone
        data = {
            'supplier': supplier.id,
            'expected_date': timezone.now().date(),
            'delivery_location': location.id,
        }
        form = PurchaseOrderForm(data=data)
        assert form.is_valid()
        instance = form.save(commit=False)
        # PO number should be generated
        assert instance.po_number is not None or hasattr(form, 'generate_po_number')


# =============================================================================
# FORM TESTS - StockCountForm
# =============================================================================

@pytest.mark.django_db
class TestStockCountForm:
    """Tests for StockCountForm."""

    def test_form_exists(self):
        """Test that StockCountForm exists."""
        from apps.inventory.forms import StockCountForm
        assert StockCountForm is not None

    def test_form_valid_full_count(self, location):
        """Test form with valid full count data."""
        from apps.inventory.forms import StockCountForm
        from django.utils import timezone
        data = {
            'location': location.id,
            'count_type': 'full',
            'count_date': timezone.now().date(),
        }
        form = StockCountForm(data=data)
        assert form.is_valid(), f"Form errors: {form.errors}"

    def test_form_valid_cycle_count(self, location):
        """Test form with cycle count."""
        from apps.inventory.forms import StockCountForm
        from django.utils import timezone
        data = {
            'location': location.id,
            'count_type': 'cycle',
            'count_date': timezone.now().date(),
        }
        form = StockCountForm(data=data)
        assert form.is_valid(), f"Form errors: {form.errors}"


# =============================================================================
# FORM TESTS - StockTransferForm
# =============================================================================

@pytest.mark.django_db
class TestStockTransferForm:
    """Tests for StockTransferForm."""

    def test_form_exists(self):
        """Test that StockTransferForm exists."""
        from apps.inventory.forms import StockTransferForm
        assert StockTransferForm is not None

    def test_form_valid_transfer(self, product, location, second_location, stock_batch):
        """Test form with valid transfer data."""
        from apps.inventory.forms import StockTransferForm
        data = {
            'product': product.id,
            'batch': stock_batch.id,
            'from_location': location.id,
            'to_location': second_location.id,
            'quantity': Decimal('25'),
            'reason': 'Restocking pharmacy',
        }
        form = StockTransferForm(data=data)
        assert form.is_valid(), f"Form errors: {form.errors}"

    def test_form_rejects_same_location_transfer(self, product, location, stock_batch):
        """Test that transfer to same location is rejected."""
        from apps.inventory.forms import StockTransferForm
        data = {
            'product': product.id,
            'batch': stock_batch.id,
            'from_location': location.id,
            'to_location': location.id,
            'quantity': Decimal('25'),
            'reason': 'Invalid transfer',
        }
        form = StockTransferForm(data=data)
        assert not form.is_valid()
        assert '__all__' in form.errors or 'to_location' in form.errors


# =============================================================================
# SERVICE TESTS - Stock Level Updates
# =============================================================================

@pytest.mark.django_db
class TestStockServices:
    """Tests for inventory service functions."""

    def test_update_stock_level_inbound(self, product, location, stock_level, staff_user):
        """Test stock level increases on inbound movement."""
        from apps.inventory.services import update_stock_level

        # Create inbound movement
        movement = StockMovement(
            product=product,
            movement_type='receive',
            to_location=location,
            quantity=Decimal('50'),
            recorded_by=staff_user
        )

        initial_qty = stock_level.quantity
        update_stock_level(movement)
        stock_level.refresh_from_db()

        assert stock_level.quantity == initial_qty + Decimal('50')

    def test_update_stock_level_outbound(self, product, location, stock_level, staff_user):
        """Test stock level decreases on outbound movement."""
        from apps.inventory.services import update_stock_level

        movement = StockMovement(
            product=product,
            movement_type='sale',
            from_location=location,
            quantity=Decimal('20'),
            recorded_by=staff_user
        )

        initial_qty = stock_level.quantity
        update_stock_level(movement)
        stock_level.refresh_from_db()

        assert stock_level.quantity == initial_qty - Decimal('20')

    def test_update_stock_level_transfer(self, product, location, second_location, stock_level, staff_user):
        """Test stock level changes on transfer."""
        from apps.inventory.services import update_stock_level

        # Create destination stock level
        dest_stock = StockLevel.objects.create(
            product=product,
            location=second_location,
            quantity=Decimal('0')
        )

        movement = StockMovement(
            product=product,
            movement_type='transfer_out',
            from_location=location,
            to_location=second_location,
            quantity=Decimal('30'),
            recorded_by=staff_user
        )

        initial_source = stock_level.quantity
        initial_dest = dest_stock.quantity

        update_stock_level(movement)

        stock_level.refresh_from_db()
        dest_stock.refresh_from_db()

        assert stock_level.quantity == initial_source - Decimal('30')
        assert dest_stock.quantity == initial_dest + Decimal('30')

    def test_update_batch_quantity_outbound(self, product, location, stock_batch, staff_user):
        """Test batch quantity decreases on outbound."""
        from apps.inventory.services import update_batch_quantity

        movement = StockMovement(
            product=product,
            movement_type='sale',
            from_location=location,
            batch=stock_batch,
            quantity=Decimal('15'),
            recorded_by=staff_user
        )

        initial_qty = stock_batch.current_quantity
        update_batch_quantity(movement)
        stock_batch.refresh_from_db()

        assert stock_batch.current_quantity == initial_qty - Decimal('15')

    def test_batch_depleted_status_update(self, product, location, stock_batch, staff_user):
        """Test batch status changes to depleted when empty."""
        from apps.inventory.services import update_batch_quantity

        # Set batch to small quantity
        stock_batch.current_quantity = Decimal('10')
        stock_batch.save()

        movement = StockMovement(
            product=product,
            movement_type='sale',
            from_location=location,
            batch=stock_batch,
            quantity=Decimal('10'),
            recorded_by=staff_user
        )

        update_batch_quantity(movement)
        stock_batch.refresh_from_db()

        assert stock_batch.current_quantity == Decimal('0')
        assert stock_batch.status == 'depleted'


# =============================================================================
# SERVICE TESTS - PO Number Generation
# =============================================================================

@pytest.mark.django_db
class TestPONumberGeneration:
    """Tests for PO number generation."""

    def test_generate_po_number_format(self):
        """Test PO number follows PO-YYYYMMDD-XXX format."""
        from apps.inventory.services import generate_po_number

        po_number = generate_po_number()

        # Should start with PO-
        assert po_number.startswith('PO-')
        # Should have format PO-YYYYMMDD-XXX
        parts = po_number.split('-')
        assert len(parts) == 3
        assert len(parts[1]) == 8  # YYYYMMDD
        assert len(parts[2]) == 3  # XXX

    def test_generate_po_number_increments(self):
        """Test PO numbers increment correctly same day."""
        from apps.inventory.services import generate_po_number

        po1 = generate_po_number()
        # Create a PO with this number
        PurchaseOrder.objects.create(
            po_number=po1,
            supplier=Supplier.objects.create(name='Test Supplier'),
            status='draft'
        )

        po2 = generate_po_number()

        # Second PO should have incremented number
        assert po1 != po2
        assert int(po2.split('-')[2]) == int(po1.split('-')[2]) + 1


# =============================================================================
# SERVICE TESTS - Stock Count Workflow
# =============================================================================

@pytest.mark.django_db
class TestStockCountServices:
    """Tests for stock count workflow services."""

    def test_create_count_lines_for_location(self, location, stock_level, staff_user):
        """Test creating count lines populates from stock levels."""
        from apps.inventory.services import create_stock_count_with_lines
        from django.utils import timezone

        stock_count = create_stock_count_with_lines(
            location=location,
            count_type='full',
            counted_by=staff_user
        )

        assert stock_count.id is not None
        assert stock_count.lines.count() >= 1

        # Line should have system_quantity from stock level
        line = stock_count.lines.first()
        assert line.system_quantity == stock_level.quantity

    def test_post_count_adjustments(self, location, stock_level, staff_user):
        """Test posting count adjustments updates stock levels."""
        from apps.inventory.services import (
            create_stock_count_with_lines,
            post_count_adjustments
        )

        # Create count
        stock_count = create_stock_count_with_lines(
            location=location,
            count_type='full',
            counted_by=staff_user
        )

        # Set counted quantity different from system
        line = stock_count.lines.first()
        line.counted_quantity = Decimal('95')  # System was 100
        line.adjustment_reason = 'Found 5 damaged units'
        line.save()

        # Post adjustments
        post_count_adjustments(stock_count, approved_by=staff_user)

        stock_level.refresh_from_db()

        # Stock should now be 95
        assert stock_level.quantity == Decimal('95')

        # Count should be posted
        stock_count.refresh_from_db()
        assert stock_count.status == 'posted'


# =============================================================================
# SERVICE TESTS - PO Receiving Workflow
# =============================================================================

@pytest.mark.django_db
class TestPOReceivingServices:
    """Tests for PO receiving workflow services."""

    def test_receive_po_creates_batch(self, supplier, location, product, staff_user):
        """Test receiving PO creates stock batch."""
        from apps.inventory.services import receive_purchase_order_line
        from django.utils import timezone

        # Create PO and line
        po = PurchaseOrder.objects.create(
            po_number='PO-TEST-001',
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

        # Receive the line
        batch = receive_purchase_order_line(
            po_line=line,
            quantity_received=Decimal('50'),
            batch_number='BATCH-NEW-001',
            lot_number='LOT-NEW-001',
            expiry_date=timezone.now().date(),
            received_by=staff_user
        )

        assert batch is not None
        assert batch.batch_number == 'BATCH-NEW-001'
        assert batch.current_quantity == Decimal('50')

        # PO line should be updated
        line.refresh_from_db()
        assert line.quantity_received == Decimal('50')

    def test_receive_po_updates_stock_level(self, supplier, location, product, staff_user):
        """Test receiving PO updates stock level."""
        from apps.inventory.services import receive_purchase_order_line
        from django.utils import timezone

        # Create initial stock level
        stock_level = StockLevel.objects.create(
            product=product,
            location=location,
            quantity=Decimal('10')
        )

        po = PurchaseOrder.objects.create(
            po_number='PO-TEST-002',
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

        receive_purchase_order_line(
            po_line=line,
            quantity_received=Decimal('50'),
            batch_number='BATCH-002',
            received_by=staff_user
        )

        stock_level.refresh_from_db()
        assert stock_level.quantity == Decimal('60')  # 10 + 50

    def test_partial_receive_updates_po_status(self, supplier, location, product, staff_user):
        """Test partial receive changes PO status to partial."""
        from apps.inventory.services import receive_purchase_order_line

        po = PurchaseOrder.objects.create(
            po_number='PO-TEST-003',
            supplier=supplier,
            delivery_location=location,
            status='confirmed'
        )
        line = PurchaseOrderLine.objects.create(
            purchase_order=po,
            product=product,
            quantity_ordered=Decimal('100'),
            unit_cost=Decimal('35.00'),
            line_total=Decimal('3500.00')
        )

        # Receive only 50 of 100
        receive_purchase_order_line(
            po_line=line,
            quantity_received=Decimal('50'),
            batch_number='BATCH-003',
            received_by=staff_user
        )

        po.refresh_from_db()
        assert po.status == 'partial'

    def test_full_receive_updates_po_status(self, supplier, location, product, staff_user):
        """Test full receive changes PO status to received."""
        from apps.inventory.services import receive_purchase_order_line

        po = PurchaseOrder.objects.create(
            po_number='PO-TEST-004',
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

        receive_purchase_order_line(
            po_line=line,
            quantity_received=Decimal('50'),
            batch_number='BATCH-004',
            received_by=staff_user
        )

        po.refresh_from_db()
        assert po.status == 'received'
