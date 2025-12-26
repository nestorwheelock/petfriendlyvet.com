"""Integration tests for inventory URL routing through staff token middleware."""
import pytest
from django.test import Client
from django.contrib.auth import get_user_model


User = get_user_model()


@pytest.fixture
def staff_user(db):
    """Create a staff user."""
    return User.objects.create_user(
        username='inventory_test_staff',
        email='invstaff@example.com',
        password='testpass123',
        is_staff=True,
    )


@pytest.fixture
def authenticated_staff_client(staff_user):
    """Return a client logged in as staff user."""
    client = Client()
    client.login(username='inventory_test_staff', password='testpass123')
    return client


@pytest.mark.django_db
class TestInventoryRouting:
    """Test that inventory URLs work through the staff token middleware."""

    def test_staff_hub_accessible(self, authenticated_staff_client):
        """Test that staff hub is accessible and sets token."""
        response = authenticated_staff_client.get('/staff/')
        assert response.status_code == 200

        # Check that staff token was generated
        session = authenticated_staff_client.session
        staff_token = session.get('staff_token')
        assert staff_token is not None
        assert len(staff_token) == 6

    def test_inventory_dashboard_via_staff_token(self, authenticated_staff_client):
        """Test accessing inventory dashboard via staff token URL."""
        # First access staff hub to generate token
        authenticated_staff_client.get('/staff/')

        # Get the token from session
        session = authenticated_staff_client.session
        staff_token = session.get('staff_token')
        assert staff_token is not None

        # Now access inventory via token URL
        url = f'/staff-{staff_token}/operations/inventory/'
        response = authenticated_staff_client.get(url)

        # Should get 200 (or 302 redirect if needed)
        print(f"Response status: {response.status_code}")
        if response.status_code == 404:
            print(f"404 for URL: {url}")
        elif response.status_code == 302:
            print(f"Redirect to: {response.url}")

        assert response.status_code in [200, 302], f"Expected 200 or 302, got {response.status_code}"

    def test_inventory_stock_levels_via_staff_token(self, authenticated_staff_client):
        """Test accessing inventory stock levels via staff token URL."""
        # Generate token
        authenticated_staff_client.get('/staff/')
        session = authenticated_staff_client.session
        staff_token = session.get('staff_token')

        # Access stock levels
        url = f'/staff-{staff_token}/operations/inventory/stock/'
        response = authenticated_staff_client.get(url)

        assert response.status_code in [200, 302], f"Expected 200 or 302, got {response.status_code}"

    def test_direct_inventory_access_blocked(self, authenticated_staff_client):
        """Test that direct access to inventory (without token) is blocked."""
        response = authenticated_staff_client.get('/operations/inventory/')
        assert response.status_code == 404

    def test_invalid_token_returns_404(self, authenticated_staff_client):
        """Test that invalid token returns 404."""
        # Generate real token first
        authenticated_staff_client.get('/staff/')

        # Try with fake token
        url = '/staff-FAKE12/operations/inventory/'
        response = authenticated_staff_client.get(url)
        assert response.status_code == 404
