"""User and authentication models."""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from .validators import validate_file_size, validate_image_type, avatar_upload_path


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
        upload_to=avatar_upload_path,
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
