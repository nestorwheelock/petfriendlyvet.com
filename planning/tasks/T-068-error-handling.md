# T-068: Fix Error Message Leakage

> **REQUIRED READING:** Before implementation, review [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)

> **Parent Story:** [S-027 Security Hardening](../stories/S-027-security-hardening.md)

**Task Type:** Security Fix
**Priority:** MEDIUM
**Estimate:** 1 hour
**Status:** PENDING

---

## Objective

Prevent sensitive information from leaking through error messages by replacing raw exception details with generic user-facing messages while maintaining detailed server-side logging.

---

## Background

The current implementation uses `str(e)` in several error handlers, which can expose:
- Internal file paths
- Database table/column names
- SQL query fragments
- Stack trace information
- Third-party service details
- Configuration values

This information could help attackers understand the system architecture and identify vulnerabilities.

---

## Current Problem

### Example: Current Chat API Error Handling

```python
# apps/ai_assistant/views.py (BEFORE)
except Exception as e:
    return JsonResponse({'error': str(e)}, status=500)
```

**Risk:** This could expose:
- OpenRouter API errors with keys
- Database connection strings
- Internal exception details

---

## Solution

### Pattern: Safe Error Handling

```python
# apps/ai_assistant/views.py (AFTER)
import logging

logger = logging.getLogger(__name__)

try:
    # ... code that might fail
except ValidationError as e:
    # Client errors - safe to show
    return JsonResponse({'error': str(e)}, status=400)
except Exception as e:
    # Server errors - log details, show generic message
    logger.exception(
        "Chat API error",
        extra={
            'session_id': session_id,
            'user_id': request.user.id if request.user.is_authenticated else None,
        }
    )
    return JsonResponse(
        {'error': 'An unexpected error occurred. Please try again later.'},
        status=500
    )
```

---

## Implementation

### Step 1: Audit Error Handlers

Search for patterns to fix:
```bash
grep -r "str(e)" apps/
grep -r "{'error':" apps/
grep -r "JsonResponse.*error" apps/
```

### Step 2: Create Error Response Helpers

```python
# apps/core/responses.py

from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)


def error_response(message, status=400, code=None):
    """
    Return a standardized error JSON response.

    Args:
        message: User-facing error message (safe to display)
        status: HTTP status code
        code: Optional error code for client handling
    """
    data = {'error': message}
    if code:
        data['code'] = code
    return JsonResponse(data, status=status)


def server_error_response(exception, context=None):
    """
    Log server error and return generic response.

    Args:
        exception: The caught exception
        context: Dict of context for logging (no sensitive data)
    """
    logger.exception(
        "Internal server error",
        extra=context or {}
    )
    return JsonResponse(
        {
            'error': 'An unexpected error occurred. Please try again later.',
            'code': 'internal_error'
        },
        status=500
    )


# Error messages mapping
ERROR_MESSAGES = {
    'rate_limit': 'Too many requests. Please slow down.',
    'invalid_input': 'Invalid input provided. Please check your data.',
    'not_found': 'The requested resource was not found.',
    'unauthorized': 'Authentication required.',
    'forbidden': 'You do not have permission to perform this action.',
    'internal_error': 'An unexpected error occurred. Please try again later.',
    'service_unavailable': 'Service temporarily unavailable. Please try again later.',
}
```

### Step 3: Update Chat View

```python
# apps/ai_assistant/views.py

import logging
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from apps.core.responses import error_response, server_error_response

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class ChatView(View):
    """Handle chat API requests."""

    def post(self, request):
        try:
            # Parse request
            message = request.POST.get('message', '').strip()
            session_id = request.POST.get('session_id', '')

            if not message:
                return error_response(
                    'Message is required.',
                    status=400,
                    code='missing_message'
                )

            # Process chat...
            response_data = self._process_chat(message, session_id, request)
            return JsonResponse(response_data)

        except ValueError as e:
            # Validation errors are safe to show
            return error_response(str(e), status=400)

        except Exception:
            # All other errors - log and return generic message
            return server_error_response(
                exception=None,  # Already logged by exception()
                context={
                    'session_id': session_id if 'session_id' in locals() else None,
                    'user_id': request.user.id if request.user.is_authenticated else None,
                    'path': request.path,
                }
            )
```

### Step 4: Create DRF Exception Handler

```python
# apps/core/exception_handlers.py

import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that sanitizes error responses.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    if response is not None:
        # Customize the response data
        custom_response_data = {
            'error': get_safe_error_message(exc, response.status_code),
            'code': get_error_code(exc),
        }

        # For validation errors, include field details
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            if hasattr(exc, 'detail') and isinstance(exc.detail, dict):
                custom_response_data['details'] = exc.detail

        response.data = custom_response_data

    else:
        # Unhandled exceptions - log and return generic 500
        logger.exception(
            "Unhandled API exception",
            extra={
                'view': context.get('view'),
                'request_path': context.get('request').path if context.get('request') else None,
            }
        )
        response = Response(
            {
                'error': 'An unexpected error occurred.',
                'code': 'internal_error',
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return response


def get_safe_error_message(exc, status_code):
    """Return a safe error message based on exception type."""
    safe_messages = {
        400: 'Invalid request data.',
        401: 'Authentication required.',
        403: 'Permission denied.',
        404: 'Resource not found.',
        405: 'Method not allowed.',
        429: 'Too many requests.',
        500: 'Internal server error.',
    }

    # For validation errors, show the actual message
    if status_code == 400 and hasattr(exc, 'detail'):
        if isinstance(exc.detail, str):
            return exc.detail

    return safe_messages.get(status_code, 'An error occurred.')


def get_error_code(exc):
    """Generate error code from exception type."""
    return exc.__class__.__name__.lower().replace('exception', '').replace('error', '') or 'unknown'
```

### Step 5: Configure DRF Settings

```python
# config/settings/base.py

REST_FRAMEWORK = {
    # ... existing settings
    'EXCEPTION_HANDLER': 'apps.core.exception_handlers.custom_exception_handler',
}
```

---

## Files to Modify

| File | Action |
|------|--------|
| `apps/core/responses.py` | Create (helper functions) |
| `apps/core/exception_handlers.py` | Create (DRF handler) |
| `apps/ai_assistant/views.py` | Update error handling |
| `apps/core/views.py` | Update error handling |
| `config/settings/base.py` | Add DRF exception handler |

---

## Tests Required

```python
# tests/test_error_handling.py

import pytest
from django.test import Client


@pytest.mark.django_db
class TestErrorHandling:
    """Test that errors don't leak sensitive information."""

    def test_server_error_is_generic(self, client, monkeypatch):
        """500 errors should not expose internal details."""
        # Force an error in chat
        def raise_error(*args, **kwargs):
            raise Exception("Database connection failed: postgresql://user:pass@host/db")

        monkeypatch.setattr('apps.ai_assistant.views.ChatView._process_chat', raise_error)

        response = client.post('/chat/', {'message': 'hello'})

        assert response.status_code == 500
        data = response.json()
        assert 'error' in data
        # Should NOT contain sensitive info
        assert 'Database' not in data['error']
        assert 'postgresql' not in data['error']
        assert 'password' not in data['error']
        # Should have generic message
        assert 'unexpected error' in data['error'].lower() or 'internal' in data['error'].lower()

    def test_validation_error_is_specific(self, client):
        """400 errors should provide helpful details."""
        response = client.post('/chat/', {})  # Missing message

        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        # Should tell user what's wrong
        assert 'message' in data['error'].lower() or 'required' in data['error'].lower()

    def test_404_is_generic(self, client):
        """404 errors should not reveal path structure."""
        response = client.get('/api/nonexistent/path/')

        assert response.status_code == 404
        data = response.json()
        assert 'not found' in data.get('error', '').lower()

    def test_no_stack_traces(self, client, monkeypatch):
        """Stack traces should never appear in responses."""
        def raise_error(*args, **kwargs):
            raise ValueError("Traceback (most recent call last):")

        monkeypatch.setattr('apps.ai_assistant.views.ChatView._process_chat', raise_error)

        response = client.post('/chat/', {'message': 'hello'})

        content = response.content.decode()
        assert 'Traceback' not in content
        assert 'File "' not in content
        assert 'line ' not in content
```

---

## Acceptance Criteria

- [ ] No `str(e)` patterns exposing internal errors
- [ ] Server errors return generic messages
- [ ] Validation errors provide helpful feedback
- [ ] All errors logged with full context server-side
- [ ] DRF exception handler configured
- [ ] Tests verify no information leakage

---

## Definition of Done

- [ ] Helper functions created in `apps/core/responses.py`
- [ ] DRF exception handler configured
- [ ] All error handlers updated in views
- [ ] Tests pass verifying no info leakage
- [ ] Server logs contain full exception details
- [ ] Manual testing confirms generic error messages

---

## Security Benefit

**Before:** Attackers could gather:
- Internal paths revealing server structure
- Database schema information
- API endpoint details
- Third-party service configurations

**After:** Attackers see only:
- Generic "An error occurred" messages
- Helpful validation feedback
- No internal implementation details

---

*Created: December 23, 2025*
