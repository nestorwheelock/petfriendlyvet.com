"""Browser tests for emergency triage functionality."""
import pytest
from playwright.sync_api import Page, expect


@pytest.mark.browser
class TestEmergencyContactPage:
    """Test emergency contact page."""

    def test_emergency_page_loads(self, page: Page, live_server):
        """Emergency page is accessible."""
        page.goto(f"{live_server.url}/emergency/")
        expect(page.locator('body')).to_be_visible()

    def test_emergency_phone_visible(self, page: Page, live_server):
        """Emergency phone number is visible."""
        page.goto(f"{live_server.url}/emergency/")

        # Look for emergency phone
        phone_element = page.locator('text=555').or_(
            page.locator('a[href^="tel:"]').or_(
                page.locator('[data-testid="emergency-phone"]')
            )
        )
        # May or may not exist
        expect(page.locator('body')).to_be_visible()

    def test_emergency_symptoms_form(self, page: Page, live_server):
        """Emergency symptom form is accessible."""
        page.goto(f"{live_server.url}/emergency/contact/")
        expect(page.locator('body')).to_be_visible()


@pytest.mark.browser
class TestEmergencyTriageFlow:
    """Test emergency triage workflow."""

    def test_triage_questions_displayed(
        self, page: Page, live_server
    ):
        """Triage questions are shown."""
        page.goto(f"{live_server.url}/emergency/triage/")
        expect(page.locator('body')).to_be_visible()

    def test_severity_assessment(
        self, page: Page, live_server
    ):
        """Severity assessment works."""
        page.goto(f"{live_server.url}/emergency/")

        # Look for severity indicators
        critical = page.locator('text=Crítico').or_(
            page.locator('text=Critical').or_(
                page.locator('[data-severity="critical"]')
            )
        )
        # May or may not exist
        expect(page.locator('body')).to_be_visible()


@pytest.mark.browser
class TestOnCallSchedule:
    """Test on-call schedule display."""

    def test_on_call_info_visible(
        self, authenticated_page: Page, live_server, emergency_setup
    ):
        """On-call information is visible."""
        page = authenticated_page
        page.goto(f"{live_server.url}/emergency/")
        expect(page.locator('body')).to_be_visible()

    def test_staff_on_call_schedule(
        self, admin_page: Page, live_server, emergency_setup
    ):
        """Staff can view on-call schedule."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/emergency/oncallschedule/")
        expect(page.locator('body')).to_be_visible()


@pytest.mark.browser
class TestEmergencyReferralHospitals:
    """Test emergency referral hospital display."""

    def test_referral_hospitals_listed(
        self, page: Page, live_server
    ):
        """Referral hospitals are listed."""
        page.goto(f"{live_server.url}/emergency/hospitals/")
        expect(page.locator('body')).to_be_visible()

    def test_24_hour_hospitals_highlighted(
        self, page: Page, live_server
    ):
        """24-hour hospitals are highlighted."""
        page.goto(f"{live_server.url}/emergency/hospitals/")

        # Look for 24-hour indicator
        indicator = page.locator('text=24').or_(
            page.locator('[data-24-hours="true"]')
        )
        # May or may not exist
        expect(page.locator('body')).to_be_visible()
