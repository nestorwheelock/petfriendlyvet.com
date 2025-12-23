"""Services app configuration."""
from django.apps import AppConfig


class ServicesConfig(AppConfig):
    """Configuration for the services app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.services'
    verbose_name = 'External Services'
