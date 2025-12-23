"""
Tests for Pet Views (S-003)

Tests cover:
- Owner dashboard view
- Pet list view
- Pet detail view
- Pet add/edit forms
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


# =============================================================================
# Owner Dashboard Tests
# =============================================================================

@pytest.mark.django_db
class TestOwnerDashboard:
    """Tests for the owner dashboard view."""

    @pytest.fixture
    def owner(self):
        return User.objects.create_user(
            username='petowner',
            email='owner@test.com',
            password='testpass123',
            role='owner'
        )

    @pytest.fixture
    def pet(self, owner):
        from apps.pets.models import Pet
        return Pet.objects.create(
            owner=owner,
            name='Luna',
            species='dog',
            breed='Golden Retriever',
            date_of_birth=date(2020, 5, 15)
        )

    def test_dashboard_requires_login(self, client):
        """Dashboard should require authentication."""
        url = reverse('pets:dashboard')
        response = client.get(url)
        assert response.status_code == 302  # Redirect to login

    def test_dashboard_accessible_when_logged_in(self, client, owner):
        """Authenticated user can access dashboard."""
        client.force_login(owner)
        url = reverse('pets:dashboard')
        response = client.get(url)
        assert response.status_code == 200

    def test_dashboard_shows_user_pets(self, client, owner, pet):
        """Dashboard should display user's pets."""
        client.force_login(owner)
        url = reverse('pets:dashboard')
        response = client.get(url)

        assert response.status_code == 200
        assert b'Luna' in response.content

    def test_dashboard_shows_upcoming_appointments(self, client, owner, pet):
        """Dashboard should show upcoming appointments."""
        from apps.appointments.models import ServiceType, Appointment

        service = ServiceType.objects.create(
            name='Checkup',
            duration_minutes=30,
            price=Decimal('450.00')
        )
        vet = User.objects.create_user(
            username='vet', email='vet@test.com', password='pass', role='vet'
        )
        start = timezone.now() + timedelta(days=3)
        Appointment.objects.create(
            owner=owner,
            pet=pet,
            service=service,
            veterinarian=vet,
            scheduled_start=start,
            scheduled_end=start + timedelta(minutes=30),
            status='scheduled'
        )

        client.force_login(owner)
        url = reverse('pets:dashboard')
        response = client.get(url)

        assert response.status_code == 200
        assert b'Checkup' in response.content

    def test_dashboard_only_shows_own_pets(self, client, owner):
        """Dashboard should only show user's own pets."""
        from apps.pets.models import Pet

        # Create another user with a pet
        other_user = User.objects.create_user(
            username='other', email='other@test.com', password='pass'
        )
        Pet.objects.create(
            owner=other_user,
            name='Max',
            species='cat'
        )

        client.force_login(owner)
        url = reverse('pets:dashboard')
        response = client.get(url)

        assert b'Max' not in response.content


# =============================================================================
# Pet List Tests
# =============================================================================

@pytest.mark.django_db
class TestPetListView:
    """Tests for the pet list view."""

    @pytest.fixture
    def owner(self):
        return User.objects.create_user(
            username='petowner',
            email='owner@test.com',
            password='testpass123'
        )

    def test_pet_list_requires_login(self, client):
        """Pet list should require authentication."""
        url = reverse('pets:pet_list')
        response = client.get(url)
        assert response.status_code == 302

    def test_pet_list_shows_all_user_pets(self, client, owner):
        """Should list all pets belonging to user."""
        from apps.pets.models import Pet

        Pet.objects.create(owner=owner, name='Luna', species='dog')
        Pet.objects.create(owner=owner, name='Max', species='cat')

        client.force_login(owner)
        url = reverse('pets:pet_list')
        response = client.get(url)

        assert response.status_code == 200
        assert b'Luna' in response.content
        assert b'Max' in response.content

    def test_pet_list_empty_state(self, client, owner):
        """Should handle empty pet list gracefully."""
        client.force_login(owner)
        url = reverse('pets:pet_list')
        response = client.get(url)

        assert response.status_code == 200


# =============================================================================
# Pet Detail Tests
# =============================================================================

@pytest.mark.django_db
class TestPetDetailView:
    """Tests for the pet detail view."""

    @pytest.fixture
    def owner(self):
        return User.objects.create_user(
            username='petowner',
            email='owner@test.com',
            password='testpass123'
        )

    @pytest.fixture
    def pet(self, owner):
        from apps.pets.models import Pet
        return Pet.objects.create(
            owner=owner,
            name='Luna',
            species='dog',
            breed='Golden Retriever',
            date_of_birth=date(2020, 5, 15),
            weight_kg=Decimal('25.5')
        )

    def test_pet_detail_requires_login(self, client, pet):
        """Pet detail should require authentication."""
        url = reverse('pets:pet_detail', kwargs={'pk': pet.pk})
        response = client.get(url)
        assert response.status_code == 302

    def test_pet_detail_shows_info(self, client, owner, pet):
        """Should show pet details."""
        client.force_login(owner)
        url = reverse('pets:pet_detail', kwargs={'pk': pet.pk})
        response = client.get(url)

        assert response.status_code == 200
        assert b'Luna' in response.content
        assert b'Golden Retriever' in response.content

    def test_pet_detail_shows_vaccinations(self, client, owner, pet):
        """Should show pet's vaccinations."""
        from apps.pets.models import Vaccination

        Vaccination.objects.create(
            pet=pet,
            vaccine_name='Rabies',
            date_administered=date.today() - timedelta(days=30),
            next_due_date=date.today() + timedelta(days=335)
        )

        client.force_login(owner)
        url = reverse('pets:pet_detail', kwargs={'pk': pet.pk})
        response = client.get(url)

        assert b'Rabies' in response.content

    def test_pet_detail_access_denied_for_other_users(self, client, pet):
        """Cannot view another user's pet."""
        other_user = User.objects.create_user(
            username='other', email='other@test.com', password='pass'
        )

        client.force_login(other_user)
        url = reverse('pets:pet_detail', kwargs={'pk': pet.pk})
        response = client.get(url)

        assert response.status_code == 404

    def test_pet_detail_shows_medical_conditions(self, client, owner, pet):
        """Should show pet's medical conditions."""
        from apps.pets.models import MedicalCondition

        MedicalCondition.objects.create(
            pet=pet,
            name='Allergies',
            notes='Seasonal allergies',
            diagnosed_date=date.today() - timedelta(days=180),
            is_active=True
        )

        client.force_login(owner)
        url = reverse('pets:pet_detail', kwargs={'pk': pet.pk})
        response = client.get(url)

        assert b'Allergies' in response.content


# =============================================================================
# Pet Add/Edit Tests
# =============================================================================

@pytest.mark.django_db
class TestPetCreateView:
    """Tests for adding a new pet."""

    @pytest.fixture
    def owner(self):
        return User.objects.create_user(
            username='petowner',
            email='owner@test.com',
            password='testpass123'
        )

    def test_pet_create_requires_login(self, client):
        """Pet creation should require authentication."""
        url = reverse('pets:pet_add')
        response = client.get(url)
        assert response.status_code == 302

    def test_pet_create_form_displayed(self, client, owner):
        """Should show pet creation form."""
        client.force_login(owner)
        url = reverse('pets:pet_add')
        response = client.get(url)

        assert response.status_code == 200
        assert b'name' in response.content.lower()

    def test_pet_create_success(self, client, owner):
        """Should create pet on valid submission."""
        from apps.pets.models import Pet

        client.force_login(owner)
        url = reverse('pets:pet_add')
        response = client.post(url, {
            'name': 'Buddy',
            'species': 'dog',
            'breed': 'Labrador',
            'gender': 'male',
        })

        assert Pet.objects.filter(name='Buddy', owner=owner).exists()
        assert response.status_code == 302  # Redirect after success

    def test_pet_create_sets_owner(self, client, owner):
        """Created pet should belong to logged-in user."""
        from apps.pets.models import Pet

        client.force_login(owner)
        url = reverse('pets:pet_add')
        client.post(url, {
            'name': 'Buddy',
            'species': 'dog',
            'gender': 'male',
        })

        pet = Pet.objects.get(name='Buddy')
        assert pet.owner == owner


@pytest.mark.django_db
class TestPetUpdateView:
    """Tests for editing a pet."""

    @pytest.fixture
    def owner(self):
        return User.objects.create_user(
            username='petowner',
            email='owner@test.com',
            password='testpass123'
        )

    @pytest.fixture
    def pet(self, owner):
        from apps.pets.models import Pet
        return Pet.objects.create(
            owner=owner,
            name='Luna',
            species='dog',
            gender='female'
        )

    def test_pet_edit_requires_login(self, client, pet):
        """Pet edit should require authentication."""
        url = reverse('pets:pet_edit', kwargs={'pk': pet.pk})
        response = client.get(url)
        assert response.status_code == 302

    def test_pet_edit_form_displayed(self, client, owner, pet):
        """Should show pet edit form with current data."""
        client.force_login(owner)
        url = reverse('pets:pet_edit', kwargs={'pk': pet.pk})
        response = client.get(url)

        assert response.status_code == 200
        assert b'Luna' in response.content

    def test_pet_edit_success(self, client, owner, pet):
        """Should update pet on valid submission."""
        client.force_login(owner)
        url = reverse('pets:pet_edit', kwargs={'pk': pet.pk})
        response = client.post(url, {
            'name': 'Luna Updated',
            'species': 'dog',
            'gender': 'female',
        })

        pet.refresh_from_db()
        assert pet.name == 'Luna Updated'

    def test_pet_edit_denied_for_other_users(self, client, pet):
        """Cannot edit another user's pet."""
        other_user = User.objects.create_user(
            username='other', email='other@test.com', password='pass'
        )

        client.force_login(other_user)
        url = reverse('pets:pet_edit', kwargs={'pk': pet.pk})
        response = client.get(url)

        assert response.status_code == 404
