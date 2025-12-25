"""Audit logging middleware."""
import re

from .models import AuditLog
from .signals import set_current_user


class AuditMiddleware:
    """Middleware to automatically log staff page views."""

    # Routes to audit (staff-only pages)
    AUDITED_PREFIXES = [
        '/inventory/',
        '/practice/',
        '/referrals/',
        '/pharmacy/',
        '/crm/',
        '/billing/',
    ]

    # High sensitivity paths
    HIGH_SENSITIVITY_PATTERNS = [
        r'^/referrals/outbound/',
        r'^/pharmacy/prescriptions/',
        r'^/practice/settings/',
        r'^/billing/invoices/',
        r'^/crm/customers/\d+/',
    ]

    # Pattern to extract resource ID from URL
    ID_PATTERN = re.compile(r'/(\d+)/?$')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Set current user for signal handlers
        if hasattr(request, 'user') and request.user.is_authenticated:
            set_current_user(request.user, request)

        response = self.get_response(request)

        # Only audit staff users on successful GET requests
        if (hasattr(request, 'user') and
            request.user.is_authenticated and
            request.user.is_staff and
            request.method == 'GET' and
            response.status_code == 200 and
            self._should_audit(request.path)):

            AuditLog.objects.create(
                user=request.user,
                action='view',
                resource_type=self._get_resource_type(request.path),
                resource_id=self._extract_resource_id(request.path),
                url_path=request.path,
                method=request.method,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                sensitivity=self._get_sensitivity(request.path),
            )

        # Clear thread-local user after request
        set_current_user(None, None)

        return response

    def _should_audit(self, path):
        """Check if path should be audited."""
        return any(path.startswith(prefix) for prefix in self.AUDITED_PREFIXES)

    def _get_resource_type(self, path):
        """Extract resource type from URL path."""
        # Remove trailing slash and ID
        clean_path = re.sub(r'/\d+/?$', '', path)
        clean_path = clean_path.rstrip('/')

        # Map path to resource type
        path_map = {
            '/inventory': 'inventory.dashboard',
            '/inventory/stock': 'inventory.stock',
            '/inventory/batches': 'inventory.batch',
            '/inventory/movements': 'inventory.movement',
            '/inventory/movements/add': 'inventory.movement',
            '/inventory/suppliers': 'inventory.supplier',
            '/inventory/purchase-orders': 'inventory.purchase_order',
            '/inventory/alerts': 'inventory.alert',
            '/inventory/expiring': 'inventory.expiring',
            '/practice': 'practice.dashboard',
            '/practice/staff': 'practice.staff',
            '/practice/schedule': 'practice.schedule',
            '/practice/shifts': 'practice.shift',
            '/practice/time': 'practice.time_tracking',
            '/practice/tasks': 'practice.task',
            '/practice/settings': 'practice.settings',
            '/referrals': 'referrals.dashboard',
            '/referrals/specialists': 'referrals.specialist',
            '/referrals/outbound': 'referrals.referral',
            '/referrals/visiting': 'referrals.visiting',
            '/pharmacy': 'pharmacy.dashboard',
            '/pharmacy/prescriptions': 'pharmacy.prescription',
            '/crm': 'crm.dashboard',
            '/crm/customers': 'crm.customer',
            '/billing': 'billing.dashboard',
            '/billing/invoices': 'billing.invoice',
        }

        return path_map.get(clean_path, f'unknown.{clean_path}')

    def _extract_resource_id(self, path):
        """Extract resource ID from URL if present."""
        match = self.ID_PATTERN.search(path)
        return match.group(1) if match else ''

    def _get_sensitivity(self, path):
        """Determine sensitivity level based on path."""
        for pattern in self.HIGH_SENSITIVITY_PATTERNS:
            if re.match(pattern, path):
                return 'high'
        return 'normal'

    def _get_client_ip(self, request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
