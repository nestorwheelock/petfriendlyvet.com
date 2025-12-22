# T-039: Pharmacy & Prescription Models

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement pharmacy management with prescriptions
**Related Story**: S-010
**Epoch**: 3
**Estimate**: 4 hours

### Constraints
**Allowed File Paths**: apps/pharmacy/
**Forbidden Paths**: None

### Deliverables
- [ ] Prescription model
- [ ] PrescriptionItem model
- [ ] Controlled substance tracking
- [ ] Refill management
- [ ] AI prescription tools

### Implementation Details

#### Models
```python
class Prescription(models.Model):
    """Veterinary prescription."""

    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('active', 'Activa'),
        ('partially_filled', 'Parcialmente surtida'),
        ('filled', 'Surtida'),
        ('expired', 'Expirada'),
        ('cancelled', 'Cancelada'),
    ]

    # Who
    pet = models.ForeignKey('vet_clinic.Pet', on_delete=models.CASCADE, related_name='prescriptions')
    prescribed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='prescriptions')

    # When
    prescribed_date = models.DateField()
    valid_until = models.DateField()

    # Medical record link
    medical_record = models.ForeignKey(
        'vet_clinic.MedicalRecord',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Notes
    diagnosis = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)

    # Refills
    total_refills_allowed = models.IntegerField(default=0)
    refills_remaining = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    activated_at = models.DateTimeField(null=True)

    class Meta:
        ordering = ['-prescribed_date']

    @property
    def is_valid(self):
        return self.status == 'active' and self.valid_until >= timezone.now().date()


class PrescriptionItem(models.Model):
    """Individual medication in prescription."""

    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('store.Product', on_delete=models.SET_NULL, null=True)

    # Medication details
    medication_name = models.CharField(max_length=500)
    strength = models.CharField(max_length=100, blank=True)  # "500mg"
    form = models.CharField(max_length=50, blank=True)  # "tablet", "liquid"

    # Dosage
    dose = models.CharField(max_length=100)  # "1 tablet"
    frequency = models.CharField(max_length=100)  # "twice daily"
    duration = models.CharField(max_length=100, blank=True)  # "7 days"
    instructions = models.TextField(blank=True)  # "Give with food"

    # Quantity
    quantity_prescribed = models.IntegerField()
    quantity_dispensed = models.IntegerField(default=0)
    quantity_remaining = models.IntegerField(default=0)

    # Refills for this item
    refills_allowed = models.IntegerField(default=0)
    refills_used = models.IntegerField(default=0)

    # Controlled substance
    is_controlled = models.BooleanField(default=False)
    dea_schedule = models.CharField(max_length=10, blank=True)  # "II", "III", etc.


class PrescriptionFill(models.Model):
    """Record of prescription being filled."""

    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='fills')
    item = models.ForeignKey(PrescriptionItem, on_delete=models.CASCADE, null=True)

    filled_date = models.DateTimeField(auto_now_add=True)
    filled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    quantity = models.IntegerField()
    lot_number = models.CharField(max_length=100, blank=True)
    expiry_date = models.DateField(null=True)

    # Linked to order if purchased
    order_item = models.ForeignKey('store.OrderItem', on_delete=models.SET_NULL, null=True)

    notes = models.TextField(blank=True)


class ControlledSubstanceLog(models.Model):
    """DEA-style log for controlled substances."""

    LOG_TYPES = [
        ('received', 'Received'),
        ('dispensed', 'Dispensed'),
        ('returned', 'Returned'),
        ('destroyed', 'Destroyed'),
        ('adjustment', 'Adjustment'),
    ]

    product = models.ForeignKey('store.Product', on_delete=models.CASCADE)
    log_type = models.CharField(max_length=20, choices=LOG_TYPES)

    date = models.DateTimeField(auto_now_add=True)
    quantity = models.IntegerField()
    balance_after = models.IntegerField()

    # References
    prescription = models.ForeignKey(Prescription, on_delete=models.SET_NULL, null=True, blank=True)
    prescription_fill = models.ForeignKey(PrescriptionFill, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey('store.Order', on_delete=models.SET_NULL, null=True, blank=True)

    # Details
    lot_number = models.CharField(max_length=100, blank=True)
    supplier = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)

    # Audit
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    witness = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    class Meta:
        ordering = ['-date']
```

#### AI Tools
```python
@tool(
    name="check_prescription",
    description="Check if a product requires prescription and if one exists",
    permission="customer",
    module="pharmacy"
)
def check_prescription(product_id: int) -> dict:
    """Check prescription status for a product."""

    product = Product.objects.get(id=product_id)

    if not product.requires_prescription:
        return {
            "requires_prescription": False,
            "message": "Este producto no requiere receta"
        }

    # Check for active prescriptions for user's pets
    prescriptions = Prescription.objects.filter(
        pet__owner=context.user,
        status='active',
        valid_until__gte=timezone.now().date(),
        items__product=product
    )

    if prescriptions.exists():
        return {
            "requires_prescription": True,
            "has_valid_prescription": True,
            "prescriptions": [
                {"id": p.id, "pet": p.pet.name, "valid_until": str(p.valid_until)}
                for p in prescriptions
            ]
        }

    return {
        "requires_prescription": True,
        "has_valid_prescription": False,
        "message": "Necesitas una receta válida para este medicamento"
    }


@tool(
    name="request_refill",
    description="Request a prescription refill",
    permission="customer",
    module="pharmacy"
)
def request_refill(prescription_id: int) -> dict:
    """Request prescription refill."""

    prescription = Prescription.objects.get(
        id=prescription_id,
        pet__owner=context.user
    )

    if not prescription.is_valid:
        return {"success": False, "error": "La receta ya no es válida"}

    if prescription.refills_remaining <= 0:
        return {"success": False, "error": "No quedan refills disponibles"}

    # Create refill request (notification to pharmacy)
    send_refill_request.delay(prescription.id, context.user.id)

    return {
        "success": True,
        "message": "Solicitud de refill enviada. Te contactaremos pronto.",
        "refills_remaining": prescription.refills_remaining - 1
    }
```

### Test Cases
- [ ] Prescriptions CRUD
- [ ] Items link to products
- [ ] Validity checking works
- [ ] Refill tracking accurate
- [ ] Controlled substance logging
- [ ] AI tools work correctly

### Definition of Done
- [ ] All models migrated
- [ ] Prescription workflow working
- [ ] DEA logging in place
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-036: Product & Category Models
- T-024: Pet Profile Models
