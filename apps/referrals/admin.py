"""Admin configuration for referrals app."""
from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Specialist,
    VisitingSchedule,
    Referral,
    ReferralDocument,
    ReferralNote,
    VisitingAppointment,
)


@admin.register(Specialist)
class SpecialistAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'specialty', 'city', 'is_facility', 'is_visiting',
        'is_24_hours', 'is_active', 'total_referrals_display'
    ]
    list_filter = ['specialty', 'is_facility', 'is_visiting', 'is_24_hours', 'is_active', 'city']
    search_fields = ['name', 'clinic_name', 'email', 'phone', 'city']
    ordering = ['name']

    fieldsets = (
        (None, {
            'fields': ('name', 'specialty', 'credentials', 'is_facility', 'clinic_name')
        }),
        ('Contact', {
            'fields': ('email', 'phone', 'fax', 'website')
        }),
        ('Location', {
            'fields': ('address', 'city', 'latitude', 'longitude', 'distance_km')
        }),
        ('Hours & Services', {
            'fields': ('is_24_hours', 'hours', 'services', 'species_treated')
        }),
        ('Visiting Specialist', {
            'fields': ('is_visiting', 'visiting_services', 'equipment_provided',
                      'revenue_share_percent'),
            'classes': ['collapse']
        }),
        ('Relationship', {
            'fields': ('relationship_status', 'referral_agreement', 'referral_instructions')
        }),
        ('Statistics', {
            'fields': ('total_referrals_sent', 'total_referrals_received', 'average_rating'),
            'classes': ['collapse']
        }),
        ('Status', {
            'fields': ('is_active', 'notes')
        }),
    )

    @admin.display(description='Total Referrals')
    def total_referrals_display(self, obj):
        total = obj.total_referrals_sent + obj.total_referrals_received
        return total


class ReferralDocumentInline(admin.TabularInline):
    model = ReferralDocument
    extra = 0
    readonly_fields = ['uploaded_at']


class ReferralNoteInline(admin.TabularInline):
    model = ReferralNote
    extra = 0
    readonly_fields = ['created_at']


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = [
        'referral_number', 'direction', 'pet', 'specialist_display',
        'urgency', 'status', 'created_at'
    ]
    list_filter = ['direction', 'status', 'urgency', 'created_at']
    search_fields = [
        'referral_number', 'pet__name', 'owner__email',
        'specialist__name', 'referring_vet_name', 'referring_clinic'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    inlines = [ReferralDocumentInline, ReferralNoteInline]
    raw_id_fields = ['pet', 'owner', 'specialist', 'referred_by',
                     'invoice', 'referring_professional_account']

    fieldsets = (
        (None, {
            'fields': ('direction', 'referral_number', 'status')
        }),
        ('Patient', {
            'fields': ('pet', 'owner')
        }),
        ('Outbound Referral', {
            'fields': ('specialist',),
            'classes': ['collapse']
        }),
        ('Inbound Referral', {
            'fields': ('referring_vet_name', 'referring_clinic',
                      'referring_contact', 'referring_professional_account'),
            'classes': ['collapse']
        }),
        ('Details', {
            'fields': ('reason', 'clinical_summary', 'urgency', 'requested_services')
        }),
        ('Timeline', {
            'fields': ('sent_at', 'appointment_date', 'seen_at', 'completed_at'),
            'classes': ['collapse']
        }),
        ('Specialist Report', {
            'fields': ('specialist_findings', 'specialist_diagnosis',
                      'specialist_recommendations', 'follow_up_needed',
                      'follow_up_instructions'),
            'classes': ['collapse']
        }),
        ('Outcome', {
            'fields': ('outcome', 'outcome_notes', 'client_satisfaction', 'quality_rating'),
            'classes': ['collapse']
        }),
        ('Staff & Billing', {
            'fields': ('referred_by', 'invoice', 'notes')
        }),
    )

    readonly_fields = ['referral_number', 'created_at', 'updated_at']

    @admin.display(description='Specialist/Referring')
    def specialist_display(self, obj):
        if obj.direction == 'outbound' and obj.specialist:
            return obj.specialist.name
        elif obj.direction == 'inbound':
            return obj.referring_clinic or obj.referring_vet_name
        return '-'


@admin.register(ReferralDocument)
class ReferralDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'referral', 'document_type', 'is_outgoing', 'uploaded_at']
    list_filter = ['document_type', 'is_outgoing']
    search_fields = ['title', 'referral__referral_number']
    raw_id_fields = ['referral', 'uploaded_by']


@admin.register(ReferralNote)
class ReferralNoteAdmin(admin.ModelAdmin):
    list_display = ['referral', 'note_preview', 'is_internal', 'author', 'created_at']
    list_filter = ['is_internal', 'created_at']
    search_fields = ['note', 'referral__referral_number']
    raw_id_fields = ['referral', 'author']

    @admin.display(description='Note')
    def note_preview(self, obj):
        return obj.note[:50] + '...' if len(obj.note) > 50 else obj.note


class VisitingAppointmentInline(admin.TabularInline):
    model = VisitingAppointment
    extra = 0
    raw_id_fields = ['pet', 'owner']
    readonly_fields = ['created_at']


@admin.register(VisitingSchedule)
class VisitingScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'specialist', 'date', 'start_time', 'end_time',
        'appointments_display', 'status'
    ]
    list_filter = ['status', 'date', 'specialist']
    search_fields = ['specialist__name']
    date_hierarchy = 'date'
    ordering = ['date', 'start_time']
    inlines = [VisitingAppointmentInline]
    raw_id_fields = ['specialist']

    @admin.display(description='Appointments')
    def appointments_display(self, obj):
        if obj.max_appointments:
            return f"{obj.appointments_booked}/{obj.max_appointments}"
        return str(obj.appointments_booked)


@admin.register(VisitingAppointment)
class VisitingAppointmentAdmin(admin.ModelAdmin):
    list_display = [
        'pet', 'specialist', 'schedule_date', 'appointment_time',
        'service', 'status'
    ]
    list_filter = ['status', 'specialist', 'schedule__date']
    search_fields = ['pet__name', 'owner__email', 'specialist__name', 'service']
    ordering = ['schedule__date', 'appointment_time']
    raw_id_fields = ['schedule', 'specialist', 'pet', 'owner', 'invoice', 'referral']

    fieldsets = (
        (None, {
            'fields': ('schedule', 'specialist', 'pet', 'owner')
        }),
        ('Appointment', {
            'fields': ('appointment_time', 'duration_minutes', 'service', 'reason', 'status')
        }),
        ('Results', {
            'fields': ('findings', 'diagnosis', 'recommendations',
                      'follow_up_needed', 'follow_up_notes'),
            'classes': ['collapse']
        }),
        ('Documents', {
            'fields': ('report_file', 'images'),
            'classes': ['collapse']
        }),
        ('Billing', {
            'fields': ('fee', 'pet_friendly_share', 'invoice'),
            'classes': ['collapse']
        }),
        ('Related', {
            'fields': ('referral', 'notes')
        }),
    )

    @admin.display(description='Date')
    def schedule_date(self, obj):
        return obj.schedule.date
