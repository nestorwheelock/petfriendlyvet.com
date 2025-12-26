"""Django admin configuration for WAF models."""
from django.contrib import admin
from django.utils.html import format_html

from .models import WAFConfig, BannedIP, AllowedCountry, SecurityEvent


@admin.register(WAFConfig)
class WAFConfigAdmin(admin.ModelAdmin):
    """Admin for WAF configuration singleton."""

    list_display = [
        'rate_limit_enabled',
        'rate_limit_requests',
        'auto_ban_enabled',
        'max_strikes',
        'pattern_detection_enabled',
        'geo_blocking_enabled',
        'updated_at',
    ]

    fieldsets = [
        ('Rate Limiting', {
            'fields': [
                'rate_limit_enabled',
                'rate_limit_requests',
                'rate_limit_window',
            ],
        }),
        ('Auto-Ban Settings', {
            'fields': [
                'auto_ban_enabled',
                'max_strikes',
                'ban_duration',
            ],
        }),
        ('Pattern Detection', {
            'fields': [
                'pattern_detection_enabled',
                'block_sql_injection',
                'block_xss',
                'block_path_traversal',
            ],
        }),
        ('Geo-Blocking', {
            'fields': [
                'geo_blocking_enabled',
            ],
        }),
        ('Logging', {
            'fields': [
                'security_log_path',
            ],
        }),
    ]

    def has_add_permission(self, request):
        """Only allow one WAF config (singleton)."""
        return not WAFConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of WAF config."""
        return False


@admin.register(BannedIP)
class BannedIPAdmin(admin.ModelAdmin):
    """Admin for banned IP addresses."""

    list_display = [
        'ip_address',
        'reason',
        'strike_count',
        'ban_status',
        'auto_banned',
        'banned_at',
        'expires_at',
    ]
    list_filter = [
        'auto_banned',
        'permanent',
        'banned_at',
    ]
    search_fields = [
        'ip_address',
        'reason',
    ]
    readonly_fields = [
        'banned_at',
        'strike_count',
    ]
    ordering = ['-banned_at']

    fieldsets = [
        ('IP Information', {
            'fields': [
                'ip_address',
                'reason',
                'strike_count',
            ],
        }),
        ('Ban Details', {
            'fields': [
                'auto_banned',
                'permanent',
                'banned_at',
                'expires_at',
                'banned_by',
            ],
        }),
        ('Request Details', {
            'fields': [
                'last_request_path',
                'last_user_agent',
            ],
            'classes': ['collapse'],
        }),
    ]

    def ban_status(self, obj):
        """Display ban status with color coding."""
        if obj.is_active:
            if obj.permanent:
                return format_html(
                    '<span style="color: red; font-weight: bold;">PERMANENT</span>'
                )
            return format_html(
                '<span style="color: orange; font-weight: bold;">ACTIVE</span>'
            )
        return format_html(
            '<span style="color: green;">Expired</span>'
        )
    ban_status.short_description = 'Status'

    actions = ['unban_selected', 'make_permanent']

    @admin.action(description='Unban selected IPs')
    def unban_selected(self, request, queryset):
        """Remove selected bans."""
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'Unbanned {count} IP(s).')

    @admin.action(description='Make bans permanent')
    def make_permanent(self, request, queryset):
        """Make selected bans permanent."""
        count = queryset.update(permanent=True, expires_at=None)
        self.message_user(request, f'Made {count} ban(s) permanent.')


@admin.register(AllowedCountry)
class AllowedCountryAdmin(admin.ModelAdmin):
    """Admin for allowed countries in geo-blocking."""

    list_display = [
        'country_code',
        'country_name',
        'created_at',
    ]
    search_fields = [
        'country_code',
        'country_name',
    ]
    ordering = ['country_name']


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    """Admin for security events (read-only log view)."""

    list_display = [
        'created_at',
        'event_type',
        'ip_address',
        'path',
        'method',
        'action_taken',
        'user',
    ]
    list_filter = [
        'event_type',
        'action_taken',
        'method',
        'created_at',
    ]
    search_fields = [
        'ip_address',
        'path',
        'details',
    ]
    readonly_fields = [
        'event_type',
        'ip_address',
        'path',
        'method',
        'user_agent',
        'details',
        'user',
        'action_taken',
        'created_at',
    ]
    ordering = ['-created_at']
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        """Security events are created automatically."""
        return False

    def has_change_permission(self, request, obj=None):
        """Security events should not be modified."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow deletion for cleanup purposes."""
        return True

    actions = ['export_to_csv']

    @admin.action(description='Export selected to CSV')
    def export_to_csv(self, request, queryset):
        """Export selected events to CSV."""
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="security_events.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Timestamp', 'Event Type', 'IP Address', 'Path',
            'Method', 'Action Taken', 'User', 'Details'
        ])

        for event in queryset:
            writer.writerow([
                event.created_at.isoformat(),
                event.event_type,
                event.ip_address,
                event.path,
                event.method,
                event.action_taken,
                event.user.email if event.user else '',
                event.details,
            ])

        return response
