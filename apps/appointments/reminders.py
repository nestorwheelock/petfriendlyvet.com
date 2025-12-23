"""Appointment reminder service."""
import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from .models import Appointment

logger = logging.getLogger(__name__)


class ReminderService:
    """Service for managing appointment reminders."""

    DEFAULT_HOURS_BEFORE = 24

    @classmethod
    def get_appointments_needing_reminder(
        cls,
        hours_before: int = None
    ) -> list[Appointment]:
        """Get appointments that need reminder emails.

        Args:
            hours_before: Send reminders for appointments within this many hours

        Returns:
            List of Appointment objects needing reminders
        """
        if hours_before is None:
            hours_before = cls.DEFAULT_HOURS_BEFORE

        now = timezone.now()
        reminder_window_end = now + timedelta(hours=hours_before)

        appointments = Appointment.objects.filter(
            scheduled_start__gte=now,
            scheduled_start__lte=reminder_window_end,
            reminder_sent=False,
            status__in=['scheduled', 'confirmed']
        ).select_related('owner', 'pet', 'service', 'veterinarian')

        return list(appointments)

    @classmethod
    def send_reminder_email(cls, appointment: Appointment) -> bool:
        """Send reminder email for an appointment.

        Args:
            appointment: The appointment to send reminder for

        Returns:
            True if email was sent successfully
        """
        if not appointment.owner.email:
            logger.warning(
                "Cannot send reminder for appointment %s: owner has no email",
                appointment.id
            )
            return False

        try:
            subject = cls._get_reminder_subject(appointment)
            message = cls._get_reminder_message(appointment)

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[appointment.owner.email],
                fail_silently=False
            )

            # Mark as sent
            appointment.reminder_sent = True
            appointment.reminder_sent_at = timezone.now()
            appointment.save(update_fields=['reminder_sent', 'reminder_sent_at'])

            logger.info(
                "Sent reminder email for appointment %s to %s",
                appointment.id,
                appointment.owner.email
            )
            return True

        except Exception as e:
            logger.exception(
                "Failed to send reminder for appointment %s: %s",
                appointment.id,
                str(e)
            )
            return False

    @classmethod
    def _get_reminder_subject(cls, appointment: Appointment) -> str:
        """Generate reminder email subject."""
        pet_name = appointment.pet.name if appointment.pet else ''
        if pet_name:
            return f"Appointment Reminder: {pet_name}'s {appointment.service.name}"
        return f"Appointment Reminder: {appointment.service.name}"

    @classmethod
    def _get_reminder_message(cls, appointment: Appointment) -> str:
        """Generate reminder email body."""
        pet_name = appointment.pet.name if appointment.pet else 'your appointment'
        vet_name = ''
        if appointment.veterinarian:
            vet_name = (
                appointment.veterinarian.get_full_name() or
                appointment.veterinarian.username
            )

        scheduled_date = appointment.scheduled_start.strftime('%A, %B %d, %Y')
        scheduled_time = appointment.scheduled_start.strftime('%I:%M %p')

        message_parts = [
            f"Hello {appointment.owner.get_full_name() or appointment.owner.username},",
            "",
            f"This is a reminder about your upcoming appointment at Pet-Friendly Veterinary Clinic.",
            "",
            "Appointment Details:",
            f"- Service: {appointment.service.name}",
        ]

        if appointment.pet:
            message_parts.append(f"- Pet: {pet_name}")

        message_parts.extend([
            f"- Date: {scheduled_date}",
            f"- Time: {scheduled_time}",
        ])

        if vet_name:
            message_parts.append(f"- Veterinarian: {vet_name}")

        message_parts.extend([
            "",
            "Please arrive 10 minutes before your scheduled time.",
            "",
            "If you need to reschedule or cancel, please contact us at +52 998 316 2438.",
            "",
            "We look forward to seeing you!",
            "",
            "Pet-Friendly Veterinary Clinic",
            "Puerto Morelos, Quintana Roo, Mexico",
        ])

        return "\n".join(message_parts)
