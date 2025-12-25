"""Tests for the audit logging module."""
import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from apps.audit.models import AuditLog
from apps.audit.services import AuditService
from apps.audit.middleware import AuditMiddleware

User = get_user_model()


@pytest.fixture
def staff_user(db):
    """Create a staff user for testing."""
    return User.objects.create_user(
        username='audit_staff',
        email='audit_staff@example.com',
        password='testpass123',
        first_name='Audit',
        last_name='Staff',
        is_staff=True,
    )


@pytest.fixture
def regular_user(db):
    """Create a regular (non-staff) user."""
    return User.objects.create_user(
        username='regular_user',
        email='regular@example.com',
        password='testpass123',
        is_staff=False,
    )


@pytest.fixture
def request_factory():
    """Request factory for creating mock requests."""
    return RequestFactory()


class TestAuditLogModel:
    """Test AuditLog model."""

    def test_create_audit_log_entry(self, db, staff_user):
        """Can create basic audit log entry."""
        log = AuditLog.objects.create(
            user=staff_user,
            action='view',
            resource_type='inventory.dashboard',
        )
        assert log.pk is not None
        assert log.action == 'view'
        assert log.resource_type == 'inventory.dashboard'
        assert log.user == staff_user

    def test_audit_log_with_resource_id(self, db, staff_user):
        """Audit log captures resource ID correctly."""
        log = AuditLog.objects.create(
            user=staff_user,
            action='view',
            resource_type='referrals.referral',
            resource_id='123',
        )
        assert log.resource_id == '123'

    def test_audit_log_sensitivity_levels(self, db, staff_user):
        """Different sensitivity levels are stored correctly."""
        normal = AuditLog.objects.create(
            user=staff_user,
            action='view',
            resource_type='inventory.dashboard',
            sensitivity='normal',
        )
        high = AuditLog.objects.create(
            user=staff_user,
            action='view',
            resource_type='referrals.referral',
            sensitivity='high',
        )
        critical = AuditLog.objects.create(
            user=staff_user,
            action='view',
            resource_type='pharmacy.controlled_substance',
            sensitivity='critical',
        )
        assert normal.sensitivity == 'normal'
        assert high.sensitivity == 'high'
        assert critical.sensitivity == 'critical'

    def test_audit_log_str_representation(self, db, staff_user):
        """String representation is readable."""
        log = AuditLog.objects.create(
            user=staff_user,
            action='view',
            resource_type='inventory.dashboard',
        )
        assert staff_user.email in str(log)
        assert 'view' in str(log)
        assert 'inventory.dashboard' in str(log)

    def test_audit_log_ordering(self, db, staff_user):
        """Logs are ordered by created_at descending."""
        log1 = AuditLog.objects.create(
            user=staff_user,
            action='view',
            resource_type='inventory.dashboard',
        )
        log2 = AuditLog.objects.create(
            user=staff_user,
            action='view',
            resource_type='practice.dashboard',
        )
        logs = list(AuditLog.objects.all())
        assert logs[0] == log2
        assert logs[1] == log1


class TestAuditService:
    """Test AuditService helper."""

    def test_log_action_creates_entry(self, db, staff_user):
        """AuditService.log_action creates AuditLog entry."""
        log = AuditService.log_action(
            user=staff_user,
            action='view',
            resource_type='inventory.dashboard',
        )
        assert log.pk is not None
        assert log.user == staff_user
        assert log.action == 'view'

    def test_log_action_with_request(self, db, staff_user, request_factory):
        """AuditService.log_action captures request context."""
        request = request_factory.get('/inventory/')
        request.META['HTTP_USER_AGENT'] = 'Test Browser'
        request.META['REMOTE_ADDR'] = '192.168.1.1'

        log = AuditService.log_action(
            user=staff_user,
            action='view',
            resource_type='inventory.dashboard',
            request=request,
        )
        assert log.url_path == '/inventory/'
        assert log.method == 'GET'
        assert log.user_agent == 'Test Browser'
        assert log.ip_address == '192.168.1.1'

    def test_log_action_with_extra_data(self, db, staff_user):
        """AuditService.log_action captures extra data."""
        log = AuditService.log_action(
            user=staff_user,
            action='export',
            resource_type='reports.inventory',
            format='csv',
            rows=1000,
        )
        assert log.extra_data['format'] == 'csv'
        assert log.extra_data['rows'] == 1000

    def test_get_client_ip_with_forwarded_for(self, db, request_factory):
        """get_client_ip handles X-Forwarded-For header."""
        request = request_factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '203.0.113.1, 192.168.1.1'
        request.META['REMOTE_ADDR'] = '10.0.0.1'

        ip = AuditService.get_client_ip(request)
        assert ip == '203.0.113.1'

    def test_get_client_ip_without_forwarded_for(self, db, request_factory):
        """get_client_ip falls back to REMOTE_ADDR."""
        request = request_factory.get('/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'

        ip = AuditService.get_client_ip(request)
        assert ip == '192.168.1.1'


class TestAuditMiddleware:
    """Test AuditMiddleware."""

    def test_get_resource_type_inventory_dashboard(self):
        """Resource type mapping for inventory dashboard."""
        middleware = AuditMiddleware(lambda r: None)
        assert middleware._get_resource_type('/inventory/') == 'inventory.dashboard'

    def test_get_resource_type_inventory_stock(self):
        """Resource type mapping for inventory stock."""
        middleware = AuditMiddleware(lambda r: None)
        assert middleware._get_resource_type('/inventory/stock/') == 'inventory.stock'

    def test_get_resource_type_practice_settings(self):
        """Resource type mapping for practice settings."""
        middleware = AuditMiddleware(lambda r: None)
        assert middleware._get_resource_type('/practice/settings/') == 'practice.settings'

    def test_get_resource_type_with_id(self):
        """Resource type extracts correctly with ID in path."""
        middleware = AuditMiddleware(lambda r: None)
        assert middleware._get_resource_type('/referrals/outbound/123/') == 'referrals.referral'

    def test_extract_resource_id(self):
        """Resource ID extraction from URL."""
        middleware = AuditMiddleware(lambda r: None)
        assert middleware._extract_resource_id('/referrals/outbound/123/') == '123'
        assert middleware._extract_resource_id('/referrals/outbound/') == ''
        assert middleware._extract_resource_id('/inventory/') == ''

    def test_get_sensitivity_normal(self):
        """Normal sensitivity for inventory paths."""
        middleware = AuditMiddleware(lambda r: None)
        assert middleware._get_sensitivity('/inventory/stock/') == 'normal'

    def test_get_sensitivity_high(self):
        """High sensitivity for referrals/prescriptions."""
        middleware = AuditMiddleware(lambda r: None)
        assert middleware._get_sensitivity('/referrals/outbound/123/') == 'high'
        assert middleware._get_sensitivity('/pharmacy/prescriptions/') == 'high'
        assert middleware._get_sensitivity('/practice/settings/') == 'high'

    def test_should_audit_inventory(self):
        """Should audit inventory paths."""
        middleware = AuditMiddleware(lambda r: None)
        assert middleware._should_audit('/inventory/') is True
        assert middleware._should_audit('/inventory/stock/') is True

    def test_should_not_audit_store(self):
        """Should not audit store paths (customer-facing)."""
        middleware = AuditMiddleware(lambda r: None)
        assert middleware._should_audit('/store/') is False
        assert middleware._should_audit('/accounts/') is False
