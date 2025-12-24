"""Tests for Email Marketing app (TDD first)."""
import pytest
from django.utils import timezone

from apps.accounts.models import User

pytestmark = pytest.mark.django_db


class TestNewsletterSubscriptionModel:
    """Tests for NewsletterSubscription model."""

    def test_create_subscription(self):
        """Test creating a subscription."""
        from apps.email_marketing.models import NewsletterSubscription

        sub = NewsletterSubscription.objects.create(
            email='subscriber@example.com',
            source='website',
        )

        assert sub.status == 'pending'
        assert sub.confirmation_token != ''

    def test_subscription_with_user(self, user):
        """Test subscription linked to user."""
        from apps.email_marketing.models import NewsletterSubscription

        sub = NewsletterSubscription.objects.create(
            email=user.email,
            user=user,
            status='active',
        )

        assert sub.user == user


class TestEmailSegmentModel:
    """Tests for EmailSegment model."""

    def test_create_segment(self):
        """Test creating a segment."""
        from apps.email_marketing.models import EmailSegment

        segment = EmailSegment.objects.create(
            name='Dog Owners',
            rules=[{'field': 'pet_type', 'operator': 'equals', 'value': 'dog'}],
        )

        assert segment.is_dynamic is True
        assert len(segment.rules) == 1


class TestEmailTemplateModel:
    """Tests for EmailTemplate model."""

    def test_create_template(self):
        """Test creating a template."""
        from apps.email_marketing.models import EmailTemplate

        template = EmailTemplate.objects.create(
            name='Welcome Email',
            template_type='welcome',
            subject='Welcome to Pet Friendly!',
            html_content='<h1>Welcome {{name}}!</h1>',
        )

        assert template.template_type == 'welcome'
        assert template.is_active is True


class TestEmailCampaignModel:
    """Tests for EmailCampaign model."""

    def test_create_campaign(self, user):
        """Test creating a campaign."""
        from apps.email_marketing.models import EmailCampaign

        campaign = EmailCampaign.objects.create(
            name='Monthly Newsletter',
            subject='Pet Care Tips for December',
            html_content='<p>Newsletter content</p>',
            from_name='Pet Friendly',
            from_email='info@petfriendlyvet.com',
            created_by=user,
        )

        assert campaign.status == 'draft'
        assert campaign.open_rate == 0

    def test_campaign_stats(self, user):
        """Test campaign statistics."""
        from apps.email_marketing.models import EmailCampaign

        campaign = EmailCampaign.objects.create(
            name='Test Campaign',
            subject='Test',
            html_content='Content',
            from_name='Test',
            from_email='test@example.com',
            total_delivered=100,
            total_opened=25,
            total_clicked=10,
        )

        assert campaign.open_rate == 25.0
        assert campaign.click_rate == 10.0


class TestEmailSendModel:
    """Tests for EmailSend model."""

    def test_create_send(self, user):
        """Test creating an email send record."""
        from apps.email_marketing.models import (
            EmailCampaign, NewsletterSubscription, EmailSend
        )

        campaign = EmailCampaign.objects.create(
            name='Test',
            subject='Test',
            html_content='<p>Test</p>',
            from_name='Test',
            from_email='test@example.com',
        )
        sub = NewsletterSubscription.objects.create(
            email='test@example.com',
            status='active',
        )

        send = EmailSend.objects.create(
            campaign=campaign,
            subscription=sub,
            status='sent',
            sent_at=timezone.now(),
        )

        assert send.status == 'sent'


class TestAutomatedSequenceModel:
    """Tests for AutomatedSequence model."""

    def test_create_sequence(self):
        """Test creating an automated sequence."""
        from apps.email_marketing.models import AutomatedSequence

        sequence = AutomatedSequence.objects.create(
            name='Welcome Series',
            trigger_type='signup',
        )

        assert sequence.is_active is True
        assert sequence.trigger_type == 'signup'


class TestSequenceStepModel:
    """Tests for SequenceStep model."""

    def test_create_steps(self):
        """Test creating sequence steps."""
        from apps.email_marketing.models import (
            AutomatedSequence, EmailTemplate, SequenceStep
        )

        sequence = AutomatedSequence.objects.create(
            name='Welcome Series',
            trigger_type='signup',
        )
        template = EmailTemplate.objects.create(
            name='Welcome 1',
            template_type='welcome',
            subject='Welcome!',
            html_content='<p>Welcome</p>',
        )

        step1 = SequenceStep.objects.create(
            sequence=sequence,
            step_number=1,
            template=template,
            delay_days=0,
        )
        step2 = SequenceStep.objects.create(
            sequence=sequence,
            step_number=2,
            template=template,
            delay_days=3,
        )

        assert sequence.steps.count() == 2


class TestEmailMarketingAITools:
    """Tests for Email Marketing AI tools."""

    def test_subscribe_newsletter_tool_exists(self):
        """Test subscribe_newsletter tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('subscribe_newsletter')
        assert tool is not None

    def test_subscribe_newsletter(self):
        """Test subscribing to newsletter."""
        from apps.ai_assistant.tools import subscribe_newsletter

        result = subscribe_newsletter(
            email='new@example.com',
            source='ai_chat',
        )

        assert result['success'] is True
        assert 'subscription_id' in result

    def test_get_email_campaigns_tool_exists(self):
        """Test get_email_campaigns tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('get_email_campaigns')
        assert tool is not None

    def test_get_email_campaigns(self, user):
        """Test getting campaigns."""
        from apps.ai_assistant.tools import get_email_campaigns
        from apps.email_marketing.models import EmailCampaign

        EmailCampaign.objects.create(
            name='Test Campaign',
            subject='Test',
            html_content='<p>Test</p>',
            from_name='Test',
            from_email='test@example.com',
            status='sent',
        )

        result = get_email_campaigns()

        assert result['success'] is True
        assert result['count'] >= 1

    def test_create_campaign_tool_exists(self):
        """Test create_campaign tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('create_email_campaign')
        assert tool is not None

    def test_create_campaign(self, user):
        """Test creating a campaign."""
        from apps.ai_assistant.tools import create_email_campaign

        result = create_email_campaign(
            name='New Campaign',
            subject='Test Subject',
            html_content='<p>Content</p>',
            from_name='Pet Friendly',
            from_email='info@petfriendlyvet.com',
        )

        assert result['success'] is True
        assert 'campaign_id' in result

    def test_get_campaign_stats_tool_exists(self):
        """Test get_campaign_stats tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('get_campaign_stats')
        assert tool is not None


# Fixtures
@pytest.fixture
def user():
    """Create a test user."""
    return User.objects.create_user(
        username='emailuser',
        email='email@example.com',
        password='testpass123',
        first_name='Email',
        last_name='User',
    )
