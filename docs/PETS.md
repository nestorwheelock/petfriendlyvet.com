# Pets Module

The `apps.pets` module manages pet profiles, medical records, vaccinations, visits, medications, and clinical documentation for the veterinary clinic.

## Table of Contents

- [Overview](#overview)
- [Models](#models)
  - [Pet](#pet)
  - [MedicalCondition](#medicalcondition)
  - [Vaccination](#vaccination)
  - [Visit](#visit)
  - [Medication](#medication)
  - [ClinicalNote](#clinicalnote)
  - [WeightRecord](#weightrecord)
  - [PetDocument](#petdocument)
- [Views](#views)
- [URL Patterns](#url-patterns)
- [Workflows](#workflows)
  - [Pet Registration](#pet-registration)
  - [Medical Records](#medical-records)
  - [Vaccination Tracking](#vaccination-tracking)
- [Species and Breeds](#species-and-breeds)
- [Integration Points](#integration-points)
- [Query Examples](#query-examples)
- [Testing](#testing)

## Overview

The pets module handles:

- **Pet Profiles** - Basic info, species, breed, weight, microchip
- **Medical Conditions** - Allergies, chronic conditions, injuries
- **Vaccinations** - Vaccine records with due date tracking
- **Visits** - Veterinary visit history with diagnosis/treatment
- **Medications** - Prescription and medication tracking
- **Clinical Notes** - Staff-only medical notes
- **Weight Tracking** - Weight history over time
- **Documents** - Lab results, x-rays, certificates

```
┌─────────────────┐
│      Pet        │
│   (profile)     │
└───────┬─────────┘
        │
        ├──────────────┬──────────────┬──────────────┬──────────────┐
        ▼              ▼              ▼              ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  Medical    │ │ Vaccination │ │   Visit     │ │ Medication  │ │  Document   │
│ Condition   │ │  (vaccines) │ │  (history)  │ │ (prescr.)   │ │  (files)    │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

## Models

### Pet

Location: `apps/pets/models.py`

Core pet profile model.

```python
SPECIES_CHOICES = [
    ('dog', 'Dog'),
    ('cat', 'Cat'),
    ('bird', 'Bird'),
    ('rabbit', 'Rabbit'),
    ('hamster', 'Hamster'),
    ('guinea_pig', 'Guinea Pig'),
    ('reptile', 'Reptile'),
    ('other', 'Other'),
]

GENDER_CHOICES = [
    ('male', 'Male'),
    ('female', 'Female'),
    ('unknown', 'Unknown'),
]

class Pet(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pets')
    name = models.CharField(max_length=100)
    species = models.CharField(max_length=20, choices=SPECIES_CHOICES, default='dog')
    breed = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='unknown')
    date_of_birth = models.DateField(null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    microchip_id = models.CharField(max_length=50, blank=True)
    is_neutered = models.BooleanField(default=False)
    photo = models.ImageField(upload_to='pets/', null=True, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
```

### MedicalCondition

Medical conditions, allergies, and chronic issues.

```python
CONDITION_TYPES = [
    ('allergy', 'Allergy'),
    ('chronic', 'Chronic Condition'),
    ('injury', 'Injury'),
    ('other', 'Other'),
]

class MedicalCondition(models.Model):
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='conditions')
    name = models.CharField(max_length=200)
    condition_type = models.CharField(max_length=20, choices=CONDITION_TYPES, default='other')
    diagnosed_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Vaccination

Vaccination records with due date tracking.

```python
class Vaccination(models.Model):
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='vaccinations')
    vaccine_name = models.CharField(max_length=200)
    date_administered = models.DateField()
    next_due_date = models.DateField(null=True, blank=True)
    administered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    batch_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    # Reminder tracking
    reminder_sent = models.BooleanField(default=False)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
```

### Visit

Veterinary visit records.

```python
class Visit(models.Model):
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='visits')
    date = models.DateTimeField()
    reason = models.CharField(max_length=500)
    diagnosis = models.TextField(blank=True)
    treatment = models.TextField(blank=True)
    veterinarian = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """Update pet's weight if recorded during visit."""
        super().save(*args, **kwargs)
        if self.weight_kg:
            self.pet.weight_kg = self.weight_kg
            self.pet.save(update_fields=['weight_kg', 'updated_at'])
```

### Medication

Medication records and prescriptions.

```python
class Medication(models.Model):
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='medications')
    name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    prescribing_vet = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_active(self):
        """Check if medication course is currently active."""
        today = date.today()
        if today < self.start_date:
            return False
        if self.end_date and today > self.end_date:
            return False
        return True
```

### ClinicalNote

Staff-only clinical notes.

```python
CLINICAL_NOTE_TYPES = [
    ('observation', 'Observation'),
    ('treatment', 'Treatment Note'),
    ('followup', 'Follow-up'),
    ('lab', 'Lab Results'),
    ('other', 'Other'),
]

class ClinicalNote(models.Model):
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='clinical_notes')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    visit = models.ForeignKey(Visit, on_delete=models.SET_NULL, null=True, blank=True)
    note = models.TextField()
    note_type = models.CharField(max_length=20, choices=CLINICAL_NOTE_TYPES, default='observation')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### WeightRecord

Weight tracking history.

```python
class WeightRecord(models.Model):
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='weight_records')
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2)
    recorded_date = models.DateField(auto_now_add=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """Update pet's current weight when record is created."""
        super().save(*args, **kwargs)
        self.pet.weight_kg = self.weight_kg
        self.pet.save(update_fields=['weight_kg', 'updated_at'])
```

### PetDocument

Documents and files associated with a pet.

```python
DOCUMENT_TYPES = [
    ('lab_result', 'Lab Result'),
    ('xray', 'X-Ray'),
    ('photo', 'Photo'),
    ('certificate', 'Certificate'),
    ('prescription', 'Prescription'),
    ('referral', 'Referral'),
    ('other', 'Other'),
]

class PetDocument(models.Model):
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=200)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, default='other')
    file = models.FileField(upload_to='pet_documents/', null=True, blank=True)
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    visible_to_owner = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

## Views

Location: `apps/pets/views.py`

### OwnerDashboardView

Dashboard showing owner's pets and upcoming appointments.

```python
class OwnerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'pets/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['pets'] = Pet.objects.filter(owner=user).order_by('name')
        context['upcoming_appointments'] = Appointment.objects.filter(
            owner=user,
            scheduled_start__gte=timezone.now(),
            status__in=['scheduled', 'confirmed']
        ).select_related('pet', 'service', 'veterinarian')[:5]
        return context
```

### Pet CRUD Views

```python
class PetListView(LoginRequiredMixin, ListView):
    """List all pets belonging to the logged-in user."""

class PetDetailView(LoginRequiredMixin, DetailView):
    """View details of a specific pet with vaccinations, conditions, appointments."""

class PetCreateView(LoginRequiredMixin, CreateView):
    """Create a new pet (auto-assigns owner)."""

class PetUpdateView(LoginRequiredMixin, UpdateView):
    """Edit an existing pet (owner-only access)."""
```

## URL Patterns

Location: `apps/pets/urls.py`

```python
app_name = 'pets'

urlpatterns = [
    path('', views.OwnerDashboardView.as_view(), name='dashboard'),
    path('pets/', views.PetListView.as_view(), name='pet_list'),
    path('pets/add/', views.PetCreateView.as_view(), name='pet_add'),
    path('pets/<int:pk>/', views.PetDetailView.as_view(), name='pet_detail'),
    path('pets/<int:pk>/edit/', views.PetUpdateView.as_view(), name='pet_edit'),

    # Document management
    path('pets/<int:pet_pk>/documents/', document_views.DocumentListView.as_view(), name='document_list'),
    path('pets/<int:pet_pk>/documents/upload/', document_views.DocumentUploadView.as_view(), name='document_upload'),
    path('pets/<int:pet_pk>/documents/<int:pk>/delete/', document_views.DocumentDeleteView.as_view(), name='document_delete'),
]
```

## Workflows

### Pet Registration

```python
from apps.pets.models import Pet

# Register new pet
pet = Pet.objects.create(
    owner=user,
    name='Max',
    species='dog',
    breed='Golden Retriever',
    gender='male',
    date_of_birth=date(2020, 5, 15),
    weight_kg=Decimal('28.5'),
    microchip_id='985141000123456',
    is_neutered=True,
    notes='Friendly, loves water',
)

# Check age
print(f"Age: {pet.age_years} years")  # e.g., "Age: 4 years"
```

### Medical Records

```python
from apps.pets.models import MedicalCondition, Medication

# Add allergy
allergy = MedicalCondition.objects.create(
    pet=pet,
    name='Chicken protein allergy',
    condition_type='allergy',
    diagnosed_date=date(2022, 3, 10),
    notes='Causes skin irritation and digestive issues',
    is_active=True,
)

# Add medication
medication = Medication.objects.create(
    pet=pet,
    name='Apoquel',
    dosage='16mg',
    frequency='Once daily with food',
    start_date=date(2024, 1, 15),
    end_date=date(2024, 2, 15),
    prescribing_vet=veterinarian,
    notes='For allergy management',
)

# Check if active
print(f"Medication active: {medication.is_active}")
```

### Vaccination Tracking

```python
from apps.pets.models import Vaccination
from datetime import date
from dateutil.relativedelta import relativedelta

# Record vaccination
vaccination = Vaccination.objects.create(
    pet=pet,
    vaccine_name='Rabies',
    date_administered=date.today(),
    next_due_date=date.today() + relativedelta(years=1),
    administered_by=veterinarian,
    batch_number='RV-2024-001234',
    notes='3-year vaccine administered',
)

# Check status
if vaccination.is_overdue:
    print("OVERDUE: Send reminder!")
elif vaccination.is_due_soon:
    print("Due within 30 days")
```

### Recording Visits

```python
from apps.pets.models import Visit, ClinicalNote
from django.utils import timezone

# Create visit record
visit = Visit.objects.create(
    pet=pet,
    date=timezone.now(),
    reason='Annual wellness exam',
    diagnosis='Healthy, mild tartar buildup',
    treatment='Recommended dental cleaning in 6 months',
    veterinarian=veterinarian,
    weight_kg=Decimal('29.2'),
    follow_up_date=date.today() + relativedelta(months=6),
    notes='Vaccinations up to date. Continue current diet.',
)
# Pet weight is automatically updated to 29.2kg

# Add clinical note
note = ClinicalNote.objects.create(
    pet=pet,
    author=veterinarian,
    visit=visit,
    note='Heart and lungs clear. No abnormalities on palpation.',
    note_type='observation',
)
```

## Species and Breeds

### Supported Species

| Species | Common Breeds |
|---------|---------------|
| `dog` | Labrador, Golden Retriever, German Shepherd, Bulldog, etc. |
| `cat` | Persian, Siamese, Maine Coon, British Shorthair, etc. |
| `bird` | Parakeet, Cockatiel, Parrot, Canary, etc. |
| `rabbit` | Holland Lop, Mini Rex, Lionhead, etc. |
| `hamster` | Syrian, Dwarf, Roborovski, etc. |
| `guinea_pig` | American, Abyssinian, Peruvian, etc. |
| `reptile` | Bearded Dragon, Gecko, Ball Python, etc. |
| `other` | Ferrets, hedgehogs, etc. |

## Integration Points

### With Appointments Module

```python
from apps.appointments.models import Appointment
from apps.pets.models import Pet

# Get upcoming appointments for a pet
pet = Pet.objects.get(pk=pet_id)
upcoming = Appointment.objects.filter(
    pet=pet,
    scheduled_start__gte=timezone.now(),
    status__in=['scheduled', 'confirmed']
).order_by('scheduled_start')
```

### With Pharmacy Module

```python
from apps.pharmacy.models import Prescription
from apps.pets.models import Pet

# Get active prescriptions for a pet
pet = Pet.objects.get(pk=pet_id)
prescriptions = Prescription.objects.filter(
    pet=pet,
    status='active'
).select_related('medication')
```

### With Referrals Module

```python
from apps.referrals.models import Referral
from apps.pets.models import Pet

# Get referral history for a pet
pet = Pet.objects.get(pk=pet_id)
referrals = pet.specialist_referrals.select_related('specialist').order_by('-created_at')
```

### With CRM Module

```python
from apps.crm.models import OwnerProfile, CustomerTag

# Tag owners with multiple pets
owners_with_multiple_pets = User.objects.annotate(
    pet_count=Count('pets')
).filter(pet_count__gte=3)

for owner in owners_with_multiple_pets:
    profile = owner.owner_profile
    tag = CustomerTag.objects.get(name='Multiple Pets')
    profile.tags.add(tag)
```

## Query Examples

### Pet Queries

```python
from apps.pets.models import Pet
from django.db.models import Count

# Pets by species
species_counts = Pet.objects.values('species').annotate(
    count=Count('id')
).order_by('-count')

# Pets needing weight check (no weight in 3 months)
three_months_ago = date.today() - timedelta(days=90)
needs_weight = Pet.objects.filter(
    weight_records__recorded_date__lt=three_months_ago
).distinct()

# Unaltered pets (not neutered/spayed)
unaltered = Pet.objects.filter(is_neutered=False)

# Pets with active conditions
with_conditions = Pet.objects.filter(
    conditions__is_active=True
).distinct()
```

### Vaccination Queries

```python
from apps.pets.models import Vaccination
from datetime import date, timedelta

# Overdue vaccinations
overdue = Vaccination.objects.filter(
    next_due_date__lt=date.today()
).select_related('pet', 'pet__owner')

# Due within 30 days
due_soon = Vaccination.objects.filter(
    next_due_date__gte=date.today(),
    next_due_date__lte=date.today() + timedelta(days=30)
).select_related('pet', 'pet__owner')

# Needing reminders
needs_reminder = Vaccination.objects.filter(
    next_due_date__lte=date.today() + timedelta(days=30),
    reminder_sent=False
)

# Vaccination history for pet
pet_vaccines = Vaccination.objects.filter(
    pet=pet
).order_by('-date_administered')
```

### Visit Queries

```python
from apps.pets.models import Visit
from django.db.models import Count
from django.db.models.functions import TruncMonth

# Visits this month
this_month = Visit.objects.filter(
    date__month=date.today().month,
    date__year=date.today().year
)

# Monthly visit trends
monthly_visits = Visit.objects.annotate(
    month=TruncMonth('date')
).values('month').annotate(
    count=Count('id')
).order_by('-month')[:12]

# Visits requiring follow-up
needs_followup = Visit.objects.filter(
    follow_up_date__lte=date.today() + timedelta(days=7),
    follow_up_date__gte=date.today()
)
```

### Medication Queries

```python
from apps.pets.models import Medication
from datetime import date

# Active medications
active_meds = Medication.objects.filter(
    start_date__lte=date.today()
).exclude(
    end_date__lt=date.today()
)

# Medications ending soon (within 7 days)
ending_soon = Medication.objects.filter(
    end_date__gte=date.today(),
    end_date__lte=date.today() + timedelta(days=7)
)
```

### Weight Tracking Queries

```python
from apps.pets.models import WeightRecord
from django.db.models import Avg

# Weight history for pet
weight_history = WeightRecord.objects.filter(
    pet=pet
).order_by('recorded_date')

# Average weight by month
monthly_avg = WeightRecord.objects.filter(
    pet=pet
).annotate(
    month=TruncMonth('recorded_date')
).values('month').annotate(
    avg_weight=Avg('weight_kg')
).order_by('month')
```

## Testing

### Unit Tests

Location: `tests/test_pets.py`

```bash
# Run pets unit tests
python -m pytest tests/test_pets.py -v
```

### Browser Tests

Location: `tests/e2e/browser/test_pets.py`

```bash
# Run pets browser tests
python -m pytest tests/e2e/browser/test_pets.py -v

# Run with visible browser
python -m pytest tests/e2e/browser/test_pets.py -v --headed --slowmo=500
```

### Key Test Scenarios

1. **Pet Profiles**
   - Create pet with all fields
   - Age calculation
   - Owner access control

2. **Medical Records**
   - Add conditions and allergies
   - Active/inactive status

3. **Vaccinations**
   - Record vaccination
   - Due date tracking
   - Overdue detection

4. **Visits**
   - Create visit record
   - Auto-update pet weight
   - Follow-up tracking

5. **Documents**
   - Upload documents
   - Owner visibility control
   - Document type categorization
