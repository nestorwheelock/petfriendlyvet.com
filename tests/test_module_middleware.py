"""Tests for module activation middleware."""
import pytest
from django.test import Client, RequestFactory, override_settings
from django.http import Http404
from django.contrib.auth import get_user_model

from apps.core.models import ModuleConfig
from apps.core.middleware.module_activation import ModuleActivationMiddleware


User = get_user_model()


@pytest.fixture
def rf():
    """Request factory fixture."""
    return RequestFactory()


@pytest.fixture
def middleware():
    """Module activation middleware fixture."""
    def get_response(request):
        from django.http import HttpResponse
        return HttpResponse('OK')
    return ModuleActivationMiddleware(get_response)


@pytest.fixture
def appointments_module(db):
    """Create enabled appointments module."""
    return ModuleConfig.objects.create(
        app_name='appointments',
        display_name='Appointments',
        section='operations',
        is_enabled=True,
    )


@pytest.fixture
def disabled_inventory_module(db):
    """Create disabled inventory module."""
    return ModuleConfig.objects.create(
        app_name='inventory',
        display_name='Inventory',
        section='admin',
        is_enabled=False,
    )


@pytest.mark.django_db
class TestModuleActivationMiddleware:
    """Tests for ModuleActivationMiddleware."""

    def test_enabled_module_accessible(self, rf, middleware, appointments_module):
        """Test that enabled modules are accessible."""
        request = rf.get('/staff-abc123/operations/appointments/')
        response = middleware(request)
        assert response.status_code == 200

    def test_disabled_module_returns_404(self, rf, middleware, disabled_inventory_module):
        """Test that disabled modules return 404."""
        request = rf.get('/staff-abc123/admin/inventory/')
        with pytest.raises(Http404):
            middleware(request)

    def test_disabled_module_not_403(self, rf, middleware, disabled_inventory_module):
        """Test that disabled modules return 404 (not 403 - no hint of existence)."""
        request = rf.get('/staff-abc123/admin/inventory/')
        try:
            middleware(request)
            assert False, "Should have raised Http404"
        except Http404:
            pass  # Expected
        except Exception as e:
            # Should not be 403 or other exception
            assert '403' not in str(e)

    def test_unknown_path_passes_through(self, rf, middleware):
        """Test that paths not matching module patterns pass through."""
        request = rf.get('/about/')
        response = middleware(request)
        assert response.status_code == 200

    def test_public_pages_not_blocked(self, rf, middleware):
        """Test that public pages (home, about, services) are never blocked."""
        public_paths = ['/', '/about/', '/services/', '/contact/']
        for path in public_paths:
            request = rf.get(path)
            response = middleware(request)
            assert response.status_code == 200, f"Public path {path} was blocked"

    def test_static_files_not_blocked(self, rf, middleware):
        """Test that static and media files are not blocked."""
        static_paths = ['/static/css/output.css', '/media/images/logo.png']
        for path in static_paths:
            request = rf.get(path)
            response = middleware(request)
            assert response.status_code == 200, f"Static path {path} was blocked"

    def test_module_without_config_passes(self, rf, middleware):
        """Test that modules without config are accessible (default enabled)."""
        # No ModuleConfig exists for 'unknown_module'
        request = rf.get('/staff-abc123/operations/unknown/')
        response = middleware(request)
        assert response.status_code == 200


@pytest.mark.django_db
class TestModulePathExtraction:
    """Tests for extracting module name from URL path."""

    def test_extract_module_from_staff_path(self, rf, middleware):
        """Test extracting module name from staff URL pattern."""
        from apps.core.middleware.module_activation import get_module_from_path

        # Staff URLs follow pattern: /staff-{token}/{section}/{module}/
        assert get_module_from_path('/staff-abc123/operations/appointments/') == 'appointments'
        assert get_module_from_path('/staff-abc123/finance/billing/') == 'billing'
        assert get_module_from_path('/staff-abc123/admin/inventory/') == 'inventory'

    def test_extract_module_returns_none_for_public(self, rf, middleware):
        """Test that public paths return None."""
        from apps.core.middleware.module_activation import get_module_from_path

        assert get_module_from_path('/') is None
        assert get_module_from_path('/about/') is None
        assert get_module_from_path('/contact/') is None

    def test_extract_module_returns_none_for_static(self, rf, middleware):
        """Test that static/media paths return None."""
        from apps.core.middleware.module_activation import get_module_from_path

        assert get_module_from_path('/static/css/output.css') is None
        assert get_module_from_path('/media/uploads/image.jpg') is None


@pytest.mark.django_db
class TestModuleStatusCache:
    """Tests for module status caching."""

    def test_middleware_caches_module_status(self, rf, middleware, appointments_module):
        """Test that module status is cached for performance."""
        from apps.core.middleware.module_activation import get_module_enabled_status
        from django.core.cache import cache

        # Clear cache
        cache.clear()

        # First call should hit database
        is_enabled = get_module_enabled_status('appointments')
        assert is_enabled is True

        # Value should be cached
        cache_key = 'module_enabled:appointments'
        cached = cache.get(cache_key)
        assert cached is True

    def test_cache_invalidates_on_module_change(self, rf, appointments_module):
        """Test that cache invalidates when module is toggled."""
        from apps.core.middleware.module_activation import get_module_enabled_status
        from django.core.cache import cache

        # Clear and populate cache
        cache.clear()
        assert get_module_enabled_status('appointments') is True

        # Disable module - should invalidate cache
        appointments_module.disable()

        # Should now return False
        assert get_module_enabled_status('appointments') is False
