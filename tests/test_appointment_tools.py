"""
Tests for Appointment AI Tools (S-004)

Tests cover:
- list_services tool
- check_availability tool
- book_appointment tool
- list_user_appointments tool
- cancel_appointment tool
"""
import pytest
from datetime import date, time, timedelta, datetime
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


# =============================================================================
# List Services Tool Tests
# =============================================================================

@pytest.mark.django_db
class TestListServicesTool:
    """Tests for the list_services AI tool."""

    def test_list_services_tool_exists(self):
        """list_services tool should be registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tools = ToolRegistry.get_tools()
        tool_names = [t.name for t in tools]
        assert 'list_services' in tool_names

    def test_list_services_returns_active_services(self):
        """Should return only active services."""
        from apps.appointments.models import ServiceType
        from apps.ai_assistant.tools import list_services

        ServiceType.objects.create(
            name='Active Service',
            duration_minutes=30,
            price=Decimal('450.00'),
            is_active=True
        )
        ServiceType.objects.create(
            name='Inactive Service',
            duration_minutes=30,
            price=Decimal('300.00'),
            is_active=False
        )

        result = list_services()

        assert 'services' in result
        service_names = [s['name'] for s in result['services']]
        assert 'Active Service' in service_names
        assert 'Inactive Service' not in service_names

    def test_list_services_by_category(self):
        """Should filter services by category."""
        from apps.appointments.models import ServiceType
        from apps.ai_assistant.tools import list_services

        ServiceType.objects.create(
            name='Clinic Service',
            duration_minutes=30,
            price=Decimal('450.00'),
            category='clinic'
        )
        ServiceType.objects.create(
            name='Grooming Service',
            duration_minutes=60,
            price=Decimal('350.00'),
            category='grooming'
        )

        result = list_services(category='clinic')

        service_names = [s['name'] for s in result['services']]
        assert 'Clinic Service' in service_names
        assert 'Grooming Service' not in service_names

    def test_list_services_includes_price_and_duration(self):
        """Should include price and duration in response."""
        from apps.appointments.models import ServiceType
        from apps.ai_assistant.tools import list_services

        ServiceType.objects.create(
            name='Consultation',
            duration_minutes=30,
            price=Decimal('450.00'),
            description='General checkup'
        )

        result = list_services()

        service = result['services'][0]
        assert 'id' in service
        assert 'name' in service
        assert 'duration_minutes' in service
        assert 'price' in service
        assert service['duration_minutes'] == 30


# =============================================================================
# Check Availability Tool Tests
# =============================================================================

@pytest.mark.django_db
class TestCheckAvailabilityTool:
    """Tests for the check_availability AI tool."""

    @pytest.fixture
    def vet(self):
        return User.objects.create_user(
            username='drpablo',
            email='pablo@test.com',
            password='pass123',
            role='vet'
        )

    @pytest.fixture
    def service(self):
        from apps.appointments.models import ServiceType
        return ServiceType.objects.create(
            name='Consultation',
            duration_minutes=30,
            price=Decimal('450.00')
        )

    @pytest.fixture
    def schedule_block(self, vet):
        from apps.appointments.models import ScheduleBlock
        return ScheduleBlock.objects.create(
            staff=vet,
            day_of_week=1,  # Tuesday
            start_time=time(9, 0),
            end_time=time(14, 0)
        )

    def test_check_availability_tool_exists(self):
        """check_availability tool should be registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tools = ToolRegistry.get_tools()
        tool_names = [t.name for t in tools]
        assert 'check_availability' in tool_names

    def test_check_availability_returns_slots(self, vet, service, schedule_block):
        """Should return available time slots."""
        from apps.ai_assistant.tools import check_availability

        today = date.today()
        days_until_tuesday = (1 - today.weekday()) % 7
        if days_until_tuesday == 0:
            days_until_tuesday = 7
        next_tuesday = today + timedelta(days=days_until_tuesday)

        result = check_availability(
            service_id=service.id,
            date=next_tuesday.isoformat()
        )

        assert 'date' in result
        assert 'slots' in result
        assert len(result['slots']) > 0

    def test_check_availability_with_staff_filter(self, vet, service, schedule_block):
        """Should filter by specific staff member."""
        from apps.ai_assistant.tools import check_availability

        today = date.today()
        days_until_tuesday = (1 - today.weekday()) % 7
        if days_until_tuesday == 0:
            days_until_tuesday = 7
        next_tuesday = today + timedelta(days=days_until_tuesday)

        result = check_availability(
            service_id=service.id,
            date=next_tuesday.isoformat(),
            staff_id=vet.id
        )

        assert len(result['slots']) > 0
        for slot in result['slots']:
            assert slot['staff_id'] == vet.id

    def test_check_availability_invalid_service(self):
        """Should return error for invalid service."""
        from apps.ai_assistant.tools import check_availability

        result = check_availability(
            service_id=99999,
            date=date.today().isoformat()
        )

        assert 'error' in result

    def test_check_availability_no_slots(self, vet, service):
        """Should return empty slots when no availability."""
        from apps.ai_assistant.tools import check_availability

        # No schedule block on Wednesday
        today = date.today()
        days_until_wednesday = (2 - today.weekday()) % 7
        if days_until_wednesday == 0:
            days_until_wednesday = 7
        next_wednesday = today + timedelta(days=days_until_wednesday)

        result = check_availability(
            service_id=service.id,
            date=next_wednesday.isoformat(),
            staff_id=vet.id
        )

        assert result['slots'] == []


# =============================================================================
# Book Appointment Tool Tests
# =============================================================================

@pytest.mark.django_db
class TestBookAppointmentTool:
    """Tests for the book_appointment AI tool."""

    @pytest.fixture
    def owner(self):
        return User.objects.create_user(
            username='petowner',
            email='owner@test.com',
            password='pass123',
            role='owner'
        )

    @pytest.fixture
    def vet(self):
        return User.objects.create_user(
            username='drpablo',
            email='pablo@test.com',
            password='pass123',
            role='vet'
        )

    @pytest.fixture
    def pet(self, owner):
        from apps.pets.models import Pet
        return Pet.objects.create(
            owner=owner,
            name='Luna',
            species='dog'
        )

    @pytest.fixture
    def service(self):
        from apps.appointments.models import ServiceType
        return ServiceType.objects.create(
            name='Consultation',
            duration_minutes=30,
            price=Decimal('450.00')
        )

    @pytest.fixture
    def schedule_block(self, vet):
        from apps.appointments.models import ScheduleBlock
        return ScheduleBlock.objects.create(
            staff=vet,
            day_of_week=1,  # Tuesday
            start_time=time(9, 0),
            end_time=time(14, 0)
        )

    def test_book_appointment_tool_exists(self):
        """book_appointment tool should be registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tools = ToolRegistry.get_tools()
        tool_names = [t.name for t in tools]
        assert 'book_appointment' in tool_names

    def test_book_appointment_creates_record(
        self, owner, pet, vet, service, schedule_block
    ):
        """Should create appointment and return confirmation."""
        from apps.ai_assistant.tools import book_appointment
        from apps.appointments.models import Appointment

        today = date.today()
        days_until_tuesday = (1 - today.weekday()) % 7
        if days_until_tuesday == 0:
            days_until_tuesday = 7
        next_tuesday = today + timedelta(days=days_until_tuesday)

        result = book_appointment(
            user_id=owner.id,
            pet_id=pet.id,
            service_id=service.id,
            staff_id=vet.id,
            date=next_tuesday.isoformat(),
            time='10:00'
        )

        assert 'appointment_id' in result
        assert 'confirmation' in result
        assert result['status'] == 'scheduled'

        # Verify record exists
        appt = Appointment.objects.get(id=result['appointment_id'])
        assert appt.owner == owner
        assert appt.pet == pet

    def test_book_appointment_requires_ownership(
        self, owner, vet, service, schedule_block
    ):
        """Cannot book with someone else's pet."""
        from apps.pets.models import Pet
        from apps.ai_assistant.tools import book_appointment

        other_owner = User.objects.create_user(
            username='other', email='other@test.com', password='pass'
        )
        other_pet = Pet.objects.create(
            owner=other_owner, name='Max', species='dog'
        )

        today = date.today()
        days_until_tuesday = (1 - today.weekday()) % 7
        if days_until_tuesday == 0:
            days_until_tuesday = 7
        next_tuesday = today + timedelta(days=days_until_tuesday)

        result = book_appointment(
            user_id=owner.id,
            pet_id=other_pet.id,  # Not owner's pet
            service_id=service.id,
            staff_id=vet.id,
            date=next_tuesday.isoformat(),
            time='10:00'
        )

        assert 'error' in result

    def test_book_appointment_slot_unavailable(
        self, owner, pet, vet, service, schedule_block
    ):
        """Should return error for unavailable slot."""
        from apps.ai_assistant.tools import book_appointment

        today = date.today()
        days_until_tuesday = (1 - today.weekday()) % 7
        if days_until_tuesday == 0:
            days_until_tuesday = 7
        next_tuesday = today + timedelta(days=days_until_tuesday)

        # Book first
        book_appointment(
            user_id=owner.id,
            pet_id=pet.id,
            service_id=service.id,
            staff_id=vet.id,
            date=next_tuesday.isoformat(),
            time='10:00'
        )

        # Try to book same slot
        from apps.pets.models import Pet
        pet2 = Pet.objects.create(owner=owner, name='Max', species='cat')

        result = book_appointment(
            user_id=owner.id,
            pet_id=pet2.id,
            service_id=service.id,
            staff_id=vet.id,
            date=next_tuesday.isoformat(),
            time='10:00'
        )

        assert 'error' in result

    def test_book_appointment_with_notes(
        self, owner, pet, vet, service, schedule_block
    ):
        """Should store notes with appointment."""
        from apps.ai_assistant.tools import book_appointment
        from apps.appointments.models import Appointment

        today = date.today()
        days_until_tuesday = (1 - today.weekday()) % 7
        if days_until_tuesday == 0:
            days_until_tuesday = 7
        next_tuesday = today + timedelta(days=days_until_tuesday)

        result = book_appointment(
            user_id=owner.id,
            pet_id=pet.id,
            service_id=service.id,
            staff_id=vet.id,
            date=next_tuesday.isoformat(),
            time='10:00',
            notes='First time visit, nervous dog'
        )

        appt = Appointment.objects.get(id=result['appointment_id'])
        assert appt.notes == 'First time visit, nervous dog'


# =============================================================================
# List User Appointments Tool Tests
# =============================================================================

@pytest.mark.django_db
class TestListUserAppointmentsTool:
    """Tests for the list_user_appointments AI tool."""

    @pytest.fixture
    def owner(self):
        return User.objects.create_user(
            username='petowner',
            email='owner@test.com',
            password='pass123',
            role='owner'
        )

    @pytest.fixture
    def vet(self):
        return User.objects.create_user(
            username='drpablo',
            email='pablo@test.com',
            password='pass123',
            role='vet'
        )

    @pytest.fixture
    def pet(self, owner):
        from apps.pets.models import Pet
        return Pet.objects.create(
            owner=owner,
            name='Luna',
            species='dog'
        )

    @pytest.fixture
    def service(self):
        from apps.appointments.models import ServiceType
        return ServiceType.objects.create(
            name='Consultation',
            duration_minutes=30,
            price=Decimal('450.00')
        )

    def test_list_user_appointments_tool_exists(self):
        """list_user_appointments tool should be registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tools = ToolRegistry.get_tools()
        tool_names = [t.name for t in tools]
        assert 'list_user_appointments' in tool_names

    def test_list_user_appointments_returns_list(
        self, owner, pet, vet, service
    ):
        """Should return list of user's appointments."""
        from apps.appointments.models import Appointment
        from apps.ai_assistant.tools import list_user_appointments

        start = timezone.now() + timedelta(days=1)
        Appointment.objects.create(
            owner=owner,
            pet=pet,
            service=service,
            veterinarian=vet,
            scheduled_start=start,
            scheduled_end=start + timedelta(minutes=30),
            status='scheduled'
        )

        result = list_user_appointments(user_id=owner.id)

        assert 'appointments' in result
        assert len(result['appointments']) == 1

    def test_list_appointments_includes_details(
        self, owner, pet, vet, service
    ):
        """Should include appointment details."""
        from apps.appointments.models import Appointment
        from apps.ai_assistant.tools import list_user_appointments

        start = timezone.now() + timedelta(days=1)
        Appointment.objects.create(
            owner=owner,
            pet=pet,
            service=service,
            veterinarian=vet,
            scheduled_start=start,
            scheduled_end=start + timedelta(minutes=30),
            status='scheduled'
        )

        result = list_user_appointments(user_id=owner.id)

        appt = result['appointments'][0]
        assert 'id' in appt
        assert 'pet_name' in appt
        assert 'service_name' in appt
        assert 'scheduled_start' in appt
        assert 'status' in appt

    def test_list_appointments_filter_by_status(
        self, owner, pet, vet, service
    ):
        """Should filter by status if provided."""
        from apps.appointments.models import Appointment
        from apps.ai_assistant.tools import list_user_appointments

        start = timezone.now() + timedelta(days=1)
        Appointment.objects.create(
            owner=owner,
            pet=pet,
            service=service,
            veterinarian=vet,
            scheduled_start=start,
            scheduled_end=start + timedelta(minutes=30),
            status='scheduled'
        )
        Appointment.objects.create(
            owner=owner,
            pet=pet,
            service=service,
            veterinarian=vet,
            scheduled_start=start + timedelta(days=1),
            scheduled_end=start + timedelta(days=1, minutes=30),
            status='completed'
        )

        result = list_user_appointments(
            user_id=owner.id,
            status='scheduled'
        )

        assert len(result['appointments']) == 1
        assert result['appointments'][0]['status'] == 'scheduled'

    def test_list_appointments_upcoming_only(
        self, owner, pet, vet, service
    ):
        """Should optionally show only upcoming appointments."""
        from apps.appointments.models import Appointment
        from apps.ai_assistant.tools import list_user_appointments

        # Past appointment
        past = timezone.now() - timedelta(days=7)
        Appointment.objects.create(
            owner=owner,
            pet=pet,
            service=service,
            veterinarian=vet,
            scheduled_start=past,
            scheduled_end=past + timedelta(minutes=30),
            status='completed'
        )
        # Future appointment
        future = timezone.now() + timedelta(days=7)
        Appointment.objects.create(
            owner=owner,
            pet=pet,
            service=service,
            veterinarian=vet,
            scheduled_start=future,
            scheduled_end=future + timedelta(minutes=30),
            status='scheduled'
        )

        result = list_user_appointments(
            user_id=owner.id,
            upcoming_only=True
        )

        assert len(result['appointments']) == 1


# =============================================================================
# Cancel Appointment Tool Tests
# =============================================================================

@pytest.mark.django_db
class TestCancelAppointmentTool:
    """Tests for the cancel_appointment AI tool."""

    @pytest.fixture
    def owner(self):
        return User.objects.create_user(
            username='petowner',
            email='owner@test.com',
            password='pass123',
            role='owner'
        )

    @pytest.fixture
    def vet(self):
        return User.objects.create_user(
            username='drpablo',
            email='pablo@test.com',
            password='pass123',
            role='vet'
        )

    @pytest.fixture
    def pet(self, owner):
        from apps.pets.models import Pet
        return Pet.objects.create(
            owner=owner,
            name='Luna',
            species='dog'
        )

    @pytest.fixture
    def service(self):
        from apps.appointments.models import ServiceType
        return ServiceType.objects.create(
            name='Consultation',
            duration_minutes=30,
            price=Decimal('450.00')
        )

    @pytest.fixture
    def appointment(self, owner, pet, vet, service):
        from apps.appointments.models import Appointment
        start = timezone.now() + timedelta(days=1)
        return Appointment.objects.create(
            owner=owner,
            pet=pet,
            service=service,
            veterinarian=vet,
            scheduled_start=start,
            scheduled_end=start + timedelta(minutes=30),
            status='scheduled'
        )

    def test_cancel_appointment_tool_exists(self):
        """cancel_appointment tool should be registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tools = ToolRegistry.get_tools()
        tool_names = [t.name for t in tools]
        assert 'cancel_appointment' in tool_names

    def test_cancel_appointment_updates_status(
        self, owner, appointment
    ):
        """Should update appointment status to cancelled."""
        from apps.ai_assistant.tools import cancel_appointment
        from apps.appointments.models import Appointment

        result = cancel_appointment(
            user_id=owner.id,
            appointment_id=appointment.id,
            reason='Schedule conflict'
        )

        assert 'success' in result
        assert result['success'] is True

        appointment.refresh_from_db()
        assert appointment.status == 'cancelled'
        assert appointment.cancellation_reason == 'Schedule conflict'

    def test_cancel_appointment_requires_ownership(
        self, appointment
    ):
        """Cannot cancel someone else's appointment."""
        from apps.ai_assistant.tools import cancel_appointment

        other_user = User.objects.create_user(
            username='other', email='other@test.com', password='pass'
        )

        result = cancel_appointment(
            user_id=other_user.id,
            appointment_id=appointment.id,
            reason='Testing'
        )

        assert 'error' in result

    def test_cancel_completed_appointment_fails(
        self, owner, appointment
    ):
        """Cannot cancel completed appointments."""
        from apps.ai_assistant.tools import cancel_appointment

        appointment.status = 'completed'
        appointment.save()

        result = cancel_appointment(
            user_id=owner.id,
            appointment_id=appointment.id,
            reason='Changed mind'
        )

        assert 'error' in result

    def test_cancel_sets_cancelled_at(
        self, owner, appointment
    ):
        """Should set cancelled_at timestamp."""
        from apps.ai_assistant.tools import cancel_appointment

        result = cancel_appointment(
            user_id=owner.id,
            appointment_id=appointment.id,
            reason='Rescheduling'
        )

        appointment.refresh_from_db()
        assert appointment.cancelled_at is not None
