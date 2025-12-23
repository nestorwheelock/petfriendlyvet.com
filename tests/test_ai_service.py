"""Tests for AI service."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from django.contrib.auth import get_user_model

from apps.ai_assistant.services import AIService

User = get_user_model()


class TestAIService:
    """Tests for AIService class."""

    def test_init_defaults(self):
        """Test service initialization with defaults."""
        service = AIService()

        assert service.user is None
        assert service.language == 'es'
        assert service.conversation is None
        assert service.client is not None

    def test_init_with_user_and_language(self, django_user_model):
        """Test service initialization with user and language."""
        user = django_user_model.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        service = AIService(user=user, language='en')

        assert service.user == user
        assert service.language == 'en'

    def test_build_system_prompt_spanish(self):
        """Test Spanish system prompt."""
        service = AIService(language='es')
        prompt = service.build_system_prompt()

        assert 'Veterinaria Pet-Friendly' in prompt
        assert 'Puerto Morelos' in prompt
        assert 'Martes-Domingo' in prompt

    def test_build_system_prompt_english(self):
        """Test English system prompt."""
        service = AIService(language='en')
        prompt = service.build_system_prompt()

        assert 'Pet-Friendly Veterinary Clinic' in prompt
        assert 'Puerto Morelos' in prompt
        assert 'Tuesday-Sunday' in prompt

    @pytest.mark.asyncio
    async def test_get_response_success(self):
        """Test successful AI response."""
        service = AIService(language='en')

        mock_response = {
            'choices': [{'message': {'content': 'Hello! How can I help?'}}]
        }

        with patch.object(service.client, 'chat', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_response

            response = await service.get_response('Hello')

            assert response == 'Hello! How can I help?'
            mock_chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_response_api_error(self):
        """Test fallback on API error."""
        service = AIService(language='en')

        mock_response = {'error': True, 'message': 'API error'}

        with patch.object(service.client, 'chat', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_response

            response = await service.get_response('Hello')

            assert 'trouble connecting' in response
            assert '+52 998 316 2438' in response

    @pytest.mark.asyncio
    async def test_get_response_malformed_response(self):
        """Test fallback on malformed response."""
        service = AIService(language='es')

        mock_response = {'something': 'else'}

        with patch.object(service.client, 'chat', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_response

            response = await service.get_response('Hola')

            assert 'problemas para conectar' in response

    @pytest.mark.asyncio
    async def test_get_response_empty_choices(self):
        """Test fallback on empty choices."""
        service = AIService(language='en')

        mock_response = {'choices': []}

        with patch.object(service.client, 'chat', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_response

            response = await service.get_response('Hello')

            assert 'trouble connecting' in response

    def test_get_response_sync_success(self):
        """Test successful sync AI response."""
        service = AIService(language='en')

        mock_response = {
            'choices': [{'message': {'content': 'Hi there!'}}]
        }

        with patch.object(service.client, 'chat_sync') as mock_chat:
            mock_chat.return_value = mock_response

            response = service.get_response_sync('Hello')

            assert response == 'Hi there!'

    def test_get_response_sync_error(self):
        """Test sync fallback on error."""
        service = AIService(language='es')

        mock_response = {'error': True}

        with patch.object(service.client, 'chat_sync') as mock_chat:
            mock_chat.return_value = mock_response

            response = service.get_response_sync('Hola')

            assert 'problemas para conectar' in response

    def test_get_response_sync_malformed(self):
        """Test sync fallback on malformed response."""
        service = AIService(language='en')

        mock_response = {'choices': [{'message': {}}]}

        with patch.object(service.client, 'chat_sync') as mock_chat:
            mock_chat.return_value = mock_response

            response = service.get_response_sync('Hello')

            assert 'trouble connecting' in response

    def test_fallback_response_english(self):
        """Test English fallback message."""
        service = AIService(language='en')
        response = service._get_fallback_response()

        assert 'trouble connecting' in response
        assert '+52 998 316 2438' in response
        assert 'WhatsApp' in response

    def test_fallback_response_spanish(self):
        """Test Spanish fallback message."""
        service = AIService(language='es')
        response = service._get_fallback_response()

        assert 'problemas para conectar' in response
        assert '+52 998 316 2438' in response
        assert 'WhatsApp' in response

    def test_get_available_tools_anonymous(self):
        """Test tools for anonymous user."""
        service = AIService()
        tools = service.get_available_tools()

        assert len(tools) == 2
        tool_names = [t['function']['name'] for t in tools]
        assert 'get_business_hours' in tool_names
        assert 'get_services' in tool_names
        assert 'schedule_appointment' not in tool_names

    def test_get_available_tools_authenticated(self, django_user_model):
        """Test tools for authenticated user."""
        user = django_user_model.objects.create_user(
            username='authuser',
            email='auth@example.com',
            password='testpass123'
        )
        service = AIService(user=user)
        tools = service.get_available_tools()

        assert len(tools) == 3
        tool_names = [t['function']['name'] for t in tools]
        assert 'get_business_hours' in tool_names
        assert 'get_services' in tool_names
        assert 'schedule_appointment' in tool_names

    def test_get_available_tools_unauthenticated_user(self):
        """Test tools for user object that is not authenticated."""
        mock_user = MagicMock()
        mock_user.is_authenticated = False

        service = AIService(user=mock_user)
        tools = service.get_available_tools()

        assert len(tools) == 2
        tool_names = [t['function']['name'] for t in tools]
        assert 'schedule_appointment' not in tool_names
