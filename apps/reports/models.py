"""Reports and Analytics models."""
from django.db import models
from django.conf import settings

from apps.core.storage import report_file_path


class ReportDefinition(models.Model):
    """Saved report templates/definitions."""

    REPORT_TYPES = [
        ('financial', 'Financial'),
        ('operational', 'Operational'),
        ('clinical', 'Clinical'),
        ('inventory', 'Inventory'),
        ('marketing', 'Marketing'),
        ('custom', 'Custom'),
    ]

    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    description = models.TextField(blank=True)

    query_config = models.JSONField(default=dict)
    filters = models.JSONField(default=dict)
    columns = models.JSONField(default=list)
    grouping = models.JSONField(default=list)

    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=False)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='report_definitions'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class GeneratedReport(models.Model):
    """Generated report instances."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    definition = models.ForeignKey(
        ReportDefinition,
        on_delete=models.CASCADE,
        related_name='generated_reports'
    )

    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='completed'
    )
    data = models.JSONField(default=dict)
    summary = models.JSONField(default=dict)

    file = models.FileField(upload_to=report_file_path, null=True, blank=True)
    file_format = models.CharField(max_length=10, blank=True)

    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    generated_at = models.DateTimeField(auto_now_add=True)

    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ['-generated_at']

    def __str__(self):
        return f"{self.definition.name} - {self.generated_at.date()}"


class Dashboard(models.Model):
    """Dashboard configurations."""

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dashboards'
    )

    layout = models.JSONField(default=dict)
    is_default = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', 'name']

    def __str__(self):
        return self.name


class DashboardWidget(models.Model):
    """Individual dashboard widgets."""

    WIDGET_TYPES = [
        ('chart', 'Chart'),
        ('metric', 'Single Metric'),
        ('table', 'Data Table'),
        ('list', 'List'),
        ('calendar', 'Calendar'),
        ('map', 'Map'),
    ]

    dashboard = models.ForeignKey(
        Dashboard,
        on_delete=models.CASCADE,
        related_name='widgets'
    )

    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    title = models.CharField(max_length=200)
    config = models.JSONField(default=dict)

    position = models.IntegerField(default=0)
    width = models.IntegerField(default=1)
    height = models.IntegerField(default=1)

    refresh_interval = models.IntegerField(default=0)
    is_visible = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position']

    def __str__(self):
        return f"{self.dashboard.name} - {self.title}"


class ScheduledReport(models.Model):
    """Scheduled report delivery."""

    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
    ]

    definition = models.ForeignKey(
        ReportDefinition,
        on_delete=models.CASCADE,
        related_name='schedules'
    )

    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    day_of_week = models.IntegerField(null=True, blank=True)
    day_of_month = models.IntegerField(null=True, blank=True)
    hour = models.IntegerField(default=8)

    recipients = models.JSONField(default=list)
    file_format = models.CharField(max_length=10, default='pdf')

    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['next_run']

    def __str__(self):
        return f"{self.definition.name} - {self.get_frequency_display()}"


class MetricSnapshot(models.Model):
    """Daily metric snapshots for trend analysis."""

    metric_name = models.CharField(max_length=100)
    metric_value = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateField()

    metadata = models.JSONField(default=dict)
    source = models.CharField(max_length=50, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['metric_name', 'date']
        indexes = [
            models.Index(fields=['metric_name', 'date']),
        ]

    def __str__(self):
        return f"{self.metric_name} - {self.date}: {self.metric_value}"
