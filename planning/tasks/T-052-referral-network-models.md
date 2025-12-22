# T-052: Referral Network Models

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement specialist directory and referral tracking
**Related Story**: S-025
**Epoch**: 4
**Estimate**: 4 hours

### Constraints
**Allowed File Paths**: apps/vet_clinic/
**Forbidden Paths**: None

### Deliverables
- [ ] Specialist model
- [ ] Referral model
- [ ] Visiting schedule model
- [ ] Referral documents
- [ ] Revenue tracking

### Wireframe Reference
See: `planning/wireframes/18-referral-network.txt`

### Implementation Details

#### Models
```python
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Specialty(models.Model):
    """Veterinary specialty."""

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    icon = models.CharField(max_length=50, blank=True)  # Icon class or emoji

    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Specialties'
        ordering = ['name']

    def __str__(self):
        return self.name


class Specialist(models.Model):
    """External specialist or referral partner."""

    PARTNER_TYPES = [
        ('specialist', 'Especialista'),
        ('hospital', 'Hospital'),
        ('lab', 'Laboratorio'),
        ('imaging', 'Imagenología'),
        ('rehab', 'Rehabilitación'),
        ('behaviorist', 'Etólogo'),
        ('grooming', 'Estética'),
        ('boarding', 'Pensión'),
        ('other', 'Otro'),
    ]

    # Basic info
    name = models.CharField(max_length=200)
    partner_type = models.CharField(max_length=20, choices=PARTNER_TYPES)
    specialties = models.ManyToManyField(Specialty, blank=True)

    # Contact
    contact_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20)
    whatsapp = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)

    # Location
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, default='Quintana Roo')
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    distance_km = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)

    # Capabilities
    services = models.TextField(blank=True)
    equipment = models.TextField(blank=True)  # MRI, CT, Ultrasound, etc.

    # Hours
    hours = models.JSONField(default=dict, blank=True)
    # {'monday': '9:00-18:00', 'saturday': '9:00-14:00', ...}
    is_24_hour = models.BooleanField(default=False)
    accepts_emergencies = models.BooleanField(default=False)

    # Visiting specialist
    is_visiting = models.BooleanField(default=False)
    visiting_frequency = models.CharField(max_length=100, blank=True)
    # 'Weekly on Thursdays', 'Monthly', etc.

    # Business terms
    accepts_referrals = models.BooleanField(default=True)
    referral_fee_percent = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    payment_terms = models.CharField(max_length=50, blank=True)

    # Rating and notes
    rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    internal_notes = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_partner_type_display()})"


class VisitingSchedule(models.Model):
    """Schedule for visiting specialists."""

    specialist = models.ForeignKey(
        Specialist, on_delete=models.CASCADE,
        related_name='visiting_schedules'
    )

    # Schedule
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    # Recurring
    is_recurring = models.BooleanField(default=False)
    recurrence_rule = models.CharField(max_length=100, blank=True)
    # 'WEEKLY:TH' (every Thursday)

    # Services offered during visit
    services_offered = models.TextField(blank=True)

    # Equipment they bring
    equipment_provided = models.TextField(blank=True)

    # Booking
    max_appointments = models.IntegerField(default=10)
    appointments_booked = models.IntegerField(default=0)
    booking_open = models.BooleanField(default=True)

    # Revenue arrangement
    revenue_share = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )  # Percentage to Pet-Friendly
    flat_fee = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )  # Or flat fee per visit

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'start_time']


class Referral(models.Model):
    """Referral to or from external specialist."""

    DIRECTION_CHOICES = [
        ('outbound', 'Referido a especialista'),
        ('inbound', 'Referido a nosotros'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('sent', 'Enviado'),
        ('received', 'Recibido'),
        ('in_progress', 'En progreso'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    ]

    # Direction
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)

    # Patient
    pet = models.ForeignKey('Pet', on_delete=models.CASCADE, related_name='referrals')
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    # Partner
    specialist = models.ForeignKey(
        Specialist, on_delete=models.SET_NULL,
        null=True, related_name='referrals'
    )

    # If inbound, referring vet info
    referring_vet_name = models.CharField(max_length=200, blank=True)
    referring_vet_phone = models.CharField(max_length=20, blank=True)
    referring_vet_email = models.EmailField(blank=True)

    # Referral details
    reason = models.TextField()
    urgency = models.CharField(max_length=20, choices=[
        ('routine', 'Rutinario'),
        ('urgent', 'Urgente'),
        ('emergency', 'Emergencia'),
    ], default='routine')

    diagnosis = models.TextField(blank=True)
    requested_services = models.TextField(blank=True)
    relevant_history = models.TextField(blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Timing
    referred_date = models.DateField()
    appointment_date = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)

    # Results
    specialist_diagnosis = models.TextField(blank=True)
    treatment_performed = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_notes = models.TextField(blank=True)

    # Linked records
    medical_record = models.ForeignKey(
        'MedicalRecord', on_delete=models.SET_NULL,
        null=True, blank=True
    )
    emergency_case = models.ForeignKey(
        'EmergencyCase', on_delete=models.SET_NULL,
        null=True, blank=True
    )

    # Communication
    sent_via = models.CharField(max_length=20, blank=True)
    # 'email', 'whatsapp', 'fax', 'phone'

    # Internal
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, related_name='+'
    )
    internal_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-referred_date']

    def __str__(self):
        return f"Referral {self.pet.name} → {self.specialist.name if self.specialist else 'Unknown'}"


class ReferralDocument(models.Model):
    """Documents attached to referral."""

    referral = models.ForeignKey(
        Referral, on_delete=models.CASCADE,
        related_name='documents'
    )

    DOCUMENT_TYPES = [
        ('referral_letter', 'Carta de referencia'),
        ('medical_history', 'Historial médico'),
        ('lab_results', 'Resultados laboratorio'),
        ('imaging', 'Imágenes'),
        ('specialist_report', 'Reporte especialista'),
        ('other', 'Otro'),
    ]

    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='referrals/')
    description = models.TextField(blank=True)

    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)


class VisitingAppointment(models.Model):
    """Appointment with visiting specialist."""

    schedule = models.ForeignKey(
        VisitingSchedule, on_delete=models.CASCADE,
        related_name='appointments'
    )

    pet = models.ForeignKey('Pet', on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    # Booking
    start_time = models.TimeField()
    end_time = models.TimeField()
    service = models.CharField(max_length=200)

    # Status
    status = models.CharField(max_length=20, choices=[
        ('booked', 'Reservada'),
        ('confirmed', 'Confirmada'),
        ('arrived', 'Llegó'),
        ('in_progress', 'En consulta'),
        ('completed', 'Completada'),
        ('no_show', 'No asistió'),
        ('cancelled', 'Cancelada'),
    ], default='booked')

    # Results
    notes = models.TextField(blank=True)
    findings = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)

    # Billing
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    invoice = models.ForeignKey(
        'billing.Invoice', on_delete=models.SET_NULL,
        null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['schedule__date', 'start_time']
```

### Test Cases
- [ ] Specialist CRUD works
- [ ] Specialty assignment works
- [ ] Referral creation works
- [ ] Visiting schedule works
- [ ] Document upload works
- [ ] Status transitions valid
- [ ] Revenue tracking accurate

### Definition of Done
- [ ] All models migrated
- [ ] Admin interface complete
- [ ] Sample data seeded
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-024: Pet Models
- T-025: Medical Records Models
- T-050: Emergency Models
