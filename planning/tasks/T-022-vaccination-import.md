# T-022: Vaccination Import

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement management command to import vaccination records
**Related Story**: S-023
**Estimate**: 3 hours

### Constraints
**Allowed File Paths**: apps/migration/, apps/vet_clinic/
**Forbidden Paths**: None

### Deliverables
- [ ] import_okvet_vaccinations management command
- [ ] Vaccine name standardization
- [ ] Due date calculation
- [ ] Batch/lot number preservation
- [ ] Manufacturer tracking

### Implementation Details

#### Vaccination Model
```python
class Vaccination(models.Model):
    """Pet vaccination record."""

    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='vaccinations')

    # Vaccine info
    vaccine_name = models.CharField(max_length=200)
    vaccine_type = models.CharField(max_length=100)  # Standardized type
    manufacturer = models.CharField(max_length=200, blank=True)
    lot_number = models.CharField(max_length=100, blank=True)

    # Administration
    administered_date = models.DateField()
    administered_by = models.CharField(max_length=200)
    administration_site = models.CharField(max_length=100, blank=True)

    # Schedule
    next_due_date = models.DateField(null=True)
    is_booster = models.BooleanField(default=False)

    # Import tracking
    okvet_id = models.CharField(max_length=100, blank=True, db_index=True)

    class Meta:
        ordering = ['-administered_date']
```

#### Vaccine Standardization
```python
# Map various vaccine names to standard types
VACCINE_MAPPING = {
    # Dogs
    'polivalente': 'canine_distemper_combo',
    'parvovirus': 'canine_parvovirus',
    'moquillo': 'canine_distemper',
    'leptospira': 'canine_leptospirosis',
    'bordetella': 'canine_bordetella',
    'rabia': 'rabies',
    'antirrábica': 'rabies',

    # Cats
    'triple felina': 'feline_triple',
    'leucemia felina': 'feline_leukemia',
    'panleucopenia': 'feline_panleukopenia',
    'rinotraqueitis': 'feline_rhinotracheitis',
    'calicivirus': 'feline_calicivirus',
}

# Recommended intervals (days) for due date calculation
VACCINE_INTERVALS = {
    'rabies': 365,  # Annual
    'canine_distemper_combo': 365,
    'feline_triple': 365,
    'canine_bordetella': 180,  # 6 months
    'puppy_initial': 21,  # 3 weeks for puppy series
}
```

#### Field Mapping
```python
OKVET_VACCINE_MAPPING = {
    'id_vacuna': 'okvet_id',
    'id_mascota': 'pet_okvet_id',
    'nombre_vacuna': 'vaccine_name',
    'fecha_aplicacion': 'administered_date',
    'fecha_proxima': 'next_due_date',
    'lote': 'lot_number',
    'fabricante': 'manufacturer',
    'veterinario': 'administered_by',
    'notas': 'notes',
}
```

#### Due Date Calculation
```python
def calculate_next_due(
    self,
    vaccine_type: str,
    administered_date: date,
    pet_age_months: int = None
) -> date:
    """Calculate next due date based on vaccine type."""

    interval_days = VACCINE_INTERVALS.get(vaccine_type, 365)

    # Adjust for puppies/kittens (more frequent)
    if pet_age_months and pet_age_months < 4:
        if vaccine_type in ['canine_distemper_combo', 'feline_triple']:
            interval_days = 21  # 3 weeks

    return administered_date + timedelta(days=interval_days)
```

### Usage Examples
```bash
# Dry run
python manage.py import_okvet_vaccinations vaccinations.csv --dry-run

# Import with due date recalculation
python manage.py import_okvet_vaccinations vaccinations.csv --recalculate-due

# Full import
python manage.py import_okvet_vaccinations vaccinations.csv
```

### Test Cases
- [ ] Vaccinations import successfully
- [ ] Pet linking works
- [ ] Vaccine names standardized
- [ ] Due dates calculated
- [ ] Lot numbers preserved
- [ ] Dates parsed correctly
- [ ] Duplicates handled

### Definition of Done
- [ ] All vaccination records importable
- [ ] Standardized vaccine types
- [ ] Due dates accurate
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-018: Migration Models & Tracking
- T-020: Pet Import Command
