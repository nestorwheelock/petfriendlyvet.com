"""OpenRouter API client for AI interactions."""
import httpx
from django.conf import settings


class OpenRouterClient:
    """Client for OpenRouter API with Claude support."""

    def __init__(self):
        self.api_key = getattr(settings, 'OPENROUTER_API_KEY', '')
        self.model = getattr(settings, 'AI_MODEL', 'anthropic/claude-sonnet-4')
        self.base_url = 'https://openrouter.ai/api/v1'
        self.max_tokens = getattr(settings, 'AI_MAX_TOKENS', 4096)

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] = None,
        stream: bool = False,
        max_tokens: int = None,
    ) -> dict:
        """Send chat completion request to OpenRouter.

        Args:
            messages: List of message dicts with 'role' and 'content'
            tools: Optional list of tool definitions
            stream: Whether to stream the response
            max_tokens: Maximum tokens in response

        Returns:
            Response dict from OpenRouter API
        """
        if not self.api_key:
            return {
                'error': True,
                'message': 'OpenRouter API key not configured'
            }

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://petfriendlyvet.com',
            'X-Title': 'Pet-Friendly Vet Assistant'
        }

        payload = {
            'model': self.model,
            'messages': messages,
            'max_tokens': max_tokens or self.max_tokens,
        }

        if tools:
            payload['tools'] = tools

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f'{self.base_url}/chat/completions',
                headers=headers,
                json=payload,
                timeout=60.0
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'error': True,
                    'status_code': response.status_code,
                    'message': response.text
                }

    def chat_sync(
        self,
        messages: list[dict],
        tools: list[dict] = None,
        max_tokens: int = None,
    ) -> dict:
        """Synchronous version of chat for non-async contexts."""
        if not self.api_key:
            return {
                'error': True,
                'message': 'OpenRouter API key not configured'
            }

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://petfriendlyvet.com',
            'X-Title': 'Pet-Friendly Vet Assistant'
        }

        payload = {
            'model': self.model,
            'messages': messages,
            'max_tokens': max_tokens or self.max_tokens,
        }

        if tools:
            payload['tools'] = tools

        with httpx.Client() as client:
            response = client.post(
                f'{self.base_url}/chat/completions',
                headers=headers,
                json=payload,
                timeout=60.0
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'error': True,
                    'status_code': response.status_code,
                    'message': response.text
                }
