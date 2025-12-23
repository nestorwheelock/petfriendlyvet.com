"""Local test settings with file-based SQLite for manual testing."""
from .test import *

# Use file-based SQLite instead of in-memory
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'local_test.db',
    }
}

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
