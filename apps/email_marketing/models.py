"""Email marketing models."""
from django.conf import settings
from django.db import models


class NewsletterSubscription(models.Model):
    """Newsletter subscription."""

    STATUS_CHOICES = [
        ('pending', 'Pending Confirmation'),
        ('active', 'Active'),
        ('unsubscribed', 'Unsubscribed'),
        ('bounced', 'Bounced'),
    ]

    email = models.EmailField(unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='newsletter_subscriptions'
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    confirmation_token = models.CharField(max_length=100, unique=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    preferences = models.JSONField(default=dict, blank=True)
    tags = models.JSONField(default=list, blank=True)

    source = models.CharField(max_length=50, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    unsubscribe_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.confirmation_token:
            import uuid
            self.confirmation_token = str(uuid.uuid4())
        super().save(*args, **kwargs)


class EmailSegment(models.Model):
    """Email list segment for targeting."""

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    rules = models.JSONField(default=list)
    is_dynamic = models.BooleanField(default=True)

    subscriber_count = models.IntegerField(default=0)
    last_computed = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.subscriber_count})"


class EmailTemplate(models.Model):
    """Reusable email template."""

    TEMPLATE_TYPES = [
        ('newsletter', 'Newsletter'),
        ('promotional', 'Promotional'),
        ('transactional', 'Transactional'),
        ('reminder', 'Reminder'),
        ('welcome', 'Welcome'),
    ]

    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES)

    subject = models.CharField(max_length=200)
    subject_es = models.CharField(max_length=200, blank=True)

    html_content = models.TextField()
    html_content_es = models.TextField(blank=True)

    text_content = models.TextField(blank=True)
    text_content_es = models.TextField(blank=True)

    variables = models.JSONField(default=list, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class EmailCampaign(models.Model):
    """Email campaign."""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('cancelled', 'Cancelled'),
    ]

    name = models.CharField(max_length=200)
    template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    subject = models.CharField(max_length=200)
    subject_es = models.CharField(max_length=200, blank=True)

    preview_text = models.CharField(max_length=200, blank=True)
    html_content = models.TextField()
    text_content = models.TextField(blank=True)

    from_name = models.CharField(max_length=100)
    from_email = models.EmailField()
    reply_to = models.EmailField(blank=True)

    segment = models.ForeignKey(
        EmailSegment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    total_recipients = models.IntegerField(default=0)
    total_sent = models.IntegerField(default=0)
    total_delivered = models.IntegerField(default=0)
    total_opened = models.IntegerField(default=0)
    total_clicked = models.IntegerField(default=0)
    total_bounced = models.IntegerField(default=0)
    total_unsubscribed = models.IntegerField(default=0)

    ab_test_enabled = models.BooleanField(default=False)
    ab_test_subject_b = models.CharField(max_length=200, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def open_rate(self):
        if self.total_delivered > 0:
            return (self.total_opened / self.total_delivered) * 100
        return 0

    @property
    def click_rate(self):
        if self.total_delivered > 0:
            return (self.total_clicked / self.total_delivered) * 100
        return 0


class EmailSend(models.Model):
    """Individual email send record."""

    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
        ('bounced', 'Bounced'),
        ('complained', 'Complained'),
        ('failed', 'Failed'),
    ]

    campaign = models.ForeignKey(
        EmailCampaign,
        on_delete=models.CASCADE,
        related_name='sends'
    )
    subscription = models.ForeignKey(
        NewsletterSubscription,
        on_delete=models.CASCADE,
        related_name='email_sends'
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')

    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)

    open_count = models.IntegerField(default=0)
    click_count = models.IntegerField(default=0)

    bounce_type = models.CharField(max_length=20, blank=True)
    bounce_reason = models.TextField(blank=True)

    message_id = models.CharField(max_length=200, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.campaign.name} -> {self.subscription.email}"


class EmailLink(models.Model):
    """Track clicks on links in emails."""

    campaign = models.ForeignKey(
        EmailCampaign,
        on_delete=models.CASCADE,
        related_name='links'
    )

    original_url = models.URLField()
    tracking_url = models.CharField(max_length=100, unique=True)

    click_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-click_count']

    def __str__(self):
        return f"{self.original_url} ({self.click_count} clicks)"

    def save(self, *args, **kwargs):
        if not self.tracking_url:
            import uuid
            self.tracking_url = str(uuid.uuid4())[:12]
        super().save(*args, **kwargs)


class AutomatedSequence(models.Model):
    """Automated email sequence."""

    TRIGGER_TYPES = [
        ('signup', 'Newsletter Signup'),
        ('purchase', 'After Purchase'),
        ('appointment', 'After Appointment'),
        ('inactivity', 'Inactivity'),
        ('birthday', 'Birthday'),
        ('custom', 'Custom Trigger'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_TYPES)

    is_active = models.BooleanField(default=True)

    total_enrolled = models.IntegerField(default=0)
    total_completed = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class SequenceStep(models.Model):
    """Step in an automated sequence."""

    sequence = models.ForeignKey(
        AutomatedSequence,
        on_delete=models.CASCADE,
        related_name='steps'
    )

    step_number = models.IntegerField()
    template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.PROTECT
    )

    delay_days = models.IntegerField(default=0)
    delay_hours = models.IntegerField(default=0)

    subject_override = models.CharField(max_length=200, blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['step_number']
        unique_together = ['sequence', 'step_number']

    def __str__(self):
        return f"{self.sequence.name} - Step {self.step_number}"


class SequenceEnrollment(models.Model):
    """Track user enrollment in sequence."""

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('exited', 'Exited'),
    ]

    sequence = models.ForeignKey(
        AutomatedSequence,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    subscription = models.ForeignKey(
        NewsletterSubscription,
        on_delete=models.CASCADE,
        related_name='sequence_enrollments'
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    current_step = models.IntegerField(default=1)

    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    next_email_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['sequence', 'subscription']

    def __str__(self):
        return f"{self.subscription.email} in {self.sequence.name}"
