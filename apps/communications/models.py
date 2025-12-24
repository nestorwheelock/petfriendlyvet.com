"""Omnichannel communications models."""
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class CommunicationChannel(models.Model):
    """User communication channel preferences."""

    CHANNEL_TYPES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
        ('voice', 'Voice Call'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='communication_channels'
    )
    channel_type = models.CharField(max_length=20, choices=CHANNEL_TYPES)
    identifier = models.CharField(max_length=255)
    is_verified = models.BooleanField(default=False)
    is_primary = models.BooleanField(default=False)
    preferences = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_primary', 'channel_type']

    def __str__(self):
        return f"{self.channel_type}: {self.identifier}"


class MessageTemplate(models.Model):
    """Message templates for different notification types."""

    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=50)
    subject_es = models.CharField(max_length=200, blank=True)
    subject_en = models.CharField(max_length=200, blank=True)
    body_es = models.TextField()
    body_en = models.TextField()
    channels = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Message(models.Model):
    """Individual message record."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
    ]

    DIRECTION_CHOICES = [
        ('outbound', 'Outbound'),
        ('inbound', 'Inbound'),
    ]

    CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
        ('voice', 'Voice Call'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='messages'
    )
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES)
    recipient = models.CharField(max_length=255)
    subject = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    external_id = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict)

    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.channel} {self.direction}: {self.recipient}"


class ReminderSchedule(models.Model):
    """Scheduled reminder for various notifications."""

    REMINDER_TYPES = [
        ('appointment', 'Appointment Reminder'),
        ('vaccination', 'Vaccination Due'),
        ('prescription', 'Prescription Refill'),
        ('followup', 'Follow-up Visit'),
    ]

    reminder_type = models.CharField(max_length=50, choices=REMINDER_TYPES)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    related_object = GenericForeignKey('content_type', 'object_id')

    scheduled_for = models.DateTimeField()
    sent = models.BooleanField(default=False)
    channels_attempted = models.JSONField(default=list)
    confirmed = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['scheduled_for']

    def __str__(self):
        return f"{self.reminder_type} scheduled for {self.scheduled_for}"


class EscalationRule(models.Model):
    """Escalation rules for reminders."""

    CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
        ('voice', 'Voice Call'),
    ]

    reminder_type = models.CharField(max_length=50)
    step = models.IntegerField()
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    wait_hours = models.IntegerField()
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['reminder_type', 'step']

    def __str__(self):
        return f"{self.reminder_type} Step {self.step}: {self.channel}"
