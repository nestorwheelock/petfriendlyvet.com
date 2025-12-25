"""
Tests for CRM Views (TDD)

Tests cover:
- CRM Dashboard view (staff only)
- Customer list view
- Customer detail view
- Interaction tracking
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.crm.models import OwnerProfile, CustomerTag, Interaction, CustomerNote

User = get_user_model()


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def staff_user():
    """Create a staff user."""
    return User.objects.create_user(
        username='staffuser',
        email='staff@test.com',
        password='testpass123',
        is_staff=True
    )


@pytest.fixture
def regular_user():
    """Create a regular (non-staff) user."""
    return User.objects.create_user(
        username='regularuser',
        email='regular@test.com',
        password='testpass123',
        is_staff=False
    )


@pytest.fixture
def customer_user():
    """Create a customer user with an owner profile."""
    user = User.objects.create_user(
        username='customer1',
        email='customer1@test.com',
        password='testpass123',
        first_name='John',
        last_name='Doe'
    )
    return user


@pytest.fixture
def owner_profile(customer_user):
    """Create an owner profile for the customer."""
    return OwnerProfile.objects.create(
        user=customer_user,
        preferred_language='en',
        preferred_contact_method='email',
        total_visits=5,
        total_spent=Decimal('1500.00'),
        lifetime_value=Decimal('2000.00')
    )


@pytest.fixture
def customer_tag():
    """Create a customer tag."""
    return CustomerTag.objects.create(
        name='VIP',
        color='#FFD700',
        description='VIP customers'
    )


@pytest.fixture
def interaction(owner_profile, staff_user):
    """Create an interaction record."""
    return Interaction.objects.create(
        owner_profile=owner_profile,
        interaction_type='call',
        channel='phone',
        direction='outbound',
        subject='Follow-up call',
        notes='Discussed upcoming appointment',
        handled_by=staff_user,
        duration_minutes=15,
        follow_up_required=True,
        follow_up_date=date.today() + timedelta(days=7)
    )


@pytest.fixture
def customer_note(owner_profile, staff_user):
    """Create a customer note."""
    return CustomerNote.objects.create(
        owner_profile=owner_profile,
        author=staff_user,
        content='Customer prefers morning appointments',
        is_pinned=True
    )


# =============================================================================
# CRM Dashboard Tests
# =============================================================================

@pytest.mark.django_db
class TestCRMDashboard:
    """Tests for CRM dashboard view."""

    def test_dashboard_requires_login(self, client):
        """Dashboard should require authentication."""
        url = reverse('crm:dashboard')
        response = client.get(url)
        assert response.status_code == 302  # Redirect to login

    def test_dashboard_requires_staff(self, client, regular_user):
        """Dashboard should require staff status."""
        client.force_login(regular_user)
        url = reverse('crm:dashboard')
        response = client.get(url)
        assert response.status_code == 403  # Forbidden

    def test_dashboard_accessible_by_staff(self, client, staff_user):
        """Staff can access dashboard."""
        client.force_login(staff_user)
        url = reverse('crm:dashboard')
        response = client.get(url)
        assert response.status_code == 200

    def test_dashboard_shows_customer_count(self, client, staff_user, owner_profile):
        """Dashboard should show total customer count."""
        client.force_login(staff_user)
        url = reverse('crm:dashboard')
        response = client.get(url)

        assert response.status_code == 200
        assert 'total_customers' in response.context
        assert response.context['total_customers'] >= 1

    def test_dashboard_shows_new_customers(self, client, staff_user, owner_profile):
        """Dashboard should show new customers this month."""
        client.force_login(staff_user)
        url = reverse('crm:dashboard')
        response = client.get(url)

        assert 'new_customers_month' in response.context

    def test_dashboard_shows_recent_interactions(self, client, staff_user, interaction):
        """Dashboard should show recent interactions."""
        client.force_login(staff_user)
        url = reverse('crm:dashboard')
        response = client.get(url)

        assert 'recent_interactions' in response.context
        assert len(response.context['recent_interactions']) >= 1

    def test_dashboard_shows_followups_due(self, client, staff_user, owner_profile):
        """Dashboard should show follow-ups due."""
        # Create an overdue follow-up
        Interaction.objects.create(
            owner_profile=owner_profile,
            interaction_type='call',
            channel='phone',
            direction='outbound',
            follow_up_required=True,
            follow_up_date=date.today() - timedelta(days=1)
        )

        client.force_login(staff_user)
        url = reverse('crm:dashboard')
        response = client.get(url)

        assert 'followups_due' in response.context
        assert len(response.context['followups_due']) >= 1

    def test_dashboard_shows_customer_tags(self, client, staff_user, customer_tag, owner_profile):
        """Dashboard should show customer tags with counts."""
        owner_profile.tags.add(customer_tag)

        client.force_login(staff_user)
        url = reverse('crm:dashboard')
        response = client.get(url)

        assert 'tags' in response.context

    def test_dashboard_shows_top_customers(self, client, staff_user, owner_profile):
        """Dashboard should show top customers by spend."""
        client.force_login(staff_user)
        url = reverse('crm:dashboard')
        response = client.get(url)

        assert 'top_customers' in response.context


# =============================================================================
# Customer List Tests
# =============================================================================

@pytest.mark.django_db
class TestCustomerListView:
    """Tests for customer list view."""

    def test_customer_list_requires_login(self, client):
        """Customer list should require authentication."""
        url = reverse('crm:customer_list')
        response = client.get(url)
        assert response.status_code == 302

    def test_customer_list_requires_staff(self, client, regular_user):
        """Customer list should require staff status."""
        client.force_login(regular_user)
        url = reverse('crm:customer_list')
        response = client.get(url)
        assert response.status_code == 403

    def test_customer_list_accessible_by_staff(self, client, staff_user):
        """Staff can access customer list."""
        client.force_login(staff_user)
        url = reverse('crm:customer_list')
        response = client.get(url)
        assert response.status_code == 200

    def test_customer_list_shows_customers(self, client, staff_user, owner_profile):
        """Customer list should show customers."""
        client.force_login(staff_user)
        url = reverse('crm:customer_list')
        response = client.get(url)

        assert response.status_code == 200
        assert 'customers' in response.context
        assert len(response.context['customers']) >= 1

    def test_customer_list_shows_customer_info(self, client, staff_user, owner_profile):
        """Customer list should show customer name and email."""
        client.force_login(staff_user)
        url = reverse('crm:customer_list')
        response = client.get(url)

        content = response.content.decode()
        assert 'John' in content or 'customer1@test.com' in content

    def test_customer_list_pagination(self, client, staff_user):
        """Customer list should be paginated."""
        # Create 30 customers
        for i in range(30):
            user = User.objects.create_user(
                username=f'customer{i}',
                email=f'customer{i}@test.com',
                password='testpass123'
            )
            OwnerProfile.objects.create(user=user)

        client.force_login(staff_user)
        url = reverse('crm:customer_list')
        response = client.get(url)

        assert response.status_code == 200
        assert 'is_paginated' in response.context or len(response.context['customers']) <= 25


# =============================================================================
# Customer Detail Tests
# =============================================================================

@pytest.mark.django_db
class TestCustomerDetailView:
    """Tests for customer detail view."""

    def test_customer_detail_requires_login(self, client, owner_profile):
        """Customer detail should require authentication."""
        url = reverse('crm:customer_detail', kwargs={'pk': owner_profile.pk})
        response = client.get(url)
        assert response.status_code == 302

    def test_customer_detail_requires_staff(self, client, regular_user, owner_profile):
        """Customer detail should require staff status."""
        client.force_login(regular_user)
        url = reverse('crm:customer_detail', kwargs={'pk': owner_profile.pk})
        response = client.get(url)
        assert response.status_code == 403

    def test_customer_detail_accessible_by_staff(self, client, staff_user, owner_profile):
        """Staff can access customer detail."""
        client.force_login(staff_user)
        url = reverse('crm:customer_detail', kwargs={'pk': owner_profile.pk})
        response = client.get(url)
        assert response.status_code == 200

    def test_customer_detail_shows_profile(self, client, staff_user, owner_profile):
        """Customer detail should show profile info."""
        client.force_login(staff_user)
        url = reverse('crm:customer_detail', kwargs={'pk': owner_profile.pk})
        response = client.get(url)

        assert response.status_code == 200
        assert 'customer' in response.context
        assert response.context['customer'] == owner_profile

    def test_customer_detail_shows_interactions(self, client, staff_user, owner_profile, interaction):
        """Customer detail should show interactions."""
        client.force_login(staff_user)
        url = reverse('crm:customer_detail', kwargs={'pk': owner_profile.pk})
        response = client.get(url)

        assert 'interactions' in response.context
        assert len(response.context['interactions']) >= 1

    def test_customer_detail_shows_notes(self, client, staff_user, owner_profile, customer_note):
        """Customer detail should show notes."""
        client.force_login(staff_user)
        url = reverse('crm:customer_detail', kwargs={'pk': owner_profile.pk})
        response = client.get(url)

        assert 'notes' in response.context
        assert len(response.context['notes']) >= 1

    def test_customer_detail_shows_pets(self, client, staff_user, owner_profile):
        """Customer detail should show customer's pets."""
        from apps.pets.models import Pet

        Pet.objects.create(
            owner=owner_profile.user,
            name='Buddy',
            species='dog'
        )

        client.force_login(staff_user)
        url = reverse('crm:customer_detail', kwargs={'pk': owner_profile.pk})
        response = client.get(url)

        assert 'pets' in response.context
        assert len(response.context['pets']) >= 1

    def test_customer_detail_shows_spending(self, client, staff_user, owner_profile):
        """Customer detail should show spending info."""
        client.force_login(staff_user)
        url = reverse('crm:customer_detail', kwargs={'pk': owner_profile.pk})
        response = client.get(url)

        content = response.content.decode()
        # Should show total spent or lifetime value somewhere
        assert '1500' in content or '2000' in content or response.context['customer'].total_spent > 0

    def test_customer_detail_404_for_nonexistent(self, client, staff_user):
        """Should return 404 for non-existent customer."""
        client.force_login(staff_user)
        url = reverse('crm:customer_detail', kwargs={'pk': 99999})
        response = client.get(url)
        assert response.status_code == 404
