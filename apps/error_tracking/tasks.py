"""Celery tasks for async error tracking operations."""
import logging

from celery import shared_task

from .services import BugCreationService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def create_bug_task(self, error_data: dict) -> str:
    """Async task to create bug file and GitHub issue.

    Args:
        error_data: Dict containing:
            - fingerprint: Unique error fingerprint
            - title: Bug title
            - description: Bug description
            - severity: Bug severity (critical, high, medium, low)
            - error_type: Type of error (csrf, not_found, etc.)
            - status_code: HTTP status code
            - url_pattern: Normalized URL pattern

    Returns:
        Bug ID (e.g., 'B-001')

    Raises:
        Exception: If bug creation fails after retries
    """
    logger.info(
        "Creating bug for fingerprint: %s",
        error_data.get('fingerprint', 'unknown')
    )

    service = BugCreationService()
    bug = service.create_full_bug(error_data)

    logger.info("Created bug %s for fingerprint %s",
                bug.bug_id, error_data.get('fingerprint'))

    return bug.bug_id
