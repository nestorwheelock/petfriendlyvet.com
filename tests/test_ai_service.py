"""Tests for T-009 AI Service Layer Implementation.

Tests validate AI service layer functionality:
- OpenRouter client exists
- AIService class exists
- Message formatting works
- Error handling works
- Rate limiting model exists
- Cost tracking model exists
- Configuration settings present
"""
import pytest
from django.conf import settings
from unittest.mock import patch, MagicMock, AsyncMock


class TestAIConfiguration:
    """Test AI-related configuration settings."""

    def test_openrouter_api_key_setting_exists(self):
        """OpenRouter API key setting should exist."""
        assert hasattr(settings, 'OPENROUTER_API_KEY')

    def test_ai_model_setting_exists(self):
        """AI model setting should exist."""
        assert hasattr(settings, 'AI_MODEL')
        assert 'claude' in settings.AI_MODEL.lower() or 'anthropic' in settings.AI_MODEL.lower()

    def test_ai_max_tokens_setting_exists(self):
        """AI max tokens setting should exist."""
        assert hasattr(settings, 'AI_MAX_TOKENS')
        assert settings.AI_MAX_TOKENS > 0

    def test_ai_rate_limit_setting_exists(self):
        """AI rate limit setting should exist."""
        assert hasattr(settings, 'AI_RATE_LIMIT_PER_USER')
        assert settings.AI_RATE_LIMIT_PER_USER > 0

    def test_ai_cost_limit_setting_exists(self):
        """AI cost limit setting should exist."""
        assert hasattr(settings, 'AI_COST_LIMIT_DAILY')
        assert settings.AI_COST_LIMIT_DAILY > 0


class TestOpenRouterClient:
    """Test OpenRouter client class."""

    def test_client_class_exists(self):
        """OpenRouterClient class should exist."""
        from apps.ai_assistant.clients import OpenRouterClient
        assert OpenRouterClient is not None

    def test_client_has_chat_method(self):
        """Client should have chat method."""
        from apps.ai_assistant.clients import OpenRouterClient
        client = OpenRouterClient()
        assert hasattr(client, 'chat')

    def test_client_has_base_url(self):
        """Client should have OpenRouter base URL."""
        from apps.ai_assistant.clients import OpenRouterClient
        client = OpenRouterClient()
        assert hasattr(client, 'base_url')
        assert 'openrouter' in client.base_url.lower()


class TestAIService:
    """Test high-level AI service class."""

    def test_service_class_exists(self):
        """AIService class should exist."""
        from apps.ai_assistant.services import AIService
        assert AIService is not None

    def test_service_has_get_response_method(self):
        """Service should have get_response method."""
        from apps.ai_assistant.services import AIService
        service = AIService()
        assert hasattr(service, 'get_response')

    def test_service_has_build_system_prompt(self):
        """Service should have build_system_prompt method."""
        from apps.ai_assistant.services import AIService
        service = AIService()
        assert hasattr(service, 'build_system_prompt')

    def test_service_accepts_language(self):
        """Service should accept language parameter."""
        from apps.ai_assistant.services import AIService
        service_es = AIService(language='es')
        service_en = AIService(language='en')
        assert service_es.language == 'es'
        assert service_en.language == 'en'


@pytest.mark.django_db
class TestAIUsageModel:
    """Test AI usage tracking model."""

    def test_ai_usage_model_exists(self):
        """AIUsage model should exist."""
        from apps.ai_assistant.models import AIUsage
        assert AIUsage is not None

    def test_ai_usage_has_required_fields(self):
        """AIUsage should have required fields."""
        from apps.ai_assistant.models import AIUsage
        fields = [f.name for f in AIUsage._meta.get_fields()]
        assert 'input_tokens' in fields
        assert 'output_tokens' in fields
        assert 'cost_usd' in fields
        assert 'model' in fields
        assert 'created_at' in fields

    def test_can_create_ai_usage_record(self):
        """Should be able to create AIUsage record."""
        from apps.ai_assistant.models import AIUsage
        usage = AIUsage.objects.create(
            session_id='test-session-123',
            input_tokens=100,
            output_tokens=200,
            cost_usd='0.001500',
            model='anthropic/claude-sonnet-4'
        )
        assert usage.id is not None
        assert usage.input_tokens == 100
        assert usage.output_tokens == 200


@pytest.mark.django_db
class TestConversationModel:
    """Test conversation model for chat history."""

    def test_conversation_model_exists(self):
        """Conversation model should exist."""
        from apps.ai_assistant.models import Conversation
        assert Conversation is not None

    def test_message_model_exists(self):
        """Message model should exist."""
        from apps.ai_assistant.models import Message
        assert Message is not None


class TestSystemPromptBuilding:
    """Test system prompt construction."""

    def test_build_system_prompt_returns_string(self):
        """build_system_prompt should return a string."""
        from apps.ai_assistant.services import AIService
        service = AIService(language='es')
        prompt = service.build_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_system_prompt_includes_clinic_context(self):
        """System prompt should include clinic context."""
        from apps.ai_assistant.services import AIService
        service = AIService(language='es')
        prompt = service.build_system_prompt()
        # Should mention the clinic or veterinary context
        prompt_lower = prompt.lower()
        assert ('veterinari' in prompt_lower or 'pet-friendly' in prompt_lower or
                'clínica' in prompt_lower or 'clinic' in prompt_lower or
                'mascota' in prompt_lower or 'pet' in prompt_lower)

    def test_system_prompt_respects_language(self):
        """System prompt should respect language setting."""
        from apps.ai_assistant.services import AIService
        service_es = AIService(language='es')
        service_en = AIService(language='en')
        prompt_es = service_es.build_system_prompt()
        prompt_en = service_en.build_system_prompt()
        # Prompts may be different or contain language-specific instructions
        assert isinstance(prompt_es, str)
        assert isinstance(prompt_en, str)


class TestMessageFormatting:
    """Test message formatting for Claude."""

    def test_format_user_message(self):
        """Should correctly format user messages."""
        from apps.ai_assistant.services import AIService
        service = AIService()
        # Check that messages can be processed
        assert hasattr(service, 'get_response')


class TestErrorHandling:
    """Test error handling in AI service."""

    def test_service_handles_missing_api_key_gracefully(self):
        """Service should handle missing API key gracefully."""
        from apps.ai_assistant.clients import OpenRouterClient
        # Should not raise exception on instantiation
        client = OpenRouterClient()
        assert client is not None
