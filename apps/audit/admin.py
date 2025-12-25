"""Audit admin configuration."""
from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for viewing audit logs."""

    list_display = [
        'created_at',
        'user',
        'action',
        'resource_type',
        'resource_id',
        'sensitivity',
        'ip_address',
    ]
    list_filter = [
        'action',
        'sensitivity',
        'resource_type',
        'created_at',
    ]
    search_fields = [
        'user__email',
        'user__first_name',
        'user__last_name',
        'resource_type',
        'resource_id',
        'url_path',
        'ip_address',
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    readonly_fields = [
        'user',
        'action',
        'resource_type',
        'resource_id',
        'resource_repr',
        'url_path',
        'method',
        'ip_address',
        'user_agent',
        'sensitivity',
        'extra_data',
        'created_at',
    ]

    fieldsets = (
        ('Action', {
            'fields': ('user', 'action', 'sensitivity', 'created_at'),
        }),
        ('Resource', {
            'fields': ('resource_type', 'resource_id', 'resource_repr'),
        }),
        ('Request Context', {
            'fields': ('url_path', 'method', 'ip_address', 'user_agent'),
        }),
        ('Extra Data', {
            'fields': ('extra_data',),
            'classes': ('collapse',),
        }),
    )

    def has_add_permission(self, request):
        """Prevent manual creation of audit logs."""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent editing of audit logs."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of audit logs."""
        return False
