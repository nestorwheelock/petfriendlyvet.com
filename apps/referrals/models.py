"""Referral network models for specialist referrals and visiting vets.

Provides:
- Specialist: Directory of specialist veterinarians and facilities
- VisitingSchedule: Schedule for visiting specialists
- Referral: Outbound/inbound referrals with tracking
- ReferralDocument: Documents attached to referrals
- ReferralNote: Communication notes on referrals
- VisitingAppointment: Appointments with visiting specialists
"""
import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class Specialist(models.Model):
    """Specialist veterinarian or facility for referrals."""

    SPECIALIST_TYPES = [
        ('oncology', 'Oncology'),
        ('cardiology', 'Cardiology'),
        ('orthopedics', 'Orthopedics'),
        ('ophthalmology', 'Ophthalmology'),
        ('dermatology', 'Dermatology'),
        ('neurology', 'Neurology'),
        ('surgery', 'Surgery'),
        ('internal_medicine', 'Internal Medicine'),
        ('emergency', 'Emergency/Critical Care'),
        ('imaging', 'Imaging/Radiology'),
        ('laboratory', 'Laboratory'),
        ('rehabilitation', 'Rehabilitation'),
        ('behavior', 'Behavior'),
        ('exotics', 'Exotic Animals'),
        ('dentistry', 'Dentistry'),
        ('other', 'Other'),
    ]

    RELATIONSHIP_STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending'),
    ]

    # Basic info
    name = models.CharField(max_length=200)
    specialty = models.CharField(max_length=50, choices=SPECIALIST_TYPES)
    credentials = models.CharField(max_length=200, blank=True)

    # Individual or facility
    is_facility = models.BooleanField(default=False)
    clinic_name = models.CharField(max_length=200, blank=True)

    # Contact
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20)
    fax = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)

    # Location
    address = models.TextField()
    city = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    distance_km = models.FloatField(null=True, blank=True)

    # Hours
    is_24_hours = models.BooleanField(default=False)
    hours = models.JSONField(default=dict)

    # Services
    services = models.JSONField(default=list)
    species_treated = models.JSONField(default=list)

    # Visiting specialist info
    is_visiting = models.BooleanField(default=False)
    visiting_services = models.JSONField(default=list)
    equipment_provided = models.JSONField(default=list)

    # Relationship
    relationship_status = models.CharField(
        max_length=20,
        choices=RELATIONSHIP_STATUS_CHOICES,
        default='active'
    )
    referral_agreement = models.TextField(blank=True)
    revenue_share_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Stats
    total_referrals_sent = models.IntegerField(default=0)
    total_referrals_received = models.IntegerField(default=0)
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Notes
    notes = models.TextField(blank=True)
    referral_instructions = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class VisitingSchedule(models.Model):
    """Schedule for visiting specialists at Pet-Friendly."""

    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    specialist = models.ForeignKey(
        Specialist,
        on_delete=models.CASCADE,
        related_name='visiting_schedules'
    )

    # When
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    # Recurring
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(max_length=50, blank=True)

    # Capacity
    max_appointments = models.IntegerField(null=True, blank=True)
    appointments_booked = models.IntegerField(default=0)

    # Services available this visit
    services_available = models.JSONField(default=list)

    # Equipment
    equipment_bringing = models.JSONField(default=list)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    cancellation_reason = models.TextField(blank=True)

    # Notes
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.specialist.name} - {self.date}"


class Referral(models.Model):
    """Referral to or from a specialist."""

    DIRECTION_CHOICES = [
        ('outbound', 'Outbound (To Specialist)'),
        ('inbound', 'Inbound (From Other Vet)'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('received', 'Received by Specialist'),
        ('scheduled', 'Appointment Scheduled'),
        ('seen', 'Patient Seen'),
        ('report_pending', 'Awaiting Report'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('declined', 'Declined by Specialist'),
    ]

    URGENCY_CHOICES = [
        ('routine', 'Routine'),
        ('urgent', 'Urgent (Within Week)'),
        ('emergency', 'Emergency (Same Day)'),
    ]

    OUTCOME_CHOICES = [
        ('successful', 'Successful Treatment'),
        ('ongoing', 'Ongoing Treatment'),
        ('referred_again', 'Referred to Another Specialist'),
        ('no_treatment', 'No Treatment Possible'),
        ('client_declined', 'Client Declined Treatment'),
        ('euthanasia', 'Euthanasia'),
        ('unknown', 'Unknown'),
    ]

    # Direction
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)

    # Referral number (auto-generated)
    referral_number = models.CharField(max_length=50, unique=True, blank=True)

    # Patient
    pet = models.ForeignKey(
        'pets.Pet',
        on_delete=models.CASCADE,
        related_name='specialist_referrals'
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pet_referrals'
    )

    # Specialist (for outbound)
    specialist = models.ForeignKey(
        Specialist,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referrals_received'
    )

    # For inbound referrals
    referring_vet_name = models.CharField(max_length=200, blank=True)
    referring_clinic = models.CharField(max_length=200, blank=True)
    referring_contact = models.CharField(max_length=200, blank=True)
    referring_professional_account = models.ForeignKey(
        'billing.ProfessionalAccount',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Reason
    reason = models.TextField()
    clinical_summary = models.TextField(blank=True)
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, default='routine')
    requested_services = models.JSONField(default=list)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Dates
    sent_at = models.DateTimeField(null=True, blank=True)
    appointment_date = models.DateTimeField(null=True, blank=True)
    seen_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Results
    specialist_findings = models.TextField(blank=True)
    specialist_diagnosis = models.TextField(blank=True)
    specialist_recommendations = models.TextField(blank=True)
    follow_up_needed = models.BooleanField(default=False)
    follow_up_instructions = models.TextField(blank=True)

    # Outcome
    outcome = models.CharField(max_length=20, choices=OUTCOME_CHOICES, blank=True)
    outcome_notes = models.TextField(blank=True)

    # Feedback
    client_satisfaction = models.IntegerField(null=True, blank=True)
    quality_rating = models.IntegerField(null=True, blank=True)

    # Staff
    referred_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='referrals_created'
    )

    # Billing
    invoice = models.ForeignKey(
        'billing.Invoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        if self.direction == 'outbound' and self.specialist:
            return f"REF-{self.referral_number}: {self.pet.name} to {self.specialist.name}"
        elif self.direction == 'inbound':
            return f"REF-{self.referral_number}: {self.pet.name} from {self.referring_clinic or self.referring_vet_name}"
        return f"REF-{self.referral_number}: {self.pet.name}"

    def save(self, *args, **kwargs):
        if not self.referral_number:
            self.referral_number = self._generate_referral_number()
        super().save(*args, **kwargs)

    def _generate_referral_number(self):
        """Generate unique referral number."""
        year = timezone.now().year
        random_part = uuid.uuid4().hex[:6].upper()
        return f"{year}-{random_part}"


class ReferralDocument(models.Model):
    """Documents attached to a referral."""

    DOCUMENT_TYPES = [
        ('referral_letter', 'Referral Letter'),
        ('medical_history', 'Medical History'),
        ('lab_results', 'Lab Results'),
        ('imaging', 'Imaging (X-ray, Ultrasound)'),
        ('specialist_report', 'Specialist Report'),
        ('prescription', 'Prescription'),
        ('other', 'Other'),
    ]

    referral = models.ForeignKey(
        Referral,
        on_delete=models.CASCADE,
        related_name='documents'
    )

    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='referrals/')
    description = models.TextField(blank=True)

    # Source
    is_outgoing = models.BooleanField(default=True)

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.get_document_type_display()})"


class ReferralNote(models.Model):
    """Communication notes on a referral."""

    referral = models.ForeignKey(
        Referral,
        on_delete=models.CASCADE,
        related_name='notes_list'
    )

    note = models.TextField()
    is_internal = models.BooleanField(default=True)

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Note on {self.referral.referral_number}: {self.note[:50]}..."


class VisitingAppointment(models.Model):
    """Appointment with a visiting specialist."""

    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked In'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('no_show', 'No Show'),
        ('cancelled', 'Cancelled'),
    ]

    schedule = models.ForeignKey(
        VisitingSchedule,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    specialist = models.ForeignKey(
        Specialist,
        on_delete=models.CASCADE
    )

    pet = models.ForeignKey(
        'pets.Pet',
        on_delete=models.CASCADE,
        related_name='visiting_appointments'
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='visiting_appointments'
    )

    # Time slot
    appointment_time = models.TimeField()
    duration_minutes = models.IntegerField(default=30)

    # Service
    service = models.CharField(max_length=100)
    reason = models.TextField()

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')

    # Results
    findings = models.TextField(blank=True)
    diagnosis = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)

    # Documents
    report_file = models.FileField(upload_to='visiting_reports/', null=True, blank=True)
    images = models.JSONField(default=list)

    # Billing
    fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pet_friendly_share = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    invoice = models.ForeignKey(
        'billing.Invoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Follow-up
    follow_up_needed = models.BooleanField(default=False)
    follow_up_notes = models.TextField(blank=True)

    # Related referral (if from referral workflow)
    referral = models.ForeignKey(
        Referral,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['schedule__date', 'appointment_time']

    def __str__(self):
        return f"{self.pet.name} with {self.specialist.name} at {self.appointment_time}"
