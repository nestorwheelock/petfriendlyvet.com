"""Knowledge base models for AI context and content management."""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class KnowledgeCategory(models.Model):
    """Category for organizing knowledge base content."""

    name = models.CharField(_('name'), max_length=100)
    name_es = models.CharField(_('name (Spanish)'), max_length=100)
    name_en = models.CharField(_('name (English)'), max_length=100)
    slug = models.SlugField(_('slug'), unique=True)
    description = models.TextField(_('description'), blank=True)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='children',
        verbose_name=_('parent category')
    )
    icon = models.CharField(_('icon'), max_length=50, blank=True)
    order = models.IntegerField(_('order'), default=0)
    is_active = models.BooleanField(_('active'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('knowledge category')
        verbose_name_plural = _('knowledge categories')
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def get_name(self, language='es'):
        """Get name in specified language."""
        return getattr(self, f'name_{language}', self.name_es)


class KnowledgeArticle(models.Model):
    """Knowledge base article for AI context."""

    category = models.ForeignKey(
        KnowledgeCategory,
        on_delete=models.CASCADE,
        related_name='articles',
        verbose_name=_('category')
    )

    # Titles
    title = models.CharField(_('title'), max_length=255)
    title_es = models.CharField(_('title (Spanish)'), max_length=255)
    title_en = models.CharField(_('title (English)'), max_length=255)

    # Content
    content = models.TextField(_('content'))
    content_es = models.TextField(_('content (Spanish)'))
    content_en = models.TextField(_('content (English)'))

    # AI-specific fields
    ai_context = models.TextField(
        _('AI context'),
        blank=True,
        help_text=_('Condensed version for AI context injection')
    )
    keywords = models.JSONField(_('keywords'), default=list)

    # Metadata
    slug = models.SlugField(_('slug'), unique=True)
    is_published = models.BooleanField(_('published'), default=False)
    priority = models.IntegerField(
        _('priority'),
        default=0,
        help_text=_('Higher = more important for AI context')
    )

    # Timestamps and author
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='knowledge_articles',
        verbose_name=_('created by')
    )

    class Meta:
        verbose_name = _('knowledge article')
        verbose_name_plural = _('knowledge articles')
        ordering = ['-priority', '-updated_at']

    def __str__(self):
        return self.title

    def get_title(self, language='es'):
        """Get title in specified language."""
        return getattr(self, f'title_{language}', self.title_es)

    def get_content(self, language='es'):
        """Get content in specified language."""
        return getattr(self, f'content_{language}', self.content_es)

    def save(self, *args, **kwargs):
        """Create version on save if content changed."""
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Create initial version if new
        if is_new and (self.content_es or self.content_en):
            ArticleVersion.objects.create(
                article=self,
                version_number=1,
                content_es=self.content_es,
                content_en=self.content_en,
                changed_by=self.created_by,
                change_summary='Initial version'
            )


class FAQ(models.Model):
    """Frequently asked questions."""

    category = models.ForeignKey(
        KnowledgeCategory,
        on_delete=models.CASCADE,
        related_name='faqs',
        verbose_name=_('category')
    )

    # Question
    question = models.CharField(_('question'), max_length=500)
    question_es = models.CharField(_('question (Spanish)'), max_length=500)
    question_en = models.CharField(_('question (English)'), max_length=500)

    # Answer
    answer = models.TextField(_('answer'))
    answer_es = models.TextField(_('answer (Spanish)'))
    answer_en = models.TextField(_('answer (English)'))

    # Metadata
    order = models.IntegerField(_('order'), default=0)
    view_count = models.IntegerField(_('view count'), default=0)
    is_featured = models.BooleanField(_('featured'), default=False)
    is_active = models.BooleanField(_('active'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('FAQ')
        verbose_name_plural = _('FAQs')
        ordering = ['order']

    def __str__(self):
        return self.question[:50]

    def get_question(self, language='es'):
        """Get question in specified language."""
        return getattr(self, f'question_{language}', self.question_es)

    def get_answer(self, language='es'):
        """Get answer in specified language."""
        return getattr(self, f'answer_{language}', self.answer_es)

    def increment_view_count(self):
        """Increment view count."""
        self.view_count += 1
        self.save(update_fields=['view_count'])


class ArticleVersion(models.Model):
    """Version history for articles."""

    article = models.ForeignKey(
        KnowledgeArticle,
        on_delete=models.CASCADE,
        related_name='versions',
        verbose_name=_('article')
    )
    version_number = models.IntegerField(_('version number'))
    content_es = models.TextField(_('content (Spanish)'))
    content_en = models.TextField(_('content (English)'))
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('changed by')
    )
    changed_at = models.DateTimeField(_('changed at'), auto_now_add=True)
    change_summary = models.CharField(
        _('change summary'),
        max_length=255,
        blank=True
    )

    class Meta:
        verbose_name = _('article version')
        verbose_name_plural = _('article versions')
        ordering = ['-version_number']
        unique_together = ['article', 'version_number']

    def __str__(self):
        return f'{self.article.title} v{self.version_number}'
