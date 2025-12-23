"""Middleware for capturing and logging HTTP errors."""
import hashlib
import logging
import re

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.db.models import F

from .models import ErrorLog, KnownBug

logger = logging.getLogger(__name__)


ERROR_TYPE_MAP = {
    400: 'bad_request',
    401: 'unauthorized',
    403: 'forbidden',
    404: 'not_found',
    405: 'method_not_allowed',
    408: 'timeout',
    429: 'rate_limited',
    500: 'server_error',
    502: 'bad_gateway',
    503: 'service_unavailable',
    504: 'gateway_timeout',
}


class ErrorCaptureMiddleware:
    """Middleware that captures all 4xx/5xx errors and logs them to the database."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Capture 4xx and 5xx errors
        if response.status_code >= 400:
            self.capture_error(request, response)

        return response

    def get_config(self):
        """Get error tracking configuration from settings."""
        return getattr(settings, 'ERROR_TRACKING', {
            'ENABLED': True,
            'EXCLUDE_PATHS': ['/health/', '/static/', '/media/'],
            'EXCLUDE_STATUS_CODES': [],
        })

    def is_enabled(self):
        """Check if error tracking is enabled."""
        return self.get_config().get('ENABLED', True)

    def should_exclude_path(self, path):
        """Check if path should be excluded from tracking."""
        exclude_paths = self.get_config().get('EXCLUDE_PATHS', [])
        for exclude_path in exclude_paths:
            if path.startswith(exclude_path):
                return True
        return False

    def should_exclude_status(self, status_code):
        """Check if status code should be excluded from tracking."""
        exclude_codes = self.get_config().get('EXCLUDE_STATUS_CODES', [])
        return status_code in exclude_codes

    def normalize_url(self, path):
        """Normalize URL by replacing dynamic segments with placeholders.

        Examples:
            /api/pets/123/ -> /api/pets/{id}/
            /users/abc-def-123-456/ -> /users/{uuid}/
        """
        # Replace numeric IDs
        normalized = re.sub(r'/\d+/', '/{id}/', path)
        # Replace UUIDs
        normalized = re.sub(r'/[a-f0-9-]{36}/', '/{uuid}/', normalized)
        return normalized

    def generate_fingerprint(self, error_type, status_code, url_pattern):
        """Generate a unique fingerprint for this error type.

        The fingerprint groups similar errors together.
        """
        data = f"{error_type}:{status_code}:{url_pattern}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def get_error_type(self, status_code):
        """Map status code to error type string."""
        return ERROR_TYPE_MAP.get(status_code, f'error_{status_code}')

    def get_client_ip(self, request):
        """Extract client IP from request, handling proxy headers."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    def get_full_url(self, request):
        """Build full URL from request."""
        scheme = 'https' if request.is_secure() else 'http'
        host = request.get_host()
        path = request.get_full_path()
        return f"{scheme}://{host}{path}"

    def capture_error(self, request, response):
        """Capture and log the error to the database."""
        if not self.is_enabled():
            return

        path = request.path
        status_code = response.status_code

        # Check exclusions
        if self.should_exclude_path(path):
            return
        if self.should_exclude_status(status_code):
            return

        try:
            error_type = self.get_error_type(status_code)
            url_pattern = self.normalize_url(path)
            fingerprint = self.generate_fingerprint(error_type, status_code, url_pattern)

            # Get user if authenticated
            user = None
            if hasattr(request, 'user') and request.user is not None:
                if not isinstance(request.user, AnonymousUser) and request.user.is_authenticated:
                    user = request.user

            # Create error log entry
            ErrorLog.objects.create(
                fingerprint=fingerprint,
                error_type=error_type,
                status_code=status_code,
                url_pattern=url_pattern,
                full_url=self.get_full_url(request),
                method=request.method,
                user=user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                request_data={
                    'method': request.method,
                    'content_type': request.content_type if hasattr(request, 'content_type') else '',
                },
            )

            logger.debug(
                "Captured error: [%s] %s %s (fingerprint: %s)",
                status_code, request.method, path, fingerprint
            )

            # Check if this fingerprint is already known
            config = self.get_config()
            auto_create_bugs = config.get('AUTO_CREATE_BUGS', True)
            bug_threshold = config.get('BUG_THRESHOLD', 1)

            if auto_create_bugs:
                known_bug = KnownBug.objects.filter(fingerprint=fingerprint).first()

                if known_bug:
                    # Increment occurrence count for existing bug
                    KnownBug.objects.filter(pk=known_bug.pk).update(
                        occurrence_count=F('occurrence_count') + 1
                    )
                    logger.debug(
                        "Incremented occurrence count for %s",
                        known_bug.bug_id
                    )
                else:
                    # Check if we've hit the threshold for creating a bug
                    error_count = ErrorLog.objects.filter(
                        fingerprint=fingerprint
                    ).count()

                    if error_count >= bug_threshold:
                        # Trigger async bug creation
                        self.trigger_bug_creation(
                            fingerprint, error_type, status_code, url_pattern
                        )

        except Exception as e:
            # Don't let error tracking break the response
            logger.exception("Failed to capture error: %s", e)

    def trigger_bug_creation(self, fingerprint, error_type, status_code, url_pattern):
        """Trigger async bug creation via Celery task."""
        from .tasks import create_bug_task

        # Generate title from error type and URL pattern
        title = f"{error_type.replace('_', ' ').title()} on {url_pattern}"

        # Determine severity based on status code
        if status_code >= 500:
            severity = 'high'
        elif status_code == 403:
            severity = 'medium'
        elif status_code == 404:
            severity = 'low'
        else:
            severity = 'medium'

        error_data = {
            'fingerprint': fingerprint,
            'title': title,
            'description': f"HTTP {status_code} error detected on URL pattern: {url_pattern}",
            'severity': severity,
            'error_type': error_type,
            'status_code': status_code,
            'url_pattern': url_pattern,
        }

        create_bug_task.delay(error_data)
        logger.info("Triggered bug creation for fingerprint: %s", fingerprint)
