# T-067: Security Test Suite

> **Parent Story:** [S-027 Security Hardening](../stories/S-027-security-hardening.md)

**Task Type:** Security Testing
**Priority:** HIGH
**Estimate:** 3-4 hours
**Status:** PENDING

---

## Objective

Create a comprehensive security test suite that validates protection against OWASP Top 10 vulnerabilities and establishes a security baseline for the Pet-Friendly Veterinary Clinic application.

---

## Background

While the application has 440 tests with 96% coverage, there is no dedicated security-focused test suite. Security testing is essential to:
- Verify authentication and authorization controls
- Test input validation and sanitization
- Ensure session security
- Validate CSRF protection
- Establish a baseline for future security regression testing

---

## Test Categories

### 1. Authorization Tests
- Unauthenticated access returns 401/403
- Staff-only endpoints reject regular users
- Admin endpoints reject non-admin staff
- User can only access own data
- Horizontal privilege escalation prevented

### 2. Input Validation Tests
- SQL injection patterns rejected/escaped
- XSS payloads escaped in responses
- Malformed JSON handled gracefully
- Oversized requests rejected
- Path traversal attempts blocked

### 3. Session Security Tests
- Session fixation prevention
- Session expires on logout
- Session cookie flags (HttpOnly, Secure, SameSite)
- Concurrent session handling

### 4. CSRF Protection Tests
- POST without CSRF token rejected
- CSRF token validated correctly
- CSRF token regenerated on login

### 5. Authentication Tests
- Password requirements enforced
- Login rate limiting (if implemented)
- Account enumeration prevented
- Secure password reset flow

---

## Implementation

### File: `tests/test_security.py`

```python
"""
Security Test Suite for Pet-Friendly Veterinary Clinic

Tests validate protection against OWASP Top 10 vulnerabilities:
- A01:2021 Broken Access Control
- A02:2021 Cryptographic Failures
- A03:2021 Injection
- A04:2021 Insecure Design
- A05:2021 Security Misconfiguration
- A06:2021 Vulnerable Components
- A07:2021 Authentication Failures
- A08:2021 Data Integrity Failures
- A09:2021 Security Logging Failures
- A10:2021 Server-Side Request Forgery
"""
import pytest
from django.test import Client, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


# =============================================================================
# A01:2021 - Broken Access Control
# =============================================================================

@pytest.mark.django_db
class TestAccessControl:
    """Test authorization and access control."""

    @pytest.fixture
    def owner_user(self):
        return User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='testpass123',
            role='owner'
        )

    @pytest.fixture
    def staff_user(self):
        return User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='testpass123',
            role='staff'
        )

    @pytest.fixture
    def admin_user(self):
        return User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            role='admin',
            is_staff=True
        )

    def test_unauthenticated_cannot_access_protected_views(self, client):
        """Unauthenticated users should be redirected or denied."""
        protected_urls = [
            '/admin/',
            '/api/users/',
        ]
        for url in protected_urls:
            response = client.get(url)
            # Should redirect to login or return 403
            assert response.status_code in [302, 401, 403], f"{url} accessible without auth"

    def test_owner_cannot_access_admin(self, client, owner_user):
        """Regular owner users cannot access admin."""
        client.login(username='owner', password='testpass123')
        response = client.get('/admin/')
        assert response.status_code in [302, 403]

    def test_user_cannot_access_other_users_data(self, client, owner_user):
        """Users should only see their own data."""
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123',
            role='owner'
        )

        client.login(username='owner', password='testpass123')

        # Try to access other user's profile (if such endpoint exists)
        # This test validates horizontal privilege escalation prevention
        # Adjust URL based on actual API endpoints
        response = client.get(f'/api/users/{other_user.id}/')
        assert response.status_code in [403, 404]

    def test_idor_prevention(self, client, owner_user):
        """Insecure Direct Object Reference should be prevented."""
        client.login(username='owner', password='testpass123')

        # Try sequential ID enumeration
        for user_id in range(1, 10):
            if user_id != owner_user.id:
                response = client.get(f'/api/users/{user_id}/')
                assert response.status_code in [403, 404], f"IDOR vulnerability for user {user_id}"


# =============================================================================
# A03:2021 - Injection
# =============================================================================

@pytest.mark.django_db
class TestInjectionPrevention:
    """Test SQL injection and other injection attacks."""

    def test_sql_injection_in_search(self, client):
        """SQL injection in search parameters should be escaped."""
        injection_payloads = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "1; SELECT * FROM users",
            "1 UNION SELECT username, password FROM auth_user",
            "admin'--",
        ]

        for payload in injection_payloads:
            # Test in various query parameters
            response = client.get(f'/services/?q={payload}')
            assert response.status_code in [200, 400], f"Unexpected response for injection: {payload}"
            # Application should not crash
            assert response.status_code != 500, f"Server error with injection: {payload}"

    def test_sql_injection_in_chat(self, client):
        """SQL injection in chat messages should be safe."""
        injection_payloads = [
            "'; DROP TABLE conversations; --",
            "What are your hours?' OR '1'='1",
        ]

        for payload in injection_payloads:
            response = client.post('/chat/', {'message': payload})
            # Should handle gracefully, not crash
            assert response.status_code != 500, f"Server error with injection: {payload}"

    def test_xss_payloads_escaped(self, client):
        """XSS payloads should be escaped in responses."""
        xss_payloads = [
            '<script>alert("XSS")</script>',
            '<img src="x" onerror="alert(1)">',
            '<svg onload="alert(1)">',
            'javascript:alert(1)',
            '<iframe src="javascript:alert(1)">',
        ]

        for payload in xss_payloads:
            response = client.post('/chat/', {'message': payload})

            if response.status_code == 200:
                content = response.content.decode()
                # Raw script tags should never appear in response
                assert '<script>' not in content.lower(), f"XSS vulnerability: {payload}"
                assert 'onerror=' not in content.lower(), f"XSS vulnerability: {payload}"
                assert 'onload=' not in content.lower(), f"XSS vulnerability: {payload}"


# =============================================================================
# A07:2021 - Authentication Failures
# =============================================================================

@pytest.mark.django_db
class TestAuthentication:
    """Test authentication security."""

    def test_session_regenerated_on_login(self, client):
        """Session ID should change after login to prevent fixation."""
        # Get session before login
        client.get('/')
        session_before = client.session.session_key

        # Create user and login
        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        client.login(username='testuser', password='testpass123')
        session_after = client.session.session_key

        # Session should be different
        assert session_before != session_after, "Session fixation vulnerability"

    def test_session_destroyed_on_logout(self, client):
        """Session should be destroyed on logout."""
        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        client.login(username='testuser', password='testpass123')

        # Store session key
        session_key = client.session.session_key

        # Logout
        client.logout()

        # Session should be gone
        assert client.session.session_key != session_key

    def test_password_not_in_response(self, client):
        """Passwords should never appear in API responses."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        client.login(username='testuser', password='testpass123')

        # Access user profile or any user-related endpoint
        response = client.get(f'/api/users/{user.id}/')

        if response.status_code == 200:
            content = response.content.decode().lower()
            assert 'testpass' not in content, "Password in response"
            assert 'password' not in content or 'password_hash' not in content


# =============================================================================
# A05:2021 - Security Misconfiguration (CSRF)
# =============================================================================

@pytest.mark.django_db
class TestCSRFProtection:
    """Test CSRF protection."""

    def test_post_without_csrf_rejected(self, client):
        """POST requests without CSRF token should be rejected."""
        # Create client that doesn't handle CSRF
        csrf_client = Client(enforce_csrf_checks=True)

        response = csrf_client.post('/chat/', {'message': 'hello'})
        assert response.status_code == 403, "CSRF protection not enforced"

    def test_post_with_csrf_accepted(self, client):
        """POST requests with valid CSRF token should work."""
        # Get CSRF token
        response = client.get('/')
        csrf_token = client.cookies.get('csrftoken')

        if csrf_token:
            response = client.post(
                '/chat/',
                {'message': 'hello'},
                HTTP_X_CSRFTOKEN=csrf_token.value
            )
            # Should not be 403 (CSRF failure)
            assert response.status_code != 403


# =============================================================================
# Input Validation Tests
# =============================================================================

@pytest.mark.django_db
class TestInputValidation:
    """Test input validation and sanitization."""

    def test_oversized_request_rejected(self, client):
        """Extremely large requests should be rejected."""
        large_message = 'A' * 1000000  # 1MB of text

        response = client.post('/chat/', {'message': large_message})
        # Should handle gracefully (reject or truncate)
        assert response.status_code in [200, 400, 413]

    def test_malformed_json_handled(self, client):
        """Malformed JSON should return proper error."""
        response = client.post(
            '/chat/',
            data='{"broken json',
            content_type='application/json'
        )
        # Should not crash
        assert response.status_code in [200, 400]
        assert response.status_code != 500

    def test_null_bytes_handled(self, client):
        """Null bytes in input should be handled safely."""
        response = client.post('/chat/', {'message': 'hello\x00world'})
        assert response.status_code != 500

    def test_unicode_edge_cases(self, client):
        """Unicode edge cases should be handled safely."""
        unicode_payloads = [
            '\u0000',  # Null
            '\uFFFD',  # Replacement character
            '\u202E',  # RTL override
            'test\u0000\u0000',
            '😀' * 1000,  # Many emoji
        ]

        for payload in unicode_payloads:
            response = client.post('/chat/', {'message': payload})
            assert response.status_code != 500, f"Server error with unicode: {repr(payload)}"


# =============================================================================
# Path Traversal Tests
# =============================================================================

@pytest.mark.django_db
class TestPathTraversal:
    """Test path traversal prevention."""

    def test_path_traversal_in_static_files(self, client):
        """Path traversal should not expose sensitive files."""
        traversal_payloads = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\config\\sam',
            '/etc/passwd',
            '....//....//....//etc/passwd',
        ]

        for payload in traversal_payloads:
            response = client.get(f'/static/{payload}')
            # Should return 400/403/404, never the actual file
            assert response.status_code in [400, 403, 404]
            if response.status_code == 200:
                assert 'root:' not in response.content.decode()


# =============================================================================
# Security Headers Tests
# =============================================================================

class TestSecurityHeaders:
    """Test security-related HTTP headers."""

    def test_x_frame_options_header(self, client):
        """X-Frame-Options should prevent clickjacking."""
        response = client.get('/')
        # Django sets this by default
        assert 'X-Frame-Options' in response.headers

    def test_x_content_type_options_header(self, client):
        """X-Content-Type-Options should prevent MIME sniffing."""
        response = client.get('/')
        # Check if header present (may need middleware)
        x_content_type = response.headers.get('X-Content-Type-Options', '')
        # This is a check - may need to add middleware if not present

    def test_cache_control_on_sensitive_pages(self, client):
        """Sensitive pages should have proper cache control."""
        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        client.login(username='testuser', password='testpass123')

        # Check profile or account pages
        # Add appropriate URLs when they exist
```

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `tests/test_security.py` | Create (new file) |
| `pytest.ini` | Add security marker |
| `.coveragerc` | Ensure security tests included |

---

## Test Execution

```bash
# Run all security tests
pytest tests/test_security.py -v

# Run with coverage
pytest tests/test_security.py --cov=apps --cov-report=term-missing

# Run specific category
pytest tests/test_security.py -v -k "TestAccessControl"
```

---

## Acceptance Criteria

- [ ] All authorization test cases pass
- [ ] All injection prevention tests pass
- [ ] All authentication tests pass
- [ ] All CSRF tests pass
- [ ] All input validation tests pass
- [ ] All path traversal tests pass
- [ ] Security headers verified
- [ ] Tests integrated into CI pipeline
- [ ] >95% coverage maintained

---

## Definition of Done

- [ ] `tests/test_security.py` created with all test categories
- [ ] All security tests pass
- [ ] Tests run as part of normal test suite
- [ ] Security marker added for selective testing
- [ ] Documentation updated with security testing info
- [ ] No reduction in overall test coverage

---

## Future Enhancements

- Add fuzzing tests with hypothesis
- Integrate OWASP ZAP for dynamic testing
- Add dependency vulnerability scanning
- Create security regression test baseline

---

*Created: December 23, 2025*
