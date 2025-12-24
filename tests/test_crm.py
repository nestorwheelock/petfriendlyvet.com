"""Tests for CRM (Customer Relationship Management) app (TDD first)."""
import pytest
from datetime import datetime, timedelta
from django.utils import timezone
from decimal import Decimal

from apps.accounts.models import User

pytestmark = pytest.mark.django_db


class TestOwnerProfileModel:
    """Tests for OwnerProfile model."""

    def test_create_owner_profile(self, user):
        """Test creating an owner profile."""
        from apps.crm.models import OwnerProfile

        profile = OwnerProfile.objects.create(
            user=user,
            preferred_language='es',
            preferred_contact_method='whatsapp',
            notes='VIP customer',
        )

        assert profile.user == user
        assert profile.preferred_language == 'es'
        assert profile.preferred_contact_method == 'whatsapp'

    def test_owner_profile_str(self, user):
        """Test string representation."""
        from apps.crm.models import OwnerProfile

        profile = OwnerProfile.objects.create(
            user=user,
            preferred_language='en',
        )

        assert user.email in str(profile) or user.first_name in str(profile)

    def test_owner_profile_marketing_preferences(self, user):
        """Test marketing preferences JSON field."""
        from apps.crm.models import OwnerProfile

        profile = OwnerProfile.objects.create(
            user=user,
            marketing_preferences={
                'email_promotions': True,
                'sms_reminders': True,
                'newsletter': False,
            }
        )

        assert profile.marketing_preferences['email_promotions'] is True
        assert profile.marketing_preferences['newsletter'] is False


class TestInteractionModel:
    """Tests for Interaction model (customer touchpoints)."""

    def test_create_interaction(self, user):
        """Test creating a customer interaction."""
        from apps.crm.models import OwnerProfile, Interaction

        profile = OwnerProfile.objects.create(user=user)

        interaction = Interaction.objects.create(
            owner_profile=profile,
            interaction_type='call',
            channel='phone',
            direction='inbound',
            subject='Question about vaccination',
            notes='Customer asked about puppy vaccination schedule',
        )

        assert interaction.owner_profile == profile
        assert interaction.interaction_type == 'call'
        assert interaction.channel == 'phone'

    def test_interaction_types(self, user):
        """Test various interaction types."""
        from apps.crm.models import OwnerProfile, Interaction

        profile = OwnerProfile.objects.create(user=user)

        types = ['call', 'email', 'chat', 'visit', 'sms', 'whatsapp']
        for itype in types:
            interaction = Interaction.objects.create(
                owner_profile=profile,
                interaction_type=itype,
                channel='phone',
                direction='outbound',
            )
            assert interaction.interaction_type == itype

    def test_interaction_ordering(self, user):
        """Test interactions are ordered by date descending."""
        from apps.crm.models import OwnerProfile, Interaction

        profile = OwnerProfile.objects.create(user=user)

        i1 = Interaction.objects.create(
            owner_profile=profile,
            interaction_type='call',
            channel='phone',
            direction='inbound',
        )
        i2 = Interaction.objects.create(
            owner_profile=profile,
            interaction_type='email',
            channel='email',
            direction='outbound',
        )

        interactions = list(Interaction.objects.filter(owner_profile=profile))
        assert interactions[0] == i2  # Most recent first


class TestCustomerSegmentModel:
    """Tests for CustomerSegment model."""

    def test_create_segment(self):
        """Test creating a customer segment."""
        from apps.crm.models import CustomerSegment

        segment = CustomerSegment.objects.create(
            name='VIP Customers',
            description='High-value repeat customers',
            criteria={
                'min_total_spent': 5000,
                'min_visits': 10,
            },
            is_active=True,
        )

        assert segment.name == 'VIP Customers'
        assert segment.criteria['min_total_spent'] == 5000

    def test_segment_types(self):
        """Test segment types."""
        from apps.crm.models import CustomerSegment

        segments = [
            ('VIP', {'min_spent': 5000}),
            ('New Customers', {'days_since_first_visit': 30}),
            ('At Risk', {'days_since_last_visit': 180}),
            ('Dog Owners', {'pet_species': 'dog'}),
        ]

        for name, criteria in segments:
            segment = CustomerSegment.objects.create(
                name=name,
                criteria=criteria,
            )
            assert segment.name == name


class TestCustomerTagModel:
    """Tests for CustomerTag model."""

    def test_create_tag(self):
        """Test creating a customer tag."""
        from apps.crm.models import CustomerTag

        tag = CustomerTag.objects.create(
            name='Breeder',
            color='#FF5733',
            description='Professional dog/cat breeder',
        )

        assert tag.name == 'Breeder'
        assert tag.color == '#FF5733'

    def test_tag_to_profile(self, user):
        """Test adding tags to owner profile."""
        from apps.crm.models import OwnerProfile, CustomerTag

        profile = OwnerProfile.objects.create(user=user)
        tag1 = CustomerTag.objects.create(name='VIP')
        tag2 = CustomerTag.objects.create(name='Rescue Partner')

        profile.tags.add(tag1, tag2)

        assert tag1 in profile.tags.all()
        assert tag2 in profile.tags.all()
        assert profile.tags.count() == 2


class TestCustomerNoteModel:
    """Tests for CustomerNote model."""

    def test_create_note(self, user, staff_user):
        """Test creating a customer note."""
        from apps.crm.models import OwnerProfile, CustomerNote

        profile = OwnerProfile.objects.create(user=user)

        note = CustomerNote.objects.create(
            owner_profile=profile,
            author=staff_user,
            content='Customer prefers morning appointments',
            is_pinned=True,
        )

        assert note.owner_profile == profile
        assert note.author == staff_user
        assert note.is_pinned is True

    def test_notes_ordering(self, user, staff_user):
        """Test notes are ordered by pinned first, then date."""
        from apps.crm.models import OwnerProfile, CustomerNote

        profile = OwnerProfile.objects.create(user=user)

        n1 = CustomerNote.objects.create(
            owner_profile=profile,
            author=staff_user,
            content='First note',
            is_pinned=False,
        )
        n2 = CustomerNote.objects.create(
            owner_profile=profile,
            author=staff_user,
            content='Pinned note',
            is_pinned=True,
        )

        notes = list(CustomerNote.objects.filter(owner_profile=profile))
        assert notes[0] == n2  # Pinned first


class TestCRMAITools:
    """Tests for CRM AI tools."""

    def test_get_customer_profile_tool_exists(self):
        """Test get_customer_profile tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('get_customer_profile')
        assert tool is not None

    def test_get_customer_profile(self, user):
        """Test getting customer profile."""
        from apps.ai_assistant.tools import get_customer_profile
        from apps.crm.models import OwnerProfile

        OwnerProfile.objects.create(
            user=user,
            preferred_language='es',
            notes='Test notes',
        )

        result = get_customer_profile(user_id=user.id)

        assert result['success'] is True
        assert result['preferred_language'] == 'es'

    def test_add_customer_note_tool_exists(self):
        """Test add_customer_note tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('add_customer_note')
        assert tool is not None

    def test_add_customer_note(self, user, staff_user):
        """Test adding a note to customer profile."""
        from apps.ai_assistant.tools import add_customer_note
        from apps.crm.models import OwnerProfile

        OwnerProfile.objects.create(user=user)

        result = add_customer_note(
            user_id=user.id,
            note='Customer mentioned they are moving soon',
            author_id=staff_user.id,
        )

        assert result['success'] is True
        assert 'note_id' in result

    def test_log_interaction_tool_exists(self):
        """Test log_interaction tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('log_interaction')
        assert tool is not None

    def test_log_interaction(self, user):
        """Test logging a customer interaction."""
        from apps.ai_assistant.tools import log_interaction
        from apps.crm.models import OwnerProfile

        OwnerProfile.objects.create(user=user)

        result = log_interaction(
            user_id=user.id,
            interaction_type='call',
            channel='phone',
            direction='inbound',
            subject='Appointment inquiry',
            notes='Customer wants to schedule a checkup',
        )

        assert result['success'] is True
        assert 'interaction_id' in result

    def test_get_customer_history_tool_exists(self):
        """Test get_customer_history tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('get_customer_history')
        assert tool is not None

    def test_get_customer_history(self, user):
        """Test getting customer interaction history."""
        from apps.ai_assistant.tools import get_customer_history
        from apps.crm.models import OwnerProfile, Interaction

        profile = OwnerProfile.objects.create(user=user)
        Interaction.objects.create(
            owner_profile=profile,
            interaction_type='visit',
            channel='in_person',
            direction='inbound',
            subject='Annual checkup',
        )

        result = get_customer_history(user_id=user.id)

        assert result['success'] is True
        assert result['interaction_count'] >= 1

    def test_search_customers_tool_exists(self):
        """Test search_customers tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('search_customers')
        assert tool is not None

    def test_search_customers(self, user):
        """Test searching customers."""
        from apps.ai_assistant.tools import search_customers
        from apps.crm.models import OwnerProfile

        OwnerProfile.objects.create(user=user)

        result = search_customers(query=user.email[:5])

        assert result['success'] is True
        assert 'customers' in result

    def test_tag_customer_tool_exists(self):
        """Test tag_customer tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('tag_customer')
        assert tool is not None

    def test_tag_customer(self, user):
        """Test tagging a customer."""
        from apps.ai_assistant.tools import tag_customer
        from apps.crm.models import OwnerProfile, CustomerTag

        OwnerProfile.objects.create(user=user)
        tag = CustomerTag.objects.create(name='VIP')

        result = tag_customer(user_id=user.id, tag_name='VIP')

        assert result['success'] is True


class TestCRMIntegration:
    """Integration tests for CRM."""

    def test_full_customer_journey(self, user, staff_user):
        """Test complete customer journey tracking."""
        from apps.crm.models import OwnerProfile, Interaction, CustomerNote, CustomerTag
        from apps.ai_assistant.tools import (
            get_customer_profile, log_interaction, add_customer_note
        )

        # Create profile
        profile = OwnerProfile.objects.create(
            user=user,
            preferred_language='es',
            preferred_contact_method='whatsapp',
        )

        # Log first interaction
        log_interaction(
            user_id=user.id,
            interaction_type='call',
            channel='phone',
            direction='inbound',
            subject='New customer inquiry',
        )

        # Add note
        add_customer_note(
            user_id=user.id,
            note='Interested in puppy package',
            author_id=staff_user.id,
        )

        # Tag customer
        CustomerTag.objects.create(name='New Customer')
        profile.tags.add(CustomerTag.objects.get(name='New Customer'))

        # Verify everything
        result = get_customer_profile(user_id=user.id)
        assert result['success'] is True

        interactions = Interaction.objects.filter(owner_profile=profile)
        assert interactions.count() == 1

        notes = CustomerNote.objects.filter(owner_profile=profile)
        assert notes.count() == 1


# Fixtures
@pytest.fixture
def user():
    """Create a test user."""
    return User.objects.create_user(
        username='crmuser',
        email='crm@example.com',
        password='testpass123',
        first_name='CRM',
        last_name='User',
    )


@pytest.fixture
def staff_user():
    """Create a staff user."""
    return User.objects.create_user(
        username='staffuser',
        email='staff@example.com',
        password='testpass123',
        first_name='Staff',
        last_name='Member',
        is_staff=True,
    )
