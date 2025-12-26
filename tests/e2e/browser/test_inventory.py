"""Browser tests for inventory management functionality."""
import re
import pytest
from playwright.sync_api import Page, expect


@pytest.mark.browser
class TestStockLocationAdmin:
    """Test stock location admin."""

    def test_stock_location_admin_loads(
        self, admin_page: Page, live_server
    ):
        """Stock location admin list is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/inventory/stocklocation/")
        expect(page.locator('h1')).to_contain_text('location', ignore_case=True)

    def test_add_stock_location_form(
        self, admin_page: Page, live_server
    ):
        """Add stock location form is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/inventory/stocklocation/add/")
        expect(page.locator('input[name="name"]')).to_be_visible()


@pytest.mark.browser
class TestStockLevelAdmin:
    """Test stock level admin."""

    def test_stock_level_admin_loads(
        self, admin_page: Page, live_server
    ):
        """Stock level admin list is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/inventory/stocklevel/")
        expect(page.locator('h1')).to_contain_text('level', ignore_case=True)


@pytest.mark.browser
class TestPurchaseOrderAdmin:
    """Test purchase order admin."""

    def test_purchase_order_admin_loads(
        self, admin_page: Page, live_server
    ):
        """Purchase order admin list is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/inventory/purchaseorder/")
        expect(page.locator('h1')).to_contain_text('purchase', ignore_case=True)

    def test_add_purchase_order_form(
        self, admin_page: Page, live_server
    ):
        """Add purchase order form is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/inventory/purchaseorder/add/")
        expect(page.locator('body')).to_be_visible()


@pytest.mark.browser
class TestStockBatchAdmin:
    """Test stock batch admin."""

    def test_stock_batch_admin_loads(
        self, admin_page: Page, live_server
    ):
        """Stock batch admin list is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/inventory/stockbatch/")
        expect(page.locator('h1')).to_contain_text('batch', ignore_case=True)

    def test_add_stock_batch_form(
        self, admin_page: Page, live_server
    ):
        """Add stock batch form is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/inventory/stockbatch/add/")
        expect(page.locator('body')).to_be_visible()


@pytest.mark.browser
class TestStockMovementAdmin:
    """Test stock movement admin."""

    def test_stock_movement_admin_loads(
        self, admin_page: Page, live_server
    ):
        """Stock movement admin list is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/inventory/stockmovement/")
        expect(page.locator('h1')).to_contain_text('movement', ignore_case=True)

    def test_add_stock_movement_form(
        self, admin_page: Page, live_server
    ):
        """Add stock movement form is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/inventory/stockmovement/add/")
        expect(page.locator('body')).to_be_visible()


@pytest.mark.browser
class TestSupplierAdmin:
    """Test supplier admin."""

    def test_supplier_admin_loads(
        self, admin_page: Page, live_server
    ):
        """Supplier admin list is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/inventory/supplier/")
        expect(page.locator('h1')).to_contain_text('supplier', ignore_case=True)

    def test_add_supplier_form(
        self, admin_page: Page, live_server
    ):
        """Add supplier form is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/inventory/supplier/add/")
        expect(page.locator('input[name="name"]')).to_be_visible()


@pytest.mark.browser
class TestReorderRuleAdmin:
    """Test reorder rule admin."""

    def test_reorder_rule_admin_loads(
        self, admin_page: Page, live_server
    ):
        """Reorder rule admin list is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/inventory/reorderrule/")
        expect(page.locator('h1')).to_contain_text('reorder', ignore_case=True)

    def test_add_reorder_rule_form(
        self, admin_page: Page, live_server
    ):
        """Add reorder rule form is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/inventory/reorderrule/add/")
        expect(page.locator('body')).to_be_visible()


# =============================================================================
# STAFF INTERFACE TESTS
# =============================================================================


@pytest.fixture
def inventory_setup(db, store_with_products):
    """Set up inventory data for staff tests."""
    from datetime import date, timedelta
    from decimal import Decimal
    from apps.inventory.models import (
        StockLocation, LocationType, StockLevel, StockBatch, StockMovement,
        Supplier, PurchaseOrder, PurchaseOrderLine
    )

    # Create location types
    warehouse_type, _ = LocationType.objects.get_or_create(
        code='warehouse',
        defaults={'name': 'Warehouse', 'is_active': True},
    )
    pharmacy_type, _ = LocationType.objects.get_or_create(
        code='pharmacy',
        defaults={'name': 'Pharmacy', 'is_active': True},
    )

    # Create locations
    warehouse = StockLocation.objects.create(
        name='Main Warehouse',
        location_type=warehouse_type,
        is_active=True,
    )
    pharmacy = StockLocation.objects.create(
        name='Pharmacy',
        location_type=pharmacy_type,
        is_active=True,
    )

    # Create a supplier
    supplier = Supplier.objects.create(
        name='VetSupply Co',
        code='VS001',
        contact_name='John Doe',
        email='john@vetsupply.com',
        phone='555-0100',
        is_active=True,
        is_preferred=True,
    )

    product = store_with_products['products'][0]

    # Create stock levels
    stock_level = StockLevel.objects.create(
        product=product,
        location=warehouse,
        quantity=100,
        min_level=10,
    )

    # Create stock batch
    batch = StockBatch.objects.create(
        product=product,
        location=warehouse,
        batch_number='BATCH-001',
        expiry_date=date.today() + timedelta(days=30),
        received_date=date.today() - timedelta(days=5),
        initial_quantity=50,
        current_quantity=45,
        unit_cost=Decimal('10.00'),
    )

    # Create stock movement
    movement = StockMovement.objects.create(
        product=product,
        from_location=warehouse,
        to_location=pharmacy,
        batch=batch,
        quantity=5,
        movement_type='transfer',
        reason='Stock transfer',
    )

    # Create purchase order
    purchase_order = PurchaseOrder.objects.create(
        supplier=supplier,
        delivery_location=warehouse,
        status='received',
        order_date=date.today() - timedelta(days=7),
        received_date=date.today() - timedelta(days=2),
    )

    PurchaseOrderLine.objects.create(
        purchase_order=purchase_order,
        product=product,
        quantity_ordered=50,
        quantity_received=50,
        unit_cost=Decimal('10.00'),
        line_total=Decimal('500.00'),
    )

    return {
        'warehouse': warehouse,
        'pharmacy': pharmacy,
        'supplier': supplier,
        'stock_level': stock_level,
        'batch': batch,
        'movement': movement,
        'purchase_order': purchase_order,
        'product': product,
    }


@pytest.mark.browser
class TestInventoryStaffPages:
    """Test inventory staff interface pages."""

    def test_staff_required_for_inventory(
        self, page: Page, live_server
    ):
        """Inventory pages require staff authentication."""
        page.goto(f"{live_server.url}/inventory/")
        # Should redirect to login
        expect(page).to_have_url(re.compile(r'.*(login|admin).*'))

    def test_dashboard_loads(
        self, staff_page: Page, live_server, inventory_setup
    ):
        """Inventory dashboard loads for staff."""
        page = staff_page
        page.goto(f"{live_server.url}/inventory/")
        expect(page.locator('h1')).to_contain_text('Inventory', ignore_case=True)

    def test_stock_levels_page(
        self, staff_page: Page, live_server, inventory_setup
    ):
        """Stock levels page shows inventory data."""
        page = staff_page
        page.goto(f"{live_server.url}/inventory/stock/")
        expect(page.locator('h1')).to_contain_text('Stock', ignore_case=True)
        # Should show the product in stock
        expect(page.locator('body')).to_contain_text('Test Product')

    def test_batches_list_page(
        self, staff_page: Page, live_server, inventory_setup
    ):
        """Batch list shows inventory batches."""
        page = staff_page
        page.goto(f"{live_server.url}/inventory/batches/")
        expect(page.locator('h1')).to_contain_text('Batch', ignore_case=True)
        # Should show the batch number
        expect(page.locator('body')).to_contain_text('BATCH-001')

    def test_batch_detail_page(
        self, staff_page: Page, live_server, inventory_setup
    ):
        """Batch detail page shows batch information."""
        page = staff_page
        batch_id = inventory_setup['batch'].pk
        page.goto(f"{live_server.url}/inventory/batches/{batch_id}/")
        expect(page.locator('body')).to_contain_text('BATCH-001')

    def test_movements_list_page(
        self, staff_page: Page, live_server, inventory_setup
    ):
        """Movements list shows stock movements."""
        page = staff_page
        page.goto(f"{live_server.url}/inventory/movements/")
        expect(page.locator('h1')).to_contain_text('Movement', ignore_case=True)

    def test_movement_add_page(
        self, staff_page: Page, live_server, inventory_setup
    ):
        """Add movement page has form."""
        page = staff_page
        page.goto(f"{live_server.url}/inventory/movements/add/")
        # Check form elements exist - use the specific form selector
        expect(page.locator('form.bg-white')).to_be_visible()

    def test_suppliers_list_page(
        self, staff_page: Page, live_server, inventory_setup
    ):
        """Suppliers list shows supplier data."""
        page = staff_page
        page.goto(f"{live_server.url}/inventory/suppliers/")
        expect(page.locator('h1')).to_contain_text('Supplier', ignore_case=True)
        expect(page.locator('body')).to_contain_text('VetSupply')

    def test_supplier_detail_page(
        self, staff_page: Page, live_server, inventory_setup
    ):
        """Supplier detail page shows supplier info."""
        page = staff_page
        supplier_id = inventory_setup['supplier'].pk
        page.goto(f"{live_server.url}/inventory/suppliers/{supplier_id}/")
        expect(page.locator('body')).to_contain_text('VetSupply')
        expect(page.locator('body')).to_contain_text('john@vetsupply.com')

    def test_purchase_orders_list_page(
        self, staff_page: Page, live_server, inventory_setup
    ):
        """Purchase orders list shows orders."""
        page = staff_page
        page.goto(f"{live_server.url}/inventory/purchase-orders/")
        expect(page.locator('h1')).to_contain_text('Purchase', ignore_case=True)

    def test_purchase_order_detail_page(
        self, staff_page: Page, live_server, inventory_setup
    ):
        """Purchase order detail page shows order info."""
        page = staff_page
        order_id = inventory_setup['purchase_order'].pk
        page.goto(f"{live_server.url}/inventory/purchase-orders/{order_id}/")
        expect(page.locator('body')).to_contain_text('VetSupply')

    def test_alerts_page(
        self, staff_page: Page, live_server, inventory_setup
    ):
        """Stock alerts page loads."""
        page = staff_page
        page.goto(f"{live_server.url}/inventory/alerts/")
        expect(page.locator('h1')).to_contain_text('Alert', ignore_case=True)

    def test_expiring_items_page(
        self, staff_page: Page, live_server, inventory_setup
    ):
        """Expiring items page loads."""
        page = staff_page
        page.goto(f"{live_server.url}/inventory/expiring/")
        expect(page.locator('h1')).to_contain_text('Expiring', ignore_case=True)
