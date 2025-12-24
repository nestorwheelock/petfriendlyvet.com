"""Tests for the delivery app."""
from decimal import Decimal
from datetime import date, time, timedelta

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.apps import apps
from django.utils import timezone

User = get_user_model()


class DeliveryAppConfigTests(TestCase):
    """Tests for delivery app configuration."""

    def test_app_is_installed(self):
        """Delivery app should be in installed apps."""
        self.assertTrue(apps.is_installed('apps.delivery'))

    def test_app_name_correct(self):
        """App config should have correct name."""
        app_config = apps.get_app_config('delivery')
        self.assertEqual(app_config.name, 'apps.delivery')
        self.assertEqual(app_config.verbose_name, 'Delivery Management')
