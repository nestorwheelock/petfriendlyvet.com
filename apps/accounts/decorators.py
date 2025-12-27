"""Permission decorators for function-based views."""
from functools import wraps

from django.core.exceptions import PermissionDenied


def require_permission(module, action='view'):
    """Decorator to require module permission for function-based views.

    Usage:
        @require_permission('practice', 'manage')
        def staff_create(request):
            ...

    Args:
        module: The module name (e.g., 'practice', 'accounting')
        action: The action name (e.g., 'view', 'manage')

    Raises:
        PermissionDenied: If user lacks the required permission.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.has_module_permission(module, action):
                raise PermissionDenied(f"Permission denied: {module}.{action}")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
