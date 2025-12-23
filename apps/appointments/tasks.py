"""Celery tasks for appointment management."""
import logging

from celery import shared_task

from .reminders import ReminderService

logger = logging.getLogger(__name__)


@shared_task
def send_appointment_reminders(hours_before: int = 24) -> dict:
    """Send reminder emails for upcoming appointments.

    This task should be scheduled to run periodically (e.g., every hour)
    to send reminders for appointments happening within the next 24 hours.

    Args:
        hours_before: Send reminders for appointments within this many hours

    Returns:
        Dict with counts of sent reminders and errors
    """
    appointments = ReminderService.get_appointments_needing_reminder(
        hours_before=hours_before
    )

    sent_count = 0
    error_count = 0

    for appointment in appointments:
        try:
            if ReminderService.send_reminder_email(appointment):
                sent_count += 1
            else:
                error_count += 1
        except Exception as e:
            logger.exception(
                "Error sending reminder for appointment %s: %s",
                appointment.id,
                str(e)
            )
            error_count += 1

    logger.info(
        "Appointment reminders: sent %d, errors %d",
        sent_count,
        error_count
    )

    return {
        'sent': sent_count,
        'errors': error_count,
        'total_checked': len(appointments)
    }
