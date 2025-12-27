"""Admin registration for Location and ExamRoom."""
from django.contrib import admin

from .models import ExamRoom, Location


class ExamRoomInline(admin.TabularInline):
    """Inline admin for managing exam rooms within a location."""

    model = ExamRoom
    extra = 1
    fields = ['name', 'room_type', 'display_order', 'is_active']
    ordering = ['display_order', 'name']


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    """Admin for Location - clinics will use this directly."""

    list_display = ['name', 'code', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    ordering = ['name']
    inlines = [ExamRoomInline]


@admin.register(ExamRoom)
class ExamRoomAdmin(admin.ModelAdmin):
    """Standalone admin for ExamRoom (mostly accessed via LocationAdmin inline)."""

    list_display = ['name', 'location', 'room_type', 'is_active', 'display_order']
    list_filter = ['location', 'room_type', 'is_active']
    search_fields = ['name', 'location__name']
    ordering = ['location', 'display_order', 'name']
