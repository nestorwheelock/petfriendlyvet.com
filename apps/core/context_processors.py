"""
Context processors for core application.
Provides navigation data for staff and customer portals.
"""

from django.utils.translation import gettext_lazy as _


# Staff navigation modules - all 10 staff backend sections
STAFF_NAV = [
    # Operations
    {'id': 'practice', 'icon': 'users', 'label': _('Practice'), 'url': 'practice:dashboard', 'section': 'Operations'},
    {'id': 'inventory', 'icon': 'package', 'label': _('Inventory'), 'url': 'inventory:dashboard', 'section': 'Operations'},
    {'id': 'referrals', 'icon': 'share-2', 'label': _('Referrals'), 'url': 'referrals:dashboard', 'section': 'Operations'},
    {'id': 'delivery', 'icon': 'truck', 'label': _('Delivery'), 'url': 'delivery:delivery_admin:dashboard', 'section': 'Operations'},
    # Customers
    {'id': 'crm', 'icon': 'heart', 'label': _('CRM'), 'url': 'crm:dashboard', 'section': 'Customers'},
    {'id': 'marketing', 'icon': 'mail', 'label': _('Marketing'), 'url': 'marketing:dashboard', 'section': 'Customers'},
    # Finance
    {'id': 'accounting', 'icon': 'dollar-sign', 'label': _('Accounting'), 'url': 'accounting:dashboard', 'section': 'Finance'},
    {'id': 'reports', 'icon': 'bar-chart-2', 'label': _('Reports'), 'url': 'reports:dashboard', 'section': 'Finance'},
    # Admin
    {'id': 'audit', 'icon': 'shield', 'label': _('Audit'), 'url': 'audit:dashboard', 'section': 'Admin'},
    {'id': 'ai_chat', 'icon': 'message-circle', 'label': _('AI Chat'), 'url': 'ai_assistant:admin_chat', 'section': 'Admin'},
]

# Customer portal navigation - all 8 customer sections
PORTAL_NAV = [
    # My Account
    {'id': 'pets', 'icon': 'heart', 'label': _('My Pets'), 'url': 'pets:dashboard', 'section': 'My Account'},
    {'id': 'appointments', 'icon': 'calendar', 'label': _('Appointments'), 'url': 'appointments:my_appointments', 'section': 'My Account'},
    {'id': 'pharmacy', 'icon': 'pill', 'label': _('Pharmacy'), 'url': 'pharmacy:prescription_list', 'section': 'My Account'},
    # Shopping
    {'id': 'orders', 'icon': 'shopping-bag', 'label': _('Orders'), 'url': 'store:order_list', 'section': 'Shopping'},
    {'id': 'billing', 'icon': 'credit-card', 'label': _('Billing'), 'url': 'billing:invoice_list', 'section': 'Shopping'},
    {'id': 'loyalty', 'icon': 'star', 'label': _('Rewards'), 'url': 'loyalty:dashboard', 'section': 'Shopping'},
    # Help
    {'id': 'emergency', 'icon': 'alert-circle', 'label': _('Emergency'), 'url': 'emergency:home', 'section': 'Help'},
    {'id': 'profile', 'icon': 'user', 'label': _('Profile'), 'url': 'accounts:profile', 'section': 'Help'},
]

# Superadmin navigation - system administration sections
SUPERADMIN_NAV = [
    {'id': 'superadmin_dashboard', 'icon': 'home', 'label': _('Dashboard'), 'url': 'superadmin:dashboard', 'section': 'System Admin'},
    {'id': 'users', 'icon': 'users', 'label': _('Users'), 'url': 'superadmin:user_list', 'section': 'System Admin'},
    {'id': 'roles', 'icon': 'key', 'label': _('Roles'), 'url': 'superadmin:role_list', 'section': 'System Admin'},
    {'id': 'settings', 'icon': 'settings', 'label': _('Settings'), 'url': 'superadmin:settings', 'section': 'System Admin'},
    {'id': 'audit_dashboard', 'icon': 'eye', 'label': _('Audit Logs'), 'url': 'superadmin:audit_dashboard', 'section': 'System Admin'},
    {'id': 'monitoring', 'icon': 'activity', 'label': _('Monitoring'), 'url': 'superadmin:monitoring', 'section': 'System Admin'},
]

# Namespace to nav ID mapping for nested namespaces
NAMESPACE_MAPPING = {
    'delivery:delivery_admin': 'delivery',
    'ai_assistant': 'ai_chat',
    'superadmin': 'superadmin_dashboard',
}


def navigation(request):
    """
    Context processor that provides navigation data for templates.

    Returns:
        dict: Contains staff_nav, portal_nav, superadmin_nav, active_nav, and is_superadmin
    """
    user = getattr(request, 'user', None)

    # Anonymous users get no navigation
    if user is None or not user.is_authenticated:
        return {
            'staff_nav': [],
            'portal_nav': [],
            'superadmin_nav': [],
            'active_nav': '',
            'is_superadmin': False,
        }

    # Determine active navigation from URL namespace
    active_nav = ''
    resolver_match = getattr(request, 'resolver_match', None)
    if resolver_match:
        namespace = resolver_match.namespace or ''

        # Check for mapped namespaces first
        if namespace in NAMESPACE_MAPPING:
            active_nav = NAMESPACE_MAPPING[namespace]
        elif ':' in namespace:
            # Handle nested namespaces - take the first part
            active_nav = namespace.split(':')[0]
        else:
            active_nav = namespace

    # Superusers get superadmin navigation + all staff navigation
    if user.is_superuser:
        return {
            'superadmin_nav': list(SUPERADMIN_NAV),
            'staff_nav': list(STAFF_NAV),
            'portal_nav': [],
            'active_nav': active_nav,
            'is_superadmin': True,
        }

    # Staff users get staff navigation only
    if user.is_staff:
        return {
            'superadmin_nav': [],
            'staff_nav': list(STAFF_NAV),
            'portal_nav': [],
            'active_nav': active_nav,
            'is_superadmin': False,
        }

    # Regular authenticated users get portal navigation
    return {
        'superadmin_nav': [],
        'staff_nav': [],
        'portal_nav': list(PORTAL_NAV),
        'active_nav': active_nav,
        'is_superadmin': False,
    }
