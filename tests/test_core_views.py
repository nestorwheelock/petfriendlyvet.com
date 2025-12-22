"""Tests for core app views."""
import pytest
from django.test import Client
from django.urls import reverse


@pytest.fixture
def client():
    """Return a Django test client."""
    return Client()


@pytest.mark.django_db
class TestHomeView:
    """Tests for the home page."""

    def test_home_page_returns_200(self, client):
        """Home page should return 200 status code."""
        response = client.get(reverse('core:home'))
        assert response.status_code == 200

    def test_home_page_uses_correct_template(self, client):
        """Home page should use the correct template."""
        response = client.get(reverse('core:home'))
        assert 'core/home.html' in [t.name for t in response.templates]

    def test_home_page_contains_site_name(self, client):
        """Home page should contain the site name."""
        response = client.get(reverse('core:home'))
        assert b'Pet-Friendly' in response.content


@pytest.mark.django_db
class TestAboutView:
    """Tests for the about page."""

    def test_about_page_returns_200(self, client):
        """About page should return 200 status code."""
        response = client.get(reverse('core:about'))
        assert response.status_code == 200

    def test_about_page_uses_correct_template(self, client):
        """About page should use the correct template."""
        response = client.get(reverse('core:about'))
        assert 'core/about.html' in [t.name for t in response.templates]


@pytest.mark.django_db
class TestServicesView:
    """Tests for the services page."""

    def test_services_page_returns_200(self, client):
        """Services page should return 200 status code."""
        response = client.get(reverse('core:services'))
        assert response.status_code == 200

    def test_services_page_uses_correct_template(self, client):
        """Services page should use the correct template."""
        response = client.get(reverse('core:services'))
        assert 'core/services.html' in [t.name for t in response.templates]


@pytest.mark.django_db
class TestContactView:
    """Tests for the contact page."""

    def test_contact_page_returns_200(self, client):
        """Contact page should return 200 status code."""
        response = client.get(reverse('core:contact'))
        assert response.status_code == 200

    def test_contact_page_uses_correct_template(self, client):
        """Contact page should use the correct template."""
        response = client.get(reverse('core:contact'))
        assert 'core/contact.html' in [t.name for t in response.templates]

    def test_contact_form_submission_redirects(self, client):
        """Contact form submission should redirect on success."""
        response = client.post(
            reverse('core:contact'),
            {
                'name': 'Test User',
                'email': 'test@example.com',
                'subject': 'question',
                'message': 'This is a test message.',
            },
        )
        assert response.status_code == 302

    def test_contact_form_missing_fields_returns_200(self, client):
        """Contact form with missing fields should return 200."""
        response = client.post(
            reverse('core:contact'),
            {
                'name': 'Test User',
                'email': '',  # Missing email
                'subject': 'question',
                'message': 'This is a test message.',
            },
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestHealthCheck:
    """Tests for the health check endpoint."""

    def test_health_check_returns_200(self, client):
        """Health check should return 200 status code."""
        response = client.get('/health/')
        assert response.status_code == 200

    def test_health_check_contains_ok(self, client):
        """Health check response should contain OK."""
        response = client.get('/health/')
        assert b'OK' in response.content
