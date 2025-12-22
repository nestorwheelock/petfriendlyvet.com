"""Tests for T-013 Chat History Persistence.

Tests validate conversation and message persistence:
- Messages saved correctly
- Conversation context builds
- Session linking works
- History retrieval works
- Export generates valid data
"""
import pytest
from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()


@pytest.mark.django_db
class TestConversationModel:
    """Test Conversation model."""

    def test_conversation_model_exists(self):
        """Conversation model should exist."""
        from apps.ai_assistant.models import Conversation
        assert Conversation is not None

    def test_conversation_has_session_id(self):
        """Conversation should have session_id field."""
        from apps.ai_assistant.models import Conversation
        conv = Conversation(session_id='test_session')
        assert conv.session_id == 'test_session'

    def test_conversation_has_language(self):
        """Conversation should have language field."""
        from apps.ai_assistant.models import Conversation
        conv = Conversation(session_id='test', language='en')
        assert conv.language == 'en'

    def test_conversation_has_timestamps(self):
        """Conversation should have created_at and updated_at."""
        from apps.ai_assistant.models import Conversation
        fields = [f.name for f in Conversation._meta.get_fields()]
        assert 'created_at' in fields
        assert 'updated_at' in fields


@pytest.mark.django_db
class TestMessageModel:
    """Test Message model."""

    def test_message_model_exists(self):
        """Message model should exist."""
        from apps.ai_assistant.models import Message
        assert Message is not None

    def test_message_has_role_choices(self):
        """Message should have role with choices."""
        from apps.ai_assistant.models import Message
        roles = [r[0] for r in Message.ROLES]
        assert 'user' in roles
        assert 'assistant' in roles
        assert 'system' in roles

    def test_message_has_tool_calls_field(self):
        """Message should have tool_calls JSONField."""
        from apps.ai_assistant.models import Message
        fields = [f.name for f in Message._meta.get_fields()]
        assert 'tool_calls' in fields


@pytest.mark.django_db
class TestMessagePersistence:
    """Test message saving and retrieval."""

    @pytest.fixture
    def conversation(self):
        from apps.ai_assistant.models import Conversation
        return Conversation.objects.create(session_id='test_persist')

    def test_message_saves_to_conversation(self, conversation):
        """Messages should save to conversation."""
        from apps.ai_assistant.models import Message
        msg = Message.objects.create(
            conversation=conversation,
            role='user',
            content='Hello'
        )
        assert msg.id is not None
        assert msg.conversation == conversation

    def test_messages_ordered_by_created_at(self, conversation):
        """Messages should be ordered by created_at."""
        from apps.ai_assistant.models import Message
        import time
        Message.objects.create(conversation=conversation, role='user', content='First')
        time.sleep(0.01)
        Message.objects.create(conversation=conversation, role='assistant', content='Second')

        messages = list(conversation.messages.all())
        assert messages[0].content == 'First'
        assert messages[1].content == 'Second'


@pytest.mark.django_db
class TestConversationContext:
    """Test conversation context building."""

    @pytest.fixture
    def conversation_with_messages(self):
        from apps.ai_assistant.models import Conversation, Message
        conv = Conversation.objects.create(session_id='test_context')
        Message.objects.create(conversation=conv, role='user', content='Hello')
        Message.objects.create(conversation=conv, role='assistant', content='Hi there!')
        Message.objects.create(conversation=conv, role='user', content='How are you?')
        return conv

    def test_get_conversation_context_exists(self):
        """get_conversation_context function should exist."""
        from apps.ai_assistant.utils import get_conversation_context
        assert callable(get_conversation_context)

    def test_context_returns_messages(self, conversation_with_messages):
        """Context should return messages in order."""
        from apps.ai_assistant.utils import get_conversation_context
        context = get_conversation_context(conversation_with_messages)
        assert len(context) == 3
        assert context[0]['role'] == 'user'
        assert context[0]['content'] == 'Hello'

    def test_context_respects_max_messages(self, conversation_with_messages):
        """Context should respect max_messages limit."""
        from apps.ai_assistant.utils import get_conversation_context
        context = get_conversation_context(conversation_with_messages, max_messages=2)
        assert len(context) == 2


@pytest.mark.django_db
class TestSessionLinking:
    """Test session-to-user linking."""

    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='linktest',
            email='link@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def anonymous_conversation(self):
        from apps.ai_assistant.models import Conversation
        return Conversation.objects.create(
            session_id='anonymous_session',
            user=None
        )

    def test_link_session_to_user_exists(self):
        """link_session_to_user function should exist."""
        from apps.ai_assistant.utils import link_session_to_user
        assert callable(link_session_to_user)

    def test_link_session_updates_conversation(self, anonymous_conversation, user):
        """Linking should update conversation user."""
        from apps.ai_assistant.utils import link_session_to_user
        link_session_to_user('anonymous_session', user)
        anonymous_conversation.refresh_from_db()
        assert anonymous_conversation.user == user


@pytest.mark.django_db
class TestHistoryAPI:
    """Test history retrieval API."""

    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='historyuser',
            email='history@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def user_conversation(self, user):
        from apps.ai_assistant.models import Conversation, Message
        conv = Conversation.objects.create(session_id='user_conv', user=user)
        Message.objects.create(conversation=conv, role='user', content='Test')
        Message.objects.create(conversation=conv, role='assistant', content='Response')
        return conv

    def test_user_conversations_endpoint_exists(self):
        """User conversations endpoint should exist."""
        from django.urls import reverse
        url = reverse('ai_assistant:user_conversations')
        assert url is not None

    def test_user_conversations_requires_auth(self, client):
        """User conversations should require authentication."""
        from django.urls import reverse
        url = reverse('ai_assistant:user_conversations')
        response = client.get(url)
        assert response.status_code in [302, 403]

    def test_user_gets_own_conversations(self, client, user, user_conversation):
        """User should see their own conversations."""
        from django.urls import reverse
        client.force_login(user)
        url = reverse('ai_assistant:user_conversations')
        response = client.get(url, HTTP_ACCEPT='application/json')
        assert response.status_code == 200
        data = response.json()
        assert 'conversations' in data
        assert len(data['conversations']) >= 1


@pytest.mark.django_db
class TestConversationExport:
    """Test conversation export functionality."""

    @pytest.fixture
    def conversation_with_messages(self):
        from apps.ai_assistant.models import Conversation, Message
        conv = Conversation.objects.create(session_id='export_test')
        Message.objects.create(conversation=conv, role='user', content='Export test')
        Message.objects.create(conversation=conv, role='assistant', content='Response')
        return conv

    def test_export_conversation_function_exists(self):
        """export_conversation function should exist."""
        from apps.ai_assistant.utils import export_conversation
        assert callable(export_conversation)

    def test_export_returns_valid_data(self, conversation_with_messages):
        """Export should return valid conversation data."""
        from apps.ai_assistant.utils import export_conversation
        data = export_conversation(conversation_with_messages)
        assert 'session_id' in data
        assert 'messages' in data
        assert len(data['messages']) == 2


@pytest.mark.django_db
class TestConversationContinuation:
    """Test conversation continuation."""

    @pytest.fixture
    def existing_conversation(self):
        from apps.ai_assistant.models import Conversation, Message
        conv = Conversation.objects.create(session_id='continue_test')
        Message.objects.create(conversation=conv, role='user', content='Previous message')
        Message.objects.create(conversation=conv, role='assistant', content='Previous response')
        return conv

    def test_continue_conversation_adds_message(self, client, existing_conversation):
        """Continuing conversation should add new messages."""
        from django.urls import reverse
        url = reverse('ai_assistant:chat')
        response = client.post(
            url,
            {
                'message': 'Follow up question',
                'session_id': 'continue_test'
            },
            content_type='application/json'
        )
        # Either success or fallback (no API key)
        assert response.status_code in [200, 500]
        existing_conversation.refresh_from_db()
        # Should have at least one more message
        assert existing_conversation.messages.count() >= 3
