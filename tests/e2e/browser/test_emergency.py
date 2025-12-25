"""Browser tests for emergency triage functionality.

Tests both admin interface and customer-facing emergency pages.
"""
import re

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.browser
class TestEmergencyCustomerPages:
    """Test customer-facing emergency pages."""

    def test_emergency_home_loads(self, page: Page, live_server):
        """Emergency home page loads for anonymous users."""
        page.goto(f"{live_server.url}/emergency/")
        expect(page.locator('h1')).to_contain_text('Emergency', ignore_case=True)

    def test_triage_form_loads(self, page: Page, live_server):
        """Triage form page loads for anonymous users."""
        page.goto(f"{live_server.url}/emergency/triage/")
        expect(page.locator('h1')).to_contain_text('Symptom', ignore_case=True)

    def test_first_aid_list_loads(self, page: Page, live_server):
        """First aid list page loads."""
        page.goto(f"{live_server.url}/emergency/first-aid/")
        expect(page.locator('h1')).to_contain_text('First Aid', ignore_case=True)

    def test_hospital_list_loads(self, page: Page, live_server):
        """Hospital list page loads."""
        page.goto(f"{live_server.url}/emergency/hospitals/")
        expect(page.locator('h1')).to_contain_text('Hospital', ignore_case=True)

    def test_contact_form_loads(self, page: Page, live_server):
        """Emergency contact form loads for anonymous users."""
        page.goto(f"{live_server.url}/emergency/contact/")
        expect(page.locator('h1')).to_contain_text('Emergency Contact', ignore_case=True)

    def test_emergency_history_requires_login(self, page: Page, live_server):
        """Emergency history requires authentication."""
        page.goto(f"{live_server.url}/emergency/history/")
        # Should redirect to login
        expect(page).to_have_url(re.compile(r'.*(login|accounts).*'))

    def test_emergency_history_loads_for_authenticated(
        self, authenticated_page: Page, live_server
    ):
        """Authenticated user can access emergency history."""
        page = authenticated_page
        page.goto(f"{live_server.url}/emergency/history/")
        expect(page.locator('h1')).to_contain_text('Emergency History', ignore_case=True)

    def test_triage_form_submission(self, page: Page, live_server):
        """Triage form submits and shows result."""
        page.goto(f"{live_server.url}/emergency/triage/")

        # Fill out form - click on the label containing the hidden radio
        page.locator('label:has(input[value="dog"])').click()
        page.fill('textarea[name="symptoms"]', 'vomiting and not eating')
        page.click('button[type="submit"]')

        # Should redirect to result page
        expect(page).to_have_url(re.compile(r'.*/triage/result.*'))

    def test_contact_form_submission(self, page: Page, live_server):
        """Emergency contact form submits successfully."""
        page.goto(f"{live_server.url}/emergency/contact/")

        # Fill out form - click on labels for hidden radio inputs
        page.fill('input[name="phone"]', '123-456-7890')
        page.locator('label:has(input[value="cat"])').click()
        page.fill('input[name="age"]', '3 years')
        page.fill('textarea[name="symptoms"]', 'not eating, lethargic')
        page.click('button[type="submit"]')

        # Should redirect to success page
        expect(page).to_have_url(re.compile(r'.*/contact/success.*'))


@pytest.mark.browser
class TestEmergencyContactAdmin:
    """Test emergency contact admin."""

    def test_emergency_contact_admin_loads(
        self, admin_page: Page, live_server
    ):
        """Emergency contact admin list is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/emergency/emergencycontact/")
        expect(page.locator('h1')).to_contain_text('emergency', ignore_case=True)

    def test_add_emergency_contact_form(
        self, admin_page: Page, live_server
    ):
        """Add emergency contact form is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/emergency/emergencycontact/add/")
        expect(page.locator('body')).to_be_visible()


@pytest.mark.browser
class TestOnCallScheduleAdmin:
    """Test on-call schedule admin."""

    def test_on_call_schedule_admin_loads(
        self, admin_page: Page, live_server
    ):
        """On-call schedule admin list is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/emergency/oncallschedule/")
        expect(page.locator('h1')).to_contain_text('call', ignore_case=True)

    def test_add_on_call_schedule_form(
        self, admin_page: Page, live_server
    ):
        """Add on-call schedule form is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/emergency/oncallschedule/add/")
        expect(page.locator('body')).to_be_visible()

    def test_view_on_call_schedule(
        self, admin_page: Page, live_server, emergency_setup
    ):
        """Can view on-call schedule in admin."""
        page = admin_page
        on_call = emergency_setup['on_call']
        page.goto(f"{live_server.url}/admin/emergency/oncallschedule/{on_call.pk}/change/")
        expect(page.locator('body')).to_be_visible()


@pytest.mark.browser
class TestEmergencySymptomAdmin:
    """Test emergency symptom admin."""

    def test_symptom_admin_loads(
        self, admin_page: Page, live_server
    ):
        """Emergency symptom admin list is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/emergency/emergencysymptom/")
        expect(page.locator('h1')).to_contain_text('symptom', ignore_case=True)

    def test_add_symptom_form(
        self, admin_page: Page, live_server
    ):
        """Add symptom form is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/emergency/emergencysymptom/add/")
        expect(page.locator('input[name="keyword"]')).to_be_visible()


@pytest.mark.browser
class TestEmergencyReferralAdmin:
    """Test emergency referral hospital admin."""

    def test_referral_hospital_admin_loads(
        self, admin_page: Page, live_server
    ):
        """Emergency referral hospital admin list is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/emergency/emergencyreferral/")
        expect(page.locator('h1')).to_contain_text('referral', ignore_case=True)

    def test_add_referral_hospital_form(
        self, admin_page: Page, live_server
    ):
        """Add referral hospital form is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/emergency/emergencyreferral/add/")
        expect(page.locator('input[name="name"]')).to_be_visible()
