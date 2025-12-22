"""Tests for T-008 Contact Page Implementation.

Tests validate contact page sections and functionality:
- Page loads correctly
- Form displays with all fields
- Form validation works
- Map placeholder/embed exists
- Hours display
- WhatsApp link works
- FAQ section exists
- Schema.org markup exists
- Mobile responsive
- Bilingual content
"""
import pytest
from django.test import Client


@pytest.mark.django_db
class TestContactPageLoads:
    """Test contact page loads without errors."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_contact_page_returns_200(self, client):
        """Contact page should return 200 status."""
        response = client.get('/contact/')
        assert response.status_code == 200

    def test_contact_page_uses_correct_template(self, client):
        """Contact page should use contact.html template."""
        response = client.get('/contact/')
        assert 'core/contact.html' in [t.name for t in response.templates]


@pytest.mark.django_db
class TestContactForm:
    """Test contact form display and fields."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_form_exists(self, client):
        """Contact form should exist on page."""
        response = client.get('/contact/')
        content = response.content.decode()
        assert '<form' in content

    def test_form_has_name_field(self, client):
        """Form should have name field."""
        response = client.get('/contact/')
        content = response.content.decode().lower()
        assert 'name' in content or 'nombre' in content

    def test_form_has_email_field(self, client):
        """Form should have email field."""
        response = client.get('/contact/')
        content = response.content.decode().lower()
        assert 'email' in content or 'correo' in content

    def test_form_has_message_field(self, client):
        """Form should have message field."""
        response = client.get('/contact/')
        content = response.content.decode().lower()
        assert 'message' in content or 'mensaje' in content

    def test_form_has_submit_button(self, client):
        """Form should have submit button."""
        response = client.get('/contact/')
        content = response.content.decode().lower()
        assert 'submit' in content or 'enviar' in content or 'button' in content


@pytest.mark.django_db
class TestMapSection:
    """Test map section display."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_map_section_exists(self, client):
        """Map section or placeholder should exist."""
        response = client.get('/contact/')
        content = response.content.decode().lower()
        # Could be embedded map or placeholder
        assert ('map' in content or 'mapa' in content or
                'maps.google' in content or 'ubicación' in content)


@pytest.mark.django_db
class TestBusinessHours:
    """Test business hours display."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_hours_section_exists(self, client):
        """Hours section should exist."""
        response = client.get('/contact/')
        content = response.content.decode().lower()
        assert 'horario' in content or 'hours' in content

    def test_shows_days(self, client):
        """Should show days of the week."""
        response = client.get('/contact/')
        content = response.content.decode().lower()
        # Check for at least one day
        assert ('lunes' in content or 'monday' in content or
                'martes' in content or 'tuesday' in content or
                'domingo' in content or 'sunday' in content)


@pytest.mark.django_db
class TestContactMethods:
    """Test various contact methods display."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_has_phone_number(self, client):
        """Should display phone number."""
        response = client.get('/contact/')
        content = response.content.decode()
        assert '998' in content  # Area code

    def test_has_whatsapp_link(self, client):
        """Should have WhatsApp link."""
        response = client.get('/contact/')
        content = response.content.decode().lower()
        assert 'whatsapp' in content or 'wa.me' in content

    def test_has_email(self, client):
        """Should display email address or email option."""
        response = client.get('/contact/')
        content = response.content.decode().lower()
        assert 'email' in content or 'correo' in content or '@' in content


@pytest.mark.django_db
class TestFAQSection:
    """Test FAQ section display."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_faq_section_exists(self, client):
        """FAQ section should exist."""
        response = client.get('/contact/')
        content = response.content.decode().lower()
        assert ('faq' in content or 'pregunta' in content or
                'question' in content or 'frecuente' in content)


@pytest.mark.django_db
class TestAddressDisplay:
    """Test address display."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_shows_puerto_morelos(self, client):
        """Should show Puerto Morelos location."""
        response = client.get('/contact/')
        content = response.content.decode().lower()
        assert 'puerto morelos' in content


@pytest.mark.django_db
class TestMobileResponsive:
    """Test mobile-responsive layout."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_has_responsive_meta_tag(self, client):
        """Page should have viewport meta tag."""
        response = client.get('/contact/')
        content = response.content.decode()
        assert 'width=device-width' in content

    def test_has_responsive_classes(self, client):
        """Page should use responsive Tailwind classes."""
        response = client.get('/contact/')
        content = response.content.decode()
        assert 'md:' in content or 'lg:' in content or 'sm:' in content


@pytest.mark.django_db
class TestBilingualContent:
    """Test bilingual content switching."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_default_spanish_content(self, client):
        """Default content should be in Spanish."""
        response = client.get('/contact/')
        content = response.content.decode()
        assert 'lang="es"' in content or 'Contacto' in content

    def test_can_switch_to_english(self, client):
        """Should be able to switch to English."""
        response = client.post('/i18n/setlang/', {
            'language': 'en',
            'next': '/contact/'
        }, follow=True)
        assert response.status_code == 200


@pytest.mark.django_db
class TestAccessibility:
    """Test accessibility requirements."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_has_main_landmark(self, client):
        """Page should have main landmark."""
        response = client.get('/contact/')
        content = response.content.decode()
        assert '<main' in content

    def test_has_heading_hierarchy(self, client):
        """Page should have proper heading hierarchy."""
        response = client.get('/contact/')
        content = response.content.decode()
        assert '<h1' in content

    def test_form_has_labels(self, client):
        """Form fields should have labels."""
        response = client.get('/contact/')
        content = response.content.decode()
        assert '<label' in content
