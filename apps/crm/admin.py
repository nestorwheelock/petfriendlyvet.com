"""Admin configuration for CRM app."""
from django.contrib import admin
from django.utils.html import format_html

from .models import (
    CustomerTag,
    CustomerSegment,
    OwnerProfile,
    Interaction,
    CustomerNote,
)


@admin.register(CustomerTag)
class CustomerTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color_badge', 'profile_count', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    ordering = ['name']

    @admin.display(description='Color')
    def color_badge(self, obj):
        return format_html(
            '<span style="background-color: {}; padding: 2px 10px; border-radius: 3px;">&nbsp;</span>',
            obj.color
        )

    @admin.display(description='Profiles')
    def profile_count(self, obj):
        return obj.profiles.count()


@admin.register(CustomerSegment)
class CustomerSegmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'updated_at']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    ordering = ['name']

    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Criteria', {
            'fields': ('criteria',)
        }),
    )


class CustomerNoteInline(admin.TabularInline):
    model = CustomerNote
    extra = 0
    readonly_fields = ['author', 'created_at']
    fields = ['content', 'is_pinned', 'author', 'created_at']


class InteractionInline(admin.TabularInline):
    model = Interaction
    extra = 0
    readonly_fields = ['created_at']
    fields = ['interaction_type', 'channel', 'direction', 'subject', 'created_at']
    ordering = ['-created_at']
    max_num = 10


@admin.register(OwnerProfile)
class OwnerProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'preferred_language', 'preferred_contact_method',
        'total_visits', 'total_spent', 'tag_list'
    ]
    list_filter = ['preferred_language', 'preferred_contact_method', 'tags']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'notes']
    raw_id_fields = ['user', 'referred_by']
    filter_horizontal = ['tags']
    inlines = [CustomerNoteInline, InteractionInline]

    fieldsets = (
        (None, {
            'fields': ('user',)
        }),
        ('Preferences', {
            'fields': ('preferred_language', 'preferred_contact_method', 'marketing_preferences')
        }),
        ('Tags & Notes', {
            'fields': ('tags', 'notes')
        }),
        ('Analytics', {
            'fields': (
                'first_visit_date', 'last_visit_date',
                'total_visits', 'total_spent', 'lifetime_value'
            )
        }),
        ('Referral', {
            'fields': ('referred_by', 'referral_source'),
            'classes': ['collapse']
        }),
        ('Social', {
            'fields': ('facebook_url', 'instagram_url'),
            'classes': ['collapse']
        }),
    )

    @admin.display(description='Tags')
    def tag_list(self, obj):
        tags = obj.tags.all()[:3]
        if not tags:
            return '-'
        tag_html = ' '.join([
            f'<span style="background-color: {t.color}; color: white; padding: 2px 6px; border-radius: 3px; margin-right: 3px;">{t.name}</span>'
            for t in tags
        ])
        return format_html(tag_html)


@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'owner_profile', 'interaction_type', 'channel',
        'direction_badge', 'subject', 'created_at'
    ]
    list_filter = ['interaction_type', 'channel', 'direction', 'created_at']
    search_fields = ['owner_profile__user__email', 'subject', 'notes']
    date_hierarchy = 'created_at'
    raw_id_fields = ['owner_profile', 'handled_by']
    ordering = ['-created_at']

    fieldsets = (
        (None, {
            'fields': ('owner_profile', 'interaction_type', 'channel', 'direction')
        }),
        ('Details', {
            'fields': ('subject', 'notes', 'duration_minutes')
        }),
        ('Staff', {
            'fields': ('handled_by',)
        }),
        ('Follow-up', {
            'fields': ('outcome', 'follow_up_required', 'follow_up_date'),
            'classes': ['collapse']
        }),
    )

    @admin.display(description='Direction')
    def direction_badge(self, obj):
        if obj.direction == 'inbound':
            return format_html('<span style="color: #198754;">IN</span>')
        return format_html('<span style="color: #0d6efd;">OUT</span>')


@admin.register(CustomerNote)
class CustomerNoteAdmin(admin.ModelAdmin):
    list_display = ['id', 'owner_profile', 'author', 'is_pinned', 'created_at']
    list_filter = ['is_pinned', 'is_private', 'created_at']
    search_fields = ['owner_profile__user__email', 'content']
    raw_id_fields = ['owner_profile', 'author']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    fieldsets = (
        (None, {
            'fields': ('owner_profile', 'author')
        }),
        ('Note', {
            'fields': ('content', 'is_pinned', 'is_private')
        }),
    )
