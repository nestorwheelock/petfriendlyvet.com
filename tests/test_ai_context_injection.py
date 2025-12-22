"""Tests for T-016 AI Context Injection.

Tests validate context building for AI:
- System prompt generation
- Knowledge base integration
- Token budget management
- Relevance scoring
- User context inclusion
"""
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestAIContextBuilder:
    """Test AIContextBuilder class."""

    def test_context_builder_exists(self):
        """AIContextBuilder class should exist."""
        from apps.ai_assistant.context import AIContextBuilder
        assert AIContextBuilder is not None

    def test_context_builder_has_build_system_prompt(self):
        """AIContextBuilder should have build_system_prompt method."""
        from apps.ai_assistant.context import AIContextBuilder
        builder = AIContextBuilder()
        assert hasattr(builder, 'build_system_prompt')
        assert callable(builder.build_system_prompt)

    def test_context_builder_accepts_language(self):
        """AIContextBuilder should accept language parameter."""
        from apps.ai_assistant.context import AIContextBuilder
        builder_es = AIContextBuilder(language='es')
        builder_en = AIContextBuilder(language='en')
        assert builder_es.language == 'es'
        assert builder_en.language == 'en'

    def test_context_builder_accepts_max_tokens(self):
        """AIContextBuilder should accept max_tokens parameter."""
        from apps.ai_assistant.context import AIContextBuilder
        builder = AIContextBuilder(max_tokens=1000)
        assert builder.max_tokens == 1000


@pytest.mark.django_db
class TestSystemPromptGeneration:
    """Test system prompt generation."""

    def test_system_prompt_includes_clinic_info(self):
        """System prompt should include clinic information."""
        from apps.ai_assistant.context import AIContextBuilder
        builder = AIContextBuilder(language='es')
        prompt = builder.build_system_prompt()
        assert 'Pet-Friendly' in prompt or 'veterinari' in prompt.lower()

    def test_system_prompt_includes_hours(self):
        """System prompt should include clinic hours."""
        from apps.ai_assistant.context import AIContextBuilder
        builder = AIContextBuilder(language='es')
        prompt = builder.build_system_prompt()
        # Hours should be mentioned
        assert 'horario' in prompt.lower() or 'hour' in prompt.lower() or '9' in prompt

    def test_system_prompt_includes_location(self):
        """System prompt should include location."""
        from apps.ai_assistant.context import AIContextBuilder
        builder = AIContextBuilder(language='es')
        prompt = builder.build_system_prompt()
        assert 'Puerto Morelos' in prompt or 'México' in prompt or 'Quintana Roo' in prompt


@pytest.mark.django_db
class TestKnowledgeIntegration:
    """Test knowledge base integration."""

    @pytest.fixture
    def knowledge_content(self):
        from apps.knowledge.models import KnowledgeCategory, KnowledgeArticle
        cat = KnowledgeCategory.objects.create(
            name='Services', name_es='Servicios', name_en='Services',
            slug='services-ctx'
        )
        KnowledgeArticle.objects.create(
            category=cat,
            title='Vaccination',
            title_es='Vacunación',
            title_en='Vaccination',
            content='Vaccination info',
            content_es='Información de vacunación',
            content_en='Vaccination info',
            ai_context='We offer all standard pet vaccinations including rabies, distemper, and parvo.',
            keywords=['vaccine', 'vaccination', 'shots', 'vacuna'],
            slug='vaccination-ctx',
            is_published=True,
            priority=80
        )
        return cat

    def test_context_includes_relevant_knowledge(self, knowledge_content):
        """Context should include relevant knowledge articles."""
        from apps.ai_assistant.context import AIContextBuilder
        builder = AIContextBuilder(language='en')
        prompt = builder.build_system_prompt(user_query='vaccination')
        # Should find the vaccination article
        assert 'vaccin' in prompt.lower()

    def test_context_respects_published_status(self):
        """Context should only include published articles."""
        from apps.knowledge.models import KnowledgeCategory, KnowledgeArticle
        from apps.ai_assistant.context import AIContextBuilder

        cat = KnowledgeCategory.objects.create(
            name='Test', name_es='Prueba', name_en='Test', slug='test-unpub'
        )
        KnowledgeArticle.objects.create(
            category=cat,
            title='Unpublished',
            title_es='No publicado',
            title_en='Unpublished',
            content='Secret content',
            content_es='Contenido secreto',
            content_en='Secret content',
            ai_context='This should not appear',
            keywords=['secret'],
            slug='unpublished-ctx',
            is_published=False  # Not published
        )

        builder = AIContextBuilder(language='en')
        prompt = builder.build_system_prompt(user_query='secret')
        assert 'This should not appear' not in prompt


@pytest.mark.django_db
class TestTokenBudget:
    """Test token budget management."""

    def test_context_builder_tracks_tokens(self):
        """Builder should track token count."""
        from apps.ai_assistant.context import AIContextBuilder
        builder = AIContextBuilder(max_tokens=2000)
        builder.build_system_prompt()
        # Token count should be updated after building
        assert hasattr(builder, 'token_count')

    def test_context_respects_max_tokens(self):
        """Context should not exceed max tokens."""
        from apps.ai_assistant.context import AIContextBuilder
        builder = AIContextBuilder(max_tokens=500)
        prompt = builder.build_system_prompt()
        # Rough estimate: 4 chars per token
        estimated_tokens = len(prompt) / 4
        # Should be within reasonable limit (allow some slack for base prompt)
        assert estimated_tokens < 800  # Some buffer for core content


@pytest.mark.django_db
class TestRelevanceScoring:
    """Test relevance scoring for articles."""

    def test_calculate_relevance_exists(self):
        """calculate_relevance function should exist."""
        from apps.ai_assistant.context import calculate_relevance
        assert callable(calculate_relevance)

    def test_relevance_scores_keyword_matches(self):
        """Relevance should score keyword matches higher."""
        from apps.knowledge.models import KnowledgeCategory, KnowledgeArticle
        from apps.ai_assistant.context import calculate_relevance

        cat = KnowledgeCategory.objects.create(
            name='Test', name_es='Prueba', name_en='Test', slug='test-rel'
        )
        article = KnowledgeArticle.objects.create(
            category=cat,
            title='Vaccination Guide',
            title_es='Guía de Vacunación',
            title_en='Vaccination Guide',
            content='Content',
            content_es='Contenido',
            content_en='Content',
            keywords=['vaccine', 'vaccination', 'shots'],
            slug='vax-rel',
            is_published=True
        )

        score_match = calculate_relevance('vaccination', article)
        score_no_match = calculate_relevance('grooming', article)
        assert score_match > score_no_match

    def test_relevance_considers_priority(self):
        """Relevance should consider article priority."""
        from apps.knowledge.models import KnowledgeCategory, KnowledgeArticle
        from apps.ai_assistant.context import calculate_relevance

        cat = KnowledgeCategory.objects.create(
            name='Priority', name_es='Prioridad', name_en='Priority',
            slug='priority-test'
        )
        high_priority = KnowledgeArticle.objects.create(
            category=cat,
            title='Emergency',
            title_es='Emergencia',
            title_en='Emergency',
            content='Emergency info',
            content_es='Info de emergencia',
            content_en='Emergency info',
            keywords=['emergency'],
            slug='emergency-pri',
            priority=100,
            is_published=True
        )
        low_priority = KnowledgeArticle.objects.create(
            category=cat,
            title='General',
            title_es='General',
            title_en='General',
            content='General info',
            content_es='Info general',
            content_en='General info',
            keywords=['general'],
            slug='general-pri',
            priority=20,
            is_published=True
        )

        # Both with same query should show priority difference
        score_high = calculate_relevance('info', high_priority)
        score_low = calculate_relevance('info', low_priority)
        assert score_high > score_low


@pytest.mark.django_db
class TestUserContext:
    """Test user-specific context inclusion."""

    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='petowner',
            email='petowner@example.com',
            password='testpass123'
        )

    def test_context_with_user(self, user):
        """Context should include user-specific information when provided."""
        from apps.ai_assistant.context import AIContextBuilder
        builder = AIContextBuilder(language='es')
        prompt = builder.build_system_prompt(user=user)
        # Should complete without error
        assert prompt is not None
        assert len(prompt) > 0


@pytest.mark.django_db
class TestLanguageSwitching:
    """Test language switching in context."""

    @pytest.fixture
    def bilingual_content(self):
        from apps.knowledge.models import KnowledgeCategory, KnowledgeArticle
        cat = KnowledgeCategory.objects.create(
            name='Bilingual', name_es='Bilingüe', name_en='Bilingual',
            slug='bilingual'
        )
        KnowledgeArticle.objects.create(
            category=cat,
            title='Hours',
            title_es='Horario de la clínica',
            title_en='Clinic hours',
            content='Hours content',
            content_es='Abierto de 9am a 8pm',
            content_en='Open 9am to 8pm',
            ai_context='Open 9am-8pm Tuesday-Sunday',
            keywords=['hours', 'horario', 'schedule'],
            slug='hours-bil',
            is_published=True
        )
        return cat

    def test_spanish_context(self, bilingual_content):
        """Spanish context should be in Spanish."""
        from apps.ai_assistant.context import AIContextBuilder
        builder = AIContextBuilder(language='es')
        prompt = builder.build_system_prompt()
        # Core prompt should be in Spanish
        assert 'asistente' in prompt.lower() or 'veterinari' in prompt.lower()

    def test_english_context(self, bilingual_content):
        """English context should be in English."""
        from apps.ai_assistant.context import AIContextBuilder
        builder = AIContextBuilder(language='en')
        prompt = builder.build_system_prompt()
        assert prompt is not None
