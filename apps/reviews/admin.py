"""Admin configuration for Reviews and Testimonials app."""
from django.contrib import admin
from django.utils.html import format_html

from .models import Review, ReviewRequest, Testimonial


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'author_display', 'rating_badge', 'platform_badge',
        'status_badge', 'display_on_homepage', 'created_at'
    ]
    list_filter = ['status', 'platform', 'rating', 'display_on_homepage', 'created_at']
    search_fields = ['content', 'title', 'author_name', 'user__email']
    ordering = ['-created_at']
    raw_id_fields = ['user', 'pet', 'responded_by']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('user', 'pet', 'author_name', 'author_location')
        }),
        ('Review', {
            'fields': ('rating', 'title', 'content', 'platform')
        }),
        ('Media', {
            'fields': ('photo', 'video_url'),
            'classes': ['collapse']
        }),
        ('Status', {
            'fields': ('status', 'is_verified_purchase', 'display_on_homepage', 'display_order')
        }),
        ('Response', {
            'fields': ('response', 'response_date', 'responded_by'),
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )

    @admin.display(description='Author')
    def author_display(self, obj):
        return obj.author

    @admin.display(description='Rating')
    def rating_badge(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        if obj.rating >= 4:
            color = '#198754'
        elif obj.rating >= 3:
            color = '#ffc107'
        else:
            color = '#dc3545'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            stars
        )

    @admin.display(description='Platform')
    def platform_badge(self, obj):
        colors = {
            'internal': '#6c757d',
            'google': '#4285f4',
            'facebook': '#1877f2',
            'yelp': '#d32323',
        }
        color = colors.get(obj.platform, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_platform_display()
        )

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'approved': '#198754',
            'featured': '#0d6efd',
            'rejected': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )


@admin.register(ReviewRequest)
class ReviewRequestAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'pet', 'status_badge', 'service_description',
        'sent_at', 'completed_at', 'created_at'
    ]
    list_filter = ['status', 'sent_channel', 'created_at']
    search_fields = ['user__email', 'service_description', 'token']
    ordering = ['-created_at']
    raw_id_fields = ['user', 'pet', 'appointment', 'review']
    readonly_fields = ['token', 'created_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('user', 'pet', 'appointment', 'service_description')
        }),
        ('Status', {
            'fields': ('status', 'sent_at', 'sent_channel', 'completed_at', 'review')
        }),
        ('Token', {
            'fields': ('token',),
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'pending': '#6c757d',
            'sent': '#0d6efd',
            'completed': '#198754',
            'declined': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'author_name', 'short_quote_display', 'is_active',
        'show_on_homepage', 'show_on_services', 'display_order'
    ]
    list_filter = ['is_active', 'show_on_homepage', 'show_on_services']
    search_fields = ['author_name', 'quote', 'short_quote']
    ordering = ['display_order', '-created_at']
    raw_id_fields = ['review']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('review', 'author_name', 'author_title', 'author_photo')
        }),
        ('Content', {
            'fields': ('quote', 'short_quote')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'display_order', 'show_on_homepage', 'show_on_services', 'tags')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )

    @admin.display(description='Quote')
    def short_quote_display(self, obj):
        text = obj.short_quote or obj.quote
        if len(text) > 50:
            return text[:50] + '...'
        return text
