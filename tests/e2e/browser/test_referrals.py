"""Browser tests for specialist referral functionality."""
import re
import pytest
from playwright.sync_api import Page, expect


@pytest.mark.browser
class TestReferralAdmin:
    """Test referral admin."""

    def test_referral_admin_loads(
        self, admin_page: Page, live_server
    ):
        """Referral admin list is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/referrals/referral/")
        expect(page.locator('h1')).to_contain_text('referral', ignore_case=True)

    def test_add_referral_form(
        self, admin_page: Page, live_server
    ):
        """Add referral form is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/referrals/referral/add/")
        expect(page.locator('body')).to_be_visible()


@pytest.mark.browser
class TestSpecialistAdmin:
    """Test specialist directory admin."""

    def test_specialist_admin_loads(
        self, admin_page: Page, live_server
    ):
        """Specialist admin list is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/referrals/specialist/")
        expect(page.locator('h1')).to_contain_text('specialist', ignore_case=True)

    def test_add_specialist_form(
        self, admin_page: Page, live_server
    ):
        """Add specialist form is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/referrals/specialist/add/")
        expect(page.locator('input[name="name"]')).to_be_visible()


@pytest.mark.browser
class TestReferralDocumentAdmin:
    """Test referral document admin."""

    def test_document_admin_loads(
        self, admin_page: Page, live_server
    ):
        """Referral document admin list is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/referrals/referraldocument/")
        expect(page.locator('h1')).to_contain_text('document', ignore_case=True)

    def test_add_document_form(
        self, admin_page: Page, live_server
    ):
        """Add referral document form is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/referrals/referraldocument/add/")
        expect(page.locator('body')).to_be_visible()


@pytest.mark.browser
class TestVisitingAppointmentAdmin:
    """Test visiting appointment admin."""

    def test_visiting_appointment_admin_loads(
        self, admin_page: Page, live_server
    ):
        """Visiting appointment admin list is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/referrals/visitingappointment/")
        expect(page.locator('h1')).to_contain_text('appointment', ignore_case=True)

    def test_add_visiting_appointment_form(
        self, admin_page: Page, live_server
    ):
        """Add visiting appointment form is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/referrals/visitingappointment/add/")
        expect(page.locator('body')).to_be_visible()


# =============================================================================
# STAFF INTERFACE TESTS
# =============================================================================


@pytest.fixture
def referrals_setup(db, owner_user):
    """Set up referral network data for tests."""
    from datetime import date, timedelta, time as time_obj
    from apps.referrals.models import Specialist, VisitingSchedule, Referral
    from apps.pets.models import Pet

    # Create a pet for referrals
    pet = Pet.objects.create(
        owner=owner_user,
        name='Referido',
        species='dog',
        breed='German Shepherd',
        gender='male',
        date_of_birth=date.today() - timedelta(days=730),
    )

    # Create specialists
    oncologist = Specialist.objects.create(
        name='Dr. Martinez - Oncology',
        specialty='oncology',
        phone='555-0200',
        email='martinez@vetspecialists.com',
        address='Av. Reforma 500',
        city='Mexico City',
        is_active=True,
        relationship_status='active',
    )

    visiting_specialist = Specialist.objects.create(
        name='Dr. Lopez - Cardiology',
        specialty='cardiology',
        phone='555-0300',
        email='lopez@vetcardio.com',
        address='Av. Insurgentes 1000',
        city='Mexico City',
        is_visiting=True,
        is_active=True,
        relationship_status='active',
    )

    # Create visiting schedule
    schedule = VisitingSchedule.objects.create(
        specialist=visiting_specialist,
        date=date.today() + timedelta(days=3),
        start_time=time_obj(9, 0),
        end_time=time_obj(17, 0),
        max_appointments=8,
        status='confirmed',
    )

    # Create referral
    referral = Referral.objects.create(
        direction='outbound',
        pet=pet,
        owner=owner_user,
        specialist=oncologist,
        reason='Suspicious mass on spleen, needs ultrasound and possible biopsy',
        urgency='urgent',
        status='sent',
    )

    return {
        'pet': pet,
        'oncologist': oncologist,
        'visiting_specialist': visiting_specialist,
        'schedule': schedule,
        'referral': referral,
    }


@pytest.mark.browser
class TestReferralsStaffPages:
    """Test referrals staff interface pages."""

    def test_staff_required_for_referrals(
        self, page: Page, live_server
    ):
        """Referrals pages require staff authentication."""
        page.goto(f"{live_server.url}/referrals/")
        expect(page).to_have_url(re.compile(r'.*(login|admin).*'))

    def test_dashboard_loads(
        self, staff_page: Page, live_server, referrals_setup
    ):
        """Referrals dashboard loads for staff."""
        page = staff_page
        page.goto(f"{live_server.url}/referrals/")
        expect(page.locator('h1')).to_contain_text('Referral', ignore_case=True)

    def test_specialist_list_page(
        self, staff_page: Page, live_server, referrals_setup
    ):
        """Specialist list shows specialists."""
        page = staff_page
        page.goto(f"{live_server.url}/referrals/specialists/")
        expect(page.locator('h1')).to_contain_text('Specialist', ignore_case=True)
        expect(page.locator('body')).to_contain_text('Martinez')

    def test_specialist_detail_page(
        self, staff_page: Page, live_server, referrals_setup
    ):
        """Specialist detail page shows specialist info."""
        page = staff_page
        specialist_id = referrals_setup['oncologist'].pk
        page.goto(f"{live_server.url}/referrals/specialists/{specialist_id}/")
        expect(page.locator('body')).to_contain_text('Martinez')
        expect(page.locator('body')).to_contain_text('Oncology')

    def test_referral_list_page(
        self, staff_page: Page, live_server, referrals_setup
    ):
        """Referral list shows referrals."""
        page = staff_page
        page.goto(f"{live_server.url}/referrals/outbound/")
        expect(page.locator('h1')).to_contain_text('Referral', ignore_case=True)
        expect(page.locator('body')).to_contain_text('Referido')

    def test_referral_detail_page(
        self, staff_page: Page, live_server, referrals_setup
    ):
        """Referral detail page shows referral info."""
        page = staff_page
        referral_id = referrals_setup['referral'].pk
        page.goto(f"{live_server.url}/referrals/outbound/{referral_id}/")
        expect(page.locator('body')).to_contain_text('Referido')
        expect(page.locator('body')).to_contain_text('mass on spleen')

    def test_visiting_schedule_page(
        self, staff_page: Page, live_server, referrals_setup
    ):
        """Visiting schedule page shows schedules."""
        page = staff_page
        page.goto(f"{live_server.url}/referrals/visiting/")
        expect(page.locator('h1')).to_contain_text('Visiting', ignore_case=True)
        expect(page.locator('body')).to_contain_text('Lopez')

    def test_visiting_detail_page(
        self, staff_page: Page, live_server, referrals_setup
    ):
        """Visiting detail page shows schedule info."""
        page = staff_page
        schedule_id = referrals_setup['schedule'].pk
        page.goto(f"{live_server.url}/referrals/visiting/{schedule_id}/")
        expect(page.locator('body')).to_contain_text('Lopez')
        expect(page.locator('body')).to_contain_text('Cardiology')
