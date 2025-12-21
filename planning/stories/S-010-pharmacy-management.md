# S-010: Pharmacy Management

**Story Type:** User Story
**Priority:** High
**Epoch:** 3 (with E-Commerce)
**Status:** PENDING
**Module:** django-simple-store (pharmacy extension)

## User Story

**As a** pet owner
**I want to** order prescription medications and request refills online
**So that** I can conveniently manage my pet's medication needs

**As a** veterinarian
**I want to** manage prescriptions and track controlled substances
**So that** I maintain compliance and provide safe medication management

**As a** pharmacy staff member
**I want to** process prescription orders and manage inventory
**So that** I can efficiently fulfill medication requests

## Acceptance Criteria

### Prescription Management
- [ ] Create prescriptions linked to pet and visit
- [ ] Prescription includes medication, dosage, frequency, duration
- [ ] Prescription has refill count and expiration date
- [ ] Track prescription status (active, expired, cancelled)
- [ ] Prescription requires vet authorization
- [ ] Link prescriptions to appointments/visits

### Refill Requests
- [ ] Pet owners can request refills via AI chat
- [ ] System checks refills remaining and expiration
- [ ] Automatic denial if no refills or expired
- [ ] Notify vet for authorization if needed
- [ ] Refill history tracked per prescription
- [ ] Remind owners when refills are due

### Controlled Substances
- [ ] Flag controlled medications (Schedule II-V)
- [ ] Require additional verification for controlled substances
- [ ] DEA-compliant logging and reporting
- [ ] Cannot refill controlled substances online (pickup only)
- [ ] Track dispensing by staff member
- [ ] Audit trail for all controlled substance transactions

### Medication Database
- [ ] Comprehensive drug database
- [ ] Drug interactions checking
- [ ] Species-specific dosing guidelines
- [ ] Contraindications and warnings
- [ ] Generic/brand name mapping
- [ ] Manufacturer and NDC tracking

### Pharmacy Inventory
- [ ] Track medication stock levels
- [ ] Lot number and expiration tracking
- [ ] Automatic reorder alerts
- [ ] Link inventory to prescriptions filled
- [ ] Wastage and adjustment logging
- [ ] Supplier management

### Order Fulfillment
- [ ] Queue for pending prescription orders
- [ ] Pharmacist verification step
- [ ] Label printing with instructions
- [ ] Pickup vs delivery options
- [ ] Notification when ready for pickup
- [ ] Payment integration with store checkout

## Technical Requirements

### Models

```python
class Medication(models.Model):
    """Drug/medication reference database"""
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True)
    brand_names = models.JSONField(default=list)
    ndc = models.CharField(max_length=20, blank=True)  # National Drug Code

    # Classification
    drug_class = models.CharField(max_length=100)
    schedule = models.CharField(max_length=10, blank=True)  # II, III, IV, V or blank
    is_controlled = models.BooleanField(default=False)
    requires_prescription = models.BooleanField(default=True)

    # Dosing
    species = models.JSONField(default=list)  # ["dog", "cat", "bird", ...]
    dosage_forms = models.JSONField(default=list)  # tablet, liquid, injection
    strengths = models.JSONField(default=list)  # ["10mg", "25mg", "50mg"]
    default_dosing = models.JSONField(default=dict)  # Per species guidelines

    # Safety
    contraindications = models.TextField(blank=True)
    side_effects = models.TextField(blank=True)
    drug_interactions = models.JSONField(default=list)  # List of interacting drug IDs
    warnings = models.TextField(blank=True)

    # Metadata
    manufacturer = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']


class Prescription(models.Model):
    """Prescription issued to a pet"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),  # All refills used
    ]

    # References
    pet = models.ForeignKey('vet_clinic.Pet', on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    prescribing_vet = models.ForeignKey(
        'practice.StaffProfile', on_delete=models.SET_NULL, null=True
    )
    visit = models.ForeignKey(
        'appointments.Appointment', on_delete=models.SET_NULL, null=True, blank=True
    )

    # Medication details
    medication = models.ForeignKey(Medication, on_delete=models.PROTECT)
    strength = models.CharField(max_length=50)
    dosage_form = models.CharField(max_length=50)  # tablet, capsule, liquid
    quantity = models.IntegerField()

    # Instructions
    dosage = models.CharField(max_length=100)  # "1 tablet"
    frequency = models.CharField(max_length=100)  # "twice daily"
    duration = models.CharField(max_length=100)  # "14 days"
    instructions = models.TextField(blank=True)  # "Give with food"

    # Refills
    refills_authorized = models.IntegerField(default=0)
    refills_remaining = models.IntegerField(default=0)

    # Validity
    prescribed_date = models.DateField()
    expiration_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    # For controlled substances
    dea_number = models.CharField(max_length=20, blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-prescribed_date']


class PrescriptionFill(models.Model):
    """Record of each time a prescription is filled"""
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE)

    # Fill details
    fill_number = models.IntegerField()  # 0 = original, 1+ = refills
    quantity_dispensed = models.IntegerField()

    # Inventory tracking
    lot_number = models.CharField(max_length=50, blank=True)
    expiration_date = models.DateField(null=True)

    # Staff
    dispensed_by = models.ForeignKey(
        'practice.StaffProfile', on_delete=models.SET_NULL, null=True
    )
    verified_by = models.ForeignKey(
        'practice.StaffProfile', on_delete=models.SET_NULL, null=True,
        related_name='verified_fills'
    )

    # Order reference
    order = models.ForeignKey(
        'store.Order', on_delete=models.SET_NULL, null=True, blank=True
    )

    # Status
    status = models.CharField(max_length=20, default='pending')
    # pending, processing, ready, picked_up, delivered, cancelled

    # Pickup/delivery
    fulfillment_method = models.CharField(max_length=20)  # pickup, delivery
    ready_at = models.DateTimeField(null=True)
    completed_at = models.DateTimeField(null=True)

    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-requested_at']


class RefillRequest(models.Model):
    """Pet owner request for prescription refill"""
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE)
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE)

    # Request details
    quantity_requested = models.IntegerField(null=True)  # null = standard quantity
    notes = models.TextField(blank=True)

    # Processing
    status = models.CharField(max_length=20, default='pending')
    # pending, approved, denied, filled

    # Authorization (if needed)
    requires_authorization = models.BooleanField(default=False)
    authorized_by = models.ForeignKey(
        'practice.StaffProfile', on_delete=models.SET_NULL, null=True, blank=True
    )
    authorized_at = models.DateTimeField(null=True)
    denial_reason = models.TextField(blank=True)

    # Result
    fill = models.ForeignKey(
        PrescriptionFill, on_delete=models.SET_NULL, null=True, blank=True
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ControlledSubstanceLog(models.Model):
    """DEA-compliant log for controlled substances"""
    medication = models.ForeignKey(Medication, on_delete=models.PROTECT)

    # Transaction
    transaction_type = models.CharField(max_length=20)
    # received, dispensed, wasted, returned, adjusted
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)  # tablets, ml, etc.

    # Running balance
    balance_before = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)

    # References
    prescription_fill = models.ForeignKey(
        PrescriptionFill, on_delete=models.SET_NULL, null=True, blank=True
    )
    lot_number = models.CharField(max_length=50, blank=True)

    # Staff
    performed_by = models.ForeignKey(
        'practice.StaffProfile', on_delete=models.PROTECT
    )
    witnessed_by = models.ForeignKey(
        'practice.StaffProfile', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='witnessed_logs'
    )

    # Notes
    notes = models.TextField(blank=True)

    # Immutable timestamp
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        # This table should be append-only for compliance


class DrugInteraction(models.Model):
    """Drug-drug interaction warnings"""
    medication_1 = models.ForeignKey(
        Medication, on_delete=models.CASCADE, related_name='interactions_as_primary'
    )
    medication_2 = models.ForeignKey(
        Medication, on_delete=models.CASCADE, related_name='interactions_as_secondary'
    )

    severity = models.CharField(max_length=20)  # major, moderate, minor
    description = models.TextField()
    clinical_effects = models.TextField(blank=True)
    management = models.TextField(blank=True)

    class Meta:
        unique_together = ['medication_1', 'medication_2']
```

### AI Tools

```python
PHARMACY_TOOLS = [
    {
        "name": "get_pet_prescriptions",
        "description": "Get active prescriptions for a pet",
        "parameters": {
            "type": "object",
            "properties": {
                "pet_id": {"type": "integer"},
                "include_expired": {"type": "boolean", "default": False}
            },
            "required": ["pet_id"]
        }
    },
    {
        "name": "request_refill",
        "description": "Request a prescription refill",
        "parameters": {
            "type": "object",
            "properties": {
                "prescription_id": {"type": "integer"},
                "quantity": {"type": "integer"},
                "notes": {"type": "string"}
            },
            "required": ["prescription_id"]
        }
    },
    {
        "name": "check_refill_eligibility",
        "description": "Check if a prescription can be refilled",
        "parameters": {
            "type": "object",
            "properties": {
                "prescription_id": {"type": "integer"}
            },
            "required": ["prescription_id"]
        }
    },
    {
        "name": "get_medication_info",
        "description": "Get information about a medication",
        "parameters": {
            "type": "object",
            "properties": {
                "medication_name": {"type": "string"},
                "species": {"type": "string"}
            },
            "required": ["medication_name"]
        }
    },
    {
        "name": "check_drug_interactions",
        "description": "Check for drug interactions with pet's current medications",
        "parameters": {
            "type": "object",
            "properties": {
                "pet_id": {"type": "integer"},
                "new_medication_id": {"type": "integer"}
            },
            "required": ["pet_id", "new_medication_id"]
        }
    },
    {
        "name": "get_refill_status",
        "description": "Check status of a refill request",
        "parameters": {
            "type": "object",
            "properties": {
                "refill_request_id": {"type": "integer"}
            },
            "required": ["refill_request_id"]
        }
    },
    {
        "name": "create_prescription",
        "description": "Create a new prescription (vet only)",
        "parameters": {
            "type": "object",
            "properties": {
                "pet_id": {"type": "integer"},
                "medication_id": {"type": "integer"},
                "strength": {"type": "string"},
                "quantity": {"type": "integer"},
                "dosage": {"type": "string"},
                "frequency": {"type": "string"},
                "duration": {"type": "string"},
                "refills": {"type": "integer"},
                "instructions": {"type": "string"}
            },
            "required": ["pet_id", "medication_id", "quantity", "dosage", "frequency"]
        }
    },
    {
        "name": "get_pharmacy_queue",
        "description": "Get pending prescription orders (staff only)",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["pending", "processing", "ready"]}
            }
        }
    }
]
```

## Example AI Conversations

### Refill Request (Customer)
```
Owner: Luna needs more of her thyroid medication

AI: I can help with that! Let me check Luna's prescriptions.

    Luna has one active prescription:
    - Methimazole 5mg tablets
    - Prescribed: Nov 15, 2025
    - Refills remaining: 2 of 3
    - Expires: May 15, 2026

    Would you like me to request a refill?

Owner: Yes please

AI: Refill requested for Luna's Methimazole 5mg.

    Order Details:
    - Quantity: 60 tablets (30-day supply)
    - Pickup: Pet-Friendly Pharmacy
    - Estimated ready: Today by 4:00 PM

    We'll send you a notification when it's ready.
    The cost will be $285 MXN.

    Would you like to pay now or when you pick up?
```

### Drug Interaction Warning (Vet)
```
Dr. Pablo: Prescribe tramadol for Max

AI: Before I create this prescription, I need to alert you
    to a potential drug interaction:

    ⚠️ MODERATE INTERACTION

    Max is currently taking:
    - Fluoxetine (Prozac) 20mg daily

    Tramadol + Fluoxetine can increase risk of
    serotonin syndrome.

    Clinical Effects:
    - Agitation, tremors, hyperthermia
    - In severe cases: seizures

    Management Options:
    1. Use alternative pain medication (gabapentin)
    2. Proceed with close monitoring
    3. Reduce fluoxetine dose temporarily

    How would you like to proceed?
```

### Controlled Substance (Staff)
```
Staff: Dispense ketamine for surgery prep

AI: This is a Schedule III controlled substance.
    I need to log this transaction.

    Current Inventory:
    - Ketamine 100mg/ml, 10ml vials
    - Balance: 5 vials (50ml total)

    Please confirm:
    - Quantity to dispense: ___
    - Patient/Purpose: ___
    - Witness present: ___

Staff: 2ml for Max's dental surgery, witnessed by Dr. Pablo

AI: Controlled substance logged:

    Transaction: Dispensed 2ml Ketamine
    Patient: Max (dental surgery)
    Dispensed by: [Staff name]
    Witnessed by: Dr. Pablo
    Balance: 48ml remaining

    DEA log updated. Receipt printed.
```

## Compliance Requirements

### DEA Compliance (Controlled Substances)
- Maintain accurate inventory records
- Log all transactions with witness for Schedule II
- Secure storage requirements
- Biennial inventory required
- Report discrepancies immediately
- Staff must have valid credentials

### Mexico Regulations (COFEPRIS)
- Prescription requirements for controlled substances
- Record retention requirements (5 years)
- Reporting requirements for psychotropics
- Proper labeling requirements

## Definition of Done

- [ ] Medication database with 500+ common vet drugs
- [ ] Prescription model with full lifecycle
- [ ] Refill request workflow
- [ ] Drug interaction checking
- [ ] Controlled substance logging (DEA-compliant)
- [ ] Pharmacy queue for staff
- [ ] Integration with e-commerce checkout
- [ ] Notification when ready for pickup
- [ ] AI tools for customer and staff
- [ ] Prescription label printing
- [ ] Tests written and passing (>95% coverage)

## Dependencies

- S-003: Pet Profiles (pet reference)
- S-004: Appointments (visit reference)
- S-005: E-Commerce (order integration)
- S-008: Practice Management (staff profiles)

## Notes

- Consider importing drug database from FDA/veterinary sources
- May need separate controlled substance storage in DB
- Label printing requires thermal printer integration
- COFEPRIS regulations may differ from DEA - research needed
