"""Admin configuration for error tracking."""
from django.contrib import admin
from django.db.models import Count
from django.utils import timezone
from django.utils.html import format_html

from .models import ErrorLog, KnownBug


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    """Admin view for error logs."""

    list_display = [
        'created_at',
        'status_code_display',
        'error_type',
        'url_pattern',
        'fingerprint_short',
        'user',
        'ip_address',
    ]
    list_filter = [
        'status_code',
        'error_type',
        'created_at',
    ]
    search_fields = [
        'url_pattern',
        'full_url',
        'fingerprint',
        'exception_message',
        'user__email',
        'ip_address',
    ]
    readonly_fields = [
        'fingerprint',
        'error_type',
        'status_code',
        'url_pattern',
        'full_url',
        'method',
        'user',
        'ip_address',
        'user_agent',
        'request_data',
        'exception_type',
        'exception_message',
        'traceback',
        'created_at',
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    def status_code_display(self, obj):
        """Display status code with color coding."""
        color = 'red' if obj.status_code >= 500 else 'orange'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.status_code
        )
    status_code_display.short_description = 'Status'

    def fingerprint_short(self, obj):
        """Display shortened fingerprint."""
        return obj.fingerprint[:8] + '...'
    fingerprint_short.short_description = 'Fingerprint'

    def has_add_permission(self, request):
        """Disable adding errors manually."""
        return False

    def has_change_permission(self, request, obj=None):
        """Disable editing errors."""
        return False


@admin.register(KnownBug)
class KnownBugAdmin(admin.ModelAdmin):
    """Admin view for known bugs."""

    list_display = [
        'bug_id',
        'title_short',
        'severity_display',
        'status',
        'occurrence_count',
        'github_link',
        'last_occurrence',
    ]
    list_filter = [
        'severity',
        'status',
        'created_at',
    ]
    search_fields = [
        'bug_id',
        'title',
        'description',
        'fingerprint',
    ]
    readonly_fields = [
        'bug_id',
        'fingerprint',
        'github_issue_number',
        'github_issue_url',
        'occurrence_count',
        'last_occurrence',
        'created_at',
        'updated_at',
    ]
    actions = ['mark_resolved', 'mark_wontfix']
    ordering = ['-created_at']

    def title_short(self, obj):
        """Display shortened title."""
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_short.short_description = 'Title'

    def severity_display(self, obj):
        """Display severity with color coding."""
        colors = {
            'critical': 'darkred',
            'high': 'red',
            'medium': 'orange',
            'low': 'gray',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.severity, 'black'),
            obj.severity.upper()
        )
    severity_display.short_description = 'Severity'

    def github_link(self, obj):
        """Display link to GitHub issue."""
        if obj.github_issue_url:
            return format_html(
                '<a href="{}" target="_blank">#{}</a>',
                obj.github_issue_url,
                obj.github_issue_number
            )
        return '-'
    github_link.short_description = 'GitHub'

    @admin.action(description='Mark selected bugs as resolved')
    def mark_resolved(self, request, queryset):
        """Mark selected bugs as resolved."""
        count = queryset.update(
            status='resolved',
            resolved_at=timezone.now()
        )
        self.message_user(request, f'{count} bugs marked as resolved.')

    @admin.action(description="Mark selected bugs as won't fix")
    def mark_wontfix(self, request, queryset):
        """Mark selected bugs as won't fix."""
        count = queryset.update(status='wontfix')
        self.message_user(request, f'{count} bugs marked as won\'t fix.')

    def changelist_view(self, request, extra_context=None):
        """Add dashboard stats to changelist view."""
        extra_context = extra_context or {}

        # Get stats for dashboard
        extra_context['open_bugs'] = KnownBug.objects.filter(status='open').count()
        extra_context['total_errors_today'] = ErrorLog.objects.filter(
            created_at__date=timezone.now().date()
        ).count()
        extra_context['top_errors'] = ErrorLog.objects.values(
            'fingerprint', 'error_type', 'url_pattern'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:5]

        return super().changelist_view(request, extra_context)
