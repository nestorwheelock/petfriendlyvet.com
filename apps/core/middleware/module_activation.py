"""Module activation middleware.

This middleware checks if modules are enabled and returns 404 for disabled modules.
It integrates with the ModuleConfig model to control access to entire Django apps.
"""
import re
from django.core.cache import cache
from django.http import Http404

from apps.core.models import ModuleConfig


# Cache timeout for module status (5 minutes)
MODULE_CACHE_TIMEOUT = 300

# Patterns that are always allowed (never blocked)
ALWAYS_ALLOWED_PATTERNS = [
    r'^/$',                          # Homepage
    r'^/about/?',                    # About page
    r'^/services/?',                 # Services page
    r'^/contact/?',                  # Contact page
    r'^/health/?',                   # Health check
    r'^/static/',                    # Static files
    r'^/media/',                     # Media files
    r'^/api/public/',                # Public API endpoints
    r'^/i18n/',                      # Language switching
    r'^/jsi18n/',                    # JavaScript i18n
    r'^/__debug__/',                 # Debug toolbar
    r'^/login/?',                    # Login page
    r'^/logout/?',                   # Logout
    r'^/password/',                  # Password reset
]

# Pattern to extract module from staff URLs
# Format: /staff-{token}/{section}/{module}/...
STAFF_URL_PATTERN = re.compile(r'^/staff-[a-zA-Z0-9]+/[a-z]+/([a-z-]+)/')

# Pattern to extract module from admin panel URLs (for superadmin)
# Format: /panel-{token}/...
ADMIN_URL_PATTERN = re.compile(r'^/panel-[a-zA-Z0-9]+/')


def get_module_from_path(path: str) -> str | None:
    """Extract the module name from a URL path.

    Args:
        path: The request path (e.g., '/staff-abc123/operations/appointments/')

    Returns:
        Module name (e.g., 'appointments') or None if path doesn't match a module.
    """
    # Check if this is a staff URL
    match = STAFF_URL_PATTERN.match(path)
    if match:
        return match.group(1).replace('-', '_')  # Convert URL slug to app name

    return None


def get_module_enabled_status(app_name: str) -> bool:
    """Get whether a module is enabled, with caching.

    Args:
        app_name: The Django app name (e.g., 'appointments')

    Returns:
        True if enabled or no config exists (default enabled), False if explicitly disabled.
    """
    cache_key = f'module_enabled:{app_name}'

    # Try cache first
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # Query database
    try:
        config = ModuleConfig.objects.get(app_name=app_name)
        is_enabled = config.is_enabled
    except ModuleConfig.DoesNotExist:
        # No config means default enabled
        is_enabled = True

    # Cache the result
    cache.set(cache_key, is_enabled, MODULE_CACHE_TIMEOUT)

    return is_enabled


def invalidate_module_cache(app_name: str) -> None:
    """Invalidate the cache for a specific module.

    Call this when a module's enabled status changes.

    Args:
        app_name: The Django app name to invalidate.
    """
    cache_key = f'module_enabled:{app_name}'
    cache.delete(cache_key)


def is_always_allowed(path: str) -> bool:
    """Check if a path should always be allowed (never blocked).

    Args:
        path: The request path.

    Returns:
        True if the path should always be allowed.
    """
    for pattern in ALWAYS_ALLOWED_PATTERNS:
        if re.match(pattern, path):
            return True
    return False


class ModuleActivationMiddleware:
    """Middleware that blocks access to disabled modules.

    Disabled modules return 404 (not 403) to avoid revealing their existence.
    Public pages, static files, and login pages are never blocked.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Always allow certain patterns
        if is_always_allowed(path):
            return self.get_response(request)

        # Extract module from path
        module_name = get_module_from_path(path)

        # If no module identified, allow through
        if module_name is None:
            return self.get_response(request)

        # Check if module is enabled
        if not get_module_enabled_status(module_name):
            # Return 404 to hide existence of disabled modules
            raise Http404("Page not found")

        return self.get_response(request)


# Signal handler to invalidate cache when ModuleConfig changes
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


@receiver(post_save, sender=ModuleConfig)
def on_module_config_save(sender, instance, **kwargs):
    """Invalidate cache when module config is saved."""
    invalidate_module_cache(instance.app_name)


@receiver(post_delete, sender=ModuleConfig)
def on_module_config_delete(sender, instance, **kwargs):
    """Invalidate cache when module config is deleted."""
    invalidate_module_cache(instance.app_name)
