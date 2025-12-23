"""Tests for OpenRouter API client."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from apps.ai_assistant.clients import OpenRouterClient


class TestOpenRouterClient:
    """Tests for OpenRouterClient."""

    def test_init_defaults(self, settings):
        """Test client initialization with default settings."""
        settings.OPENROUTER_API_KEY = 'test-key'
        settings.AI_MODEL = 'test-model'
        settings.AI_MAX_TOKENS = 1000

        client = OpenRouterClient()

        assert client.api_key == 'test-key'
        assert client.model == 'test-model'
        assert client.max_tokens == 1000
        assert client.base_url == 'https://openrouter.ai/api/v1'

    def test_init_missing_settings(self, settings):
        """Test client initialization with missing settings."""
        # Remove settings to test defaults
        if hasattr(settings, 'OPENROUTER_API_KEY'):
            delattr(settings, 'OPENROUTER_API_KEY')

        client = OpenRouterClient()
        assert client.api_key == ''

    @pytest.mark.asyncio
    async def test_chat_no_api_key(self, settings):
        """Test chat returns error when API key not configured."""
        settings.OPENROUTER_API_KEY = ''

        client = OpenRouterClient()
        result = await client.chat(messages=[{'role': 'user', 'content': 'Hello'}])

        assert result['error'] is True
        assert 'API key not configured' in result['message']

    @pytest.mark.asyncio
    async def test_chat_success(self, settings):
        """Test successful chat completion."""
        settings.OPENROUTER_API_KEY = 'test-key'

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'Hello!'}}]
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = OpenRouterClient()
            result = await client.chat(
                messages=[{'role': 'user', 'content': 'Hello'}]
            )

            assert 'choices' in result
            assert result['choices'][0]['message']['content'] == 'Hello!'

    @pytest.mark.asyncio
    async def test_chat_with_tools(self, settings):
        """Test chat completion with tools."""
        settings.OPENROUTER_API_KEY = 'test-key'

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'choices': []}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = OpenRouterClient()
            tools = [{'type': 'function', 'function': {'name': 'test'}}]
            await client.chat(
                messages=[{'role': 'user', 'content': 'Hello'}],
                tools=tools
            )

            # Verify tools were included in payload
            call_args = mock_client.post.call_args
            payload = call_args.kwargs['json']
            assert 'tools' in payload
            assert payload['tools'] == tools

    @pytest.mark.asyncio
    async def test_chat_api_error(self, settings):
        """Test chat handles API errors."""
        settings.OPENROUTER_API_KEY = 'test-key'

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = OpenRouterClient()
            result = await client.chat(
                messages=[{'role': 'user', 'content': 'Hello'}]
            )

            assert result['error'] is True
            assert result['status_code'] == 500
            assert 'Internal Server Error' in result['message']

    @pytest.mark.asyncio
    async def test_chat_custom_max_tokens(self, settings):
        """Test chat with custom max_tokens."""
        settings.OPENROUTER_API_KEY = 'test-key'
        settings.AI_MAX_TOKENS = 1000

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'choices': []}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = OpenRouterClient()
            await client.chat(
                messages=[{'role': 'user', 'content': 'Hello'}],
                max_tokens=500
            )

            call_args = mock_client.post.call_args
            payload = call_args.kwargs['json']
            assert payload['max_tokens'] == 500

    def test_chat_sync_no_api_key(self, settings):
        """Test sync chat returns error when API key not configured."""
        settings.OPENROUTER_API_KEY = ''

        client = OpenRouterClient()
        result = client.chat_sync(messages=[{'role': 'user', 'content': 'Hello'}])

        assert result['error'] is True
        assert 'API key not configured' in result['message']

    def test_chat_sync_success(self, settings):
        """Test successful sync chat completion."""
        settings.OPENROUTER_API_KEY = 'test-key'

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'Hello!'}}]
        }

        with patch('httpx.Client') as mock_client_class:
            mock_client = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = OpenRouterClient()
            result = client.chat_sync(
                messages=[{'role': 'user', 'content': 'Hello'}]
            )

            assert 'choices' in result
            assert result['choices'][0]['message']['content'] == 'Hello!'

    def test_chat_sync_with_tools(self, settings):
        """Test sync chat with tools."""
        settings.OPENROUTER_API_KEY = 'test-key'

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'choices': []}

        with patch('httpx.Client') as mock_client_class:
            mock_client = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = OpenRouterClient()
            tools = [{'type': 'function', 'function': {'name': 'test'}}]
            client.chat_sync(
                messages=[{'role': 'user', 'content': 'Hello'}],
                tools=tools
            )

            call_args = mock_client.post.call_args
            payload = call_args.kwargs['json']
            assert 'tools' in payload

    def test_chat_sync_api_error(self, settings):
        """Test sync chat handles API errors."""
        settings.OPENROUTER_API_KEY = 'test-key'

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = 'Rate limit exceeded'

        with patch('httpx.Client') as mock_client_class:
            mock_client = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = OpenRouterClient()
            result = client.chat_sync(
                messages=[{'role': 'user', 'content': 'Hello'}]
            )

            assert result['error'] is True
            assert result['status_code'] == 429
            assert 'Rate limit' in result['message']
