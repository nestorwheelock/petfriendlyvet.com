"""User and authentication models."""
from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.storage import avatar_path
from .validators import validate_file_size, validate_image_type


class Role(models.Model):
    """Custom roles with configurable permissions and hierarchy."""

    name = models.CharField(_('name'), max_length=100, unique=True)
    slug = models.SlugField(_('slug'), unique=True)
    description = models.TextField(_('description'), blank=True)
    hierarchy_level = models.IntegerField(
        _('hierarchy level'),
        default=20,
        help_text=_('Higher number = more authority (10-100)')
    )
    is_active = models.BooleanField(_('active'), default=True)

    # Link to Django's built-in Group for permissions
    group = models.OneToOneField(
        Group,
        on_delete=models.CASCADE,
        related_name='custom_role',
        verbose_name=_('group')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('role')
        verbose_name_plural = _('roles')
        ordering = ['-hierarchy_level', 'name']

    def __str__(self):
        return self.name


class Permission(models.Model):
    """Custom permission definitions by module."""

    MODULE_CHOICES = [
        ('practice', _('Practice Management')),
        ('inventory', _('Inventory')),
        ('accounting', _('Accounting')),
        ('pharmacy', _('Pharmacy')),
        ('appointments', _('Appointments')),
        ('delivery', _('Delivery')),
        ('crm', _('CRM')),
        ('reports', _('Reports')),
        ('billing', _('Billing')),
        ('superadmin', _('System Admin')),
    ]

    ACTION_CHOICES = [
        ('view', _('View')),
        ('create', _('Create')),
        ('edit', _('Edit')),
        ('delete', _('Delete')),
        ('approve', _('Approve')),
        ('manage', _('Full Control')),
    ]

    module = models.CharField(_('module'), max_length=50, choices=MODULE_CHOICES)
    action = models.CharField(_('action'), max_length=20, choices=ACTION_CHOICES)
    resource = models.CharField(
        _('resource'),
        max_length=100,
        help_text=_('Specific resource like "staff", "schedules", "bills"')
    )
    codename = models.CharField(_('codename'), max_length=100, unique=True)
    name = models.CharField(_('name'), max_length=255)

    class Meta:
        verbose_name = _('permission')
        verbose_name_plural = _('permissions')
        ordering = ['module', 'action', 'resource']

    def __str__(self):
        return f"{self.module}.{self.action}_{self.resource}"


class UserRole(models.Model):
    """Links users to roles (many-to-many with metadata)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_roles',
        verbose_name=_('user')
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='user_roles',
        verbose_name=_('role')
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='roles_assigned',
        verbose_name=_('assigned by')
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    is_primary = models.BooleanField(
        _('is primary'),
        default=False,
        help_text=_("User's main role for display purposes")
    )

    class Meta:
        verbose_name = _('user role')
        verbose_name_plural = _('user roles')
        unique_together = ['user', 'role']

    def __str__(self):
        return f"{self.user} - {self.role}"


class User(AbstractUser):
    """Login account for Pet-Friendly Vet.

    This is an authentication account, separate from Person (identity).
    - One Person can have multiple User accounts (different auth methods)
    - A User can exist without a Person (API/service accounts)
    - A Person can exist without a User (contacts, leads)
    """

    AUTH_METHOD_CHOICES = [
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('google', 'Google'),
        ('apple', 'Apple'),
        ('facebook', 'Facebook'),
        ('api_key', 'API Key'),
    ]

    ROLE_CHOICES = [
        ('owner', 'Pet Owner'),
        ('staff', 'Staff'),
        ('vet', 'Veterinarian'),
        ('admin', 'Administrator'),
    ]

    # Link to Person (the real-world identity)
    # Nullable: API/service accounts may not have a Person
    person = models.ForeignKey(
        'parties.Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accounts',
        verbose_name=_('person'),
        help_text=_('The real-world person this account belongs to'),
    )

    email = models.EmailField(_('email address'), unique=True, null=True, blank=True)
    phone_number = models.CharField(
        _('phone number'),
        max_length=20,
        unique=True,
        null=True,
        blank=True
    )
    phone_verified = models.BooleanField(_('phone verified'), default=False)
    email_verified = models.BooleanField(_('email verified'), default=False)

    preferred_language = models.CharField(
        _('preferred language'),
        max_length=5,
        default='es',
        choices=[
            ('es', 'Español'),
            ('en', 'English'),
            ('de', 'Deutsch'),
            ('fr', 'Français'),
            ('it', 'Italiano'),
        ]
    )

    auth_method = models.CharField(
        _('authentication method'),
        max_length=20,
        choices=AUTH_METHOD_CHOICES,
        default='email'
    )

    role = models.CharField(
        _('role'),
        max_length=20,
        choices=ROLE_CHOICES,
        default='owner'
    )

    # Profile picture (with security validators)
    avatar = models.ImageField(
        _('avatar'),
        upload_to=avatar_path,
        validators=[validate_file_size, validate_image_type],
        null=True,
        blank=True
    )

    # Consent tracking
    marketing_consent = models.BooleanField(_('marketing consent'), default=False)
    marketing_consent_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.get_full_name() or self.email or self.phone_number or self.username

    @property
    def is_pet_owner(self):
        return self.role == 'owner'

    @property
    def is_staff_member(self):
        return self.role in ['staff', 'vet', 'admin']

    @property
    def is_veterinarian(self):
        return self.role == 'vet'

    # RBAC System Methods

    @property
    def hierarchy_level(self):
        """Get user's highest hierarchy level from all roles.

        Returns:
            int: The highest hierarchy level from all assigned roles.
                 100 for superusers, 0 for users with no roles.
        """
        if self.is_superuser:
            return 100
        levels = self.user_roles.values_list('role__hierarchy_level', flat=True)
        return max(levels) if levels else 0

    def can_manage_user(self, other_user):
        """Check if this user can manage another user (hierarchy check).

        A user can only manage users with a LOWER hierarchy level.
        Users at the same level cannot manage each other.

        Args:
            other_user: The user to check management permission for.

        Returns:
            bool: True if this user can manage the other user.
        """
        return self.hierarchy_level > other_user.hierarchy_level

    def get_manageable_roles(self):
        """Get roles this user can assign to others.

        Returns:
            QuerySet: Roles with hierarchy_level below this user's level.
        """
        return Role.objects.filter(
            hierarchy_level__lt=self.hierarchy_level,
            is_active=True
        )

    def has_module_permission(self, module, action='view'):
        """Check if user has permission for module+action.

        Superusers always have all permissions.
        Regular users must have the permission assigned via their role's group.

        Args:
            module: The module name (e.g., 'practice', 'accounting')
            action: The action name (e.g., 'view', 'manage')

        Returns:
            bool: True if user has the permission.
        """
        if self.is_superuser:
            return True

        # Build the permission codename
        codename = f"{module}.{action}"

        # Check permissions via Role's groups
        from django.contrib.auth.models import Permission as DjangoPermission
        role_group_ids = self.user_roles.values_list('role__group_id', flat=True)
        return DjangoPermission.objects.filter(
            group__id__in=role_group_ids,
            codename=codename
        ).exists()


class EmailChangeRequest(models.Model):
    """Request to change user's email address."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='email_change_requests'
    )
    new_email = models.EmailField(_('new email address'))
    token = models.CharField(_('verification token'), max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    confirmed_at = models.DateTimeField(null=True, blank=True)
    old_email = models.EmailField(_('old email address'), blank=True)

    class Meta:
        verbose_name = _('email change request')
        verbose_name_plural = _('email change requests')
        ordering = ['-created_at']

    def __str__(self):
        return f"Email change request for {self.user} to {self.new_email}"

    @property
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return not self.is_expired and self.confirmed_at is None


# =============================================================================
# Party Pattern Models - MOVED TO apps/parties/models.py
# =============================================================================
# All Party models (Person, Organization, Group, PartyRelationship) are now
# in the parties app. Import them from there:
#
# from apps.parties.models import Person, Organization, Group, PartyRelationship
#
# This keeps accounts app focused on authentication only.
