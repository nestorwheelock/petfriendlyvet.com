"""Tests for SEO and Content Marketing app (TDD first)."""
import pytest
from django.utils import timezone

from apps.accounts.models import User

pytestmark = pytest.mark.django_db


class TestBlogCategoryModel:
    """Tests for BlogCategory model."""

    def test_create_category(self):
        """Test creating a blog category."""
        from apps.seo.models import BlogCategory

        category = BlogCategory.objects.create(
            name='Pet Care Tips',
            description='Helpful tips for pet owners',
        )

        assert category.slug == 'pet-care-tips'
        assert category.is_active is True

    def test_nested_categories(self):
        """Test nested categories."""
        from apps.seo.models import BlogCategory

        parent = BlogCategory.objects.create(name='Health')
        child = BlogCategory.objects.create(
            name='Vaccinations',
            parent=parent,
        )

        assert child.parent == parent
        assert parent.children.first() == child


class TestBlogPostModel:
    """Tests for BlogPost model."""

    def test_create_post(self, user):
        """Test creating a blog post."""
        from apps.seo.models import BlogPost

        post = BlogPost.objects.create(
            title='5 Tips for Pet Health',
            content='Lorem ipsum ' * 100,
            author=user,
            status='draft',
        )

        assert post.slug == '5-tips-for-pet-health'
        assert post.reading_time_minutes >= 1

    def test_post_with_category(self, user):
        """Test post with category."""
        from apps.seo.models import BlogPost, BlogCategory

        category = BlogCategory.objects.create(name='Pet Care')
        post = BlogPost.objects.create(
            title='Caring for Your Dog',
            content='Content here...',
            author=user,
            category=category,
        )

        assert post.category == category
        assert category.posts.first() == post

    def test_featured_post(self, user):
        """Test featured post."""
        from apps.seo.models import BlogPost

        post = BlogPost.objects.create(
            title='Featured Post',
            content='Featured content',
            author=user,
            is_featured=True,
            status='published',
            published_at=timezone.now(),
        )

        assert post.is_featured is True


class TestLandingPageModel:
    """Tests for LandingPage model."""

    def test_create_landing_page(self):
        """Test creating a landing page."""
        from apps.seo.models import LandingPage

        page = LandingPage.objects.create(
            title='Vaccinations in Puerto Morelos',
            slug='vaccinations-puerto-morelos',
            page_type='service',
            headline='Professional Pet Vaccinations',
            content='We offer comprehensive vaccination services...',
        )

        assert page.page_type == 'service'
        assert page.is_active is True


class TestSEOMetadataModel:
    """Tests for SEOMetadata model."""

    def test_create_metadata(self):
        """Test creating SEO metadata."""
        from apps.seo.models import SEOMetadata

        meta = SEOMetadata.objects.create(
            path='/services/',
            title='Veterinary Services - Pet Friendly',
            description='Full range of veterinary services in Puerto Morelos',
        )

        assert meta.path == '/services/'
        assert meta.robots == 'index, follow'


class TestContentCalendarModel:
    """Tests for ContentCalendarItem model."""

    def test_create_calendar_item(self, user):
        """Test creating a calendar item."""
        from apps.seo.models import ContentCalendarItem

        item = ContentCalendarItem.objects.create(
            title='Summer Pet Safety Tips',
            content_type='blog',
            status='planned',
            assigned_to=user,
            planned_date=timezone.now().date(),
        )

        assert item.status == 'planned'
        assert item.content_type == 'blog'


class TestRedirectModel:
    """Tests for Redirect model."""

    def test_create_redirect(self):
        """Test creating a redirect."""
        from apps.seo.models import Redirect

        redirect = Redirect.objects.create(
            old_path='/old-page/',
            new_path='/new-page/',
            redirect_type=301,
        )

        assert redirect.redirect_type == 301
        assert redirect.is_active is True


class TestSEOAITools:
    """Tests for SEO AI tools."""

    def test_get_blog_posts_tool_exists(self):
        """Test get_blog_posts tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('get_blog_posts')
        assert tool is not None

    def test_get_blog_posts(self, user):
        """Test getting blog posts."""
        from apps.ai_assistant.tools import get_blog_posts
        from apps.seo.models import BlogPost

        BlogPost.objects.create(
            title='Test Post',
            content='Content',
            author=user,
            status='published',
            published_at=timezone.now(),
        )

        result = get_blog_posts()

        assert result['success'] is True
        assert result['count'] >= 1

    def test_create_blog_post_tool_exists(self):
        """Test create_blog_post tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('create_blog_post')
        assert tool is not None

    def test_create_blog_post(self, user):
        """Test creating a blog post."""
        from apps.ai_assistant.tools import create_blog_post

        result = create_blog_post(
            title='AI Generated Post',
            content='Content generated by AI',
            author_id=user.id,
        )

        assert result['success'] is True
        assert 'post_id' in result

    def test_get_seo_metadata_tool_exists(self):
        """Test get_seo_metadata tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('get_seo_metadata')
        assert tool is not None

    def test_get_seo_metadata(self):
        """Test getting SEO metadata."""
        from apps.ai_assistant.tools import get_seo_metadata
        from apps.seo.models import SEOMetadata

        SEOMetadata.objects.create(
            path='/test/',
            title='Test Page',
            description='Test description',
        )

        result = get_seo_metadata(path='/test/')

        assert result['success'] is True
        assert result['title'] == 'Test Page'

    def test_update_seo_metadata_tool_exists(self):
        """Test update_seo_metadata tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('update_seo_metadata')
        assert tool is not None

    def test_update_seo_metadata(self):
        """Test updating SEO metadata."""
        from apps.ai_assistant.tools import update_seo_metadata
        from apps.seo.models import SEOMetadata

        SEOMetadata.objects.create(
            path='/about/',
            title='About Us',
            description='Learn about us',
        )

        result = update_seo_metadata(
            path='/about/',
            title='About Pet Friendly Vet',
            description='Learn about our clinic',
        )

        assert result['success'] is True

    def test_suggest_content_tool_exists(self):
        """Test suggest_content tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('suggest_content')
        assert tool is not None


# Fixtures
@pytest.fixture
def user():
    """Create a test user."""
    return User.objects.create_user(
        username='seouser',
        email='seo@example.com',
        password='testpass123',
        first_name='SEO',
        last_name='User',
    )
