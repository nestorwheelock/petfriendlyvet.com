"""Core admin configuration."""
from django.contrib import admin

from .models import ContactSubmission, ModuleConfig, FeatureFlag


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'status', 'created_at')
    list_filter = ('status', 'subject', 'created_at')
    search_fields = ('name', 'email', 'message')
    readonly_fields = ('ip_address', 'user_agent', 'created_at', 'updated_at')


@admin.register(ModuleConfig)
class ModuleConfigAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'app_name', 'section', 'is_enabled', 'sort_order')
    list_filter = ('is_enabled', 'section')
    search_fields = ('app_name', 'display_name')
    list_editable = ('is_enabled', 'sort_order')
    ordering = ('section', 'sort_order', 'display_name')
    readonly_fields = ('disabled_at', 'disabled_by', 'created_at', 'updated_at')


@admin.register(FeatureFlag)
class FeatureFlagAdmin(admin.ModelAdmin):
    list_display = ('key', 'description', 'is_enabled', 'module')
    list_filter = ('is_enabled', 'module')
    search_fields = ('key', 'description')
    list_editable = ('is_enabled',)
    ordering = ('key',)
    readonly_fields = ('created_at', 'updated_at')
