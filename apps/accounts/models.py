"""User and authentication models."""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.storage import avatar_path
from .validators import validate_file_size, validate_image_type


class User(AbstractUser):
    """Custom user model for Pet-Friendly Vet."""

    AUTH_METHOD_CHOICES = [
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('google', 'Google'),
    ]

    ROLE_CHOICES = [
        ('owner', 'Pet Owner'),
        ('staff', 'Staff'),
        ('vet', 'Veterinarian'),
        ('admin', 'Administrator'),
    ]

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
