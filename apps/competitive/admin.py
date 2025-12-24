"""Admin configuration for Competitive Intelligence app."""
from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Competitor,
    CompetitorService,
    CompetitorReview,
    MarketTrend,
    PriceHistory,
)


class CompetitorServiceInline(admin.TabularInline):
    model = CompetitorService
    extra = 0
    fields = ['name', 'price', 'previous_price', 'our_price', 'price_difference']
    readonly_fields = ['price_difference']


class CompetitorReviewInline(admin.TabularInline):
    model = CompetitorReview
    extra = 0
    fields = ['platform', 'rating', 'review_count', 'captured_at']
    readonly_fields = ['captured_at']


@admin.register(Competitor)
class CompetitorAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'phone', 'distance_km', 'service_count', 'is_active', 'last_updated'
    ]
    list_filter = ['is_active']
    search_fields = ['name', 'address', 'phone']
    ordering = ['distance_km', 'name']
    inlines = [CompetitorServiceInline, CompetitorReviewInline]

    fieldsets = (
        (None, {
            'fields': ('name', 'is_active')
        }),
        ('Contact', {
            'fields': ('address', 'phone', 'email', 'website')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude', 'distance_km', 'google_maps_url')
        }),
        ('Operations', {
            'fields': ('hours', 'services_offered', 'species_treated'),
            'classes': ['collapse']
        }),
        ('Social', {
            'fields': ('facebook_url', 'instagram_url'),
            'classes': ['collapse']
        }),
        ('Analysis', {
            'fields': ('notes', 'strengths', 'weaknesses'),
            'classes': ['collapse']
        }),
    )

    @admin.display(description='Services')
    def service_count(self, obj):
        return obj.services.count()


@admin.register(CompetitorService)
class CompetitorServiceAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'competitor', 'price', 'our_price',
        'price_diff_badge', 'price_updated_at'
    ]
    list_filter = ['competitor', 'category']
    search_fields = ['name', 'competitor__name']
    ordering = ['name']
    raw_id_fields = ['competitor']

    @admin.display(description='Difference')
    def price_diff_badge(self, obj):
        if not obj.price_difference:
            return '-'
        diff = float(obj.price_difference)
        if diff > 0:
            return format_html(
                '<span style="color: #198754;">+${:.2f}</span>',
                diff
            )
        elif diff < 0:
            return format_html(
                '<span style="color: #dc3545;">${:.2f}</span>',
                diff
            )
        return '$0.00'


@admin.register(CompetitorReview)
class CompetitorReviewAdmin(admin.ModelAdmin):
    list_display = [
        'competitor', 'platform', 'rating_badge', 'review_count', 'captured_at'
    ]
    list_filter = ['platform', 'captured_at']
    search_fields = ['competitor__name']
    date_hierarchy = 'captured_at'
    raw_id_fields = ['competitor']

    @admin.display(description='Rating')
    def rating_badge(self, obj):
        rating = float(obj.rating)
        if rating >= 4.5:
            color = '#198754'
        elif rating >= 4.0:
            color = '#0d6efd'
        elif rating >= 3.5:
            color = '#ffc107'
        else:
            color = '#dc3545'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.rating
        )


@admin.register(MarketTrend)
class MarketTrendAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'category', 'impact_badge', 'is_active', 'created_at'
    ]
    list_filter = ['category', 'impact_level', 'is_active']
    search_fields = ['title', 'description']
    filter_horizontal = ['competitors']
    date_hierarchy = 'created_at'

    fieldsets = (
        (None, {
            'fields': ('title', 'category', 'impact_level', 'is_active')
        }),
        ('Details', {
            'fields': ('description', 'source', 'competitors')
        }),
        ('Actions', {
            'fields': ('recommended_action', 'action_taken', 'action_date'),
            'classes': ['collapse']
        }),
    )

    @admin.display(description='Impact')
    def impact_badge(self, obj):
        colors = {
            'low': '#6c757d',
            'medium': '#0d6efd',
            'high': '#fd7e14',
            'critical': '#dc3545',
        }
        color = colors.get(obj.impact_level, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.impact_level.upper()
        )


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ['service', 'price', 'captured_at']
    list_filter = ['captured_at']
    search_fields = ['service__name', 'service__competitor__name']
    date_hierarchy = 'captured_at'
    raw_id_fields = ['service']
