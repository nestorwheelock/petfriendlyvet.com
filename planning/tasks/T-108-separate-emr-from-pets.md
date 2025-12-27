# T-108: Separate EMR (Medical Records) from Pets Module

> **REQUIRED READING:** Before implementation, review [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)

## AI Coding Brief

**Role**: Backend Architect / Django Developer
**Objective**: Refactor the codebase to separate medical/EMR functionality from the pets module, moving it to the practice module for better separation of concerns.

### Background

Currently, the `pets` app contains both pet identity/ownership data AND medical records. This tight coupling limits reusability:

- A pet store might want pet tracking without medical baggage
- A pet sitting service just needs basic pet info
- Someone tracking friends' pets doesn't need health data

### Current State (Tightly Coupled)

```
apps/pets/models.py
├── Pet                    # Identity & ownership (KEEP)
├── Vaccination            # Medical → MOVE
├── MedicalCondition       # Medical → MOVE
├── Visit                  # Medical → MOVE
├── Medication             # Medical → MOVE
├── ClinicalNote           # Medical → MOVE
├── WeightRecord           # Medical → MOVE
└── PetDocument            # Medical → MOVE (rename to MedicalDocument)
```

### Target State (Separated)

```
apps/pets/models.py           apps/practice/models.py
├── Pet                       ├── PatientRecord (NEW - links Pet to practice)
│   ├── name                  ├── Vaccination
│   ├── species               ├── MedicalCondition
│   ├── breed                 ├── Visit
│   ├── gender                ├── Medication
│   ├── date_of_birth         ├── ClinicalNote
│   ├── photo                 ├── WeightRecord
│   ├── microchip_id          └── MedicalDocument
│   ├── owner (Party)
│   ├── is_neutered
│   ├── is_archived
│   └── notes (general)
```

### New Model: PatientRecord

```python
class PatientRecord(BaseModel):
    """Links a Pet to this practice's medical system."""

    pet = models.OneToOneField(
        'pets.Pet',
        on_delete=models.CASCADE,
        related_name='patient_record'
    )
    patient_number = models.CharField(max_length=20, unique=True)
    primary_veterinarian = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='primary_patients'
    )
    first_visit_date = models.DateField(null=True, blank=True)

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('transferred', 'Transferred'),
        ('deceased', 'Deceased'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    referring_practice = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)  # Medical-specific notes

    class Meta:
        ordering = ['patient_number']

    def __str__(self):
        return f"{self.patient_number} - {self.pet.name}"
```

### Constraints

**Allowed File Paths**:
- `apps/pets/models.py` - Remove medical models
- `apps/practice/models.py` - Add medical models
- `apps/practice/admin.py` - Register new models
- `apps/pets/views.py` - Update imports
- `apps/practice/views.py` - Add EMR views if needed
- `templates/pets/*.html` - Update to use practice models
- `apps/pets/migrations/` - Create migration
- `apps/practice/migrations/` - Create migration

**Forbidden Paths**:
- Do not modify unrelated apps
- Do not change Pet model core fields

### Migration Strategy

1. **Phase 1: Add models to practice** (non-destructive)
   - Create PatientRecord model in practice
   - Create copies of medical models in practice
   - Run `makemigrations practice`

2. **Phase 2: Data migration**
   - Create data migration to copy records
   - Link existing pets to new PatientRecords
   - Migrate medical records to practice tables

3. **Phase 3: Update references**
   - Update views to import from practice
   - Update templates
   - Update admin registrations

4. **Phase 4: Remove old models** (after verification)
   - Remove medical models from pets
   - Run `makemigrations pets`

### Definition of Done

- [ ] PatientRecord model created in practice app
- [ ] All medical models moved to practice app
- [ ] Data migration preserves all existing records
- [ ] Foreign keys updated (medical models → PatientRecord or Pet)
- [ ] Views updated to import from correct locations
- [ ] Templates updated to use new model paths
- [ ] Admin registrations updated
- [ ] All existing tests pass (may need updates)
- [ ] New tests for PatientRecord model
- [ ] No circular import issues
- [ ] Pet model works standalone without medical models

### Test Cases

1. **PatientRecord Creation**
   - Create a Pet without PatientRecord (valid - not every pet is a patient)
   - Create PatientRecord for a Pet (valid)
   - Attempt duplicate PatientRecord for same Pet (should fail - OneToOne)

2. **Medical Records**
   - Create Vaccination linked to PatientRecord
   - Create Visit linked to PatientRecord
   - Query all medical history for a patient

3. **Backward Compatibility**
   - Existing pet detail views still work
   - Existing medical data accessible through new structure

### Related Stories

- Party Pattern Architecture (Person, Organization, Group)
- Staff vs Customer Portal separation

### Estimated Effort

4-6 hours (including data migration and testing)
