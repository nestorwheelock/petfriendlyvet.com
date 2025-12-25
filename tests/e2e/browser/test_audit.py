"""Browser tests for audit logging verification."""
import pytest
from datetime import date, timedelta, time as time_obj
from decimal import Decimal
from playwright.sync_api import Page, expect


@pytest.fixture
def audit_inventory_setup(db, staff_user):
    """Minimal inventory setup for audit tests."""
    from apps.store.models import Category, Product
    from apps.inventory.models import StockLocation, Supplier

    category = Category.objects.create(
        name='Audit Test Category',
        slug='audit-test-cat',
        is_active=True,
    )
    product = Product.objects.create(
        name='Audit Test Product',
        slug='audit-test-product',
        category=category,
        price=Decimal('100.00'),
        stock_quantity=50,
        sku='AUDIT-001',
        is_active=True,
    )
    location = StockLocation.objects.create(
        name='Main Warehouse',
        location_type='warehouse',
        is_active=True,
    )
    supplier = Supplier.objects.create(
        name='Audit Supplier',
        email='audit@supplier.com',
        is_active=True,
    )
    return {'product': product, 'location': location, 'supplier': supplier}


@pytest.fixture
def audit_referrals_setup(db, owner_user):
    """Minimal referrals setup for audit tests."""
    from apps.referrals.models import Specialist, Referral
    from apps.pets.models import Pet

    pet = Pet.objects.create(
        owner=owner_user,
        name='AuditPet',
        species='dog',
        breed='Labrador',
        gender='male',
        date_of_birth=date.today() - timedelta(days=365),
    )
    specialist = Specialist.objects.create(
        name='Dr. Audit',
        specialty='oncology',
        phone='555-0100',
        email='audit@specialist.com',
        is_active=True,
        relationship_status='active',
    )
    referral = Referral.objects.create(
        direction='outbound',
        pet=pet,
        owner=owner_user,
        specialist=specialist,
        reason='Audit test referral',
        urgency='routine',
        status='sent',
    )
    return {'pet': pet, 'specialist': specialist, 'referral': referral}


@pytest.fixture
def audit_practice_setup(db, staff_user):
    """Minimal practice setup for audit tests."""
    from apps.practice.models import StaffProfile, ClinicSettings

    profile, _ = StaffProfile.objects.get_or_create(
        user=staff_user,
        defaults={'role': 'receptionist'}
    )
    settings, _ = ClinicSettings.objects.get_or_create(
        pk=1,
        defaults={
            'name': 'Audit Test Clinic',
            'opening_time': time_obj(9, 0),
            'closing_time': time_obj(18, 0),
        }
    )
    return {'profile': profile, 'settings': settings}


@pytest.mark.browser
class TestAuditLogging:
    """Browser tests verifying audit logging."""

    def test_inventory_dashboard_creates_audit_log(
        self, staff_page: Page, live_server, audit_inventory_setup
    ):
        """Accessing inventory dashboard creates audit entry."""
        page = staff_page
        page.goto(f"{live_server.url}/inventory/")

        # Wait for page to fully load
        expect(page.locator('h1')).to_contain_text('Inventory', ignore_case=True)

        # Verify audit log was created
        from apps.audit.models import AuditLog
        log = AuditLog.objects.filter(resource_type='inventory.dashboard').first()
        assert log is not None, "Audit log entry should be created for inventory dashboard"
        assert log.action == 'view'
        assert log.user.is_staff

    def test_referral_detail_creates_audit_log(
        self, staff_page: Page, live_server, audit_referrals_setup
    ):
        """Viewing referral detail creates audit entry with resource ID."""
        page = staff_page
        referral_id = audit_referrals_setup['referral'].pk
        page.goto(f"{live_server.url}/referrals/outbound/{referral_id}/")

        # Wait for page to fully load
        expect(page.locator('body')).to_contain_text('AuditPet')

        from apps.audit.models import AuditLog
        log = AuditLog.objects.filter(
            resource_type='referrals.referral',
            resource_id=str(referral_id)
        ).first()
        assert log is not None, "Audit log should capture referral detail access"
        assert log.action == 'view'

    def test_practice_settings_marked_high_sensitivity(
        self, staff_page: Page, live_server, audit_practice_setup
    ):
        """Clinic settings access is marked as high sensitivity."""
        page = staff_page
        page.goto(f"{live_server.url}/practice/settings/")

        # Wait for page to fully load
        expect(page.locator('h1')).to_contain_text('Settings', ignore_case=True)

        from apps.audit.models import AuditLog
        log = AuditLog.objects.filter(resource_type='practice.settings').first()
        assert log is not None, "Audit log should be created for settings access"
        assert log.sensitivity == 'high', "Settings access should be high sensitivity"

    def test_multiple_page_views_create_multiple_logs(
        self, staff_page: Page, live_server, audit_inventory_setup
    ):
        """Each page view creates a separate audit entry."""
        page = staff_page

        # Clear any existing audit logs
        from apps.audit.models import AuditLog
        AuditLog.objects.all().delete()

        # Visit multiple pages
        page.goto(f"{live_server.url}/inventory/")
        expect(page.locator('h1')).to_contain_text('Inventory', ignore_case=True)

        page.goto(f"{live_server.url}/inventory/stock/")
        expect(page.locator('h1')).to_contain_text('Stock', ignore_case=True)

        page.goto(f"{live_server.url}/inventory/alerts/")
        expect(page.locator('h1')).to_contain_text('Alert', ignore_case=True)

        logs = AuditLog.objects.filter(resource_type__startswith='inventory.')
        assert logs.count() >= 3, "Each page view should create a separate audit log"

    def test_audit_log_captures_user_ip(
        self, staff_page: Page, live_server, audit_inventory_setup
    ):
        """Audit log captures IP address."""
        page = staff_page
        page.goto(f"{live_server.url}/inventory/")

        expect(page.locator('h1')).to_contain_text('Inventory', ignore_case=True)

        from apps.audit.models import AuditLog
        log = AuditLog.objects.filter(resource_type='inventory.dashboard').first()
        assert log is not None
        assert log.ip_address is not None, "IP address should be captured"

    def test_audit_log_captures_user_agent(
        self, staff_page: Page, live_server, audit_inventory_setup
    ):
        """Audit log captures user agent."""
        page = staff_page
        page.goto(f"{live_server.url}/inventory/")

        expect(page.locator('h1')).to_contain_text('Inventory', ignore_case=True)

        from apps.audit.models import AuditLog
        log = AuditLog.objects.filter(resource_type='inventory.dashboard').first()
        assert log is not None
        assert log.user_agent != '', "User agent should be captured"

    def test_referrals_dashboard_audit(
        self, staff_page: Page, live_server, audit_referrals_setup
    ):
        """Referrals dashboard creates audit entry."""
        page = staff_page
        page.goto(f"{live_server.url}/referrals/")

        expect(page.locator('h1')).to_contain_text('Referral', ignore_case=True)

        from apps.audit.models import AuditLog
        log = AuditLog.objects.filter(resource_type='referrals.dashboard').first()
        assert log is not None, "Audit log should be created for referrals dashboard"

    def test_practice_dashboard_audit(
        self, staff_page: Page, live_server, audit_practice_setup
    ):
        """Practice dashboard creates audit entry."""
        page = staff_page
        page.goto(f"{live_server.url}/practice/")

        expect(page.locator('h1')).to_contain_text('Practice', ignore_case=True)

        from apps.audit.models import AuditLog
        log = AuditLog.objects.filter(resource_type='practice.dashboard').first()
        assert log is not None, "Audit log should be created for practice dashboard"

    def test_non_audited_paths_no_log(
        self, staff_page: Page, live_server
    ):
        """Non-audited paths (like store) don't create audit entries."""
        page = staff_page

        # Clear any existing audit logs
        from apps.audit.models import AuditLog
        AuditLog.objects.all().delete()

        # Visit store (customer-facing, not audited)
        page.goto(f"{live_server.url}/store/")

        # Check no audit log was created for store
        logs = AuditLog.objects.filter(resource_type__startswith='store.')
        assert logs.count() == 0, "Store pages should not create audit logs"


@pytest.mark.browser
class TestAuditAdmin:
    """Test audit admin interface."""

    def test_audit_admin_loads(
        self, admin_page: Page, live_server
    ):
        """Audit admin list is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/audit/auditlog/")
        expect(page.locator('h1')).to_contain_text('audit log', ignore_case=True)

    def test_audit_admin_search_works(
        self, admin_page: Page, live_server, staff_user
    ):
        """Audit admin search functionality works."""
        # Create some audit logs first
        from apps.audit.models import AuditLog
        AuditLog.objects.create(
            user=staff_user,
            action='view',
            resource_type='inventory.dashboard',
        )

        page = admin_page
        page.goto(f"{live_server.url}/admin/audit/auditlog/")

        # Search should be present
        search_input = page.locator('input[name="q"]')
        expect(search_input).to_be_visible()
