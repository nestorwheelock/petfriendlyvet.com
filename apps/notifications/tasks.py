"""Celery tasks for notifications."""
import logging

from celery import shared_task

from .services import VaccinationReminderService

logger = logging.getLogger(__name__)


@shared_task
def send_vaccination_reminders(days_ahead: int = 30) -> dict:
    """
    Send vaccination reminder emails for vaccinations due soon.

    Args:
        days_ahead: Number of days to look ahead for due vaccinations

    Returns:
        Dict with counts of sent reminders, errors, and total checked
    """
    vaccinations = VaccinationReminderService.get_vaccinations_due_soon(days_ahead)

    sent = 0
    errors = 0
    total = vaccinations.count()

    for vaccination in vaccinations:
        try:
            success = VaccinationReminderService.send_reminder_email(vaccination)
            if success:
                sent += 1
            else:
                errors += 1
        except Exception as e:
            logger.exception(f"Error sending vaccination reminder: {e}")
            errors += 1

    logger.info(
        f"Vaccination reminders: {sent} sent, {errors} errors, {total} total"
    )

    return {
        'sent': sent,
        'errors': errors,
        'total_checked': total
    }


@shared_task
def send_overdue_vaccination_alerts() -> dict:
    """
    Send alerts for overdue vaccinations.

    Returns:
        Dict with counts of sent alerts, errors, and total checked
    """
    vaccinations = VaccinationReminderService.get_overdue_vaccinations()

    sent = 0
    errors = 0
    total = vaccinations.count()

    for vaccination in vaccinations:
        try:
            success = VaccinationReminderService.send_reminder_email(vaccination)
            if success:
                sent += 1
            else:
                errors += 1
        except Exception as e:
            logger.exception(f"Error sending overdue vaccination alert: {e}")
            errors += 1

    logger.info(
        f"Overdue vaccination alerts: {sent} sent, {errors} errors, {total} total"
    )

    return {
        'sent': sent,
        'errors': errors,
        'total_checked': total
    }
