# T-034: External Services & Partner Directory

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md and [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement partner directory for outsourced services (grooming, boarding)
**Related Story**: S-021
**Epoch**: 2
**Estimate**: 3 hours

### Constraints
**Allowed File Paths**: apps/partners/
**Forbidden Paths**: apps/store/

### Deliverables
- [ ] ExternalPartner model
- [ ] ServiceReferral model
- [ ] Partner directory views
- [ ] AI tools for recommendations
- [ ] Referral tracking

### Implementation Details

#### Models
```python
class ExternalPartner(models.Model):
    """External service provider (groomer, boarding, etc.)."""

    SERVICE_TYPES = [
        ('grooming', 'Estética/Grooming'),
        ('boarding', 'Hospedaje/Boarding'),
        ('training', 'Entrenamiento'),
        ('daycare', 'Guardería'),
        ('transport', 'Transporte'),
        ('specialist', 'Especialista'),
        ('emergency', 'Emergencias 24h'),
        ('pharmacy', 'Farmacia'),
        ('other', 'Otro'),
    ]

    # Basic info
    name = models.CharField(max_length=200)
    service_type = models.CharField(max_length=50, choices=SERVICE_TYPES)
    description = models.TextField(blank=True)
    description_es = models.TextField(blank=True)
    description_en = models.TextField(blank=True)

    # Contact
    phone = models.CharField(max_length=20)
    whatsapp = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)

    # Location
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, default='Puerto Morelos')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    distance_km = models.DecimalField(max_digits=5, decimal_places=1, null=True)

    # Hours
    hours = models.JSONField(default=dict)
    # {"mon": {"open": "09:00", "close": "18:00"}, ...}

    # Rating
    our_rating = models.IntegerField(null=True)  # 1-5, our assessment
    client_rating_avg = models.DecimalField(max_digits=3, decimal_places=2, null=True)
    client_rating_count = models.IntegerField(default=0)

    # Business relationship
    has_agreement = models.BooleanField(default=False)
    commission_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    notes = models.TextField(blank=True)

    # Status
    is_recommended = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_recommended', '-our_rating', 'name']


class PartnerService(models.Model):
    """Specific services offered by a partner."""

    partner = models.ForeignKey(
        ExternalPartner,
        on_delete=models.CASCADE,
        related_name='services'
    )
    name = models.CharField(max_length=200)
    name_es = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price_range = models.CharField(max_length=100, blank=True)  # "$200-$500"
    duration = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['name']


class ServiceReferral(models.Model):
    """Track referrals to external partners."""

    STATUS_CHOICES = [
        ('referred', 'Referred'),
        ('contacted', 'Contacted Partner'),
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    # Who
    pet = models.ForeignKey(
        'vet_clinic.Pet',
        on_delete=models.CASCADE,
        related_name='referrals'
    )
    partner = models.ForeignKey(
        ExternalPartner,
        on_delete=models.CASCADE,
        related_name='referrals'
    )

    # What
    service_type = models.CharField(max_length=50)
    notes = models.TextField(blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='referred')
    referred_at = models.DateTimeField(auto_now_add=True)
    scheduled_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True)

    # Feedback
    client_feedback = models.TextField(blank=True)
    client_rating = models.IntegerField(null=True)  # 1-5
    would_recommend = models.BooleanField(null=True)

    # Medication handoff (for boarding)
    medications_provided = models.JSONField(default=list)
    special_instructions = models.TextField(blank=True)

    # Staff
    referred_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )

    class Meta:
        ordering = ['-referred_at']
```

#### AI Tools
```python
@tool(
    name="find_groomer",
    description="Find grooming services near the clinic",
    permission="public",
    module="partners"
)
def find_groomer(
    pet_type: str = None,
    service: str = None
) -> dict:
    """Find recommended groomers."""

    partners = ExternalPartner.objects.filter(
        service_type='grooming',
        is_active=True
    ).order_by('-is_recommended', '-our_rating')

    return {
        "success": True,
        "message": "No ofrecemos estética en la clínica, pero te recomendamos:",
        "partners": [
            {
                "name": p.name,
                "phone": p.phone,
                "whatsapp": p.whatsapp,
                "rating": p.our_rating,
                "recommended": p.is_recommended,
                "address": p.address,
            }
            for p in partners[:3]
        ]
    }


@tool(
    name="find_boarding",
    description="Find pet boarding/hotel services",
    permission="public",
    module="partners"
)
def find_boarding(
    dates: dict = None,
    pet_type: str = None
) -> dict:
    """Find boarding facilities."""

    partners = ExternalPartner.objects.filter(
        service_type='boarding',
        is_active=True
    ).order_by('-is_recommended', '-our_rating')

    return {
        "success": True,
        "message": "No ofrecemos hospedaje, pero recomendamos:",
        "partners": [
            {
                "name": p.name,
                "phone": p.phone,
                "description": p.description_es or p.description,
                "rating": p.our_rating,
            }
            for p in partners[:3]
        ]
    }


@tool(
    name="create_boarding_referral",
    description="Create a referral for boarding with medication handoff info",
    permission="customer",
    module="partners"
)
def create_boarding_referral(
    pet_id: int,
    partner_id: int,
    start_date: str,
    end_date: str,
    special_instructions: str = ""
) -> dict:
    """Create boarding referral with medication info."""

    pet = Pet.objects.get(id=pet_id, owner=context.user)
    partner = ExternalPartner.objects.get(id=partner_id)

    # Get current medications
    medications = pet.current_medications()

    referral = ServiceReferral.objects.create(
        pet=pet,
        partner=partner,
        service_type='boarding',
        scheduled_date=datetime.strptime(start_date, "%Y-%m-%d").date(),
        medications_provided=medications,
        special_instructions=special_instructions,
        referred_by=context.user
    )

    return {
        "success": True,
        "referral_id": referral.id,
        "partner": partner.name,
        "partner_phone": partner.phone,
        "message": f"Hemos creado una referencia para {pet.name} en {partner.name}. " +
                   f"Por favor contáctalos al {partner.phone} para confirmar."
    }
```

### Test Cases
- [ ] Partners CRUD works
- [ ] Referrals created
- [ ] AI tools return partners
- [ ] Medication handoff tracked
- [ ] Client feedback captured
- [ ] Ratings calculated

### Definition of Done
- [ ] Partner directory functional
- [ ] Referral tracking working
- [ ] AI recommendations work
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-024: Pet Profile Models
- T-010: Tool Calling Framework
