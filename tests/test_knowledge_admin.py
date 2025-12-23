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


@pytest.mark.django_db
class TestKnowledgeAdminSaveModel:
    """Test admin save_model methods."""

    @pytest.fixture
    def admin_user(self):
        return User.objects.create_superuser(
            username='adminsave',
            email='adminsave@example.com',
            password='adminpass123'
        )

    @pytest.fixture
    def category(self):
        from apps.knowledge.models import KnowledgeCategory
        return KnowledgeCategory.objects.create(
            name='Save Test', name_es='Prueba Guardar',
            name_en='Save Test', slug='save-test'
        )

    def test_article_save_sets_created_by(self, admin_user, category):
        """save_model should set created_by on new articles."""
        from apps.knowledge.models import KnowledgeArticle
        from django.contrib.admin.sites import AdminSite
        from apps.knowledge.admin import KnowledgeArticleAdmin

        # Create article without pk (new article)
        article = KnowledgeArticle(
            category=category,
            slug='new-article-test',
            title='',
            title_es='Nuevo Artículo',
            title_en='New Article',
            content='',
            content_es='Contenido en español',
            content_en='Content in English'
        )

        admin_site = AdminSite()
        article_admin = KnowledgeArticleAdmin(KnowledgeArticle, admin_site)

        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.post('/admin/')
        request.user = admin_user

        # save_model should set created_by
        article_admin.save_model(request, article, form=None, change=False)

        # Check created_by was set
        assert article.created_by == admin_user
        # Title should be set from Spanish translation
        assert article.title == 'Nuevo Artículo'
        assert article.content == 'Contenido en español'

    def test_article_save_fills_title_from_translation(self, client, admin_user, category):
        """save_model should fill title from translations if empty."""
        from apps.knowledge.models import KnowledgeArticle
        from django.contrib.admin.sites import AdminSite
        from apps.knowledge.admin import KnowledgeArticleAdmin

        # Create article without title
        article = KnowledgeArticle(
            category=category,
            slug='fill-title',
            title='',  # Empty
            title_es='Título en Español',
            title_en='Title in English',
            content='',  # Empty
            content_es='Contenido',
            content_en='Content'
        )

        # Simulate admin save
        admin_site = AdminSite()
        article_admin = KnowledgeArticleAdmin(KnowledgeArticle, admin_site)

        # Create mock request
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.post('/admin/')
        request.user = admin_user

        # Call save_model
        article_admin.save_model(request, article, form=None, change=False)

        # Verify title was filled from translation
        assert article.title == 'Título en Español'
        assert article.content == 'Contenido'

    def test_article_save_uses_english_if_spanish_empty(self, client, admin_user, category):
        """save_model should use English if Spanish is empty."""
        from apps.knowledge.models import KnowledgeArticle
        from django.contrib.admin.sites import AdminSite
        from apps.knowledge.admin import KnowledgeArticleAdmin

        article = KnowledgeArticle(
            category=category,
            slug='english-only',
            title='',
            title_es='',  # Empty Spanish
            title_en='English Title',
            content='',
            content_es='',
            content_en='English Content'
        )

        admin_site = AdminSite()
        article_admin = KnowledgeArticleAdmin(KnowledgeArticle, admin_site)

        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.post('/admin/')
        request.user = admin_user

        article_admin.save_model(request, article, form=None, change=False)

        assert article.title == 'English Title'
        assert article.content == 'English Content'

    def test_faq_save_fills_question_from_translation(self, category):
        """FAQ save_model should fill question from translations."""
        from apps.knowledge.models import FAQ
        from django.contrib.admin.sites import AdminSite
        from apps.knowledge.admin import FAQAdmin

        faq = FAQ(
            category=category,
            question='',  # Empty
            question_es='¿Cuál es su horario?',
            question_en='What are your hours?',
            answer='',  # Empty
            answer_es='9am-8pm',
            answer_en='9am-8pm'
        )

        admin_site = AdminSite()
        faq_admin = FAQAdmin(FAQ, admin_site)

        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.post('/admin/')

        faq_admin.save_model(request, faq, form=None, change=False)

        assert faq.question == '¿Cuál es su horario?'
        assert faq.answer == '9am-8pm'

    def test_faq_save_uses_english_if_spanish_empty(self, category):
        """FAQ save_model should use English if Spanish is empty."""
        from apps.knowledge.models import FAQ
        from django.contrib.admin.sites import AdminSite
        from apps.knowledge.admin import FAQAdmin

        faq = FAQ(
            category=category,
            question='',
            question_es='',
            question_en='What services do you offer?',
            answer='',
            answer_es='',
            answer_en='Full veterinary care'
        )

        admin_site = AdminSite()
        faq_admin = FAQAdmin(FAQ, admin_site)

        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.post('/admin/')

        faq_admin.save_model(request, faq, form=None, change=False)

        assert faq.question == 'What services do you offer?'
        assert faq.answer == 'Full veterinary care'

    def test_article_save_keeps_existing_title(self, admin_user, category):
        """save_model should not overwrite existing title."""
        from apps.knowledge.models import KnowledgeArticle
        from django.contrib.admin.sites import AdminSite
        from apps.knowledge.admin import KnowledgeArticleAdmin

        # Article with title already set
        article = KnowledgeArticle(
            category=category,
            slug='existing-title',
            title='Existing Title',  # Already set
            title_es='Título en Español',
            title_en='Title in English',
            content='Existing Content',  # Already set
            content_es='Contenido',
            content_en='Content'
        )

        admin_site = AdminSite()
        article_admin = KnowledgeArticleAdmin(KnowledgeArticle, admin_site)

        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.post('/admin/')
        request.user = admin_user

        article_admin.save_model(request, article, form=None, change=False)

        # Should keep existing values
        assert article.title == 'Existing Title'
        assert article.content == 'Existing Content'

    def test_article_save_existing_keeps_created_by(self, admin_user, category):
        """save_model should not change created_by on existing articles."""
        from apps.knowledge.models import KnowledgeArticle
        from django.contrib.admin.sites import AdminSite
        from apps.knowledge.admin import KnowledgeArticleAdmin

        # Create article with another user
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123'
        )

        article = KnowledgeArticle.objects.create(
            category=category,
            slug='existing-article',
            title='Existing',
            title_es='Existente',
            title_en='Existing',
            content='Content',
            content_es='Contenido',
            content_en='Content',
            created_by=other_user
        )

        admin_site = AdminSite()
        article_admin = KnowledgeArticleAdmin(KnowledgeArticle, admin_site)

        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.post('/admin/')
        request.user = admin_user

        # change=True means it's an existing article
        article_admin.save_model(request, article, form=None, change=True)

        # created_by should not be changed
        assert article.created_by == other_user

    def test_faq_save_keeps_existing_question(self, category):
        """FAQ save_model should not overwrite existing question."""
        from apps.knowledge.models import FAQ
        from django.contrib.admin.sites import AdminSite
        from apps.knowledge.admin import FAQAdmin

        faq = FAQ(
            category=category,
            question='Existing Question',  # Already set
            question_es='¿Pregunta en español?',
            question_en='Question in English?',
            answer='Existing Answer',  # Already set
            answer_es='Respuesta',
            answer_en='Answer'
        )

        admin_site = AdminSite()
        faq_admin = FAQAdmin(FAQ, admin_site)

        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.post('/admin/')

        faq_admin.save_model(request, faq, form=None, change=False)

        # Should keep existing values
        assert faq.question == 'Existing Question'
        assert faq.answer == 'Existing Answer'


@pytest.mark.django_db
class TestKnowledgeAdminDisplayMethods:
    """Test admin display helper methods."""

    @pytest.fixture
    def category(self):
        from apps.knowledge.models import KnowledgeCategory
        return KnowledgeCategory.objects.create(
            name='Display Test', name_es='Prueba Display',
            name_en='Display Test', slug='display-test'
        )

    def test_article_version_count_display(self, category):
        """version_count should display formatted version count."""
        from apps.knowledge.models import KnowledgeArticle
        from django.contrib.admin.sites import AdminSite
        from apps.knowledge.admin import KnowledgeArticleAdmin

        article = KnowledgeArticle.objects.create(
            category=category,
            title='Version Display Test',
            title_es='Test',
            title_en='Test',
            content='Content',
            content_es='Contenido',
            content_en='Content',
            slug='version-display'
        )

        admin_site = AdminSite()
        article_admin = KnowledgeArticleAdmin(KnowledgeArticle, admin_site)

        result = article_admin.version_count(article)
        assert 'v1' in result

    def test_faq_question_short_truncates(self, category):
        """question_short should truncate long questions."""
        from apps.knowledge.models import FAQ
        from django.contrib.admin.sites import AdminSite
        from apps.knowledge.admin import FAQAdmin

        long_question = 'This is a very long question that should be truncated because it exceeds fifty characters'
        faq = FAQ.objects.create(
            category=category,
            question=long_question,
            question_es=long_question,
            question_en=long_question,
            answer='Short answer',
            answer_es='Respuesta corta',
            answer_en='Short answer'
        )

        admin_site = AdminSite()
        faq_admin = FAQAdmin(FAQ, admin_site)

        result = faq_admin.question_short(faq)
        assert len(result) == 53  # 50 chars + '...'
        assert result.endswith('...')

    def test_faq_question_short_no_truncate(self, category):
        """question_short should not truncate short questions."""
        from apps.knowledge.models import FAQ
        from django.contrib.admin.sites import AdminSite
        from apps.knowledge.admin import FAQAdmin

        short_question = 'Short question?'
        faq = FAQ.objects.create(
            category=category,
            question=short_question,
            question_es=short_question,
            question_en=short_question,
            answer='Answer',
            answer_es='Respuesta',
            answer_en='Answer'
        )

        admin_site = AdminSite()
        faq_admin = FAQAdmin(FAQ, admin_site)

        result = faq_admin.question_short(faq)
        assert result == short_question
        assert '...' not in result
