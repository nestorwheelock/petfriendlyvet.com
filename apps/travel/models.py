"""Models for travel certificates and health documentation."""
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.storage import travel_document_path


CERTIFICATE_STATUS = [
    ('pending', _('Pending')),
    ('in_review', _('In Review')),
    ('issued', _('Issued')),
    ('expired', _('Expired')),
    ('cancelled', _('Cancelled')),
]

TRAVEL_PLAN_STATUS = [
    ('planning', _('Planning')),
    ('documents_pending', _('Documents Pending')),
    ('ready', _('Ready to Travel')),
    ('completed', _('Completed')),
    ('cancelled', _('Cancelled')),
]


class TravelDestination(models.Model):
    """Country/destination with travel requirements."""

    country_code = models.CharField(_('country code'), max_length=3, unique=True)
    country_name = models.CharField(_('country name'), max_length=100)

    requirements = models.JSONField(
        _('requirements'),
        default=dict,
        help_text=_('JSON object with requirement details')
    )

    certificate_validity_days = models.IntegerField(
        _('certificate validity (days)'),
        default=10,
        help_text=_('How many days the health certificate is valid')
    )

    quarantine_required = models.BooleanField(_('quarantine required'), default=False)
    quarantine_days = models.IntegerField(_('quarantine days'), null=True, blank=True)

    airline_requirements = models.TextField(_('airline requirements'), blank=True)
    notes = models.TextField(_('notes'), blank=True)

    is_active = models.BooleanField(_('active'), default=True)
    last_updated = models.DateTimeField(_('last updated'), auto_now=True)

    class Meta:
        verbose_name = _('travel destination')
        verbose_name_plural = _('travel destinations')
        ordering = ['country_name']

    def __str__(self):
        return f"{self.country_name} ({self.country_code})"


class HealthCertificate(models.Model):
    """Health certificate for international pet travel."""

    pet = models.ForeignKey(
        'pets.Pet',
        on_delete=models.CASCADE,
        related_name='health_certificates',
        verbose_name=_('pet')
    )
    destination = models.ForeignKey(
        TravelDestination,
        on_delete=models.PROTECT,
        related_name='certificates',
        verbose_name=_('destination')
    )

    travel_date = models.DateField(_('travel date'))
    issue_date = models.DateField(_('issue date'), null=True, blank=True)
    expiry_date = models.DateField(_('expiry date'), null=True, blank=True)

    status = models.CharField(
        _('status'),
        max_length=20,
        choices=CERTIFICATE_STATUS,
        default='pending'
    )

    certificate_number = models.CharField(
        _('certificate number'),
        max_length=50,
        blank=True
    )

    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='certificates_issued',
        verbose_name=_('issued by')
    )

    pdf_document = models.FileField(
        _('PDF document'),
        upload_to=travel_document_path,
        null=True,
        blank=True
    )

    notes = models.TextField(_('notes'), blank=True)

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('health certificate')
        verbose_name_plural = _('health certificates')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.pet.name} - {self.destination.country_name}"

    def calculate_expiry(self):
        """Calculate expiry date based on issue date and destination validity."""
        if self.issue_date:
            self.expiry_date = self.issue_date + timedelta(
                days=self.destination.certificate_validity_days
            )
            self.save(update_fields=['expiry_date'])


class CertificateRequirement(models.Model):
    """Individual requirement for a health certificate."""

    certificate = models.ForeignKey(
        HealthCertificate,
        on_delete=models.CASCADE,
        related_name='requirements',
        verbose_name=_('certificate')
    )

    requirement_type = models.CharField(_('requirement type'), max_length=50)
    description = models.TextField(_('description'))

    is_verified = models.BooleanField(_('verified'), default=False)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requirements_verified',
        verbose_name=_('verified by')
    )
    verified_at = models.DateField(_('verified at'), null=True, blank=True)

    notes = models.TextField(_('notes'), blank=True)

    class Meta:
        verbose_name = _('certificate requirement')
        verbose_name_plural = _('certificate requirements')
        ordering = ['requirement_type']

    def __str__(self):
        status = '✓' if self.is_verified else '○'
        return f"{status} {self.requirement_type}"


class TravelPlan(models.Model):
    """Travel plan for a pet."""

    pet = models.ForeignKey(
        'pets.Pet',
        on_delete=models.CASCADE,
        related_name='travel_plans',
        verbose_name=_('pet')
    )
    destination = models.ForeignKey(
        TravelDestination,
        on_delete=models.PROTECT,
        related_name='travel_plans',
        verbose_name=_('destination')
    )

    departure_date = models.DateField(_('departure date'))
    return_date = models.DateField(_('return date'), null=True, blank=True)

    airline = models.CharField(_('airline'), max_length=100, blank=True)
    flight_number = models.CharField(_('flight number'), max_length=20, blank=True)

    status = models.CharField(
        _('status'),
        max_length=20,
        choices=TRAVEL_PLAN_STATUS,
        default='planning'
    )

    certificate = models.ForeignKey(
        HealthCertificate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='travel_plans',
        verbose_name=_('health certificate')
    )

    notes = models.TextField(_('notes'), blank=True)

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('travel plan')
        verbose_name_plural = _('travel plans')
        ordering = ['-departure_date']

    def __str__(self):
        return f"{self.pet.name} - {self.destination.country_name} ({self.departure_date})"
