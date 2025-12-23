"""Models for error tracking and bug management."""
from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel, SoftDeleteModel


class ErrorLog(TimeStampedModel):
    """Captures all 4xx/5xx errors for analysis and bug detection."""

    fingerprint = models.CharField(max_length=64, db_index=True)
    error_type = models.CharField(max_length=50)
    status_code = models.IntegerField()
    url_pattern = models.CharField(max_length=500)
    full_url = models.URLField(max_length=2000)
    method = models.CharField(max_length=10)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='error_logs',
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    request_data = models.JSONField(default=dict, blank=True)
    exception_type = models.CharField(max_length=200, blank=True)
    exception_message = models.TextField(blank=True)
    traceback = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Error Log'
        verbose_name_plural = 'Error Logs'
        indexes = [
            models.Index(fields=['fingerprint', 'created_at']),
            models.Index(fields=['status_code', 'created_at']),
        ]

    def __str__(self):
        return f"[{self.status_code}] {self.error_type} - {self.url_pattern}"


SEVERITY_CHOICES = [
    ('critical', 'Critical'),
    ('high', 'High'),
    ('medium', 'Medium'),
    ('low', 'Low'),
]

STATUS_CHOICES = [
    ('open', 'Open'),
    ('in_progress', 'In Progress'),
    ('resolved', 'Resolved'),
    ('wontfix', "Won't Fix"),
]


class KnownBug(TimeStampedModel, SoftDeleteModel):
    """Links error fingerprints to tracked bugs with GitHub integration."""

    bug_id = models.CharField(max_length=10, unique=True)
    fingerprint = models.CharField(max_length=64, unique=True, db_index=True)
    github_issue_number = models.IntegerField(null=True, blank=True)
    github_issue_url = models.URLField(blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    occurrence_count = models.IntegerField(default=1)
    last_occurrence = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Known Bug'
        verbose_name_plural = 'Known Bugs'

    def __str__(self):
        return f"{self.bug_id}: {self.title}"
