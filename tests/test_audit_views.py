"""
Tests for Audit Views (TDD)

Tests cover:
- Audit Log list view (staff only)
- Audit Log detail view
- User activity report
- Export functionality
"""
import pytest
from datetime import date, timedelta
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.audit.models import AuditLog

User = get_user_model()

pytestmark = pytest.mark.django_db


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def staff_user():
    """Create a staff user."""
    return User.objects.create_user(
        username='staffuser',
        email='staff@test.com',
        password='testpass123',
        is_staff=True
    )


@pytest.fixture
def regular_user():
    """Create a regular (non-staff) user."""
    return User.objects.create_user(
        username='regularuser',
        email='regular@test.com',
        password='testpass123',
        is_staff=False
    )


@pytest.fixture
def audit_log(staff_user):
    """Create an audit log entry."""
    return AuditLog.objects.create(
        user=staff_user,
        action='view',
        resource_type='inventory.dashboard',
        resource_id='',
        url_path='/inventory/',
        method='GET',
        ip_address='127.0.0.1',
        sensitivity='normal'
    )


@pytest.fixture
def multiple_audit_logs(staff_user, regular_user):
    """Create multiple audit log entries."""
    logs = []
    for i in range(15):
        logs.append(AuditLog.objects.create(
            user=staff_user if i % 2 == 0 else regular_user,
            action='view' if i % 3 == 0 else 'create',
            resource_type='inventory.dashboard' if i % 2 == 0 else 'practice.dashboard',
            resource_id=str(i),
            url_path=f'/test/{i}/',
            method='GET',
            ip_address='127.0.0.1',
            sensitivity='normal' if i % 4 == 0 else 'high'
        ))
    return logs


# =============================================================================
# Audit Log List Tests
# =============================================================================

class TestAuditLogList:
    """Tests for the Audit Log list view."""

    def test_audit_list_requires_authentication(self, client):
        """Anonymous users should be redirected to login."""
        url = reverse('audit:log_list')
        response = client.get(url)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_audit_list_requires_staff(self, client, regular_user):
        """Non-staff users should be denied access."""
        client.force_login(regular_user)
        url = reverse('audit:log_list')
        response = client.get(url)
        assert response.status_code == 403

    def test_audit_list_accessible_by_staff(self, client, staff_user):
        """Staff users should access the audit log list."""
        client.force_login(staff_user)
        url = reverse('audit:log_list')
        response = client.get(url)
        assert response.status_code == 200

    def test_audit_list_shows_logs(self, client, staff_user, audit_log):
        """Audit list should show audit log entries."""
        client.force_login(staff_user)
        url = reverse('audit:log_list')
        response = client.get(url)
        assert response.status_code == 200
        assert 'logs' in response.context
        assert audit_log in response.context['logs']

    def test_audit_list_is_paginated(self, client, staff_user, multiple_audit_logs):
        """Audit list should be paginated."""
        client.force_login(staff_user)
        url = reverse('audit:log_list')
        response = client.get(url)
        assert response.status_code == 200
        assert 'is_paginated' in response.context or hasattr(response.context.get('logs'), 'paginator')

    def test_audit_list_filter_by_user(self, client, staff_user, multiple_audit_logs):
        """Audit list should filter by user."""
        client.force_login(staff_user)
        url = reverse('audit:log_list') + f'?user={staff_user.pk}'
        response = client.get(url)
        assert response.status_code == 200

    def test_audit_list_filter_by_action(self, client, staff_user, multiple_audit_logs):
        """Audit list should filter by action type."""
        client.force_login(staff_user)
        url = reverse('audit:log_list') + '?action=view'
        response = client.get(url)
        assert response.status_code == 200

    def test_audit_list_filter_by_resource_type(self, client, staff_user, multiple_audit_logs):
        """Audit list should filter by resource type."""
        client.force_login(staff_user)
        url = reverse('audit:log_list') + '?resource_type=inventory.dashboard'
        response = client.get(url)
        assert response.status_code == 200


# =============================================================================
# Audit Log Detail Tests
# =============================================================================

class TestAuditLogDetail:
    """Tests for the Audit Log detail view."""

    def test_audit_detail_requires_staff(self, client, regular_user, audit_log):
        """Non-staff users should be denied access."""
        client.force_login(regular_user)
        url = reverse('audit:log_detail', kwargs={'pk': audit_log.pk})
        response = client.get(url)
        assert response.status_code == 403

    def test_audit_detail_shows_log_info(self, client, staff_user, audit_log):
        """Audit detail should show log information."""
        client.force_login(staff_user)
        url = reverse('audit:log_detail', kwargs={'pk': audit_log.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert response.context['log'] == audit_log

    def test_audit_detail_shows_user_info(self, client, staff_user, audit_log):
        """Audit detail should show user information."""
        client.force_login(staff_user)
        url = reverse('audit:log_detail', kwargs={'pk': audit_log.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert 'log' in response.context
        assert response.context['log'].user == staff_user


# =============================================================================
# User Activity Report Tests
# =============================================================================

class TestUserActivityReport:
    """Tests for the User Activity Report view."""

    def test_activity_report_requires_staff(self, client, regular_user):
        """Non-staff users should be denied access."""
        client.force_login(regular_user)
        url = reverse('audit:user_activity')
        response = client.get(url)
        assert response.status_code == 403

    def test_activity_report_accessible_by_staff(self, client, staff_user):
        """Staff users should access the activity report."""
        client.force_login(staff_user)
        url = reverse('audit:user_activity')
        response = client.get(url)
        assert response.status_code == 200

    def test_activity_report_shows_summary(self, client, staff_user, multiple_audit_logs):
        """Activity report should show user activity summary."""
        client.force_login(staff_user)
        url = reverse('audit:user_activity')
        response = client.get(url)
        assert response.status_code == 200
        assert 'user_stats' in response.context


# =============================================================================
# Audit Dashboard Tests
# =============================================================================

class TestAuditDashboard:
    """Tests for the Audit Dashboard view."""

    def test_dashboard_requires_staff(self, client, regular_user):
        """Non-staff users should be denied access."""
        client.force_login(regular_user)
        url = reverse('audit:dashboard')
        response = client.get(url)
        assert response.status_code == 403

    def test_dashboard_accessible_by_staff(self, client, staff_user):
        """Staff users should access the dashboard."""
        client.force_login(staff_user)
        url = reverse('audit:dashboard')
        response = client.get(url)
        assert response.status_code == 200

    def test_dashboard_shows_recent_logs(self, client, staff_user, multiple_audit_logs):
        """Dashboard should show recent audit logs."""
        client.force_login(staff_user)
        url = reverse('audit:dashboard')
        response = client.get(url)
        assert response.status_code == 200
        assert 'recent_logs' in response.context

    def test_dashboard_shows_stats(self, client, staff_user, multiple_audit_logs):
        """Dashboard should show audit statistics."""
        client.force_login(staff_user)
        url = reverse('audit:dashboard')
        response = client.get(url)
        assert response.status_code == 200
        assert 'total_logs' in response.context
