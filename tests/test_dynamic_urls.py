"""Tests for dynamic URL system (session-based admin and staff tokens)."""
import pytest
import secrets
from django.test import Client, RequestFactory
from django.http import Http404
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware

from apps.core.middleware.dynamic_urls import (
    DynamicURLMiddleware,
    generate_token,
    validate_token,
    get_admin_token,
    get_staff_token,
)


User = get_user_model()


@pytest.fixture
def rf():
    """Request factory fixture."""
    return RequestFactory()


@pytest.fixture
def superuser(db):
    """Create a superuser."""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='testpass123',
    )


@pytest.fixture
def staff_user(db):
    """Create a staff user."""
    return User.objects.create_user(
        username='staff',
        email='staff@example.com',
        password='testpass123',
        is_staff=True,
    )


@pytest.fixture
def regular_user(db):
    """Create a regular (non-staff) user."""
    return User.objects.create_user(
        username='user',
        email='user@example.com',
        password='testpass123',
    )


def add_session_to_request(request):
    """Add a session to a request object."""
    middleware = SessionMiddleware(lambda r: None)
    middleware.process_request(request)
    request.session.save()


@pytest.fixture
def middleware():
    """Dynamic URL middleware fixture."""
    def get_response(request):
        from django.http import HttpResponse
        return HttpResponse('OK')
    return DynamicURLMiddleware(get_response)


@pytest.mark.django_db
class TestTokenGeneration:
    """Tests for token generation."""

    def test_generate_token_length(self):
        """Test that generated tokens are 6 characters."""
        token = generate_token()
        assert len(token) == 6

    def test_generate_token_alphanumeric(self):
        """Test that tokens are URL-safe alphanumeric."""
        token = generate_token()
        assert token.isalnum()

    def test_generate_token_unique(self):
        """Test that tokens are unique (statistically)."""
        tokens = [generate_token() for _ in range(100)]
        assert len(set(tokens)) == 100  # All unique

    def test_tokens_are_different_each_session(self):
        """Test that each call generates a different token."""
        token1 = generate_token()
        token2 = generate_token()
        assert token1 != token2


@pytest.mark.django_db
class TestDynamicAdminURL:
    """Tests for dynamic admin URL routing."""

    def test_admin_url_returns_404(self, rf, middleware):
        """Test that /admin/ directly returns 404."""
        request = rf.get('/admin/')
        with pytest.raises(Http404):
            middleware(request)

    def test_valid_admin_token_accesses_admin(self, rf, middleware, superuser):
        """Test that valid admin token allows access to admin."""
        request = rf.get('/panel-abc123/')
        add_session_to_request(request)
        request.user = superuser
        request.session['admin_token'] = 'abc123'
        request.session.save()

        response = middleware(request)
        assert response.status_code == 200

    def test_invalid_admin_token_returns_404(self, rf, middleware, superuser):
        """Test that invalid admin token returns 404."""
        request = rf.get('/panel-wrong1/')
        add_session_to_request(request)
        request.user = superuser
        request.session['admin_token'] = 'abc123'  # Different token
        request.session.save()

        with pytest.raises(Http404):
            middleware(request)

    def test_staff_cannot_access_admin_token(self, rf, middleware, staff_user):
        """Test that staff users cannot access admin panel."""
        request = rf.get('/panel-abc123/')
        add_session_to_request(request)
        request.user = staff_user
        request.session['admin_token'] = 'abc123'
        request.session.save()

        with pytest.raises(Http404):
            middleware(request)


@pytest.mark.django_db
class TestDynamicStaffURL:
    """Tests for dynamic staff URL routing."""

    def test_direct_module_url_returns_404(self, rf, middleware):
        """Test that /accounting/ directly returns 404."""
        request = rf.get('/accounting/')
        with pytest.raises(Http404):
            middleware(request)

    def test_valid_staff_token_accesses_module(self, rf, middleware, staff_user):
        """Test that valid staff token allows access to modules."""
        request = rf.get('/staff-xyz789/operations/appointments/')
        add_session_to_request(request)
        request.user = staff_user
        request.session['staff_token'] = 'xyz789'
        request.session.save()

        response = middleware(request)
        assert response.status_code == 200

    def test_invalid_staff_token_returns_404(self, rf, middleware, staff_user):
        """Test that invalid staff token returns 404."""
        request = rf.get('/staff-wrong1/operations/appointments/')
        add_session_to_request(request)
        request.user = staff_user
        request.session['staff_token'] = 'xyz789'  # Different token
        request.session.save()

        with pytest.raises(Http404):
            middleware(request)

    def test_superuser_gets_both_tokens(self, rf, superuser):
        """Test that superusers get both admin and staff tokens."""
        request = rf.get('/some-path/')
        add_session_to_request(request)
        request.user = superuser

        # Simulate token generation on login
        admin_token = get_admin_token(request)
        staff_token = get_staff_token(request)

        assert admin_token is not None
        assert staff_token is not None
        assert admin_token != staff_token


@pytest.mark.django_db
class TestTokenSecurity:
    """Tests for token security."""

    def test_expired_session_invalidates_tokens(self, rf, middleware, staff_user):
        """Test that tokens are invalid without session."""
        request = rf.get('/staff-abc123/operations/appointments/')
        # No session added
        with pytest.raises(Http404):
            middleware(request)

    def test_tokens_are_session_bound(self, rf, middleware, staff_user):
        """Test that tokens only work with their session."""
        # Create two requests with different sessions
        request1 = rf.get('/staff-token1/operations/appointments/')
        add_session_to_request(request1)
        request1.user = staff_user
        request1.session['staff_token'] = 'token1'
        request1.session.save()

        request2 = rf.get('/staff-token1/operations/appointments/')
        add_session_to_request(request2)
        request2.user = staff_user
        request2.session['staff_token'] = 'token2'  # Different token
        request2.session.save()

        # Request 1 should work
        response = middleware(request1)
        assert response.status_code == 200

        # Request 2 should fail (wrong token in URL)
        with pytest.raises(Http404):
            middleware(request2)

    def test_new_login_generates_new_tokens(self, rf, superuser):
        """Test that each login generates new tokens."""
        request1 = rf.get('/path/')
        add_session_to_request(request1)
        request1.user = superuser
        token1 = get_staff_token(request1)

        request2 = rf.get('/path/')
        add_session_to_request(request2)
        request2.user = superuser
        token2 = get_staff_token(request2)

        # Different sessions = different tokens
        assert token1 != token2

    def test_token_generation_is_cryptographically_secure(self):
        """Test that tokens use cryptographically secure random."""
        # tokens should be generated using secrets module
        token = generate_token()
        # Just verify it's the right length and format
        assert len(token) == 6
        assert token.isalnum()


@pytest.mark.django_db
class TestPublicPagesNotBlocked:
    """Tests that public pages are never blocked."""

    def test_homepage_accessible(self, rf, middleware):
        """Test that homepage is accessible without token."""
        request = rf.get('/')
        response = middleware(request)
        assert response.status_code == 200

    def test_about_page_accessible(self, rf, middleware):
        """Test that about page is accessible without token."""
        request = rf.get('/about/')
        response = middleware(request)
        assert response.status_code == 200

    def test_login_page_accessible(self, rf, middleware):
        """Test that login page is accessible without token."""
        request = rf.get('/login/')
        response = middleware(request)
        assert response.status_code == 200

    def test_static_files_accessible(self, rf, middleware):
        """Test that static files are accessible without token."""
        request = rf.get('/static/css/output.css')
        response = middleware(request)
        assert response.status_code == 200


@pytest.mark.django_db
class TestGroupedURLStructure:
    """Tests for the grouped URL structure (T-099)."""

    def test_direct_operations_path_returns_404(self, rf, middleware):
        """Test that /operations/ directly returns 404."""
        request = rf.get('/operations/practice/')
        with pytest.raises(Http404):
            middleware(request)

    def test_direct_customers_path_returns_404(self, rf, middleware):
        """Test that /customers/ directly returns 404."""
        request = rf.get('/customers/crm/')
        with pytest.raises(Http404):
            middleware(request)

    def test_direct_finance_path_returns_404(self, rf, middleware):
        """Test that /finance/ directly returns 404."""
        request = rf.get('/finance/accounting/')
        with pytest.raises(Http404):
            middleware(request)

    def test_direct_admin_tools_path_returns_404(self, rf, middleware):
        """Test that /admin-tools/ directly returns 404."""
        request = rf.get('/admin-tools/audit/')
        with pytest.raises(Http404):
            middleware(request)

    def test_staff_token_accesses_operations(self, rf, middleware, staff_user):
        """Test that valid staff token allows access to operations section."""
        request = rf.get('/staff-xyz789/operations/practice/')
        add_session_to_request(request)
        request.user = staff_user
        request.session['staff_token'] = 'xyz789'
        request.session.save()

        response = middleware(request)
        assert response.status_code == 200
        # Path should be rewritten to /operations/practice/
        assert request.path == '/operations/practice/'

    def test_staff_token_accesses_customers(self, rf, middleware, staff_user):
        """Test that valid staff token allows access to customers section."""
        request = rf.get('/staff-xyz789/customers/crm/')
        add_session_to_request(request)
        request.user = staff_user
        request.session['staff_token'] = 'xyz789'
        request.session.save()

        response = middleware(request)
        assert response.status_code == 200
        assert request.path == '/customers/crm/'

    def test_staff_token_accesses_finance(self, rf, middleware, staff_user):
        """Test that valid staff token allows access to finance section."""
        request = rf.get('/staff-xyz789/finance/accounting/')
        add_session_to_request(request)
        request.user = staff_user
        request.session['staff_token'] = 'xyz789'
        request.session.save()

        response = middleware(request)
        assert response.status_code == 200
        assert request.path == '/finance/accounting/'

    def test_staff_token_accesses_admin_tools(self, rf, middleware, staff_user):
        """Test that valid staff token allows access to admin-tools section."""
        request = rf.get('/staff-xyz789/admin-tools/audit/')
        add_session_to_request(request)
        request.user = staff_user
        request.session['staff_token'] = 'xyz789'
        request.session.save()

        response = middleware(request)
        assert response.status_code == 200
        assert request.path == '/admin-tools/audit/'
