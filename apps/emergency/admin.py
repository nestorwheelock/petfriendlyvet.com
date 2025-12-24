"""Admin configuration for emergency services app."""
from django.contrib import admin
from django.utils.html import format_html

from .models import (
    EmergencySymptom,
    EmergencyContact,
    OnCallSchedule,
    EmergencyReferral,
    EmergencyFirstAid,
)


@admin.register(EmergencySymptom)
class EmergencySymptomAdmin(admin.ModelAdmin):
    list_display = ['keyword', 'severity', 'species_display', 'is_active']
    list_filter = ['severity', 'is_active']
    search_fields = ['keyword', 'description']
    ordering = ['severity', 'keyword']

    fieldsets = (
        (None, {
            'fields': ('keyword', 'severity', 'description')
        }),
        ('Keywords', {
            'fields': ('keywords_es', 'keywords_en', 'species')
        }),
        ('Triage', {
            'fields': ('follow_up_questions', 'first_aid_instructions', 'warning_signs')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

    @admin.display(description='Species')
    def species_display(self, obj):
        if not obj.species:
            return 'All'
        return ', '.join(obj.species[:3])


@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'pet_species', 'severity_badge', 'status_badge',
        'channel', 'created_at'
    ]
    list_filter = ['severity', 'status', 'channel', 'created_at']
    search_fields = ['phone', 'reported_symptoms', 'owner__email']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    raw_id_fields = ['owner', 'pet', 'handled_by', 'appointment']

    fieldsets = (
        (None, {
            'fields': ('owner', 'pet', 'phone', 'channel')
        }),
        ('Emergency Details', {
            'fields': ('reported_symptoms', 'pet_species', 'pet_age')
        }),
        ('Triage', {
            'fields': ('severity', 'triage_notes', 'ai_assessment')
        }),
        ('Status', {
            'fields': ('status', 'handled_by', 'response_time_seconds')
        }),
        ('Resolution', {
            'fields': ('resolution', 'outcome', 'appointment'),
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ('created_at', 'escalated_at', 'resolved_at'),
            'classes': ['collapse']
        }),
    )

    readonly_fields = ['created_at', 'escalated_at', 'resolved_at']

    @admin.display(description='Severity')
    def severity_badge(self, obj):
        colors = {
            'critical': '#dc3545',
            'urgent': '#fd7e14',
            'moderate': '#ffc107',
            'low': '#28a745',
        }
        color = colors.get(obj.severity, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.severity or 'Unknown'
        )

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'initiated': '#6c757d',
            'triaging': '#17a2b8',
            'escalated': '#fd7e14',
            'resolved': '#28a745',
            'referred': '#007bff',
            'no_response': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display()
        )


@admin.register(OnCallSchedule)
class OnCallScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'staff', 'date', 'start_time', 'end_time',
        'contact_phone', 'is_active', 'swap_requested'
    ]
    list_filter = ['is_active', 'swap_requested', 'date']
    search_fields = ['staff__user__first_name', 'staff__user__last_name']
    date_hierarchy = 'date'
    ordering = ['date', 'start_time']
    raw_id_fields = ['staff', 'swap_with']

    fieldsets = (
        (None, {
            'fields': ('staff', 'date', 'start_time', 'end_time')
        }),
        ('Contact', {
            'fields': ('contact_phone', 'backup_phone')
        }),
        ('Status', {
            'fields': ('is_active', 'swap_requested', 'swap_with')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ['collapse']
        }),
    )


@admin.register(EmergencyReferral)
class EmergencyReferralAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'phone', 'is_24_hours', 'distance_km',
        'services_count', 'is_active'
    ]
    list_filter = ['is_24_hours', 'is_active']
    search_fields = ['name', 'address', 'phone']
    ordering = ['distance_km', 'name']

    fieldsets = (
        (None, {
            'fields': ('name', 'address', 'phone', 'whatsapp')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude', 'distance_km')
        }),
        ('Hours', {
            'fields': ('is_24_hours', 'hours')
        }),
        ('Services', {
            'fields': ('services', 'species_treated')
        }),
        ('Status', {
            'fields': ('is_active', 'last_verified', 'notes'),
            'classes': ['collapse']
        }),
    )

    @admin.display(description='Services')
    def services_count(self, obj):
        count = len(obj.services) if obj.services else 0
        return f'{count} services'


@admin.register(EmergencyFirstAid)
class EmergencyFirstAidAdmin(admin.ModelAdmin):
    list_display = ['title', 'condition', 'species_display', 'steps_count', 'is_active']
    list_filter = ['is_active']
    search_fields = ['title', 'title_es', 'condition', 'description']
    ordering = ['title']
    filter_horizontal = ['related_symptoms']

    fieldsets = (
        (None, {
            'fields': ('title', 'title_es', 'condition')
        }),
        ('Description', {
            'fields': ('description', 'description_es', 'species')
        }),
        ('Instructions', {
            'fields': ('steps', 'warnings', 'do_not')
        }),
        ('Media', {
            'fields': ('video_url', 'images'),
            'classes': ['collapse']
        }),
        ('Related', {
            'fields': ('related_symptoms',),
            'classes': ['collapse']
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

    @admin.display(description='Species')
    def species_display(self, obj):
        if not obj.species:
            return 'All'
        return ', '.join(obj.species[:3])

    @admin.display(description='Steps')
    def steps_count(self, obj):
        count = len(obj.steps) if obj.steps else 0
        return f'{count} steps'
