"""Tests for Django settings configuration."""
import pytest
from django.conf import settings


class TestBaseSettings:
    """Tests for base Django settings."""

    def test_secret_key_is_set(self):
        """SECRET_KEY should be set."""
        assert hasattr(settings, 'SECRET_KEY')
        assert settings.SECRET_KEY is not None
        assert len(settings.SECRET_KEY) > 0

    def test_installed_apps_contain_core_apps(self):
        """INSTALLED_APPS should contain all core apps."""
        required_apps = [
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
        for app in required_apps:
            assert app in settings.INSTALLED_APPS, f'{app} should be in INSTALLED_APPS'

    def test_auth_user_model_is_custom(self):
        """AUTH_USER_MODEL should be the custom User model."""
        assert settings.AUTH_USER_MODEL == 'accounts.User'

    def test_language_code_is_spanish(self):
        """LANGUAGE_CODE should be Spanish."""
        assert settings.LANGUAGE_CODE == 'es'

    def test_timezone_is_cancun(self):
        """TIME_ZONE should be America/Cancun."""
        assert settings.TIME_ZONE == 'America/Cancun'

    def test_i18n_is_enabled(self):
        """Internationalization should be enabled."""
        assert settings.USE_I18N is True

    def test_available_languages(self):
        """LANGUAGES should contain Spanish and English at minimum."""
        language_codes = [code for code, name in settings.LANGUAGES]
        assert 'es' in language_codes
        assert 'en' in language_codes

    def test_templates_configuration(self):
        """Templates should be configured correctly."""
        assert len(settings.TEMPLATES) > 0
        template_config = settings.TEMPLATES[0]
        assert 'django.template.backends.django.DjangoTemplates' == template_config['BACKEND']

    def test_static_url_is_set(self):
        """STATIC_URL should be set."""
        assert settings.STATIC_URL is not None

    def test_media_url_is_set(self):
        """MEDIA_URL should be set."""
        assert settings.MEDIA_URL is not None


class TestTestSettings:
    """Tests for test-specific settings."""

    def test_password_hashers_are_fast(self):
        """Test settings should use fast password hashers."""
        assert 'MD5PasswordHasher' in settings.PASSWORD_HASHERS[0]

    def test_skip_license_check_is_enabled(self):
        """Test settings should skip license validation."""
        assert getattr(settings, 'SCC_SKIP_LICENSE_CHECK', False) is True


class TestProductionSecuritySettings:
    """Tests for production security settings (B-001: CSRF trusted origins)."""

    def test_csrf_trusted_origins_is_configured(self):
        """CSRF_TRUSTED_ORIGINS must be configured in production settings."""
        from config.settings import production
        assert hasattr(production, 'CSRF_TRUSTED_ORIGINS'), \
            'CSRF_TRUSTED_ORIGINS must be defined in production settings'
        assert isinstance(production.CSRF_TRUSTED_ORIGINS, list), \
            'CSRF_TRUSTED_ORIGINS must be a list'
        assert len(production.CSRF_TRUSTED_ORIGINS) > 0, \
            'CSRF_TRUSTED_ORIGINS must not be empty'

    def test_csrf_trusted_origins_contains_main_domain(self):
        """CSRF_TRUSTED_ORIGINS must include petfriendlyvet.com."""
        from config.settings import production
        assert 'https://petfriendlyvet.com' in production.CSRF_TRUSTED_ORIGINS, \
            'CSRF_TRUSTED_ORIGINS must include https://petfriendlyvet.com'

    def test_csrf_trusted_origins_contains_www_subdomain(self):
        """CSRF_TRUSTED_ORIGINS must include www.petfriendlyvet.com."""
        from config.settings import production
        assert 'https://www.petfriendlyvet.com' in production.CSRF_TRUSTED_ORIGINS, \
            'CSRF_TRUSTED_ORIGINS must include https://www.petfriendlyvet.com'

    def test_csrf_trusted_origins_excludes_dev_subdomain(self):
        """CSRF_TRUSTED_ORIGINS intentionally excludes dev for custom 403 page testing (B-001)."""
        from config.settings import production
        # dev.petfriendlyvet.com intentionally excluded to test custom CSRF failure page
        assert 'https://dev.petfriendlyvet.com' not in production.CSRF_TRUSTED_ORIGINS, \
            'dev.petfriendlyvet.com should be excluded from CSRF_TRUSTED_ORIGINS (B-001)'

    def test_cors_allowed_origins_contains_dev_subdomain(self):
        """CORS_ALLOWED_ORIGINS must include dev.petfriendlyvet.com."""
        from config.settings import production
        assert 'https://dev.petfriendlyvet.com' in production.CORS_ALLOWED_ORIGINS, \
            'CORS_ALLOWED_ORIGINS must include https://dev.petfriendlyvet.com'
