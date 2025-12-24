"""Models for veterinary services and external partner directory."""
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


SERVICE_CATEGORIES = [
    ('consultation', _('Consultation')),
    ('vaccination', _('Vaccination')),
    ('surgery', _('Surgery')),
    ('dental', _('Dental')),
    ('laboratory', _('Laboratory')),
    ('imaging', _('Imaging')),
    ('grooming', _('Grooming')),
    ('emergency', _('Emergency')),
    ('preventive', _('Preventive Care')),
    ('other', _('Other')),
]


class Service(models.Model):
    """Veterinary service offered by the clinic."""

    name = models.CharField(_('name'), max_length=200)
    name_es = models.CharField(_('name (Spanish)'), max_length=200, blank=True)
    description = models.TextField(_('description'), blank=True)
    category = models.CharField(
        _('category'),
        max_length=20,
        choices=SERVICE_CATEGORIES,
        default='consultation'
    )

    # Pricing
    base_price = models.DecimalField(
        _('base price'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0')
    )
    duration_minutes = models.PositiveIntegerField(
        _('duration (minutes)'),
        default=30
    )

    # SAT codes for CFDI
    clave_producto_sat = models.CharField(
        _('SAT product code'),
        max_length=10,
        blank=True
    )
    clave_unidad_sat = models.CharField(
        _('SAT unit code'),
        max_length=5,
        default='E48'  # Unit of service
    )

    # Status
    is_active = models.BooleanField(_('active'), default=True)
    requires_appointment = models.BooleanField(
        _('requires appointment'),
        default=True
    )

    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('service')
        verbose_name_plural = _('services')
        ordering = ['category', 'name']

    def __str__(self):
        return self.name


PARTNER_TYPES = [
    ('grooming', _('Grooming')),
    ('boarding', _('Boarding')),
    ('training', _('Training')),
    ('daycare', _('Daycare')),
    ('pet_sitting', _('Pet Sitting')),
    ('transport', _('Pet Transport')),
    ('other', _('Other')),
]

REFERRAL_STATUS = [
    ('pending', _('Pending')),
    ('contacted', _('Contacted')),
    ('scheduled', _('Scheduled')),
    ('completed', _('Completed')),
    ('cancelled', _('Cancelled')),
]


class ExternalPartner(models.Model):
    """External service partner (grooming, boarding, etc.)."""

    name = models.CharField(_('business name'), max_length=200)
    partner_type = models.CharField(
        _('type'),
        max_length=20,
        choices=PARTNER_TYPES
    )

    # Contact information
    contact_name = models.CharField(_('contact name'), max_length=200, blank=True)
    phone = models.CharField(_('phone'), max_length=50, blank=True)
    email = models.EmailField(_('email'), blank=True)
    website = models.URLField(_('website'), blank=True)
    address = models.TextField(_('address'), blank=True)

    # Details
    description = models.TextField(_('description'), blank=True)
    services_offered = models.TextField(_('services offered'), blank=True)
    hours_of_operation = models.TextField(_('hours of operation'), blank=True)
    price_range = models.CharField(_('price range'), max_length=100, blank=True)

    # Rating and status
    average_rating = models.DecimalField(
        _('average rating'),
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True
    )
    is_active = models.BooleanField(_('active'), default=True)
    is_preferred = models.BooleanField(_('preferred partner'), default=False)

    # Notes for staff
    internal_notes = models.TextField(_('internal notes'), blank=True)

    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('external partner')
        verbose_name_plural = _('external partners')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_partner_type_display()})"


class Referral(models.Model):
    """Track referrals to external partners."""

    pet = models.ForeignKey(
        'pets.Pet',
        on_delete=models.CASCADE,
        related_name='referrals',
        verbose_name=_('pet')
    )
    partner = models.ForeignKey(
        ExternalPartner,
        on_delete=models.CASCADE,
        related_name='referrals',
        verbose_name=_('partner')
    )
    referred_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='referrals_made',
        verbose_name=_('referred by')
    )

    service_type = models.CharField(
        _('service type'),
        max_length=20,
        choices=PARTNER_TYPES
    )
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=REFERRAL_STATUS,
        default='pending'
    )

    # Scheduling
    preferred_date = models.DateField(_('preferred date'), null=True, blank=True)
    scheduled_date = models.DateField(_('scheduled date'), null=True, blank=True)

    # Notes and feedback
    notes = models.TextField(_('notes'), blank=True)
    feedback = models.TextField(_('feedback'), blank=True)
    rating = models.IntegerField(_('rating'), null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    completed_at = models.DateTimeField(_('completed at'), null=True, blank=True)

    class Meta:
        verbose_name = _('referral')
        verbose_name_plural = _('referrals')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.pet.name} -> {self.partner.name}"
