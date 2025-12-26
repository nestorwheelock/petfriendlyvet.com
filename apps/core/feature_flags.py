"""Feature flag utilities for granular feature control.

This module provides utilities for checking feature flags in code,
including a decorator for views and cache management.
"""
from functools import wraps
from typing import Callable

from django.core.cache import cache
from django.http import Http404

from apps.core.models import FeatureFlag


# Cache timeout for feature flags (5 minutes)
FEATURE_CACHE_TIMEOUT = 300


def is_enabled(key: str) -> bool:
    """Check if a feature flag is enabled.

    Args:
        key: The feature flag key (e.g., 'appointments.online_booking')

    Returns:
        True if the feature is enabled, False otherwise.
        Returns False for non-existent flags.
    """
    cache_key = f'feature_flag:{key}'

    # Try cache first
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # Query database
    try:
        flag = FeatureFlag.objects.get(key=key)
        result = flag.is_enabled
    except FeatureFlag.DoesNotExist:
        result = False

    # Cache the result
    cache.set(cache_key, result, FEATURE_CACHE_TIMEOUT)

    return result


def invalidate_feature_cache(key: str) -> None:
    """Invalidate the cache for a specific feature flag.

    Call this when a feature flag's status changes.

    Args:
        key: The feature flag key to invalidate.
    """
    cache_key = f'feature_flag:{key}'
    cache.delete(cache_key)


def require_feature(key: str) -> Callable:
    """Decorator that requires a feature flag to be enabled.

    If the feature is disabled, returns a 404 response.

    Args:
        key: The feature flag key that must be enabled.

    Returns:
        Decorated view function.

    Example:
        @require_feature('appointments.online_booking')
        def online_booking_view(request):
            ...
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not is_enabled(key):
                raise Http404("Page not found")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# Signal handlers to invalidate cache when FeatureFlag changes
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


@receiver(post_save, sender=FeatureFlag)
def on_feature_flag_save(sender, instance, **kwargs):
    """Invalidate cache when feature flag is saved."""
    invalidate_feature_cache(instance.key)


@receiver(post_delete, sender=FeatureFlag)
def on_feature_flag_delete(sender, instance, **kwargs):
    """Invalidate cache when feature flag is deleted."""
    invalidate_feature_cache(instance.key)
