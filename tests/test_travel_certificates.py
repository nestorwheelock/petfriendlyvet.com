"""Tests for travel certificates functionality."""
import pytest
from datetime import date, timedelta
from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model

from apps.pets.models import Pet, Vaccination
from apps.travel.models import (
    TravelDestination,
    HealthCertificate,
    CertificateRequirement,
    TravelPlan,
)

User = get_user_model()


@pytest.fixture
def user(db):
    """Create a regular test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def staff_user(db):
    """Create a staff user."""
    return User.objects.create_user(
        username='staffuser',
        email='staff@example.com',
        password='staffpass123',
        is_staff=True
    )


@pytest.fixture
def auth_client(client, user):
    """Return authenticated client."""
    client.force_login(user)
    return client


@pytest.fixture
def destination_usa(db):
    """Create USA destination with requirements."""
    return TravelDestination.objects.create(
        country_code='US',
        country_name='United States',
        requirements={
            'rabies_vaccine': {
                'required': True,
                'days_before': 30,
                'description': 'Rabies vaccination required at least 30 days before travel'
            },
            'microchip': {
                'required': True,
                'description': 'ISO-compatible microchip required'
            },
            'health_exam': {
                'required': True,
                'days_before': 10,
                'description': 'Veterinary health examination within 10 days of travel'
            }
        },
        certificate_validity_days=10,
        quarantine_required=False,
        notes='USDA endorsement required for commercial flights'
    )


@pytest.fixture
def destination_uk(db):
    """Create UK destination with requirements."""
    return TravelDestination.objects.create(
        country_code='GB',
        country_name='United Kingdom',
        requirements={
            'rabies_vaccine': {
                'required': True,
                'days_before': 21,
                'description': 'Rabies vaccination required at least 21 days before travel'
            },
            'microchip': {
                'required': True,
                'description': 'ISO 11784/11785 microchip required'
            },
            'tapeworm_treatment': {
                'required': True,
                'hours_before': 120,
                'description': 'Tapeworm treatment 24-120 hours before arrival'
            }
        },
        certificate_validity_days=10,
        quarantine_required=False,
        notes='EU Pet Passport or Third Country Official Veterinary Certificate'
    )


@pytest.fixture
def pet_with_vaccines(user, db):
    """Create pet with up-to-date vaccinations."""
    pet = Pet.objects.create(
        name='Travel Buddy',
        species='dog',
        breed='Labrador',
        owner=user,
        microchip_id='123456789012345',
    )

    Vaccination.objects.create(
        pet=pet,
        vaccine_name='Rabies',
        date_administered=date.today() - timedelta(days=60),
        next_due_date=date.today() + timedelta(days=365 * 3 - 60),
        batch_number='RAB2024001'
    )

    return pet


class TestTravelDestinationModel:
    """Test TravelDestination model."""

    def test_create_destination(self, destination_usa):
        """Test creating a travel destination."""
        assert destination_usa.country_code == 'US'
        assert destination_usa.country_name == 'United States'
        assert destination_usa.certificate_validity_days == 10
        assert not destination_usa.quarantine_required

    def test_destination_str(self, destination_usa):
        """Test destination string representation."""
        assert str(destination_usa) == 'United States (US)'

    def test_destination_requirements(self, destination_usa):
        """Test destination requirements JSON."""
        assert 'rabies_vaccine' in destination_usa.requirements
        assert destination_usa.requirements['rabies_vaccine']['required'] is True
        assert destination_usa.requirements['rabies_vaccine']['days_before'] == 30


class TestHealthCertificateModel:
    """Test HealthCertificate model."""

    def test_create_certificate(self, pet_with_vaccines, destination_usa, staff_user):
        """Test creating a health certificate."""
        certificate = HealthCertificate.objects.create(
            pet=pet_with_vaccines,
            destination=destination_usa,
            travel_date=date.today() + timedelta(days=7),
            issued_by=staff_user,
        )

        assert certificate.pet == pet_with_vaccines
        assert certificate.destination == destination_usa
        assert certificate.status == 'pending'

    def test_certificate_str(self, pet_with_vaccines, destination_usa, staff_user):
        """Test certificate string representation."""
        certificate = HealthCertificate.objects.create(
            pet=pet_with_vaccines,
            destination=destination_usa,
            travel_date=date.today() + timedelta(days=7),
            issued_by=staff_user,
        )

        assert 'Travel Buddy' in str(certificate)
        assert 'United States' in str(certificate)

    def test_certificate_expiry(self, pet_with_vaccines, destination_usa, staff_user):
        """Test certificate expiry date calculation."""
        travel_date = date.today() + timedelta(days=7)
        certificate = HealthCertificate.objects.create(
            pet=pet_with_vaccines,
            destination=destination_usa,
            travel_date=travel_date,
            issued_by=staff_user,
            issue_date=date.today(),
        )
        certificate.calculate_expiry()

        # Certificate should expire based on destination validity
        expected_expiry = date.today() + timedelta(days=10)
        assert certificate.expiry_date == expected_expiry

    def test_certificate_statuses(self, pet_with_vaccines, destination_usa, staff_user):
        """Test certificate status transitions."""
        certificate = HealthCertificate.objects.create(
            pet=pet_with_vaccines,
            destination=destination_usa,
            travel_date=date.today() + timedelta(days=7),
            issued_by=staff_user,
        )

        assert certificate.status == 'pending'

        certificate.status = 'issued'
        certificate.save()
        assert certificate.status == 'issued'


class TestCertificateRequirementModel:
    """Test CertificateRequirement model."""

    def test_create_requirement(self, pet_with_vaccines, destination_usa, staff_user):
        """Test creating a certificate requirement."""
        certificate = HealthCertificate.objects.create(
            pet=pet_with_vaccines,
            destination=destination_usa,
            travel_date=date.today() + timedelta(days=7),
            issued_by=staff_user,
        )

        requirement = CertificateRequirement.objects.create(
            certificate=certificate,
            requirement_type='rabies_vaccine',
            description='Rabies vaccination verified',
            is_verified=True,
            verified_by=staff_user,
            verified_at=date.today(),
        )

        assert requirement.is_verified
        assert requirement.verified_by == staff_user

    def test_requirement_str(self, pet_with_vaccines, destination_usa, staff_user):
        """Test requirement string representation."""
        certificate = HealthCertificate.objects.create(
            pet=pet_with_vaccines,
            destination=destination_usa,
            travel_date=date.today() + timedelta(days=7),
            issued_by=staff_user,
        )

        requirement = CertificateRequirement.objects.create(
            certificate=certificate,
            requirement_type='rabies_vaccine',
            description='Rabies vaccination verified',
        )

        assert 'rabies_vaccine' in str(requirement)


class TestTravelPlanModel:
    """Test TravelPlan model."""

    def test_create_travel_plan(self, pet_with_vaccines, destination_usa):
        """Test creating a travel plan."""
        travel_plan = TravelPlan.objects.create(
            pet=pet_with_vaccines,
            destination=destination_usa,
            departure_date=date.today() + timedelta(days=30),
            return_date=date.today() + timedelta(days=45),
            airline='American Airlines',
            flight_number='AA123',
        )

        assert travel_plan.pet == pet_with_vaccines
        assert travel_plan.status == 'planning'

    def test_travel_plan_str(self, pet_with_vaccines, destination_usa):
        """Test travel plan string representation."""
        travel_plan = TravelPlan.objects.create(
            pet=pet_with_vaccines,
            destination=destination_usa,
            departure_date=date.today() + timedelta(days=30),
        )

        assert 'Travel Buddy' in str(travel_plan)
        assert 'United States' in str(travel_plan)


class TestTravelCertificateViews:
    """Test travel certificate views."""

    def test_destination_list_requires_login(self, client, destination_usa):
        """Test destination list requires authentication."""
        response = client.get(reverse('travel:destination_list'))
        assert response.status_code == 302
        assert 'login' in response.url

    def test_destination_list_shows_countries(self, auth_client, destination_usa, destination_uk):
        """Test destination list shows all countries."""
        response = auth_client.get(reverse('travel:destination_list'))
        assert response.status_code == 200
        assert 'United States' in response.content.decode()
        assert 'United Kingdom' in response.content.decode()

    def test_destination_detail_view(self, auth_client, destination_usa):
        """Test destination detail shows requirements."""
        response = auth_client.get(
            reverse('travel:destination_detail', kwargs={'pk': destination_usa.pk})
        )
        assert response.status_code == 200
        assert 'Rabies' in response.content.decode()

    def test_request_certificate_requires_login(self, client, pet_with_vaccines, destination_usa):
        """Test certificate request requires authentication."""
        response = client.get(
            reverse('travel:certificate_request', kwargs={'pet_pk': pet_with_vaccines.pk})
        )
        assert response.status_code == 302

    def test_request_certificate_form_displayed(self, auth_client, pet_with_vaccines, destination_usa):
        """Test certificate request form is displayed."""
        response = auth_client.get(
            reverse('travel:certificate_request', kwargs={'pet_pk': pet_with_vaccines.pk})
        )
        assert response.status_code == 200
        assert 'Travel Buddy' in response.content.decode()

    def test_request_certificate_success(self, auth_client, pet_with_vaccines, destination_usa):
        """Test successful certificate request."""
        response = auth_client.post(
            reverse('travel:certificate_request', kwargs={'pet_pk': pet_with_vaccines.pk}),
            {
                'destination': destination_usa.pk,
                'travel_date': (date.today() + timedelta(days=30)).isoformat(),
                'notes': 'Flying to visit family',
            }
        )
        assert response.status_code == 302
        assert HealthCertificate.objects.filter(pet=pet_with_vaccines).exists()

    def test_certificate_list_shows_user_certificates(self, auth_client, pet_with_vaccines, destination_usa, staff_user):
        """Test certificate list shows user's certificates."""
        HealthCertificate.objects.create(
            pet=pet_with_vaccines,
            destination=destination_usa,
            travel_date=date.today() + timedelta(days=7),
            issued_by=staff_user,
        )

        response = auth_client.get(reverse('travel:certificate_list'))
        assert response.status_code == 200
        assert 'Travel Buddy' in response.content.decode()

    def test_certificate_detail_view(self, auth_client, pet_with_vaccines, destination_usa, staff_user):
        """Test certificate detail view."""
        certificate = HealthCertificate.objects.create(
            pet=pet_with_vaccines,
            destination=destination_usa,
            travel_date=date.today() + timedelta(days=7),
            issued_by=staff_user,
        )

        response = auth_client.get(
            reverse('travel:certificate_detail', kwargs={'pk': certificate.pk})
        )
        assert response.status_code == 200
        assert 'United States' in response.content.decode()


class TestTravelTools:
    """Test AI tools for travel certificates."""

    def test_check_travel_requirements(self, pet_with_vaccines, destination_usa):
        """Test check travel requirements tool."""
        from apps.travel.tools import check_travel_requirements

        result = check_travel_requirements(
            pet_id=pet_with_vaccines.pk,
            destination_id=destination_usa.pk,
            travel_date=(date.today() + timedelta(days=30)).isoformat()
        )

        assert result['success']
        assert 'requirements' in result
        assert 'rabies_vaccine' in result['requirements']

    def test_check_requirements_invalid_pet(self, destination_usa):
        """Test check requirements with invalid pet."""
        from apps.travel.tools import check_travel_requirements

        result = check_travel_requirements(
            pet_id=99999,
            destination_id=destination_usa.pk,
            travel_date=(date.today() + timedelta(days=30)).isoformat()
        )

        assert not result['success']
        assert 'error' in result

    def test_get_destination_requirements(self, destination_usa):
        """Test get destination requirements tool."""
        from apps.travel.tools import get_destination_requirements

        result = get_destination_requirements(destination_id=destination_usa.pk)

        assert result['success']
        assert result['country'] == 'United States'
        assert 'requirements' in result

    def test_list_destinations(self, destination_usa, destination_uk):
        """Test list destinations tool."""
        from apps.travel.tools import list_destinations

        result = list_destinations()

        assert result['success']
        assert len(result['destinations']) >= 2
