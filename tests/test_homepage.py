"""Tests for T-005 Homepage Implementation.

Tests validate homepage sections and functionality:
- Hero section with CTA
- Services overview grid
- About Dr. Pablo section
- Location with map
- Chat widget teaser
- Mobile responsiveness
- Bilingual content
"""
import pytest
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
class TestHomepageLoads:
    """Test homepage loads without errors."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_homepage_returns_200(self, client):
        """Homepage should return 200 status."""
        response = client.get('/')
        assert response.status_code == 200

    def test_homepage_uses_correct_template(self, client):
        """Homepage should use home.html template."""
        response = client.get('/')
        assert 'core/home.html' in [t.name for t in response.templates]


@pytest.mark.django_db
class TestHeroSection:
    """Test hero section with CTA."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_hero_section_exists(self, client):
        """Hero section should exist on homepage."""
        response = client.get('/')
        content = response.content.decode()
        assert 'hero' in content.lower() or 'cuidado integral' in content.lower()

    def test_hero_has_headline(self, client):
        """Hero should have a headline."""
        response = client.get('/')
        content = response.content.decode()
        assert '<h1' in content

    def test_hero_has_cta_buttons(self, client):
        """Hero should have CTA buttons."""
        response = client.get('/')
        content = response.content.decode().lower()
        # Check for appointment or contact CTAs
        assert 'cita' in content or 'appointment' in content or 'contacto' in content


@pytest.mark.django_db
class TestServicesSection:
    """Test services overview grid."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_services_section_exists(self, client):
        """Services section should exist."""
        response = client.get('/')
        content = response.content.decode().lower()
        assert 'servicios' in content or 'services' in content

    def test_services_has_clinic(self, client):
        """Services should include clinic."""
        response = client.get('/')
        content = response.content.decode().lower()
        assert 'clínica' in content or 'clinica' in content or 'clinic' in content

    def test_services_has_pharmacy(self, client):
        """Services should include pharmacy."""
        response = client.get('/')
        content = response.content.decode().lower()
        assert 'farmacia' in content or 'pharmacy' in content

    def test_services_has_store(self, client):
        """Services should include store."""
        response = client.get('/')
        content = response.content.decode().lower()
        assert 'tienda' in content or 'store' in content

    def test_services_uses_grid_layout(self, client):
        """Services should use grid layout."""
        response = client.get('/')
        content = response.content.decode()
        assert 'grid' in content


@pytest.mark.django_db
class TestAboutSection:
    """Test about Dr. Pablo preview section."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_about_section_exists(self, client):
        """About section should exist."""
        response = client.get('/')
        content = response.content.decode().lower()
        assert 'dr. pablo' in content or 'pablo' in content or 'nosotros' in content

    def test_about_has_image(self, client):
        """About section should have Dr. Pablo image."""
        response = client.get('/')
        content = response.content.decode()
        # Check for image in about area
        assert 'dr-pablo' in content.lower() or '<img' in content


@pytest.mark.django_db
class TestLocationSection:
    """Test location section with map."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_location_section_exists(self, client):
        """Location section should exist."""
        response = client.get('/')
        content = response.content.decode().lower()
        assert 'puerto morelos' in content

    def test_location_has_address(self, client):
        """Location should show address."""
        response = client.get('/')
        content = response.content.decode().lower()
        assert 'puerto morelos' in content or 'quintana roo' in content

    def test_location_has_hours(self, client):
        """Location should show business hours."""
        response = client.get('/')
        content = response.content.decode().lower()
        assert 'horario' in content or 'hours' in content or 'lunes' in content or 'martes' in content

    def test_location_has_phone(self, client):
        """Location should show phone number."""
        response = client.get('/')
        content = response.content.decode()
        assert '998' in content  # Area code for Cancun/Puerto Morelos

    def test_location_has_whatsapp(self, client):
        """Location should have WhatsApp link."""
        response = client.get('/')
        content = response.content.decode().lower()
        assert 'whatsapp' in content or 'wa.me' in content


@pytest.mark.django_db
class TestChatWidget:
    """Test AI chat widget teaser."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_chat_element_exists(self, client):
        """Chat widget or teaser should exist."""
        response = client.get('/')
        content = response.content.decode().lower()
        # Check for chat-related content
        assert 'chat' in content or 'asistente' in content or 'assistant' in content or 'pregunta' in content


@pytest.mark.django_db
class TestMobileResponsive:
    """Test mobile-responsive layout."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_has_responsive_meta_tag(self, client):
        """Page should have viewport meta tag."""
        response = client.get('/')
        content = response.content.decode()
        assert 'width=device-width' in content

    def test_has_responsive_classes(self, client):
        """Page should use responsive Tailwind classes."""
        response = client.get('/')
        content = response.content.decode()
        # Check for responsive breakpoint classes
        assert 'md:' in content or 'lg:' in content or 'sm:' in content


@pytest.mark.django_db
class TestBilingualContent:
    """Test bilingual content switching."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_default_spanish_content(self, client):
        """Default content should be in Spanish."""
        response = client.get('/')
        content = response.content.decode()
        # Check for Spanish indicators
        assert 'lang="es"' in content or 'Inicio' in content or 'Servicios' in content

    def test_can_switch_to_english(self, client):
        """Should be able to switch to English."""
        response = client.post('/i18n/setlang/', {
            'language': 'en',
            'next': '/'
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
        response = client.get('/')
        content = response.content.decode()
        assert '<main' in content

    def test_has_heading_hierarchy(self, client):
        """Page should have proper heading hierarchy."""
        response = client.get('/')
        content = response.content.decode()
        assert '<h1' in content
        assert '<h2' in content or '<h3' in content

    def test_images_have_alt(self, client):
        """Images should have alt attributes."""
        response = client.get('/')
        content = response.content.decode()
        import re
        img_tags = re.findall(r'<img[^>]+>', content)
        for img in img_tags:
            assert 'alt=' in img, f"Image missing alt: {img}"

    def test_links_are_descriptive(self, client):
        """Links should have descriptive text."""
        response = client.get('/')
        content = response.content.decode()
        # Should not have empty links or "click here"
        assert 'href="#"' not in content or 'aria-label' in content


@pytest.mark.django_db
class TestCTALinks:
    """Test CTA buttons link correctly."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_contact_link_works(self, client):
        """Contact/appointment link should work."""
        response = client.get('/contact/')
        assert response.status_code == 200

    def test_services_link_works(self, client):
        """Services link should work."""
        response = client.get('/services/')
        assert response.status_code == 200

    def test_about_link_works(self, client):
        """About link should work."""
        response = client.get('/about/')
        assert response.status_code == 200
