"""CRM (Customer Relationship Management) models."""
from django.conf import settings
from django.db import models


class CustomerTag(models.Model):
    """Tags for categorizing customers."""

    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#6c757d')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class CustomerSegment(models.Model):
    """Dynamic customer segments based on criteria."""

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    criteria = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class OwnerProfile(models.Model):
    """Extended profile for pet owners (CRM data)."""

    LANGUAGE_CHOICES = [
        ('es', 'Spanish'),
        ('en', 'English'),
    ]

    CONTACT_METHOD_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
        ('phone', 'Phone Call'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owner_profile'
    )

    # Preferences
    preferred_language = models.CharField(
        max_length=5,
        choices=LANGUAGE_CHOICES,
        default='es'
    )
    preferred_contact_method = models.CharField(
        max_length=20,
        choices=CONTACT_METHOD_CHOICES,
        default='whatsapp'
    )
    marketing_preferences = models.JSONField(default=dict)

    # CRM data
    tags = models.ManyToManyField(CustomerTag, blank=True, related_name='profiles')
    notes = models.TextField(blank=True)

    # Analytics
    first_visit_date = models.DateField(null=True, blank=True)
    last_visit_date = models.DateField(null=True, blank=True)
    total_visits = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    lifetime_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Referral tracking
    referred_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referrals'
    )
    referral_source = models.CharField(max_length=100, blank=True)

    # Social
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user__first_name', 'user__last_name']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.email}"


class Interaction(models.Model):
    """Customer interaction/touchpoint record."""

    INTERACTION_TYPES = [
        ('call', 'Phone Call'),
        ('email', 'Email'),
        ('chat', 'Chat'),
        ('visit', 'In-Person Visit'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
    ]

    CHANNEL_CHOICES = [
        ('phone', 'Phone'),
        ('email', 'Email'),
        ('chat', 'Chat'),
        ('in_person', 'In Person'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
        ('social', 'Social Media'),
    ]

    DIRECTION_CHOICES = [
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound'),
    ]

    owner_profile = models.ForeignKey(
        OwnerProfile,
        on_delete=models.CASCADE,
        related_name='interactions'
    )
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES)

    subject = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)

    # Staff who handled
    handled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='handled_interactions'
    )

    # Duration for calls
    duration_minutes = models.IntegerField(null=True, blank=True)

    # Outcome
    outcome = models.CharField(max_length=100, blank=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.interaction_type} - {self.owner_profile.user.email}"


class CustomerNote(models.Model):
    """Internal notes about customers."""

    owner_profile = models.ForeignKey(
        OwnerProfile,
        on_delete=models.CASCADE,
        related_name='customer_notes'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='authored_notes'
    )
    content = models.TextField()
    is_pinned = models.BooleanField(default=False)
    is_private = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return f"Note for {self.owner_profile.user.email}"
