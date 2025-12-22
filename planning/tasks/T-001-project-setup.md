# T-001: Django Project Setup

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Set up Django project with proper structure, modular architecture, and all dependencies
**Related Story**: S-001 (Foundation + AI Core)

### Constraints
**Allowed File Paths**: Root project directory, config/, apps/, requirements/
**Forbidden Paths**: None

### Standards Compliance
- [ ] Follow TDD (tests first)
- [ ] Follow ADR-001 (monorepo with extractable packages)
- [ ] No cross-package imports
- [ ] Services for public APIs

## Context
This is the foundational task for the Pet-Friendly veterinary clinic website. The project uses a modular architecture designed for 9 pip-installable packages, with Django 5.x, PostgreSQL, and a modern frontend stack (HTMX + Alpine.js + Tailwind CSS).

## Deliverables
- [ ] Django project created with proper settings structure
- [ ] Apps structure created for all 9 modules
- [ ] requirements/ directory with split dependency files
- [ ] .env.example with all required environment variables
- [ ] .gitignore properly configured for Django/Python/Node
- [ ] PostgreSQL database configuration (development + test)
- [ ] Django i18n configured for ES/EN (primary/secondary)
- [ ] Tailwind CSS integrated with custom brand colors
- [ ] HTMX and Alpine.js included via CDN
- [ ] Celery configuration for background tasks
- [ ] Redis configuration for caching and Celery broker

## Implementation Details

### Project Structure
```
petfriendlyvet/
├── config/                     # Project configuration
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py            # Shared settings
│   │   ├── development.py     # Dev-specific
│   │   ├── production.py      # Production-specific
│   │   └── test.py            # Test configuration
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/                       # Django applications
│   ├── __init__.py
│   ├── core/                  # Core utilities, base models
│   ├── accounts/              # User authentication
│   ├── multilingual/          # AI translation system
│   ├── ai_assistant/          # Chat and AI tools
│   ├── appointments/          # Booking system
│   ├── pets/                  # Pet profiles and records
│   ├── store/                 # E-commerce
│   ├── pharmacy/              # Prescription management
│   ├── communications/        # Email, SMS, WhatsApp
│   ├── crm/                   # Customer relationships
│   └── practice/              # Staff, accounting, reports
├── templates/                  # Global templates
│   ├── base.html
│   ├── components/
│   └── partials/
├── static/                     # Static files
│   ├── css/
│   ├── js/
│   └── images/
├── locale/                     # Translation files
│   ├── es/
│   └── en/
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   ├── production.txt
│   └── test.txt
├── manage.py
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

### Settings Base (config/settings/base.py)
```python
"""
Django base settings for Pet-Friendly Vet project.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'change-me-in-production')
DEBUG = os.getenv('DJANGO_DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
]

THIRD_PARTY_APPS = [
    'django_htmx',
    'widget_tweaks',
    'django_celery_beat',
    'django_celery_results',
    'rest_framework',
    'corsheaders',
]

LOCAL_APPS = [
    'apps.core',
    'apps.accounts',
    'apps.multilingual',
    'apps.ai_assistant',
    'apps.appointments',
    'apps.pets',
    'apps.store',
    'apps.pharmacy',
    'apps.communications',
    'apps.crm',
    'apps.practice',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'apps.core.context_processors.site_settings',
                'apps.store.context_processors.cart',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'petfriendly'),
        'USER': os.getenv('POSTGRES_USER', 'postgres'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
        'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
    }
}

# Authentication
AUTH_USER_MODEL = 'accounts.User'
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'core:dashboard'
LOGOUT_REDIRECT_URL = 'core:home'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'apps.accounts.backends.EmailBackend',
    'apps.accounts.backends.PhoneBackend',
]

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Cancun'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('es', 'Español'),
    ('en', 'English'),
    ('de', 'Deutsch'),
    ('fr', 'Français'),
    ('it', 'Italiano'),
]

LOCALE_PATHS = [BASE_DIR / 'locale']

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Celery Configuration
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://localhost:6379/1'),
    }
}

# Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# Email Configuration (Amazon SES)
EMAIL_BACKEND = 'django_ses.SESBackend'
AWS_SES_REGION_NAME = os.getenv('AWS_SES_REGION', 'us-east-1')
AWS_SES_REGION_ENDPOINT = f'email.{AWS_SES_REGION_NAME}.amazonaws.com'
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@petfriendlyvet.com')

# OpenRouter AI Configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_BASE_URL = 'https://openrouter.ai/api/v1'
AI_MODEL = os.getenv('AI_MODEL', 'anthropic/claude-sonnet-4')

# Stripe Configuration
STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

# Twilio Configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

# WhatsApp Configuration
WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
WHATSAPP_ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
WHATSAPP_VERIFY_TOKEN = os.getenv('WHATSAPP_VERIFY_TOKEN')

# Facturama CFDI Configuration
FACTURAMA_USER = os.getenv('FACTURAMA_USER')
FACTURAMA_PASSWORD = os.getenv('FACTURAMA_PASSWORD')
FACTURAMA_SANDBOX = os.getenv('FACTURAMA_SANDBOX', 'True').lower() == 'true'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

### Development Settings (config/settings/development.py)
```python
"""Development settings."""
from .base import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Debug toolbar
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
INTERNAL_IPS = ['127.0.0.1']

# Use console email backend in development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable whitenoise in development
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
```

### Environment Variables (.env.example)
```bash
# Django
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database
POSTGRES_DB=petfriendly
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password-here
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# AI (OpenRouter)
OPENROUTER_API_KEY=your-openrouter-key
AI_MODEL=anthropic/claude-sonnet-4

# Stripe (Mexico)
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Twilio SMS
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+52...

# WhatsApp Business
WHATSAPP_PHONE_NUMBER_ID=...
WHATSAPP_ACCESS_TOKEN=...
WHATSAPP_VERIFY_TOKEN=...

# Amazon SES
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_SES_REGION=us-east-1
DEFAULT_FROM_EMAIL=noreply@petfriendlyvet.com

# Facturama CFDI
FACTURAMA_USER=...
FACTURAMA_PASSWORD=...
FACTURAMA_SANDBOX=True

# Google OAuth
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

### Requirements Base (requirements/base.txt)
```
# Django
Django>=5.0,<6.0
psycopg[binary]>=3.1

# Django extensions
django-htmx>=1.17
django-widget-tweaks>=1.5
django-environ>=0.11
whitenoise>=6.6

# REST API
djangorestframework>=3.14
django-cors-headers>=4.3

# Celery
celery>=5.3
django-celery-beat>=2.5
django-celery-results>=2.5
redis>=5.0

# AI/ML
httpx>=0.25
openai>=1.6

# Payments
stripe>=7.0

# Communications
django-ses>=3.5
twilio>=8.10

# CFDI
facturama>=0.0.6

# Security
python-dotenv>=1.0

# Utilities
Pillow>=10.1
python-dateutil>=2.8
```

### Requirements Development (requirements/development.txt)
```
-r base.txt

# Development tools
django-debug-toolbar>=4.2
ipython>=8.18
black>=23.12
isort>=5.13
flake8>=6.1
mypy>=1.7

# Testing
pytest>=7.4
pytest-django>=4.7
pytest-cov>=4.1
factory-boy>=3.3
faker>=22.0
```

### Core App Base Model (apps/core/models.py)
```python
"""Base models for all apps."""
import uuid
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """Abstract base model with created/updated timestamps."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """Abstract base model with UUID primary key."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class SoftDeleteManager(models.Manager):
    """Manager that excludes soft-deleted objects by default."""
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

    def with_deleted(self):
        return super().get_queryset()

    def deleted_only(self):
        return super().get_queryset().filter(deleted_at__isnull=False)


class SoftDeleteModel(models.Model):
    """Abstract base model with soft delete functionality."""
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    def hard_delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])

    @property
    def is_deleted(self):
        return self.deleted_at is not None


class BaseModel(TimeStampedModel, SoftDeleteModel):
    """Standard base model combining timestamps and soft delete."""
    class Meta:
        abstract = True
```

### Main URLs (config/urls.py)
```python
"""URL configuration for Pet-Friendly project."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('api/', include('apps.core.api_urls')),
]

urlpatterns += i18n_patterns(
    path('', include('apps.core.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('pets/', include('apps.pets.urls')),
    path('appointments/', include('apps.appointments.urls')),
    path('store/', include('apps.store.urls')),
    path('pharmacy/', include('apps.pharmacy.urls')),
    path('chat/', include('apps.ai_assistant.urls')),
    path('crm/', include('apps.crm.urls')),
    path('practice/', include('apps.practice.urls')),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]
```

### Tailwind Configuration (tailwind.config.js)
```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './apps/**/templates/**/*.html',
    './static/js/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#E8F0F8',
          100: '#D1E1F1',
          200: '#A3C3E3',
          300: '#75A5D5',
          400: '#4787C7',
          500: '#1E4D8C',  // Primary Blue
          600: '#183D70',
          700: '#122E54',
          800: '#0C1E38',
          900: '#060F1C',
        },
        secondary: {
          50: '#EFF8E8',
          100: '#DFF1D1',
          200: '#BFE3A3',
          300: '#9FD575',
          400: '#7FC747',
          500: '#5FAD41',  // Secondary Green
          600: '#4C8A34',
          700: '#396827',
          800: '#26451A',
          900: '#13230D',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}
```

## Test Cases

### Test Settings Configuration
```python
# tests/test_settings.py
import pytest
from django.conf import settings


class TestSettings:
    def test_debug_is_configurable(self):
        assert hasattr(settings, 'DEBUG')

    def test_database_configured(self):
        assert 'default' in settings.DATABASES
        assert settings.DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql'

    def test_installed_apps_includes_local_apps(self):
        assert 'apps.core' in settings.INSTALLED_APPS
        assert 'apps.accounts' in settings.INSTALLED_APPS
        assert 'apps.pets' in settings.INSTALLED_APPS

    def test_language_settings(self):
        assert settings.LANGUAGE_CODE == 'es'
        assert ('es', 'Español') in settings.LANGUAGES
        assert ('en', 'English') in settings.LANGUAGES

    def test_timezone_is_cancun(self):
        assert settings.TIME_ZONE == 'America/Cancun'

    def test_celery_configured(self):
        assert hasattr(settings, 'CELERY_BROKER_URL')
        assert hasattr(settings, 'CELERY_RESULT_BACKEND')

    def test_ai_settings_exist(self):
        assert hasattr(settings, 'OPENROUTER_API_KEY')
        assert hasattr(settings, 'AI_MODEL')
```

### Test Project Structure
```python
# tests/test_project_structure.py
import pytest
from pathlib import Path


class TestProjectStructure:
    @pytest.fixture
    def base_dir(self):
        return Path(__file__).resolve().parent.parent

    def test_apps_directory_exists(self, base_dir):
        assert (base_dir / 'apps').is_dir()

    def test_all_apps_exist(self, base_dir):
        apps = [
            'core', 'accounts', 'multilingual', 'ai_assistant',
            'appointments', 'pets', 'store', 'pharmacy',
            'communications', 'crm', 'practice'
        ]
        for app in apps:
            assert (base_dir / 'apps' / app).is_dir(), f"Missing app: {app}"

    def test_templates_directory_exists(self, base_dir):
        assert (base_dir / 'templates').is_dir()

    def test_static_directory_exists(self, base_dir):
        assert (base_dir / 'static').is_dir()

    def test_locale_directory_exists(self, base_dir):
        assert (base_dir / 'locale').is_dir()
```

### Test Django Checks
```python
# tests/test_django_checks.py
import pytest
from django.core.management import call_command
from io import StringIO


class TestDjangoChecks:
    def test_check_passes(self):
        out = StringIO()
        call_command('check', stdout=out)
        output = out.getvalue()
        assert 'System check identified no issues' in output or output == ''

    def test_migrations_no_pending(self):
        out = StringIO()
        call_command('migrate', '--check', stdout=out, stderr=out)
        # If this doesn't raise, migrations are up to date
```

## Acceptance Criteria

### AC-1: Django Application Starts Successfully
**Given** the project is set up with all dependencies installed
**When** I run `python manage.py runserver`
**Then** the server starts without errors on port 8000

### AC-2: Database Connection Works
**Given** PostgreSQL is running and configured in .env
**When** I run `python manage.py migrate`
**Then** all migrations apply successfully without errors

### AC-3: All Django Apps Load
**Given** the project is configured
**When** I run `python manage.py check`
**Then** it reports "System check identified no issues"

### AC-4: Rust License Validator Works
**Given** Rust is installed and components are built
**When** I run `scc-license license.key`
**Then** it returns valid JSON with license information

### AC-5: Development Environment Ready
**Given** the project is fully set up
**When** a new developer clones and follows README instructions
**Then** they can start the server within 15 minutes

## Definition of Done
- [ ] `python manage.py check` passes with no issues
- [ ] `python manage.py runserver` starts without errors
- [ ] Development database connects and migrations run
- [ ] All 11 Django apps initialized with __init__.py and apps.py
- [ ] Tailwind CSS builds successfully
- [ ] HTMX and Alpine.js load in templates
- [ ] Tests written and passing (>95% coverage)
- [ ] .env.example documents all required variables
- [ ] README.md updated with setup instructions
- [ ] requirements/base.txt includes all production dependencies
- [ ] Celery configuration verified with Redis

## Dependencies
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Node.js 18+ (for Tailwind CSS)
- Rust 1.70+ (for SCC components)

## Rust Workspace Setup (SCC Components)

### Overview
South City Computer (SCC) Rust components provide performance-critical functionality with embedded license verification. These are reusable across all SCC projects and will be distributed as standalone pip packages.

See: [RUST_COMPONENTS.md](../RUST_COMPONENTS.md) and [LICENSING.md](../LICENSING.md)

### Rust Workspace Structure
```
rust/
├── Cargo.toml                 # Workspace root
├── README.md
└── scc-license/              # License validation (first component)
    ├── Cargo.toml
    └── src/
        ├── main.rs           # License validator binary
        └── bin/
            └── generate.rs   # License generator (internal use)
```

### Required Build Steps

**1. Install Rust toolchain:**
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env
```

**2. Build SCC components:**
```bash
cd rust
cargo build --release
```

**3. Verify binaries created:**
```bash
ls -la target/release/scc-license
ls -la target/release/scc-license-generate
```

**4. Generate development license:**
```bash
./target/release/scc-license-generate \
    --licensee "Development" \
    --email "dev@localhost" \
    --type developer \
    --domains "localhost,127.0.0.1" \
    --days 365 \
    --output license.key
```

### Django Integration

**Environment variable (.env.example addition):**
```bash
# SCC License
SCC_LICENSE_FILE=license.key
```

**License validation at Django startup (apps/core/apps.py):**
```python
"""Core app configuration with license validation."""
import os
import subprocess
import json
from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'

    def ready(self):
        self._validate_license()

    def _validate_license(self):
        """Validate SCC license at startup."""
        license_file = os.getenv('SCC_LICENSE_FILE', 'license.key')
        validator_path = os.getenv('SCC_LICENSE_BINARY', 'rust/target/release/scc-license')

        # Skip in test mode
        if os.getenv('DJANGO_SETTINGS_MODULE', '').endswith('.test'):
            return

        if not os.path.exists(validator_path):
            raise ImproperlyConfigured(
                f"SCC license validator not found at {validator_path}. "
                "Build with: cd rust && cargo build --release"
            )

        try:
            result = subprocess.run(
                [validator_path, license_file],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                raise ImproperlyConfigured(
                    f"License validation failed: {result.stderr}"
                )

            # Parse license info for features
            license_info = json.loads(result.stdout)
            os.environ['SCC_LICENSE_TYPE'] = license_info.get('license_type', 'unknown')
            os.environ['SCC_LICENSEE'] = license_info.get('licensee', 'unknown')

        except subprocess.TimeoutExpired:
            raise ImproperlyConfigured("License validation timed out")
        except json.JSONDecodeError:
            raise ImproperlyConfigured("Invalid license response format")
```

### Deliverables (Rust Setup)
- [ ] Rust toolchain installed
- [ ] `cargo build --release` completes successfully
- [ ] scc-license binary validates licenses
- [ ] scc-license-generate creates valid license files
- [ ] Development license.key generated
- [ ] Django startup validates license
- [ ] SCC_LICENSE_FILE in .env.example

### Test Cases (Rust Integration)
```python
# tests/test_license_integration.py
import pytest
import subprocess
import os
from pathlib import Path


class TestLicenseIntegration:
    @pytest.fixture
    def rust_binary_path(self):
        return Path(__file__).resolve().parent.parent / 'rust' / 'target' / 'release' / 'scc-license'

    def test_license_binary_exists(self, rust_binary_path):
        """Verify scc-license binary was built."""
        assert rust_binary_path.exists(), "Run: cd rust && cargo build --release"

    def test_license_validates_valid_file(self, rust_binary_path, tmp_path):
        """Test that a valid license file passes validation."""
        # Generate test license
        generator = rust_binary_path.parent / 'scc-license-generate'
        license_path = tmp_path / 'test.key'

        result = subprocess.run([
            str(generator),
            '--licensee', 'Test',
            '--email', 'test@test.com',
            '--type', 'developer',
            '--domains', 'localhost',
            '--days', '1',
            '--output', str(license_path)
        ], capture_output=True)

        assert result.returncode == 0

        # Validate it
        result = subprocess.run(
            [str(rust_binary_path), str(license_path)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert 'Test' in result.stdout

    def test_license_rejects_invalid_file(self, rust_binary_path, tmp_path):
        """Test that an invalid license file fails."""
        invalid_license = tmp_path / 'invalid.key'
        invalid_license.write_text('{"version": 1, "payload": "invalid", "signature": "wrong"}')

        result = subprocess.run(
            [str(rust_binary_path), str(invalid_license)],
            capture_output=True,
            text=True
        )

        assert result.returncode != 0
```

## Estimated Effort
5 hours (including Rust setup)
