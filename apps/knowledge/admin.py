"""Admin configuration for Knowledge Base."""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import KnowledgeCategory, KnowledgeArticle, FAQ, ArticleVersion


class ArticleVersionInline(admin.TabularInline):
    """Inline display of article versions."""

    model = ArticleVersion
    extra = 0
    readonly_fields = ['version_number', 'content_es', 'content_en',
                       'changed_by', 'changed_at', 'change_summary']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(KnowledgeCategory)
class KnowledgeCategoryAdmin(admin.ModelAdmin):
    """Admin for knowledge categories."""

    list_display = ['name', 'name_es', 'name_en', 'parent', 'order', 'is_active']
    list_filter = ['is_active', 'parent']
    search_fields = ['name', 'name_es', 'name_en', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']

    fieldsets = [
        (None, {
            'fields': ['name', 'slug', 'parent', 'icon', 'order', 'is_active']
        }),
        (_('Translations'), {
            'fields': ['name_es', 'name_en', 'description'],
            'classes': ['collapse']
        }),
    ]


@admin.register(KnowledgeArticle)
class KnowledgeArticleAdmin(admin.ModelAdmin):
    """Admin for knowledge articles."""

    list_display = ['title', 'category', 'is_published', 'priority',
                    'updated_at', 'version_count']
    list_filter = ['is_published', 'category', 'created_at']
    search_fields = ['title', 'title_es', 'title_en', 'content_es',
                     'content_en', 'keywords']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    ordering = ['-priority', '-updated_at']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    inlines = [ArticleVersionInline]

    fieldsets = [
        (None, {
            'fields': ['category', 'slug', 'is_published', 'priority']
        }),
        (_('Spanish Content'), {
            'fields': ['title_es', 'content_es']
        }),
        (_('English Content'), {
            'fields': ['title_en', 'content_en'],
            'classes': ['collapse']
        }),
        (_('AI Configuration'), {
            'fields': ['ai_context', 'keywords'],
            'classes': ['collapse']
        }),
        (_('Metadata'), {
            'fields': ['title', 'content', 'created_by', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    def version_count(self, obj):
        """Display version count."""
        count = obj.versions.count()
        return format_html('<span style="color: #666;">v{}</span>', count)
    version_count.short_description = _('Versions')

    def save_model(self, request, obj, form, change):
        """Set created_by on save."""
        if not obj.pk:
            obj.created_by = request.user
        # Set primary fields from translations if empty
        if not obj.title:
            obj.title = obj.title_es or obj.title_en
        if not obj.content:
            obj.content = obj.content_es or obj.content_en
        super().save_model(request, obj, form, change)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    """Admin for FAQs."""

    list_display = ['question_short', 'category', 'is_featured', 'is_active',
                    'view_count', 'order']
    list_filter = ['is_featured', 'is_active', 'category']
    search_fields = ['question', 'question_es', 'question_en',
                     'answer_es', 'answer_en']
    ordering = ['order']
    list_editable = ['order', 'is_featured', 'is_active']

    fieldsets = [
        (None, {
            'fields': ['category', 'order', 'is_featured', 'is_active']
        }),
        (_('Spanish'), {
            'fields': ['question_es', 'answer_es']
        }),
        (_('English'), {
            'fields': ['question_en', 'answer_en'],
            'classes': ['collapse']
        }),
        (_('Statistics'), {
            'fields': ['question', 'answer', 'view_count'],
            'classes': ['collapse']
        }),
    ]

    def question_short(self, obj):
        """Truncated question for list display."""
        q = obj.question_es or obj.question
        return q[:50] + '...' if len(q) > 50 else q
    question_short.short_description = _('Question')

    def save_model(self, request, obj, form, change):
        """Set primary fields from translations if empty."""
        if not obj.question:
            obj.question = obj.question_es or obj.question_en
        if not obj.answer:
            obj.answer = obj.answer_es or obj.answer_en
        super().save_model(request, obj, form, change)


@admin.register(ArticleVersion)
class ArticleVersionAdmin(admin.ModelAdmin):
    """Admin for article versions (read-only)."""

    list_display = ['article', 'version_number', 'changed_by', 'changed_at',
                    'change_summary']
    list_filter = ['changed_at', 'article']
    search_fields = ['article__title', 'change_summary']
    readonly_fields = ['article', 'version_number', 'content_es', 'content_en',
                       'changed_by', 'changed_at', 'change_summary']
    ordering = ['-changed_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
