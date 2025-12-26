"""Core utility functions for the application."""

from django.http import HttpResponseRedirect
from django.urls import reverse


def staff_redirect(request, view_name, *args, **kwargs):
    """Redirect to a staff URL with the session's staff token prefix.

    When views call redirect('inventory:stock'), Django generates URLs like
    /operations/inventory/stock/ which get blocked by the DynamicURLMiddleware
    because direct access to /operations/ paths is forbidden for security.

    This function builds the full URL with the staff token prefix:
    /staff-{token}/operations/inventory/stock/

    Args:
        request: The Django request object (needed to access session token)
        view_name: The URL name to redirect to (e.g., 'inventory:stock')
        *args: Positional arguments for reverse()
        **kwargs: Keyword arguments for reverse()

    Returns:
        HttpResponseRedirect to the staff-prefixed URL

    Example:
        # In a view:
        from apps.core.utils import staff_redirect

        def my_view(request):
            # Instead of: return redirect('inventory:stock')
            return staff_redirect(request, 'inventory:stock')

            # With URL arguments:
            return staff_redirect(request, 'inventory:supplier_detail', pk=supplier.pk)
    """
    # Get staff token from session
    staff_token = request.session.get('staff_token')

    if not staff_token:
        # Fallback to regular redirect if no token (shouldn't happen for staff)
        url = reverse(view_name, args=args, kwargs=kwargs)
        return HttpResponseRedirect(url)

    # Build the URL with reverse()
    base_url = reverse(view_name, args=args, kwargs=kwargs)

    # Prefix with staff token
    # base_url is like /operations/inventory/stock/
    # We want /staff-{token}/operations/inventory/stock/
    staff_url = f'/staff-{staff_token}{base_url}'

    return HttpResponseRedirect(staff_url)


def get_staff_url(request, view_name, *args, **kwargs):
    """Get a staff URL with the session's staff token prefix.

    Similar to staff_redirect but returns the URL string instead of
    a redirect response. Useful for building URLs in templates or
    when you need the URL for other purposes.

    Args:
        request: The Django request object (needed to access session token)
        view_name: The URL name (e.g., 'inventory:stock')
        *args: Positional arguments for reverse()
        **kwargs: Keyword arguments for reverse()

    Returns:
        The full staff-prefixed URL string
    """
    staff_token = request.session.get('staff_token')
    base_url = reverse(view_name, args=args, kwargs=kwargs)

    if not staff_token:
        return base_url

    return f'/staff-{staff_token}{base_url}'
