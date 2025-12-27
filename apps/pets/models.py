"""Pet models for Pet-Friendly Vet."""
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.storage import pet_photo_path, pet_document_path


SPECIES_CHOICES = [
    ('dog', _('Dog')),
    ('cat', _('Cat')),
    ('bird', _('Bird')),
    ('rabbit', _('Rabbit')),
    ('hamster', _('Hamster')),
    ('guinea_pig', _('Guinea Pig')),
    ('reptile', _('Reptile')),
    ('other', _('Other')),
]

GENDER_CHOICES = [
    ('male', _('Male')),
    ('female', _('Female')),
    ('unknown', _('Unknown')),
]


class Pet(models.Model):
    """Pet profile model.

    A pet can be owned by:
    - A Person - most common: individual pet owner
    - A Group - household/family sharing a pet
    - An Organization - zoo, school, rescue, clinic

    At least one owner FK must be set.

    For organizations (e.g., zoo), the responsible_person field
    links to the individual legally responsible for the animal.
    """

    # Party ownership - exactly one should be set
    owner_person = models.ForeignKey(
        'parties.Person',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='owned_pets',
        verbose_name=_('owner (person)'),
        help_text=_('Individual person who owns this pet'),
    )
    owner_group = models.ForeignKey(
        'parties.Group',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='owned_pets',
        verbose_name=_('owner (group)'),
        help_text=_('Household/family group that owns this pet'),
    )
    owner_organization = models.ForeignKey(
        'parties.Organization',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='owned_pets',
        verbose_name=_('owner (organization)'),
        help_text=_('Organization that owns this pet (zoo, school, rescue, etc.)'),
    )

    # Multiple people can be responsible for a pet
    # (e.g., zoo has head keeper + backup keepers)
    # Use PetResponsibility M2M through table below

    # DEPRECATED - kept for backwards compatibility during migration
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='pets',
        verbose_name=_('owner (deprecated)'),
        help_text=_('DEPRECATED: Use owner_person instead'),
    )

    name = models.CharField(_('name'), max_length=100)
    species = models.CharField(
        _('species'),
        max_length=20,
        choices=SPECIES_CHOICES,
        default='dog'
    )
    breed = models.CharField(_('breed'), max_length=100, blank=True)
    gender = models.CharField(
        _('gender'),
        max_length=10,
        choices=GENDER_CHOICES,
        default='unknown'
    )
    date_of_birth = models.DateField(_('date of birth'), null=True, blank=True)
    weight_kg = models.DecimalField(
        _('weight (kg)'),
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )
    microchip_id = models.CharField(
        _('microchip ID'),
        max_length=50,
        blank=True
    )
    is_neutered = models.BooleanField(_('neutered/spayed'), default=False)
    photo = models.ImageField(
        _('photo'),
        upload_to=pet_photo_path,
        null=True,
        blank=True
    )
    notes = models.TextField(_('notes'), blank=True)
    is_archived = models.BooleanField(
        _('archived'),
        default=False,
        help_text=_('Hidden from active pet list but preserved for records')
    )
    deceased_date = models.DateField(
        _('date passed away'),
        null=True,
        blank=True,
        help_text=_('If the pet has passed away')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('pet')
        verbose_name_plural = _('pets')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_species_display()})"

    @property
    def party_owner(self):
        """Returns whichever owner is set (Person, Group, or Organization)."""
        return self.owner_person or self.owner_group or self.owner_organization or self.owner

    @property
    def owner_name(self):
        """Returns display name for owner."""
        owner = self.party_owner
        if owner is None:
            return None
        # User has get_full_name(), Group and Organization have name
        if hasattr(owner, 'get_full_name'):
            return owner.get_full_name() or str(owner)
        return owner.name if hasattr(owner, 'name') else str(owner)

    @property
    def owner_type(self):
        """Returns the type of owner: 'person', 'group', 'organization', or None."""
        if self.owner_person_id:
            return 'person'
        elif self.owner_group_id:
            return 'group'
        elif self.owner_organization_id:
            return 'organization'
        elif self.owner_id:  # deprecated field
            return 'person'
        return None

    @property
    def age_years(self):
        """Calculate pet's age in years."""
        if not self.date_of_birth:
            return None
        today = date.today()
        age = today.year - self.date_of_birth.year
        if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
            age -= 1
        return age


class MedicalCondition(models.Model):
    """Medical conditions, allergies, and chronic issues."""

    CONDITION_TYPES = [
        ('allergy', _('Allergy')),
        ('chronic', _('Chronic Condition')),
        ('injury', _('Injury')),
        ('other', _('Other')),
    ]

    pet = models.ForeignKey(
        Pet,
        on_delete=models.CASCADE,
        related_name='conditions',
        verbose_name=_('pet')
    )
    name = models.CharField(_('condition name'), max_length=200)
    condition_type = models.CharField(
        _('type'),
        max_length=20,
        choices=CONDITION_TYPES,
        default='other'
    )
    diagnosed_date = models.DateField(_('diagnosed date'), null=True, blank=True)
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
        Pet,
        on_delete=models.CASCADE,
        related_name='vaccinations',
        verbose_name=_('pet')
    )
    vaccine_name = models.CharField(_('vaccine name'), max_length=200)
    date_administered = models.DateField(_('date administered'))
    next_due_date = models.DateField(_('next due date'), null=True, blank=True)
    administered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vaccinations_given',
        verbose_name=_('administered by')
    )
    batch_number = models.CharField(_('batch number'), max_length=100, blank=True)
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
        Pet,
        on_delete=models.CASCADE,
        related_name='visits',
        verbose_name=_('pet')
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
        related_name='visits_conducted',
        verbose_name=_('veterinarian')
    )
    weight_kg = models.DecimalField(
        _('weight at visit (kg)'),
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
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
        Pet,
        on_delete=models.CASCADE,
        related_name='medications',
        verbose_name=_('pet')
    )
    name = models.CharField(_('medication name'), max_length=200)
    dosage = models.CharField(_('dosage'), max_length=100)
    frequency = models.CharField(_('frequency'), max_length=100)
    start_date = models.DateField(_('start date'))
    end_date = models.DateField(_('end date'), null=True, blank=True)
    prescribing_vet = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pet_medications_prescribed',
        verbose_name=_('prescribing veterinarian')
    )
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


CLINICAL_NOTE_TYPES = [
    ('observation', _('Observation')),
    ('treatment', _('Treatment Note')),
    ('followup', _('Follow-up')),
    ('lab', _('Lab Results')),
    ('other', _('Other')),
]


class ClinicalNote(models.Model):
    """Staff-only clinical notes about pets."""

    pet = models.ForeignKey(
        Pet,
        on_delete=models.CASCADE,
        related_name='clinical_notes',
        verbose_name=_('pet')
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='clinical_notes_authored',
        verbose_name=_('author')
    )
    visit = models.ForeignKey(
        Visit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clinical_notes',
        verbose_name=_('related visit')
    )
    note = models.TextField(_('note'))
    note_type = models.CharField(
        _('note type'),
        max_length=20,
        choices=CLINICAL_NOTE_TYPES,
        default='observation'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('clinical note')
        verbose_name_plural = _('clinical notes')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.pet.name} - {self.get_note_type_display()} ({self.created_at.date()})"


class WeightRecord(models.Model):
    """Weight tracking history for pets."""

    pet = models.ForeignKey(
        Pet,
        on_delete=models.CASCADE,
        related_name='weight_records',
        verbose_name=_('pet')
    )
    weight_kg = models.DecimalField(
        _('weight (kg)'),
        max_digits=6,
        decimal_places=2
    )
    recorded_date = models.DateField(_('recorded date'), auto_now_add=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='weight_records_recorded',
        verbose_name=_('recorded by')
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
        super().save(*args, **kwargs)
        self.pet.weight_kg = self.weight_kg
        self.pet.save(update_fields=['weight_kg', 'updated_at'])


DOCUMENT_TYPES = [
    ('lab_result', _('Lab Result')),
    ('xray', _('X-Ray')),
    ('photo', _('Photo')),
    ('certificate', _('Certificate')),
    ('prescription', _('Prescription')),
    ('referral', _('Referral')),
    ('other', _('Other')),
]


class PetDocument(models.Model):
    """Documents and files associated with a pet."""

    pet = models.ForeignKey(
        Pet,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name=_('pet')
    )
    title = models.CharField(_('title'), max_length=200)
    document_type = models.CharField(
        _('document type'),
        max_length=20,
        choices=DOCUMENT_TYPES,
        default='other'
    )
    file = models.FileField(
        _('file'),
        upload_to=pet_document_path,
        null=True,
        blank=True
    )
    description = models.TextField(_('description'), blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='pet_documents_uploaded',
        verbose_name=_('uploaded by')
    )
    visible_to_owner = models.BooleanField(
        _('visible to owner'),
        default=True,
        help_text=_('Whether the pet owner can see this document')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('pet document')
        verbose_name_plural = _('pet documents')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.pet.name} - {self.title}"


RESPONSIBILITY_TYPES = [
    ('primary', _('Primary Responsible')),
    ('secondary', _('Secondary/Backup')),
    ('caretaker', _('Caretaker')),
    ('emergency', _('Emergency Contact')),
    ('veterinary', _('Veterinary Contact')),
    ('other', _('Other')),
]


class PetResponsibility(models.Model):
    """Links a Person to a Pet with a responsibility role.

    Examples:
    - Zoo elephant: Head keeper (primary), Assistant keepers (secondary)
    - Family dog: Both parents (primary), Grandma (emergency)
    - School horse: Teacher (primary), Stable hand (caretaker)
    """

    pet = models.ForeignKey(
        Pet,
        on_delete=models.CASCADE,
        related_name='responsibilities',
        verbose_name=_('pet'),
    )
    person = models.ForeignKey(
        'parties.Person',
        on_delete=models.CASCADE,
        related_name='pet_responsibilities',
        verbose_name=_('person'),
    )
    responsibility_type = models.CharField(
        _('responsibility type'),
        max_length=20,
        choices=RESPONSIBILITY_TYPES,
        default='primary',
    )
    is_active = models.BooleanField(_('active'), default=True)

    # When they became/stopped being responsible
    start_date = models.DateField(_('start date'), null=True, blank=True)
    end_date = models.DateField(_('end date'), null=True, blank=True)

    notes = models.TextField(_('notes'), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('pet responsibility')
        verbose_name_plural = _('pet responsibilities')
        ordering = ['responsibility_type', 'person__last_name']
        unique_together = ['pet', 'person', 'responsibility_type']

    def __str__(self):
        return f"{self.person} - {self.get_responsibility_type_display()} for {self.pet.name}"
