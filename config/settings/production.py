"""Production settings for Pet-Friendly Vet project."""
import os
from .base import *

DEBUG = False

# Dynamic URL middleware for admin/staff security (insert after WAF)
# WAF is already in base.py, add DynamicURLMiddleware after it
MIDDLEWARE.insert(2, 'apps.core.middleware.dynamic_urls.DynamicURLMiddleware')

# WAF settings for production
WAF_ENABLED = True
WAF_RATE_LIMIT = 100  # requests per minute
WAF_RATE_LIMIT_WINDOW = 60  # seconds
WAF_BAN_THRESHOLD = 5  # strikes before ban
WAF_BAN_DURATION = 3600  # 1 hour ban
WAF_DATA_LEAK_DETECTION = True
WAF_GEO_BLOCKING_ENABLED = False  # Enable via superadmin when needed

# Subdirectory deployment support (e.g., petfriendlyvet.com/dev)
# Set SCRIPT_NAME environment variable to deploy under a URL prefix
SCRIPT_NAME = os.getenv('SCRIPT_NAME', '')
if SCRIPT_NAME:
    FORCE_SCRIPT_NAME = SCRIPT_NAME
    # Prefix static and media URLs for subdirectory deployment
    STATIC_URL = f'{SCRIPT_NAME}/static/'
    MEDIA_URL = f'{SCRIPT_NAME}/media/'
    # Update login redirect URLs
    LOGIN_REDIRECT_URL = f'{SCRIPT_NAME}/'
    LOGOUT_REDIRECT_URL = f'{SCRIPT_NAME}/'

# Proxy settings - nginx terminates SSL
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# HTTPS settings (can be disabled for local Docker testing)
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'True').lower() == 'true'
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'True').lower() == 'true'
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'True').lower() == 'true'

# Static files with whitenoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Email via Amazon SES
EMAIL_BACKEND = 'django_ses.SESBackend'
AWS_SES_REGION_NAME = os.getenv('AWS_SES_REGION', 'us-east-1')
AWS_SES_REGION_ENDPOINT = f'email.{AWS_SES_REGION_NAME}.amazonaws.com'

# CORS settings for production
CORS_ALLOWED_ORIGINS = [
    'https://petfriendlyvet.com',
    'https://www.petfriendlyvet.com',
    'https://dev.petfriendlyvet.com',
]

# CSRF trusted origins for cross-origin requests
# NOTE: dev.petfriendlyvet.com intentionally excluded to test custom 403 page (B-001)
CSRF_TRUSTED_ORIGINS = [
    'https://petfriendlyvet.com',
    'https://www.petfriendlyvet.com',
]

# Custom CSRF failure view (friendly error page)
CSRF_FAILURE_VIEW = 'apps.core.views.csrf_failure'


# Content Security Policy - Enforce in production (django-csp 4.0+)
# Copy base directives to enforced policy (not report-only)
CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": ["'self'"],
        "script-src": [
            "'self'",
            "'unsafe-inline'",
            "'unsafe-eval'",  # Required for Alpine.js expression evaluation
            "unpkg.com",
            "cdn.jsdelivr.net",
        ],
        "style-src": [
            "'self'",
            "'unsafe-inline'",
            "fonts.googleapis.com",
            "cdn.jsdelivr.net",
        ],
        "font-src": [
            "'self'",
            "fonts.gstatic.com",
            "cdn.jsdelivr.net",
        ],
        "img-src": [
            "'self'",
            "data:",
            "https:",
            "blob:",
        ],
        "connect-src": [
            "'self'",
            "https://openrouter.ai",
        ],
        "frame-ancestors": ["'none'"],
        "form-action": ["'self'"],
        "base-uri": ["'self'"],
    }
}
# Clear report-only in production (enforce the policy)
CONTENT_SECURITY_POLICY_REPORT_ONLY = None
