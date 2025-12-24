"""Emergency app configuration."""
from django.apps import AppConfig


class EmergencyConfig(AppConfig):
    """Emergency services app config."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.emergency'
    verbose_name = 'Emergency Services'
