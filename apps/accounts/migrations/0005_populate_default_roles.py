"""Data migration to create default roles and migrate existing users."""
from django.db import migrations


DEFAULT_ROLES = [
    {
        'name': 'Pet Owner',
        'slug': 'pet-owner',
        'hierarchy_level': 10,
        'description': 'Pet owners and customers',
    },
    {
        'name': 'Receptionist',
        'slug': 'receptionist',
        'hierarchy_level': 20,
        'description': 'Front desk and customer service staff',
    },
    {
        'name': 'Veterinary Technician',
        'slug': 'vet-tech',
        'hierarchy_level': 30,
        'description': 'Veterinary technicians and assistants',
    },
    {
        'name': 'Veterinarian',
        'slug': 'veterinarian',
        'hierarchy_level': 40,
        'description': 'Licensed veterinarians',
    },
    {
        'name': 'Practice Manager',
        'slug': 'practice-manager',
        'hierarchy_level': 60,
        'description': 'Manages staff schedules and practice operations',
    },
    {
        'name': 'Finance Manager',
        'slug': 'finance-manager',
        'hierarchy_level': 60,
        'description': 'Manages accounting and financial operations',
    },
    {
        'name': 'Administrator',
        'slug': 'administrator',
        'hierarchy_level': 80,
        'description': 'Full system administrator access',
    },
]

# Maps old User.role to new Role slug
USER_ROLE_MAP = {
    'owner': 'pet-owner',
    'staff': 'receptionist',
    'vet': 'veterinarian',
    'admin': 'administrator',
}


def create_default_roles(apps, schema_editor):
    """Create default roles with linked Django Groups."""
    Group = apps.get_model('auth', 'Group')
    Role = apps.get_model('accounts', 'Role')

    for role_data in DEFAULT_ROLES:
        # Create Django Group for this role
        group, _ = Group.objects.get_or_create(name=role_data['name'])

        # Create Role linked to Group
        Role.objects.get_or_create(
            slug=role_data['slug'],
            defaults={
                'name': role_data['name'],
                'hierarchy_level': role_data['hierarchy_level'],
                'description': role_data['description'],
                'group': group,
                'is_active': True,
            }
        )


def migrate_existing_users(apps, schema_editor):
    """Assign roles to existing users based on their old role field."""
    User = apps.get_model('accounts', 'User')
    Role = apps.get_model('accounts', 'Role')
    UserRole = apps.get_model('accounts', 'UserRole')

    for user in User.objects.all():
        # Skip if user already has roles assigned
        if UserRole.objects.filter(user=user).exists():
            continue

        # Get new role slug based on old role
        old_role = getattr(user, 'role', 'owner')
        new_role_slug = USER_ROLE_MAP.get(old_role, 'pet-owner')

        try:
            role = Role.objects.get(slug=new_role_slug)
            UserRole.objects.create(
                user=user,
                role=role,
                is_primary=True,
            )
        except Role.DoesNotExist:
            # Fallback to pet-owner if role not found
            role = Role.objects.get(slug='pet-owner')
            UserRole.objects.create(
                user=user,
                role=role,
                is_primary=True,
            )


def reverse_roles(apps, schema_editor):
    """Remove all roles and user roles (for rollback)."""
    UserRole = apps.get_model('accounts', 'UserRole')
    Role = apps.get_model('accounts', 'Role')
    Group = apps.get_model('auth', 'Group')

    # Delete UserRoles first
    UserRole.objects.all().delete()

    # Delete Roles and their Groups
    for role in Role.objects.all():
        group = role.group
        role.delete()
        if group:
            group.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_rbac_models'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_default_roles, reverse_roles),
        migrations.RunPython(migrate_existing_users, migrations.RunPython.noop),
    ]
