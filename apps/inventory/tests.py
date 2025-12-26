"""Tests for inventory app with staff_redirect utility."""
from django.test import TestCase
from django.test import RequestFactory
from apps.core.utils import staff_redirect, get_staff_url


class StaffRedirectUtilityTests(TestCase):
    """Test the staff_redirect utility function."""

    def test_get_staff_url_adds_token_prefix(self):
        """Test that get_staff_url adds staff token prefix to URL."""
        factory = RequestFactory()
        request = factory.get('/')
        request.session = {'staff_token': 'abc123'}

        url = get_staff_url(request, 'inventory:stock')

        self.assertEqual(url, '/staff-abc123/operations/inventory/stock/')

    def test_get_staff_url_with_pk_argument(self):
        """Test that get_staff_url handles pk argument correctly."""
        factory = RequestFactory()
        request = factory.get('/')
        request.session = {'staff_token': 'xyz789'}

        url = get_staff_url(request, 'inventory:supplier_detail', pk=5)

        self.assertEqual(url, '/staff-xyz789/operations/inventory/suppliers/5/')

    def test_staff_redirect_returns_302(self):
        """Test that staff_redirect returns a 302 redirect."""
        factory = RequestFactory()
        request = factory.get('/')
        request.session = {'staff_token': 'abc123'}

        response = staff_redirect(request, 'inventory:movements')

        self.assertEqual(response.status_code, 302)
        self.assertIn('/staff-abc123/', response.url)
        self.assertIn('/operations/inventory/movements/', response.url)

    def test_staff_redirect_without_token_falls_back(self):
        """Test that staff_redirect falls back when no token in session."""
        factory = RequestFactory()
        request = factory.get('/')
        request.session = {}

        response = staff_redirect(request, 'inventory:stock')

        self.assertEqual(response.status_code, 302)
        # Without token, returns base URL
        self.assertEqual(response.url, '/operations/inventory/stock/')
