# T-024: Pet Profile Models

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement comprehensive pet profile models with medical data
**Related Story**: S-003
**Epoch**: 2
**Estimate**: 4 hours

### Constraints
**Allowed File Paths**: apps/vet_clinic/models/, apps/vet_clinic/
**Forbidden Paths**: apps/store/, apps/billing/

### Deliverables
- [ ] Pet model with comprehensive fields
- [ ] Species and breed management
- [ ] Medical conditions model
- [ ] Allergy tracking
- [ ] Weight history
- [ ] Microchip tracking
- [ ] Pet photo handling

### Implementation Details

#### Models
```python
class Pet(models.Model):
    """Comprehensive pet profile."""

    # Owner relationship
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='pets'
    )

    # Basic info
    name = models.CharField(max_length=100)
    species = models.CharField(max_length=50, choices=SPECIES_CHOICES)
    breed = models.CharField(max_length=100, blank=True)
    color = models.CharField(max_length=100, blank=True)
    sex = models.CharField(max_length=10, choices=SEX_CHOICES)
    birth_date = models.DateField(null=True, blank=True)
    birth_date_estimated = models.BooleanField(default=False)

    # Identification
    microchip_id = models.CharField(max_length=50, blank=True, unique=True, null=True)
    microchip_location = models.CharField(max_length=100, blank=True)
    registration_number = models.CharField(max_length=100, blank=True)

    # Status
    is_neutered = models.BooleanField(default=False)
    neutered_date = models.DateField(null=True, blank=True)
    is_deceased = models.BooleanField(default=False)
    deceased_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    # Physical
    photo = models.ImageField(upload_to='pets/photos/', null=True, blank=True)

    # Notes
    notes = models.TextField(blank=True)
    special_handling = models.TextField(blank=True)  # "Nervous", "Aggressive", etc.

    # Import tracking
    okvet_id = models.CharField(max_length=100, blank=True, db_index=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def age(self) -> str:
        """Return age in human-readable format."""
        if not self.birth_date:
            return "Unknown"
        delta = timezone.now().date() - self.birth_date
        years = delta.days // 365
        months = (delta.days % 365) // 30
        if years > 0:
            return f"{years} años, {months} meses"
        return f"{months} meses"

    @property
    def current_weight(self) -> Decimal | None:
        """Return most recent weight."""
        weight = self.weight_history.order_by('-date').first()
        return weight.weight_kg if weight else None


class PetWeight(models.Model):
    """Weight history tracking."""

    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='weight_history')
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2)
    date = models.DateField()
    notes = models.CharField(max_length=200, blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['pet', 'date']


class MedicalCondition(models.Model):
    """Chronic conditions and diagnoses."""

    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='conditions')
    name = models.CharField(max_length=200)
    diagnosis_date = models.DateField(null=True)
    diagnosed_by = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('managed', 'Managed'),
        ('resolved', 'Resolved'),
    ])
    notes = models.TextField(blank=True)
    requires_monitoring = models.BooleanField(default=False)


class Allergy(models.Model):
    """Allergy tracking."""

    SEVERITY_CHOICES = [
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
        ('life_threatening', 'Life Threatening'),
    ]

    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='allergies')
    allergen = models.CharField(max_length=200)
    allergy_type = models.CharField(max_length=50, choices=[
        ('food', 'Food'),
        ('medication', 'Medication'),
        ('environmental', 'Environmental'),
        ('contact', 'Contact'),
    ])
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    reaction_description = models.TextField(blank=True)
    discovered_date = models.DateField(null=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Allergies"
```

#### Species and Breed
```python
SPECIES_CHOICES = [
    ('dog', 'Perro'),
    ('cat', 'Gato'),
    ('bird', 'Ave'),
    ('rabbit', 'Conejo'),
    ('hamster', 'Hámster'),
    ('guinea_pig', 'Cobaya'),
    ('turtle', 'Tortuga'),
    ('fish', 'Pez'),
    ('ferret', 'Hurón'),
    ('reptile', 'Reptil'),
    ('other', 'Otro'),
]

# Breed database (loaded from fixture or managed in admin)
class Breed(models.Model):
    species = models.CharField(max_length=50, choices=SPECIES_CHOICES)
    name = models.CharField(max_length=100)
    name_es = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    size_category = models.CharField(max_length=20, blank=True)  # small, medium, large
    life_expectancy_years = models.IntegerField(null=True)
```

### Test Cases
- [ ] Pet creation with all fields
- [ ] Owner relationship works
- [ ] Age calculation accurate
- [ ] Weight history tracking
- [ ] Conditions management
- [ ] Allergies with severity
- [ ] Photo upload
- [ ] Microchip uniqueness

### Definition of Done
- [ ] All models migrated
- [ ] Admin interface for pets
- [ ] Age/weight properties work
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-001: Django Project Setup
- T-003: Authentication System
