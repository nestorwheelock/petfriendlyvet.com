"""Practice models for staff and clinic management."""
from django.db import models
from django.conf import settings

from apps.core.storage import clinic_logo_path


class StaffProfile(models.Model):
    """Staff profile for clinic employees."""

    ROLE_CHOICES = [
        ('veterinarian', 'Veterinarian'),
        ('vet_tech', 'Veterinary Technician'),
        ('pharmacy_tech', 'Pharmacy Technician'),
        ('receptionist', 'Receptionist'),
        ('manager', 'Manager'),
        ('admin', 'Administrator'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='staff_profile'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    title = models.CharField(max_length=100, blank=True)

    # Permissions
    can_prescribe = models.BooleanField(default=False)
    can_dispense = models.BooleanField(default=False)
    can_handle_controlled = models.BooleanField(default=False)

    # DEA credentials (for controlled substances)
    dea_number = models.CharField(max_length=20, blank=True)
    dea_expiration = models.DateField(null=True, blank=True)

    # Contact
    phone = models.CharField(max_length=20, blank=True)
    emergency_phone = models.CharField(max_length=20, blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    hire_date = models.DateField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user__first_name', 'user__last_name']

    def __str__(self):
        name = self.user.get_full_name() or self.user.username
        return f"{name} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        # Auto-set permissions based on role
        if self.role == 'veterinarian':
            self.can_prescribe = True
            self.can_dispense = True
            self.can_handle_controlled = True
        elif self.role == 'pharmacy_tech':
            self.can_dispense = True
        super().save(*args, **kwargs)


class Shift(models.Model):
    """Staff work shift."""

    staff = models.ForeignKey(
        StaffProfile,
        on_delete=models.CASCADE,
        related_name='shifts'
    )

    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    is_confirmed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'start_time']
        unique_together = ['staff', 'date', 'start_time']

    def __str__(self):
        return f"{self.staff.user.get_full_name()} - {self.date}"


class TimeEntry(models.Model):
    """Time tracking for staff."""

    staff = models.ForeignKey(
        StaffProfile,
        on_delete=models.CASCADE,
        related_name='time_entries'
    )
    shift = models.ForeignKey(
        Shift,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    clock_in = models.DateTimeField()
    clock_out = models.DateTimeField(null=True, blank=True)

    break_minutes = models.IntegerField(default=0)
    notes = models.TextField(blank=True)

    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-clock_in']

    def __str__(self):
        return f"{self.staff.user.get_full_name()} - {self.clock_in.date()}"

    @property
    def hours_worked(self):
        if self.clock_out:
            delta = self.clock_out - self.clock_in
            hours = (delta.total_seconds() / 3600) - (self.break_minutes / 60)
            return round(hours, 2)
        return 0


class ClinicSettings(models.Model):
    """Clinic configuration settings."""

    name = models.CharField(max_length=200)
    legal_name = models.CharField(max_length=200, blank=True)
    tax_id = models.CharField(max_length=50, blank=True)

    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    website = models.URLField(blank=True)

    # Hours
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    days_open = models.JSONField(default=list)

    # Emergency
    emergency_phone = models.CharField(max_length=20, blank=True)
    emergency_available = models.BooleanField(default=False)

    # Social
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    google_maps_url = models.URLField(blank=True)

    # Branding
    logo = models.ImageField(upload_to=clinic_logo_path, blank=True, null=True)
    primary_color = models.CharField(max_length=7, default='#2563eb')

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Clinic Settings'
        verbose_name_plural = 'Clinic Settings'

    def __str__(self):
        return self.name


class ClinicalNote(models.Model):
    """Clinical notes for patient records."""

    NOTE_TYPES = [
        ('soap', 'SOAP Note'),
        ('progress', 'Progress Note'),
        ('procedure', 'Procedure Note'),
        ('lab', 'Lab Results'),
        ('phone', 'Phone Consultation'),
        ('internal', 'Internal Note'),
    ]

    pet = models.ForeignKey(
        'pets.Pet',
        on_delete=models.CASCADE,
        related_name='practice_notes'
    )
    appointment = models.ForeignKey(
        'appointments.Appointment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    note_type = models.CharField(max_length=20, choices=NOTE_TYPES)

    # SOAP structure
    subjective = models.TextField(blank=True)
    objective = models.TextField(blank=True)
    assessment = models.TextField(blank=True)
    plan = models.TextField(blank=True)

    # General content (for non-SOAP notes)
    content = models.TextField(blank=True)

    # Metadata
    is_confidential = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    locked_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.pet.name} - {self.get_note_type_display()} ({self.created_at.date()})"


class Task(models.Model):
    """Staff task management."""

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    assigned_to = models.ForeignKey(
        StaffProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    due_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Related entities
    pet = models.ForeignKey(
        'pets.Pet',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    appointment = models.ForeignKey(
        'appointments.Appointment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority', 'due_date', '-created_at']

    def __str__(self):
        return self.title
