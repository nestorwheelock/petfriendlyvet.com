"""Data migration to create module permissions and assign to roles."""
from django.db import migrations


# All modules that need permissions
MODULES = [
    ('practice', 'Practice Management'),
    ('accounting', 'Accounting'),
    ('inventory', 'Inventory'),
    ('pharmacy', 'Pharmacy'),
    ('appointments', 'Appointments'),
    ('delivery', 'Delivery'),
    ('crm', 'CRM'),
    ('reports', 'Reports'),
    ('billing', 'Billing'),
    ('superadmin', 'System Admin'),
    ('audit', 'Audit'),
    ('email_marketing', 'Email Marketing'),
    ('core', 'Core'),
]

# All actions
ACTIONS = [
    ('view', 'View'),
    ('create', 'Create'),
    ('edit', 'Edit'),
    ('delete', 'Delete'),
    ('approve', 'Approve'),
    ('manage', 'Full Control'),
]

# Default permissions for each role (from plan matrix)
# Format: role_slug -> list of permission codenames
ROLE_PERMISSIONS = {
    'pet-owner': [
        'appointments.view', 'appointments.create',
        'billing.view',
    ],
    'receptionist': [
        'practice.view',
        'appointments.view', 'appointments.create', 'appointments.edit',
        'appointments.delete', 'appointments.manage',
        'crm.view', 'crm.create',
        'delivery.view',
        'billing.view',
        'core.view',
    ],
    'vet-tech': [
        'practice.view',
        'inventory.view',
        'pharmacy.view',
        'appointments.view', 'appointments.create', 'appointments.edit',
        'appointments.delete', 'appointments.manage',
        'core.view',
    ],
    'veterinarian': [
        'practice.view', 'practice.edit',
        'inventory.view',
        'pharmacy.view', 'pharmacy.create', 'pharmacy.edit',
        'pharmacy.delete', 'pharmacy.approve', 'pharmacy.manage',
        'appointments.view', 'appointments.create', 'appointments.edit',
        'appointments.delete', 'appointments.approve', 'appointments.manage',
        'reports.view',
        'billing.view',
        'core.view',
    ],
    'practice-manager': [
        'practice.view', 'practice.create', 'practice.edit',
        'practice.delete', 'practice.approve', 'practice.manage',
        'inventory.view', 'inventory.create', 'inventory.edit',
        'inventory.delete', 'inventory.approve', 'inventory.manage',
        'pharmacy.view',
        'appointments.view', 'appointments.create', 'appointments.edit',
        'appointments.delete', 'appointments.approve', 'appointments.manage',
        'delivery.view', 'delivery.create', 'delivery.edit',
        'delivery.delete', 'delivery.approve', 'delivery.manage',
        'crm.view', 'crm.create', 'crm.edit',
        'crm.delete', 'crm.approve', 'crm.manage',
        'reports.view',
        'billing.view',
        'audit.view',
        'email_marketing.view', 'email_marketing.create', 'email_marketing.edit',
        'email_marketing.delete', 'email_marketing.approve', 'email_marketing.manage',
        'core.view',
    ],
    'finance-manager': [
        'accounting.view', 'accounting.create', 'accounting.edit',
        'accounting.delete', 'accounting.approve', 'accounting.manage',
        'billing.view', 'billing.create', 'billing.edit',
        'billing.delete', 'billing.approve', 'billing.manage',
        'reports.view', 'reports.create', 'reports.edit',
        'reports.delete', 'reports.approve', 'reports.manage',
        'crm.view',
        'audit.view',
        'core.view',
    ],
    'administrator': [
        # Practice - full control
        'practice.view', 'practice.create', 'practice.edit',
        'practice.delete', 'practice.approve', 'practice.manage',
        # Accounting - full control
        'accounting.view', 'accounting.create', 'accounting.edit',
        'accounting.delete', 'accounting.approve', 'accounting.manage',
        # Inventory - full control
        'inventory.view', 'inventory.create', 'inventory.edit',
        'inventory.delete', 'inventory.approve', 'inventory.manage',
        # Pharmacy - full control
        'pharmacy.view', 'pharmacy.create', 'pharmacy.edit',
        'pharmacy.delete', 'pharmacy.approve', 'pharmacy.manage',
        # Appointments - full control
        'appointments.view', 'appointments.create', 'appointments.edit',
        'appointments.delete', 'appointments.approve', 'appointments.manage',
        # Delivery - full control
        'delivery.view', 'delivery.create', 'delivery.edit',
        'delivery.delete', 'delivery.approve', 'delivery.manage',
        # CRM - full control
        'crm.view', 'crm.create', 'crm.edit',
        'crm.delete', 'crm.approve', 'crm.manage',
        # Reports - full control
        'reports.view', 'reports.create', 'reports.edit',
        'reports.delete', 'reports.approve', 'reports.manage',
        # Billing - full control
        'billing.view', 'billing.create', 'billing.edit',
        'billing.delete', 'billing.approve', 'billing.manage',
        # Superadmin - view only (manage requires superuser)
        'superadmin.view',
        # Audit - full control
        'audit.view', 'audit.create', 'audit.edit',
        'audit.delete', 'audit.approve', 'audit.manage',
        # Email marketing - full control
        'email_marketing.view', 'email_marketing.create', 'email_marketing.edit',
        'email_marketing.delete', 'email_marketing.approve', 'email_marketing.manage',
        # Core - view
        'core.view',
    ],
}


def create_module_permissions(apps, schema_editor):
    """Create Django Permission objects for all module/action combinations."""
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    User = apps.get_model('accounts', 'User')

    # Get content type for User model (all our permissions use this)
    content_type = ContentType.objects.get_for_model(User)

    # Create all module permissions
    for module_code, module_name in MODULES:
        for action_code, action_name in ACTIONS:
            codename = f'{module_code}.{action_code}'
            name = f'Can {action_name.lower()} {module_name.lower()}'

            Permission.objects.get_or_create(
                codename=codename,
                content_type=content_type,
                defaults={'name': name}
            )


def assign_permissions_to_roles(apps, schema_editor):
    """Assign default permissions to each role's group."""
    Permission = apps.get_model('auth', 'Permission')
    Role = apps.get_model('accounts', 'Role')

    for role_slug, permission_codenames in ROLE_PERMISSIONS.items():
        try:
            role = Role.objects.get(slug=role_slug)
        except Role.DoesNotExist:
            continue

        # Get all permissions for this role
        permissions = Permission.objects.filter(codename__in=permission_codenames)

        # Add permissions to role's group
        role.group.permissions.add(*permissions)


def reverse_permissions(apps, schema_editor):
    """Remove all module permissions (for rollback)."""
    Permission = apps.get_model('auth', 'Permission')
    Role = apps.get_model('accounts', 'Role')

    # Clear permissions from all role groups
    for role in Role.objects.all():
        role.group.permissions.clear()

    # Delete all module permissions (those with . in codename)
    Permission.objects.filter(codename__contains='.').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_populate_default_roles'),
        ('auth', '0012_alter_user_first_name_max_length'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.RunPython(create_module_permissions, reverse_permissions),
        migrations.RunPython(assign_permissions_to_roles, migrations.RunPython.noop),
    ]
