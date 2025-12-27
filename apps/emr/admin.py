"""Admin registration for EMR models."""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Encounter, PatientProblem, ClinicalEvent


@admin.register(Encounter)
class EncounterAdmin(admin.ModelAdmin):
    """Admin for Encounter (aggregate root)."""

    list_display = [
        'id',
        'patient',
        'pipeline_state_badge',
        'encounter_type',
        'assigned_vet',
        'room',
        'created_at',
    ]
    list_filter = [
        'pipeline_state',
        'encounter_type',
        'location',
        'created_at',
    ]
    search_fields = [
        'patient__pet__name',
        'patient__patient_number',
        'chief_complaint',
        'room',
    ]
    readonly_fields = [
        'created_at',
        'updated_at',
        'created_by',
    ]
    raw_id_fields = ['patient', 'appointment', 'invoice']
    autocomplete_fields = ['location', 'assigned_vet', 'assigned_tech']
    fieldsets = [
        (_('Location & Patient'), {
            'fields': ('location', 'patient', 'appointment'),
        }),
        (_('Pipeline'), {
            'fields': ('pipeline_state', 'encounter_type', 'chief_complaint'),
        }),
        (_('Assignment'), {
            'fields': ('assigned_vet', 'assigned_tech', 'room'),
        }),
        (_('State Timestamps'), {
            'fields': (
                'scheduled_at',
                'checked_in_at',
                'roomed_at',
                'exam_started_at',
                'exam_ended_at',
                'discharged_at',
            ),
            'classes': ('collapse',),
        }),
        (_('Billing'), {
            'fields': ('invoice',),
            'classes': ('collapse',),
        }),
        (_('Audit'), {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',),
        }),
    ]

    def pipeline_state_badge(self, obj):
        """Display pipeline state with color badge."""
        colors = {
            'scheduled': '#6b7280',     # gray
            'checked_in': '#3b82f6',    # blue
            'roomed': '#8b5cf6',        # purple
            'in_exam': '#f59e0b',       # amber
            'pending_orders': '#f97316', # orange
            'awaiting_results': '#ef4444', # red
            'treatment': '#10b981',     # emerald
            'checkout': '#06b6d4',      # cyan
            'completed': '#22c55e',     # green
            'no_show': '#9ca3af',       # gray
            'cancelled': '#ef4444',     # red
        }
        color = colors.get(obj.pipeline_state, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 4px; font-size: 11px;">{}</span>',
            color,
            obj.get_pipeline_state_display()
        )
    pipeline_state_badge.short_description = _('Status')
    pipeline_state_badge.admin_order_field = 'pipeline_state'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PatientProblem)
class PatientProblemAdmin(admin.ModelAdmin):
    """Admin for PatientProblem (persistent alerts/allergies)."""

    list_display = [
        'name',
        'patient',
        'problem_type',
        'severity_badge',
        'status',
        'is_alert',
        'created_at',
    ]
    list_filter = [
        'problem_type',
        'severity',
        'status',
        'is_alert',
    ]
    search_fields = [
        'name',
        'description',
        'alert_text',
        'patient__pet__name',
        'patient__patient_number',
    ]
    readonly_fields = [
        'created_at',
        'updated_at',
        'created_by',
    ]
    raw_id_fields = ['patient']
    fieldsets = [
        (_('Patient'), {
            'fields': ('patient',),
        }),
        (_('Problem Details'), {
            'fields': ('name', 'description', 'problem_type', 'severity', 'status'),
        }),
        (_('Lifecycle'), {
            'fields': ('onset_date', 'resolved_date'),
        }),
        (_('Alert Display'), {
            'fields': ('is_alert', 'alert_text', 'alert_severity'),
        }),
        (_('Audit'), {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',),
        }),
    ]

    def severity_badge(self, obj):
        """Display severity with color badge."""
        colors = {
            'low': '#22c55e',       # green
            'moderate': '#f59e0b',  # amber
            'high': '#f97316',      # orange
            'critical': '#ef4444',  # red
        }
        color = colors.get(obj.severity, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 4px; font-size: 11px;">{}</span>',
            color,
            obj.get_severity_display()
        )
    severity_badge.short_description = _('Severity')
    severity_badge.admin_order_field = 'severity'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ClinicalEvent)
class ClinicalEventAdmin(admin.ModelAdmin):
    """Admin for ClinicalEvent (append-only timeline).

    IMPORTANT: This is append-only. Content should not be edited.
    Only error correction fields can be modified.
    """

    list_display = [
        'id',
        'event_type',
        'summary_truncated',
        'patient',
        'encounter',
        'occurred_at',
        'error_status',
    ]
    list_filter = [
        'event_type',
        'is_significant',
        'is_entered_in_error',
        'location',
        'occurred_at',
    ]
    search_fields = [
        'summary',
        'patient__pet__name',
        'patient__patient_number',
    ]
    readonly_fields = [
        'patient',
        'encounter',
        'location',
        'event_type',
        'event_subtype',
        'occurred_at',
        'recorded_at',
        'recorded_by',
        'patient_problem',
        'summary',
        'is_significant',
        'superseded_by',
    ]
    raw_id_fields = ['patient', 'encounter']  # location is read-only
    fieldsets = [
        (_('Event Details (Read-Only)'), {
            'fields': (
                'patient',
                'encounter',
                'location',
                'event_type',
                'event_subtype',
                'summary',
                'is_significant',
            ),
        }),
        (_('Timestamps (Read-Only)'), {
            'fields': ('occurred_at', 'recorded_at', 'recorded_by'),
        }),
        (_('Related Records (Read-Only)'), {
            'fields': ('patient_problem',),
            'classes': ('collapse',),
        }),
        (_('Error Correction'), {
            'fields': (
                'is_entered_in_error',
                'error_correction_reason',
                'error_corrected_at',
                'error_corrected_by',
                'superseded_by',
            ),
            'description': _(
                'Medical records are append-only. Use these fields to mark '
                'events as "entered in error" per SYSTEM_CHARTER.md.'
            ),
        }),
    ]

    def summary_truncated(self, obj):
        """Truncate summary for list display."""
        if len(obj.summary) > 60:
            return obj.summary[:60] + '...'
        return obj.summary
    summary_truncated.short_description = _('Summary')

    def error_status(self, obj):
        """Display error status with badge."""
        if obj.is_entered_in_error:
            return format_html(
                '<span style="background-color: #ef4444; color: white; padding: 2px 8px; '
                'border-radius: 4px; font-size: 11px;">Error</span>'
            )
        return format_html(
            '<span style="background-color: #22c55e; color: white; padding: 2px 8px; '
            'border-radius: 4px; font-size: 11px;">Valid</span>'
        )
    error_status.short_description = _('Status')

    def has_delete_permission(self, request, obj=None):
        """Medical records should never be deleted."""
        return False

    def has_add_permission(self, request):
        """ClinicalEvents are created programmatically, not via admin."""
        return False

    def save_model(self, request, obj, form, change):
        """Only allow error correction updates."""
        if change and obj.is_entered_in_error:
            if not obj.error_corrected_by:
                obj.error_corrected_by = request.user
            if not obj.error_corrected_at:
                from django.utils import timezone
                obj.error_corrected_at = timezone.now()
        super().save_model(request, obj, form, change)
