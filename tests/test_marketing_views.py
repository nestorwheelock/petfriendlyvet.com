"""
Tests for Email Marketing Views (TDD)

Tests cover:
- Marketing Dashboard view (staff only)
- Campaign list and detail views
- Subscriber list view
- Template list view
- Segment list view
- Sequence list view
"""
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.email_marketing.models import (
    EmailCampaign, EmailTemplate, EmailSegment,
    NewsletterSubscription, AutomatedSequence
)

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
def regular_user():
    """Create a regular (non-staff) user."""
    return User.objects.create_user(
        username='regularuser',
        email='regular@test.com',
        password='testpass123',
        is_staff=False
    )


@pytest.fixture
def email_template():
    """Create an email template."""
    return EmailTemplate.objects.create(
        name='Welcome Email',
        template_type='welcome',
        subject='Welcome to Pet-Friendly Vet!',
        html_content='<h1>Welcome!</h1>',
        is_active=True
    )


@pytest.fixture
def email_segment():
    """Create an email segment."""
    return EmailSegment.objects.create(
        name='Active Customers',
        description='Customers who visited in the last 90 days',
        is_dynamic=True,
        is_active=True
    )


@pytest.fixture
def email_campaign(staff_user, email_template, email_segment):
    """Create an email campaign."""
    return EmailCampaign.objects.create(
        name='Monthly Newsletter',
        subject='Pet Care Tips for the Month',
        html_content='<h1>Newsletter</h1>',
        from_name='Pet-Friendly Vet',
        from_email='newsletter@petfriendlyvet.com',
        template=email_template,
        segment=email_segment,
        status='draft',
        created_by=staff_user
    )


@pytest.fixture
def newsletter_subscription():
    """Create a newsletter subscription."""
    return NewsletterSubscription.objects.create(
        email='subscriber@example.com',
        status='active',
        source='website'
    )


@pytest.fixture
def automated_sequence():
    """Create an automated sequence."""
    return AutomatedSequence.objects.create(
        name='Welcome Series',
        description='Onboarding email sequence',
        trigger_type='signup',
        is_active=True
    )


# =============================================================================
# Marketing Dashboard Tests
# =============================================================================

class TestMarketingDashboard:
    """Tests for the Marketing Dashboard view."""

    def test_dashboard_requires_authentication(self, client):
        """Anonymous users should be redirected to login."""
        url = reverse('marketing:dashboard')
        response = client.get(url)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_dashboard_requires_staff(self, client, regular_user):
        """Non-staff users should be denied access."""
        client.force_login(regular_user)
        url = reverse('marketing:dashboard')
        response = client.get(url)
        assert response.status_code == 403

    def test_dashboard_accessible_by_staff(self, client, staff_user):
        """Staff users should access the dashboard."""
        client.force_login(staff_user)
        url = reverse('marketing:dashboard')
        response = client.get(url)
        assert response.status_code == 200

    def test_dashboard_shows_stats(self, client, staff_user, email_campaign, newsletter_subscription):
        """Dashboard should show marketing statistics."""
        client.force_login(staff_user)
        url = reverse('marketing:dashboard')
        response = client.get(url)
        assert response.status_code == 200
        assert 'total_subscribers' in response.context
        assert 'total_campaigns' in response.context


# =============================================================================
# Campaign Tests
# =============================================================================

class TestCampaigns:
    """Tests for Campaign views."""

    def test_campaign_list_requires_staff(self, client, regular_user):
        """Non-staff users should be denied access."""
        client.force_login(regular_user)
        url = reverse('marketing:campaign_list')
        response = client.get(url)
        assert response.status_code == 403

    def test_campaign_list_shows_campaigns(self, client, staff_user, email_campaign):
        """Campaign list should show all campaigns."""
        client.force_login(staff_user)
        url = reverse('marketing:campaign_list')
        response = client.get(url)
        assert response.status_code == 200
        assert 'campaigns' in response.context
        assert email_campaign in response.context['campaigns']

    def test_campaign_detail_shows_info(self, client, staff_user, email_campaign):
        """Campaign detail should show campaign information."""
        client.force_login(staff_user)
        url = reverse('marketing:campaign_detail', kwargs={'pk': email_campaign.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert response.context['campaign'] == email_campaign

    def test_campaign_list_filter_by_status(self, client, staff_user, email_campaign):
        """Campaign list should filter by status."""
        client.force_login(staff_user)
        url = reverse('marketing:campaign_list') + '?status=draft'
        response = client.get(url)
        assert response.status_code == 200


# =============================================================================
# Subscriber Tests
# =============================================================================

class TestSubscribers:
    """Tests for Subscriber views."""

    def test_subscriber_list_requires_staff(self, client, regular_user):
        """Non-staff users should be denied access."""
        client.force_login(regular_user)
        url = reverse('marketing:subscriber_list')
        response = client.get(url)
        assert response.status_code == 403

    def test_subscriber_list_shows_subscribers(self, client, staff_user, newsletter_subscription):
        """Subscriber list should show all subscribers."""
        client.force_login(staff_user)
        url = reverse('marketing:subscriber_list')
        response = client.get(url)
        assert response.status_code == 200
        assert 'subscribers' in response.context
        assert newsletter_subscription in response.context['subscribers']

    def test_subscriber_list_filter_by_status(self, client, staff_user, newsletter_subscription):
        """Subscriber list should filter by status."""
        client.force_login(staff_user)
        url = reverse('marketing:subscriber_list') + '?status=active'
        response = client.get(url)
        assert response.status_code == 200


# =============================================================================
# Template Tests
# =============================================================================

class TestTemplates:
    """Tests for Template views."""

    def test_template_list_requires_staff(self, client, regular_user):
        """Non-staff users should be denied access."""
        client.force_login(regular_user)
        url = reverse('marketing:template_list')
        response = client.get(url)
        assert response.status_code == 403

    def test_template_list_shows_templates(self, client, staff_user, email_template):
        """Template list should show all templates."""
        client.force_login(staff_user)
        url = reverse('marketing:template_list')
        response = client.get(url)
        assert response.status_code == 200
        assert 'templates' in response.context
        assert email_template in response.context['templates']


# =============================================================================
# Segment Tests
# =============================================================================

class TestSegments:
    """Tests for Segment views."""

    def test_segment_list_requires_staff(self, client, regular_user):
        """Non-staff users should be denied access."""
        client.force_login(regular_user)
        url = reverse('marketing:segment_list')
        response = client.get(url)
        assert response.status_code == 403

    def test_segment_list_shows_segments(self, client, staff_user, email_segment):
        """Segment list should show all segments."""
        client.force_login(staff_user)
        url = reverse('marketing:segment_list')
        response = client.get(url)
        assert response.status_code == 200
        assert 'segments' in response.context
        assert email_segment in response.context['segments']


# =============================================================================
# Sequence Tests
# =============================================================================

class TestSequences:
    """Tests for Sequence views."""

    def test_sequence_list_requires_staff(self, client, regular_user):
        """Non-staff users should be denied access."""
        client.force_login(regular_user)
        url = reverse('marketing:sequence_list')
        response = client.get(url)
        assert response.status_code == 403

    def test_sequence_list_shows_sequences(self, client, staff_user, automated_sequence):
        """Sequence list should show all sequences."""
        client.force_login(staff_user)
        url = reverse('marketing:sequence_list')
        response = client.get(url)
        assert response.status_code == 200
        assert 'sequences' in response.context
        assert automated_sequence in response.context['sequences']
