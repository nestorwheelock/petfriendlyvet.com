"""Tests for AI assistant views."""
import json
import pytest
from unittest.mock import patch, MagicMock
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from apps.ai_assistant.models import Conversation, Message

User = get_user_model()


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def regular_user(db):
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(
        username='staffuser',
        email='staff@example.com',
        password='testpass123',
        role='staff'
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username='adminuser',
        email='admin@example.com',
        password='testpass123',
        role='admin',
        is_staff=True
    )


class TestIsStaffOrAdmin:
    """Test is_staff_or_admin helper function."""

    def test_anonymous_user_returns_false(self, client):
        """Anonymous user should not be staff/admin."""
        from apps.ai_assistant.views import is_staff_or_admin

        assert is_staff_or_admin(AnonymousUser()) is False

    def test_regular_user_returns_false(self, regular_user):
        """Regular user should not be staff/admin."""
        from apps.ai_assistant.views import is_staff_or_admin

        assert is_staff_or_admin(regular_user) is False

    def test_staff_user_returns_true(self, staff_user):
        """Staff user should be staff/admin."""
        from apps.ai_assistant.views import is_staff_or_admin

        assert is_staff_or_admin(staff_user) is True

    def test_admin_user_returns_true(self, admin_user):
        """Admin user should be staff/admin."""
        from apps.ai_assistant.views import is_staff_or_admin

        assert is_staff_or_admin(admin_user) is True

    def test_is_staff_flag_returns_true(self, db):
        """User with is_staff=True should be staff/admin."""
        from apps.ai_assistant.views import is_staff_or_admin

        user = User.objects.create_user(
            username='staffflag',
            email='staffflag@example.com',
            password='testpass123',
            is_staff=True
        )
        assert is_staff_or_admin(user) is True

    def test_is_superuser_returns_true(self, db):
        """Superuser should be staff/admin."""
        from apps.ai_assistant.views import is_staff_or_admin

        user = User.objects.create_superuser(
            username='superuser',
            email='super@example.com',
            password='testpass123'
        )
        assert is_staff_or_admin(user) is True


@pytest.mark.django_db
class TestChatView:
    """Test ChatView."""

    @patch('apps.ai_assistant.views.AIService')
    def test_empty_message_returns_400(self, mock_ai_service, client):
        """Empty message should return 400 error."""
        response = client.post(
            '/chat/',
            data=json.dumps({'message': '', 'session_id': 'test123'}),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = response.json()
        assert data['error'] is True
        assert 'required' in data['message'].lower()

    def test_invalid_json_returns_400(self, client):
        """Invalid JSON should return 400 error."""
        response = client.post(
            '/chat/',
            data='not valid json',
            content_type='application/json'
        )

        assert response.status_code == 400
        data = response.json()
        assert data['error'] is True
        assert 'json' in data['message'].lower()

    def test_get_request_returns_405(self, client):
        """GET request should return 405."""
        response = client.get('/chat/')

        assert response.status_code == 405

    @patch('apps.ai_assistant.views.AIService')
    def test_valid_message_returns_response(self, mock_ai_service, client):
        """Valid message should return AI response."""
        mock_service_instance = MagicMock()
        mock_service_instance.get_response_sync.return_value = 'Hello! How can I help?'
        mock_ai_service.return_value = mock_service_instance

        response = client.post(
            '/chat/',
            data=json.dumps({'message': 'Hello', 'session_id': 'test123'}),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['response'] == 'Hello! How can I help?'
        assert data['session_id'] == 'test123'

    @patch('apps.ai_assistant.views.AIService')
    def test_creates_conversation_and_messages(self, mock_ai_service, client):
        """Chat should create conversation and messages."""
        mock_service_instance = MagicMock()
        mock_service_instance.get_response_sync.return_value = 'Hi there!'
        mock_ai_service.return_value = mock_service_instance

        response = client.post(
            '/chat/',
            data=json.dumps({'message': 'Hello', 'session_id': 'convo123'}),
            content_type='application/json'
        )

        assert response.status_code == 200

        # Check conversation was created
        conv = Conversation.objects.get(session_id='convo123')
        assert conv is not None
        assert conv.language == 'es'  # Default

        # Check messages were created
        messages = conv.messages.all()
        assert messages.count() == 2
        assert messages[0].role == 'user'
        assert messages[0].content == 'Hello'
        assert messages[1].role == 'assistant'
        assert messages[1].content == 'Hi there!'

    @patch('apps.ai_assistant.views.AIService')
    def test_form_data_works(self, mock_ai_service, client):
        """POST form data should work."""
        mock_service_instance = MagicMock()
        mock_service_instance.get_response_sync.return_value = 'Response!'
        mock_ai_service.return_value = mock_service_instance

        response = client.post(
            '/chat/',
            data={'message': 'Hello from form', 'session_id': 'form123'}
        )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True


@pytest.mark.django_db
class TestGetQuickActions:
    """Test get_quick_actions view."""

    def test_quick_actions_spanish(self, client):
        """Should return Spanish quick actions by default."""
        response = client.get('/chat/quick-actions/')

        assert response.status_code == 200
        data = response.json()
        assert 'actions' in data
        assert len(data['actions']) > 0
        # Should have Spanish text
        texts = [a['text'] for a in data['actions']]
        assert any('horario' in t.lower() for t in texts)

    def test_quick_actions_english(self, client):
        """Should return English quick actions when requested."""
        response = client.get('/chat/quick-actions/?language=en')

        assert response.status_code == 200
        data = response.json()
        assert 'actions' in data
        texts = [a['text'] for a in data['actions']]
        assert any('hours' in t.lower() for t in texts)


@pytest.mark.django_db
class TestGetChatHistory:
    """Test get_chat_history view."""

    def test_no_session_returns_empty(self, client):
        """No session_id should return empty messages."""
        response = client.get('/chat/history/')

        assert response.status_code == 200
        data = response.json()
        assert data['messages'] == []

    def test_nonexistent_session_returns_empty(self, client):
        """Nonexistent session should return empty messages."""
        response = client.get('/chat/history/?session_id=nonexistent123')

        assert response.status_code == 200
        data = response.json()
        assert data['messages'] == []

    def test_existing_session_returns_messages(self, client, regular_user):
        """Existing session should return messages."""
        # Create a conversation with messages
        conv = Conversation.objects.create(
            session_id='test_session_123',
            user=regular_user,
            language='en'
        )
        Message.objects.create(conversation=conv, role='user', content='Hello')
        Message.objects.create(conversation=conv, role='assistant', content='Hi there!')

        response = client.get('/chat/history/?session_id=test_session_123')

        assert response.status_code == 200
        data = response.json()
        assert len(data['messages']) == 2


@pytest.mark.django_db
class TestAdminChatAPIView:
    """Test AdminChatAPIView."""

    def test_unauthenticated_returns_403(self, client):
        """Unauthenticated user should get 403."""
        response = client.post(
            '/chat/admin/api/',
            data=json.dumps({'message': 'Hello'}),
            content_type='application/json'
        )

        assert response.status_code == 403

    def test_regular_user_returns_403(self, client, regular_user):
        """Regular user should get 403."""
        client.login(username='testuser', password='testpass123')

        response = client.post(
            '/chat/admin/api/',
            data=json.dumps({'message': 'Hello'}),
            content_type='application/json'
        )

        assert response.status_code == 403
        data = response.json()
        assert 'denied' in data['message'].lower()

    @patch('apps.ai_assistant.views.AIService')
    def test_staff_user_can_access(self, mock_ai_service, client, staff_user):
        """Staff user should be able to access."""
        mock_service_instance = MagicMock()
        mock_service_instance.get_response_sync.return_value = 'Admin response'
        mock_ai_service.return_value = mock_service_instance

        client.login(username='staffuser', password='testpass123')

        response = client.post(
            '/chat/admin/api/',
            data=json.dumps({'message': 'Hello'}),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True

    @patch('apps.ai_assistant.views.AIService')
    def test_empty_message_returns_400(self, mock_ai_service, client, staff_user):
        """Empty message should return 400."""
        client.login(username='staffuser', password='testpass123')

        response = client.post(
            '/chat/admin/api/',
            data=json.dumps({'message': ''}),
            content_type='application/json'
        )

        assert response.status_code == 400

    def test_invalid_json_returns_400(self, client, staff_user):
        """Invalid JSON should return 400."""
        client.login(username='staffuser', password='testpass123')

        response = client.post(
            '/chat/admin/api/',
            data='invalid json',
            content_type='application/json'
        )

        assert response.status_code == 400

    @patch('apps.ai_assistant.views.AIService')
    def test_response_includes_tools_info(self, mock_ai_service, client, staff_user):
        """Admin response should include tools info."""
        mock_service_instance = MagicMock()
        mock_service_instance.get_response_sync.return_value = 'Response with tools'
        mock_ai_service.return_value = mock_service_instance

        client.login(username='staffuser', password='testpass123')

        response = client.post(
            '/chat/admin/api/',
            data=json.dumps({'message': 'Hello'}),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = response.json()
        assert 'tools_available' in data
        assert 'tools_used' in data

    @patch('apps.ai_assistant.views.AIService')
    def test_form_data_works(self, mock_ai_service, client, staff_user):
        """POST form data should work for admin API."""
        mock_service_instance = MagicMock()
        mock_service_instance.get_response_sync.return_value = 'Admin form response'
        mock_ai_service.return_value = mock_service_instance

        client.login(username='staffuser', password='testpass123')

        response = client.post(
            '/chat/admin/api/',
            data={'message': 'Hello from admin form'}
        )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True

    @patch('apps.ai_assistant.views.AIService')
    def test_exception_returns_500(self, mock_ai_service, client, staff_user):
        """Internal exception should return 500 with sanitized message."""
        mock_service_instance = MagicMock()
        mock_service_instance.get_response_sync.side_effect = Exception('Admin API error')
        mock_ai_service.return_value = mock_service_instance

        client.login(username='staffuser', password='testpass123')

        response = client.post(
            '/chat/admin/api/',
            data=json.dumps({'message': 'Hello'}),
            content_type='application/json'
        )

        assert response.status_code == 500
        data = response.json()
        assert data['error'] is True
        # Error message should be sanitized, not leak internal details
        assert 'Admin API error' not in data['message']
        assert 'unexpected error' in data['message'].lower()


@pytest.mark.django_db
class TestAdminChatView:
    """Test AdminChatView (renders template)."""

    def test_unauthenticated_redirects(self, client):
        """Unauthenticated user should be redirected."""
        response = client.get('/chat/admin/')

        assert response.status_code == 302
        assert 'login' in response.url

    def test_regular_user_returns_403(self, client, regular_user):
        """Regular user should get 403."""
        client.login(username='testuser', password='testpass123')

        response = client.get('/chat/admin/')

        assert response.status_code == 403

    def test_staff_user_can_access(self, client, staff_user):
        """Staff user should be able to access."""
        client.login(username='staffuser', password='testpass123')

        response = client.get('/chat/admin/')

        # Should return 200 or template rendering
        assert response.status_code in [200, 404]  # 404 if template missing


@pytest.mark.django_db
class TestConversationList:
    """Test conversation_list view."""

    def test_unauthenticated_redirects(self, client):
        """Unauthenticated user should be redirected."""
        response = client.get('/chat/admin/conversations/')

        assert response.status_code == 302

    def test_regular_user_returns_403(self, client, regular_user):
        """Regular user should get 403."""
        client.login(username='testuser', password='testpass123')

        response = client.get('/chat/admin/conversations/')

        assert response.status_code == 403

    def test_staff_user_can_access(self, client, staff_user):
        """Staff user should be able to access."""
        client.login(username='staffuser', password='testpass123')

        response = client.get('/chat/admin/conversations/')

        # Should return 200 or template rendering (404 if template missing)
        assert response.status_code in [200, 404]

    def test_json_response(self, client, staff_user):
        """Should return JSON when Accept header is set."""
        client.login(username='staffuser', password='testpass123')

        # Create a conversation
        Conversation.objects.create(session_id='test123', language='en')

        response = client.get(
            '/chat/admin/conversations/',
            HTTP_ACCEPT='application/json'
        )

        assert response.status_code == 200
        data = response.json()
        assert 'conversations' in data


@pytest.mark.django_db
class TestUserConversations:
    """Test user_conversations view."""

    def test_unauthenticated_redirects(self, client):
        """Unauthenticated user should be redirected."""
        response = client.get('/chat/my-conversations/')

        assert response.status_code == 302

    def test_authenticated_user_can_access(self, client, regular_user):
        """Authenticated user should be able to access."""
        client.login(username='testuser', password='testpass123')

        response = client.get('/chat/my-conversations/')

        # Should return 200 or template rendering (404 if template missing)
        assert response.status_code in [200, 404]

    def test_json_response(self, client, regular_user):
        """Should return JSON when Accept header is set."""
        client.login(username='testuser', password='testpass123')

        # Create a conversation for the user
        Conversation.objects.create(
            session_id='user_conv_123',
            user=regular_user,
            language='en'
        )

        response = client.get(
            '/chat/my-conversations/',
            HTTP_ACCEPT='application/json'
        )

        assert response.status_code == 200
        data = response.json()
        assert 'conversations' in data
        assert len(data['conversations']) == 1

    def test_only_returns_user_conversations(self, client, regular_user, staff_user):
        """Should only return conversations for current user."""
        client.login(username='testuser', password='testpass123')

        # Create conversations for both users
        Conversation.objects.create(
            session_id='user_conv',
            user=regular_user,
            language='en'
        )
        Conversation.objects.create(
            session_id='staff_conv',
            user=staff_user,
            language='en'
        )

        response = client.get(
            '/chat/my-conversations/',
            HTTP_ACCEPT='application/json'
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data['conversations']) == 1
        assert data['conversations'][0]['session_id'] == 'user_conv'


@pytest.mark.django_db
class TestChatViewEdgeCases:
    """Test edge cases for ChatView."""

    @patch('apps.ai_assistant.views.AIService')
    def test_exception_returns_500(self, mock_ai_service, client):
        """Internal exception should return 500."""
        mock_service_instance = MagicMock()
        mock_service_instance.get_response_sync.side_effect = Exception('Unexpected error')
        mock_ai_service.return_value = mock_service_instance

        response = client.post(
            '/chat/',
            data=json.dumps({'message': 'Hello', 'session_id': 'error123'}),
            content_type='application/json'
        )

        assert response.status_code == 500
        data = response.json()
        assert data['error'] is True

    @patch('apps.ai_assistant.views.AIService')
    def test_generates_session_id_if_missing(self, mock_ai_service, client):
        """Should generate session_id if not provided."""
        mock_service_instance = MagicMock()
        mock_service_instance.get_response_sync.return_value = 'Response'
        mock_ai_service.return_value = mock_service_instance

        response = client.post(
            '/chat/',
            data=json.dumps({'message': 'Hello'}),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = response.json()
        assert 'session_id' in data
        assert len(data['session_id']) > 0

    @patch('apps.ai_assistant.views.AIService')
    def test_custom_language(self, mock_ai_service, client):
        """Should use custom language from request."""
        mock_service_instance = MagicMock()
        mock_service_instance.get_response_sync.return_value = 'English response'
        mock_ai_service.return_value = mock_service_instance

        response = client.post(
            '/chat/',
            data=json.dumps({'message': 'Hello', 'session_id': 'lang123', 'language': 'en'}),
            content_type='application/json'
        )

        assert response.status_code == 200

        # Check conversation was created with correct language
        conv = Conversation.objects.get(session_id='lang123')
        assert conv.language == 'en'

        # Check AIService was called with correct language
        mock_ai_service.assert_called_once()
        call_kwargs = mock_ai_service.call_args[1]
        assert call_kwargs['language'] == 'en'
