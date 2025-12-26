"""WAF database models."""
from django.conf import settings
from django.db import models
from django.utils import timezone


class WAFConfig(models.Model):
    """Global WAF configuration settings."""

    # Rate limiting
    rate_limit_enabled = models.BooleanField(default=True)
    rate_limit_requests = models.PositiveIntegerField(
        default=200,
        help_text="Maximum requests per IP per minute"
    )
    rate_limit_window = models.PositiveIntegerField(
        default=60,
        help_text="Time window in seconds"
    )

    # Banning
    auto_ban_enabled = models.BooleanField(default=True)
    max_strikes = models.PositiveIntegerField(
        default=5,
        help_text="Security events before auto-ban"
    )
    ban_duration = models.PositiveIntegerField(
        default=900,
        help_text="Ban duration in seconds (default 15 min)"
    )

    # Pattern detection
    pattern_detection_enabled = models.BooleanField(default=True)
    block_sql_injection = models.BooleanField(default=True)
    block_xss = models.BooleanField(default=True)
    block_path_traversal = models.BooleanField(default=True)

    # Geo-blocking
    geo_blocking_enabled = models.BooleanField(default=False)

    # Logging
    security_log_path = models.CharField(
        max_length=500,
        default='/var/log/django/security.log',
        help_text="Path for fail2ban-compatible security log"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'WAF Configuration'
        verbose_name_plural = 'WAF Configuration'

    def __str__(self):
        return "WAF Configuration"

    @classmethod
    def get_config(cls):
        """Get or create the singleton WAF config."""
        config, _ = cls.objects.get_or_create(pk=1)
        return config


class BannedIP(models.Model):
    """IP addresses banned by WAF."""

    ip_address = models.GenericIPAddressField(unique=True)
    reason = models.CharField(max_length=200)
    strike_count = models.PositiveIntegerField(default=0)

    # Auto-ban details
    auto_banned = models.BooleanField(default=False)
    banned_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    # Manual ban details
    banned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    permanent = models.BooleanField(default=False)

    # Extra data
    last_request_path = models.CharField(max_length=500, blank=True)
    last_user_agent = models.CharField(max_length=500, blank=True)

    class Meta:
        verbose_name = 'Banned IP'
        verbose_name_plural = 'Banned IPs'
        ordering = ['-banned_at']

    def __str__(self):
        return f"{self.ip_address} ({self.reason})"

    @property
    def is_expired(self):
        """Check if the ban has expired."""
        if self.permanent:
            return False
        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at

    @property
    def is_active(self):
        """Check if the ban is still active."""
        return not self.is_expired


class AllowedCountry(models.Model):
    """Countries allowed when geo-blocking is enabled."""

    country_code = models.CharField(
        max_length=2,
        unique=True,
        help_text="ISO 3166-1 alpha-2 country code (e.g., US, GB)"
    )
    country_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Allowed Country'
        verbose_name_plural = 'Allowed Countries'
        ordering = ['country_name']

    def __str__(self):
        return f"{self.country_name} ({self.country_code})"


class SecurityEvent(models.Model):
    """Security events logged by WAF."""

    EVENT_TYPES = [
        ('failed_login', 'Failed Login'),
        ('invalid_token', 'Invalid Token'),
        ('rate_limit', 'Rate Limit Exceeded'),
        ('sqli', 'SQL Injection Detected'),
        ('xss', 'XSS Detected'),
        ('path_traversal', 'Path Traversal'),
        ('banned_access', 'Banned IP Access'),
        ('geo_blocked', 'Geo-blocked'),
        ('other', 'Other'),
    ]

    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    ip_address = models.GenericIPAddressField()
    path = models.CharField(max_length=500)
    method = models.CharField(max_length=10, default='GET')
    user_agent = models.CharField(max_length=500, blank=True)
    details = models.TextField(blank=True)

    # User if authenticated
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    # Action taken
    action_taken = models.CharField(
        max_length=50,
        default='logged',
        help_text="Action taken (logged, blocked, banned)"
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Security Event'
        verbose_name_plural = 'Security Events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['ip_address', 'created_at']),
            models.Index(fields=['event_type', 'created_at']),
        ]

    def __str__(self):
        return f"{self.event_type}: {self.ip_address} at {self.created_at}"
