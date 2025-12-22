"""Production settings for Pet-Friendly Vet project."""
import os
from .base import *

DEBUG = False

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

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# HTTPS settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

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
]
