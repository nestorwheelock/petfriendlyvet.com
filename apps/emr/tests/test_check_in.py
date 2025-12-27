"""Tests for appointment check-in flow."""
import pytest
from django.utils import timezone

from apps.appointments.models import Appointment, ServiceType
from apps.emr.models import ClinicalEvent, Encounter
from apps.emr.services import encounters as encounter_service
from apps.locations.models import Location
from apps.parties.models import Organization
from apps.pets.models import Pet


@pytest.fixture
def organization(db):
    """Create test organization."""
    return Organization.objects.create(
        name='Test Clinic',
        org_type='clinic',
    )


@pytest.fixture
def location(db, organization):
    """Create test location."""
    return Location.objects.create(
        name='Main Clinic',
        organization=organization,
        is_active=True,
    )


@pytest.fixture
def staff_user(db, django_user_model):
    """Create staff user."""
    return django_user_model.objects.create_user(
        username='staff',
        email='staff@test.com',
        password='testpass123',
        is_staff=True,
    )


@pytest.fixture
def customer_user(db, django_user_model):
    """Create customer user."""
    return django_user_model.objects.create_user(
        username='customer',
        email='customer@test.com',
        password='testpass123',
    )


@pytest.fixture
def pet(db, customer_user):
    """Create test pet."""
    return Pet.objects.create(
        name='Buddy',
        species='dog',
        breed='Golden Retriever',
        owner=customer_user,
    )


@pytest.fixture
def service_type(db):
    """Create test service type."""
    return ServiceType.objects.create(
        name='General Checkup',
        duration_minutes=30,
        price=50.00,
        category='clinic',
    )


@pytest.fixture
def appointment(db, customer_user, pet, service_type, location):
    """Create test appointment."""
    now = timezone.now()
    return Appointment.objects.create(
        owner=customer_user,
        pet=pet,
        service=service_type,
        location=location,
        scheduled_start=now,
        scheduled_end=now + timezone.timedelta(minutes=30),
        status='scheduled',
    )


class TestCheckInAppointment:
    """Tests for check_in_appointment service function."""

    def test_check_in_creates_encounter(self, appointment, location, staff_user):
        """Check-in creates a new encounter."""
        encounter, created = encounter_service.check_in_appointment(
            appointment=appointment,
            location=location,
            user=staff_user,
        )

        assert created is True
        assert encounter is not None
        assert encounter.appointment == appointment
        assert encounter.location == location
        assert encounter.pipeline_state == 'checked_in'
        assert encounter.checked_in_at is not None
        assert encounter.scheduled_at == appointment.scheduled_start

    def test_check_in_idempotent(self, appointment, location, staff_user):
        """Repeat check-in returns existing encounter, doesn't create new one."""
        # First check-in
        encounter1, created1 = encounter_service.check_in_appointment(
            appointment=appointment,
            location=location,
            user=staff_user,
        )
        assert created1 is True

        # Second check-in - should return same encounter
        encounter2, created2 = encounter_service.check_in_appointment(
            appointment=appointment,
            location=location,
            user=staff_user,
        )
        assert created2 is False
        assert encounter1.id == encounter2.id

        # Should still only have one encounter
        assert Encounter.objects.filter(appointment=appointment).count() == 1

    def test_check_in_location_matches_appointment(self, appointment, location, staff_user):
        """Encounter location matches the location passed in."""
        encounter, _ = encounter_service.check_in_appointment(
            appointment=appointment,
            location=location,
            user=staff_user,
        )

        assert encounter.location == location
        assert encounter.location.name == 'Main Clinic'

    def test_check_in_creates_clinical_events(self, appointment, location, staff_user):
        """Check-in creates clinical events for audit trail."""
        encounter, _ = encounter_service.check_in_appointment(
            appointment=appointment,
            location=location,
            user=staff_user,
        )

        events = ClinicalEvent.objects.filter(encounter=encounter)
        assert events.count() == 2  # encounter_created + state_change

        event_types = list(events.values_list('event_type', flat=True))
        assert 'encounter_created' in event_types
        assert 'state_change' in event_types

    def test_check_in_updates_appointment_status(self, appointment, location, staff_user):
        """Check-in updates appointment status to in_progress."""
        encounter_service.check_in_appointment(
            appointment=appointment,
            location=location,
            user=staff_user,
        )

        appointment.refresh_from_db()
        assert appointment.status == 'in_progress'

    def test_check_in_sets_chief_complaint_from_notes(self, appointment, location, staff_user):
        """Chief complaint comes from appointment notes."""
        appointment.notes = "Dog is limping"
        appointment.save()

        encounter, _ = encounter_service.check_in_appointment(
            appointment=appointment,
            location=location,
            user=staff_user,
        )

        assert encounter.chief_complaint == "Dog is limping"

    def test_check_in_sets_chief_complaint_from_service_if_no_notes(
        self, appointment, location, staff_user
    ):
        """Chief complaint falls back to service name if no notes."""
        appointment.notes = ""
        appointment.save()

        encounter, _ = encounter_service.check_in_appointment(
            appointment=appointment,
            location=location,
            user=staff_user,
        )

        assert encounter.chief_complaint == appointment.service.name

    def test_check_in_assigns_vet_from_appointment(
        self, appointment, location, staff_user, django_user_model
    ):
        """Assigned vet comes from appointment."""
        vet = django_user_model.objects.create_user(
            username='drvet',
            email='vet@test.com',
            password='testpass123',
            is_staff=True,
        )
        appointment.veterinarian = vet
        appointment.save()

        encounter, _ = encounter_service.check_in_appointment(
            appointment=appointment,
            location=location,
            user=staff_user,
        )

        assert encounter.assigned_vet == vet

    def test_check_in_rejected_for_cancelled_appointment(
        self, appointment, location, staff_user
    ):
        """Cannot check in cancelled appointment."""
        appointment.status = 'cancelled'
        appointment.save()

        with pytest.raises(ValueError, match="Cannot check in cancelled"):
            encounter_service.check_in_appointment(
                appointment=appointment,
                location=location,
                user=staff_user,
            )

    def test_check_in_rejected_for_completed_appointment(
        self, appointment, location, staff_user
    ):
        """Cannot check in completed appointment."""
        # Use update to bypass signals that try to create invoices
        Appointment.objects.filter(pk=appointment.pk).update(status='completed')
        appointment.refresh_from_db()

        with pytest.raises(ValueError, match="Cannot check in completed"):
            encounter_service.check_in_appointment(
                appointment=appointment,
                location=location,
                user=staff_user,
            )

    def test_check_in_rejected_without_pet(
        self, appointment, location, staff_user
    ):
        """Cannot check in appointment without a pet."""
        appointment.pet = None
        appointment.save()

        with pytest.raises(ValueError, match="requires a pet"):
            encounter_service.check_in_appointment(
                appointment=appointment,
                location=location,
                user=staff_user,
            )

    def test_check_in_creates_patient_record(self, appointment, location, staff_user):
        """Check-in creates patient record if not exists."""
        from apps.practice.models import PatientRecord

        # Ensure no patient record exists
        assert not PatientRecord.objects.filter(pet=appointment.pet).exists()

        encounter, _ = encounter_service.check_in_appointment(
            appointment=appointment,
            location=location,
            user=staff_user,
        )

        # Patient record should now exist
        assert PatientRecord.objects.filter(pet=appointment.pet).exists()
        assert encounter.patient.pet == appointment.pet
