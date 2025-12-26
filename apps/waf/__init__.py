"""WAF (Web Application Firewall) module for Django.

A standalone security module providing:
- Rate limiting with token bucket algorithm
- Pattern detection (SQL injection, XSS, path traversal)
- Security event logging (fail2ban compatible)
- IP ban list management
- Geo-blocking (optional, with GeoIP2)

Installation:
    Add 'apps.waf' to INSTALLED_APPS
    Add 'apps.waf.middleware.WAFMiddleware' to MIDDLEWARE

Configuration in settings.py:
    WAF_ENABLED = True
    WAF_RATE_LIMIT_REQUESTS = 200  # per minute
    WAF_RATE_LIMIT_WINDOW = 60  # seconds
    WAF_MAX_STRIKES = 5
    WAF_BAN_DURATION = 900  # 15 minutes
    WAF_LOG_PATH = '/var/log/django/security.log'
"""
default_app_config = 'apps.waf.apps.WafConfig'
