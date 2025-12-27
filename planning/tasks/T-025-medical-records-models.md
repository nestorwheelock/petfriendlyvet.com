# T-025: Medical Records Models

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md and [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement comprehensive medical records system
**Related Story**: S-003
**Epoch**: 2
**Estimate**: 4 hours

### Constraints
**Allowed File Paths**: apps/vet_clinic/models/
**Forbidden Paths**: apps/store/, apps/billing/

### Deliverables
- [ ] MedicalRecord model with SOAP notes
- [ ] Vital signs tracking
- [ ] Medication administration records
- [ ] Lab results model
- [ ] Clinical notes
- [ ] Record attachments

### Implementation Details

#### Models
```python
class MedicalRecord(models.Model):
    """Individual medical record / visit."""

    RECORD_TYPES = [
        ('consultation', 'Consulta'),
        ('surgery', 'Cirugía'),
        ('vaccination', 'Vacunación'),
        ('emergency', 'Emergencia'),
        ('follow_up', 'Seguimiento'),
        ('grooming', 'Estética'),
        ('lab_work', 'Laboratorio'),
        ('imaging', 'Imagenología'),
        ('dental', 'Dental'),
        ('hospitalization', 'Hospitalización'),
        ('other', 'Otro'),
    ]

    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='medical_records')

    # Classification
    record_type = models.CharField(max_length=50, choices=RECORD_TYPES)
    date = models.DateTimeField()

    # SOAP Notes
    chief_complaint = models.TextField(blank=True)  # Reason for visit
    subjective = models.TextField(blank=True)  # S - Owner's report
    objective = models.TextField(blank=True)  # O - Physical exam findings
    assessment = models.TextField(blank=True)  # A - Diagnosis/assessment
    plan = models.TextField(blank=True)  # P - Treatment plan

    # Additional notes
    internal_notes = models.TextField(blank=True)  # Staff-only notes
    followup_notes = models.TextField(blank=True)

    # Status
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('complete', 'Complete'),
        ('signed', 'Signed'),
    ], default='draft')

    # Staff
    veterinarian = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='medical_records'
    )
    signed_at = models.DateTimeField(null=True)
    signed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='signed_records'
    )

    # Billing link
    invoice = models.ForeignKey(
        'billing.Invoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Import tracking
    okvet_id = models.CharField(max_length=100, blank=True, db_index=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']


class VitalSigns(models.Model):
    """Vital signs recorded during visit."""

    record = models.OneToOneField(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='vitals'
    )

    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    temperature_c = models.DecimalField(max_digits=4, decimal_places=1, null=True)
    heart_rate_bpm = models.IntegerField(null=True)  # beats per minute
    respiratory_rate = models.IntegerField(null=True)  # breaths per minute
    blood_pressure_systolic = models.IntegerField(null=True)
    blood_pressure_diastolic = models.IntegerField(null=True)
    capillary_refill_seconds = models.DecimalField(max_digits=3, decimal_places=1, null=True)
    hydration_status = models.CharField(max_length=50, blank=True)
    body_condition_score = models.IntegerField(null=True)  # 1-9 scale
    pain_score = models.IntegerField(null=True)  # 0-10 scale

    notes = models.TextField(blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)


class Diagnosis(models.Model):
    """Diagnoses associated with a record."""

    record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='diagnoses'
    )
    name = models.CharField(max_length=500)
    code = models.CharField(max_length=50, blank=True)  # Internal code if used
    is_primary = models.BooleanField(default=False)
    is_rule_out = models.BooleanField(default=False)  # Suspected but not confirmed
    notes = models.TextField(blank=True)


class MedicationAdministered(models.Model):
    """Medications given during visit."""

    record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='medications_given'
    )
    medication_name = models.CharField(max_length=200)
    dose = models.CharField(max_length=100)
    route = models.CharField(max_length=50, choices=[
        ('oral', 'Oral'),
        ('injectable_im', 'IM Injection'),
        ('injectable_iv', 'IV Injection'),
        ('injectable_sq', 'SQ Injection'),
        ('topical', 'Topical'),
        ('ophthalmic', 'Ophthalmic'),
        ('otic', 'Otic'),
    ])
    administered_at = models.DateTimeField()
    administered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    lot_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)


class LabResult(models.Model):
    """Laboratory results."""

    record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='lab_results'
    )
    test_name = models.CharField(max_length=200)
    test_type = models.CharField(max_length=50, choices=[
        ('blood', 'Blood Work'),
        ('urinalysis', 'Urinalysis'),
        ('fecal', 'Fecal'),
        ('cytology', 'Cytology'),
        ('biopsy', 'Biopsy'),
        ('culture', 'Culture'),
        ('other', 'Other'),
    ])
    value = models.CharField(max_length=100, blank=True)
    unit = models.CharField(max_length=50, blank=True)
    reference_range = models.CharField(max_length=100, blank=True)
    is_abnormal = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    performed_at = models.DateTimeField(null=True)
    reported_at = models.DateTimeField(null=True)
    attachment = models.FileField(upload_to='lab_results/', null=True, blank=True)


class RecordAttachment(models.Model):
    """Attachments for medical records."""

    record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to='medical_records/')
    file_type = models.CharField(max_length=50, choices=[
        ('image', 'Image'),
        ('xray', 'X-Ray'),
        ('ultrasound', 'Ultrasound'),
        ('lab_report', 'Lab Report'),
        ('consent', 'Consent Form'),
        ('referral', 'Referral'),
        ('other', 'Other'),
    ])
    description = models.CharField(max_length=500, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
```

### Test Cases
- [ ] Medical record CRUD
- [ ] SOAP notes saved
- [ ] Vital signs associated
- [ ] Diagnoses linked
- [ ] Medications tracked
- [ ] Lab results with abnormal flag
- [ ] Attachments uploaded
- [ ] Record signing workflow

### Definition of Done
- [ ] All models migrated
- [ ] Admin interface complete
- [ ] SOAP workflow functional
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-024: Pet Profile Models
