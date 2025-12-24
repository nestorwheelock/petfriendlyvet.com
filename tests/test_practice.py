"""Tests for Practice Management app (TDD first)."""
import pytest
from datetime import time, date, timedelta
from django.utils import timezone

from apps.accounts.models import User

pytestmark = pytest.mark.django_db


class TestStaffProfileModel:
    """Tests for StaffProfile model."""

    def test_create_staff_profile(self, user):
        """Test creating a staff profile."""
        from apps.practice.models import StaffProfile

        staff = StaffProfile.objects.create(
            user=user,
            role='veterinarian',
            title='Lead Veterinarian',
        )

        assert staff.role == 'veterinarian'
        assert staff.can_prescribe is True  # Auto-set

    def test_auto_permissions(self, user):
        """Test auto-set permissions based on role."""
        from apps.practice.models import StaffProfile

        vet = StaffProfile.objects.create(user=user, role='veterinarian')
        assert vet.can_prescribe is True
        assert vet.can_dispense is True
        assert vet.can_handle_controlled is True


class TestShiftModel:
    """Tests for Shift model."""

    def test_create_shift(self, staff_profile):
        """Test creating a shift."""
        from apps.practice.models import Shift

        shift = Shift.objects.create(
            staff=staff_profile,
            date=date.today(),
            start_time=time(9, 0),
            end_time=time(17, 0),
        )

        assert shift.is_confirmed is False


class TestTimeEntryModel:
    """Tests for TimeEntry model."""

    def test_create_time_entry(self, staff_profile):
        """Test creating a time entry."""
        from apps.practice.models import TimeEntry

        entry = TimeEntry.objects.create(
            staff=staff_profile,
            clock_in=timezone.now(),
        )

        assert entry.clock_out is None
        assert entry.hours_worked == 0

    def test_hours_worked(self, staff_profile):
        """Test hours worked calculation."""
        from apps.practice.models import TimeEntry

        clock_in = timezone.now()
        clock_out = clock_in + timedelta(hours=8)

        entry = TimeEntry.objects.create(
            staff=staff_profile,
            clock_in=clock_in,
            clock_out=clock_out,
            break_minutes=30,
        )

        assert entry.hours_worked == 7.5


class TestClinicSettingsModel:
    """Tests for ClinicSettings model."""

    def test_create_settings(self):
        """Test creating clinic settings."""
        from apps.practice.models import ClinicSettings

        settings = ClinicSettings.objects.create(
            name='Pet Friendly',
            address='Puerto Morelos, Mexico',
            phone='+52 998 123 4567',
            email='info@petfriendly.com',
            opening_time=time(9, 0),
            closing_time=time(20, 0),
            days_open=['tue', 'wed', 'thu', 'fri', 'sat', 'sun'],
        )

        assert settings.name == 'Pet Friendly'


class TestClinicalNoteModel:
    """Tests for ClinicalNote model."""

    def test_create_soap_note(self, user, pet):
        """Test creating a SOAP note."""
        from apps.practice.models import ClinicalNote

        note = ClinicalNote.objects.create(
            pet=pet,
            author=user,
            note_type='soap',
            subjective='Owner reports lethargy',
            objective='T: 39.2C, HR: 100',
            assessment='Possible infection',
            plan='Start antibiotics',
        )

        assert note.note_type == 'soap'


class TestTaskModel:
    """Tests for Task model."""

    def test_create_task(self, user, staff_profile):
        """Test creating a task."""
        from apps.practice.models import Task

        task = Task.objects.create(
            title='Call patient owner',
            assigned_to=staff_profile,
            created_by=user,
            priority='high',
        )

        assert task.status == 'pending'
        assert task.priority == 'high'


class TestPracticeAITools:
    """Tests for Practice AI tools."""

    def test_get_staff_schedule_tool_exists(self):
        """Test get_staff_schedule tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('get_staff_schedule')
        assert tool is not None

    def test_get_staff_schedule(self, staff_profile):
        """Test getting staff schedule."""
        from apps.ai_assistant.tools import get_staff_schedule
        from apps.practice.models import Shift

        Shift.objects.create(
            staff=staff_profile,
            date=date.today(),
            start_time=time(9, 0),
            end_time=time(17, 0),
        )

        result = get_staff_schedule(date=date.today().isoformat())

        assert result['success'] is True

    def test_clock_in_tool_exists(self):
        """Test clock_in tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('clock_in')
        assert tool is not None

    def test_clock_in(self, staff_profile):
        """Test clocking in."""
        from apps.ai_assistant.tools import clock_in

        result = clock_in(staff_id=staff_profile.id)

        assert result['success'] is True
        assert 'time_entry_id' in result

    def test_create_clinical_note_tool_exists(self):
        """Test create_clinical_note tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('create_clinical_note')
        assert tool is not None

    def test_create_task_tool_exists(self):
        """Test create_task tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('create_staff_task')
        assert tool is not None

    def test_create_task(self, user, staff_profile):
        """Test creating a task."""
        from apps.ai_assistant.tools import create_staff_task

        result = create_staff_task(
            title='Follow up with patient',
            assigned_to_id=staff_profile.id,
            priority='high',
        )

        assert result['success'] is True
        assert 'task_id' in result


# Fixtures
@pytest.fixture
def user():
    """Create a test user."""
    return User.objects.create_user(
        username='practiceuser',
        email='practice@example.com',
        password='testpass123',
        first_name='Practice',
        last_name='User',
    )


@pytest.fixture
def staff_profile(user):
    """Create a staff profile."""
    from apps.practice.models import StaffProfile
    return StaffProfile.objects.create(
        user=user,
        role='veterinarian',
    )


@pytest.fixture
def pet(user):
    """Create a test pet."""
    from apps.pets.models import Pet
    return Pet.objects.create(
        name='TestPet',
        owner=user,
        species='dog',
        breed='Labrador',
    )
