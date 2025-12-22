"""Tests for T-006 About Page Implementation.

Tests validate about page sections and functionality:
- Page loads correctly
- Dr. Pablo bio section
- Clinic story section
- Mission/values section
- Certifications section
- Photo gallery placeholder
- CTA links
- Mobile responsiveness
- Bilingual content
"""
import pytest
from django.test import Client


@pytest.mark.django_db
class TestAboutPageLoads:
    """Test about page loads without errors."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_about_page_returns_200(self, client):
        """About page should return 200 status."""
        response = client.get('/about/')
        assert response.status_code == 200

    def test_about_page_uses_correct_template(self, client):
        """About page should use about.html template."""
        response = client.get('/about/')
        assert 'core/about.html' in [t.name for t in response.templates]


@pytest.mark.django_db
class TestHeroSection:
    """Test hero section with Dr. Pablo photo."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_hero_section_exists(self, client):
        """Hero section should exist on about page."""
        response = client.get('/about/')
        content = response.content.decode().lower()
        assert 'dr. pablo' in content or 'pablo' in content

    def test_hero_has_doctor_title(self, client):
        """Hero should show doctor title."""
        response = client.get('/about/')
        content = response.content.decode().lower()
        assert 'veterinario' in content or 'veterinarian' in content or 'dr.' in content


@pytest.mark.django_db
class TestBiographySection:
    """Test Dr. Pablo biography section."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_biography_section_exists(self, client):
        """Biography section should exist."""
        response = client.get('/about/')
        content = response.content.decode().lower()
        assert 'experiencia' in content or 'experience' in content or 'about' in content

    def test_biography_mentions_experience(self, client):
        """Biography should mention experience or education."""
        response = client.get('/about/')
        content = response.content.decode().lower()
        assert ('medicina' in content or 'medicine' in content or
                'experiencia' in content or 'experience' in content or
                'formación' in content or 'education' in content)


@pytest.mark.django_db
class TestClinicSection:
    """Test clinic story section."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_clinic_section_exists(self, client):
        """Clinic section should exist."""
        response = client.get('/about/')
        content = response.content.decode().lower()
        assert 'clínica' in content or 'clinic' in content

    def test_clinic_mentions_puerto_morelos(self, client):
        """Clinic section should mention Puerto Morelos."""
        response = client.get('/about/')
        content = response.content.decode().lower()
        assert 'puerto morelos' in content


@pytest.mark.django_db
class TestMissionSection:
    """Test mission/values section."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_mission_section_exists(self, client):
        """Mission section should exist."""
        response = client.get('/about/')
        content = response.content.decode().lower()
        assert ('misión' in content or 'mission' in content or
                'valores' in content or 'values' in content or
                'compromiso' in content or 'commitment' in content)


@pytest.mark.django_db
class TestCertificationsSection:
    """Test certifications section."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_certifications_section_exists(self, client):
        """Certifications section should exist or be placeholder."""
        response = client.get('/about/')
        content = response.content.decode().lower()
        # May show as placeholder or actual content
        assert ('certificación' in content or 'certification' in content or
                'licencia' in content or 'license' in content or
                'profesional' in content or 'professional' in content or
                'calificación' in content or 'qualification' in content)


@pytest.mark.django_db
class TestPhotoGallery:
    """Test photo gallery section."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_gallery_section_exists(self, client):
        """Gallery section or images should exist."""
        response = client.get('/about/')
        content = response.content.decode()
        # Should have images or gallery placeholder
        assert '<img' in content or 'galería' in content.lower() or 'gallery' in content.lower()

    def test_images_have_alt_attributes(self, client):
        """Images should have alt attributes."""
        response = client.get('/about/')
        content = response.content.decode()
        import re
        img_tags = re.findall(r'<img[^>]+>', content)
        for img in img_tags:
            assert 'alt=' in img, f"Image missing alt: {img}"


@pytest.mark.django_db
class TestCTALinks:
    """Test CTA buttons link correctly."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_has_contact_cta(self, client):
        """About page should have contact CTA."""
        response = client.get('/about/')
        content = response.content.decode().lower()
        assert 'contacto' in content or 'contact' in content or 'cita' in content

    def test_contact_link_works(self, client):
        """Contact link should work."""
        response = client.get('/contact/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestMobileResponsive:
    """Test mobile-responsive layout."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_has_responsive_meta_tag(self, client):
        """Page should have viewport meta tag."""
        response = client.get('/about/')
        content = response.content.decode()
        assert 'width=device-width' in content

    def test_has_responsive_classes(self, client):
        """Page should use responsive Tailwind classes."""
        response = client.get('/about/')
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
        response = client.get('/about/')
        content = response.content.decode()
        assert 'lang="es"' in content or 'Nosotros' in content

    def test_can_switch_to_english(self, client):
        """Should be able to switch to English."""
        response = client.post('/i18n/setlang/', {
            'language': 'en',
            'next': '/about/'
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
        response = client.get('/about/')
        content = response.content.decode()
        assert '<main' in content

    def test_has_heading_hierarchy(self, client):
        """Page should have proper heading hierarchy."""
        response = client.get('/about/')
        content = response.content.decode()
        assert '<h1' in content
        assert '<h2' in content
