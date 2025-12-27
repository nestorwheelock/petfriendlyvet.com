"""Practice models for staff, clinic management, and veterinary procedures.

Provides:
- PatientRecord: Links a Pet to the practice's medical system
- VetCredentials: Veterinary credentials and capabilities
- Vaccination: Vaccination records
- MedicalCondition: Allergies, chronic conditions
- Visit: Veterinary visit records
- Medication: Prescriptions and medication records
- WeightRecord: Weight tracking history
- MedicalDocument: Medical documents and files
- StaffProfile: Staff profiles with roles and permissions (DEPRECATED)
- Shift: Staff work shifts
- TimeEntry: Time tracking
- ClinicSettings: Clinic configuration
- ClinicalNote: Clinical notes (SOAP format)
- Task: Staff task management
- ProcedureCategory: Categories for veterinary procedures
- VetProcedure: Veterinary services/procedures
"""
from datetime import date
from decimal import Decimal

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from apps.core.storage import clinic_logo_path, pet_document_path


# =============================================================================
# Patient Records & Medical History (EMR)
# =============================================================================

class PatientRecord(models.Model):
    """Links a Pet to this practice's medical system.

    A Pet can exist without being a patient (e.g., friend's pet, pet store inventory).
    Once they visit the practice, a PatientRecord is created to track their medical history.
    """

    pet = models.OneToOneField(
        'pets.Pet',
        on_delete=models.CASCADE,
        related_name='patient_record',
        verbose_name=_('pet'),
    )
    patient_number = models.CharField(
        _('patient number'),
        max_length=20,
        unique=True,
        help_text=_('Practice-specific patient ID'),
    )
    primary_veterinarian = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='primary_patients',
        verbose_name=_('primary veterinarian'),
    )
    first_visit_date = models.DateField(
        _('first visit date'),
        null=True,
        blank=True,
    )

    STATUS_CHOICES = [
        ('active', _('Active')),
        ('inactive', _('Inactive')),
        ('transferred', _('Transferred')),
        ('deceased', _('Deceased')),
    ]
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
    )

    referring_practice = models.CharField(
        _('referring practice'),
        max_length=200,
        blank=True,
        help_text=_('If referred from another veterinary practice'),
    )
    notes = models.TextField(
        _('medical notes'),
        blank=True,
        help_text=_('Practice-specific medical notes'),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('patient record')
        verbose_name_plural = _('patient records')
        ordering = ['patient_number']

    def __str__(self):
        return f"{self.patient_number} - {self.pet.name}"

    def save(self, *args, **kwargs):
        # Auto-generate patient number if not set
        if not self.patient_number:
            from django.utils import timezone
            year = timezone.now().year
            last_record = PatientRecord.objects.filter(
                patient_number__startswith=f'P{year}'
            ).order_by('-patient_number').first()
            if last_record:
                last_num = int(last_record.patient_number[5:])
                self.patient_number = f'P{year}{last_num + 1:04d}'
            else:
                self.patient_number = f'P{year}0001'
        super().save(*args, **kwargs)


CONDITION_TYPES = [
    ('allergy', _('Allergy')),
    ('chronic', _('Chronic Condition')),
    ('injury', _('Injury')),
    ('other', _('Other')),
]


class MedicalCondition(models.Model):
    """Medical conditions, allergies, and chronic issues."""

    pet = models.ForeignKey(
        'pets.Pet',
        on_delete=models.CASCADE,
        related_name='medical_conditions',
        verbose_name=_('pet'),
    )
    name = models.CharField(_('condition name'), max_length=200)
    condition_type = models.CharField(
        _('type'),
        max_length=20,
        choices=CONDITION_TYPES,
        default='other',
    )
    diagnosed_date = models.DateField(_('diagnosed date'), null=True, blank=True)
    diagnosed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conditions_diagnosed',
        verbose_name=_('diagnosed by'),
    )
    notes = models.TextField(_('notes'), blank=True)
    is_active = models.BooleanField(_('active'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('medical condition')
        verbose_name_plural = _('medical conditions')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.pet.name} - {self.name}"


class Vaccination(models.Model):
    """Vaccination records."""

    pet = models.ForeignKey(
        'pets.Pet',
        on_delete=models.CASCADE,
        related_name='vaccination_records',
        verbose_name=_('pet'),
    )
    vaccine_name = models.CharField(_('vaccine name'), max_length=200)
    date_administered = models.DateField(_('date administered'))
    next_due_date = models.DateField(_('next due date'), null=True, blank=True)
    administered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vaccinations_administered',
        verbose_name=_('administered by'),
    )
    batch_number = models.CharField(_('batch number'), max_length=100, blank=True)
    manufacturer = models.CharField(_('manufacturer'), max_length=100, blank=True)
    notes = models.TextField(_('notes'), blank=True)

    # Reminder tracking
    reminder_sent = models.BooleanField(_('reminder sent'), default=False)
    reminder_sent_at = models.DateTimeField(_('reminder sent at'), null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('vaccination')
        verbose_name_plural = _('vaccinations')
        ordering = ['-date_administered']

    def __str__(self):
        return f"{self.pet.name} - {self.vaccine_name} ({self.date_administered})"

    @property
    def is_overdue(self):
        """Check if vaccination is overdue."""
        if not self.next_due_date:
            return False
        return date.today() > self.next_due_date

    @property
    def is_due_soon(self):
        """Check if vaccination is due within 30 days."""
        if not self.next_due_date:
            return False
        days_until_due = (self.next_due_date - date.today()).days
        return 0 < days_until_due <= 30


class Visit(models.Model):
    """Veterinary visit records."""

    pet = models.ForeignKey(
        'pets.Pet',
        on_delete=models.CASCADE,
        related_name='visit_records',
        verbose_name=_('pet'),
    )
    date = models.DateTimeField(_('visit date'))
    reason = models.CharField(_('reason for visit'), max_length=500)
    diagnosis = models.TextField(_('diagnosis'), blank=True)
    treatment = models.TextField(_('treatment'), blank=True)
    veterinarian = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='visits_as_vet',
        verbose_name=_('veterinarian'),
    )
    weight_kg = models.DecimalField(
        _('weight at visit (kg)'),
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )
    temperature = models.DecimalField(
        _('temperature (°C)'),
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
    )
    follow_up_date = models.DateField(_('follow-up date'), null=True, blank=True)
    notes = models.TextField(_('notes'), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('visit')
        verbose_name_plural = _('visits')
        ordering = ['-date']

    def __str__(self):
        return f"{self.pet.name} - {self.reason} ({self.date.date()})"

    def save(self, *args, **kwargs):
        """Update pet's weight if recorded during visit."""
        super().save(*args, **kwargs)
        if self.weight_kg:
            self.pet.weight_kg = self.weight_kg
            self.pet.save(update_fields=['weight_kg', 'updated_at'])


class Medication(models.Model):
    """Medication records and prescriptions."""

    pet = models.ForeignKey(
        'pets.Pet',
        on_delete=models.CASCADE,
        related_name='medication_records',
        verbose_name=_('pet'),
    )
    name = models.CharField(_('medication name'), max_length=200)
    dosage = models.CharField(_('dosage'), max_length=100)
    frequency = models.CharField(_('frequency'), max_length=100)
    route = models.CharField(
        _('route of administration'),
        max_length=50,
        blank=True,
        help_text=_('e.g., oral, injection, topical'),
    )
    start_date = models.DateField(_('start date'))
    end_date = models.DateField(_('end date'), null=True, blank=True)
    prescribing_vet = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medications_prescribed',
        verbose_name=_('prescribing veterinarian'),
    )
    visit = models.ForeignKey(
        Visit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prescribed_medications',
        verbose_name=_('related visit'),
    )
    refills_remaining = models.PositiveIntegerField(_('refills remaining'), default=0)
    notes = models.TextField(_('notes'), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('medication')
        verbose_name_plural = _('medications')
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.pet.name} - {self.name}"

    @property
    def is_active(self):
        """Check if medication course is currently active."""
        today = date.today()
        if today < self.start_date:
            return False
        if self.end_date and today > self.end_date:
            return False
        return True


class WeightRecord(models.Model):
    """Weight tracking history for pets."""

    pet = models.ForeignKey(
        'pets.Pet',
        on_delete=models.CASCADE,
        related_name='weight_history',
        verbose_name=_('pet'),
    )
    weight_kg = models.DecimalField(
        _('weight (kg)'),
        max_digits=6,
        decimal_places=2,
    )
    recorded_date = models.DateField(_('recorded date'))
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='weight_records',
        verbose_name=_('recorded by'),
    )
    notes = models.TextField(_('notes'), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('weight record')
        verbose_name_plural = _('weight records')
        ordering = ['-recorded_date']

    def __str__(self):
        return f"{self.pet.name} - {self.weight_kg}kg ({self.recorded_date})"

    def save(self, *args, **kwargs):
        """Update pet's current weight when record is created."""
        if not self.recorded_date:
            self.recorded_date = date.today()
        super().save(*args, **kwargs)
        self.pet.weight_kg = self.weight_kg
        self.pet.save(update_fields=['weight_kg', 'updated_at'])


DOCUMENT_TYPES = [
    ('lab_result', _('Lab Result')),
    ('xray', _('X-Ray')),
    ('ultrasound', _('Ultrasound')),
    ('photo', _('Clinical Photo')),
    ('certificate', _('Certificate')),
    ('prescription', _('Prescription')),
    ('referral', _('Referral')),
    ('discharge', _('Discharge Summary')),
    ('consent', _('Consent Form')),
    ('other', _('Other')),
]


class MedicalDocument(models.Model):
    """Medical documents and files associated with a pet."""

    pet = models.ForeignKey(
        'pets.Pet',
        on_delete=models.CASCADE,
        related_name='medical_documents',
        verbose_name=_('pet'),
    )
    title = models.CharField(_('title'), max_length=200)
    document_type = models.CharField(
        _('document type'),
        max_length=20,
        choices=DOCUMENT_TYPES,
        default='other',
    )
    file = models.FileField(
        _('file'),
        upload_to=pet_document_path,
        null=True,
        blank=True,
    )
    description = models.TextField(_('description'), blank=True)
    visit = models.ForeignKey(
        Visit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        verbose_name=_('related visit'),
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='medical_documents_uploaded',
        verbose_name=_('uploaded by'),
    )
    visible_to_owner = models.BooleanField(
        _('visible to owner'),
        default=True,
        help_text=_('Whether the pet owner can see this document'),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('medical document')
        verbose_name_plural = _('medical documents')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.pet.name} - {self.title}"


# =============================================================================
# Veterinary Credentials & Capabilities
# =============================================================================

class VetCredentials(models.Model):
    """Veterinary credentials - a person's ability to practice veterinary medicine.

    This is a CAPABILITY attached to a Person (User), not an employment record.
    Employment details (hire date, department, tax IDs) are managed through
    PartyRelationship + EmploymentDetails in accounts/hr modules.

    A person with VetCredentials can be:
    - A full-time employed veterinarian
    - A part-time contractor vet
    - A visiting specialist
    - A vet tech with specific certifications
    """

    CREDENTIAL_TYPE_CHOICES = [
        ('veterinarian', 'Veterinarian (DVM/MVZ)'),
        ('vet_tech', 'Veterinary Technician'),
        ('pharmacy_tech', 'Pharmacy Technician'),
        ('specialist', 'Veterinary Specialist'),
    ]

    person = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vet_credentials',
        verbose_name='person',
    )

    credential_type = models.CharField(
        max_length=20,
        choices=CREDENTIAL_TYPE_CHOICES,
        default='veterinarian',
    )
    title = models.CharField(
        max_length=100,
        blank=True,
        help_text='Professional title (e.g., "DVM", "MVZ", "Veterinary Technician")',
    )
    specialty = models.CharField(
        max_length=100,
        blank=True,
        help_text='Specialty area (e.g., "Oncology", "Surgery", "Dentistry")',
    )

    # License info
    license_number = models.CharField(max_length=50, blank=True)
    license_state = models.CharField(
        max_length=50,
        blank=True,
        help_text='Issuing state/country',
    )
    license_expiry = models.DateField(null=True, blank=True)

    # DEA credentials (for controlled substances - US/Mexico)
    dea_number = models.CharField(max_length=20, blank=True)
    dea_expiration = models.DateField(null=True, blank=True)

    # Permissions (what this person CAN do based on credentials)
    can_prescribe = models.BooleanField(
        default=False,
        help_text='Can prescribe medications',
    )
    can_dispense = models.BooleanField(
        default=False,
        help_text='Can dispense medications',
    )
    can_handle_controlled = models.BooleanField(
        default=False,
        help_text='Can handle controlled substances',
    )
    can_perform_surgery = models.BooleanField(
        default=False,
        help_text='Can perform surgical procedures',
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'veterinary credentials'
        verbose_name_plural = 'veterinary credentials'
        ordering = ['person__first_name', 'person__last_name']

    def __str__(self):
        name = self.person.get_full_name() or self.person.username
        return f'{name} ({self.get_credential_type_display()})'

    def save(self, *args, **kwargs):
        # Auto-set permissions based on credential type
        if self.credential_type == 'veterinarian':
            self.can_prescribe = True
            self.can_dispense = True
            self.can_handle_controlled = True
            self.can_perform_surgery = True
        elif self.credential_type == 'specialist':
            self.can_prescribe = True
            self.can_dispense = True
            self.can_handle_controlled = True
            self.can_perform_surgery = True
        elif self.credential_type == 'pharmacy_tech':
            self.can_dispense = True
        super().save(*args, **kwargs)

    @property
    def is_licensed(self):
        """Check if credentials are currently valid."""
        from django.utils import timezone
        if not self.license_number:
            return False
        if self.license_expiry and self.license_expiry < timezone.now().date():
            return False
        return True


# =============================================================================
# Backwards Compatibility - DEPRECATED
# =============================================================================

class StaffProfile(models.Model):
    """DEPRECATED: Use VetCredentials + PartyRelationship instead.

    This model is kept temporarily for backwards compatibility during migration.
    Will be removed in a future version.
    """

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
    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff_profiles',
        help_text='Link to HR Employee record for unified tracking'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    title = models.CharField(max_length=100, blank=True)

    # Permissions (now in VetCredentials)
    can_prescribe = models.BooleanField(default=False)
    can_dispense = models.BooleanField(default=False)
    can_handle_controlled = models.BooleanField(default=False)

    # DEA credentials (now in VetCredentials)
    dea_number = models.CharField(max_length=20, blank=True)
    dea_expiration = models.DateField(null=True, blank=True)

    # Contact (now in User or EmploymentDetails)
    phone = models.CharField(max_length=20, blank=True)
    emergency_phone = models.CharField(max_length=20, blank=True)

    # Status (now in EmploymentDetails)
    is_active = models.BooleanField(default=True)
    hire_date = models.DateField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'staff profile (deprecated)'
        verbose_name_plural = 'staff profiles (deprecated)'
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


class ProcedureCategory(models.Model):
    """Categories for veterinary procedures.

    Groups procedures for organization and reporting.
    Examples: Consultation, Surgery, Vaccination, Dental, Lab Work
    """

    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique identifier (e.g., 'surgery', 'dental')"
    )
    name = models.CharField(max_length=100)
    name_es = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)

    icon = models.CharField(max_length=50, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = 'Procedure Category'
        verbose_name_plural = 'Procedure Categories'

    def __str__(self):
        return self.name


class VetProcedure(models.Model):
    """Veterinary procedure/service definition.

    This is the service-module-specific model for veterinary clinics.
    Other business types would have their own service models:
    - AutoShop: RepairService
    - Restaurant: MenuItem
    - WaterDelivery: DeliveryService
    """

    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Internal procedure code (e.g., 'CONSULT-GEN')"
    )
    name = models.CharField(max_length=200)
    name_es = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)

    category = models.ForeignKey(
        ProcedureCategory,
        on_delete=models.PROTECT,
        related_name='procedures'
    )

    # Qualified providers who can perform this procedure
    qualified_providers = models.ManyToManyField(
        StaffProfile,
        blank=True,
        related_name='qualified_procedures',
        help_text="Staff members qualified to perform this procedure"
    )

    # Pricing
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Standard price for this procedure"
    )
    price_varies = models.BooleanField(
        default=False,
        help_text="Price depends on factors (size, complexity, etc.)"
    )

    # Time
    duration_minutes = models.PositiveIntegerField(
        default=30,
        help_text="Expected duration in minutes"
    )

    # SAT codes for Mexican tax compliance
    sat_product_code = models.ForeignKey(
        'billing.SATProductCode',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="SAT Clave Producto for CFDI invoicing"
    )
    sat_unit_code = models.ForeignKey(
        'billing.SATUnitCode',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="SAT Clave Unidad for CFDI invoicing"
    )

    # Requirements
    requires_appointment = models.BooleanField(default=True)
    requires_hospitalization = models.BooleanField(default=False)
    requires_anesthesia = models.BooleanField(default=False)
    requires_vet_license = models.BooleanField(
        default=True,
        help_text="Must be performed by licensed veterinarian"
    )

    # Status
    is_active = models.BooleanField(default=True)
    is_visible_online = models.BooleanField(
        default=True,
        help_text="Show in online booking system"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'Veterinary Procedure'
        verbose_name_plural = 'Veterinary Procedures'

    def __str__(self):
        return self.name

    @property
    def total_consumable_cost(self):
        """Calculate total cost of consumable items."""
        total = Decimal('0.00')
        for consumable in self.consumables.all():
            if consumable.inventory_item and consumable.inventory_item.cost_price:
                total += consumable.inventory_item.cost_price * consumable.quantity
        return total


class ProcedureConsumable(models.Model):
    """Inventory items consumed when performing a procedure.

    Tracks what items are used (vaccines, syringes, needles, towels, etc.)
    and the quantity consumed per procedure.
    """

    procedure = models.ForeignKey(
        VetProcedure,
        on_delete=models.CASCADE,
        related_name='consumables'
    )
    inventory_item = models.ForeignKey(
        'inventory.InventoryItem',
        on_delete=models.PROTECT,
        related_name='procedure_uses',
        help_text="Inventory item consumed during this procedure"
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('1.00'),
        help_text="Quantity consumed per procedure"
    )
    is_required = models.BooleanField(
        default=True,
        help_text="If true, procedure cannot be performed without this item in stock"
    )
    notes = models.CharField(
        max_length=200,
        blank=True,
        help_text="Optional notes (e.g., 'Use 3ml syringe for small dogs')"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['procedure', 'inventory_item']
        unique_together = ['procedure', 'inventory_item']
        verbose_name = 'Procedure Consumable'
        verbose_name_plural = 'Procedure Consumables'

    def __str__(self):
        return f"{self.procedure.name}: {self.quantity} x {self.inventory_item.name}"

    @property
    def unit_cost(self):
        """Get the cost of this consumable."""
        if self.inventory_item and self.inventory_item.cost_price:
            return self.inventory_item.cost_price * self.quantity
        return Decimal('0.00')
