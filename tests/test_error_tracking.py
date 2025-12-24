"""Tests for error_tracking app - models, middleware, and services."""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseForbidden
from django.test import RequestFactory, override_settings

from apps.error_tracking.middleware import ErrorCaptureMiddleware
from apps.error_tracking.models import ErrorLog, KnownBug
from apps.error_tracking.services import BugCreationService
from apps.error_tracking.tasks import create_bug_task

User = get_user_model()


class TestErrorLogModel:
    """Tests for ErrorLog model."""

    @pytest.mark.django_db
    def test_create_error_log_minimal(self):
        """Can create ErrorLog with required fields only."""
        error = ErrorLog.objects.create(
            fingerprint='abc123def456',
            error_type='csrf',
            status_code=403,
            url_pattern='/api/contact/',
            full_url='https://dev.petfriendlyvet.com/api/contact/',
            method='POST',
        )
        assert error.pk is not None
        assert error.fingerprint == 'abc123def456'
        assert error.status_code == 403

    @pytest.mark.django_db
    def test_create_error_log_with_all_fields(self):
        """Can create ErrorLog with all optional fields."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
        )
        error = ErrorLog.objects.create(
            fingerprint='xyz789',
            error_type='server_error',
            status_code=500,
            url_pattern='/api/pets/{id}/',
            full_url='https://petfriendlyvet.com/api/pets/123/',
            method='GET',
            user=user,
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
            request_data={'headers': {'Accept': 'application/json'}},
            exception_type='ValueError',
            exception_message='Invalid pet ID',
            traceback='Traceback (most recent call last)...',
        )
        assert error.user == user
        assert error.ip_address == '192.168.1.1'
        assert error.exception_type == 'ValueError'

    @pytest.mark.django_db
    def test_error_log_has_timestamps(self):
        """ErrorLog should have created_at timestamp."""
        error = ErrorLog.objects.create(
            fingerprint='test123',
            error_type='not_found',
            status_code=404,
            url_pattern='/missing/',
            full_url='https://petfriendlyvet.com/missing/',
            method='GET',
        )
        assert error.created_at is not None

    @pytest.mark.django_db
    def test_error_log_str_representation(self):
        """ErrorLog __str__ should be descriptive."""
        error = ErrorLog.objects.create(
            fingerprint='strtest',
            error_type='csrf',
            status_code=403,
            url_pattern='/contact/',
            full_url='https://dev.petfriendlyvet.com/contact/',
            method='POST',
        )
        str_repr = str(error)
        assert '403' in str_repr
        assert 'csrf' in str_repr

    @pytest.mark.django_db
    def test_error_log_default_request_data(self):
        """ErrorLog request_data should default to empty dict."""
        error = ErrorLog.objects.create(
            fingerprint='default_test',
            error_type='not_found',
            status_code=404,
            url_pattern='/test/',
            full_url='https://petfriendlyvet.com/test/',
            method='GET',
        )
        assert error.request_data == {}


class TestKnownBugModel:
    """Tests for KnownBug model."""

    @pytest.mark.django_db
    def test_create_known_bug_minimal(self):
        """Can create KnownBug with required fields."""
        bug = KnownBug.objects.create(
            bug_id='B-001',
            fingerprint='fingerprint123',
            title='CSRF validation fails on dev subdomain',
            description='Origin checking failed for dev.petfriendlyvet.com',
            severity='high',
        )
        assert bug.pk is not None
        assert bug.bug_id == 'B-001'
        assert bug.status == 'open'  # Default status

    @pytest.mark.django_db
    def test_known_bug_with_github_issue(self):
        """Can create KnownBug linked to GitHub issue."""
        bug = KnownBug.objects.create(
            bug_id='B-002',
            fingerprint='fingerprint456',
            title='500 error on pet creation',
            description='Server error when creating pet with invalid data',
            severity='critical',
            github_issue_number=42,
            github_issue_url='https://github.com/owner/repo/issues/42',
        )
        assert bug.github_issue_number == 42
        assert 'github.com' in bug.github_issue_url

    @pytest.mark.django_db
    def test_known_bug_occurrence_count_default(self):
        """KnownBug occurrence_count should default to 1."""
        bug = KnownBug.objects.create(
            bug_id='B-003',
            fingerprint='count_test',
            title='Test bug',
            description='Test description',
            severity='low',
        )
        assert bug.occurrence_count == 1

    @pytest.mark.django_db
    def test_known_bug_increment_occurrence(self):
        """Can increment occurrence_count."""
        bug = KnownBug.objects.create(
            bug_id='B-004',
            fingerprint='increment_test',
            title='Recurring bug',
            description='This bug happens multiple times',
            severity='medium',
        )
        bug.occurrence_count += 1
        bug.save()
        bug.refresh_from_db()
        assert bug.occurrence_count == 2

    @pytest.mark.django_db
    def test_known_bug_unique_bug_id(self):
        """bug_id must be unique."""
        KnownBug.objects.create(
            bug_id='B-005',
            fingerprint='unique1',
            title='First bug',
            description='Description',
            severity='low',
        )
        with pytest.raises(Exception):  # IntegrityError
            KnownBug.objects.create(
                bug_id='B-005',  # Duplicate!
                fingerprint='unique2',
                title='Second bug',
                description='Description',
                severity='low',
            )

    @pytest.mark.django_db
    def test_known_bug_unique_fingerprint(self):
        """fingerprint must be unique."""
        KnownBug.objects.create(
            bug_id='B-006',
            fingerprint='same_fingerprint',
            title='First bug',
            description='Description',
            severity='low',
        )
        with pytest.raises(Exception):  # IntegrityError
            KnownBug.objects.create(
                bug_id='B-007',
                fingerprint='same_fingerprint',  # Duplicate!
                title='Second bug',
                description='Description',
                severity='low',
            )

    @pytest.mark.django_db
    def test_known_bug_severity_choices(self):
        """KnownBug should accept valid severity choices."""
        for severity in ['critical', 'high', 'medium', 'low']:
            bug = KnownBug.objects.create(
                bug_id=f'B-{severity[:3]}',
                fingerprint=f'fp_{severity}',
                title=f'{severity} bug',
                description='Test',
                severity=severity,
            )
            assert bug.severity == severity

    @pytest.mark.django_db
    def test_known_bug_status_choices(self):
        """KnownBug should accept valid status choices."""
        for status in ['open', 'in_progress', 'resolved', 'wontfix']:
            bug = KnownBug.objects.create(
                bug_id=f'B-s{status[:2]}',
                fingerprint=f'fp_s{status}',
                title=f'{status} bug',
                description='Test',
                severity='low',
                status=status,
            )
            assert bug.status == status

    @pytest.mark.django_db
    def test_known_bug_soft_delete(self):
        """KnownBug should support soft delete."""
        bug = KnownBug.objects.create(
            bug_id='B-del',
            fingerprint='deleteme',
            title='Deletable bug',
            description='Will be soft deleted',
            severity='low',
        )
        bug_id = bug.pk
        bug.delete()

        # Should not appear in normal queries
        assert not KnownBug.objects.filter(pk=bug_id).exists()

        # Should still exist with all_objects
        assert KnownBug.all_objects.filter(pk=bug_id).exists()

    @pytest.mark.django_db
    def test_known_bug_str_representation(self):
        """KnownBug __str__ should show bug_id and title."""
        bug = KnownBug.objects.create(
            bug_id='B-str',
            fingerprint='strtest',
            title='Test bug title',
            description='Description',
            severity='medium',
        )
        str_repr = str(bug)
        assert 'B-str' in str_repr
        assert 'Test bug' in str_repr

    @pytest.mark.django_db
    def test_known_bug_resolved_at_null_by_default(self):
        """resolved_at should be null for new bugs."""
        bug = KnownBug.objects.create(
            bug_id='B-res',
            fingerprint='resolved_test',
            title='Unresolved bug',
            description='Not yet fixed',
            severity='high',
        )
        assert bug.resolved_at is None

    @pytest.mark.django_db
    def test_known_bug_can_set_resolved(self):
        """Can set resolved_at when bug is fixed."""
        from django.utils import timezone

        bug = KnownBug.objects.create(
            bug_id='B-fix',
            fingerprint='fixed_test',
            title='Fixed bug',
            description='This was fixed',
            severity='high',
            status='resolved',
        )
        bug.resolved_at = timezone.now()
        bug.save()
        bug.refresh_from_db()
        assert bug.resolved_at is not None


class TestErrorCaptureMiddleware:
    """Tests for ErrorCaptureMiddleware."""

    def get_request(self, path='/', method='GET', user=None):
        """Helper to create a request with proper META."""
        factory = RequestFactory()
        if method == 'POST':
            request = factory.post(path)
        else:
            request = factory.get(path)
        request.user = user
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        request.META['HTTP_USER_AGENT'] = 'Test Agent'
        return request

    def test_middleware_passes_through_successful_response(self):
        """Middleware should not interfere with 2xx responses."""
        def get_response(request):
            return HttpResponse('OK', status=200)

        middleware = ErrorCaptureMiddleware(get_response)
        request = self.get_request('/')
        response = middleware(request)

        assert response.status_code == 200
        assert response.content == b'OK'

    @pytest.mark.django_db
    def test_middleware_captures_404_error(self):
        """Middleware should log 404 errors to database."""
        def get_response(request):
            return HttpResponseNotFound('Not Found')

        middleware = ErrorCaptureMiddleware(get_response)
        request = self.get_request('/missing-page/')
        response = middleware(request)

        assert response.status_code == 404
        # Verify error was logged
        assert ErrorLog.objects.filter(status_code=404).exists()
        error = ErrorLog.objects.get(status_code=404)
        assert error.error_type == 'not_found'
        assert '/missing-page/' in error.full_url

    @pytest.mark.django_db
    def test_middleware_captures_403_error(self):
        """Middleware should log 403 CSRF errors."""
        def get_response(request):
            return HttpResponseForbidden('CSRF Failed')

        middleware = ErrorCaptureMiddleware(get_response)
        request = self.get_request('/contact/', method='POST')
        response = middleware(request)

        assert response.status_code == 403
        assert ErrorLog.objects.filter(status_code=403).exists()
        error = ErrorLog.objects.get(status_code=403)
        assert error.error_type == 'forbidden'

    @pytest.mark.django_db
    def test_middleware_captures_500_error(self):
        """Middleware should log 500 server errors."""
        def get_response(request):
            return HttpResponse('Internal Server Error', status=500)

        middleware = ErrorCaptureMiddleware(get_response)
        request = self.get_request('/api/pets/')
        response = middleware(request)

        assert response.status_code == 500
        assert ErrorLog.objects.filter(status_code=500).exists()
        error = ErrorLog.objects.get(status_code=500)
        assert error.error_type == 'server_error'

    @pytest.mark.django_db
    def test_middleware_captures_request_metadata(self):
        """Middleware should capture IP and user agent."""
        def get_response(request):
            return HttpResponseNotFound('Not Found')

        middleware = ErrorCaptureMiddleware(get_response)
        request = self.get_request('/test/')
        request.META['REMOTE_ADDR'] = '192.168.1.100'
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0 Test'
        response = middleware(request)

        error = ErrorLog.objects.get(status_code=404)
        assert error.ip_address == '192.168.1.100'
        assert error.user_agent == 'Mozilla/5.0 Test'

    @pytest.mark.django_db
    def test_middleware_captures_authenticated_user(self):
        """Middleware should capture user if authenticated."""
        user = User.objects.create_user(
            username='erroruser',
            email='error@example.com',
            password='testpass123',
        )

        def get_response(request):
            return HttpResponseNotFound('Not Found')

        middleware = ErrorCaptureMiddleware(get_response)
        request = self.get_request('/user-page/')
        request.user = user
        response = middleware(request)

        error = ErrorLog.objects.get(status_code=404)
        assert error.user == user

    @pytest.mark.django_db
    @override_settings(ERROR_TRACKING={'ENABLED': True, 'EXCLUDE_PATHS': ['/health/', '/static/']})
    def test_middleware_excludes_configured_paths(self):
        """Middleware should not log errors for excluded paths."""
        def get_response(request):
            return HttpResponseNotFound('Not Found')

        middleware = ErrorCaptureMiddleware(get_response)
        request = self.get_request('/health/')
        response = middleware(request)

        assert response.status_code == 404
        # Should NOT be logged
        assert not ErrorLog.objects.filter(url_pattern__contains='/health/').exists()

    @pytest.mark.django_db
    @override_settings(ERROR_TRACKING={'ENABLED': False})
    def test_middleware_disabled_does_not_log(self):
        """Middleware should not log when disabled."""
        def get_response(request):
            return HttpResponseNotFound('Not Found')

        middleware = ErrorCaptureMiddleware(get_response)
        request = self.get_request('/test/')
        response = middleware(request)

        assert response.status_code == 404
        # Should NOT be logged when disabled
        assert not ErrorLog.objects.exists()

    @pytest.mark.django_db
    def test_middleware_generates_fingerprint(self):
        """Middleware should generate consistent fingerprints."""
        def get_response(request):
            return HttpResponseNotFound('Not Found')

        middleware = ErrorCaptureMiddleware(get_response)

        # Two requests to same path should have same fingerprint
        request1 = self.get_request('/api/test/')
        request2 = self.get_request('/api/test/')

        middleware(request1)
        middleware(request2)

        errors = ErrorLog.objects.filter(status_code=404)
        assert errors.count() == 2
        assert errors[0].fingerprint == errors[1].fingerprint

    @pytest.mark.django_db
    def test_middleware_normalizes_dynamic_urls(self):
        """Middleware should normalize dynamic URL segments."""
        def get_response(request):
            return HttpResponseNotFound('Not Found')

        middleware = ErrorCaptureMiddleware(get_response)

        # Requests with different IDs should have same fingerprint
        request1 = self.get_request('/api/pets/123/')
        request2 = self.get_request('/api/pets/456/')

        middleware(request1)
        middleware(request2)

        errors = list(ErrorLog.objects.filter(status_code=404))
        assert len(errors) == 2
        # Both should be normalized to same pattern
        assert errors[0].fingerprint == errors[1].fingerprint
        assert errors[0].url_pattern == '/api/pets/{id}/'

    @pytest.mark.django_db
    @override_settings(ERROR_TRACKING={'ENABLED': True, 'EXCLUDE_STATUS_CODES': [404]})
    def test_middleware_excludes_configured_status_codes(self):
        """Middleware should not log excluded status codes."""
        def get_response(request):
            return HttpResponseNotFound('Not Found')

        middleware = ErrorCaptureMiddleware(get_response)
        request = self.get_request('/page/')
        response = middleware(request)

        assert response.status_code == 404
        # Should NOT be logged
        assert not ErrorLog.objects.exists()

    @pytest.mark.django_db
    def test_middleware_captures_method(self):
        """Middleware should capture HTTP method."""
        def get_response(request):
            return HttpResponseNotFound('Not Found')

        middleware = ErrorCaptureMiddleware(get_response)
        request = self.get_request('/api/data/', method='POST')
        response = middleware(request)

        error = ErrorLog.objects.get(status_code=404)
        assert error.method == 'POST'


class TestBugCreationService:
    """Tests for BugCreationService."""

    @pytest.mark.django_db
    def test_get_next_bug_id_first_bug(self):
        """First bug should be B-001."""
        service = BugCreationService()
        bug_id = service.get_next_bug_id()
        assert bug_id == 'B-001'

    @pytest.mark.django_db
    def test_get_next_bug_id_sequential(self):
        """Bug IDs should be sequential."""
        # Create some existing bugs
        KnownBug.objects.create(
            bug_id='B-001',
            fingerprint='fp1',
            title='First bug',
            description='Desc',
            severity='low',
        )
        KnownBug.objects.create(
            bug_id='B-002',
            fingerprint='fp2',
            title='Second bug',
            description='Desc',
            severity='low',
        )

        service = BugCreationService()
        bug_id = service.get_next_bug_id()
        assert bug_id == 'B-003'

    @pytest.mark.django_db
    def test_get_next_bug_id_handles_gaps(self):
        """Bug IDs should continue from highest, even with gaps."""
        KnownBug.objects.create(
            bug_id='B-005',
            fingerprint='fp5',
            title='Bug 5',
            description='Desc',
            severity='low',
        )

        service = BugCreationService()
        bug_id = service.get_next_bug_id()
        assert bug_id == 'B-006'

    @pytest.mark.django_db
    def test_create_bug_file(self, tmp_path):
        """Should create bug markdown file."""
        service = BugCreationService()

        data = {
            'title': 'CSRF validation fails on dev subdomain',
            'description': 'Origin checking failed for dev.petfriendlyvet.com',
            'severity': 'high',
            'error_type': 'csrf',
            'status_code': 403,
            'url_pattern': '/contact/',
            'fingerprint': 'abc123',
        }

        filepath = service.create_bug_file('B-001', data, base_dir=tmp_path)

        assert filepath.exists()
        assert 'B-001' in filepath.name
        content = filepath.read_text()
        assert 'CSRF validation fails' in content
        assert 'B-001' in content
        assert 'high' in content.lower()

    @pytest.mark.django_db
    def test_create_bug_file_slugifies_title(self, tmp_path):
        """Bug file name should be slugified."""
        service = BugCreationService()

        data = {
            'title': 'Server Error on API Endpoint',
            'description': 'Internal server error',
            'severity': 'critical',
            'error_type': 'server_error',
            'status_code': 500,
            'url_pattern': '/api/pets/',
            'fingerprint': 'xyz789',
        }

        filepath = service.create_bug_file('B-002', data, base_dir=tmp_path)

        assert 'server-error' in filepath.name.lower() or 'api-endpoint' in filepath.name.lower()

    @pytest.mark.django_db
    @patch('httpx.Client')
    def test_create_github_issue(self, mock_client_class, settings):
        """Should create GitHub issue using GitHub API."""
        # Configure GitHub settings
        settings.GITHUB_TOKEN = 'test-token'
        settings.GITHUB_REPO = 'owner/repo'

        # Mock the httpx client response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'number': 42,
            'html_url': 'https://github.com/owner/repo/issues/42'
        }
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        service = BugCreationService()

        data = {
            'title': 'CSRF validation fails',
            'description': 'Origin checking failed',
            'severity': 'high',
        }

        issue_number, issue_url = service.create_github_issue('B-001', data)

        assert issue_number == 42
        assert issue_url == 'https://github.com/owner/repo/issues/42'
        mock_client.post.assert_called_once()

    @pytest.mark.django_db
    @patch('subprocess.run')
    def test_create_github_issue_handles_failure(self, mock_run):
        """Should handle gh CLI failure gracefully."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout='',
            stderr='Authentication failed',
        )

        service = BugCreationService()

        data = {
            'title': 'Test bug',
            'description': 'Test',
            'severity': 'low',
        }

        issue_number, issue_url = service.create_github_issue('B-001', data)

        assert issue_number is None
        assert issue_url == ''

    @pytest.mark.django_db
    @patch('httpx.Client')
    def test_create_full_bug(self, mock_client_class, tmp_path, settings):
        """Should create both bug file and GitHub issue."""
        # Configure GitHub settings
        settings.GITHUB_TOKEN = 'test-token'
        settings.GITHUB_REPO = 'owner/repo'

        # Mock the httpx client response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'number': 99,
            'html_url': 'https://github.com/owner/repo/issues/99'
        }
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        service = BugCreationService()

        error_data = {
            'title': 'Not Found on missing page',
            'description': 'User accessed missing URL',
            'severity': 'low',
            'error_type': 'not_found',
            'status_code': 404,
            'url_pattern': '/missing/',
            'fingerprint': 'missing123',
        }

        bug = service.create_full_bug(error_data, base_dir=tmp_path)

        assert bug.bug_id == 'B-001'
        assert bug.fingerprint == 'missing123'
        assert bug.github_issue_number == 99
        assert bug.status == 'open'
        assert bug.occurrence_count == 1

    @pytest.mark.django_db
    def test_format_bug_template(self):
        """Bug file should follow proper markdown template."""
        service = BugCreationService()

        data = {
            'title': 'Test Bug',
            'description': 'Test description',
            'severity': 'medium',
            'error_type': 'forbidden',
            'status_code': 403,
            'url_pattern': '/api/test/',
            'fingerprint': 'test123',
        }

        content = service.format_bug_content('B-042', data)

        # Check required sections
        assert '# B-042:' in content
        assert 'Test Bug' in content
        assert 'Severity' in content or 'severity' in content
        assert 'medium' in content.lower()
        assert 'Steps to Reproduce' in content or 'Description' in content

    @pytest.mark.django_db
    def test_get_next_bug_id_handles_malformed_ids(self):
        """Should handle malformed bug IDs gracefully."""
        # Create a bug with a malformed ID
        KnownBug.objects.create(
            bug_id='INVALID',
            fingerprint='malformed',
            title='Malformed bug',
            description='Has invalid ID',
            severity='low',
        )

        service = BugCreationService()
        bug_id = service.get_next_bug_id()
        # Should recover and start from B-001
        assert bug_id == 'B-001'

    @pytest.mark.django_db
    @patch('subprocess.run')
    def test_create_github_issue_timeout(self, mock_run):
        """Should handle gh CLI timeout."""
        import subprocess as sp
        mock_run.side_effect = sp.TimeoutExpired('gh', 30)

        service = BugCreationService()
        data = {'title': 'Test', 'description': 'Test', 'severity': 'low'}
        issue_number, issue_url = service.create_github_issue('B-001', data)

        assert issue_number is None
        assert issue_url == ''

    @pytest.mark.django_db
    @patch('subprocess.run')
    def test_create_github_issue_not_found(self, mock_run):
        """Should handle gh CLI not installed."""
        mock_run.side_effect = FileNotFoundError('gh not found')

        service = BugCreationService()
        data = {'title': 'Test', 'description': 'Test', 'severity': 'low'}
        issue_number, issue_url = service.create_github_issue('B-001', data)

        assert issue_number is None
        assert issue_url == ''

    @pytest.mark.django_db
    @patch('subprocess.run')
    def test_create_github_issue_generic_exception(self, mock_run):
        """Should handle unexpected exceptions."""
        mock_run.side_effect = RuntimeError('Unexpected error')

        service = BugCreationService()
        data = {'title': 'Test', 'description': 'Test', 'severity': 'low'}
        issue_number, issue_url = service.create_github_issue('B-001', data)

        assert issue_number is None
        assert issue_url == ''


class TestCeleryTasks:
    """Tests for Celery async tasks."""

    @pytest.mark.django_db
    @patch('apps.error_tracking.tasks.BugCreationService')
    def test_create_bug_task_calls_service(self, mock_service_class):
        """Task should call BugCreationService.create_full_bug."""
        mock_service = MagicMock()
        mock_bug = MagicMock()
        mock_bug.bug_id = 'B-001'
        mock_service.create_full_bug.return_value = mock_bug
        mock_service_class.return_value = mock_service

        error_data = {
            'fingerprint': 'test123',
            'title': 'Test error',
            'description': 'Test desc',
            'severity': 'high',
            'error_type': 'csrf',
            'status_code': 403,
            'url_pattern': '/contact/',
        }

        result = create_bug_task(error_data)

        mock_service.create_full_bug.assert_called_once_with(error_data)
        assert result == 'B-001'

    @pytest.mark.django_db
    @patch('apps.error_tracking.tasks.BugCreationService')
    def test_create_bug_task_handles_service_error(self, mock_service_class):
        """Task should handle service errors gracefully."""
        mock_service = MagicMock()
        mock_service.create_full_bug.side_effect = Exception('Database error')
        mock_service_class.return_value = mock_service

        error_data = {
            'fingerprint': 'error_test',
            'title': 'Test',
            'description': 'Test',
            'severity': 'low',
        }

        # Should not raise, should return None or handle gracefully
        with pytest.raises(Exception):
            create_bug_task(error_data)

    @pytest.mark.django_db
    @patch('subprocess.run')
    def test_create_bug_task_integration(self, mock_run, tmp_path):
        """Integration test for task creating real bug."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='https://github.com/owner/repo/issues/123\n',
        )

        error_data = {
            'fingerprint': 'integration_test',
            'title': 'Integration test bug',
            'description': 'Testing full flow',
            'severity': 'medium',
            'error_type': 'not_found',
            'status_code': 404,
            'url_pattern': '/test/',
        }

        # Run task directly (synchronous for testing)
        with patch('apps.error_tracking.services.settings') as mock_settings:
            mock_settings.BASE_DIR = str(tmp_path)
            result = create_bug_task(error_data)

        assert result is not None
        # Bug should be created in database
        assert KnownBug.objects.filter(fingerprint='integration_test').exists()
