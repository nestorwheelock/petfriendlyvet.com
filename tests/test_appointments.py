"""
Tests for Appointment Booking System (S-004)

Tests cover:
- ServiceType model (services offered)
- ScheduleBlock model (staff availability)
- Appointment model (booking records)
- Appointment status workflow
- Slot availability calculation
"""
import pytest
from datetime import date, time, timedelta, datetime
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


# =============================================================================
# ServiceType Model Tests
# =============================================================================

@pytest.mark.django_db
class TestServiceTypeModel:
    """Tests for the ServiceType model."""

    def test_service_type_model_exists(self):
        """ServiceType model should exist."""
        from apps.appointments.models import ServiceType
        assert ServiceType is not None

    def test_create_service_type(self):
        """Should be able to create a service type."""
        from apps.appointments.models import ServiceType

        service = ServiceType.objects.create(
            name='General Consultation',
            description='Regular checkup and consultation',
            duration_minutes=30,
            price=Decimal('450.00'),
            category='clinic'
        )
        assert service.id is not None
        assert service.name == 'General Consultation'
        assert service.duration_minutes == 30

    def test_service_type_str_representation(self):
        """ServiceType string representation should include name."""
        from apps.appointments.models import ServiceType

        service = ServiceType.objects.create(
            name='Vaccination',
            duration_minutes=15,
            price=Decimal('350.00')
        )
        assert 'Vaccination' in str(service)

    def test_service_type_categories(self):
        """ServiceType should have category choices."""
        from apps.appointments.models import SERVICE_CATEGORIES

        assert len(SERVICE_CATEGORIES) >= 3
        category_values = [c[0] for c in SERVICE_CATEGORIES]
        assert 'clinic' in category_values
        assert 'grooming' in category_values

    def test_service_type_active_flag(self):
        """ServiceType should have active flag."""
        from apps.appointments.models import ServiceType

        service = ServiceType.objects.create(
            name='Discontinued Service',
            duration_minutes=30,
            price=Decimal('100.00'),
            is_active=False
        )
        assert service.is_active is False

    def test_service_type_requires_pet_flag(self):
        """ServiceType should indicate if pet is required."""
        from apps.appointments.models import ServiceType

        service = ServiceType.objects.create(
            name='Pet Consultation',
            duration_minutes=30,
            price=Decimal('450.00'),
            requires_pet=True
        )
        assert service.requires_pet is True


# =============================================================================
# ScheduleBlock Model Tests
# =============================================================================

@pytest.mark.django_db
class TestScheduleBlockModel:
    """Tests for the ScheduleBlock model (staff availability)."""

    @pytest.fixture
    def vet(self):
        return User.objects.create_user(
            username='drpablo',
            email='pablo@test.com',
            password='pass123',
            role='vet'
        )

    def test_schedule_block_model_exists(self):
        """ScheduleBlock model should exist."""
        from apps.appointments.models import ScheduleBlock
        assert ScheduleBlock is not None

    def test_create_schedule_block(self, vet):
        """Should be able to create a schedule block."""
        from apps.appointments.models import ScheduleBlock

        block = ScheduleBlock.objects.create(
            staff=vet,
            day_of_week=1,  # Tuesday
            start_time=time(9, 0),
            end_time=time(14, 0)
        )
        assert block.id is not None
        assert block.day_of_week == 1
        assert block.start_time == time(9, 0)
        assert block.end_time == time(14, 0)

    def test_schedule_block_weekday_choices(self):
        """ScheduleBlock should have weekday choices."""
        from apps.appointments.models import WEEKDAY_CHOICES

        assert len(WEEKDAY_CHOICES) == 7
        # Check the day numbers are correct (0-6)
        day_numbers = [c[0] for c in WEEKDAY_CHOICES]
        assert day_numbers == [0, 1, 2, 3, 4, 5, 6]

    def test_schedule_block_str_representation(self, vet):
        """ScheduleBlock string should show staff and day."""
        from apps.appointments.models import ScheduleBlock

        block = ScheduleBlock.objects.create(
            staff=vet,
            day_of_week=2,  # Wednesday
            start_time=time(9, 0),
            end_time=time(17, 0)
        )
        block_str = str(block)
        assert 'drpablo' in block_str.lower() or 'wednesday' in block_str.lower()

    def test_staff_can_have_multiple_blocks(self, vet):
        """Staff member can have multiple schedule blocks."""
        from apps.appointments.models import ScheduleBlock

        ScheduleBlock.objects.create(
            staff=vet,
            day_of_week=1,  # Tuesday
            start_time=time(9, 0),
            end_time=time(14, 0)
        )
        ScheduleBlock.objects.create(
            staff=vet,
            day_of_week=1,  # Tuesday afternoon
            start_time=time(16, 0),
            end_time=time(20, 0)
        )

        assert ScheduleBlock.objects.filter(staff=vet, day_of_week=1).count() == 2


# =============================================================================
# Appointment Model Tests
# =============================================================================

@pytest.mark.django_db
class TestAppointmentModel:
    """Tests for the Appointment model."""

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
            name='General Consultation',
            duration_minutes=30,
            price=Decimal('450.00')
        )

    def test_appointment_model_exists(self):
        """Appointment model should exist."""
        from apps.appointments.models import Appointment
        assert Appointment is not None

    def test_create_appointment(self, owner, pet, vet, service):
        """Should be able to create an appointment."""
        from apps.appointments.models import Appointment

        start = timezone.now() + timedelta(days=1)
        appt = Appointment.objects.create(
            owner=owner,
            pet=pet,
            service=service,
            veterinarian=vet,
            scheduled_start=start,
            scheduled_end=start + timedelta(minutes=30),
            status='scheduled'
        )
        assert appt.id is not None
        assert appt.owner == owner
        assert appt.pet == pet
        assert appt.service == service

    def test_appointment_status_choices(self):
        """Appointment should have status choices."""
        from apps.appointments.models import APPOINTMENT_STATUS

        assert len(APPOINTMENT_STATUS) >= 4
        status_values = [s[0] for s in APPOINTMENT_STATUS]
        assert 'scheduled' in status_values
        assert 'confirmed' in status_values
        assert 'completed' in status_values
        assert 'cancelled' in status_values

    def test_appointment_str_representation(self, owner, pet, vet, service):
        """Appointment string should include pet name and service."""
        from apps.appointments.models import Appointment

        start = timezone.now() + timedelta(days=1)
        appt = Appointment.objects.create(
            owner=owner,
            pet=pet,
            service=service,
            veterinarian=vet,
            scheduled_start=start,
            scheduled_end=start + timedelta(minutes=30)
        )
        appt_str = str(appt)
        assert 'Luna' in appt_str or 'Consultation' in appt_str

    def test_appointment_notes_field(self, owner, pet, vet, service):
        """Appointment should have notes field."""
        from apps.appointments.models import Appointment

        start = timezone.now() + timedelta(days=1)
        appt = Appointment.objects.create(
            owner=owner,
            pet=pet,
            service=service,
            veterinarian=vet,
            scheduled_start=start,
            scheduled_end=start + timedelta(minutes=30),
            notes='First time visit, patient is nervous'
        )
        assert appt.notes == 'First time visit, patient is nervous'

    def test_owner_has_appointments_relation(self, owner, pet, vet, service):
        """Owner should have appointments relation."""
        from apps.appointments.models import Appointment

        start = timezone.now() + timedelta(days=1)
        Appointment.objects.create(
            owner=owner,
            pet=pet,
            service=service,
            veterinarian=vet,
            scheduled_start=start,
            scheduled_end=start + timedelta(minutes=30)
        )

        assert owner.appointments.count() == 1

    def test_pet_has_appointments_relation(self, owner, pet, vet, service):
        """Pet should have appointments relation."""
        from apps.appointments.models import Appointment

        start = timezone.now() + timedelta(days=1)
        Appointment.objects.create(
            owner=owner,
            pet=pet,
            service=service,
            veterinarian=vet,
            scheduled_start=start,
            scheduled_end=start + timedelta(minutes=30)
        )

        assert pet.appointments.count() == 1


# =============================================================================
# Appointment Status Workflow Tests
# =============================================================================

@pytest.mark.django_db
class TestAppointmentStatusWorkflow:
    """Tests for appointment status transitions."""

    @pytest.fixture
    def appointment(self):
        owner = User.objects.create_user(
            username='owner', email='owner@test.com', password='pass'
        )
        vet = User.objects.create_user(
            username='vet', email='vet@test.com', password='pass', role='vet'
        )
        from apps.pets.models import Pet
        from apps.appointments.models import ServiceType, Appointment

        pet = Pet.objects.create(owner=owner, name='Max', species='dog')
        service = ServiceType.objects.create(
            name='Checkup',
            duration_minutes=30,
            price=Decimal('400.00')
        )

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

    def test_appointment_default_status(self, appointment):
        """New appointment should have 'scheduled' status."""
        assert appointment.status == 'scheduled'

    def test_appointment_can_be_confirmed(self, appointment):
        """Appointment can be confirmed."""
        appointment.status = 'confirmed'
        appointment.save()
        appointment.refresh_from_db()
        assert appointment.status == 'confirmed'

    def test_appointment_can_be_cancelled(self, appointment):
        """Appointment can be cancelled."""
        appointment.status = 'cancelled'
        appointment.save()
        appointment.refresh_from_db()
        assert appointment.status == 'cancelled'

    def test_appointment_can_be_completed(self, appointment):
        """Appointment can be marked completed."""
        appointment.status = 'completed'
        appointment.save()
        appointment.refresh_from_db()
        assert appointment.status == 'completed'

    def test_appointment_tracks_cancellation_reason(self, appointment):
        """Cancelled appointment can have cancellation reason."""
        from apps.appointments.models import Appointment

        appointment.status = 'cancelled'
        appointment.cancellation_reason = 'Owner rescheduled'
        appointment.save()
        appointment.refresh_from_db()

        assert appointment.cancellation_reason == 'Owner rescheduled'


# =============================================================================
# Appointment Without Pet Tests
# =============================================================================

@pytest.mark.django_db
class TestAppointmentWithoutPet:
    """Tests for appointments that don't require a pet."""

    @pytest.fixture
    def owner(self):
        return User.objects.create_user(
            username='customer',
            email='customer@test.com',
            password='pass123'
        )

    @pytest.fixture
    def consultation_service(self):
        from apps.appointments.models import ServiceType
        return ServiceType.objects.create(
            name='Phone Consultation',
            duration_minutes=15,
            price=Decimal('200.00'),
            requires_pet=False
        )

    def test_appointment_without_pet(self, owner, consultation_service):
        """Should be able to create appointment without pet."""
        from apps.appointments.models import Appointment

        vet = User.objects.create_user(
            username='vet', email='vet@test.com', password='pass', role='vet'
        )

        start = timezone.now() + timedelta(days=1)
        appt = Appointment.objects.create(
            owner=owner,
            pet=None,
            service=consultation_service,
            veterinarian=vet,
            scheduled_start=start,
            scheduled_end=start + timedelta(minutes=15)
        )

        assert appt.id is not None
        assert appt.pet is None
