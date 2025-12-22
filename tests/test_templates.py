"""Tests for base templates and components.

These tests validate that templates meet T-002 requirements:
- Base template has required meta tags, scripts
- Header has navigation and language switcher
- Footer has contact info and social links
- Accessibility requirements are met
- Responsive design elements exist
"""
import re

import pytest
from django.test import Client


@pytest.mark.django_db
class TestBaseTemplate:
    """Test base.html template structure and requirements."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_homepage_renders(self, client):
        """Homepage should render with 200 status and Pet-Friendly branding."""
        response = client.get('/')
        assert response.status_code == 200
        assert 'Pet-Friendly' in response.content.decode()

    def test_base_template_has_meta_tags(self, client):
        """Base template should include required meta tags."""
        response = client.get('/')
        content = response.content.decode()
        assert '<meta charset="UTF-8">' in content or 'charset="utf-8"' in content.lower()
        assert 'viewport' in content

    def test_base_template_includes_htmx(self, client):
        """Base template should include HTMX library."""
        response = client.get('/')
        assert 'htmx' in response.content.decode().lower()

    def test_base_template_includes_alpine(self, client):
        """Base template should include Alpine.js library."""
        response = client.get('/')
        assert 'alpine' in response.content.decode().lower()

    def test_base_template_has_tailwind_classes(self, client):
        """Base template should use Tailwind CSS classes."""
        response = client.get('/')
        content = response.content.decode()
        # Check for common Tailwind patterns
        assert 'class=' in content
        # Check for brand colors or common Tailwind classes
        assert any(cls in content for cls in ['bg-', 'text-', 'flex', 'container'])


@pytest.mark.django_db
class TestHeaderComponent:
    """Test header component requirements."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_header_has_navigation_links(self, client):
        """Header should have navigation links for main pages."""
        response = client.get('/')
        content = response.content.decode()
        # Check for Spanish or English navigation
        assert 'Inicio' in content or 'Home' in content
        assert 'Servicios' in content or 'Services' in content

    def test_header_has_language_switcher(self, client):
        """Header should have a language switcher component."""
        response = client.get('/')
        content = response.content.decode()
        # Look for language switcher form or dropdown
        assert 'set_language' in content or 'language' in content.lower() or 'lang' in content.lower()

    def test_header_has_cart_icon(self, client):
        """Header should have a cart icon for e-commerce."""
        response = client.get('/')
        content = response.content.decode().lower()
        assert 'cart' in content or 'carrito' in content

    def test_header_has_logo(self, client):
        """Header should have the clinic logo or brand name."""
        response = client.get('/')
        content = response.content.decode()
        assert 'Pet-Friendly' in content or 'logo' in content.lower()


@pytest.mark.django_db
class TestFooterComponent:
    """Test footer component requirements."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_footer_has_contact_info(self, client):
        """Footer should display clinic contact information."""
        response = client.get('/')
        content = response.content.decode()
        assert 'Puerto Morelos' in content
        assert '998' in content  # Phone number prefix

    def test_footer_has_social_links(self, client):
        """Footer should have social media links."""
        response = client.get('/')
        content = response.content.decode().lower()
        assert 'instagram' in content or 'facebook' in content

    def test_footer_has_business_hours(self, client):
        """Footer should mention business hours."""
        response = client.get('/')
        content = response.content.decode().lower()
        # Check for hours indicator
        assert 'horario' in content or 'hours' in content or 'lunes' in content or 'monday' in content


@pytest.mark.django_db
class TestAccessibility:
    """Test accessibility requirements per T-002."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_skip_to_content_link_exists(self, client):
        """Page should have a skip-to-content accessibility link."""
        response = client.get('/')
        content = response.content.decode().lower()
        assert 'skip' in content or 'saltar' in content

    def test_images_have_alt_text(self, client):
        """All images should have alt attributes."""
        response = client.get('/')
        content = response.content.decode()
        img_tags = re.findall(r'<img[^>]+>', content)
        for img in img_tags:
            assert 'alt=' in img, f"Image missing alt attribute: {img}"

    def test_html_has_lang_attribute(self, client):
        """HTML tag should have lang attribute for screen readers."""
        response = client.get('/')
        content = response.content.decode()
        assert 'lang=' in content.lower()

    def test_main_content_has_landmark(self, client):
        """Page should have main content landmark for accessibility."""
        response = client.get('/')
        content = response.content.decode().lower()
        assert '<main' in content or 'role="main"' in content


@pytest.mark.django_db
class TestResponsive:
    """Test responsive design elements."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_mobile_menu_button_exists(self, client):
        """Page should have a mobile menu toggle button."""
        response = client.get('/')
        content = response.content.decode()
        assert 'mobileMenuOpen' in content or 'mobile-menu' in content.lower() or 'menuOpen' in content

    def test_viewport_meta_tag(self, client):
        """Page should have viewport meta tag for responsive design."""
        response = client.get('/')
        content = response.content.decode()
        assert 'width=device-width' in content

    def test_responsive_classes_present(self, client):
        """Page should use responsive Tailwind classes."""
        response = client.get('/')
        content = response.content.decode()
        # Check for responsive breakpoint classes
        assert any(bp in content for bp in ['sm:', 'md:', 'lg:', 'xl:'])


@pytest.mark.django_db
class TestFlashMessages:
    """Test flash message component."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_messages_component_included(self, client):
        """Base template should include messages component."""
        response = client.get('/')
        content = response.content.decode()
        # Check for messages block or include
        assert 'messages' in content.lower()


@pytest.mark.django_db
class TestLoadingSpinner:
    """Test HTMX loading spinner."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_htmx_indicator_exists(self, client):
        """Page should have HTMX loading indicator."""
        response = client.get('/')
        content = response.content.decode()
        # Check for htmx indicator class or element
        assert 'htmx-indicator' in content or 'hx-indicator' in content.lower() or 'loading' in content.lower()
