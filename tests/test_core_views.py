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
class TestContactFormSubmission:
    """Tests for contact form submission and storage (T-070)."""

    def test_contact_submission_model_exists(self):
        """ContactSubmission model should exist."""
        from apps.core.models import ContactSubmission
        assert ContactSubmission is not None

    def test_contact_submission_created_on_valid_post(self, client):
        """Valid form submission should create ContactSubmission record."""
        from apps.core.models import ContactSubmission

        initial_count = ContactSubmission.objects.count()
        client.post(
            reverse('core:contact'),
            {
                'name': 'Test User',
                'email': 'test@example.com',
                'phone': '+521234567890',
                'subject': 'question',
                'message': 'This is a test message.',
            },
        )
        assert ContactSubmission.objects.count() == initial_count + 1

    def test_contact_submission_stores_correct_data(self, client):
        """ContactSubmission should store the submitted data correctly."""
        from apps.core.models import ContactSubmission

        client.post(
            reverse('core:contact'),
            {
                'name': 'Jane Doe',
                'email': 'jane@example.com',
                'phone': '+521234567890',
                'subject': 'pricing',
                'message': 'What are your prices?',
            },
        )
        submission = ContactSubmission.objects.latest('created_at')
        assert submission.name == 'Jane Doe'
        assert submission.email == 'jane@example.com'
        assert submission.subject == 'pricing'
        assert 'prices' in submission.message

    def test_contact_submission_stores_ip_address(self, client):
        """ContactSubmission should store the client IP address."""
        from apps.core.models import ContactSubmission

        client.post(
            reverse('core:contact'),
            {
                'name': 'Test User',
                'email': 'test@example.com',
                'subject': 'question',
                'message': 'Hello',
            },
        )
        submission = ContactSubmission.objects.latest('created_at')
        assert submission.ip_address is not None

    def test_honeypot_field_prevents_spam(self, client):
        """Filling honeypot field should silently reject submission."""
        from apps.core.models import ContactSubmission

        initial_count = ContactSubmission.objects.count()
        response = client.post(
            reverse('core:contact'),
            {
                'name': 'Spammer',
                'email': 'spam@example.com',
                'subject': 'spam',
                'message': 'Buy now!',
                'website': 'http://spam.com',  # Honeypot field
            },
        )
        # Should appear successful but not save
        assert response.status_code == 302
        assert ContactSubmission.objects.count() == initial_count

    def test_email_sent_on_contact_submission(self, client, settings):
        """Email notification should be sent on submission."""
        from django.core import mail

        client.post(
            reverse('core:contact'),
            {
                'name': 'Test User',
                'email': 'test@example.com',
                'subject': 'question',
                'message': 'Test message',
            },
        )
        # Check email was sent (using locmem backend in tests)
        assert len(mail.outbox) >= 1


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
