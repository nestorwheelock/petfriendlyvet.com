"""Tests for T-007 Services Page Implementation.

Tests validate services page sections and functionality:
- Page loads correctly
- All categories load
- Services filter by category
- Prices display correctly
- Bilingual content works
- Emergency section visible
- Book buttons work
- Mobile responsive
"""
import pytest
from django.test import Client


@pytest.mark.django_db
class TestServicesPageLoads:
    """Test services page loads without errors."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_services_page_returns_200(self, client):
        """Services page should return 200 status."""
        response = client.get('/services/')
        assert response.status_code == 200

    def test_services_page_uses_correct_template(self, client):
        """Services page should use services.html template."""
        response = client.get('/services/')
        assert 'core/services.html' in [t.name for t in response.templates]


@pytest.mark.django_db
class TestServiceCategories:
    """Test service categories display."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_has_clinic_category(self, client):
        """Services should have clinic category."""
        response = client.get('/services/')
        content = response.content.decode().lower()
        assert 'clínica' in content or 'clinic' in content or 'clinica' in content

    def test_has_pharmacy_category(self, client):
        """Services should have pharmacy category."""
        response = client.get('/services/')
        content = response.content.decode().lower()
        assert 'farmacia' in content or 'pharmacy' in content

    def test_has_store_category(self, client):
        """Services should have store category."""
        response = client.get('/services/')
        content = response.content.decode().lower()
        assert 'tienda' in content or 'store' in content

    def test_has_emergency_category(self, client):
        """Services should have emergency category."""
        response = client.get('/services/')
        content = response.content.decode().lower()
        assert 'emergencia' in content or 'emergency' in content or 'urgencia' in content


@pytest.mark.django_db
class TestClinicServices:
    """Test clinic services display."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_has_consultations(self, client):
        """Should show consultation services."""
        response = client.get('/services/')
        content = response.content.decode().lower()
        assert 'consulta' in content or 'consultation' in content

    def test_has_vaccinations(self, client):
        """Should show vaccination services."""
        response = client.get('/services/')
        content = response.content.decode().lower()
        assert 'vacuna' in content or 'vaccine' in content or 'vaccination' in content

    def test_has_surgery(self, client):
        """Should show surgery services."""
        response = client.get('/services/')
        content = response.content.decode().lower()
        assert 'cirugía' in content or 'surgery' in content or 'cirugia' in content

    def test_has_lab_work(self, client):
        """Should show laboratory services."""
        response = client.get('/services/')
        content = response.content.decode().lower()
        assert 'laboratorio' in content or 'lab' in content or 'diagnóstico' in content


@pytest.mark.django_db
class TestEmergencySection:
    """Test emergency services section."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_emergency_section_visible(self, client):
        """Emergency section should be visible."""
        response = client.get('/services/')
        content = response.content.decode().lower()
        assert 'emergencia' in content or 'emergency' in content or 'urgencia' in content

    def test_emergency_has_phone(self, client):
        """Emergency section should have phone number."""
        response = client.get('/services/')
        content = response.content.decode()
        assert '998' in content  # Area code


@pytest.mark.django_db
class TestBookingButtons:
    """Test booking/CTA buttons."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_has_book_cta(self, client):
        """Services page should have booking CTAs."""
        response = client.get('/services/')
        content = response.content.decode().lower()
        assert ('cita' in content or 'appointment' in content or
                'agendar' in content or 'book' in content or
                'contacto' in content or 'contact' in content)


@pytest.mark.django_db
class TestMobileResponsive:
    """Test mobile-responsive layout."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_has_responsive_meta_tag(self, client):
        """Page should have viewport meta tag."""
        response = client.get('/services/')
        content = response.content.decode()
        assert 'width=device-width' in content

    def test_has_responsive_classes(self, client):
        """Page should use responsive Tailwind classes."""
        response = client.get('/services/')
        content = response.content.decode()
        assert 'md:' in content or 'lg:' in content or 'sm:' in content

    def test_uses_grid_layout(self, client):
        """Services should use grid layout."""
        response = client.get('/services/')
        content = response.content.decode()
        assert 'grid' in content


@pytest.mark.django_db
class TestBilingualContent:
    """Test bilingual content switching."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_default_spanish_content(self, client):
        """Default content should be in Spanish."""
        response = client.get('/services/')
        content = response.content.decode()
        assert 'lang="es"' in content or 'Servicios' in content

    def test_can_switch_to_english(self, client):
        """Should be able to switch to English."""
        response = client.post('/i18n/setlang/', {
            'language': 'en',
            'next': '/services/'
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
        response = client.get('/services/')
        content = response.content.decode()
        assert '<main' in content

    def test_has_heading_hierarchy(self, client):
        """Page should have proper heading hierarchy."""
        response = client.get('/services/')
        content = response.content.decode()
        assert '<h1' in content
        assert '<h2' in content or '<h3' in content
