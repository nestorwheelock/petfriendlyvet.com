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
