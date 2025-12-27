# T-050: Emergency Services Models

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md and [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement emergency case tracking and triage
**Related Story**: S-015
**Epoch**: 4
**Estimate**: 3 hours

### Constraints
**Allowed File Paths**: apps/vet_clinic/
**Forbidden Paths**: None

### Deliverables
- [ ] EmergencyCase model
- [ ] Triage classification
- [ ] Emergency contact routing
- [ ] After-hours handling
- [ ] Emergency protocols

### Wireframe Reference
See: `planning/wireframes/17-emergency-triage.txt`

### Implementation Details

#### Models
```python
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class EmergencyProtocol(models.Model):
    """Emergency response protocols."""

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    # Symptoms/triggers
    keywords = models.JSONField(default=list)
    # ['bleeding', 'unconscious', 'not breathing', ...]

    # Triage level this triggers
    triage_level = models.CharField(max_length=20, choices=[
        ('critical', 'Crítico - Inmediato'),
        ('urgent', 'Urgente - < 1 hora'),
        ('semi_urgent', 'Semi-urgente - < 4 horas'),
        ('non_urgent', 'No urgente - Puede esperar'),
    ])

    # Instructions
    first_aid_instructions = models.TextField(blank=True)
    what_to_bring = models.TextField(blank=True)
    what_not_to_do = models.TextField(blank=True)

    # Estimated treatment
    typical_treatment = models.TextField(blank=True)
    estimated_cost_range = models.CharField(max_length=100, blank=True)

    # Species specific
    applies_to_species = models.JSONField(default=list)
    # ['dog', 'cat', 'bird', ...]

    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']


class EmergencyCase(models.Model):
    """Emergency case record."""

    TRIAGE_LEVELS = [
        ('critical', 'Crítico'),
        ('urgent', 'Urgente'),
        ('semi_urgent', 'Semi-urgente'),
        ('non_urgent', 'No urgente'),
        ('unknown', 'Pendiente triage'),
    ]

    STATUS_CHOICES = [
        ('reported', 'Reportado'),
        ('triaged', 'En triage'),
        ('en_route', 'En camino'),
        ('arrived', 'Llegó'),
        ('in_treatment', 'En tratamiento'),
        ('stabilized', 'Estabilizado'),
        ('hospitalized', 'Hospitalizado'),
        ('discharged', 'Dado de alta'),
        ('referred', 'Referido'),
        ('deceased', 'Fallecido'),
        ('cancelled', 'Cancelado'),
    ]

    # Case identification
    case_number = models.CharField(max_length=50, unique=True)

    # Patient
    pet = models.ForeignKey(
        'Pet', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='emergencies'
    )
    owner = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True
    )

    # If pet not in system
    pet_name = models.CharField(max_length=200, blank=True)
    pet_species = models.CharField(max_length=50, blank=True)
    pet_breed = models.CharField(max_length=100, blank=True)
    pet_age = models.CharField(max_length=50, blank=True)
    pet_weight = models.CharField(max_length=50, blank=True)

    # Contact if owner not in system
    contact_name = models.CharField(max_length=200, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)

    # Emergency details
    chief_complaint = models.TextField()
    symptoms = models.TextField(blank=True)
    symptom_duration = models.CharField(max_length=100, blank=True)

    # Matched protocol
    protocol = models.ForeignKey(
        EmergencyProtocol, on_delete=models.SET_NULL,
        null=True, blank=True
    )

    # Triage
    triage_level = models.CharField(
        max_length=20, choices=TRIAGE_LEVELS, default='unknown'
    )
    triage_notes = models.TextField(blank=True)
    triaged_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+'
    )
    triaged_at = models.DateTimeField(null=True)

    # Status
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='reported'
    )

    # Location
    is_at_clinic = models.BooleanField(default=False)
    eta_minutes = models.IntegerField(null=True, blank=True)
    location_notes = models.TextField(blank=True)

    # Treatment
    treating_vet = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+'
    )
    treatment_notes = models.TextField(blank=True)
    outcome = models.TextField(blank=True)

    # Referral
    referred_to = models.ForeignKey(
        'Specialist', on_delete=models.SET_NULL,
        null=True, blank=True
    )
    referral_notes = models.TextField(blank=True)

    # Timing
    reported_at = models.DateTimeField(auto_now_add=True)
    arrived_at = models.DateTimeField(null=True)
    treatment_started_at = models.DateTimeField(null=True)
    resolved_at = models.DateTimeField(null=True)

    # Source
    SOURCE_CHOICES = [
        ('phone', 'Llamada'),
        ('whatsapp', 'WhatsApp'),
        ('ai_chat', 'Chat AI'),
        ('walk_in', 'Llegó directo'),
        ('referral', 'Referido'),
    ]
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    conversation = models.ForeignKey(
        'communications.Conversation',
        on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ['-reported_at']
        verbose_name_plural = 'Emergency Cases'

    def save(self, *args, **kwargs):
        if not self.case_number:
            self.case_number = self._generate_case_number()
        super().save(*args, **kwargs)

    def _generate_case_number(self):
        from django.utils import timezone
        import random
        prefix = timezone.now().strftime('%Y%m%d')
        suffix = ''.join(random.choices('0123456789', k=4))
        return f'EM-{prefix}-{suffix}'


class EmergencyNote(models.Model):
    """Notes/updates on emergency case."""

    case = models.ForeignKey(
        EmergencyCase, on_delete=models.CASCADE,
        related_name='notes'
    )

    note_type = models.CharField(max_length=20, choices=[
        ('triage', 'Triage'),
        ('treatment', 'Tratamiento'),
        ('update', 'Actualización'),
        ('vitals', 'Signos vitales'),
        ('lab', 'Laboratorio'),
        ('outcome', 'Resultado'),
    ])

    content = models.TextField()
    vitals = models.JSONField(null=True, blank=True)
    # {'temperature': 38.5, 'heart_rate': 120, 'respiratory_rate': 30, ...}

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']


class EmergencyContact(models.Model):
    """Emergency contact for after-hours."""

    name = models.CharField(max_length=200)
    role = models.CharField(max_length=100)  # 'Veterinarian', 'Technician'
    phone = models.CharField(max_length=20)
    whatsapp = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    is_on_call = models.BooleanField(default=False)
    on_call_start = models.TimeField(null=True, blank=True)
    on_call_end = models.TimeField(null=True, blank=True)
    on_call_days = models.JSONField(default=list)
    # ['monday', 'tuesday', ...]

    receives_critical = models.BooleanField(default=True)
    receives_urgent = models.BooleanField(default=True)

    priority = models.IntegerField(default=0)  # Lower = first to contact

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['priority', 'name']


class AfterHoursMessage(models.Model):
    """After-hours emergency messages."""

    MESSAGE_TYPES = [
        ('voicemail', 'Correo de voz'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
        ('form', 'Formulario web'),
    ]

    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES)
    from_phone = models.CharField(max_length=20, blank=True)
    from_email = models.EmailField(blank=True)
    content = models.TextField()

    # Pet info if provided
    pet_name = models.CharField(max_length=200, blank=True)
    pet_species = models.CharField(max_length=50, blank=True)
    symptoms = models.TextField(blank=True)

    # Urgency assessment
    ai_triage = models.CharField(max_length=20, blank=True)
    ai_triage_notes = models.TextField(blank=True)

    # Handling
    forwarded_to = models.ForeignKey(
        EmergencyContact, on_delete=models.SET_NULL,
        null=True, blank=True
    )
    forwarded_at = models.DateTimeField(null=True)
    response_notes = models.TextField(blank=True)

    # Linked case if created
    emergency_case = models.ForeignKey(
        EmergencyCase, on_delete=models.SET_NULL,
        null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    handled_at = models.DateTimeField(null=True)

    class Meta:
        ordering = ['-created_at']
```

### Test Cases
- [ ] Protocol matching works
- [ ] Case creation works
- [ ] Triage assignment works
- [ ] Notes tracked correctly
- [ ] Status transitions valid
- [ ] Emergency contacts retrieved
- [ ] After-hours routing works

### Definition of Done
- [ ] All models migrated
- [ ] Admin interface for protocols
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-024: Pet Models
- T-044: Communication Models
