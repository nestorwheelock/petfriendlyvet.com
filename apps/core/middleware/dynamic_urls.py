"""Dynamic URL middleware for session-based admin and staff tokens.

This middleware provides security by obscuring admin and staff URLs with
session-bound tokens. Direct access to /admin/ or /accounting/ returns 404.
Only URLs with valid session tokens are routed to protected areas.

URL Patterns:
    /panel-{admin_token}/  -> Django admin (superusers only)
    /staff-{staff_token}/operations/appointments/ -> Staff module
"""
import re
import secrets

from django.http import Http404


# Token configuration
TOKEN_LENGTH = 6

# URL patterns for dynamic routing
ADMIN_PATTERN = re.compile(r'^/panel-([a-zA-Z0-9]{6})(/.*)?$')
STAFF_PATTERN = re.compile(r'^/staff-([a-zA-Z0-9]{6})/(.*)$')

# URLs that are always blocked (return 404)
BLOCKED_PATTERNS = [
    re.compile(r'^/admin(/.*)?$'),
]

# Direct module URLs that should be blocked (must use /staff-{token}/...)
# Block both old-style direct paths AND new grouped paths when accessed directly
DIRECT_MODULE_PATTERNS = [
    # Old-style direct module access (legacy, blocked)
    re.compile(r'^/accounting(/.*)?$'),
    re.compile(r'^/inventory(/.*)?$'),
    re.compile(r'^/appointments(/.*)?$'),
    re.compile(r'^/patients(/.*)?$'),
    re.compile(r'^/clients(/.*)?$'),
    re.compile(r'^/billing(/.*)?$'),
    re.compile(r'^/reports(/.*)?$'),
    re.compile(r'^/communications(/.*)?$'),
    re.compile(r'^/medical-records(/.*)?$'),
    re.compile(r'^/practice(/.*)?$'),
    re.compile(r'^/referrals(/.*)?$'),
    re.compile(r'^/crm(/.*)?$'),
    re.compile(r'^/marketing(/.*)?$'),
    re.compile(r'^/audit(/.*)?$'),
    # New grouped paths (must use /staff-{token}/section/...)
    re.compile(r'^/operations(/.*)?$'),
    re.compile(r'^/customers(/.*)?$'),
    re.compile(r'^/finance(/.*)?$'),
    re.compile(r'^/admin-tools(/.*)?$'),
]

# Public paths that never require tokens
PUBLIC_PATHS = [
    '/',
    '/about/',
    '/contact/',
    '/services/',
    '/login/',
    '/logout/',
    '/register/',
    '/password-reset/',
]

# Static/media paths
STATIC_PREFIXES = [
    '/static/',
    '/media/',
    '/__reload__/',
    '/_allauth/',
]


def generate_token() -> str:
    """Generate a cryptographically secure URL-safe token.

    Returns:
        A 6-character alphanumeric token.
    """
    alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(secrets.choice(alphabet) for _ in range(TOKEN_LENGTH))


def validate_token(request, token: str, token_type: str) -> bool:
    """Validate a token against the session.

    Args:
        request: The Django request object.
        token: The token from the URL.
        token_type: Either 'admin_token' or 'staff_token'.

    Returns:
        True if token matches session token, False otherwise.
    """
    if not hasattr(request, 'session'):
        return False

    session_token = request.session.get(token_type)
    if session_token is None:
        return False

    return secrets.compare_digest(token, session_token)


def get_admin_token(request) -> str | None:
    """Get or create admin token for superuser session.

    Args:
        request: The Django request object.

    Returns:
        The admin token if user is superuser, None otherwise.
    """
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return None

    if not request.user.is_superuser:
        return None

    if not hasattr(request, 'session'):
        return None

    # Check if token exists in session
    if 'admin_token' not in request.session:
        request.session['admin_token'] = generate_token()
        request.session.modified = True

    return request.session['admin_token']


def get_staff_token(request) -> str | None:
    """Get or create staff token for staff/superuser session.

    Args:
        request: The Django request object.

    Returns:
        The staff token if user is staff, None otherwise.
    """
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return None

    if not request.user.is_staff:
        return None

    if not hasattr(request, 'session'):
        return None

    # Check if token exists in session
    if 'staff_token' not in request.session:
        request.session['staff_token'] = generate_token()
        request.session.modified = True

    return request.session['staff_token']


def is_public_path(path: str) -> bool:
    """Check if path is a public (non-protected) path.

    Args:
        path: The request path.

    Returns:
        True if path is public and doesn't need token.
    """
    # Exact matches
    if path in PUBLIC_PATHS:
        return True

    # Static/media prefixes
    for prefix in STATIC_PREFIXES:
        if path.startswith(prefix):
            return True

    return False


def is_blocked_path(path: str) -> bool:
    """Check if path should be blocked entirely.

    Args:
        path: The request path.

    Returns:
        True if path should return 404.
    """
    # Check blocked patterns (like /admin/)
    for pattern in BLOCKED_PATTERNS:
        if pattern.match(path):
            return True

    # Check direct module access (like /accounting/)
    for pattern in DIRECT_MODULE_PATTERNS:
        if pattern.match(path):
            return True

    return False


class DynamicURLMiddleware:
    """Middleware for dynamic URL routing with session-based tokens.

    This middleware:
    1. Blocks direct access to /admin/ (returns 404)
    2. Routes /panel-{token}/ to Django admin for superusers with valid token
    3. Blocks direct access to staff modules (returns 404)
    4. Routes /staff-{token}/section/module/ to staff areas for valid tokens
    5. Passes through public paths without modification
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Public paths pass through
        if is_public_path(path):
            return self.get_response(request)

        # Blocked paths return 404
        if is_blocked_path(path):
            raise Http404("Page not found")

        # Check for admin panel access (/panel-{token}/)
        admin_match = ADMIN_PATTERN.match(path)
        if admin_match:
            token = admin_match.group(1)
            remainder = admin_match.group(2) or '/'

            # Must have session
            if not hasattr(request, 'session'):
                raise Http404("Page not found")

            # Validate token
            if not validate_token(request, token, 'admin_token'):
                raise Http404("Page not found")

            # Must be superuser
            if not hasattr(request, 'user') or not request.user.is_superuser:
                raise Http404("Page not found")

            # Rewrite path to /admin/
            request.path = '/admin' + remainder
            request.path_info = request.path

            return self.get_response(request)

        # Check for staff access (/staff-{token}/...)
        staff_match = STAFF_PATTERN.match(path)
        if staff_match:
            token = staff_match.group(1)
            remainder = staff_match.group(2)

            # Must have session
            if not hasattr(request, 'session'):
                raise Http404("Page not found")

            # Validate token
            if not validate_token(request, token, 'staff_token'):
                raise Http404("Page not found")

            # Must be staff
            if not hasattr(request, 'user') or not request.user.is_staff:
                raise Http404("Page not found")

            # Rewrite path to the actual module path
            # /staff-abc123/operations/appointments/ -> /operations/appointments/
            request.path = '/' + remainder
            request.path_info = request.path

            return self.get_response(request)

        # All other paths pass through
        return self.get_response(request)
