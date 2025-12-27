"""HR app configuration."""
from django.apps import AppConfig


class HrConfig(AppConfig):
    """Configuration for HR app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.hr'
    verbose_name = 'Human Resources'
