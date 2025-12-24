"""Admin configuration for Practice Management app."""
from django.contrib import admin
from django.utils.html import format_html

from .models import (
    StaffProfile,
    Shift,
    TimeEntry,
    ClinicSettings,
    ClinicalNote,
    Task,
)


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'role_badge', 'title', 'phone',
        'can_prescribe', 'can_dispense', 'is_active'
    ]
    list_filter = ['role', 'is_active', 'can_prescribe', 'can_handle_controlled']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'title']
    raw_id_fields = ['user']

    fieldsets = (
        (None, {
            'fields': ('user', 'role', 'title', 'is_active')
        }),
        ('Permissions', {
            'fields': ('can_prescribe', 'can_dispense', 'can_handle_controlled')
        }),
        ('DEA Credentials', {
            'fields': ('dea_number', 'dea_expiration'),
            'classes': ['collapse']
        }),
        ('Contact', {
            'fields': ('phone', 'emergency_phone')
        }),
        ('Employment', {
            'fields': ('hire_date',)
        }),
    )

    @admin.display(description='Role')
    def role_badge(self, obj):
        colors = {
            'veterinarian': '#198754',
            'vet_tech': '#0d6efd',
            'pharmacy_tech': '#6f42c1',
            'receptionist': '#fd7e14',
            'manager': '#20c997',
            'admin': '#dc3545',
        }
        color = colors.get(obj.role, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_role_display()
        )


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = [
        'staff', 'date', 'start_time', 'end_time',
        'duration_display', 'confirmed_badge'
    ]
    list_filter = ['date', 'is_confirmed', 'staff__role']
    search_fields = ['staff__user__first_name', 'staff__user__last_name', 'notes']
    raw_id_fields = ['staff']
    date_hierarchy = 'date'

    @admin.display(description='Duration')
    def duration_display(self, obj):
        from datetime import datetime, timedelta
        start = datetime.combine(obj.date, obj.start_time)
        end = datetime.combine(obj.date, obj.end_time)
        duration = end - start
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        return f"{hours}h {minutes}m"

    @admin.display(description='Confirmed')
    def confirmed_badge(self, obj):
        if obj.is_confirmed:
            return format_html(
                '<span style="color: #198754; font-weight: bold;">Yes</span>'
            )
        return format_html(
            '<span style="color: #dc3545; font-weight: bold;">No</span>'
        )


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = [
        'staff', 'clock_in', 'clock_out', 'break_minutes',
        'hours_display', 'approved_badge'
    ]
    list_filter = ['is_approved', 'staff__role', 'clock_in']
    search_fields = ['staff__user__first_name', 'staff__user__last_name', 'notes']
    raw_id_fields = ['staff', 'shift', 'approved_by']
    date_hierarchy = 'clock_in'

    @admin.display(description='Hours')
    def hours_display(self, obj):
        hours = obj.hours_worked
        if hours == 0:
            return format_html(
                '<span style="color: #ffc107;">In Progress</span>'
            )
        if hours >= 8:
            color = '#198754'
        elif hours >= 4:
            color = '#0d6efd'
        else:
            color = '#fd7e14'
        return format_html(
            '<span style="color: {};">{:.1f}h</span>',
            color, hours
        )

    @admin.display(description='Approved')
    def approved_badge(self, obj):
        if obj.is_approved:
            return format_html(
                '<span style="color: #198754; font-weight: bold;">Yes</span>'
            )
        return format_html(
            '<span style="color: #6c757d;">Pending</span>'
        )


@admin.register(ClinicSettings)
class ClinicSettingsAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'opening_time', 'closing_time']
    search_fields = ['name', 'legal_name', 'email']

    fieldsets = (
        (None, {
            'fields': ('name', 'legal_name', 'tax_id')
        }),
        ('Contact', {
            'fields': ('address', 'phone', 'email', 'website')
        }),
        ('Hours', {
            'fields': ('opening_time', 'closing_time', 'days_open')
        }),
        ('Emergency', {
            'fields': ('emergency_phone', 'emergency_available')
        }),
        ('Social', {
            'fields': ('facebook_url', 'instagram_url', 'google_maps_url'),
            'classes': ['collapse']
        }),
        ('Branding', {
            'fields': ('logo', 'primary_color'),
            'classes': ['collapse']
        }),
    )


@admin.register(ClinicalNote)
class ClinicalNoteAdmin(admin.ModelAdmin):
    list_display = [
        'pet', 'note_type_badge', 'author', 'created_at',
        'confidential_badge', 'locked_badge'
    ]
    list_filter = ['note_type', 'is_confidential', 'is_locked', 'created_at']
    search_fields = ['pet__name', 'author__first_name', 'subjective', 'objective', 'assessment']
    raw_id_fields = ['pet', 'appointment', 'author']
    date_hierarchy = 'created_at'

    fieldsets = (
        (None, {
            'fields': ('pet', 'appointment', 'author', 'note_type')
        }),
        ('SOAP Note', {
            'fields': ('subjective', 'objective', 'assessment', 'plan'),
            'classes': ['collapse']
        }),
        ('Content', {
            'fields': ('content',)
        }),
        ('Settings', {
            'fields': ('is_confidential', 'is_locked', 'locked_at'),
            'classes': ['collapse']
        }),
    )

    @admin.display(description='Type')
    def note_type_badge(self, obj):
        colors = {
            'soap': '#198754',
            'progress': '#0d6efd',
            'procedure': '#6f42c1',
            'lab': '#fd7e14',
            'phone': '#20c997',
            'internal': '#6c757d',
        }
        color = colors.get(obj.note_type, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_note_type_display()
        )

    @admin.display(description='Confidential')
    def confidential_badge(self, obj):
        if obj.is_confidential:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">Yes</span>'
            )
        return format_html('<span style="color: #6c757d;">No</span>')

    @admin.display(description='Locked')
    def locked_badge(self, obj):
        if obj.is_locked:
            return format_html(
                '<span style="color: #6c757d; font-weight: bold;">Locked</span>'
            )
        return format_html('<span style="color: #198754;">Editable</span>')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'assigned_to', 'priority_badge', 'status_badge',
        'due_date', 'created_at'
    ]
    list_filter = ['status', 'priority', 'created_at', 'assigned_to']
    search_fields = ['title', 'description', 'assigned_to__user__first_name']
    raw_id_fields = ['assigned_to', 'created_by', 'pet', 'appointment']
    date_hierarchy = 'created_at'

    fieldsets = (
        (None, {
            'fields': ('title', 'description')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'created_by', 'priority', 'status')
        }),
        ('Dates', {
            'fields': ('due_date', 'completed_at')
        }),
        ('Related', {
            'fields': ('pet', 'appointment'),
            'classes': ['collapse']
        }),
    )

    @admin.display(description='Priority')
    def priority_badge(self, obj):
        colors = {
            'low': '#6c757d',
            'medium': '#0d6efd',
            'high': '#fd7e14',
            'urgent': '#dc3545',
        }
        color = colors.get(obj.priority, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_priority_display()
        )

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'in_progress': '#0d6efd',
            'completed': '#198754',
            'cancelled': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
