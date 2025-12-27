"""Practice models for staff, clinic management, and veterinary procedures.

Provides:
- StaffProfile: Staff profiles with roles and permissions
- Shift: Staff work shifts
- TimeEntry: Time tracking
- ClinicSettings: Clinic configuration
- ClinicalNote: Clinical notes (SOAP format)
- Task: Staff task management
- ProcedureCategory: Categories for veterinary procedures
- VetProcedure: Veterinary services/procedures
"""
from decimal import Decimal

from django.db import models
from django.conf import settings

from apps.core.storage import clinic_logo_path


class StaffProfile(models.Model):
    """Staff profile for clinic employees."""

    ROLE_CHOICES = [
        ('veterinarian', 'Veterinarian'),
        ('vet_tech', 'Veterinary Technician'),
        ('pharmacy_tech', 'Pharmacy Technician'),
        ('receptionist', 'Receptionist'),
        ('manager', 'Manager'),
        ('admin', 'Administrator'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='staff_profile'
    )
    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff_profiles',
        help_text='Link to HR Employee record for unified tracking'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    title = models.CharField(max_length=100, blank=True)

    # Permissions
    can_prescribe = models.BooleanField(default=False)
    can_dispense = models.BooleanField(default=False)
    can_handle_controlled = models.BooleanField(default=False)

    # DEA credentials (for controlled substances)
    dea_number = models.CharField(max_length=20, blank=True)
    dea_expiration = models.DateField(null=True, blank=True)

    # Contact
    phone = models.CharField(max_length=20, blank=True)
    emergency_phone = models.CharField(max_length=20, blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    hire_date = models.DateField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user__first_name', 'user__last_name']

    def __str__(self):
        name = self.user.get_full_name() or self.user.username
        return f"{name} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        # Auto-set permissions based on role
        if self.role == 'veterinarian':
            self.can_prescribe = True
            self.can_dispense = True
            self.can_handle_controlled = True
        elif self.role == 'pharmacy_tech':
            self.can_dispense = True
        super().save(*args, **kwargs)


class Shift(models.Model):
    """Staff work shift."""

    staff = models.ForeignKey(
        StaffProfile,
        on_delete=models.CASCADE,
        related_name='shifts'
    )

    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    is_confirmed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'start_time']
        unique_together = ['staff', 'date', 'start_time']

    def __str__(self):
        return f"{self.staff.user.get_full_name()} - {self.date}"


class TimeEntry(models.Model):
    """Time tracking for staff."""

    staff = models.ForeignKey(
        StaffProfile,
        on_delete=models.CASCADE,
        related_name='time_entries'
    )
    shift = models.ForeignKey(
        Shift,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    clock_in = models.DateTimeField()
    clock_out = models.DateTimeField(null=True, blank=True)

    break_minutes = models.IntegerField(default=0)
    notes = models.TextField(blank=True)

    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-clock_in']

    def __str__(self):
        return f"{self.staff.user.get_full_name()} - {self.clock_in.date()}"

    @property
    def hours_worked(self):
        if self.clock_out:
            delta = self.clock_out - self.clock_in
            hours = (delta.total_seconds() / 3600) - (self.break_minutes / 60)
            return round(hours, 2)
        return 0


class ClinicSettings(models.Model):
    """Clinic configuration settings."""

    name = models.CharField(max_length=200)
    legal_name = models.CharField(max_length=200, blank=True)
    tax_id = models.CharField(max_length=50, blank=True)

    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    website = models.URLField(blank=True)

    # Hours
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    days_open = models.JSONField(default=list)

    # Emergency
    emergency_phone = models.CharField(max_length=20, blank=True)
    emergency_available = models.BooleanField(default=False)

    # Social
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    google_maps_url = models.URLField(blank=True)

    # Branding
    logo = models.ImageField(upload_to=clinic_logo_path, blank=True, null=True)
    primary_color = models.CharField(max_length=7, default='#2563eb')

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Clinic Settings'
        verbose_name_plural = 'Clinic Settings'

    def __str__(self):
        return self.name


class ClinicalNote(models.Model):
    """Clinical notes for patient records."""

    NOTE_TYPES = [
        ('soap', 'SOAP Note'),
        ('progress', 'Progress Note'),
        ('procedure', 'Procedure Note'),
        ('lab', 'Lab Results'),
        ('phone', 'Phone Consultation'),
        ('internal', 'Internal Note'),
    ]

    pet = models.ForeignKey(
        'pets.Pet',
        on_delete=models.CASCADE,
        related_name='practice_notes'
    )
    appointment = models.ForeignKey(
        'appointments.Appointment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    note_type = models.CharField(max_length=20, choices=NOTE_TYPES)

    # SOAP structure
    subjective = models.TextField(blank=True)
    objective = models.TextField(blank=True)
    assessment = models.TextField(blank=True)
    plan = models.TextField(blank=True)

    # General content (for non-SOAP notes)
    content = models.TextField(blank=True)

    # Metadata
    is_confidential = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    locked_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.pet.name} - {self.get_note_type_display()} ({self.created_at.date()})"


class Task(models.Model):
    """Staff task management."""

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    assigned_to = models.ForeignKey(
        StaffProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    due_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Related entities
    pet = models.ForeignKey(
        'pets.Pet',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    appointment = models.ForeignKey(
        'appointments.Appointment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority', 'due_date', '-created_at']

    def __str__(self):
        return self.title


class ProcedureCategory(models.Model):
    """Categories for veterinary procedures.

    Groups procedures for organization and reporting.
    Examples: Consultation, Surgery, Vaccination, Dental, Lab Work
    """

    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique identifier (e.g., 'surgery', 'dental')"
    )
    name = models.CharField(max_length=100)
    name_es = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)

    icon = models.CharField(max_length=50, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = 'Procedure Category'
        verbose_name_plural = 'Procedure Categories'

    def __str__(self):
        return self.name


class VetProcedure(models.Model):
    """Veterinary procedure/service definition.

    This is the service-module-specific model for veterinary clinics.
    Other business types would have their own service models:
    - AutoShop: RepairService
    - Restaurant: MenuItem
    - WaterDelivery: DeliveryService
    """

    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Internal procedure code (e.g., 'CONSULT-GEN')"
    )
    name = models.CharField(max_length=200)
    name_es = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)

    category = models.ForeignKey(
        ProcedureCategory,
        on_delete=models.PROTECT,
        related_name='procedures'
    )

    # Qualified providers who can perform this procedure
    qualified_providers = models.ManyToManyField(
        StaffProfile,
        blank=True,
        related_name='qualified_procedures',
        help_text="Staff members qualified to perform this procedure"
    )

    # Pricing
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Standard price for this procedure"
    )
    price_varies = models.BooleanField(
        default=False,
        help_text="Price depends on factors (size, complexity, etc.)"
    )

    # Time
    duration_minutes = models.PositiveIntegerField(
        default=30,
        help_text="Expected duration in minutes"
    )

    # SAT codes for Mexican tax compliance
    sat_product_code = models.ForeignKey(
        'billing.SATProductCode',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="SAT Clave Producto for CFDI invoicing"
    )
    sat_unit_code = models.ForeignKey(
        'billing.SATUnitCode',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="SAT Clave Unidad for CFDI invoicing"
    )

    # Requirements
    requires_appointment = models.BooleanField(default=True)
    requires_hospitalization = models.BooleanField(default=False)
    requires_anesthesia = models.BooleanField(default=False)
    requires_vet_license = models.BooleanField(
        default=True,
        help_text="Must be performed by licensed veterinarian"
    )

    # Status
    is_active = models.BooleanField(default=True)
    is_visible_online = models.BooleanField(
        default=True,
        help_text="Show in online booking system"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'Veterinary Procedure'
        verbose_name_plural = 'Veterinary Procedures'

    def __str__(self):
        return self.name

    @property
    def total_consumable_cost(self):
        """Calculate total cost of consumable items."""
        total = Decimal('0.00')
        for consumable in self.consumables.all():
            if consumable.inventory_item and consumable.inventory_item.cost_price:
                total += consumable.inventory_item.cost_price * consumable.quantity
        return total


class ProcedureConsumable(models.Model):
    """Inventory items consumed when performing a procedure.

    Tracks what items are used (vaccines, syringes, needles, towels, etc.)
    and the quantity consumed per procedure.
    """

    procedure = models.ForeignKey(
        VetProcedure,
        on_delete=models.CASCADE,
        related_name='consumables'
    )
    inventory_item = models.ForeignKey(
        'inventory.InventoryItem',
        on_delete=models.PROTECT,
        related_name='procedure_uses',
        help_text="Inventory item consumed during this procedure"
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('1.00'),
        help_text="Quantity consumed per procedure"
    )
    is_required = models.BooleanField(
        default=True,
        help_text="If true, procedure cannot be performed without this item in stock"
    )
    notes = models.CharField(
        max_length=200,
        blank=True,
        help_text="Optional notes (e.g., 'Use 3ml syringe for small dogs')"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['procedure', 'inventory_item']
        unique_together = ['procedure', 'inventory_item']
        verbose_name = 'Procedure Consumable'
        verbose_name_plural = 'Procedure Consumables'

    def __str__(self):
        return f"{self.procedure.name}: {self.quantity} x {self.inventory_item.name}"

    @property
    def unit_cost(self):
        """Get the cost of this consumable."""
        if self.inventory_item and self.inventory_item.cost_price:
            return self.inventory_item.cost_price * self.quantity
        return Decimal('0.00')
