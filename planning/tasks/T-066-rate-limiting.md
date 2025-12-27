# T-066: Implement API Rate Limiting

> **REQUIRED READING:** Before implementation, review [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)

> **Parent Story:** [S-027 Security Hardening](../stories/S-027-security-hardening.md)

**Task Type:** Security Implementation
**Priority:** HIGH
**Estimate:** 2-3 hours
**Status:** PENDING

---

## Objective

Protect the chat API from abuse and control AI costs by implementing rate limiting on all API endpoints, with different limits for anonymous and authenticated users.

---

## Background

The current chat API has no rate limiting, which creates several risks:
- **Cost abuse**: Malicious actors could spam the API, generating excessive AI costs
- **Denial of service**: High request volume could degrade service for legitimate users
- **Bot attacks**: Automated scripts could harvest data or test exploits

---

## Technical Approach

### Package Selection

Use `django-ratelimit` for rate limiting:
- Well-maintained, Django-native solution
- Supports multiple backends (cache, database)
- Decorators work with both function and class-based views
- Supports custom rate limit keys (IP, user, session)

### Rate Limits

| Endpoint | Anonymous | Authenticated |
|----------|-----------|---------------|
| `/chat/` | 10/minute per IP | 50/hour per user |
| `/api/*` | 30/minute per IP | 100/hour per user |

---

## Implementation

### Step 1: Add Dependency

```bash
# requirements/base.txt
django-ratelimit>=4.1.0
```

### Step 2: Configure Settings

```python
# config/settings/base.py

# Rate limiting configuration
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'
RATELIMIT_VIEW = 'apps.core.views.ratelimited_error'

# AI-specific rate limits
AI_RATE_LIMIT_ANONYMOUS = "10/m"  # 10 requests per minute
AI_RATE_LIMIT_AUTHENTICATED = "50/h"  # 50 requests per hour
```

### Step 3: Create Rate Limit Decorator

```python
# apps/ai_assistant/decorators.py
from functools import wraps
from django.conf import settings
from django.http import JsonResponse
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited
import logging

logger = logging.getLogger(__name__)


def ai_ratelimit(view_func):
    """
    Apply rate limiting to AI endpoints.

    Anonymous users: 10 requests/minute per IP
    Authenticated users: 50 requests/hour per user
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Determine rate limit based on authentication
        if request.user.is_authenticated:
            key = f'user:{request.user.id}'
            rate = getattr(settings, 'AI_RATE_LIMIT_AUTHENTICATED', '50/h')
        else:
            key = 'ip'
            rate = getattr(settings, 'AI_RATE_LIMIT_ANONYMOUS', '10/m')

        # Apply rate limit using django-ratelimit
        @ratelimit(key=key, rate=rate, method='POST', block=True)
        def limited_view(request, *args, **kwargs):
            return view_func(request, *args, **kwargs)

        try:
            return limited_view(request, *args, **kwargs)
        except Ratelimited:
            logger.warning(
                "Rate limit exceeded",
                extra={
                    'user_id': request.user.id if request.user.is_authenticated else None,
                    'ip': get_client_ip(request),
                    'path': request.path,
                }
            )
            return JsonResponse(
                {
                    'error': 'Too many requests. Please try again later.',
                    'retry_after': 60 if 'm' in rate else 3600,
                },
                status=429,
                headers={'Retry-After': '60' if 'm' in rate else '3600'}
            )

    return wrapper


def get_client_ip(request):
    """Extract client IP from request, handling proxies."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')
```

### Step 4: Apply to Chat View

```python
# apps/ai_assistant/views.py
from .decorators import ai_ratelimit

class ChatView(View):
    @method_decorator(ai_ratelimit)
    def post(self, request):
        # Existing chat logic
        ...
```

### Step 5: Create Rate Limit Error View

```python
# apps/core/views.py
from django.http import JsonResponse

def ratelimited_error(request, exception):
    """Handle rate limit exceeded errors."""
    return JsonResponse(
        {
            'error': 'Too many requests. Please slow down.',
            'code': 'rate_limit_exceeded',
        },
        status=429,
        headers={'Retry-After': '60'}
    )
```

---

## Files to Modify

| File | Action |
|------|--------|
| `requirements/base.txt` | Add django-ratelimit |
| `config/settings/base.py` | Add rate limit settings |
| `apps/ai_assistant/decorators.py` | Create (new file) |
| `apps/ai_assistant/views.py` | Apply decorator |
| `apps/core/views.py` | Add error handler |

---

## Tests Required

### Unit Tests

```python
# tests/test_rate_limiting.py
import pytest
from django.test import Client, override_settings
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestRateLimiting:
    """Test rate limiting on chat API."""

    def test_anonymous_rate_limit_allows_under_threshold(self, client):
        """Anonymous user under limit should succeed."""
        for _ in range(5):
            response = client.post('/chat/', {'message': 'hello'})
            assert response.status_code != 429

    @override_settings(AI_RATE_LIMIT_ANONYMOUS='2/m')
    def test_anonymous_rate_limit_blocks_over_threshold(self, client):
        """Anonymous user over limit should get 429."""
        # First two should succeed
        for _ in range(2):
            client.post('/chat/', {'message': 'hello'})

        # Third should be rate limited
        response = client.post('/chat/', {'message': 'hello'})
        assert response.status_code == 429
        assert 'Retry-After' in response.headers

    def test_rate_limit_response_format(self, client):
        """Rate limit response should have proper format."""
        # Force rate limit
        with override_settings(AI_RATE_LIMIT_ANONYMOUS='1/m'):
            client.post('/chat/', {'message': 'hello'})
            response = client.post('/chat/', {'message': 'hello'})

        assert response.status_code == 429
        data = response.json()
        assert 'error' in data
        assert 'retry_after' in data

    def test_authenticated_has_higher_limit(self, client):
        """Authenticated users should have higher limits."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        client.login(username='testuser', password='testpass123')

        # Should allow more requests
        for _ in range(10):
            response = client.post('/chat/', {'message': 'hello'})
            # Should not be rate limited at 10 requests
            assert response.status_code != 429

    def test_rate_limit_resets_after_window(self, client, freezer):
        """Rate limit should reset after time window."""
        with override_settings(AI_RATE_LIMIT_ANONYMOUS='2/m'):
            # Hit limit
            client.post('/chat/', {'message': 'hello'})
            client.post('/chat/', {'message': 'hello'})
            response = client.post('/chat/', {'message': 'hello'})
            assert response.status_code == 429

            # Advance time past window
            freezer.move_to('+61 seconds')

            # Should work again
            response = client.post('/chat/', {'message': 'hello'})
            assert response.status_code != 429
```

### Integration Tests

```python
def test_rate_limit_logged(self, client, caplog):
    """Rate limit violations should be logged."""
    with override_settings(AI_RATE_LIMIT_ANONYMOUS='1/m'):
        client.post('/chat/', {'message': 'hello'})
        client.post('/chat/', {'message': 'hello'})

    assert 'Rate limit exceeded' in caplog.text
```

---

## Acceptance Criteria

- [ ] Anonymous users limited to 10 requests/minute
- [ ] Authenticated users limited to 50 requests/hour
- [ ] 429 response includes Retry-After header
- [ ] 429 response is JSON formatted
- [ ] Rate limit violations are logged
- [ ] Tests cover all rate limit scenarios
- [ ] Documentation updated

---

## Definition of Done

- [ ] `django-ratelimit` package added to requirements
- [ ] Rate limit decorator created and applied to chat endpoint
- [ ] Error handler returns proper 429 response
- [ ] All tests pass (>95% coverage maintained)
- [ ] Rate limit events logged with user/IP context
- [ ] Manual testing confirms rate limits work

---

## Security Considerations

- Use cache backend (Redis in production) for rate limit storage
- Consider implementing exponential backoff for repeat offenders
- Monitor rate limit logs for attack patterns
- Consider IP-based blocking for persistent abuse

---

*Created: December 23, 2025*
