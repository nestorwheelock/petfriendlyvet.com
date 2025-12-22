"""Tests for T-015 Knowledge Admin.

Tests validate admin functionality:
- Admin registration
- Article CRUD views
- Category management
- FAQ management
- Permission checks
"""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


@pytest.mark.django_db
class TestKnowledgeAdminRegistration:
    """Test knowledge models registered in Django admin."""

    def test_category_registered_in_admin(self):
        """KnowledgeCategory should be in admin."""
        from django.contrib import admin
        from apps.knowledge.models import KnowledgeCategory
        assert KnowledgeCategory in admin.site._registry

    def test_article_registered_in_admin(self):
        """KnowledgeArticle should be in admin."""
        from django.contrib import admin
        from apps.knowledge.models import KnowledgeArticle
        assert KnowledgeArticle in admin.site._registry

    def test_faq_registered_in_admin(self):
        """FAQ should be in admin."""
        from django.contrib import admin
        from apps.knowledge.models import FAQ
        assert FAQ in admin.site._registry


@pytest.mark.django_db
class TestKnowledgeAdminPermissions:
    """Test admin access permissions."""

    @pytest.fixture
    def staff_user(self):
        user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='testpass123'
        )
        user.is_staff = True
        user.save()
        return user

    @pytest.fixture
    def regular_user(self):
        return User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='testpass123'
        )

    def test_staff_can_access_admin(self, client, staff_user):
        """Staff user should access admin."""
        client.force_login(staff_user)
        response = client.get('/admin/')
        assert response.status_code == 200

    def test_regular_user_cannot_access_admin(self, client, regular_user):
        """Regular user should not access admin."""
        client.force_login(regular_user)
        response = client.get('/admin/')
        assert response.status_code == 302  # Redirect to login


@pytest.mark.django_db
class TestKnowledgeArticleAdmin:
    """Test article admin functionality."""

    @pytest.fixture
    def admin_user(self):
        return User.objects.create_superuser(
            username='adminuser',
            email='admin@example.com',
            password='adminpass123'
        )

    @pytest.fixture
    def category(self):
        from apps.knowledge.models import KnowledgeCategory
        return KnowledgeCategory.objects.create(
            name='Test', name_es='Prueba', name_en='Test', slug='test'
        )

    @pytest.fixture
    def article(self, category):
        from apps.knowledge.models import KnowledgeArticle
        return KnowledgeArticle.objects.create(
            category=category,
            title='Test Article',
            title_es='Artículo de Prueba',
            title_en='Test Article',
            content='Test content',
            content_es='Contenido de prueba',
            content_en='Test content',
            slug='test-article'
        )

    def test_article_list_view(self, client, admin_user, article):
        """Admin can view article list."""
        client.force_login(admin_user)
        url = reverse('admin:knowledge_knowledgearticle_changelist')
        response = client.get(url)
        assert response.status_code == 200
        assert b'Test Article' in response.content

    def test_article_add_view(self, client, admin_user, category):
        """Admin can access add article view."""
        client.force_login(admin_user)
        url = reverse('admin:knowledge_knowledgearticle_add')
        response = client.get(url)
        assert response.status_code == 200

    def test_article_change_view(self, client, admin_user, article):
        """Admin can access change article view."""
        client.force_login(admin_user)
        url = reverse('admin:knowledge_knowledgearticle_change', args=[article.id])
        response = client.get(url)
        assert response.status_code == 200


@pytest.mark.django_db
class TestKnowledgeCategoryAdmin:
    """Test category admin functionality."""

    @pytest.fixture
    def admin_user(self):
        return User.objects.create_superuser(
            username='admincat',
            email='admincat@example.com',
            password='adminpass123'
        )

    @pytest.fixture
    def category(self):
        from apps.knowledge.models import KnowledgeCategory
        return KnowledgeCategory.objects.create(
            name='Pet Care', name_es='Cuidado de Mascotas',
            name_en='Pet Care', slug='pet-care'
        )

    def test_category_list_view(self, client, admin_user, category):
        """Admin can view category list."""
        client.force_login(admin_user)
        url = reverse('admin:knowledge_knowledgecategory_changelist')
        response = client.get(url)
        assert response.status_code == 200
        assert b'Pet Care' in response.content

    def test_category_hierarchy_display(self, client, admin_user):
        """Categories show parent hierarchy."""
        from apps.knowledge.models import KnowledgeCategory
        parent = KnowledgeCategory.objects.create(
            name='Animals', name_es='Animales', name_en='Animals', slug='animals'
        )
        child = KnowledgeCategory.objects.create(
            name='Dogs', name_es='Perros', name_en='Dogs',
            slug='dogs', parent=parent
        )
        client.force_login(admin_user)
        url = reverse('admin:knowledge_knowledgecategory_changelist')
        response = client.get(url)
        assert response.status_code == 200


@pytest.mark.django_db
class TestFAQAdmin:
    """Test FAQ admin functionality."""

    @pytest.fixture
    def admin_user(self):
        return User.objects.create_superuser(
            username='adminfaq',
            email='adminfaq@example.com',
            password='adminpass123'
        )

    @pytest.fixture
    def category(self):
        from apps.knowledge.models import KnowledgeCategory
        return KnowledgeCategory.objects.create(
            name='FAQ', name_es='Preguntas', name_en='FAQ', slug='faq'
        )

    @pytest.fixture
    def faq(self, category):
        from apps.knowledge.models import FAQ
        return FAQ.objects.create(
            category=category,
            question='What are your hours?',
            question_es='¿Cuál es su horario?',
            question_en='What are your hours?',
            answer='9am-8pm',
            answer_es='9am-8pm',
            answer_en='9am-8pm'
        )

    def test_faq_list_view(self, client, admin_user, faq):
        """Admin can view FAQ list."""
        client.force_login(admin_user)
        url = reverse('admin:knowledge_faq_changelist')
        response = client.get(url)
        assert response.status_code == 200

    def test_faq_add_view(self, client, admin_user, category):
        """Admin can access add FAQ view."""
        client.force_login(admin_user)
        url = reverse('admin:knowledge_faq_add')
        response = client.get(url)
        assert response.status_code == 200


@pytest.mark.django_db
class TestArticleVersionAdmin:
    """Test article version tracking in admin."""

    @pytest.fixture
    def admin_user(self):
        return User.objects.create_superuser(
            username='adminver',
            email='adminver@example.com',
            password='adminpass123'
        )

    @pytest.fixture
    def article(self):
        from apps.knowledge.models import KnowledgeCategory, KnowledgeArticle
        cat = KnowledgeCategory.objects.create(
            name='Test', name_es='Prueba', name_en='Test', slug='test-ver'
        )
        return KnowledgeArticle.objects.create(
            category=cat,
            title='Versioned',
            title_es='Versionado',
            title_en='Versioned',
            content='Content v1',
            content_es='Contenido v1',
            content_en='Content v1',
            slug='versioned-article'
        )

    def test_version_created_on_article_save(self, article):
        """Version should be created when article is saved."""
        assert article.versions.count() == 1
        assert article.versions.first().version_number == 1


@pytest.mark.django_db
class TestAdminSearchAndFiltering:
    """Test admin search and filter functionality."""

    @pytest.fixture
    def admin_user(self):
        return User.objects.create_superuser(
            username='adminsearch',
            email='adminsearch@example.com',
            password='adminpass123'
        )

    @pytest.fixture
    def articles(self):
        from apps.knowledge.models import KnowledgeCategory, KnowledgeArticle
        cat = KnowledgeCategory.objects.create(
            name='Search', name_es='Buscar', name_en='Search', slug='search'
        )
        KnowledgeArticle.objects.create(
            category=cat,
            title='Vaccination Guide',
            title_es='Guía de Vacunación',
            title_en='Vaccination Guide',
            content='About vaccines',
            content_es='Sobre vacunas',
            content_en='About vaccines',
            slug='vaccination-guide',
            is_published=True
        )
        KnowledgeArticle.objects.create(
            category=cat,
            title='Surgery Info',
            title_es='Info de Cirugía',
            title_en='Surgery Info',
            content='About surgery',
            content_es='Sobre cirugía',
            content_en='About surgery',
            slug='surgery-info',
            is_published=False
        )
        return cat

    def test_search_articles_by_title(self, client, admin_user, articles):
        """Admin can search articles by title."""
        client.force_login(admin_user)
        url = reverse('admin:knowledge_knowledgearticle_changelist')
        response = client.get(url, {'q': 'Vaccination'})
        assert response.status_code == 200
        assert b'Vaccination' in response.content

    def test_filter_articles_by_published(self, client, admin_user, articles):
        """Admin can filter by published status."""
        client.force_login(admin_user)
        url = reverse('admin:knowledge_knowledgearticle_changelist')
        response = client.get(url, {'is_published__exact': '1'})
        assert response.status_code == 200
