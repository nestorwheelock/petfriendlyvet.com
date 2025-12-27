"""Tests for seed_dev_data management command.

TDD: These tests verify the seed data management command creates
the expected dev data for EMR workflow testing.
"""
import pytest
from django.core.management import call_command
from io import StringIO

from apps.accounts.models import User
from apps.appointments.models import Appointment, ServiceType
from apps.locations.models import Location
from apps.parties.models import Organization
from apps.pets.models import Pet
from apps.practice.models import PatientRecord


@pytest.fixture
def clear_seed_data(db):
    """Ensure clean state before each test."""
    Appointment.objects.filter(notes__startswith='[SEED]').delete()
    Pet.objects.filter(name__startswith='[SEED]').delete()
    User.objects.filter(username__startswith='seed_').delete()
    ServiceType.objects.filter(name__startswith='[SEED]').delete()
    Location.objects.filter(name__startswith='[SEED]').delete()
    Organization.objects.filter(name__startswith='[SEED]').delete()


@pytest.mark.django_db
class TestSeedDevDataCommand:
    """Test seed_dev_data management command."""

    def test_creates_organization(self, clear_seed_data):
        """Command creates seed organization."""
        out = StringIO()
        call_command('seed_dev_data', stdout=out)

        org = Organization.objects.filter(name='[SEED] Pet Friendly Vet Clinic')
        assert org.exists()
        assert org.first().org_type == 'clinic'
        assert 'Created organization' in out.getvalue()

    def test_creates_location(self, clear_seed_data):
        """Command creates seed location linked to organization."""
        out = StringIO()
        call_command('seed_dev_data', stdout=out)

        location = Location.objects.filter(name='[SEED] Main Clinic')
        assert location.exists()
        loc = location.first()
        assert loc.organization.name == '[SEED] Pet Friendly Vet Clinic'
        assert loc.is_active is True
        assert 'Created location' in out.getvalue()

    def test_creates_staff_users(self, clear_seed_data):
        """Command creates 3 staff users with correct roles."""
        out = StringIO()
        call_command('seed_dev_data', stdout=out)

        vet = User.objects.filter(username='seed_vet')
        tech = User.objects.filter(username='seed_tech')
        reception = User.objects.filter(username='seed_reception')

        assert vet.exists()
        assert tech.exists()
        assert reception.exists()

        assert vet.first().is_staff is True
        assert tech.first().is_staff is True
        assert reception.first().is_staff is True

        output = out.getvalue()
        assert 'Created staff' in output

    def test_creates_customer(self, clear_seed_data):
        """Command creates customer user."""
        out = StringIO()
        call_command('seed_dev_data', stdout=out)

        customer = User.objects.filter(username='seed_customer')
        assert customer.exists()
        assert customer.first().is_staff is False
        assert 'Created customer' in out.getvalue()

    def test_creates_pets(self, clear_seed_data):
        """Command creates 3 pets for customer."""
        out = StringIO()
        call_command('seed_dev_data', stdout=out)

        pets = Pet.objects.filter(name__startswith='[SEED]')
        assert pets.count() == 3

        pet_names = [p.name for p in pets]
        assert '[SEED] Buddy' in pet_names
        assert '[SEED] Whiskers' in pet_names
        assert '[SEED] Max' in pet_names

    def test_creates_patient_records(self, clear_seed_data):
        """Command creates PatientRecord for each pet (required for EMR)."""
        out = StringIO()
        call_command('seed_dev_data', stdout=out)

        pets = Pet.objects.filter(name__startswith='[SEED]')
        for pet in pets:
            assert hasattr(pet, 'patient_record')
            assert pet.patient_record is not None
            assert pet.patient_record.patient_number.startswith('SEED-')
            assert pet.patient_record.status == 'active'

    def test_creates_service_types(self, clear_seed_data):
        """Command creates service types."""
        out = StringIO()
        call_command('seed_dev_data', stdout=out)

        services = ServiceType.objects.filter(name__startswith='[SEED]')
        assert services.count() == 3

    def test_creates_appointments(self, clear_seed_data):
        """Command creates today's appointments."""
        out = StringIO()
        call_command('seed_dev_data', stdout=out)

        appointments = Appointment.objects.filter(notes__startswith='[SEED]')
        assert appointments.count() >= 3

        statuses = [a.status for a in appointments]
        assert 'scheduled' in statuses or 'confirmed' in statuses

    def test_clear_flag_removes_seed_data(self, clear_seed_data):
        """--clear flag removes existing seed data before creating new."""
        call_command('seed_dev_data')

        assert Organization.objects.filter(name='[SEED] Pet Friendly Vet Clinic').exists()
        assert Pet.objects.filter(name__startswith='[SEED]').count() == 3

        out = StringIO()
        call_command('seed_dev_data', '--clear', stdout=out)

        assert 'Clearing existing seed data' in out.getvalue()
        assert Organization.objects.filter(name='[SEED] Pet Friendly Vet Clinic').exists()

    def test_idempotent_without_clear(self, clear_seed_data):
        """Running without --clear doesn't create duplicates."""
        call_command('seed_dev_data')
        call_command('seed_dev_data')

        assert Organization.objects.filter(name='[SEED] Pet Friendly Vet Clinic').count() == 1
        assert Pet.objects.filter(name__startswith='[SEED]').count() == 3
        assert User.objects.filter(username__startswith='seed_').count() == 4

    def test_login_credentials(self, clear_seed_data):
        """Staff users can authenticate with devpass123."""
        call_command('seed_dev_data')

        vet = User.objects.get(username='seed_vet')
        assert vet.check_password('devpass123')

        customer = User.objects.get(username='seed_customer')
        assert customer.check_password('devpass123')
