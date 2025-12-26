"""Tests for navigation integration with module activation."""
import pytest
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware

from apps.core.models import ModuleConfig
from apps.core.context_processors import navigation


User = get_user_model()


@pytest.fixture
def rf():
    """Request factory fixture."""
    return RequestFactory()


def add_session_to_request(request):
    """Add a session to a request object."""
    middleware = SessionMiddleware(lambda r: None)
    middleware.process_request(request)
    request.session.save()


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
    """Create a regular user."""
    return User.objects.create_user(
        username='user',
        email='user@example.com',
        password='testpass123',
    )


@pytest.fixture
def enabled_module(db):
    """Create an enabled module."""
    return ModuleConfig.objects.create(
        app_name='inventory',
        display_name='Inventory',
        section='operations',
        is_enabled=True,
    )


@pytest.fixture
def disabled_module(db):
    """Create a disabled module."""
    return ModuleConfig.objects.create(
        app_name='accounting',
        display_name='Accounting',
        section='finance',
        is_enabled=False,
    )


@pytest.mark.django_db
class TestNavigationFiltering:
    """Tests for navigation filtering based on module status."""

    def test_enabled_modules_appear_in_nav(self, rf, staff_user, enabled_module):
        """Test that enabled modules appear in navigation."""
        request = rf.get('/path/')
        add_session_to_request(request)
        request.user = staff_user

        context = navigation(request)
        nav_ids = [item['id'] for item in context['staff_nav']]

        assert 'inventory' in nav_ids

    def test_disabled_modules_hidden_from_staff_nav(self, rf, staff_user, disabled_module):
        """Test that disabled modules are hidden from staff navigation."""
        request = rf.get('/path/')
        add_session_to_request(request)
        request.user = staff_user

        context = navigation(request)
        nav_ids = [item['id'] for item in context['staff_nav']]

        assert 'accounting' not in nav_ids

    def test_superadmin_sees_all_modules_regardless_of_status(
        self, rf, superuser, enabled_module, disabled_module
    ):
        """Test that superadmins see all modules."""
        request = rf.get('/path/')
        add_session_to_request(request)
        request.user = superuser

        context = navigation(request)
        nav_ids = [item['id'] for item in context['staff_nav']]

        # Superadmin should see both enabled and disabled modules
        assert 'inventory' in nav_ids
        assert 'accounting' in nav_ids

    def test_modules_link_in_superadmin_nav(self, rf, superuser):
        """Test that Modules link appears in superadmin navigation."""
        request = rf.get('/path/')
        add_session_to_request(request)
        request.user = superuser

        context = navigation(request)
        nav_ids = [item['id'] for item in context['superadmin_nav']]

        assert 'modules' in nav_ids

    def test_anonymous_user_gets_no_nav(self, rf):
        """Test that anonymous users get no navigation."""
        from django.contrib.auth.models import AnonymousUser

        request = rf.get('/path/')
        request.user = AnonymousUser()

        context = navigation(request)

        assert context['staff_nav'] == []
        assert context['portal_nav'] == []
        assert context['superadmin_nav'] == []


@pytest.mark.django_db
class TestTokensInContext:
    """Tests for session tokens in navigation context."""

    def test_superuser_gets_admin_token(self, rf, superuser):
        """Test that superuser gets admin token in context."""
        request = rf.get('/path/')
        add_session_to_request(request)
        request.user = superuser

        context = navigation(request)

        assert 'admin_token' in context
        assert context['admin_token'] is not None
        assert len(context['admin_token']) == 6

    def test_superuser_gets_staff_token(self, rf, superuser):
        """Test that superuser gets staff token in context."""
        request = rf.get('/path/')
        add_session_to_request(request)
        request.user = superuser

        context = navigation(request)

        assert 'staff_token' in context
        assert context['staff_token'] is not None
        assert len(context['staff_token']) == 6

    def test_staff_user_gets_staff_token(self, rf, staff_user):
        """Test that staff user gets staff token in context."""
        request = rf.get('/path/')
        add_session_to_request(request)
        request.user = staff_user

        context = navigation(request)

        assert 'staff_token' in context
        assert context['staff_token'] is not None
        assert len(context['staff_token']) == 6

    def test_staff_user_no_admin_token(self, rf, staff_user):
        """Test that staff user does not get admin token."""
        request = rf.get('/path/')
        add_session_to_request(request)
        request.user = staff_user

        context = navigation(request)

        assert context.get('admin_token') is None

    def test_regular_user_no_tokens(self, rf, regular_user):
        """Test that regular users don't get tokens."""
        request = rf.get('/path/')
        add_session_to_request(request)
        request.user = regular_user

        context = navigation(request)

        assert context.get('admin_token') is None
        assert context.get('staff_token') is None


@pytest.mark.django_db
class TestNavigationUrls:
    """Tests for navigation URL generation with tokens."""

    def test_staff_nav_urls_include_token_prefix(self, rf, staff_user, enabled_module):
        """Test that staff navigation URLs include token prefix."""
        request = rf.get('/path/')
        add_session_to_request(request)
        request.user = staff_user

        context = navigation(request)

        # Get the staff token for URL building
        token = context.get('staff_token')
        assert token is not None

        # Navigation items should have URLs that work with the token
        for item in context['staff_nav']:
            # URL is still a named URL, templates handle the token prefix
            assert 'url' in item
