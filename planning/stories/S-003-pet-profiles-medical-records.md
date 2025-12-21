# S-003: Pet Profiles + Medical Records

**Story Type:** User Story
**Priority:** High
**Epoch:** 2
**Status:** PENDING

## User Story

**As a** pet owner
**I want to** view and manage my pet's profile and medical records
**So that** I can track their health history and share information with the vet easily

**As a** veterinary staff member
**I want to** access and update pet medical records
**So that** I can provide informed care and maintain accurate health histories

## Acceptance Criteria

### Pet Profiles (Owner View)
- [ ] Owner can add pets to their account
- [ ] Pet profile includes: name, species, breed, birthdate, weight, photo
- [ ] Owner can update basic pet information
- [ ] Owner can view vaccination history
- [ ] Owner can view visit history
- [ ] Owner can upload documents/photos

### Pet Profiles (Staff View)
- [ ] Staff can search for pets by name or owner
- [ ] Staff can view complete medical history
- [ ] Staff can add clinical notes (internal only)
- [ ] Staff can update vaccinations
- [ ] Staff can record treatments and prescriptions

### Medical Records
- [ ] Vaccination records with dates and next-due reminders
- [ ] Visit history with notes
- [ ] Medication history
- [ ] Allergies and conditions flagged
- [ ] Weight tracking over time
- [ ] Document storage (lab results, X-rays, etc.)

### Privacy & Access Control
- [ ] Owners only see their own pets
- [ ] Staff notes are internal only (not visible to owners)
- [ ] Medical records are read-only for owners
- [ ] Audit log for all medical record changes

### AI Integration
- [ ] AI can retrieve pet information during chat
- [ ] AI can show vaccination due dates
- [ ] AI can summarize pet's recent visits
- [ ] Staff AI can search and update records

## Technical Requirements

### Package: django-vet-clinic

```python
# models.py

class Pet(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pets')
    name = models.CharField(max_length=100)
    species = models.CharField(max_length=50, choices=SPECIES_CHOICES)
    breed = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    photo = models.ImageField(upload_to='pets/', null=True, blank=True)
    microchip_id = models.CharField(max_length=50, blank=True)
    is_neutered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

SPECIES_CHOICES = [
    ('dog', 'Perro / Dog'),
    ('cat', 'Gato / Cat'),
    ('bird', 'Ave / Bird'),
    ('reptile', 'Reptil / Reptile'),
    ('small_mammal', 'Mamífero pequeño / Small Mammal'),
    ('other', 'Otro / Other'),
]


class MedicalCondition(models.Model):
    """Allergies, chronic conditions, etc."""
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='conditions')
    name = models.CharField(max_length=200)
    condition_type = models.CharField(max_length=50)  # allergy, chronic, etc.
    notes = models.TextField(blank=True)
    diagnosed_date = models.DateField(null=True)
    is_active = models.BooleanField(default=True)


class Vaccination(models.Model):
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='vaccinations')
    vaccine_name = models.CharField(max_length=100)
    date_administered = models.DateField()
    next_due_date = models.DateField(null=True)
    batch_number = models.CharField(max_length=50, blank=True)
    administered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)


class Visit(models.Model):
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='visits')
    date = models.DateTimeField()
    reason = models.CharField(max_length=200)
    diagnosis = models.TextField(blank=True)
    treatment = models.TextField(blank=True)
    veterinarian = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    follow_up_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ClinicalNote(models.Model):
    """Internal notes not visible to pet owners"""
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='clinical_notes')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    content = models.TextField()
    is_internal = models.BooleanField(default=True)  # Not shown to owner
    created_at = models.DateTimeField(auto_now_add=True)


class Medication(models.Model):
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='medications')
    visit = models.ForeignKey(Visit, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True)
    prescribing_vet = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)


class PetDocument(models.Model):
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=200)
    document_type = models.CharField(max_length=50)  # lab_result, xray, certificate, etc.
    file = models.FileField(upload_to='pet_documents/')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    visit = models.ForeignKey(Visit, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class WeightRecord(models.Model):
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='weight_history')
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2)
    date = models.DateField()
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
```

### AI Tools (Epoch 2 additions)

```python
EPOCH_2_TOOLS = EPOCH_1_TOOLS + [
    {
        "name": "get_pet_profile",
        "description": "Get information about a user's pet",
        "parameters": {
            "type": "object",
            "properties": {
                "pet_id": {"type": "integer"},
                "include_medical": {"type": "boolean", "default": False}
            },
            "required": ["pet_id"]
        }
    },
    {
        "name": "list_user_pets",
        "description": "List all pets belonging to the current user",
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "name": "get_vaccination_status",
        "description": "Get vaccination status and upcoming due dates for a pet",
        "parameters": {
            "type": "object",
            "properties": {
                "pet_id": {"type": "integer"}
            },
            "required": ["pet_id"]
        }
    },
    {
        "name": "get_visit_history",
        "description": "Get recent visit history for a pet",
        "parameters": {
            "type": "object",
            "properties": {
                "pet_id": {"type": "integer"},
                "limit": {"type": "integer", "default": 5}
            },
            "required": ["pet_id"]
        }
    }
]

# Admin-only tools
ADMIN_PET_TOOLS = [
    {
        "name": "search_pets",
        "description": "Search for pets by name, owner, or species",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "species": {"type": "string"},
                "owner_name": {"type": "string"}
            }
        }
    },
    {
        "name": "add_visit_record",
        "description": "Record a new visit for a pet",
        "parameters": {
            "type": "object",
            "properties": {
                "pet_id": {"type": "integer"},
                "reason": {"type": "string"},
                "diagnosis": {"type": "string"},
                "treatment": {"type": "string"}
            },
            "required": ["pet_id", "reason"]
        }
    },
    {
        "name": "add_vaccination",
        "description": "Record a vaccination for a pet",
        "parameters": {
            "type": "object",
            "properties": {
                "pet_id": {"type": "integer"},
                "vaccine_name": {"type": "string"},
                "next_due_date": {"type": "string", "format": "date"}
            },
            "required": ["pet_id", "vaccine_name"]
        }
    }
]
```

## Example AI Conversations

### Owner Checking Pet Info
```
User: What vaccinations does Luna need?
AI: Let me check Luna's vaccination records...

Luna (Golden Retriever, 3 years old) has the following vaccination status:

✅ Rabies - Current (given March 15, 2025, next due March 2026)
✅ DHPP - Current (given March 15, 2025, next due March 2026)
⚠️ Bordetella - Due soon (last given June 2024, due December 2025)

Would you like to schedule an appointment for Luna's Bordetella vaccination?
```

### Admin Adding Records
```
Dr. Pablo: Add a visit for Max, the poodle owned by María García
AI: I found Max (Poodle, 5 years) owned by María García.
    What was the reason for the visit?

Dr. Pablo: Annual checkup, everything looks good, weight 8.2kg
AI: I've recorded the visit for Max:
    - Date: Today (December 20, 2025)
    - Reason: Annual checkup
    - Notes: Everything looks good
    - Weight: 8.2 kg (up from 7.8 kg last visit)

    Would you like to add any vaccinations or prescriptions?
```

## Definition of Done

- [ ] Pet CRUD operations working for owners
- [ ] Medical records viewable by owners
- [ ] Staff can add/edit all medical records
- [ ] Clinical notes hidden from owners
- [ ] Vaccination due dates calculated correctly
- [ ] Document upload working
- [ ] AI can retrieve and display pet info
- [ ] Weight tracking chart implemented
- [ ] Audit logging for medical record changes
- [ ] Tests written and passing (>95% coverage)

## Dependencies

- S-001: Foundation + AI Core
- S-002: AI Chat Interface
- User authentication system

## Notes

- Medical records are sensitive data - ensure HIPAA-like protections
- Consider OCR for uploaded lab results in future epoch
- Weight chart could use Chart.js or similar

## Development Process

**Before implementing this story**, review and follow the **23-Step TDD Cycle** in:
- `CLAUDE.md` - Global development workflow
- `planning/TASK_BREAKDOWN.md` - Specific tasks for this story

Tests must be written before implementation. >95% coverage required.
