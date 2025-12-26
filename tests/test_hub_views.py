"""
Tests for Staff Hub and Customer Portal Dashboard views.
TDD tests for unified navigation hub dashboards.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.pets.models import Pet
from apps.appointments.models import Appointment
from apps.store.models import Order
from apps.loyalty.models import LoyaltyProgram, LoyaltyAccount

User = get_user_model()

pytestmark = pytest.mark.django_db


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
def customer_user():
    """Create a regular customer user."""
    return User.objects.create_user(
        username='customeruser',
        email='customer@test.com',
        password='testpass123',
        is_staff=False
    )


@pytest.fixture
def customer_with_pet(customer_user):
    """Create a customer with a pet."""
    Pet.objects.create(
        owner=customer_user,
        name='Buddy',
        species='dog',
        breed='Golden Retriever',
        date_of_birth=date.today() - timedelta(days=365*3),
        gender='male'
    )
    return customer_user


@pytest.fixture
def loyalty_program(db):
    """Create a loyalty program."""
    return LoyaltyProgram.objects.create(
        name='Pet Rewards',
        points_per_currency=10,
        is_active=True
    )


@pytest.fixture
def customer_with_loyalty(customer_user, loyalty_program):
    """Create a customer with loyalty account."""
    LoyaltyAccount.objects.create(
        user=customer_user,
        program=loyalty_program,
        points_balance=500
    )
    return customer_user


# =============================================================================
# Staff Hub Dashboard Tests
# =============================================================================

class TestStaffHubDashboard:
    """Tests for the staff hub dashboard."""

    def test_hub_requires_authentication(self, client):
        """Hub requires login."""
        url = reverse('core:staff_hub')
        response = client.get(url)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_hub_requires_staff(self, client, customer_user):
        """Hub returns 403 for non-staff users."""
        client.force_login(customer_user)
        url = reverse('core:staff_hub')
        response = client.get(url)
        assert response.status_code == 403

    def test_hub_accessible_by_staff(self, client, staff_user):
        """Staff users can access the hub."""
        client.force_login(staff_user)
        url = reverse('core:staff_hub')
        response = client.get(url)
        assert response.status_code == 200

    def test_hub_uses_correct_template(self, client, staff_user):
        """Hub uses the staff hub template."""
        client.force_login(staff_user)
        url = reverse('core:staff_hub')
        response = client.get(url)
        assert 'staff/hub.html' in [t.name for t in response.templates]

    def test_hub_shows_module_links(self, client, staff_user):
        """Hub shows quick links to all staff modules."""
        client.force_login(staff_user)
        url = reverse('core:staff_hub')
        response = client.get(url)
        content = response.content.decode()

        # Check for module links
        assert 'Practice' in content
        assert 'Inventory' in content
        assert 'Accounting' in content
        assert 'Marketing' in content

    def test_hub_shows_summary_stats(self, client, staff_user):
        """Hub shows summary statistics."""
        client.force_login(staff_user)
        url = reverse('core:staff_hub')
        response = client.get(url)

        # Check context has stats
        assert 'stats' in response.context

    def test_hub_shows_recent_activity(self, client, staff_user):
        """Hub shows recent activity section."""
        client.force_login(staff_user)
        url = reverse('core:staff_hub')
        response = client.get(url)
        content = response.content.decode()

        assert 'Recent Activity' in content or 'recent' in content.lower()


# =============================================================================
# Customer Portal Dashboard Tests
# =============================================================================

class TestPortalDashboard:
    """Tests for the customer portal dashboard."""

    def test_portal_requires_authentication(self, client):
        """Portal requires login."""
        url = reverse('core:portal_dashboard')
        response = client.get(url)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_portal_accessible_by_customer(self, client, customer_user):
        """Customers can access the portal."""
        client.force_login(customer_user)
        url = reverse('core:portal_dashboard')
        response = client.get(url)
        assert response.status_code == 200

    def test_portal_uses_correct_template(self, client, customer_user):
        """Portal uses the portal dashboard template."""
        client.force_login(customer_user)
        url = reverse('core:portal_dashboard')
        response = client.get(url)
        assert 'portal/dashboard.html' in [t.name for t in response.templates]

    def test_portal_shows_pets_section(self, client, customer_with_pet):
        """Portal shows user's pets."""
        client.force_login(customer_with_pet)
        url = reverse('core:portal_dashboard')
        response = client.get(url)
        content = response.content.decode()

        assert 'Buddy' in content or 'My Pets' in content

    def test_portal_shows_pets_in_context(self, client, customer_with_pet):
        """Portal includes pets in context."""
        client.force_login(customer_with_pet)
        url = reverse('core:portal_dashboard')
        response = client.get(url)

        assert 'pets' in response.context
        assert response.context['pets'].count() == 1

    def test_portal_shows_appointments_section(self, client, customer_user):
        """Portal shows appointments section."""
        client.force_login(customer_user)
        url = reverse('core:portal_dashboard')
        response = client.get(url)
        content = response.content.decode()

        assert 'Appointments' in content or 'appointments' in content.lower()

    def test_portal_shows_orders_section(self, client, customer_user):
        """Portal shows orders section."""
        client.force_login(customer_user)
        url = reverse('core:portal_dashboard')
        response = client.get(url)
        content = response.content.decode()

        assert 'Orders' in content or 'orders' in content.lower()

    def test_portal_shows_loyalty_points(self, client, customer_with_loyalty):
        """Portal shows loyalty points for customers with accounts."""
        client.force_login(customer_with_loyalty)
        url = reverse('core:portal_dashboard')
        response = client.get(url)

        assert 'loyalty_account' in response.context
        assert response.context['loyalty_account'].points_balance == 500

    def test_portal_no_loyalty_without_account(self, client, customer_user):
        """Portal handles customers without loyalty accounts."""
        client.force_login(customer_user)
        url = reverse('core:portal_dashboard')
        response = client.get(url)

        # Should not error, loyalty_account should be None
        assert response.context.get('loyalty_account') is None

    def test_portal_shows_quick_actions(self, client, customer_user):
        """Portal shows quick action buttons."""
        client.force_login(customer_user)
        url = reverse('core:portal_dashboard')
        response = client.get(url)
        content = response.content.decode()

        # Check for action links
        assert 'Book' in content or 'appointment' in content.lower()
