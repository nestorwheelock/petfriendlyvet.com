"""Tests for T-014 Knowledge Base Models.

Tests validate knowledge base functionality:
- KnowledgeCategory hierarchy
- KnowledgeArticle with bilingual content
- FAQ model
- ArticleVersion for history
- Search functionality
"""
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestKnowledgeCategory:
    """Test KnowledgeCategory model."""

    def test_category_model_exists(self):
        """KnowledgeCategory model should exist."""
        from apps.knowledge.models import KnowledgeCategory
        assert KnowledgeCategory is not None

    def test_category_has_bilingual_names(self):
        """Category should have name_es and name_en fields."""
        from apps.knowledge.models import KnowledgeCategory
        fields = [f.name for f in KnowledgeCategory._meta.get_fields()]
        assert 'name_es' in fields
        assert 'name_en' in fields

    def test_category_has_slug(self):
        """Category should have slug field."""
        from apps.knowledge.models import KnowledgeCategory
        cat = KnowledgeCategory(
            name='Test',
            name_es='Prueba',
            name_en='Test',
            slug='test'
        )
        assert cat.slug == 'test'

    def test_category_has_parent(self):
        """Category should support parent-child hierarchy."""
        from apps.knowledge.models import KnowledgeCategory
        parent = KnowledgeCategory.objects.create(
            name='Parent',
            name_es='Padre',
            name_en='Parent',
            slug='parent'
        )
        child = KnowledgeCategory.objects.create(
            name='Child',
            name_es='Hijo',
            name_en='Child',
            slug='child',
            parent=parent
        )
        assert child.parent == parent

    def test_category_hierarchy_depth(self):
        """Categories should support multi-level hierarchy."""
        from apps.knowledge.models import KnowledgeCategory
        root = KnowledgeCategory.objects.create(
            name='Root', name_es='Raíz', name_en='Root', slug='root'
        )
        level1 = KnowledgeCategory.objects.create(
            name='Level1', name_es='Nivel1', name_en='Level1',
            slug='level1', parent=root
        )
        level2 = KnowledgeCategory.objects.create(
            name='Level2', name_es='Nivel2', name_en='Level2',
            slug='level2', parent=level1
        )
        assert level2.parent.parent == root


@pytest.mark.django_db
class TestKnowledgeArticle:
    """Test KnowledgeArticle model."""

    @pytest.fixture
    def category(self):
        from apps.knowledge.models import KnowledgeCategory
        return KnowledgeCategory.objects.create(
            name='Test', name_es='Prueba', name_en='Test', slug='test'
        )

    def test_article_model_exists(self):
        """KnowledgeArticle model should exist."""
        from apps.knowledge.models import KnowledgeArticle
        assert KnowledgeArticle is not None

    def test_article_has_bilingual_content(self):
        """Article should have title and content in both languages."""
        from apps.knowledge.models import KnowledgeArticle
        fields = [f.name for f in KnowledgeArticle._meta.get_fields()]
        assert 'title_es' in fields
        assert 'title_en' in fields
        assert 'content_es' in fields
        assert 'content_en' in fields

    def test_article_has_ai_context(self):
        """Article should have ai_context field."""
        from apps.knowledge.models import KnowledgeArticle
        fields = [f.name for f in KnowledgeArticle._meta.get_fields()]
        assert 'ai_context' in fields

    def test_article_has_keywords(self):
        """Article should have keywords JSONField."""
        from apps.knowledge.models import KnowledgeArticle
        fields = [f.name for f in KnowledgeArticle._meta.get_fields()]
        assert 'keywords' in fields

    def test_article_saves_correctly(self, category):
        """Article should save with all required fields."""
        from apps.knowledge.models import KnowledgeArticle
        article = KnowledgeArticle.objects.create(
            category=category,
            title='Test Article',
            title_es='Artículo de Prueba',
            title_en='Test Article',
            content='Content',
            content_es='Contenido',
            content_en='Content',
            slug='test-article',
            is_published=True
        )
        assert article.id is not None
        assert article.category == category


@pytest.mark.django_db
class TestFAQ:
    """Test FAQ model."""

    @pytest.fixture
    def category(self):
        from apps.knowledge.models import KnowledgeCategory
        return KnowledgeCategory.objects.create(
            name='FAQ', name_es='Preguntas', name_en='FAQ', slug='faq'
        )

    def test_faq_model_exists(self):
        """FAQ model should exist."""
        from apps.knowledge.models import FAQ
        assert FAQ is not None

    def test_faq_has_bilingual_qa(self):
        """FAQ should have question and answer in both languages."""
        from apps.knowledge.models import FAQ
        fields = [f.name for f in FAQ._meta.get_fields()]
        assert 'question_es' in fields
        assert 'question_en' in fields
        assert 'answer_es' in fields
        assert 'answer_en' in fields

    def test_faq_has_metadata(self):
        """FAQ should have view_count, is_featured, order."""
        from apps.knowledge.models import FAQ
        fields = [f.name for f in FAQ._meta.get_fields()]
        assert 'view_count' in fields
        assert 'is_featured' in fields
        assert 'order' in fields

    def test_faq_saves_correctly(self, category):
        """FAQ should save with all required fields."""
        from apps.knowledge.models import FAQ
        faq = FAQ.objects.create(
            category=category,
            question='What are your hours?',
            question_es='¿Cuál es su horario?',
            question_en='What are your hours?',
            answer='9am-8pm',
            answer_es='9am-8pm',
            answer_en='9am-8pm'
        )
        assert faq.id is not None


@pytest.mark.django_db
class TestArticleVersion:
    """Test ArticleVersion model."""

    @pytest.fixture
    def article(self):
        from apps.knowledge.models import KnowledgeCategory, KnowledgeArticle
        cat = KnowledgeCategory.objects.create(
            name='Test', name_es='Prueba', name_en='Test', slug='test-version'
        )
        return KnowledgeArticle.objects.create(
            category=cat,
            title='Test',
            title_es='Prueba',
            title_en='Test',
            content='Original',
            content_es='Original',
            content_en='Original',
            slug='test-article-version'
        )

    def test_version_model_exists(self):
        """ArticleVersion model should exist."""
        from apps.knowledge.models import ArticleVersion
        assert ArticleVersion is not None

    def test_version_tracks_changes(self, article):
        """ArticleVersion should track content changes."""
        from apps.knowledge.models import ArticleVersion
        # Version 1 is auto-created by article save, so create version 2
        version = ArticleVersion.objects.create(
            article=article,
            version_number=2,
            content_es='Updated content',
            content_en='Updated content',
            change_summary='Second version'
        )
        assert version.article == article
        assert version.version_number == 2
        # Should have 2 versions now (1 auto-created, 1 manual)
        assert article.versions.count() == 2


@pytest.mark.django_db
class TestKnowledgeSearch:
    """Test knowledge base search functionality."""

    @pytest.fixture
    def populated_knowledge(self):
        from apps.knowledge.models import KnowledgeCategory, KnowledgeArticle
        cat = KnowledgeCategory.objects.create(
            name='Services', name_es='Servicios', name_en='Services',
            slug='services'
        )
        KnowledgeArticle.objects.create(
            category=cat,
            title='Vaccination Services',
            title_es='Servicios de Vacunación',
            title_en='Vaccination Services',
            content='Complete vaccination services',
            content_es='Servicios completos de vacunación',
            content_en='Complete vaccination services',
            slug='vaccination-services',
            keywords=['vaccine', 'vaccination', 'shots'],
            is_published=True
        )
        KnowledgeArticle.objects.create(
            category=cat,
            title='Surgery Services',
            title_es='Servicios de Cirugía',
            title_en='Surgery Services',
            content='Surgical procedures',
            content_es='Procedimientos quirúrgicos',
            content_en='Surgical procedures',
            slug='surgery-services',
            keywords=['surgery', 'operation'],
            is_published=True
        )
        return cat

    def test_search_function_exists(self):
        """search_knowledge_base function should exist."""
        from apps.knowledge.utils import search_knowledge_base
        assert callable(search_knowledge_base)

    def test_search_finds_by_keyword(self, populated_knowledge):
        """Search should find articles by keyword."""
        from apps.knowledge.utils import search_knowledge_base
        results = search_knowledge_base('vaccination', language='en')
        assert len(results) >= 1
        assert 'Vaccination' in results[0].title_en

    def test_search_respects_language(self, populated_knowledge):
        """Search should work in specified language."""
        from apps.knowledge.utils import search_knowledge_base
        results = search_knowledge_base('vacunación', language='es')
        assert len(results) >= 1


@pytest.mark.django_db
class TestGetContextFunction:
    """Test context retrieval for AI."""

    @pytest.fixture
    def knowledge_content(self):
        from apps.knowledge.models import KnowledgeCategory, KnowledgeArticle, FAQ
        cat = KnowledgeCategory.objects.create(
            name='Info', name_es='Info', name_en='Info', slug='info'
        )
        KnowledgeArticle.objects.create(
            category=cat,
            title='Hours',
            title_es='Horario',
            title_en='Hours',
            content='Open 9am-8pm',
            content_es='Abierto 9am-8pm',
            content_en='Open 9am-8pm',
            ai_context='Clinic hours: 9am-8pm, Tuesday-Sunday, closed Monday',
            slug='hours',
            is_published=True,
            priority=10
        )
        FAQ.objects.create(
            category=cat,
            question='What are your hours?',
            question_es='¿Cuál es su horario?',
            question_en='What are your hours?',
            answer='9am to 8pm',
            answer_es='9am a 8pm',
            answer_en='9am to 8pm',
            is_featured=True
        )
        return cat

    def test_get_ai_context_function_exists(self):
        """get_ai_context function should exist."""
        from apps.knowledge.utils import get_ai_context
        assert callable(get_ai_context)

    def test_get_ai_context_returns_relevant_content(self, knowledge_content):
        """get_ai_context should return relevant knowledge."""
        from apps.knowledge.utils import get_ai_context
        context = get_ai_context(['hours', 'schedule'], language='en')
        assert 'hours' in context.lower() or 'open' in context.lower()
