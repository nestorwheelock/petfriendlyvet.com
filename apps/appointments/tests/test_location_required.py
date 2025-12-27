"""Tests for Location requirement on Appointments.

TDD: Location should be required for appointment creation.
"""
import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from apps.appointments.models import Appointment, ServiceType
from apps.locations.models import Location
from apps.parties.models import Organization


@pytest.fixture
def organization(db):
    """Create test organization."""
    return Organization.objects.create(name='Test Clinic', org_type='clinic')


@pytest.fixture
def location(db, organization):
    """Create test location."""
    return Location.objects.create(
        name='Main Clinic',
        organization=organization,
        is_active=True,
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
def customer_user(db, django_user_model):
    """Create customer user."""
    return django_user_model.objects.create_user(
        username='customer',
        email='customer@test.com',
        password='testpass123',
    )


@pytest.mark.django_db
class TestLocationRequiredOnAppointment:
    """Tests that Location is required on Appointment model."""

    def test_appointment_with_location_succeeds(
        self, customer_user, service_type, location
    ):
        """Appointment with location is valid."""
        now = timezone.now()
        appointment = Appointment.objects.create(
            owner=customer_user,
            service=service_type,
            location=location,
            scheduled_start=now,
            scheduled_end=now + timezone.timedelta(minutes=30),
            status='scheduled',
        )
        assert appointment.location == location

    def test_appointment_without_location_fails_validation(
        self, customer_user, service_type
    ):
        """Appointment without location fails model validation."""
        now = timezone.now()
        appointment = Appointment(
            owner=customer_user,
            service=service_type,
            location=None,
            scheduled_start=now,
            scheduled_end=now + timezone.timedelta(minutes=30),
            status='scheduled',
        )
        with pytest.raises(ValidationError):
            appointment.full_clean()

    def test_location_field_not_nullable(self, customer_user, service_type):
        """Location field should not allow NULL in database."""
        now = timezone.now()
        with pytest.raises((IntegrityError, ValidationError)):
            Appointment.objects.create(
                owner=customer_user,
                service=service_type,
                location=None,
                scheduled_start=now,
                scheduled_end=now + timezone.timedelta(minutes=30),
                status='scheduled',
            )
