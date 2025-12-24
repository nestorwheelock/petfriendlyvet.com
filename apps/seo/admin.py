"""Admin configuration for SEO and Content Marketing app."""
from django.contrib import admin
from django.utils.html import format_html

from .models import (
    BlogCategory,
    BlogPost,
    LandingPage,
    SEOMetadata,
    ContentCalendarItem,
    Redirect,
)


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent', 'post_count', 'is_active', 'display_order']
    list_filter = ['is_active', 'parent']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['display_order', 'name']

    @admin.display(description='Posts')
    def post_count(self, obj):
        return obj.posts.count()


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'status_badge', 'category', 'author',
        'is_featured', 'view_count', 'published_at'
    ]
    list_filter = ['status', 'category', 'is_featured', 'published_at']
    search_fields = ['title', 'content', 'excerpt']
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ['author']
    date_hierarchy = 'published_at'
    ordering = ['-created_at']

    fieldsets = (
        (None, {
            'fields': ('title', 'title_es', 'slug', 'author', 'category', 'tags')
        }),
        ('Content', {
            'fields': ('excerpt', 'excerpt_es', 'content', 'content_es')
        }),
        ('Media', {
            'fields': ('featured_image', 'featured_image_alt'),
            'classes': ['collapse']
        }),
        ('Status', {
            'fields': ('status', 'is_featured', 'published_at')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords', 'canonical_url'),
            'classes': ['collapse']
        }),
        ('Open Graph', {
            'fields': ('og_title', 'og_description', 'og_image'),
            'classes': ['collapse']
        }),
        ('Analytics', {
            'fields': ('view_count', 'reading_time_minutes'),
            'classes': ['collapse']
        }),
    )

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'draft': '#6c757d',
            'review': '#ffc107',
            'scheduled': '#0d6efd',
            'published': '#198754',
            'archived': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )


@admin.register(LandingPage)
class LandingPageAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'page_type', 'is_active', 'view_count',
        'conversion_count', 'conversion_rate'
    ]
    list_filter = ['page_type', 'is_active', 'is_indexed']
    search_fields = ['title', 'headline', 'content']
    prepopulated_fields = {'slug': ('title',)}

    fieldsets = (
        (None, {
            'fields': ('title', 'title_es', 'slug', 'page_type')
        }),
        ('Content', {
            'fields': ('headline', 'headline_es', 'subheadline', 'content', 'content_es')
        }),
        ('Hero', {
            'fields': ('hero_image', 'cta_text', 'cta_url')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'is_indexed'),
            'classes': ['collapse']
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Analytics', {
            'fields': ('view_count', 'conversion_count'),
            'classes': ['collapse']
        }),
    )

    @admin.display(description='Conv. Rate')
    def conversion_rate(self, obj):
        if obj.view_count > 0:
            rate = (obj.conversion_count / obj.view_count) * 100
            return f"{rate:.1f}%"
        return '-'


@admin.register(SEOMetadata)
class SEOMetadataAdmin(admin.ModelAdmin):
    list_display = ['path', 'title', 'robots', 'priority', 'is_active', 'updated_at']
    list_filter = ['is_active', 'robots']
    search_fields = ['path', 'title', 'description']
    ordering = ['path']

    fieldsets = (
        (None, {
            'fields': ('path', 'is_active')
        }),
        ('Meta Tags', {
            'fields': ('title', 'title_es', 'description', 'description_es', 'keywords')
        }),
        ('Open Graph', {
            'fields': ('og_title', 'og_description', 'og_image'),
            'classes': ['collapse']
        }),
        ('Twitter', {
            'fields': ('twitter_card', 'twitter_title', 'twitter_description'),
            'classes': ['collapse']
        }),
        ('Technical', {
            'fields': ('canonical_url', 'robots', 'priority', 'changefreq'),
            'classes': ['collapse']
        }),
    )


@admin.register(ContentCalendarItem)
class ContentCalendarItemAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'content_type', 'status_badge', 'assigned_to',
        'planned_date', 'published_date'
    ]
    list_filter = ['content_type', 'status', 'assigned_to', 'planned_date']
    search_fields = ['title', 'description']
    raw_id_fields = ['assigned_to', 'blog_post', 'landing_page']
    date_hierarchy = 'planned_date'

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'idea': '#6c757d',
            'planned': '#0d6efd',
            'in_progress': '#ffc107',
            'review': '#fd7e14',
            'scheduled': '#6f42c1',
            'published': '#198754',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )


@admin.register(Redirect)
class RedirectAdmin(admin.ModelAdmin):
    list_display = ['old_path', 'new_path', 'redirect_type', 'hit_count', 'is_active', 'last_hit']
    list_filter = ['redirect_type', 'is_active']
    search_fields = ['old_path', 'new_path']
    ordering = ['old_path']
