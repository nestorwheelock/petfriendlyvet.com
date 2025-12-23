"""Notification services."""
import logging
from datetime import date, timedelta
from typing import Optional

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from .models import Notification, NotificationPreference

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing user notifications."""

    # Mapping of notification types to preference fields
    TYPE_TO_PREFERENCE = {
        'appointment_reminder': 'email_appointments',
        'appointment_confirmed': 'email_appointments',
        'appointment_cancelled': 'email_appointments',
        'vaccination_reminder': 'email_vaccinations',
        'vaccination_overdue': 'email_vaccinations',
        'promotion': 'email_promotions',
        'system': 'email_system',
        'general': 'email_system',
    }

    @classmethod
    def create_notification(
        cls,
        user,
        notification_type: str,
        title: str,
        message: str,
        send_email: bool = False,
        related_pet_id: Optional[int] = None,
        related_appointment_id: Optional[int] = None
    ) -> Notification:
        """Create a notification for a user."""
        notification = Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            related_pet_id=related_pet_id,
            related_appointment_id=related_appointment_id
        )

        if send_email and user.email:
            if cls._should_send_email(user, notification_type):
                cls._send_notification_email(notification)

        return notification

    @classmethod
    def _should_send_email(cls, user, notification_type: str) -> bool:
        """Check if email should be sent based on user preferences."""
        try:
            prefs = user.notification_preferences
        except NotificationPreference.DoesNotExist:
            # Default to sending email if no preferences set
            return True

        pref_field = cls.TYPE_TO_PREFERENCE.get(notification_type, 'email_system')
        return getattr(prefs, pref_field, True)

    @classmethod
    def _send_notification_email(cls, notification: Notification) -> bool:
        """Send email for a notification."""
        try:
            subject = notification.title
            message = notification.message

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notification.user.email],
                fail_silently=False
            )

            notification.email_sent = True
            notification.email_sent_at = timezone.now()
            notification.save(update_fields=['email_sent', 'email_sent_at'])

            return True
        except Exception as e:
            logger.exception(f"Failed to send notification email: {e}")
            return False

    @classmethod
    def get_user_notifications(cls, user, unread_only: bool = False, limit: int = 50):
        """Get notifications for a user."""
        qs = Notification.objects.filter(user=user)
        if unread_only:
            qs = qs.filter(is_read=False)
        return qs[:limit]

    @classmethod
    def get_unread_count(cls, user) -> int:
        """Get count of unread notifications."""
        return Notification.objects.filter(user=user, is_read=False).count()

    @classmethod
    def mark_all_as_read(cls, user) -> int:
        """Mark all user notifications as read."""
        return Notification.objects.filter(
            user=user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )


class VaccinationReminderService:
    """Service for vaccination reminders."""

    @classmethod
    def get_vaccinations_due_soon(cls, days_ahead: int = 30):
        """Get vaccinations due within specified days."""
        from apps.pets.models import Vaccination

        due_date = date.today() + timedelta(days=days_ahead)

        return Vaccination.objects.filter(
            next_due_date__lte=due_date,
            next_due_date__gte=date.today(),
            reminder_sent=False
        ).select_related('pet', 'pet__owner')

    @classmethod
    def get_overdue_vaccinations(cls):
        """Get overdue vaccinations."""
        from apps.pets.models import Vaccination

        return Vaccination.objects.filter(
            next_due_date__lt=date.today(),
            reminder_sent=False
        ).select_related('pet', 'pet__owner')

    @classmethod
    def send_reminder_email(cls, vaccination) -> bool:
        """Send reminder email for a vaccination."""
        owner = vaccination.pet.owner

        if not owner.email:
            logger.warning(
                f"Cannot send vaccination reminder - no email for user {owner.pk}"
            )
            return False

        try:
            subject = f"Vaccination Reminder: {vaccination.vaccine_name} for {vaccination.pet.name}"

            message = (
                f"Dear {owner.get_full_name() or owner.username},\n\n"
                f"This is a reminder that {vaccination.pet.name}'s "
                f"{vaccination.vaccine_name} vaccination is due on "
                f"{vaccination.next_due_date.strftime('%B %d, %Y')}.\n\n"
                f"Please schedule an appointment at your earliest convenience.\n\n"
                f"Best regards,\n"
                f"Pet Friendly Veterinary Clinic"
            )

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[owner.email],
                fail_silently=False
            )

            # Mark as reminded
            vaccination.reminder_sent = True
            vaccination.reminder_sent_at = timezone.now()
            vaccination.save(update_fields=['reminder_sent', 'reminder_sent_at'])

            # Create in-app notification
            NotificationService.create_notification(
                user=owner,
                notification_type='vaccination_reminder',
                title=f"Vaccination Due: {vaccination.vaccine_name}",
                message=f"{vaccination.pet.name}'s {vaccination.vaccine_name} vaccination is due on {vaccination.next_due_date}.",
                related_pet_id=vaccination.pet.pk
            )

            logger.info(f"Sent vaccination reminder for {vaccination.pet.name}")
            return True

        except Exception as e:
            logger.exception(f"Failed to send vaccination reminder: {e}")
            return False
