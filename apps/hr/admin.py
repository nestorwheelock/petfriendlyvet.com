"""Admin configuration for HR module."""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Department, Employee, Position, TimeEntry, Shift


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'parent', 'manager', 'is_active']
    list_filter = ['is_active', 'parent']
    search_fields = ['name', 'code', 'description']
    ordering = ['name']


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ['title', 'code', 'department', 'is_exempt', 'is_active']
    list_filter = ['is_active', 'is_exempt', 'department']
    search_fields = ['title', 'code', 'description']
    ordering = ['title']


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'user', 'department', 'position', 'status', 'hire_date']
    list_filter = ['status', 'employment_type', 'department', 'position']
    search_fields = ['employee_id', 'user__email', 'user__first_name', 'user__last_name']
    ordering = ['employee_id']
    raw_id_fields = ['user', 'manager']


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ['person', 'date', 'clock_in', 'clock_out', 'hours_worked', 'is_approved']
    list_filter = ['is_approved', 'approval_status', 'date']
    search_fields = ['person__email', 'person__first_name', 'person__last_name']
    date_hierarchy = 'date'
    ordering = ['-date', '-clock_in']
    raw_id_fields = ['person', 'approved_by']


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ['person', 'date', 'start_time', 'end_time', 'shift_type', 'status']
    list_filter = ['status', 'shift_type', 'department', 'date']
    search_fields = ['person__email', 'person__first_name', 'person__last_name']
    date_hierarchy = 'date'
    ordering = ['date', 'start_time']
    raw_id_fields = ['person']
