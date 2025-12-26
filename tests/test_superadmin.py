"""Tests for Superadmin app views."""
import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.practice.models import ClinicSettings

pytestmark = pytest.mark.django_db


class TestSuperadminDashboard:
    """Tests for SuperadminDashboardView."""

    def test_dashboard_requires_login(self, client):
        """Test dashboard redirects to login for anonymous users."""
        url = reverse('superadmin:dashboard')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_dashboard_requires_superuser(self, client, staff_user):
        """Test regular staff cannot access dashboard."""
        client.force_login(staff_user)
        url = reverse('superadmin:dashboard')
        response = client.get(url)
        assert response.status_code == 403

    def test_dashboard_accessible_by_superuser(self, client, superuser):
        """Test superuser can access dashboard."""
        client.force_login(superuser)
        url = reverse('superadmin:dashboard')
        response = client.get(url)
        assert response.status_code == 200

    def test_dashboard_shows_user_metrics(self, client, superuser):
        """Test dashboard displays user statistics."""
        client.force_login(superuser)
        url = reverse('superadmin:dashboard')
        response = client.get(url)
        assert 'total_users' in response.context
        assert 'staff_users' in response.context
        assert 'superusers' in response.context
        assert 'active_users' in response.context

    def test_dashboard_shows_system_health(self, client, superuser):
        """Test dashboard displays system health."""
        client.force_login(superuser)
        url = reverse('superadmin:dashboard')
        response = client.get(url)
        assert 'system_health' in response.context
        assert 'database' in response.context['system_health']


class TestUserListView:
    """Tests for UserListView."""

    def test_user_list_requires_superuser(self, client, staff_user):
        """Test regular staff cannot access user list."""
        client.force_login(staff_user)
        url = reverse('superadmin:user_list')
        response = client.get(url)
        assert response.status_code == 403

    def test_user_list_accessible_by_superuser(self, client, superuser):
        """Test superuser can access user list."""
        client.force_login(superuser)
        url = reverse('superadmin:user_list')
        response = client.get(url)
        assert response.status_code == 200

    def test_user_list_shows_all_users(self, client, superuser, staff_user, regular_user):
        """Test user list displays all users."""
        client.force_login(superuser)
        url = reverse('superadmin:user_list')
        response = client.get(url)
        users = response.context['users']
        assert len(users) >= 3

    def test_user_list_filter_by_staff(self, client, superuser, staff_user, regular_user):
        """Test filtering users by staff status."""
        client.force_login(superuser)
        url = reverse('superadmin:user_list') + '?is_staff=1'
        response = client.get(url)
        users = response.context['users']
        for user in users:
            assert user.is_staff is True

    def test_user_list_filter_by_role(self, client, superuser, staff_user):
        """Test filtering users by role."""
        staff_user.role = 'vet'
        staff_user.save()
        client.force_login(superuser)
        url = reverse('superadmin:user_list') + '?role=vet'
        response = client.get(url)
        users = response.context['users']
        for user in users:
            assert user.role == 'vet'

    def test_user_list_search(self, client, superuser, staff_user):
        """Test searching users by email."""
        client.force_login(superuser)
        url = reverse('superadmin:user_list') + f'?search={staff_user.email}'
        response = client.get(url)
        users = response.context['users']
        assert staff_user in users


class TestUserCreateView:
    """Tests for UserCreateView."""

    def test_user_create_requires_superuser(self, client, staff_user):
        """Test regular staff cannot access user create."""
        client.force_login(staff_user)
        url = reverse('superadmin:user_create')
        response = client.get(url)
        assert response.status_code == 403

    def test_user_create_form_renders(self, client, superuser):
        """Test user create form renders."""
        client.force_login(superuser)
        url = reverse('superadmin:user_create')
        response = client.get(url)
        assert response.status_code == 200
        assert 'form' in response.context

    def test_user_create_success(self, client, superuser):
        """Test creating a new user."""
        client.force_login(superuser)
        url = reverse('superadmin:user_create')
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'staff',
            'is_active': True,
            'is_staff': False,
            'password1': 'securepass123!',
            'password2': 'securepass123!',
        }
        response = client.post(url, data)
        assert response.status_code == 302
        assert User.objects.filter(email='newuser@example.com').exists()


class TestUserUpdateView:
    """Tests for UserUpdateView."""

    def test_user_update_requires_superuser(self, client, staff_user, regular_user):
        """Test regular staff cannot update users."""
        client.force_login(staff_user)
        url = reverse('superadmin:user_update', args=[regular_user.pk])
        response = client.get(url)
        assert response.status_code == 403

    def test_user_update_form_renders(self, client, superuser, regular_user):
        """Test user update form renders."""
        client.force_login(superuser)
        url = reverse('superadmin:user_update', args=[regular_user.pk])
        response = client.get(url)
        assert response.status_code == 200
        assert 'form' in response.context

    def test_user_update_success(self, client, superuser, regular_user):
        """Test updating a user."""
        client.force_login(superuser)
        url = reverse('superadmin:user_update', args=[regular_user.pk])
        data = {
            'email': regular_user.email,
            'username': regular_user.username,
            'first_name': 'Updated',
            'last_name': 'Name',
            'role': 'staff',
            'is_active': True,
            'is_staff': True,
        }
        response = client.post(url, data)
        assert response.status_code == 302
        regular_user.refresh_from_db()
        assert regular_user.first_name == 'Updated'
        assert regular_user.is_staff is True


class TestUserDeactivateView:
    """Tests for UserDeactivateView (soft delete)."""

    def test_deactivate_requires_superuser(self, client, staff_user, regular_user):
        """Test regular staff cannot deactivate users."""
        client.force_login(staff_user)
        url = reverse('superadmin:user_deactivate', args=[regular_user.pk])
        response = client.get(url)
        assert response.status_code == 403

    def test_deactivate_confirmation_renders(self, client, superuser, regular_user):
        """Test deactivation confirmation page renders."""
        client.force_login(superuser)
        url = reverse('superadmin:user_deactivate', args=[regular_user.pk])
        response = client.get(url)
        assert response.status_code == 200

    def test_deactivate_soft_deletes_user(self, client, superuser, regular_user):
        """Test user is soft deleted (deactivated, not removed)."""
        assert regular_user.is_active is True
        client.force_login(superuser)
        url = reverse('superadmin:user_deactivate', args=[regular_user.pk])
        response = client.post(url)
        assert response.status_code == 302
        regular_user.refresh_from_db()
        assert regular_user.is_active is False
        assert User.objects.filter(pk=regular_user.pk).exists()


class TestRoleListView:
    """Tests for RoleListView."""

    def test_role_list_requires_superuser(self, client, staff_user):
        """Test regular staff cannot access role list."""
        client.force_login(staff_user)
        url = reverse('superadmin:role_list')
        response = client.get(url)
        assert response.status_code == 403

    def test_role_list_accessible_by_superuser(self, client, superuser):
        """Test superuser can access role list."""
        client.force_login(superuser)
        url = reverse('superadmin:role_list')
        response = client.get(url)
        assert response.status_code == 200

    def test_role_list_shows_roles(self, client, superuser):
        """Test role list displays user roles."""
        client.force_login(superuser)
        url = reverse('superadmin:role_list')
        response = client.get(url)
        assert 'user_roles' in response.context
        assert len(response.context['user_roles']) > 0


class TestSettingsView:
    """Tests for SettingsView."""

    def test_settings_requires_superuser(self, client, staff_user):
        """Test regular staff cannot access settings."""
        client.force_login(staff_user)
        url = reverse('superadmin:settings')
        response = client.get(url)
        assert response.status_code == 403

    def test_settings_form_renders(self, client, superuser):
        """Test settings form renders."""
        client.force_login(superuser)
        url = reverse('superadmin:settings')
        response = client.get(url)
        assert response.status_code == 200
        assert 'form' in response.context

    def test_settings_creates_if_not_exists(self, client, superuser):
        """Test settings are created if they don't exist."""
        ClinicSettings.objects.all().delete()
        client.force_login(superuser)
        url = reverse('superadmin:settings')
        response = client.get(url)
        assert response.status_code == 200
        assert ClinicSettings.objects.exists()

    def test_settings_save_success(self, client, superuser):
        """Test saving settings."""
        import json
        client.force_login(superuser)
        url = reverse('superadmin:settings')
        # First GET creates the settings with defaults
        client.get(url)
        data = {
            'name': 'Updated Clinic Name',
            'legal_name': 'Updated Legal Name LLC',
            'tax_id': 'TAX123',
            'address': '123 Main St, City',
            'phone': '555-1234',
            'email': 'updated@clinic.com',
            'website': 'https://clinic.com',
            'opening_time': '08:00',
            'closing_time': '18:00',
            'days_open': json.dumps(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']),
            'emergency_phone': '555-9999',
            'emergency_available': True,
            'facebook_url': '',
            'instagram_url': '',
            'google_maps_url': '',
            'primary_color': '#2563eb',
        }
        response = client.post(url, data)
        assert response.status_code == 302
        settings = ClinicSettings.objects.get(pk=1)
        assert settings.name == 'Updated Clinic Name'


class TestAuditDashboardView:
    """Tests for AuditDashboardView."""

    def test_audit_dashboard_requires_superuser(self, client, staff_user):
        """Test regular staff cannot access audit dashboard."""
        client.force_login(staff_user)
        url = reverse('superadmin:audit_dashboard')
        response = client.get(url)
        assert response.status_code == 403

    def test_audit_dashboard_accessible_by_superuser(self, client, superuser):
        """Test superuser can access audit dashboard."""
        client.force_login(superuser)
        url = reverse('superadmin:audit_dashboard')
        response = client.get(url)
        assert response.status_code == 200

    def test_audit_dashboard_shows_logs(self, client, superuser, audit_log):
        """Test audit dashboard displays logs."""
        client.force_login(superuser)
        url = reverse('superadmin:audit_dashboard')
        response = client.get(url)
        assert 'audit_logs' in response.context

    def test_audit_dashboard_filter_by_user(self, client, superuser, staff_user):
        """Test filtering audit logs by user."""
        AuditLog.objects.create(
            user=staff_user,
            action='login',
            ip_address='127.0.0.1',
        )
        client.force_login(superuser)
        url = reverse('superadmin:audit_dashboard') + f'?user={staff_user.pk}'
        response = client.get(url)
        logs = response.context['audit_logs']
        for log in logs:
            assert log.user_id == staff_user.pk


class TestMonitoringView:
    """Tests for MonitoringView."""

    def test_monitoring_requires_superuser(self, client, staff_user):
        """Test regular staff cannot access monitoring."""
        client.force_login(staff_user)
        url = reverse('superadmin:monitoring')
        response = client.get(url)
        assert response.status_code == 403

    def test_monitoring_accessible_by_superuser(self, client, superuser):
        """Test superuser can access monitoring."""
        client.force_login(superuser)
        url = reverse('superadmin:monitoring')
        response = client.get(url)
        assert response.status_code == 200

    def test_monitoring_shows_model_counts(self, client, superuser):
        """Test monitoring displays model counts."""
        client.force_login(superuser)
        url = reverse('superadmin:monitoring')
        response = client.get(url)
        assert 'model_counts' in response.context
        assert 'users' in response.context['model_counts']

    def test_monitoring_shows_db_stats(self, client, superuser):
        """Test monitoring displays database stats."""
        client.force_login(superuser)
        url = reverse('superadmin:monitoring')
        response = client.get(url)
        assert 'db_stats' in response.context


class TestSuperuserRequiredMixin:
    """Tests for SuperuserRequiredMixin."""

    def test_mixin_allows_superuser(self, client, superuser):
        """Test mixin allows superuser access."""
        client.force_login(superuser)
        url = reverse('superadmin:dashboard')
        response = client.get(url)
        assert response.status_code == 200

    def test_mixin_blocks_staff(self, client, staff_user):
        """Test mixin blocks non-superuser staff."""
        client.force_login(staff_user)
        url = reverse('superadmin:dashboard')
        response = client.get(url)
        assert response.status_code == 403

    def test_mixin_blocks_regular_user(self, client, regular_user):
        """Test mixin blocks regular users."""
        client.force_login(regular_user)
        url = reverse('superadmin:dashboard')
        response = client.get(url)
        assert response.status_code == 403


# Fixtures
@pytest.fixture
def superuser(db):
    """Create a superuser."""
    return User.objects.create_superuser(
        username='superadmin',
        email='superadmin@example.com',
        password='superpass123',
        first_name='Super',
        last_name='Admin',
    )


@pytest.fixture
def staff_user(db):
    """Create a staff user (not superuser)."""
    return User.objects.create_user(
        username='staffuser',
        email='staff@example.com',
        password='staffpass123',
        first_name='Staff',
        last_name='User',
        is_staff=True,
        role='staff',
    )


@pytest.fixture
def regular_user(db):
    """Create a regular user."""
    return User.objects.create_user(
        username='regularuser',
        email='regular@example.com',
        password='regularpass123',
        first_name='Regular',
        last_name='User',
        role='owner',
    )


@pytest.fixture
def audit_log(staff_user):
    """Create an audit log entry."""
    return AuditLog.objects.create(
        user=staff_user,
        action='login',
        ip_address='127.0.0.1',
    )
