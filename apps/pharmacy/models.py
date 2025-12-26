"""Pharmacy models for prescription management."""
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import date


class Medication(models.Model):
    """Drug/medication reference database."""

    name = models.CharField(max_length=200)
    name_es = models.CharField(max_length=200, blank=True)
    generic_name = models.CharField(max_length=200, blank=True)
    brand_names = models.JSONField(default=list, blank=True)
    ndc = models.CharField(max_length=20, blank=True)  # National Drug Code

    # Classification
    drug_class = models.CharField(max_length=100)
    schedule = models.CharField(max_length=10, blank=True)  # II, III, IV, V or blank
    is_controlled = models.BooleanField(default=False)
    requires_prescription = models.BooleanField(default=True)

    # Dosing
    species = models.JSONField(default=list, blank=True)  # ["dog", "cat", "bird", ...]
    dosage_forms = models.JSONField(default=list, blank=True)  # tablet, liquid, injection
    strengths = models.JSONField(default=list, blank=True)  # ["10mg", "25mg", "50mg"]
    default_dosing = models.JSONField(default=dict, blank=True)  # Per species guidelines

    # Safety
    contraindications = models.TextField(blank=True)
    side_effects = models.TextField(blank=True)
    warnings = models.TextField(blank=True)

    # Metadata
    manufacturer = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        if self.schedule:
            return f"{self.name} (Schedule {self.schedule})"
        return self.name


class Prescription(models.Model):
    """Prescription issued to a pet."""

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),  # All refills used
    ]

    # References
    pet = models.ForeignKey(
        'pets.Pet',
        on_delete=models.CASCADE,
        related_name='prescriptions'
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pharmacy_prescriptions'
    )
    prescribing_vet = models.ForeignKey(
        'practice.StaffProfile',
        on_delete=models.SET_NULL,
        null=True,
        related_name='prescribed_medications'
    )
    visit = models.ForeignKey(
        'appointments.Appointment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prescriptions'
    )

    # Medication details
    medication = models.ForeignKey(
        Medication,
        on_delete=models.PROTECT,
        related_name='prescriptions'
    )
    strength = models.CharField(max_length=50)
    dosage_form = models.CharField(max_length=50)  # tablet, capsule, liquid
    quantity = models.IntegerField()

    # Instructions
    dosage = models.CharField(max_length=100)  # "1 tablet"
    frequency = models.CharField(max_length=100)  # "twice daily"
    duration = models.CharField(max_length=100, blank=True)  # "14 days"
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

    def __str__(self):
        return f"{self.medication.name} for {self.pet.name}"

    @property
    def is_active(self):
        """Check if prescription is active status."""
        return self.status == 'active'

    @property
    def is_expired(self):
        """Check if prescription has expired."""
        return self.expiration_date < date.today()

    @property
    def has_refills(self):
        """Check if refills are available."""
        return self.refills_remaining > 0

    @property
    def can_refill(self):
        """Check if prescription can be refilled."""
        if self.is_expired:
            return False
        if not self.has_refills:
            return False
        if self.status != 'active':
            return False
        return True

    def use_refill(self):
        """Use one refill."""
        if self.refills_remaining > 0:
            self.refills_remaining -= 1
            if self.refills_remaining == 0:
                self.status = 'completed'
            self.save()
            return True
        return False


class PrescriptionFill(models.Model):
    """Record of each time a prescription is filled."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('ready', 'Ready for Pickup'),
        ('picked_up', 'Picked Up'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name='fills'
    )

    # Fill details
    fill_number = models.IntegerField()  # 0 = original, 1+ = refills
    quantity_dispensed = models.IntegerField()

    # Inventory tracking
    lot_number = models.CharField(max_length=50, blank=True)
    expiration_date = models.DateField(null=True, blank=True)

    # Staff
    dispensed_by = models.ForeignKey(
        'practice.StaffProfile',
        on_delete=models.SET_NULL,
        null=True,
        related_name='dispensed_fills'
    )
    verified_by = models.ForeignKey(
        'practice.StaffProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_fills'
    )

    # Order reference
    order = models.ForeignKey(
        'store.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prescription_fills'
    )

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Pickup/delivery
    fulfillment_method = models.CharField(max_length=20)  # pickup, delivery
    ready_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-requested_at']

    def __str__(self):
        return f"Fill #{self.fill_number} - {self.prescription}"


class RefillRequest(models.Model):
    """Pet owner request for prescription refill."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
        ('filled', 'Filled'),
        ('cancelled', 'Cancelled'),
    ]

    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name='refill_requests'
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='refill_requests'
    )

    # Request details
    quantity_requested = models.IntegerField(null=True, blank=True)  # null = standard quantity
    notes = models.TextField(blank=True)

    # Processing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Authorization (if needed)
    requires_authorization = models.BooleanField(default=False)
    authorized_by = models.ForeignKey(
        'practice.StaffProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='authorized_refills'
    )
    authorized_at = models.DateTimeField(null=True, blank=True)
    denial_reason = models.TextField(blank=True)

    # Cancellation
    cancellation_reason = models.TextField(blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    # Result
    fill = models.ForeignKey(
        PrescriptionFill,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='refill_request'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Refill request for {self.prescription}"


class ControlledSubstanceLog(models.Model):
    """DEA-compliant log for controlled substances."""

    TRANSACTION_TYPES = [
        ('received', 'Received'),
        ('dispensed', 'Dispensed'),
        ('wasted', 'Wasted'),
        ('returned', 'Returned'),
        ('adjusted', 'Adjusted'),
    ]

    medication = models.ForeignKey(
        Medication,
        on_delete=models.PROTECT,
        related_name='controlled_logs'
    )

    # Transaction
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)  # tablets, ml, etc.

    # Running balance
    balance_before = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)

    # References
    prescription_fill = models.ForeignKey(
        PrescriptionFill,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='controlled_logs'
    )
    lot_number = models.CharField(max_length=50, blank=True)

    # Staff
    performed_by = models.ForeignKey(
        'practice.StaffProfile',
        on_delete=models.PROTECT,
        related_name='controlled_transactions'
    )
    witnessed_by = models.ForeignKey(
        'practice.StaffProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='witnessed_logs'
    )

    # Notes
    notes = models.TextField(blank=True)

    # Immutable timestamp
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        # This table should be append-only for compliance

    def __str__(self):
        return f"{self.get_transaction_type_display()} {self.quantity} {self.medication.name}"


class DrugInteraction(models.Model):
    """Drug-drug interaction warnings."""

    SEVERITY_CHOICES = [
        ('major', 'Major'),
        ('moderate', 'Moderate'),
        ('minor', 'Minor'),
    ]

    medication_1 = models.ForeignKey(
        Medication,
        on_delete=models.CASCADE,
        related_name='interactions_as_primary'
    )
    medication_2 = models.ForeignKey(
        Medication,
        on_delete=models.CASCADE,
        related_name='interactions_as_secondary'
    )

    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    description = models.TextField()
    clinical_effects = models.TextField(blank=True)
    management = models.TextField(blank=True)

    class Meta:
        unique_together = ['medication_1', 'medication_2']

    def __str__(self):
        return f"{self.medication_1.name} + {self.medication_2.name} ({self.severity})"
