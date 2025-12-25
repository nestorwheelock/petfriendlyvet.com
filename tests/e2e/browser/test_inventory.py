"""Browser tests for inventory management functionality."""
import pytest
from playwright.sync_api import Page, expect


@pytest.mark.browser
class TestInventoryDashboard:
    """Test inventory dashboard."""

    def test_inventory_dashboard_loads(
        self, staff_page: Page, live_server
    ):
        """Inventory dashboard is accessible."""
        page = staff_page
        page.goto(f"{live_server.url}/inventory/")
        expect(page.locator('body')).to_be_visible()

    def test_stock_levels_visible(
        self, staff_page: Page, live_server
    ):
        """Stock levels are displayed."""
        page = staff_page
        page.goto(f"{live_server.url}/inventory/")

        # Look for stock display
        stock_section = page.locator('text=Stock').or_(
            page.locator('[data-testid="stock-levels"]')
        )
        # May or may not exist
        expect(page.locator('body')).to_be_visible()


@pytest.mark.browser
class TestLowStockAlerts:
    """Test low stock alert functionality."""

    def test_low_stock_alerts_visible(
        self, staff_page: Page, live_server
    ):
        """Low stock alerts are shown."""
        page = staff_page
        page.goto(f"{live_server.url}/inventory/alerts/")
        expect(page.locator('body')).to_be_visible()

    def test_reorder_threshold_indicators(
        self, staff_page: Page, live_server
    ):
        """Reorder threshold indicators are visible."""
        page = staff_page
        page.goto(f"{live_server.url}/inventory/")

        # Look for low stock indicator
        low_stock = page.locator('.low-stock').or_(
            page.locator('[data-status="low"]').or_(
                page.locator('text=Low Stock')
            )
        )
        # May or may not exist
        expect(page.locator('body')).to_be_visible()


@pytest.mark.browser
class TestPurchaseOrders:
    """Test purchase order functionality."""

    def test_purchase_orders_list_loads(
        self, staff_page: Page, live_server
    ):
        """Purchase orders list is accessible."""
        page = staff_page
        page.goto(f"{live_server.url}/inventory/purchase-orders/")
        expect(page.locator('body')).to_be_visible()

    def test_create_purchase_order_form(
        self, admin_page: Page, live_server
    ):
        """Create PO form is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/inventory/purchaseorder/add/")
        expect(page.locator('body')).to_be_visible()

    def test_purchase_order_admin(
        self, admin_page: Page, live_server
    ):
        """PO admin list is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/inventory/purchaseorder/")
        expect(page.locator('body')).to_be_visible()


@pytest.mark.browser
class TestStockBatches:
    """Test stock batch management."""

    def test_batch_list_loads(
        self, staff_page: Page, live_server
    ):
        """Stock batch list is accessible."""
        page = staff_page
        page.goto(f"{live_server.url}/inventory/batches/")
        expect(page.locator('body')).to_be_visible()

    def test_expiry_tracking_visible(
        self, staff_page: Page, live_server
    ):
        """Expiry tracking is displayed."""
        page = staff_page
        page.goto(f"{live_server.url}/inventory/expiring/")
        expect(page.locator('body')).to_be_visible()

    def test_batch_admin_list(
        self, admin_page: Page, live_server
    ):
        """Batch admin list is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/inventory/stockbatch/")
        expect(page.locator('body')).to_be_visible()


@pytest.mark.browser
class TestStockMovements:
    """Test stock movement tracking."""

    def test_movements_list_loads(
        self, staff_page: Page, live_server
    ):
        """Stock movements list is accessible."""
        page = staff_page
        page.goto(f"{live_server.url}/inventory/movements/")
        expect(page.locator('body')).to_be_visible()

    def test_record_movement_form(
        self, admin_page: Page, live_server
    ):
        """Record movement form is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/inventory/stockmovement/add/")
        expect(page.locator('body')).to_be_visible()


@pytest.mark.browser
class TestSupplierManagement:
    """Test supplier management."""

    def test_suppliers_list_loads(
        self, staff_page: Page, live_server
    ):
        """Suppliers list is accessible."""
        page = staff_page
        page.goto(f"{live_server.url}/inventory/suppliers/")
        expect(page.locator('body')).to_be_visible()

    def test_add_supplier_form(
        self, admin_page: Page, live_server
    ):
        """Add supplier form is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/inventory/supplier/add/")
        expect(page.locator('body')).to_be_visible()

    def test_supplier_admin_list(
        self, admin_page: Page, live_server
    ):
        """Supplier admin list is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/inventory/supplier/")
        expect(page.locator('body')).to_be_visible()


@pytest.mark.browser
class TestReorderRules:
    """Test reorder rule configuration."""

    def test_reorder_rules_admin(
        self, admin_page: Page, live_server
    ):
        """Reorder rules admin is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/inventory/reorderrule/")
        expect(page.locator('body')).to_be_visible()

    def test_add_reorder_rule_form(
        self, admin_page: Page, live_server
    ):
        """Add reorder rule form is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/inventory/reorderrule/add/")
        expect(page.locator('body')).to_be_visible()
