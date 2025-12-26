"""Base models for all apps."""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """Abstract base model with created/updated timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """Abstract base model with UUID primary key."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class SoftDeleteManager(models.Manager):
    """Manager that excludes soft-deleted objects by default."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

    def with_deleted(self):
        """Include soft-deleted objects."""
        return super().get_queryset()

    def deleted_only(self):
        """Only soft-deleted objects."""
        return super().get_queryset().filter(deleted_at__isnull=False)


class SoftDeleteModel(models.Model):
    """Abstract base model with soft delete functionality."""

    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """Soft delete the object."""
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    def hard_delete(self, using=None, keep_parents=False):
        """Permanently delete the object."""
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        """Restore a soft-deleted object."""
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])

    @property
    def is_deleted(self):
        """Check if object is soft-deleted."""
        return self.deleted_at is not None


class BaseModel(TimeStampedModel, SoftDeleteModel):
    """Standard base model combining timestamps and soft delete."""

    class Meta:
        abstract = True


class ContactSubmission(TimeStampedModel):
    """Model to store and track contact form submissions."""

    SUBJECT_CHOICES = [
        ('question', 'General Question'),
        ('appointment', 'Appointment Request'),
        ('emergency', 'Emergency'),
        ('pricing', 'Pricing Information'),
        ('feedback', 'Feedback'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('new', 'New'),
        ('read', 'Read'),
        ('responded', 'Responded'),
        ('archived', 'Archived'),
    ]

    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=50, choices=SUBJECT_CHOICES, default='question')
    message = models.TextField()

    # Tracking fields
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')

    # Response tracking
    responded_at = models.DateTimeField(null=True, blank=True)
    response_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Submission'
        verbose_name_plural = 'Contact Submissions'

    def __str__(self):
        return f"{self.name} - {self.subject} ({self.created_at.strftime('%Y-%m-%d')})"


class ModuleConfigManager(models.Manager):
    """Manager for ModuleConfig with convenience methods."""

    def enabled(self):
        """Return only enabled modules."""
        return self.filter(is_enabled=True)

    def disabled(self):
        """Return only disabled modules."""
        return self.filter(is_enabled=False)

    def by_section(self, section):
        """Return modules in a specific section."""
        return self.filter(section=section)


class ModuleConfig(TimeStampedModel):
    """Configuration for application modules (apps).

    Controls whether entire Django apps are enabled/disabled.
    Disabled modules return 404 for all their URLs.
    """

    SECTION_CHOICES = [
        ('operations', 'Operations'),
        ('customers', 'Customers'),
        ('finance', 'Finance'),
        ('admin', 'Admin'),
        ('system', 'System'),
    ]

    app_name = models.CharField(
        max_length=100,
        unique=True,
        help_text='Django app name (e.g., "appointments")',
    )
    display_name = models.CharField(
        max_length=100,
        help_text='Human-readable name for the module',
    )
    section = models.CharField(
        max_length=50,
        choices=SECTION_CHOICES,
        default='operations',
        help_text='Navigation section this module belongs to',
    )
    is_enabled = models.BooleanField(
        default=True,
        help_text='Whether this module is active',
    )
    disabled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the module was disabled',
    )
    disabled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='disabled_modules',
        help_text='User who disabled this module',
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text='Icon name for navigation (e.g., "calendar")',
    )
    url_name = models.CharField(
        max_length=100,
        blank=True,
        help_text='URL pattern name (e.g., "appointments:list")',
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text='Order in navigation menu',
    )

    objects = ModuleConfigManager()

    class Meta:
        ordering = ['section', 'sort_order', 'display_name']
        verbose_name = 'Module Configuration'
        verbose_name_plural = 'Module Configurations'

    def __str__(self):
        return f'{self.display_name} ({self.app_name})'

    def disable(self, user=None):
        """Disable this module."""
        self.is_enabled = False
        self.disabled_at = timezone.now()
        self.disabled_by = user
        self.save(update_fields=['is_enabled', 'disabled_at', 'disabled_by', 'updated_at'])

    def enable(self):
        """Enable this module."""
        self.is_enabled = True
        self.disabled_at = None
        self.disabled_by = None
        self.save(update_fields=['is_enabled', 'disabled_at', 'disabled_by', 'updated_at'])


class FeatureFlag(TimeStampedModel):
    """Feature flags for granular control within modules.

    Feature flags allow enabling/disabling specific features
    without affecting entire modules.
    """

    key = models.CharField(
        max_length=100,
        unique=True,
        help_text='Unique identifier (e.g., "appointments.online_booking")',
    )
    description = models.TextField(
        blank=True,
        help_text='What this feature flag controls',
    )
    is_enabled = models.BooleanField(
        default=True,
        help_text='Whether this feature is active',
    )
    module = models.ForeignKey(
        ModuleConfig,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='feature_flags',
        help_text='Parent module (null for global flags)',
    )

    class Meta:
        ordering = ['key']
        verbose_name = 'Feature Flag'
        verbose_name_plural = 'Feature Flags'

    def __str__(self):
        return self.key


class Tag(models.Model):
    """Flexible tagging for products, procedures, and other entities.

    Tags can be used across multiple models for filtering and organization.
    Examples: Bestseller, New Arrival, On Sale, Prescription Required
    """

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    color = models.CharField(
        max_length=7,
        default='#6B7280',
        help_text="Hex color code for display (e.g., '#10B981')"
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Icon name for display"
    )

    is_visible = models.BooleanField(
        default=True,
        help_text="Show this tag publicly"
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'

    def __str__(self):
        return self.name
