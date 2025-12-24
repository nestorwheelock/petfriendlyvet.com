"""Admin configuration for Reports & Analytics app."""
from django.contrib import admin
from django.utils.html import format_html

from .models import (
    ReportDefinition,
    GeneratedReport,
    Dashboard,
    DashboardWidget,
    ScheduledReport,
    MetricSnapshot,
)


class DashboardWidgetInline(admin.TabularInline):
    model = DashboardWidget
    extra = 0
    fields = ['widget_type', 'title', 'position', 'width', 'height', 'is_visible']


@admin.register(ReportDefinition)
class ReportDefinitionAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'type_badge', 'created_by', 'is_active', 'is_public', 'created_at'
    ]
    list_filter = ['report_type', 'is_active', 'is_public']
    search_fields = ['name', 'description']
    raw_id_fields = ['created_by']

    fieldsets = (
        (None, {
            'fields': ('name', 'report_type', 'description')
        }),
        ('Configuration', {
            'fields': ('query_config', 'filters', 'columns', 'grouping'),
            'classes': ['collapse']
        }),
        ('Settings', {
            'fields': ('is_active', 'is_public', 'created_by')
        }),
    )

    @admin.display(description='Type')
    def type_badge(self, obj):
        colors = {
            'financial': '#198754',
            'operational': '#0d6efd',
            'clinical': '#6f42c1',
            'inventory': '#fd7e14',
            'marketing': '#20c997',
            'custom': '#6c757d',
        }
        color = colors.get(obj.report_type, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_report_type_display()
        )


@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    list_display = [
        'definition', 'status_badge', 'period_display',
        'generated_by', 'generated_at'
    ]
    list_filter = ['status', 'definition__report_type', 'generated_at']
    search_fields = ['definition__name']
    raw_id_fields = ['definition', 'generated_by']
    date_hierarchy = 'generated_at'

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'processing': '#0d6efd',
            'completed': '#198754',
            'failed': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )

    @admin.display(description='Period')
    def period_display(self, obj):
        if obj.period_start and obj.period_end:
            return f"{obj.period_start} to {obj.period_end}"
        return '-'


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'widget_count', 'is_default', 'is_public', 'updated_at']
    list_filter = ['is_default', 'is_public']
    search_fields = ['name', 'owner__email']
    raw_id_fields = ['owner']
    inlines = [DashboardWidgetInline]

    @admin.display(description='Widgets')
    def widget_count(self, obj):
        return obj.widgets.count()


@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'dashboard', 'type_badge', 'position', 'is_visible'
    ]
    list_filter = ['widget_type', 'is_visible', 'dashboard']
    search_fields = ['title', 'dashboard__name']
    raw_id_fields = ['dashboard']

    @admin.display(description='Type')
    def type_badge(self, obj):
        colors = {
            'chart': '#0d6efd',
            'metric': '#198754',
            'table': '#6c757d',
            'list': '#fd7e14',
            'calendar': '#6f42c1',
            'map': '#20c997',
        }
        color = colors.get(obj.widget_type, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_widget_type_display()
        )


@admin.register(ScheduledReport)
class ScheduledReportAdmin(admin.ModelAdmin):
    list_display = [
        'definition', 'frequency_badge', 'recipient_count',
        'is_active', 'last_run', 'next_run'
    ]
    list_filter = ['frequency', 'is_active']
    search_fields = ['definition__name']
    raw_id_fields = ['definition']

    @admin.display(description='Frequency')
    def frequency_badge(self, obj):
        colors = {
            'daily': '#dc3545',
            'weekly': '#fd7e14',
            'monthly': '#0d6efd',
            'quarterly': '#198754',
        }
        color = colors.get(obj.frequency, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_frequency_display()
        )

    @admin.display(description='Recipients')
    def recipient_count(self, obj):
        return len(obj.recipients)


@admin.register(MetricSnapshot)
class MetricSnapshotAdmin(admin.ModelAdmin):
    list_display = ['metric_name', 'metric_value', 'date', 'source']
    list_filter = ['metric_name', 'source', 'date']
    search_fields = ['metric_name']
    date_hierarchy = 'date'
