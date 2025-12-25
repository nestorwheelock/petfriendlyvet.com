"""Audit app configuration."""
from django.apps import AppConfig


class AuditConfig(AppConfig):
    """Audit logging app config."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.audit'
    verbose_name = 'Audit Logging'

    def ready(self):
        """Import signals when app is ready."""
        import apps.audit.signals  # noqa: F401
