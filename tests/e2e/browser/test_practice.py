"""Browser tests for practice management functionality."""
import re
import pytest
from playwright.sync_api import Page, expect


@pytest.fixture
def practice_setup(db, staff_schedule_setup):
    """Set up practice data for tests."""
    from datetime import date, timedelta, time as time_obj
    from django.utils import timezone
    from apps.practice.models import (
        StaffProfile, Shift, TimeEntry, Task, ClinicSettings
    )
    from django.contrib.auth import get_user_model

    User = get_user_model()
    profile = staff_schedule_setup['profile']

    # Create a task
    task = Task.objects.create(
        title='Follow up with Mrs. Garcia',
        description='Call about lab results',
        assigned_to=profile,
        priority='high',
        status='pending',
        due_date=timezone.now() + timedelta(days=1),
    )

    # Create time entry
    time_entry = TimeEntry.objects.create(
        staff=profile,
        clock_in=timezone.now() - timedelta(hours=2),
        clock_out=timezone.now(),
    )

    # Create clinic settings
    settings = ClinicSettings.objects.create(
        name='PetFriendly Vet Clinic',
        legal_name='PetFriendly Veterinary Services, S.A. de C.V.',
        address='Av. Insurgentes Sur 1234\nCol. Del Valle\nMexico City, CDMX 03100',
        phone='555-123-4567',
        email='info@petfriendlyvet.com',
        opening_time=time_obj(8, 0),
        closing_time=time_obj(20, 0),
        emergency_phone='555-EMERGENCY',
        emergency_available=True,
    )

    return {
        'profile': profile,
        'shift': staff_schedule_setup['shift'],
        'task': task,
        'time_entry': time_entry,
        'settings': settings,
    }


@pytest.mark.browser
class TestPracticeStaffPages:
    """Test practice staff interface pages."""

    def test_staff_required_for_practice(
        self, page: Page, live_server
    ):
        """Practice pages require staff authentication."""
        page.goto(f"{live_server.url}/practice/")
        expect(page).to_have_url(re.compile(r'.*(login|admin).*'))

    def test_dashboard_loads(
        self, staff_page: Page, live_server, practice_setup
    ):
        """Practice dashboard loads for staff."""
        page = staff_page
        page.goto(f"{live_server.url}/practice/")
        expect(page.locator('h1')).to_contain_text('Practice', ignore_case=True)

    def test_staff_list_page(
        self, staff_page: Page, live_server, practice_setup
    ):
        """Staff list page shows staff members."""
        page = staff_page
        page.goto(f"{live_server.url}/practice/staff/")
        expect(page.locator('h1')).to_contain_text('Staff', ignore_case=True)

    def test_staff_detail_page(
        self, staff_page: Page, live_server, practice_setup
    ):
        """Staff detail page shows staff info."""
        page = staff_page
        profile_id = practice_setup['profile'].pk
        page.goto(f"{live_server.url}/practice/staff/{profile_id}/")
        expect(page.locator('body')).to_be_visible()

    def test_schedule_page(
        self, staff_page: Page, live_server, practice_setup
    ):
        """Weekly schedule page loads."""
        page = staff_page
        page.goto(f"{live_server.url}/practice/schedule/")
        expect(page.locator('h1')).to_contain_text('Schedule', ignore_case=True)

    def test_shift_list_page(
        self, staff_page: Page, live_server, practice_setup
    ):
        """Shifts list page loads."""
        page = staff_page
        page.goto(f"{live_server.url}/practice/shifts/")
        expect(page.locator('h1')).to_contain_text('Shift', ignore_case=True)

    def test_time_tracking_page(
        self, staff_page: Page, live_server, practice_setup
    ):
        """Time tracking page loads."""
        page = staff_page
        page.goto(f"{live_server.url}/practice/time/")
        expect(page.locator('h1')).to_contain_text('Time', ignore_case=True)

    def test_task_list_page(
        self, staff_page: Page, live_server, practice_setup
    ):
        """Task list page shows tasks."""
        page = staff_page
        page.goto(f"{live_server.url}/practice/tasks/")
        expect(page.locator('h1')).to_contain_text('Task', ignore_case=True)
        expect(page.locator('body')).to_contain_text('Mrs. Garcia')

    def test_task_detail_page(
        self, staff_page: Page, live_server, practice_setup
    ):
        """Task detail page shows task info."""
        page = staff_page
        task_id = practice_setup['task'].pk
        page.goto(f"{live_server.url}/practice/tasks/{task_id}/")
        expect(page.locator('body')).to_contain_text('Mrs. Garcia')
        expect(page.locator('body')).to_contain_text('lab results')

    def test_clinic_settings_page(
        self, staff_page: Page, live_server, practice_setup
    ):
        """Clinic settings page shows settings."""
        page = staff_page
        page.goto(f"{live_server.url}/practice/settings/")
        expect(page.locator('h1')).to_contain_text('Settings', ignore_case=True)
        expect(page.locator('body')).to_contain_text('PetFriendly Vet')
