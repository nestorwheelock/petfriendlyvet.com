"""WAF app configuration."""
from django.apps import AppConfig


class WafConfig(AppConfig):
    """Configuration for WAF app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.waf'
    verbose_name = 'Web Application Firewall'

    def ready(self):
        """Initialize WAF when Django starts."""
        pass
