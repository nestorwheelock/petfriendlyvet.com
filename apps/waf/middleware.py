"""WAF Middleware - Web Application Firewall for Django.

This middleware provides:
- Rate limiting with token bucket algorithm
- Attack pattern detection (SQL injection, XSS, path traversal)
- Data leak prevention (SSN, credit card numbers)
- IP banning with auto-ban on repeated violations
- Geo-blocking (when enabled)
- Security event logging for fail2ban integration
"""
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponseForbidden, HttpResponse
from django.utils import timezone

from .rate_limiter import TokenBucketRateLimiter
from .pattern_detector import scan_request, scan_response
from .security_logger import (
    log_rate_limit,
    log_pattern_detected,
    log_ip_banned,
    log_banned_access,
    log_security_event,
)


def get_client_ip(request) -> str:
    """Extract client IP from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


def is_path_excluded(path: str) -> bool:
    """Check if path is excluded from WAF processing."""
    excluded = getattr(settings, 'WAF_EXCLUDED_PATHS', [
        '/static/',
        '/media/',
        '/__reload__/',
        '/favicon.ico',
    ])
    for excluded_path in excluded:
        if path.startswith(excluded_path):
            return True
    return False


class WAFMiddleware:
    """Web Application Firewall middleware.

    Configuration via Django settings:
        WAF_ENABLED = True
        WAF_RATE_LIMIT_REQUESTS = 200
        WAF_RATE_LIMIT_WINDOW = 60
        WAF_MAX_STRIKES = 5
        WAF_BAN_DURATION = 900
        WAF_PATTERN_DETECTION = True
        WAF_DATA_LEAK_DETECTION = True
        WAF_EXCLUDED_PATHS = ['/static/', '/media/']
    """

    def __init__(self, get_response):
        self.get_response = get_response

        # Configuration from settings
        self.enabled = getattr(settings, 'WAF_ENABLED', True)
        self.rate_limit_requests = getattr(settings, 'WAF_RATE_LIMIT_REQUESTS', 200)
        self.rate_limit_window = getattr(settings, 'WAF_RATE_LIMIT_WINDOW', 60)
        self.max_strikes = getattr(settings, 'WAF_MAX_STRIKES', 5)
        self.ban_duration = getattr(settings, 'WAF_BAN_DURATION', 900)
        self.pattern_detection = getattr(settings, 'WAF_PATTERN_DETECTION', True)
        self.data_leak_detection = getattr(settings, 'WAF_DATA_LEAK_DETECTION', True)

        # Initialize rate limiter
        self.rate_limiter = TokenBucketRateLimiter(
            max_requests=self.rate_limit_requests,
            window_seconds=self.rate_limit_window,
        )

    def __call__(self, request):
        # Skip if disabled
        if not self.enabled:
            return self.get_response(request)

        # Skip excluded paths
        if is_path_excluded(request.path):
            return self.get_response(request)

        ip = get_client_ip(request)

        # Check if IP is banned
        if self._is_ip_banned(ip):
            log_banned_access(ip, request.path)
            return HttpResponseForbidden("Access denied.")

        # Rate limiting
        allowed, remaining = self.rate_limiter.is_allowed(ip)
        if not allowed:
            self._record_strike(ip, 'rate_limit', request.path)
            log_rate_limit(ip, self.rate_limit_requests, request.path)
            return HttpResponse("Too many requests.", status=429)

        # Pattern detection
        if self.pattern_detection:
            result = scan_request(request)
            if result.detected:
                self._record_strike(ip, result.pattern_type, request.path)
                log_pattern_detected(ip, result.pattern_type, request.path, result.matched_pattern)
                return HttpResponseForbidden("Request blocked.")

        # Get response
        response = self.get_response(request)

        # Data leak detection on responses
        if self.data_leak_detection and self._should_scan_response(response):
            content = self._get_response_content(response)
            if content:
                result = scan_response(content)
                if result.detected:
                    # Log data leak attempt and block response
                    log_security_event(
                        'DATA_LEAK_BLOCKED',
                        ip,
                        pattern=result.pattern_type,
                        path=request.path,
                        matched=result.matched_pattern,
                    )
                    # Return a generic error instead of the leaky response
                    return HttpResponse(
                        "An error occurred processing your request.",
                        status=500,
                        content_type='text/plain',
                    )

        # Add rate limit headers
        response['X-RateLimit-Remaining'] = str(remaining)
        response['X-RateLimit-Limit'] = str(self.rate_limit_requests)

        return response

    def _is_ip_banned(self, ip: str) -> bool:
        """Check if IP is currently banned."""
        # Check cache first
        cache_key = f'waf:banned:{ip}'
        if cache.get(cache_key):
            return True

        # Check database
        try:
            from .models import BannedIP
            ban = BannedIP.objects.filter(ip_address=ip).first()
            if ban and ban.is_active:
                # Cache the ban status
                cache.set(cache_key, True, self.ban_duration)
                return True
        except Exception:
            pass

        return False

    def _record_strike(self, ip: str, event_type: str, path: str):
        """Record a strike against an IP."""
        cache_key = f'waf:strikes:{ip}'
        strikes = cache.get(cache_key, 0) + 1
        cache.set(cache_key, strikes, self.ban_duration)

        # Auto-ban if strikes exceed threshold
        if strikes >= self.max_strikes:
            self._ban_ip(ip, f'Auto-banned after {strikes} strikes ({event_type})')

        # Save to database
        try:
            from .models import SecurityEvent
            SecurityEvent.objects.create(
                event_type=event_type,
                ip_address=ip,
                path=path,
                method=getattr(self, '_current_request', {}).get('method', 'GET'),
                action_taken='logged' if strikes < self.max_strikes else 'banned',
            )
        except Exception:
            pass

    def _ban_ip(self, ip: str, reason: str):
        """Ban an IP address."""
        # Cache the ban
        cache_key = f'waf:banned:{ip}'
        cache.set(cache_key, True, self.ban_duration)

        # Log the ban
        log_ip_banned(ip, reason, self.ban_duration)

        # Save to database
        try:
            from .models import BannedIP
            BannedIP.objects.update_or_create(
                ip_address=ip,
                defaults={
                    'reason': reason,
                    'auto_banned': True,
                    'expires_at': timezone.now() + timezone.timedelta(seconds=self.ban_duration),
                }
            )
        except Exception:
            pass

    def _should_scan_response(self, response) -> bool:
        """Determine if response should be scanned for data leaks."""
        # Only scan successful responses
        if response.status_code >= 400:
            return False

        # Only scan text content
        content_type = response.get('Content-Type', '')
        scannable_types = ('text/html', 'text/plain', 'application/json', 'text/xml')
        return any(t in content_type for t in scannable_types)

    def _get_response_content(self, response) -> str | None:
        """Extract text content from response."""
        try:
            # Handle streaming responses
            if hasattr(response, 'streaming_content'):
                return None  # Don't scan streaming responses

            content = response.content
            if isinstance(content, bytes):
                content = content.decode('utf-8', errors='ignore')

            # Don't scan very large responses
            if len(content) > 1_000_000:  # 1MB limit
                return None

            return content
        except Exception:
            return None
