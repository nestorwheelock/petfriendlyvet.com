# Pharmacy Module

The `apps.pharmacy` module provides comprehensive prescription management for veterinary medications, including controlled substance tracking for DEA compliance.

## Table of Contents

- [Overview](#overview)
- [Models](#models)
  - [Medication](#medication)
  - [Prescription](#prescription)
  - [PrescriptionFill](#prescriptionfill)
  - [RefillRequest](#refillrequest)
  - [ControlledSubstanceLog](#controlledsubstancelog)
  - [DrugInteraction](#druginteraction)
- [Customer Views](#customer-views)
- [Prescription Lifecycle](#prescription-lifecycle)
- [Refill Workflow](#refill-workflow)
- [Controlled Substances](#controlled-substances)
- [Drug Interactions](#drug-interactions)
- [Integration Points](#integration-points)
- [Querying Examples](#querying-examples)
- [Compliance Notes](#compliance-notes)
- [Testing](#testing)

## Overview

The pharmacy module handles:

- **Medication database** - Drug reference with species-specific dosing, schedules, and safety info
- **Prescription management** - Issuing, tracking, and expiring prescriptions
- **Refill workflow** - Customer requests, staff approval, dispensing
- **Controlled substance logging** - DEA-compliant tracking with witness signatures
- **Drug interaction warnings** - Safety alerts for medication combinations

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Medication    │────▶│   Prescription  │────▶│ PrescriptionFill│
│   (drug ref)    │     │   (Rx issued)   │     │   (dispensed)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │                        │
                               ▼                        ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │  RefillRequest  │     │ ControlledLog   │
                        │ (customer req)  │     │ (DEA tracking)  │
                        └─────────────────┘     └─────────────────┘
```

## Models

### Medication

Drug/medication reference database with species-specific information.

Location: `apps/pharmacy/models.py`

```python
class Medication(models.Model):
    # Identification
    name = models.CharField(max_length=200)
    name_es = models.CharField(max_length=200)  # Spanish translation
    generic_name = models.CharField(max_length=200)
    brand_names = models.JSONField(default=list)  # ["Tapazole", "Felimazole"]
    ndc = models.CharField(max_length=20)  # National Drug Code

    # Classification
    drug_class = models.CharField(max_length=100)  # "Antithyroid", "NSAID"
    schedule = models.CharField(max_length=10)  # "II", "III", "IV", "V" or blank
    is_controlled = models.BooleanField(default=False)
    requires_prescription = models.BooleanField(default=True)

    # Dosing
    species = models.JSONField(default=list)  # ["dog", "cat", "bird"]
    dosage_forms = models.JSONField(default=list)  # ["tablet", "liquid", "injection"]
    strengths = models.JSONField(default=list)  # ["10mg", "25mg", "50mg"]
    default_dosing = models.JSONField(default=dict)  # Per-species guidelines

    # Safety
    contraindications = models.TextField()
    side_effects = models.TextField()
    warnings = models.TextField()
```

**Key Fields:**

| Field | Purpose |
|-------|---------|
| `schedule` | DEA schedule (II-V) for controlled substances |
| `is_controlled` | Quick check for controlled substance handling |
| `species` | Which animals this medication is approved for |
| `default_dosing` | Species-specific dosing guidelines as JSON |

**Example Usage:**

```python
from apps.pharmacy.models import Medication

# Create a controlled medication
tramadol = Medication.objects.create(
    name='Tramadol',
    generic_name='Tramadol HCl',
    drug_class='Opioid Analgesic',
    schedule='IV',
    is_controlled=True,
    species=['dog', 'cat'],
    dosage_forms=['tablet'],
    strengths=['50mg', '100mg'],
    default_dosing={
        'dog': '2-5 mg/kg every 8-12 hours',
        'cat': '1-2 mg/kg every 12 hours'
    }
)

# Find all controlled medications
controlled = Medication.objects.filter(is_controlled=True)

# Find medications for cats
cat_meds = Medication.objects.filter(species__contains='cat')
```

### Prescription

Prescription issued to a pet by a veterinarian.

```python
class Prescription(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),  # All refills used
    ]

    # References
    pet = models.ForeignKey('pets.Pet', on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    prescribing_vet = models.ForeignKey('practice.StaffProfile', ...)
    visit = models.ForeignKey('appointments.Appointment', ...)  # Optional

    # Medication details
    medication = models.ForeignKey(Medication, on_delete=models.PROTECT)
    strength = models.CharField(max_length=50)  # "50mg"
    dosage_form = models.CharField(max_length=50)  # "tablet"
    quantity = models.IntegerField()  # 30

    # Instructions
    dosage = models.CharField(max_length=100)  # "1 tablet"
    frequency = models.CharField(max_length=100)  # "twice daily"
    duration = models.CharField(max_length=100)  # "14 days"
    instructions = models.TextField()  # "Give with food"

    # Refills
    refills_authorized = models.IntegerField(default=0)
    refills_remaining = models.IntegerField(default=0)

    # Validity
    prescribed_date = models.DateField()
    expiration_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    # For controlled substances
    dea_number = models.CharField(max_length=20)
```

**Properties:**

| Property | Returns | Description |
|----------|---------|-------------|
| `is_active` | bool | Status is 'active' |
| `is_expired` | bool | Expiration date has passed |
| `has_refills` | bool | Refills remaining > 0 |
| `can_refill` | bool | Active, not expired, has refills |

**Methods:**

```python
# Use one refill
prescription.use_refill()  # Returns True if successful, decrements refills_remaining
```

### PrescriptionFill

Record of each time a prescription is filled/dispensed.

```python
class PrescriptionFill(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('ready', 'Ready for Pickup'),
        ('picked_up', 'Picked Up'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    prescription = models.ForeignKey(Prescription, related_name='fills')

    # Fill details
    fill_number = models.IntegerField()  # 0 = original, 1+ = refills
    quantity_dispensed = models.IntegerField()

    # Inventory tracking
    lot_number = models.CharField(max_length=50)
    expiration_date = models.DateField()

    # Staff
    dispensed_by = models.ForeignKey('practice.StaffProfile', ...)
    verified_by = models.ForeignKey('practice.StaffProfile', ...)  # Double-check

    # Order reference (if through store)
    order = models.ForeignKey('store.Order', ...)

    # Fulfillment
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    fulfillment_method = models.CharField(max_length=20)  # 'pickup' or 'delivery'
    ready_at = models.DateTimeField()
    completed_at = models.DateTimeField()
```

### RefillRequest

Customer-initiated request for prescription refill.

```python
class RefillRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
        ('filled', 'Filled'),
    ]

    prescription = models.ForeignKey(Prescription, related_name='refill_requests')
    requested_by = models.ForeignKey(User, ...)

    # Request details
    quantity_requested = models.IntegerField()  # null = standard quantity
    notes = models.TextField()  # Customer notes

    # Processing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    # Authorization (for controlled or special cases)
    requires_authorization = models.BooleanField(default=False)
    authorized_by = models.ForeignKey('practice.StaffProfile', ...)
    authorized_at = models.DateTimeField()
    denial_reason = models.TextField()

    # Result
    fill = models.ForeignKey(PrescriptionFill, ...)  # Created when filled
```

### ControlledSubstanceLog

DEA-compliant perpetual inventory log for Schedule II-V medications.

```python
class ControlledSubstanceLog(models.Model):
    TRANSACTION_TYPES = [
        ('received', 'Received'),      # Inventory received from supplier
        ('dispensed', 'Dispensed'),    # Given to patient
        ('wasted', 'Wasted'),          # Disposed/destroyed
        ('returned', 'Returned'),      # Returned to supplier
        ('adjusted', 'Adjusted'),      # Inventory correction
    ]

    medication = models.ForeignKey(Medication, on_delete=models.PROTECT)

    # Transaction
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)  # "tablets", "ml"

    # Running balance (perpetual inventory)
    balance_before = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)

    # References
    prescription_fill = models.ForeignKey(PrescriptionFill, ...)
    lot_number = models.CharField(max_length=50)

    # Staff (required for DEA compliance)
    performed_by = models.ForeignKey('practice.StaffProfile', on_delete=models.PROTECT)
    witnessed_by = models.ForeignKey('practice.StaffProfile', ...)  # Required for waste

    notes = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)  # Immutable
```

**Important:** This table is designed to be **append-only**. Records should never be deleted or modified for compliance purposes.

### DrugInteraction

Drug-drug interaction warnings for safety.

```python
class DrugInteraction(models.Model):
    SEVERITY_CHOICES = [
        ('major', 'Major'),       # Avoid combination
        ('moderate', 'Moderate'), # Use with caution
        ('minor', 'Minor'),       # Monitor
    ]

    medication_1 = models.ForeignKey(Medication, related_name='interactions_as_primary')
    medication_2 = models.ForeignKey(Medication, related_name='interactions_as_secondary')

    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    description = models.TextField()  # What happens
    clinical_effects = models.TextField()  # Symptoms
    management = models.TextField()  # How to handle
```

## Customer Views

### URL Patterns

| URL | View | Description |
|-----|------|-------------|
| `/pharmacy/prescriptions/` | `PrescriptionListView` | List user's prescriptions |
| `/pharmacy/prescriptions/<id>/` | `PrescriptionDetailView` | Prescription details + fills |
| `/pharmacy/refills/` | `RefillListView` | List user's refill requests |
| `/pharmacy/refills/<id>/` | `RefillDetailView` | Refill request details |
| `/pharmacy/prescriptions/<id>/refill/` | `RefillRequestCreateView` | Request a refill |

### Templates

| Template | Purpose |
|----------|---------|
| `pharmacy/prescription_list.html` | List of prescriptions with status |
| `pharmacy/prescription_detail.html` | Full prescription info, fill history |
| `pharmacy/refill_list.html` | List of refill requests |
| `pharmacy/refill_detail.html` | Refill request status |
| `pharmacy/refill_request_form.html` | Form to request refill |

## Prescription Lifecycle

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Created   │────▶│   Active    │────▶│  Completed  │
│ (by vet)    │     │             │     │(all refills)│
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Expired   │
                    │(past date)  │
                    └─────────────┘
```

**Status Transitions:**

1. **Created → Active**: Prescription issued by veterinarian
2. **Active → Completed**: All refills used (`refills_remaining = 0`)
3. **Active → Expired**: `expiration_date` passes
4. **Active → Cancelled**: Manually cancelled by staff

## Refill Workflow

```
Customer                    Staff                       System
   │                          │                           │
   │  Request Refill          │                           │
   │─────────────────────────▶│                           │
   │                          │  Check prescription       │
   │                          │────────────────────────▶  │
   │                          │                           │
   │                          │  ◀─ can_refill = True    │
   │                          │                           │
   │                          │  Approve/Deny             │
   │                          │────────────────────────▶  │
   │                          │                           │
   │                          │  Create PrescriptionFill  │
   │                          │────────────────────────▶  │
   │                          │                           │
   │                          │  Dispense medication      │
   │                          │────────────────────────▶  │
   │                          │                           │
   │  ◀───────────────────────│  use_refill()            │
   │  Notification: Ready     │                           │
   │                          │                           │
```

**Refill Validation:**

```python
# In RefillRequestCreateView.form_valid()

# Check if prescription can be refilled
if not prescription.can_refill:
    messages.error(request, 'This prescription cannot be refilled.')
    return redirect(...)

# Block online refills for controlled substances
if prescription.medication.is_controlled:
    messages.error(
        request,
        'Controlled substances cannot be refilled online. Please call the clinic.'
    )
    return redirect(...)
```

## Controlled Substances

### Schedule Classifications

| Schedule | Description | Examples | Online Refill |
|----------|-------------|----------|---------------|
| II | High abuse potential | Fentanyl, Morphine | No |
| III | Moderate abuse potential | Ketamine, Buprenorphine | No |
| IV | Low abuse potential | Tramadol, Phenobarbital | No |
| V | Lowest abuse potential | Some cough preparations | No |
| (blank) | Non-controlled | Antibiotics, etc. | Yes |

### DEA Compliance Logging

Every controlled substance transaction must be logged:

```python
from apps.pharmacy.models import ControlledSubstanceLog, Medication

def dispense_controlled(medication, quantity, fill, staff, witness=None):
    """Log controlled substance dispensing."""
    # Get current balance
    last_log = ControlledSubstanceLog.objects.filter(
        medication=medication
    ).order_by('-timestamp').first()

    balance_before = last_log.balance_after if last_log else Decimal('0')
    balance_after = balance_before - quantity

    ControlledSubstanceLog.objects.create(
        medication=medication,
        transaction_type='dispensed',
        quantity=quantity,
        unit='tablets',
        balance_before=balance_before,
        balance_after=balance_after,
        prescription_fill=fill,
        performed_by=staff,
        witnessed_by=witness,  # Required for waste, recommended for dispense
    )
```

### Witness Requirements

| Transaction | Witness Required |
|-------------|------------------|
| Received | No |
| Dispensed | Recommended |
| Wasted | **Yes** |
| Returned | Recommended |
| Adjusted | **Yes** |

## Drug Interactions

### Checking for Interactions

```python
from apps.pharmacy.models import DrugInteraction

def check_interactions(new_medication, pet):
    """Check for drug interactions with pet's current medications."""
    # Get pet's active prescriptions
    active_meds = Prescription.objects.filter(
        pet=pet,
        status='active'
    ).values_list('medication_id', flat=True)

    # Find interactions
    interactions = DrugInteraction.objects.filter(
        models.Q(medication_1=new_medication, medication_2__in=active_meds) |
        models.Q(medication_2=new_medication, medication_1__in=active_meds)
    ).select_related('medication_1', 'medication_2')

    return interactions

# Usage
interactions = check_interactions(tramadol, pet)
for interaction in interactions:
    if interaction.severity == 'major':
        # Block or require override
        pass
```

### Severity Actions

| Severity | UI Treatment | Workflow |
|----------|--------------|----------|
| Major | Red warning, block | Requires vet override |
| Moderate | Yellow warning | Proceed with acknowledgment |
| Minor | Info message | Log and proceed |

## Integration Points

### With Appointments

```python
# Prescription can be linked to visit
prescription = Prescription.objects.create(
    pet=pet,
    owner=pet.owner,
    prescribing_vet=vet_profile,
    visit=appointment,  # Links to appointment
    medication=medication,
    ...
)
```

### With Store/Orders

```python
# Prescription fill can be linked to store order
fill = PrescriptionFill.objects.create(
    prescription=prescription,
    order=order,  # Store order for payment/delivery
    ...
)
```

### With Inventory

Prescriptions should integrate with `apps.inventory` for:
- Stock level checks before dispensing
- Automatic stock deduction on fill
- Reorder alerts for low medication stock

### With Audit Logging

Pharmacy paths are automatically audited:
- `/pharmacy/prescriptions/*` → `pharmacy.prescription` (high sensitivity)
- All controlled substance actions are logged

## Querying Examples

### Active Prescriptions for a Pet

```python
from apps.pharmacy.models import Prescription

active = Prescription.objects.filter(
    pet=pet,
    status='active',
    expiration_date__gte=date.today()
).select_related('medication')
```

### Prescriptions Expiring Soon

```python
from datetime import date, timedelta

expiring_soon = Prescription.objects.filter(
    status='active',
    expiration_date__lte=date.today() + timedelta(days=30),
    expiration_date__gt=date.today()
)
```

### Controlled Substance Inventory

```python
from django.db.models import Sum

# Current balance for a medication
balance = ControlledSubstanceLog.objects.filter(
    medication=tramadol
).order_by('-timestamp').first()

current_stock = balance.balance_after if balance else 0

# Total dispensed this month
from django.utils import timezone
from datetime import timedelta

month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0)
dispensed = ControlledSubstanceLog.objects.filter(
    medication=tramadol,
    transaction_type='dispensed',
    timestamp__gte=month_start
).aggregate(total=Sum('quantity'))['total'] or 0
```

### Pending Refill Requests

```python
pending = RefillRequest.objects.filter(
    status='pending'
).select_related(
    'prescription__medication',
    'prescription__pet',
    'requested_by'
).order_by('created_at')
```

## Compliance Notes

### DEA Requirements

1. **Perpetual Inventory**: `ControlledSubstanceLog` maintains running balance
2. **Witness Signatures**: Required for waste, recommended for all transactions
3. **Immutable Records**: Logs should never be deleted or modified
4. **DEA Number**: Stored on prescription for controlled substances
5. **Schedule Tracking**: Each medication marked with DEA schedule

### HIPAA Considerations

1. **Access Control**: Views require login, filter by owner
2. **Audit Trail**: All pharmacy access is logged via AuditMiddleware
3. **Data Minimization**: Only show necessary information in lists
4. **Secure Transmission**: HTTPS required for all pharmacy pages

### Mexican Regulations (COFEPRIS)

1. **Recipe Médico**: Prescription documentation requirements
2. **Controlled Substance Schedules**: May differ from DEA schedules
3. **Record Retention**: Keep logs for required period (typically 5 years)

## Testing

### Unit Tests

Location: `tests/test_pharmacy.py` (842 lines)

```bash
# Run pharmacy unit tests
python -m pytest tests/test_pharmacy.py -v
```

Covers:
- Medication CRUD and validation
- Prescription lifecycle and status transitions
- Refill request workflow
- Controlled substance logging
- Drug interaction detection

### Browser Tests

Location: `tests/e2e/browser/test_pharmacy.py` (658 lines)

```bash
# Run pharmacy browser tests
python -m pytest tests/e2e/browser/test_pharmacy.py -v

# Run with visible browser
python -m pytest tests/e2e/browser/test_pharmacy.py -v --headed --slowmo=500
```

Covers:
- Prescription list and detail views
- Refill request form submission
- Controlled substance warnings
- Mobile responsiveness
- Fill history display

### Test Coverage

~1500 lines of tests covering:
- Model validation and business logic
- View access control and permissions
- Form validation and submission
- Edge cases (expired, no refills, controlled)
