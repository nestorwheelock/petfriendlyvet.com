# T-062: Clinical Notes & Internal Documentation

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Full Stack Developer
**Objective**: Implement internal clinical notes and SOAP documentation
**Related Story**: S-008
**Epoch**: 6
**Estimate**: 4 hours

### Constraints
**Allowed File Paths**: apps/vet_clinic/, apps/appointments/
**Forbidden Paths**: None

### Deliverables
- [ ] ClinicalNote model
- [ ] SOAP note templates
- [ ] Internal staff-only notes
- [ ] Treatment protocols
- [ ] Clinical documentation views

### Implementation Details

#### Models
```python
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField

User = get_user_model()


class ClinicalNote(models.Model):
    """Internal clinical notes for appointments."""

    appointment = models.ForeignKey(
        'appointments.Appointment', on_delete=models.CASCADE,
        related_name='clinical_notes'
    )
    pet = models.ForeignKey(
        'vet_clinic.Pet', on_delete=models.CASCADE,
        related_name='clinical_notes'
    )

    NOTE_TYPES = [
        ('soap', 'SOAP Note'),
        ('progress', 'Nota de Progreso'),
        ('surgical', 'Nota Quirúrgica'),
        ('lab', 'Resultados de Laboratorio'),
        ('internal', 'Nota Interna'),
        ('followup', 'Seguimiento'),
    ]
    note_type = models.CharField(max_length=20, choices=NOTE_TYPES, default='soap')

    # SOAP Format
    subjective = models.TextField(blank=True)
    # Patient history, owner observations, symptoms

    objective = models.TextField(blank=True)
    # Physical exam, vital signs, test results

    assessment = models.TextField(blank=True)
    # Diagnosis, differential diagnoses

    plan = models.TextField(blank=True)
    # Treatment plan, medications, follow-up

    # General note content (for non-SOAP notes)
    content = models.TextField(blank=True)

    # Visibility
    is_internal = models.BooleanField(default=False)
    # Internal notes not visible to owner

    is_confidential = models.BooleanField(default=False)
    # Restricted to certain staff only

    # Attachments
    attachments = models.JSONField(default=list)
    # [{"file": "path/to/file", "type": "image", "description": "..."}]

    # Author
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, related_name='clinical_notes_written'
    )
    last_edited_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, related_name='+'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']


class VitalSigns(models.Model):
    """Vital signs recorded during exam."""

    clinical_note = models.OneToOneField(
        ClinicalNote, on_delete=models.CASCADE,
        related_name='vital_signs'
    )
    pet = models.ForeignKey(
        'vet_clinic.Pet', on_delete=models.CASCADE,
        related_name='vital_signs_history'
    )

    # Measurements
    weight_kg = models.DecimalField(
        max_digits=6, decimal_places=2, null=True
    )
    temperature_c = models.DecimalField(
        max_digits=4, decimal_places=1, null=True
    )
    heart_rate_bpm = models.IntegerField(null=True)
    respiratory_rate = models.IntegerField(null=True)

    # Assessment scores
    body_condition_score = models.IntegerField(null=True)
    # 1-9 scale
    pain_score = models.IntegerField(null=True)
    # 0-10 scale
    hydration_status = models.CharField(max_length=50, blank=True)

    # Observations
    mucous_membrane_color = models.CharField(max_length=50, blank=True)
    capillary_refill_time = models.CharField(max_length=20, blank=True)
    lymph_nodes = models.CharField(max_length=100, blank=True)

    notes = models.TextField(blank=True)

    recorded_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True
    )


class TreatmentProtocol(models.Model):
    """Standard treatment protocols for conditions."""

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    # Applicable to
    species = models.JSONField(default=list)
    conditions = models.JSONField(default=list)

    # Protocol steps
    steps = models.JSONField(default=list)
    # [
    #   {"order": 1, "action": "...", "medications": [...], "notes": "..."},
    #   {"order": 2, "action": "...", "duration": "7 days"}
    # ]

    # Medications typically used
    default_medications = models.JSONField(default=list)

    # Follow-up schedule
    followup_schedule = models.JSONField(default=list)
    # [{"days": 3, "type": "phone"}, {"days": 7, "type": "visit"}]

    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class TreatmentRecord(models.Model):
    """Record of treatment given during appointment."""

    clinical_note = models.ForeignKey(
        ClinicalNote, on_delete=models.CASCADE,
        related_name='treatments'
    )
    pet = models.ForeignKey(
        'vet_clinic.Pet', on_delete=models.CASCADE,
        related_name='treatment_records'
    )

    # Treatment details
    treatment_type = models.CharField(max_length=100)
    description = models.TextField()

    # Protocol used (if applicable)
    protocol = models.ForeignKey(
        TreatmentProtocol, on_delete=models.SET_NULL,
        null=True, blank=True
    )

    # Medications administered
    medications = models.JSONField(default=list)
    # [{"name": "...", "dose": "...", "route": "IV", "time": "..."}]

    # Procedures performed
    procedures = models.JSONField(default=list)
    # [{"name": "...", "duration": "...", "notes": "..."}]

    # Response/outcome
    response = models.TextField(blank=True)
    complications = models.TextField(blank=True)

    performed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True
    )
    performed_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)


class LabResult(models.Model):
    """Laboratory test results."""

    clinical_note = models.ForeignKey(
        ClinicalNote, on_delete=models.CASCADE,
        null=True, blank=True, related_name='lab_results'
    )
    pet = models.ForeignKey(
        'vet_clinic.Pet', on_delete=models.CASCADE,
        related_name='lab_results'
    )

    TEST_TYPES = [
        ('blood', 'Análisis de Sangre'),
        ('urine', 'Urianálisis'),
        ('fecal', 'Examen Fecal'),
        ('cytology', 'Citología'),
        ('biopsy', 'Biopsia'),
        ('imaging', 'Imagen'),
        ('other', 'Otro'),
    ]
    test_type = models.CharField(max_length=20, choices=TEST_TYPES)
    test_name = models.CharField(max_length=200)

    # Results
    results = models.JSONField(default=dict)
    # {"WBC": {"value": 12.5, "unit": "10^9/L", "range": "6-17", "flag": "normal"}}

    interpretation = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)

    # Files
    result_file = models.FileField(
        upload_to='lab_results/', null=True, blank=True
    )
    images = models.JSONField(default=list)

    # External lab
    external_lab = models.CharField(max_length=200, blank=True)
    external_reference = models.CharField(max_length=100, blank=True)

    sample_collected_at = models.DateTimeField()
    results_received_at = models.DateTimeField(null=True)

    ordered_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, related_name='lab_orders'
    )
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='lab_reviews'
    )
    reviewed_at = models.DateTimeField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sample_collected_at']
```

#### Clinical Notes Views
```python
from django.views.generic import CreateView, UpdateView, DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin


class ClinicalNoteCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create new clinical note."""

    model = ClinicalNote
    template_name = 'vet_clinic/clinical_note_form.html'
    permission_required = 'vet_clinic.add_clinicalnote'
    fields = [
        'note_type', 'subjective', 'objective', 'assessment', 'plan',
        'content', 'is_internal', 'is_confidential'
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        appointment_id = self.kwargs.get('appointment_id')
        context['appointment'] = Appointment.objects.get(id=appointment_id)
        context['protocols'] = TreatmentProtocol.objects.filter(is_active=True)
        return context

    def form_valid(self, form):
        form.instance.appointment_id = self.kwargs.get('appointment_id')
        form.instance.pet = form.instance.appointment.pet
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class SOAPNoteView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Edit SOAP note with structured form."""

    model = ClinicalNote
    template_name = 'vet_clinic/soap_note_form.html'
    permission_required = 'vet_clinic.change_clinicalnote'
    fields = ['subjective', 'objective', 'assessment', 'plan']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vital_signs_form'] = VitalSignsForm(
            instance=getattr(self.object, 'vital_signs', None)
        )
        context['previous_notes'] = ClinicalNote.objects.filter(
            pet=self.object.pet
        ).exclude(pk=self.object.pk).order_by('-created_at')[:5]
        return context

    def form_valid(self, form):
        form.instance.last_edited_by = self.request.user
        return super().form_valid(form)


class PetMedicalHistoryView(LoginRequiredMixin, DetailView):
    """Complete medical history for a pet."""

    model = Pet
    template_name = 'vet_clinic/pet_medical_history.html'
    context_object_name = 'pet'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pet = self.object

        # Clinical notes (excluding internal if not staff)
        notes = pet.clinical_notes.all()
        if not self.request.user.is_staff:
            notes = notes.filter(is_internal=False)
        context['clinical_notes'] = notes.order_by('-created_at')

        # Vital signs history
        context['vital_signs'] = pet.vital_signs_history.order_by('-recorded_at')

        # Lab results
        context['lab_results'] = pet.lab_results.order_by('-sample_collected_at')

        # Treatment records
        context['treatments'] = pet.treatment_records.order_by('-performed_at')

        # Vaccinations
        context['vaccinations'] = pet.vaccination_records.order_by('-administered_date')

        return context
```

### Test Cases
- [ ] SOAP note creation works
- [ ] Vital signs recording works
- [ ] Internal notes hidden from owners
- [ ] Lab results display correctly
- [ ] Treatment protocol application works
- [ ] Medical history timeline accurate
- [ ] Confidential notes restricted

### Definition of Done
- [ ] Clinical notes system complete
- [ ] SOAP format functional
- [ ] Internal notes protected
- [ ] Medical history view working
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-024: Pet Models
- T-020: Appointment Models
