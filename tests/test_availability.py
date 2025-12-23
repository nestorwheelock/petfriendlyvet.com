"""
Tests for Appointment Availability Service (S-004)

Tests cover:
- Available slot calculation
- Conflict detection (double-booking prevention)
- Staff schedule block integration
- Appointment booking logic
"""
import pytest
from datetime import date, time, timedelta, datetime
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


# =============================================================================
# Available Slots Calculation Tests
# =============================================================================

@pytest.mark.django_db
class TestAvailableSlots:
    """Tests for calculating available appointment slots."""

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
            name='General Consultation',
            duration_minutes=30,
            price=Decimal('450.00')
        )

    @pytest.fixture
    def schedule_block(self, vet):
        from apps.appointments.models import ScheduleBlock
        # Tuesday 9am-2pm
        return ScheduleBlock.objects.create(
            staff=vet,
            day_of_week=1,  # Tuesday
            start_time=time(9, 0),
            end_time=time(14, 0)
        )

    def test_availability_service_exists(self):
        """AvailabilityService should exist."""
        from apps.appointments.services import AvailabilityService
        assert AvailabilityService is not None

    def test_get_available_slots_for_date(self, vet, service, schedule_block):
        """Should return available time slots for a date."""
        from apps.appointments.services import AvailabilityService

        # Find next Tuesday
        today = date.today()
        days_until_tuesday = (1 - today.weekday()) % 7
        if days_until_tuesday == 0:
            days_until_tuesday = 7
        next_tuesday = today + timedelta(days=days_until_tuesday)

        slots = AvailabilityService.get_available_slots(
            date=next_tuesday,
            service=service,
            staff=vet
        )

        assert isinstance(slots, list)
        assert len(slots) > 0

    def test_slots_match_service_duration(self, vet, service, schedule_block):
        """Slots should be spaced by service duration."""
        from apps.appointments.services import AvailabilityService

        today = date.today()
        days_until_tuesday = (1 - today.weekday()) % 7
        if days_until_tuesday == 0:
            days_until_tuesday = 7
        next_tuesday = today + timedelta(days=days_until_tuesday)

        slots = AvailabilityService.get_available_slots(
            date=next_tuesday,
            service=service,
            staff=vet
        )

        # With 30-minute service and 9am-2pm block, should have 10 slots
        # 9:00, 9:30, 10:00, 10:30, 11:00, 11:30, 12:00, 12:30, 13:00, 13:30
        assert len(slots) == 10

    def test_no_slots_outside_schedule(self, vet, service, schedule_block):
        """Should return empty list for days without schedule blocks."""
        from apps.appointments.services import AvailabilityService

        # Find next Wednesday (no schedule block)
        today = date.today()
        days_until_wednesday = (2 - today.weekday()) % 7
        if days_until_wednesday == 0:
            days_until_wednesday = 7
        next_wednesday = today + timedelta(days=days_until_wednesday)

        slots = AvailabilityService.get_available_slots(
            date=next_wednesday,
            service=service,
            staff=vet
        )

        assert slots == []

    def test_slots_exclude_booked_times(self, vet, service, schedule_block):
        """Booked appointments should not appear in available slots."""
        from apps.appointments.models import Appointment
        from apps.appointments.services import AvailabilityService

        today = date.today()
        days_until_tuesday = (1 - today.weekday()) % 7
        if days_until_tuesday == 0:
            days_until_tuesday = 7
        next_tuesday = today + timedelta(days=days_until_tuesday)

        owner = User.objects.create_user(
            username='owner', email='owner@test.com', password='pass'
        )

        # Book 10:00 slot
        start = timezone.make_aware(datetime.combine(next_tuesday, time(10, 0)))
        Appointment.objects.create(
            owner=owner,
            service=service,
            veterinarian=vet,
            scheduled_start=start,
            scheduled_end=start + timedelta(minutes=30),
            status='scheduled'
        )

        slots = AvailabilityService.get_available_slots(
            date=next_tuesday,
            service=service,
            staff=vet
        )

        # 10:00 should not be available
        slot_times = [s['time'] for s in slots]
        assert time(10, 0) not in slot_times

    def test_cancelled_appointments_free_up_slots(self, vet, service, schedule_block):
        """Cancelled appointments should not block slots."""
        from apps.appointments.models import Appointment
        from apps.appointments.services import AvailabilityService

        today = date.today()
        days_until_tuesday = (1 - today.weekday()) % 7
        if days_until_tuesday == 0:
            days_until_tuesday = 7
        next_tuesday = today + timedelta(days=days_until_tuesday)

        owner = User.objects.create_user(
            username='owner', email='owner@test.com', password='pass'
        )

        # Book then cancel 10:00 slot
        start = timezone.make_aware(datetime.combine(next_tuesday, time(10, 0)))
        Appointment.objects.create(
            owner=owner,
            service=service,
            veterinarian=vet,
            scheduled_start=start,
            scheduled_end=start + timedelta(minutes=30),
            status='cancelled'
        )

        slots = AvailabilityService.get_available_slots(
            date=next_tuesday,
            service=service,
            staff=vet
        )

        # 10:00 should still be available
        slot_times = [s['time'] for s in slots]
        assert time(10, 0) in slot_times


# =============================================================================
# Slot Availability Check Tests
# =============================================================================

@pytest.mark.django_db
class TestSlotAvailabilityCheck:
    """Tests for checking if a specific slot is available."""

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
            name='General Consultation',
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

    def test_is_slot_available_returns_bool(self, vet, service, schedule_block):
        """is_slot_available should return boolean."""
        from apps.appointments.services import AvailabilityService

        today = date.today()
        days_until_tuesday = (1 - today.weekday()) % 7
        if days_until_tuesday == 0:
            days_until_tuesday = 7
        next_tuesday = today + timedelta(days=days_until_tuesday)

        start = timezone.make_aware(datetime.combine(next_tuesday, time(10, 0)))

        result = AvailabilityService.is_slot_available(
            start_time=start,
            service=service,
            staff=vet
        )

        assert isinstance(result, bool)

    def test_available_slot_returns_true(self, vet, service, schedule_block):
        """Available slot should return True."""
        from apps.appointments.services import AvailabilityService

        today = date.today()
        days_until_tuesday = (1 - today.weekday()) % 7
        if days_until_tuesday == 0:
            days_until_tuesday = 7
        next_tuesday = today + timedelta(days=days_until_tuesday)

        start = timezone.make_aware(datetime.combine(next_tuesday, time(10, 0)))

        result = AvailabilityService.is_slot_available(
            start_time=start,
            service=service,
            staff=vet
        )

        assert result is True

    def test_booked_slot_returns_false(self, vet, service, schedule_block):
        """Booked slot should return False."""
        from apps.appointments.models import Appointment
        from apps.appointments.services import AvailabilityService

        today = date.today()
        days_until_tuesday = (1 - today.weekday()) % 7
        if days_until_tuesday == 0:
            days_until_tuesday = 7
        next_tuesday = today + timedelta(days=days_until_tuesday)

        owner = User.objects.create_user(
            username='owner', email='owner@test.com', password='pass'
        )

        start = timezone.make_aware(datetime.combine(next_tuesday, time(10, 0)))
        Appointment.objects.create(
            owner=owner,
            service=service,
            veterinarian=vet,
            scheduled_start=start,
            scheduled_end=start + timedelta(minutes=30),
            status='scheduled'
        )

        result = AvailabilityService.is_slot_available(
            start_time=start,
            service=service,
            staff=vet
        )

        assert result is False

    def test_outside_schedule_returns_false(self, vet, service, schedule_block):
        """Slot outside schedule block should return False."""
        from apps.appointments.services import AvailabilityService

        today = date.today()
        days_until_tuesday = (1 - today.weekday()) % 7
        if days_until_tuesday == 0:
            days_until_tuesday = 7
        next_tuesday = today + timedelta(days=days_until_tuesday)

        # 8:00 is before 9:00 start
        start = timezone.make_aware(datetime.combine(next_tuesday, time(8, 0)))

        result = AvailabilityService.is_slot_available(
            start_time=start,
            service=service,
            staff=vet
        )

        assert result is False

    def test_overlapping_appointment_returns_false(self, vet, service, schedule_block):
        """Overlapping appointment should block slot."""
        from apps.appointments.models import Appointment
        from apps.appointments.services import AvailabilityService

        today = date.today()
        days_until_tuesday = (1 - today.weekday()) % 7
        if days_until_tuesday == 0:
            days_until_tuesday = 7
        next_tuesday = today + timedelta(days=days_until_tuesday)

        owner = User.objects.create_user(
            username='owner', email='owner@test.com', password='pass'
        )

        # Book 10:00-10:30
        booked_start = timezone.make_aware(datetime.combine(next_tuesday, time(10, 0)))
        Appointment.objects.create(
            owner=owner,
            service=service,
            veterinarian=vet,
            scheduled_start=booked_start,
            scheduled_end=booked_start + timedelta(minutes=30),
            status='scheduled'
        )

        # Try to book 10:15 - overlaps with 10:00-10:30
        requested_start = timezone.make_aware(datetime.combine(next_tuesday, time(10, 15)))

        result = AvailabilityService.is_slot_available(
            start_time=requested_start,
            service=service,
            staff=vet
        )

        assert result is False


# =============================================================================
# Appointment Booking Tests
# =============================================================================

@pytest.mark.django_db
class TestAppointmentBooking:
    """Tests for booking appointments."""

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

    @pytest.fixture
    def schedule_block(self, vet):
        from apps.appointments.models import ScheduleBlock
        return ScheduleBlock.objects.create(
            staff=vet,
            day_of_week=1,  # Tuesday
            start_time=time(9, 0),
            end_time=time(14, 0)
        )

    def test_book_appointment_creates_record(
        self, owner, pet, vet, service, schedule_block
    ):
        """Booking should create appointment record."""
        from apps.appointments.models import Appointment
        from apps.appointments.services import AvailabilityService

        today = date.today()
        days_until_tuesday = (1 - today.weekday()) % 7
        if days_until_tuesday == 0:
            days_until_tuesday = 7
        next_tuesday = today + timedelta(days=days_until_tuesday)

        start = timezone.make_aware(datetime.combine(next_tuesday, time(10, 0)))

        appointment = AvailabilityService.book_appointment(
            owner=owner,
            pet=pet,
            service=service,
            staff=vet,
            start_time=start,
            notes='First visit'
        )

        assert appointment is not None
        assert appointment.id is not None
        assert appointment.owner == owner
        assert appointment.pet == pet
        assert appointment.service == service
        assert appointment.veterinarian == vet
        assert appointment.status == 'scheduled'
        assert appointment.notes == 'First visit'

    def test_book_appointment_sets_end_time(
        self, owner, pet, vet, service, schedule_block
    ):
        """Booking should calculate end time from service duration."""
        from apps.appointments.services import AvailabilityService

        today = date.today()
        days_until_tuesday = (1 - today.weekday()) % 7
        if days_until_tuesday == 0:
            days_until_tuesday = 7
        next_tuesday = today + timedelta(days=days_until_tuesday)

        start = timezone.make_aware(datetime.combine(next_tuesday, time(10, 0)))

        appointment = AvailabilityService.book_appointment(
            owner=owner,
            pet=pet,
            service=service,
            staff=vet,
            start_time=start
        )

        expected_end = start + timedelta(minutes=30)
        assert appointment.scheduled_end == expected_end

    def test_book_unavailable_slot_raises_error(
        self, owner, pet, vet, service, schedule_block
    ):
        """Booking unavailable slot should raise ValueError."""
        from apps.appointments.services import AvailabilityService

        today = date.today()
        days_until_tuesday = (1 - today.weekday()) % 7
        if days_until_tuesday == 0:
            days_until_tuesday = 7
        next_tuesday = today + timedelta(days=days_until_tuesday)

        # Book 10:00 first
        start = timezone.make_aware(datetime.combine(next_tuesday, time(10, 0)))
        AvailabilityService.book_appointment(
            owner=owner,
            pet=pet,
            service=service,
            staff=vet,
            start_time=start
        )

        # Try to book same slot again with different owner
        owner2 = User.objects.create_user(
            username='owner2', email='owner2@test.com', password='pass'
        )
        from apps.pets.models import Pet
        pet2 = Pet.objects.create(owner=owner2, name='Max', species='dog')

        with pytest.raises(ValueError) as exc_info:
            AvailabilityService.book_appointment(
                owner=owner2,
                pet=pet2,
                service=service,
                staff=vet,
                start_time=start
            )

        assert 'not available' in str(exc_info.value).lower()

    def test_book_appointment_without_pet(
        self, owner, vet, schedule_block
    ):
        """Services that don't require pet can be booked without one."""
        from apps.appointments.models import ServiceType
        from apps.appointments.services import AvailabilityService

        phone_consultation = ServiceType.objects.create(
            name='Phone Consultation',
            duration_minutes=15,
            price=Decimal('200.00'),
            requires_pet=False
        )

        today = date.today()
        days_until_tuesday = (1 - today.weekday()) % 7
        if days_until_tuesday == 0:
            days_until_tuesday = 7
        next_tuesday = today + timedelta(days=days_until_tuesday)

        start = timezone.make_aware(datetime.combine(next_tuesday, time(10, 0)))

        appointment = AvailabilityService.book_appointment(
            owner=owner,
            pet=None,
            service=phone_consultation,
            staff=vet,
            start_time=start
        )

        assert appointment.pet is None

    def test_book_requires_pet_when_service_requires_pet(
        self, owner, vet, service, schedule_block
    ):
        """Services requiring pet should fail without one."""
        from apps.appointments.services import AvailabilityService

        today = date.today()
        days_until_tuesday = (1 - today.weekday()) % 7
        if days_until_tuesday == 0:
            days_until_tuesday = 7
        next_tuesday = today + timedelta(days=days_until_tuesday)

        start = timezone.make_aware(datetime.combine(next_tuesday, time(10, 0)))

        with pytest.raises(ValueError) as exc_info:
            AvailabilityService.book_appointment(
                owner=owner,
                pet=None,
                service=service,
                staff=vet,
                start_time=start
            )

        assert 'pet' in str(exc_info.value).lower()


# =============================================================================
# Multiple Schedule Blocks Tests
# =============================================================================

@pytest.mark.django_db
class TestMultipleScheduleBlocks:
    """Tests for handling multiple schedule blocks."""

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
            name='General Consultation',
            duration_minutes=30,
            price=Decimal('450.00')
        )

    def test_multiple_blocks_same_day(self, vet, service):
        """Should handle multiple blocks on same day (morning + afternoon)."""
        from apps.appointments.models import ScheduleBlock
        from apps.appointments.services import AvailabilityService

        # Morning block 9am-12pm
        ScheduleBlock.objects.create(
            staff=vet,
            day_of_week=1,  # Tuesday
            start_time=time(9, 0),
            end_time=time(12, 0)
        )
        # Afternoon block 2pm-5pm
        ScheduleBlock.objects.create(
            staff=vet,
            day_of_week=1,  # Tuesday
            start_time=time(14, 0),
            end_time=time(17, 0)
        )

        today = date.today()
        days_until_tuesday = (1 - today.weekday()) % 7
        if days_until_tuesday == 0:
            days_until_tuesday = 7
        next_tuesday = today + timedelta(days=days_until_tuesday)

        slots = AvailabilityService.get_available_slots(
            date=next_tuesday,
            service=service,
            staff=vet
        )

        # Morning: 9:00, 9:30, 10:00, 10:30, 11:00, 11:30 = 6 slots
        # Afternoon: 14:00, 14:30, 15:00, 15:30, 16:00, 16:30 = 6 slots
        assert len(slots) == 12

        slot_times = [s['time'] for s in slots]
        assert time(9, 0) in slot_times
        assert time(11, 30) in slot_times
        assert time(14, 0) in slot_times
        assert time(16, 30) in slot_times
        # Gap should not have slots
        assert time(12, 30) not in slot_times
        assert time(13, 0) not in slot_times


# =============================================================================
# Any Available Staff Tests
# =============================================================================

@pytest.mark.django_db
class TestAnyAvailableStaff:
    """Tests for finding any available staff member."""

    @pytest.fixture
    def service(self):
        from apps.appointments.models import ServiceType
        return ServiceType.objects.create(
            name='General Consultation',
            duration_minutes=30,
            price=Decimal('450.00')
        )

    def test_get_slots_without_specific_staff(self, service):
        """Should return slots from any available staff."""
        from apps.appointments.models import ScheduleBlock
        from apps.appointments.services import AvailabilityService

        vet1 = User.objects.create_user(
            username='vet1', email='vet1@test.com', password='pass', role='vet'
        )
        vet2 = User.objects.create_user(
            username='vet2', email='vet2@test.com', password='pass', role='vet'
        )

        # vet1 works Tuesday morning
        ScheduleBlock.objects.create(
            staff=vet1,
            day_of_week=1,
            start_time=time(9, 0),
            end_time=time(12, 0)
        )
        # vet2 works Tuesday afternoon
        ScheduleBlock.objects.create(
            staff=vet2,
            day_of_week=1,
            start_time=time(14, 0),
            end_time=time(17, 0)
        )

        today = date.today()
        days_until_tuesday = (1 - today.weekday()) % 7
        if days_until_tuesday == 0:
            days_until_tuesday = 7
        next_tuesday = today + timedelta(days=days_until_tuesday)

        slots = AvailabilityService.get_available_slots(
            date=next_tuesday,
            service=service,
            staff=None  # Any staff
        )

        # Should include slots from both vets
        assert len(slots) == 12

        # Slots should indicate which staff
        morning_slot = next(s for s in slots if s['time'] == time(9, 0))
        assert morning_slot['staff_id'] == vet1.id

        afternoon_slot = next(s for s in slots if s['time'] == time(14, 0))
        assert afternoon_slot['staff_id'] == vet2.id


# =============================================================================
# Inactive Schedule Block Tests
# =============================================================================

@pytest.mark.django_db
class TestInactiveScheduleBlocks:
    """Tests for inactive schedule blocks."""

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
            name='General Consultation',
            duration_minutes=30,
            price=Decimal('450.00')
        )

    def test_inactive_blocks_are_ignored(self, vet, service):
        """Inactive schedule blocks should not provide slots."""
        from apps.appointments.models import ScheduleBlock
        from apps.appointments.services import AvailabilityService

        ScheduleBlock.objects.create(
            staff=vet,
            day_of_week=1,  # Tuesday
            start_time=time(9, 0),
            end_time=time(14, 0),
            is_active=False  # Inactive
        )

        today = date.today()
        days_until_tuesday = (1 - today.weekday()) % 7
        if days_until_tuesday == 0:
            days_until_tuesday = 7
        next_tuesday = today + timedelta(days=days_until_tuesday)

        slots = AvailabilityService.get_available_slots(
            date=next_tuesday,
            service=service,
            staff=vet
        )

        assert slots == []
