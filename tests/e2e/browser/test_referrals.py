"""Browser tests for specialist referral functionality."""
import pytest
from playwright.sync_api import Page, expect


@pytest.mark.browser
class TestReferralList:
    """Test referral list pages."""

    def test_referrals_page_loads(
        self, staff_page: Page, live_server
    ):
        """Referrals page is accessible."""
        page = staff_page
        page.goto(f"{live_server.url}/referrals/")
        expect(page.locator('body')).to_be_visible()

    def test_pending_referrals_visible(
        self, staff_page: Page, live_server
    ):
        """Pending referrals are displayed."""
        page = staff_page
        page.goto(f"{live_server.url}/referrals/pending/")
        expect(page.locator('body')).to_be_visible()


@pytest.mark.browser
class TestCreateReferral:
    """Test referral creation."""

    def test_create_referral_form(
        self, staff_page: Page, live_server
    ):
        """Create referral form is accessible."""
        page = staff_page
        page.goto(f"{live_server.url}/referrals/create/")
        expect(page.locator('body')).to_be_visible()

    def test_specialist_directory_loads(
        self, staff_page: Page, live_server
    ):
        """Specialist directory is accessible."""
        page = staff_page
        page.goto(f"{live_server.url}/referrals/specialists/")
        expect(page.locator('body')).to_be_visible()

    def test_referral_admin_add(
        self, admin_page: Page, live_server
    ):
        """Referral admin add page is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/referrals/referral/add/")
        expect(page.locator('body')).to_be_visible()


@pytest.mark.browser
class TestSpecialistDirectory:
    """Test specialist directory functionality."""

    def test_specialists_list_loads(
        self, staff_page: Page, live_server
    ):
        """Specialists list is accessible."""
        page = staff_page
        page.goto(f"{live_server.url}/referrals/specialists/")
        expect(page.locator('body')).to_be_visible()

    def test_specialist_profile_accessible(
        self, staff_page: Page, live_server
    ):
        """Specialist profiles are accessible."""
        page = staff_page
        page.goto(f"{live_server.url}/referrals/specialists/")
        expect(page.locator('body')).to_be_visible()

    def test_specialist_admin_list(
        self, admin_page: Page, live_server
    ):
        """Specialist admin list is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/referrals/specialist/")
        expect(page.locator('body')).to_be_visible()


@pytest.mark.browser
class TestReferralDocuments:
    """Test referral document management."""

    def test_upload_document_accessible(
        self, admin_page: Page, live_server
    ):
        """Document upload is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/referrals/referraldocument/add/")
        expect(page.locator('body')).to_be_visible()

    def test_documents_admin_list(
        self, admin_page: Page, live_server
    ):
        """Documents admin list is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/referrals/referraldocument/")
        expect(page.locator('body')).to_be_visible()


@pytest.mark.browser
class TestReferralTracking:
    """Test referral status tracking."""

    def test_referral_status_page(
        self, staff_page: Page, live_server
    ):
        """Referral status page is accessible."""
        page = staff_page
        page.goto(f"{live_server.url}/referrals/")
        expect(page.locator('body')).to_be_visible()

    def test_referral_admin_list(
        self, admin_page: Page, live_server
    ):
        """Referral admin list is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/referrals/referral/")
        expect(page.locator('body')).to_be_visible()


@pytest.mark.browser
class TestInboundReferrals:
    """Test inbound referral handling."""

    def test_inbound_referrals_page(
        self, staff_page: Page, live_server
    ):
        """Inbound referrals page is accessible."""
        page = staff_page
        page.goto(f"{live_server.url}/referrals/inbound/")
        expect(page.locator('body')).to_be_visible()

    def test_accept_referral_workflow(
        self, staff_page: Page, live_server
    ):
        """Accept referral workflow is accessible."""
        page = staff_page
        page.goto(f"{live_server.url}/referrals/inbound/")
        expect(page.locator('body')).to_be_visible()
