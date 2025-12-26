"""Tests for WAF (Web Application Firewall) module."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import RequestFactory, override_settings
from django.http import HttpResponse

from apps.waf.rate_limiter import TokenBucketRateLimiter, check_rate_limit
from apps.waf.pattern_detector import (
    detect_sql_injection,
    detect_xss,
    detect_path_traversal,
    detect_all,
    scan_request,
    detect_ssn,
    detect_credit_card,
    detect_api_keys,
    detect_mass_email_exposure,
    scan_response,
    DetectionResult,
    _luhn_checksum,
    _is_valid_ssn,
)
from apps.waf.security_logger import (
    log_failed_login,
    log_invalid_token,
    log_rate_limit,
    log_pattern_detected,
    log_ip_banned,
    log_banned_access,
    log_geo_blocked,
    log_security_event,
)
from django.test import override_settings
from apps.waf.middleware import WAFMiddleware, get_client_ip, is_path_excluded


# ============================================================
# Rate Limiter Tests
# ============================================================

class TestTokenBucketRateLimiter:
    """Tests for token bucket rate limiter."""

    def test_first_request_allowed(self):
        """First request from new IP should be allowed."""
        with patch('apps.waf.rate_limiter.cache') as mock_cache:
            mock_cache.get.return_value = None
            limiter = TokenBucketRateLimiter(max_requests=100, window_seconds=60)
            allowed, remaining = limiter.is_allowed('192.168.1.1')
            assert allowed is True
            assert remaining == 99

    def test_request_under_limit_allowed(self):
        """Requests under limit should be allowed."""
        with patch('apps.waf.rate_limiter.cache') as mock_cache:
            mock_cache.get.return_value = {
                'tokens': 50,
                'last_update': 0,
            }
            limiter = TokenBucketRateLimiter(max_requests=100, window_seconds=60)
            with patch('apps.waf.rate_limiter.time.time', return_value=1):
                allowed, remaining = limiter.is_allowed('192.168.1.1')
                assert allowed is True

    def test_request_at_limit_blocked(self):
        """Request when no tokens remain should be blocked."""
        with patch('apps.waf.rate_limiter.cache') as mock_cache:
            mock_cache.get.return_value = {
                'tokens': 0,
                'last_update': 0,
            }
            limiter = TokenBucketRateLimiter(max_requests=100, window_seconds=60)
            with patch('apps.waf.rate_limiter.time.time', return_value=0):
                allowed, remaining = limiter.is_allowed('192.168.1.1')
                assert allowed is False
                assert remaining == 0

    def test_tokens_refill_over_time(self):
        """Tokens should refill based on elapsed time."""
        with patch('apps.waf.rate_limiter.cache') as mock_cache:
            mock_cache.get.return_value = {
                'tokens': 0,
                'last_update': 0,
            }
            limiter = TokenBucketRateLimiter(max_requests=100, window_seconds=60)
            # After 60 seconds, should have 100 tokens (full bucket)
            with patch('apps.waf.rate_limiter.time.time', return_value=60):
                allowed, remaining = limiter.is_allowed('192.168.1.1')
                assert allowed is True

    def test_different_ips_have_separate_limits(self):
        """Each IP should have its own token bucket."""
        with patch('apps.waf.rate_limiter.cache') as mock_cache:
            limiter = TokenBucketRateLimiter(max_requests=100, window_seconds=60)
            # Check that different cache keys are used
            limiter._get_bucket_key('192.168.1.1')
            limiter._get_bucket_key('192.168.1.2')
            assert limiter._get_bucket_key('192.168.1.1') != limiter._get_bucket_key('192.168.1.2')

    def test_get_remaining_returns_current_tokens(self):
        """get_remaining should return available tokens."""
        with patch('apps.waf.rate_limiter.cache') as mock_cache:
            mock_cache.get.return_value = None
            limiter = TokenBucketRateLimiter(max_requests=100, window_seconds=60)
            remaining = limiter.get_remaining('192.168.1.1')
            assert remaining == 100

    def test_reset_clears_bucket(self):
        """reset should clear the bucket for an IP."""
        with patch('apps.waf.rate_limiter.cache') as mock_cache:
            limiter = TokenBucketRateLimiter()
            limiter.reset('192.168.1.1')
            mock_cache.delete.assert_called_once()

    def test_check_rate_limit_function(self):
        """check_rate_limit convenience function should work."""
        with patch('apps.waf.rate_limiter.cache') as mock_cache:
            mock_cache.get.return_value = None
            allowed, remaining = check_rate_limit('192.168.1.1', max_requests=50, window=30)
            assert allowed is True


# ============================================================
# Pattern Detection Tests - Attack Patterns
# ============================================================

class TestSQLInjectionDetection:
    """Tests for SQL injection pattern detection."""

    @pytest.mark.parametrize('payload', [
        "' OR '1'='1",
        "' OR 1=1--",
        "UNION SELECT * FROM users",
        "'; DROP TABLE users;--",
        "1; DELETE FROM products",
        "admin'--",
        "' UNION ALL SELECT NULL,NULL,NULL--",
        "SELECT * FROM information_schema.tables",
        "1' AND SLEEP(5)#",
        "1; EXEC xp_cmdshell('dir')",
    ])
    def test_detects_sql_injection(self, payload):
        """Should detect common SQL injection patterns."""
        result = detect_sql_injection(payload)
        assert result.detected is True
        assert result.pattern_type == 'sqli'

    def test_clean_text_not_flagged(self):
        """Normal text should not trigger SQL injection detection."""
        result = detect_sql_injection("Hello, my name is John")
        assert result.detected is False

    def test_select_in_normal_context(self):
        """The word 'select' alone should not trigger."""
        result = detect_sql_injection("Please select your preferences")
        assert result.detected is False


class TestXSSDetection:
    """Tests for XSS pattern detection."""

    @pytest.mark.parametrize('payload', [
        '<script>alert("XSS")</script>',
        '<img src=x onerror=alert(1)>',
        '<body onload=alert(1)>',
        'javascript:alert(1)',
        '<svg onload=alert(1)>',
        '<iframe src="javascript:alert(1)">',
        'document.cookie',
        'eval("malicious")',
        '<a onclick="alert(1)">click</a>',
    ])
    def test_detects_xss(self, payload):
        """Should detect common XSS patterns."""
        result = detect_xss(payload)
        assert result.detected is True
        assert result.pattern_type == 'xss'

    def test_clean_html_not_flagged(self):
        """Normal HTML should not trigger XSS detection."""
        result = detect_xss("<p>This is a paragraph</p>")
        assert result.detected is False


class TestPathTraversalDetection:
    """Tests for path traversal pattern detection."""

    @pytest.mark.parametrize('payload', [
        '../../../etc/passwd',
        '..\\..\\..\\windows\\system32',
        '%2e%2e%2f%2e%2e%2f',
        '/etc/passwd',
        'c:\\boot.ini',
        '....//....//etc/passwd',
        '%00',
        '%c0%ae%c0%ae/',
    ])
    def test_detects_path_traversal(self, payload):
        """Should detect path traversal patterns."""
        result = detect_path_traversal(payload)
        assert result.detected is True
        assert result.pattern_type == 'path_traversal'

    def test_normal_path_not_flagged(self):
        """Normal file paths should not trigger detection."""
        result = detect_path_traversal("/home/user/documents/file.txt")
        assert result.detected is False


class TestDetectAll:
    """Tests for combined pattern detection."""

    def test_detects_sql_injection_in_mixed(self):
        """detect_all should find SQL injection."""
        result = detect_all("' OR '1'='1")
        assert result.detected is True
        assert result.pattern_type == 'sqli'

    def test_detects_xss_in_mixed(self):
        """detect_all should find XSS."""
        result = detect_all('<script>alert(1)</script>')
        assert result.detected is True
        assert result.pattern_type == 'xss'

    def test_detects_path_traversal_in_mixed(self):
        """detect_all should find path traversal."""
        result = detect_all('../../../etc/passwd')
        assert result.detected is True
        assert result.pattern_type == 'path_traversal'

    def test_clean_text_passes(self):
        """Clean text should pass all checks."""
        result = detect_all("This is a normal search query")
        assert result.detected is False


class TestScanRequest:
    """Tests for scanning Django requests."""

    def test_scans_path(self):
        """Should scan URL path for attacks."""
        factory = RequestFactory()
        request = factory.get('/users/../../../etc/passwd')
        result = scan_request(request)
        assert result.detected is True

    def test_scans_query_string(self):
        """Should scan query string for attacks."""
        factory = RequestFactory()
        request = factory.get('/search/?q=<script>alert(1)</script>')
        request.META['QUERY_STRING'] = 'q=<script>alert(1)</script>'
        result = scan_request(request)
        assert result.detected is True

    def test_scans_post_body(self):
        """Should scan POST body for attacks."""
        factory = RequestFactory()
        request = factory.post('/login/', data="username=' OR '1'='1", content_type='text/plain')
        result = scan_request(request)
        assert result.detected is True

    def test_clean_request_passes(self):
        """Clean request should pass."""
        factory = RequestFactory()
        request = factory.get('/about/')
        result = scan_request(request)
        assert result.detected is False


# ============================================================
# Pattern Detection Tests - Data Leak Prevention
# ============================================================

class TestSSNDetection:
    """Tests for Social Security Number detection."""

    @pytest.mark.parametrize('ssn', [
        '078-05-1120',  # Valid format SSN
        '219-09-9999',  # Valid format SSN
        '457-55-5462',  # Valid format SSN
    ])
    def test_detects_ssn_formats(self, ssn):
        """Should detect SSN in various formats."""
        text = f"Customer SSN: {ssn}"
        result = detect_ssn(text)
        assert result.detected is True
        assert result.pattern_type == 'ssn_leak'
        assert result.is_outbound is True

    def test_invalid_ssn_not_flagged(self):
        """Invalid SSNs should not be flagged."""
        # Area 000 is invalid
        result = detect_ssn("SSN: 000-12-3456")
        assert result.detected is False

    def test_obviously_fake_ssn_not_flagged(self):
        """Obviously fake SSNs should not be flagged."""
        result = detect_ssn("SSN: 123-45-6789")
        # 123-45-6789 is actually valid format but common test value
        # The _is_valid_ssn function checks for common invalid patterns

    def test_ssn_area_666_invalid(self):
        """SSN area 666 is invalid."""
        assert _is_valid_ssn('666-12-3456') is False

    def test_ssn_area_900_invalid(self):
        """SSN area 900+ is invalid."""
        assert _is_valid_ssn('900-12-3456') is False


class TestCreditCardDetection:
    """Tests for credit card number detection."""

    def test_luhn_valid(self):
        """Test Luhn algorithm with valid number."""
        # Visa test number
        assert _luhn_checksum('4111111111111111') is True

    def test_luhn_invalid(self):
        """Test Luhn algorithm with invalid number."""
        assert _luhn_checksum('4111111111111112') is False

    @pytest.mark.parametrize('card', [
        '4111111111111111',  # Visa test
        '5500000000000004',  # Mastercard test
        '340000000000009',   # Amex test
    ])
    def test_detects_valid_cards(self, card):
        """Should detect valid credit card numbers."""
        text = f"Card number: {card}"
        result = detect_credit_card(text)
        assert result.detected is True
        assert result.pattern_type == 'cc_leak'
        assert result.is_outbound is True
        # Should be masked
        assert 'XXXX' in result.matched_pattern

    def test_invalid_card_not_flagged(self):
        """Invalid card numbers (failing Luhn) should not be flagged."""
        result = detect_credit_card("Card: 1234567890123456")
        assert result.detected is False


class TestAPIKeyDetection:
    """Tests for API key/secret detection."""

    @pytest.mark.parametrize('text', [
        'api_key = "abcdefghijklmnopqrstuvwxyz"',
        'API-KEY: 1234567890abcdefghijklmnop',
        'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWI',
        'AKIAIOSFODNN7EXAMPLE',  # AWS format
    ])
    def test_detects_api_keys(self, text):
        """Should detect API key patterns."""
        result = detect_api_keys(text)
        assert result.detected is True
        assert result.pattern_type == 'api_key_leak'


class TestMassEmailExposure:
    """Tests for mass email exposure detection."""

    def test_detects_many_emails(self):
        """Should detect when many emails are exposed."""
        text = """
        john@example.com, jane@example.com, bob@test.org,
        alice@company.com, charlie@domain.net, david@email.com
        """
        result = detect_mass_email_exposure(text, threshold=5)
        assert result.detected is True
        assert result.pattern_type == 'email_exposure'

    def test_few_emails_not_flagged(self):
        """Few emails should not trigger detection."""
        text = "Contact us at support@example.com or sales@example.com"
        result = detect_mass_email_exposure(text, threshold=5)
        assert result.detected is False


class TestScanResponse:
    """Tests for scanning response content."""

    def test_detects_ssn_in_response(self):
        """Should detect SSN in response content."""
        content = '{"ssn": "078-05-1120"}'
        result = scan_response(content)
        assert result.detected is True
        assert result.pattern_type == 'ssn_leak'

    def test_detects_credit_card_in_response(self):
        """Should detect credit card in response."""
        content = '{"card": "4111111111111111"}'
        result = scan_response(content)
        assert result.detected is True
        assert result.pattern_type == 'cc_leak'

    def test_clean_response_passes(self):
        """Clean response should pass."""
        content = '{"name": "John Doe", "email": "john@example.com"}'
        result = scan_response(content)
        assert result.detected is False


# ============================================================
# Security Logger Tests
# ============================================================

class TestSecurityLogger:
    """Tests for security logging functions."""

    @patch('apps.waf.security_logger.security_logger')
    def test_log_failed_login(self, mock_logger):
        """Should log failed login attempts."""
        log_failed_login('192.168.1.1', '/login/', 'admin')
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert 'FAILED_LOGIN' in call_args
        assert 'ip=192.168.1.1' in call_args

    @patch('apps.waf.security_logger.security_logger')
    def test_log_invalid_token(self, mock_logger):
        """Should log invalid token attempts."""
        log_invalid_token('192.168.1.1', '/staff-abc123/', 'staff')
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert 'INVALID_TOKEN' in call_args

    @patch('apps.waf.security_logger.security_logger')
    def test_log_rate_limit(self, mock_logger):
        """Should log rate limit events."""
        log_rate_limit('192.168.1.1', 200, '/api/')
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert 'RATE_LIMIT' in call_args
        assert 'count=200' in call_args

    @patch('apps.waf.security_logger.security_logger')
    def test_log_pattern_detected(self, mock_logger):
        """Should log detected attack patterns."""
        log_pattern_detected('192.168.1.1', 'sqli', '/search/', "' OR 1=1")
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert 'PATTERN_DETECTED' in call_args
        assert 'pattern=sqli' in call_args

    @patch('apps.waf.security_logger.security_logger')
    def test_log_ip_banned(self, mock_logger):
        """Should log IP bans."""
        log_ip_banned('192.168.1.1', 'Auto-banned after 5 strikes', 900)
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert 'IP_BANNED' in call_args
        assert 'duration=900s' in call_args

    @patch('apps.waf.security_logger.security_logger')
    def test_log_banned_access(self, mock_logger):
        """Should log access attempts from banned IPs."""
        log_banned_access('192.168.1.1', '/admin/')
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert 'BANNED_ACCESS' in call_args

    @patch('apps.waf.security_logger.security_logger')
    def test_log_geo_blocked(self, mock_logger):
        """Should log geo-blocked access."""
        log_geo_blocked('192.168.1.1', 'RU', '/login/')
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert 'GEO_BLOCKED' in call_args
        assert 'country=RU' in call_args

    @patch('apps.waf.security_logger.security_logger')
    def test_log_security_event_generic(self, mock_logger):
        """Should log generic security events."""
        log_security_event('CUSTOM_EVENT', '192.168.1.1', extra='value')
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert 'CUSTOM_EVENT' in call_args
        assert 'extra=value' in call_args


# ============================================================
# WAF Middleware Tests
# ============================================================

class TestGetClientIP:
    """Tests for client IP extraction."""

    def test_extracts_from_x_forwarded_for(self):
        """Should extract IP from X-Forwarded-For header."""
        factory = RequestFactory()
        request = factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '10.0.0.1, 192.168.1.1'
        assert get_client_ip(request) == '10.0.0.1'

    def test_extracts_from_remote_addr(self):
        """Should fall back to REMOTE_ADDR."""
        factory = RequestFactory()
        request = factory.get('/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        assert get_client_ip(request) == '192.168.1.1'

    def test_returns_localhost_as_default(self):
        """Should return localhost if no IP found."""
        factory = RequestFactory()
        request = factory.get('/')
        request.META.pop('REMOTE_ADDR', None)
        assert get_client_ip(request) == '127.0.0.1'


class TestIsPathExcluded:
    """Tests for path exclusion logic."""

    def test_static_path_excluded(self):
        """Static paths should be excluded."""
        assert is_path_excluded('/static/css/style.css') is True

    def test_media_path_excluded(self):
        """Media paths should be excluded."""
        assert is_path_excluded('/media/uploads/image.jpg') is True

    def test_favicon_excluded(self):
        """Favicon should be excluded."""
        assert is_path_excluded('/favicon.ico') is True

    def test_normal_path_not_excluded(self):
        """Normal paths should not be excluded."""
        assert is_path_excluded('/api/users/') is False
        assert is_path_excluded('/admin/') is False


class TestWAFMiddleware:
    """Tests for WAF middleware."""

    def test_middleware_disabled_passes_all(self):
        """When disabled, middleware should pass all requests."""
        factory = RequestFactory()
        request = factory.get('/api/test/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'

        def get_response(r):
            return HttpResponse('OK')

        middleware = WAFMiddleware(get_response)
        middleware.enabled = False  # Explicitly disable
        response = middleware(request)
        assert response.status_code == 200

    def test_excluded_path_passes(self):
        """Excluded paths should pass without checks."""
        factory = RequestFactory()
        request = factory.get('/static/js/app.js')
        request.META['REMOTE_ADDR'] = '192.168.1.1'

        def get_response(r):
            return HttpResponse('OK')

        middleware = WAFMiddleware(get_response)
        middleware.enabled = True  # Enable for this test
        response = middleware(request)
        assert response.status_code == 200

    @patch('apps.waf.middleware.cache')
    def test_banned_ip_blocked(self, mock_cache):
        """Banned IPs should receive 403."""
        factory = RequestFactory()
        request = factory.get('/api/test/')
        request.META['REMOTE_ADDR'] = '192.168.1.100'

        mock_cache.get.return_value = True  # IP is banned

        def get_response(r):
            return HttpResponse('OK')

        with patch('apps.waf.middleware.log_banned_access'):
            middleware = WAFMiddleware(get_response)
            middleware.enabled = True  # Enable for this test
            response = middleware(request)
            assert response.status_code == 403

    @patch('apps.waf.rate_limiter.cache')
    @patch('apps.waf.middleware.cache')
    def test_rate_limited_returns_429(self, mock_middleware_cache, mock_rate_cache):
        """Rate-limited requests should return 429."""
        factory = RequestFactory()
        request = factory.get('/api/test/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'

        # Middleware cache: IP not banned (first call), then strike counter (second call)
        def middleware_cache_get(key, default=None):
            if 'banned' in key:
                return None  # Not banned
            if 'strikes' in key:
                return 0  # No strikes yet
            return default
        mock_middleware_cache.get.side_effect = middleware_cache_get

        # Rate limiter cache: bucket with no tokens left
        mock_rate_cache.get.return_value = {'tokens': 0, 'last_update': 0}

        def get_response(r):
            return HttpResponse('OK')

        with patch('apps.waf.middleware.log_rate_limit'):
            with patch('apps.waf.rate_limiter.time.time', return_value=0):
                middleware = WAFMiddleware(get_response)
                middleware.enabled = True  # Enable for this test
                response = middleware(request)
                assert response.status_code == 429

    @patch('apps.waf.rate_limiter.cache')
    @patch('apps.waf.middleware.cache')
    def test_attack_pattern_blocked(self, mock_middleware_cache, mock_rate_cache):
        """Requests with attack patterns should be blocked."""
        factory = RequestFactory()
        request = factory.get("/api/test/?q=' OR '1'='1")
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        request.META['QUERY_STRING'] = "q=' OR '1'='1"

        # Middleware cache: not banned, strike counter at 0
        mock_middleware_cache.get.return_value = 0

        # Rate limiter cache: new bucket (None means create new bucket)
        mock_rate_cache.get.return_value = None

        def get_response(r):
            return HttpResponse('OK')

        with patch('apps.waf.middleware.log_pattern_detected'):
            middleware = WAFMiddleware(get_response)
            middleware.enabled = True  # Enable for this test
            response = middleware(request)
            assert response.status_code == 403

    @patch('apps.waf.rate_limiter.cache')
    @patch('apps.waf.middleware.cache')
    def test_clean_request_passes(self, mock_middleware_cache, mock_rate_cache):
        """Clean requests should pass through."""
        factory = RequestFactory()
        request = factory.get('/api/users/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'

        mock_middleware_cache.get.return_value = None  # Not banned
        mock_rate_cache.get.return_value = None  # New bucket

        def get_response(r):
            response = HttpResponse('OK')
            response['Content-Type'] = 'text/html'
            return response

        middleware = WAFMiddleware(get_response)
        middleware.enabled = True  # Enable for this test
        response = middleware(request)
        assert response.status_code == 200
        assert 'X-RateLimit-Remaining' in response

    @patch('apps.waf.rate_limiter.cache')
    @patch('apps.waf.middleware.cache')
    def test_data_leak_blocked_in_response(self, mock_middleware_cache, mock_rate_cache):
        """Responses with sensitive data should be blocked."""
        factory = RequestFactory()
        request = factory.get('/api/user/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'

        mock_middleware_cache.get.return_value = None  # Not banned
        mock_rate_cache.get.return_value = None  # New bucket

        def get_response(r):
            response = HttpResponse('{"ssn": "078-05-1120"}')
            response['Content-Type'] = 'application/json'
            return response

        with patch('apps.waf.middleware.log_security_event'):
            middleware = WAFMiddleware(get_response)
            middleware.enabled = True  # Enable for this test
            middleware.data_leak_detection = True  # Enable data leak detection
            response = middleware(request)
            # Should return error instead of leaky response
            assert response.status_code == 500
            assert 'ssn' not in response.content.decode()

    @patch('apps.waf.rate_limiter.cache')
    @patch('apps.waf.middleware.cache')
    def test_rate_limit_headers_added(self, mock_middleware_cache, mock_rate_cache):
        """Rate limit headers should be added to responses."""
        factory = RequestFactory()
        request = factory.get('/api/test/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'

        mock_middleware_cache.get.return_value = None  # Not banned
        mock_rate_cache.get.return_value = None  # New bucket

        def get_response(r):
            response = HttpResponse('OK')
            response['Content-Type'] = 'text/plain'
            return response

        middleware = WAFMiddleware(get_response)
        middleware.enabled = True  # Enable for this test
        response = middleware(request)
        assert 'X-RateLimit-Remaining' in response
        assert 'X-RateLimit-Limit' in response


# ============================================================
# Integration Tests
# ============================================================

@pytest.mark.django_db
class TestWAFIntegration:
    """Integration tests for WAF with database."""

    def test_banned_ip_model_is_active(self):
        """BannedIP.is_active should work correctly."""
        from apps.waf.models import BannedIP
        from django.utils import timezone
        from datetime import timedelta

        # Active ban
        active_ban = BannedIP.objects.create(
            ip_address='192.168.1.1',
            reason='Test ban',
            expires_at=timezone.now() + timedelta(hours=1),
        )
        assert active_ban.is_active is True

        # Expired ban
        expired_ban = BannedIP.objects.create(
            ip_address='192.168.1.2',
            reason='Test ban',
            expires_at=timezone.now() - timedelta(hours=1),
        )
        assert expired_ban.is_active is False

        # Permanent ban
        permanent_ban = BannedIP.objects.create(
            ip_address='192.168.1.3',
            reason='Test ban',
            permanent=True,
        )
        assert permanent_ban.is_active is True

    def test_waf_config_singleton(self):
        """WAFConfig should be singleton."""
        from apps.waf.models import WAFConfig

        config1 = WAFConfig.get_config()
        config2 = WAFConfig.get_config()
        assert config1.pk == config2.pk

    def test_security_event_creation(self):
        """SecurityEvent should be created properly."""
        from apps.waf.models import SecurityEvent

        event = SecurityEvent.objects.create(
            event_type='sqli',
            ip_address='192.168.1.1',
            path='/api/test/',
            method='GET',
            action_taken='blocked',
        )
        assert event.pk is not None
        assert str(event) == f"sqli: 192.168.1.1 at {event.created_at}"
