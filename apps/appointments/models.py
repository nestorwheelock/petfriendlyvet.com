"""Appointment models for Pet-Friendly Vet."""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


SERVICE_CATEGORIES = [
    ('clinic', _('Clinic')),
    ('grooming', _('Grooming')),
    ('lab', _('Laboratory')),
    ('surgery', _('Surgery')),
    ('dental', _('Dental')),
    ('emergency', _('Emergency')),
    ('other', _('Other')),
]

WEEKDAY_CHOICES = [
    (0, _('Monday')),
    (1, _('Tuesday')),
    (2, _('Wednesday')),
    (3, _('Thursday')),
    (4, _('Friday')),
    (5, _('Saturday')),
    (6, _('Sunday')),
]

APPOINTMENT_STATUS = [
    ('scheduled', _('Scheduled')),
    ('confirmed', _('Confirmed')),
    ('in_progress', _('In Progress')),
    ('completed', _('Completed')),
    ('cancelled', _('Cancelled')),
    ('no_show', _('No Show')),
]


class ServiceType(models.Model):
    """Types of services offered by the clinic."""

    name = models.CharField(_('name'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    duration_minutes = models.PositiveIntegerField(_('duration (minutes)'))
    price = models.DecimalField(
        _('price'),
        max_digits=10,
        decimal_places=2
    )
    category = models.CharField(
        _('category'),
        max_length=20,
        choices=SERVICE_CATEGORIES,
        default='clinic'
    )
    is_active = models.BooleanField(_('active'), default=True)
    requires_pet = models.BooleanField(
        _('requires pet'),
        default=True,
        help_text=_('Whether this service requires a pet to be selected')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('service type')
        verbose_name_plural = _('service types')
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.duration_minutes} min)"


class ScheduleBlock(models.Model):
    """Staff availability blocks for scheduling."""

    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='schedule_blocks',
        verbose_name=_('staff member')
    )
    day_of_week = models.IntegerField(
        _('day of week'),
        choices=WEEKDAY_CHOICES
    )
    start_time = models.TimeField(_('start time'))
    end_time = models.TimeField(_('end time'))
    is_active = models.BooleanField(_('active'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('schedule block')
        verbose_name_plural = _('schedule blocks')
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        day_name = dict(WEEKDAY_CHOICES).get(self.day_of_week, 'Unknown')
        return f"{self.staff.username} - {day_name} {self.start_time}-{self.end_time}"


class Appointment(models.Model):
    """Appointment booking records."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name=_('owner')
    )
    pet = models.ForeignKey(
        'pets.Pet',
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name=_('pet'),
        null=True,
        blank=True
    )
    service = models.ForeignKey(
        ServiceType,
        on_delete=models.PROTECT,
        related_name='appointments',
        verbose_name=_('service')
    )
    veterinarian = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointments_as_vet',
        verbose_name=_('veterinarian')
    )
    scheduled_start = models.DateTimeField(_('scheduled start'))
    scheduled_end = models.DateTimeField(_('scheduled end'))
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=APPOINTMENT_STATUS,
        default='scheduled'
    )
    notes = models.TextField(_('notes'), blank=True)
    cancellation_reason = models.TextField(_('cancellation reason'), blank=True)
    confirmed_at = models.DateTimeField(_('confirmed at'), null=True, blank=True)
    completed_at = models.DateTimeField(_('completed at'), null=True, blank=True)
    cancelled_at = models.DateTimeField(_('cancelled at'), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('appointment')
        verbose_name_plural = _('appointments')
        ordering = ['-scheduled_start']

    def __str__(self):
        pet_name = self.pet.name if self.pet else 'No Pet'
        return f"{pet_name} - {self.service.name} ({self.scheduled_start.date()})"
