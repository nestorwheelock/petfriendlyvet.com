"""Emergency services models for triage and on-call management."""
from django.conf import settings
from django.db import models


class EmergencySymptom(models.Model):
    """Known emergency symptoms for triage."""

    SEVERITY_CHOICES = [
        ('critical', 'Critical - Life Threatening'),
        ('urgent', 'Urgent - Needs Same-Day Care'),
        ('moderate', 'Moderate - Can Wait'),
        ('low', 'Low - Schedule Appointment'),
    ]

    keyword = models.CharField(max_length=100)
    keywords_es = models.JSONField(default=list)
    keywords_en = models.JSONField(default=list)

    species = models.JSONField(default=list)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    description = models.TextField()

    follow_up_questions = models.JSONField(default=list)
    first_aid_instructions = models.TextField(blank=True)
    warning_signs = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['severity', 'keyword']

    def __str__(self):
        return f"{self.keyword} ({self.severity})"


class EmergencyContact(models.Model):
    """Emergency contact attempt."""

    STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('triaging', 'Triaging'),
        ('escalated', 'Escalated to Staff'),
        ('resolved', 'Resolved'),
        ('referred', 'Referred Elsewhere'),
        ('no_response', 'No Response'),
    ]

    SEVERITY_CHOICES = [
        ('critical', 'Critical - Life Threatening'),
        ('urgent', 'Urgent - Needs Same-Day Care'),
        ('moderate', 'Moderate - Can Wait'),
        ('low', 'Low - Schedule Appointment'),
    ]

    CHANNEL_CHOICES = [
        ('web', 'Website'),
        ('whatsapp', 'WhatsApp'),
        ('phone', 'Phone'),
        ('sms', 'SMS'),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='emergency_contacts'
    )
    pet = models.ForeignKey(
        'pets.Pet',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='emergency_contacts'
    )

    phone = models.CharField(max_length=20)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)

    reported_symptoms = models.TextField()
    pet_species = models.CharField(max_length=50)
    pet_age = models.CharField(max_length=50, blank=True)

    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        null=True,
        blank=True
    )
    triage_notes = models.TextField(blank=True)
    ai_assessment = models.JSONField(default=dict)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='initiated'
    )

    handled_by = models.ForeignKey(
        'practice.StaffProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='emergency_contacts_handled'
    )
    response_time_seconds = models.IntegerField(null=True, blank=True)

    resolution = models.TextField(blank=True)
    outcome = models.CharField(max_length=50, blank=True)

    appointment = models.ForeignKey(
        'appointments.Appointment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='emergency_contacts'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    escalated_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Emergency: {self.pet_species} - {self.severity or 'Pending'} ({self.status})"


class OnCallSchedule(models.Model):
    """After-hours on-call schedule."""

    staff = models.ForeignKey(
        'practice.StaffProfile',
        on_delete=models.CASCADE,
        related_name='oncall_schedules'
    )

    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    contact_phone = models.CharField(max_length=20)
    backup_phone = models.CharField(max_length=20, blank=True)

    is_active = models.BooleanField(default=True)
    swap_requested = models.BooleanField(default=False)
    swap_with = models.ForeignKey(
        'practice.StaffProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='swap_requests'
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'start_time']
        unique_together = ['staff', 'date']

    def __str__(self):
        return f"{self.staff} - {self.date} ({self.start_time} - {self.end_time})"


class EmergencyReferral(models.Model):
    """Emergency referral hospitals (24-hour facilities)."""

    name = models.CharField(max_length=200)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    whatsapp = models.CharField(max_length=20, blank=True)

    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    distance_km = models.FloatField(null=True, blank=True)

    is_24_hours = models.BooleanField(default=False)
    hours = models.JSONField(default=dict)

    services = models.JSONField(default=list)
    species_treated = models.JSONField(default=list)

    is_active = models.BooleanField(default=True)
    last_verified = models.DateField(null=True, blank=True)

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['distance_km', 'name']

    def __str__(self):
        return self.name


class EmergencyFirstAid(models.Model):
    """First aid instructions for common emergencies."""

    title = models.CharField(max_length=200)
    title_es = models.CharField(max_length=200)

    condition = models.CharField(max_length=100)
    species = models.JSONField(default=list)

    description = models.TextField()
    description_es = models.TextField()

    steps = models.JSONField(default=list)
    warnings = models.JSONField(default=list)
    do_not = models.JSONField(default=list)

    video_url = models.URLField(blank=True)
    images = models.JSONField(default=list)

    related_symptoms = models.ManyToManyField(
        EmergencySymptom,
        blank=True,
        related_name='first_aid_guides'
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']
        verbose_name_plural = 'Emergency First Aid'

    def __str__(self):
        return self.title
