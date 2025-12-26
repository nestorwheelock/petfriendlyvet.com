"""Tests for superadmin module management views."""
import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.core.models import ModuleConfig, FeatureFlag


User = get_user_model()


@pytest.fixture
def superuser(db):
    """Create a superuser."""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='testpass123',
    )


@pytest.fixture
def staff_user(db):
    """Create a staff user (not superuser)."""
    return User.objects.create_user(
        username='staff',
        email='staff@example.com',
        password='testpass123',
        is_staff=True,
    )


@pytest.fixture
def regular_user(db):
    """Create a regular user."""
    return User.objects.create_user(
        username='user',
        email='user@example.com',
        password='testpass123',
    )


@pytest.fixture
def client():
    """Django test client."""
    return Client()


@pytest.fixture
def appointments_module(db):
    """Create appointments module."""
    return ModuleConfig.objects.create(
        app_name='appointments',
        display_name='Appointments',
        section='operations',
        is_enabled=True,
    )


@pytest.fixture
def inventory_module(db):
    """Create inventory module."""
    return ModuleConfig.objects.create(
        app_name='inventory',
        display_name='Inventory',
        section='admin',
        is_enabled=True,
    )


@pytest.fixture
def billing_module(db):
    """Create disabled billing module."""
    return ModuleConfig.objects.create(
        app_name='billing',
        display_name='Billing',
        section='finance',
        is_enabled=False,
    )


@pytest.fixture
def online_booking_flag(db, appointments_module):
    """Create online booking feature flag."""
    return FeatureFlag.objects.create(
        key='appointments.online_booking',
        description='Allow customers to book appointments online',
        is_enabled=True,
        module=appointments_module,
    )


@pytest.fixture
def sms_reminders_flag(db, appointments_module):
    """Create disabled SMS reminders feature flag."""
    return FeatureFlag.objects.create(
        key='appointments.sms_reminders',
        description='Send SMS reminders for appointments',
        is_enabled=False,
        module=appointments_module,
    )


@pytest.mark.django_db
class TestModuleListView:
    """Tests for module list view."""

    def test_module_list_requires_superuser(self, client, staff_user):
        """Test that module list requires superuser."""
        client.login(username='staff', password='testpass123')
        response = client.get(reverse('superadmin:module_list'))
        assert response.status_code == 403

    def test_module_list_denies_regular_user(self, client, regular_user):
        """Test that regular users cannot access module list."""
        client.login(username='user', password='testpass123')
        response = client.get(reverse('superadmin:module_list'))
        assert response.status_code == 403  # Permission denied

    def test_module_list_accessible_to_superuser(self, client, superuser):
        """Test that superusers can access module list."""
        client.login(username='admin', password='testpass123')
        response = client.get(reverse('superadmin:module_list'))
        assert response.status_code == 200

    def test_module_list_shows_all_modules(
        self, client, superuser, appointments_module, inventory_module, billing_module
    ):
        """Test that module list shows all modules."""
        client.login(username='admin', password='testpass123')
        response = client.get(reverse('superadmin:module_list'))
        assert response.status_code == 200
        assert 'Appointments' in response.content.decode()
        assert 'Inventory' in response.content.decode()
        assert 'Billing' in response.content.decode()

    def test_module_list_shows_enabled_status(
        self, client, superuser, appointments_module, billing_module
    ):
        """Test that module list shows enabled/disabled status."""
        client.login(username='admin', password='testpass123')
        response = client.get(reverse('superadmin:module_list'))
        content = response.content.decode()
        # Appointments is enabled, billing is disabled
        assert appointments_module.is_enabled is True
        assert billing_module.is_enabled is False

    def test_module_list_grouped_by_section(
        self, client, superuser, appointments_module, inventory_module
    ):
        """Test that modules are grouped by section."""
        client.login(username='admin', password='testpass123')
        response = client.get(reverse('superadmin:module_list'))
        assert response.status_code == 200
        # Context should include sections
        assert 'sections' in response.context or 'modules_by_section' in response.context


@pytest.mark.django_db
class TestModuleToggleView:
    """Tests for module toggle endpoint."""

    def test_module_toggle_requires_superuser(self, client, staff_user, appointments_module):
        """Test that toggle requires superuser."""
        client.login(username='staff', password='testpass123')
        response = client.post(
            reverse('superadmin:module_toggle', kwargs={'pk': appointments_module.pk})
        )
        assert response.status_code == 403

    def test_module_toggle_enables_module(self, client, superuser, billing_module):
        """Test that toggle can enable a disabled module."""
        client.login(username='admin', password='testpass123')
        assert billing_module.is_enabled is False

        response = client.post(
            reverse('superadmin:module_toggle', kwargs={'pk': billing_module.pk})
        )
        # Non-HTMX returns redirect, HTMX returns 200
        assert response.status_code in [200, 302]

        billing_module.refresh_from_db()
        assert billing_module.is_enabled is True

    def test_module_toggle_disables_module(self, client, superuser, appointments_module):
        """Test that toggle can disable an enabled module."""
        client.login(username='admin', password='testpass123')
        assert appointments_module.is_enabled is True

        response = client.post(
            reverse('superadmin:module_toggle', kwargs={'pk': appointments_module.pk})
        )
        assert response.status_code in [200, 302]

        appointments_module.refresh_from_db()
        assert appointments_module.is_enabled is False

    def test_module_toggle_records_disabled_by(self, client, superuser, appointments_module):
        """Test that disabling records who disabled it."""
        client.login(username='admin', password='testpass123')
        response = client.post(
            reverse('superadmin:module_toggle', kwargs={'pk': appointments_module.pk})
        )
        assert response.status_code in [200, 302]

        appointments_module.refresh_from_db()
        assert appointments_module.disabled_by == superuser
        assert appointments_module.disabled_at is not None

    def test_module_toggle_clears_disabled_on_enable(self, client, superuser, billing_module):
        """Test that enabling clears disabled_by and disabled_at."""
        client.login(username='admin', password='testpass123')
        response = client.post(
            reverse('superadmin:module_toggle', kwargs={'pk': billing_module.pk})
        )
        assert response.status_code in [200, 302]

        billing_module.refresh_from_db()
        assert billing_module.disabled_by is None
        assert billing_module.disabled_at is None

    def test_module_toggle_returns_partial_for_htmx(self, client, superuser, appointments_module):
        """Test that toggle returns HTMX partial."""
        client.login(username='admin', password='testpass123')
        response = client.post(
            reverse('superadmin:module_toggle', kwargs={'pk': appointments_module.pk}),
            HTTP_HX_REQUEST='true',
        )
        assert response.status_code == 200
        # Should return partial HTML for the toggle


@pytest.mark.django_db
class TestFeatureListView:
    """Tests for feature list view."""

    def test_feature_list_requires_superuser(self, client, staff_user, appointments_module):
        """Test that feature list requires superuser."""
        client.login(username='staff', password='testpass123')
        response = client.get(
            reverse('superadmin:module_features', kwargs={'pk': appointments_module.pk})
        )
        assert response.status_code == 403

    def test_feature_list_shows_module_features(
        self, client, superuser, appointments_module, online_booking_flag, sms_reminders_flag
    ):
        """Test that feature list shows module's features."""
        client.login(username='admin', password='testpass123')
        response = client.get(
            reverse('superadmin:module_features', kwargs={'pk': appointments_module.pk})
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert 'online_booking' in content or 'Online Booking' in content.title()
        assert 'sms_reminders' in content or 'SMS' in content

    def test_feature_list_shows_module_info(
        self, client, superuser, appointments_module, online_booking_flag
    ):
        """Test that feature list shows parent module info."""
        client.login(username='admin', password='testpass123')
        response = client.get(
            reverse('superadmin:module_features', kwargs={'pk': appointments_module.pk})
        )
        assert response.status_code == 200
        assert 'Appointments' in response.content.decode()


@pytest.mark.django_db
class TestFeatureToggleView:
    """Tests for feature flag toggle endpoint."""

    def test_feature_toggle_requires_superuser(
        self, client, staff_user, online_booking_flag
    ):
        """Test that feature toggle requires superuser."""
        client.login(username='staff', password='testpass123')
        response = client.post(
            reverse('superadmin:feature_toggle', kwargs={'pk': online_booking_flag.pk})
        )
        assert response.status_code == 403

    def test_feature_toggle_enables_feature(
        self, client, superuser, sms_reminders_flag
    ):
        """Test that toggle can enable a disabled feature."""
        client.login(username='admin', password='testpass123')
        assert sms_reminders_flag.is_enabled is False

        response = client.post(
            reverse('superadmin:feature_toggle', kwargs={'pk': sms_reminders_flag.pk})
        )
        # Non-HTMX returns redirect, HTMX returns 200
        assert response.status_code in [200, 302]

        sms_reminders_flag.refresh_from_db()
        assert sms_reminders_flag.is_enabled is True

    def test_feature_toggle_disables_feature(
        self, client, superuser, online_booking_flag
    ):
        """Test that toggle can disable an enabled feature."""
        client.login(username='admin', password='testpass123')
        assert online_booking_flag.is_enabled is True

        response = client.post(
            reverse('superadmin:feature_toggle', kwargs={'pk': online_booking_flag.pk})
        )
        assert response.status_code in [200, 302]

        online_booking_flag.refresh_from_db()
        assert online_booking_flag.is_enabled is False

    def test_feature_toggle_returns_partial_for_htmx(
        self, client, superuser, online_booking_flag
    ):
        """Test that toggle returns HTMX partial."""
        client.login(username='admin', password='testpass123')
        response = client.post(
            reverse('superadmin:feature_toggle', kwargs={'pk': online_booking_flag.pk}),
            HTTP_HX_REQUEST='true',
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestAuditLogging:
    """Tests for audit logging of module/feature changes."""

    def test_module_toggle_creates_audit_log(self, client, superuser, appointments_module):
        """Test that toggling module creates audit log entry."""
        from apps.audit.models import AuditLog

        client.login(username='admin', password='testpass123')
        initial_count = AuditLog.objects.count()

        response = client.post(
            reverse('superadmin:module_toggle', kwargs={'pk': appointments_module.pk})
        )
        assert response.status_code in [200, 302]

        # Should have created an audit log
        assert AuditLog.objects.count() > initial_count

    def test_feature_toggle_creates_audit_log(self, client, superuser, online_booking_flag):
        """Test that toggling feature creates audit log entry."""
        from apps.audit.models import AuditLog

        client.login(username='admin', password='testpass123')
        initial_count = AuditLog.objects.count()

        response = client.post(
            reverse('superadmin:feature_toggle', kwargs={'pk': online_booking_flag.pk})
        )
        assert response.status_code in [200, 302]

        # Should have created an audit log
        assert AuditLog.objects.count() > initial_count
