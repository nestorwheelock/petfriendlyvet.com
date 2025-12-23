"""Notification models."""
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Notification(models.Model):
    """User notification record."""

    NOTIFICATION_TYPES = [
        ('appointment_reminder', _('Appointment Reminder')),
        ('appointment_confirmed', _('Appointment Confirmed')),
        ('appointment_cancelled', _('Appointment Cancelled')),
        ('vaccination_reminder', _('Vaccination Reminder')),
        ('vaccination_overdue', _('Vaccination Overdue')),
        ('general', _('General')),
        ('promotion', _('Promotion')),
        ('system', _('System')),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('user')
    )
    notification_type = models.CharField(
        _('type'),
        max_length=30,
        choices=NOTIFICATION_TYPES,
        default='general'
    )
    title = models.CharField(_('title'), max_length=200)
    message = models.TextField(_('message'))

    # Related objects (optional)
    related_pet_id = models.IntegerField(_('related pet'), null=True, blank=True)
    related_appointment_id = models.IntegerField(_('related appointment'), null=True, blank=True)

    # Read status
    is_read = models.BooleanField(_('read'), default=False)
    read_at = models.DateTimeField(_('read at'), null=True, blank=True)

    # Email tracking
    email_sent = models.BooleanField(_('email sent'), default=False)
    email_sent_at = models.DateTimeField(_('email sent at'), null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.username}"

    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class NotificationPreference(models.Model):
    """User notification preferences."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        verbose_name=_('user')
    )

    # Email preferences
    email_appointments = models.BooleanField(
        _('email appointment reminders'),
        default=True
    )
    email_vaccinations = models.BooleanField(
        _('email vaccination reminders'),
        default=True
    )
    email_promotions = models.BooleanField(
        _('email promotions'),
        default=False
    )
    email_system = models.BooleanField(
        _('email system notifications'),
        default=True
    )

    # Reminder timing
    appointment_reminder_hours = models.IntegerField(
        _('appointment reminder hours before'),
        default=24
    )
    vaccination_reminder_days = models.IntegerField(
        _('vaccination reminder days before'),
        default=14
    )

    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('notification preference')
        verbose_name_plural = _('notification preferences')

    def __str__(self):
        return f"Preferences for {self.user.username}"
