"""Audit logging models."""
from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """Tracks user actions for compliance and accountability."""

    ACTION_CHOICES = [
        ('view', 'Viewed'),
        ('create', 'Created'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
        ('export', 'Exported'),
        ('login', 'Logged In'),
        ('logout', 'Logged Out'),
    ]

    SENSITIVITY_CHOICES = [
        ('normal', 'Normal'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    # Who
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
    )

    # What
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    resource_type = models.CharField(max_length=100)
    resource_id = models.CharField(max_length=50, blank=True)
    resource_repr = models.CharField(max_length=200, blank=True)

    # Context
    url_path = models.CharField(max_length=500, blank=True)
    method = models.CharField(max_length=10, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)

    # Metadata
    sensitivity = models.CharField(
        max_length=20,
        choices=SENSITIVITY_CHOICES,
        default='normal',
    )
    extra_data = models.JSONField(default=dict, blank=True)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['resource_type', 'created_at']),
            models.Index(fields=['action', 'created_at']),
        ]

    def __str__(self):
        user_str = self.user.email if self.user else 'Anonymous'
        return f"{user_str} {self.action} {self.resource_type}"
