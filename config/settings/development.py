"""Development settings for Pet-Friendly Vet project."""
from .base import *

DEBUG = True

# Use ALLOWED_HOSTS from environment, with dev defaults
import os
ALLOWED_HOSTS = os.getenv(
    'DJANGO_ALLOWED_HOSTS',
    'localhost,127.0.0.1,0.0.0.0,dev.petfriendlyvet.com,dev.nestorwheelock.com,dev.linuxremotesupport.com'
).split(',')

# Debug toolbar (optional - only if installed)
try:
    import debug_toolbar  # noqa: F401
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = ['127.0.0.1', '172.17.0.1']  # Docker bridge
except ImportError:
    pass  # debug_toolbar not installed (e.g., in Docker with production deps)

# Use console email backend in development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable whitenoise compression in development
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Use SQLite for quick local development without Docker
# Override in .env if you want PostgreSQL
import os
if os.getenv('USE_SQLITE', 'False').lower() == 'true':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Simpler cache for development
if os.getenv('USE_LOCMEM_CACHE', 'False').lower() == 'true':
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True
