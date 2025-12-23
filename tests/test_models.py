"""Tests for model coverage - string representations and properties."""
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserModelProperties:
    """Test User model role properties."""

    def test_is_pet_owner_true(self):
        """Test is_pet_owner returns True for owner role."""
        user = User.objects.create_user(
            username='owner_test',
            email='owner@example.com',
            password='testpass123',
            role='owner'
        )
        assert user.is_pet_owner is True

    def test_is_pet_owner_false(self):
        """Test is_pet_owner returns False for non-owner role."""
        user = User.objects.create_user(
            username='staff_test',
            email='staff@example.com',
            password='testpass123',
            role='staff'
        )
        assert user.is_pet_owner is False

    def test_is_staff_member_true_for_staff(self):
        """Test is_staff_member returns True for staff role."""
        user = User.objects.create_user(
            username='staff_test2',
            email='staff2@example.com',
            password='testpass123',
            role='staff'
        )
        assert user.is_staff_member is True

    def test_is_staff_member_true_for_vet(self):
        """Test is_staff_member returns True for vet role."""
        user = User.objects.create_user(
            username='vet_test',
            email='vet@example.com',
            password='testpass123',
            role='vet'
        )
        assert user.is_staff_member is True

    def test_is_staff_member_true_for_admin(self):
        """Test is_staff_member returns True for admin role."""
        user = User.objects.create_user(
            username='admin_test',
            email='admin@example.com',
            password='testpass123',
            role='admin'
        )
        assert user.is_staff_member is True

    def test_is_staff_member_false_for_owner(self):
        """Test is_staff_member returns False for owner role."""
        user = User.objects.create_user(
            username='owner_test2',
            email='owner2@example.com',
            password='testpass123',
            role='owner'
        )
        assert user.is_staff_member is False

    def test_is_veterinarian_true(self):
        """Test is_veterinarian returns True for vet role."""
        user = User.objects.create_user(
            username='vet_test2',
            email='vet2@example.com',
            password='testpass123',
            role='vet'
        )
        assert user.is_veterinarian is True

    def test_is_veterinarian_false(self):
        """Test is_veterinarian returns False for non-vet role."""
        user = User.objects.create_user(
            username='owner_test3',
            email='owner3@example.com',
            password='testpass123',
            role='owner'
        )
        assert user.is_veterinarian is False


@pytest.mark.django_db
class TestAIAssistantModelStrings:
    """Test AI assistant model __str__ methods."""

    def test_ai_usage_str(self):
        """Test AIUsage string representation."""
        from apps.ai_assistant.models import AIUsage
        from decimal import Decimal

        usage = AIUsage.objects.create(
            model='claude-3-sonnet',
            input_tokens=100,
            output_tokens=200,
            cost_usd=Decimal('0.001500'),
            session_id='test-session'
        )
        expected = 'claude-3-sonnet - 100+200 tokens'
        assert str(usage) == expected

    def test_conversation_str(self):
        """Test Conversation string representation."""
        from apps.ai_assistant.models import Conversation

        conv = Conversation.objects.create(
            session_id='abc12345xyz',
            title='Test Chat'
        )
        assert 'abc12345' in str(conv)
        assert 'Test Chat' in str(conv)

    def test_conversation_str_untitled(self):
        """Test Conversation string without title."""
        from apps.ai_assistant.models import Conversation

        conv = Conversation.objects.create(
            session_id='def67890uvw'
        )
        assert 'def67890' in str(conv)
        assert 'Untitled' in str(conv)

    def test_message_str(self):
        """Test Message string representation."""
        from apps.ai_assistant.models import Conversation, Message

        conv = Conversation.objects.create(session_id='msg_test_123')
        msg = Message.objects.create(
            conversation=conv,
            role='user',
            content='Hello, this is a test message that is longer than fifty characters to test truncation'
        )
        result = str(msg)
        assert result.startswith('user:')
        assert '...' in result


