"""Referrals app configuration."""
from django.apps import AppConfig


class ReferralsConfig(AppConfig):
    """Configuration for the referrals app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.referrals'
    verbose_name = 'Referral Network'
