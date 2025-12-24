"""Competitive intelligence app configuration."""
from django.apps import AppConfig


class CompetitiveConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.competitive'
    verbose_name = 'Competitive Intelligence'
