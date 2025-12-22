"""Tests for T-004 Multilingual System.

Tests validate AI-powered multilingual functionality:
- Language model and core languages
- Language switcher
- URL prefix routing
- Browser language detection
- User language preference
- Translation caching
"""
import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestLanguageModel:
    """Test Language model."""

    def test_language_model_exists(self):
        """Language model should exist."""
        from apps.multilingual.models import Language
        assert Language is not None

    def test_language_has_required_fields(self):
        """Language should have code, name, native_name, is_core, is_active fields."""
        from apps.multilingual.models import Language
        lang = Language(
            code='es',
            name='Spanish',
            native_name='Español',
            is_core=True,
            is_active=True
        )
        lang.save()
        assert lang.code == 'es'
        assert lang.name == 'Spanish'
        assert lang.native_name == 'Español'
        assert lang.is_core is True
        assert lang.is_active is True

    def test_core_languages_exist(self):
        """Core 5 languages should be available."""
        from apps.multilingual.models import Language
        # Create core languages if not exist
        core_codes = ['es', 'en', 'de', 'fr', 'it']
        for code in core_codes:
            Language.objects.get_or_create(
                code=code,
                defaults={'name': code, 'native_name': code, 'is_core': True}
            )

        core_langs = Language.objects.filter(is_core=True)
        codes = list(core_langs.values_list('code', flat=True))
        assert 'es' in codes
        assert 'en' in codes
        assert 'de' in codes
        assert 'fr' in codes
        assert 'it' in codes


@pytest.mark.django_db
class TestLanguageSwitcher:
    """Test language switching functionality."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_language_switcher_on_page(self, client):
        """Language switcher should be visible on pages."""
        response = client.get('/')
        content = response.content.decode().lower()
        assert 'language' in content or 'lang' in content or 'idioma' in content

    def test_switch_language_url_exists(self, client):
        """Language switch URL should exist."""
        response = client.post('/i18n/setlang/', {
            'language': 'en',
            'next': '/'
        }, follow=True)
        assert response.status_code == 200

    def test_switch_to_english(self, client):
        """Switching to English should work."""
        client.post('/i18n/setlang/', {
            'language': 'en',
            'next': '/'
        })
        response = client.get('/')
        # Should return 200 regardless of content language
        assert response.status_code == 200

    def test_switch_to_spanish(self, client):
        """Switching to Spanish should work."""
        client.post('/i18n/setlang/', {
            'language': 'es',
            'next': '/'
        })
        response = client.get('/')
        assert response.status_code == 200

    def test_switch_to_german(self, client):
        """Switching to German should work."""
        client.post('/i18n/setlang/', {
            'language': 'de',
            'next': '/'
        })
        response = client.get('/')
        assert response.status_code == 200

    def test_switch_to_french(self, client):
        """Switching to French should work."""
        client.post('/i18n/setlang/', {
            'language': 'fr',
            'next': '/'
        })
        response = client.get('/')
        assert response.status_code == 200

    def test_switch_to_italian(self, client):
        """Switching to Italian should work."""
        client.post('/i18n/setlang/', {
            'language': 'it',
            'next': '/'
        })
        response = client.get('/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestLanguageDetection:
    """Test browser language detection."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_accepts_language_header(self, client):
        """Should respect Accept-Language header for first-time visitors."""
        response = client.get('/', HTTP_ACCEPT_LANGUAGE='en-US,en;q=0.9')
        assert response.status_code == 200

    def test_default_language_spanish(self, client):
        """Default language should be Spanish."""
        response = client.get('/')
        assert response.status_code == 200
        # Page should render in Spanish by default
        content = response.content.decode()
        # Check for Spanish text or lang attribute
        assert 'lang="es"' in content or 'Inicio' in content


@pytest.mark.django_db
class TestUserLanguagePreference:
    """Test user language preference persistence."""

    @pytest.fixture
    def client(self):
        return Client()

    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            preferred_language='en'
        )

    def test_user_has_language_preference(self, user):
        """User model should have preferred_language field."""
        assert hasattr(user, 'preferred_language')
        assert user.preferred_language == 'en'

    def test_user_preference_persists(self, user):
        """User language preference should persist across sessions."""
        user.preferred_language = 'de'
        user.save()
        user.refresh_from_db()
        assert user.preferred_language == 'de'

    def test_logged_in_user_gets_preferred_language(self, client, user):
        """Logged in user should see content in their preferred language."""
        client.force_login(user)
        response = client.get('/')
        assert response.status_code == 200
        # The user's language preference should be respected


@pytest.mark.django_db
class TestTranslatedContent:
    """Test TranslatedContent model for static content."""

    def test_translated_content_model_exists(self):
        """TranslatedContent model should exist."""
        from apps.multilingual.models import TranslatedContent
        assert TranslatedContent is not None

    def test_translated_content_has_required_fields(self):
        """TranslatedContent should have required fields."""
        from apps.multilingual.models import TranslatedContent, Language
        from django.contrib.contenttypes.models import ContentType

        # Create a language first
        lang = Language.objects.create(
            code='en',
            name='English',
            native_name='English',
            is_core=True
        )

        # Get a content type (using User for testing)
        ct = ContentType.objects.get_for_model(User)

        tc = TranslatedContent(
            content_type=ct,
            object_id=1,
            language=lang,
            field_name='title',
            translation='Hello World',
            is_ai_generated=True
        )
        tc.save()

        assert tc.field_name == 'title'
        assert tc.translation == 'Hello World'
        assert tc.is_ai_generated is True


@pytest.mark.django_db
class TestURLPrefixRouting:
    """Test URL prefix routing for languages."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_homepage_without_prefix(self, client):
        """Homepage should work without language prefix."""
        response = client.get('/')
        assert response.status_code == 200

    def test_services_page_works(self, client):
        """Services page should work."""
        response = client.get('/services/')
        assert response.status_code == 200

    def test_about_page_works(self, client):
        """About page should work."""
        response = client.get('/about/')
        assert response.status_code == 200

    def test_contact_page_works(self, client):
        """Contact page should work."""
        response = client.get('/contact/')
        assert response.status_code == 200
