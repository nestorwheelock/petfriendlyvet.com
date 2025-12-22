# T-035: Travel Certificates

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement international travel health certificate system
**Related Story**: S-022
**Epoch**: 2
**Estimate**: 4 hours

### Constraints
**Allowed File Paths**: apps/travel/
**Forbidden Paths**: apps/store/

### Deliverables
- [ ] TravelDestination model (requirements database)
- [ ] TravelPlan model
- [ ] HealthCertificate model
- [ ] Requirements checker
- [ ] PDF certificate generation
- [ ] AI travel assistant tools

### Implementation Details

#### Models
```python
class TravelDestination(models.Model):
    """Country/region with travel requirements."""

    country_code = models.CharField(max_length=2, unique=True)  # ISO 3166-1
    country_name = models.CharField(max_length=100)
    country_name_es = models.CharField(max_length=100)

    # Requirements
    requirements = models.JSONField(default=dict)
    # {
    #   "rabies_required": true,
    #   "rabies_min_days_before": 30,
    #   "rabies_max_days_before": 365,
    #   "microchip_required": true,
    #   "health_cert_validity_days": 10,
    #   "quarantine_days": 0,
    #   "import_permit_required": false,
    #   "additional_vaccines": ["distemper"],
    #   "parasite_treatment_required": true,
    #   "parasite_treatment_hours_before": 120,
    #   "blood_test_required": false,
    # }

    # Species-specific requirements
    dog_requirements = models.JSONField(default=dict)
    cat_requirements = models.JSONField(default=dict)
    bird_requirements = models.JSONField(default=dict)

    # Documentation
    notes = models.TextField(blank=True)
    notes_es = models.TextField(blank=True)
    official_link = models.URLField(blank=True)

    # Status
    last_verified = models.DateField(null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['country_name']


class TravelPlan(models.Model):
    """Pet's travel plan."""

    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('in_progress', 'In Progress'),
        ('ready', 'Ready to Travel'),
        ('completed', 'Travel Completed'),
        ('cancelled', 'Cancelled'),
    ]

    pet = models.ForeignKey(
        'vet_clinic.Pet',
        on_delete=models.CASCADE,
        related_name='travel_plans'
    )
    destination = models.ForeignKey(
        TravelDestination,
        on_delete=models.PROTECT
    )

    # Travel details
    departure_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    airline = models.CharField(max_length=100, blank=True)
    flight_number = models.CharField(max_length=20, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')

    # Requirements checklist
    requirements_met = models.JSONField(default=dict)
    # {"rabies": true, "microchip": true, "parasite_treatment": false}

    # Notes
    notes = models.TextField(blank=True)
    special_instructions = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-departure_date']


class HealthCertificate(models.Model):
    """Official health certificate for travel."""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_review', 'Pending Review'),
        ('approved', 'Approved'),
        ('issued', 'Issued'),
        ('expired', 'Expired'),
        ('revoked', 'Revoked'),
    ]

    travel_plan = models.ForeignKey(
        TravelPlan,
        on_delete=models.CASCADE,
        related_name='certificates'
    )

    # Certificate details
    certificate_number = models.CharField(max_length=50, unique=True)
    issue_date = models.DateField()
    expiry_date = models.DateField()

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Content (stored for audit)
    certificate_data = models.JSONField(default=dict)

    # Files
    pdf = models.FileField(upload_to='certificates/', null=True, blank=True)
    qr_code = models.ImageField(upload_to='certificates/qr/', null=True, blank=True)

    # Verification
    verification_url = models.URLField(blank=True)
    verification_code = models.CharField(max_length=20, blank=True)

    # Approval
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='approved_certificates'
    )
    approved_at = models.DateTimeField(null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-issue_date']
```

#### Requirements Checker
```python
class TravelRequirementsChecker:
    """Check if pet meets travel requirements."""

    def check_requirements(
        self,
        pet: Pet,
        destination: TravelDestination,
        travel_date: date
    ) -> dict:
        """Check all requirements and return status."""

        results = {
            "eligible": True,
            "requirements": {},
            "blocking_issues": [],
            "warnings": [],
            "recommendations": []
        }

        reqs = destination.requirements
        species_reqs = getattr(destination, f"{pet.species}_requirements", {})
        all_reqs = {**reqs, **species_reqs}

        # Check microchip
        if all_reqs.get('microchip_required'):
            has_chip = bool(pet.microchip_id)
            results["requirements"]["microchip"] = has_chip
            if not has_chip:
                results["blocking_issues"].append(
                    "Se requiere microchip para viajar a este destino"
                )
                results["eligible"] = False

        # Check rabies vaccination
        if all_reqs.get('rabies_required'):
            rabies = self._check_rabies(pet, travel_date, all_reqs)
            results["requirements"]["rabies"] = rabies["valid"]
            if not rabies["valid"]:
                results["blocking_issues"].append(rabies["message"])
                results["eligible"] = False

        # Check parasite treatment
        if all_reqs.get('parasite_treatment_required'):
            hours_before = all_reqs.get('parasite_treatment_hours_before', 120)
            results["requirements"]["parasite_treatment"] = False
            results["recommendations"].append(
                f"Programar tratamiento antiparasitario {hours_before} horas antes del vuelo"
            )

        return results

    def _check_rabies(
        self,
        pet: Pet,
        travel_date: date,
        reqs: dict
    ) -> dict:
        """Check rabies vaccination status."""

        rabies_vacc = pet.vaccinations.filter(
            vaccine_type='rabies'
        ).order_by('-administered_date').first()

        if not rabies_vacc:
            return {
                "valid": False,
                "message": "No tiene vacuna de rabia registrada"
            }

        # Check timing
        min_days = reqs.get('rabies_min_days_before', 30)
        max_days = reqs.get('rabies_max_days_before', 365)

        days_before = (travel_date - rabies_vacc.administered_date).days

        if days_before < min_days:
            return {
                "valid": False,
                "message": f"La vacuna de rabia debe ser al menos {min_days} días antes del viaje"
            }

        if days_before > max_days:
            return {
                "valid": False,
                "message": f"La vacuna de rabia debe ser menos de {max_days} días antes del viaje"
            }

        return {"valid": True, "message": "OK"}
```

#### PDF Generation
```python
class CertificateGenerator:
    """Generate PDF health certificates."""

    def generate(self, certificate: HealthCertificate) -> bytes:
        """Generate PDF certificate."""
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from io import BytesIO

        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)

        # Header
        p.setFont("Helvetica-Bold", 16)
        p.drawString(200, 750, "CERTIFICADO DE SALUD ANIMAL")

        # Pet info
        pet = certificate.travel_plan.pet
        p.setFont("Helvetica", 12)
        p.drawString(50, 700, f"Nombre: {pet.name}")
        p.drawString(50, 680, f"Especie: {pet.get_species_display()}")
        p.drawString(50, 660, f"Raza: {pet.breed or 'Mestizo'}")
        p.drawString(50, 640, f"Microchip: {pet.microchip_id or 'N/A'}")

        # Destination
        dest = certificate.travel_plan.destination
        p.drawString(50, 600, f"Destino: {dest.country_name}")
        p.drawString(50, 580, f"Fecha de viaje: {certificate.travel_plan.departure_date}")

        # Certificate details
        p.drawString(50, 540, f"No. Certificado: {certificate.certificate_number}")
        p.drawString(50, 520, f"Válido hasta: {certificate.expiry_date}")

        # QR Code
        qr_path = self._generate_qr(certificate)
        p.drawImage(qr_path, 450, 600, 100, 100)

        # Signature line
        p.drawString(50, 150, "____________________________")
        p.drawString(50, 135, "Dr. Pablo Rojo Mendoza")
        p.drawString(50, 120, "MVZ Cédula: XXXXXX")

        p.save()
        buffer.seek(0)
        return buffer.getvalue()
```

### AI Tools
```python
@tool(
    name="check_travel_requirements",
    description="Check what's needed for pet travel to a specific country",
    permission="public",
    module="travel"
)
def check_travel_requirements(
    destination: str,
    pet_id: int = None,
    travel_date: str = None
) -> dict:
    """Check travel requirements for destination."""

    destination_obj = TravelDestination.objects.filter(
        Q(country_name__icontains=destination) |
        Q(country_name_es__icontains=destination) |
        Q(country_code__iexact=destination)
    ).first()

    if not destination_obj:
        return {
            "success": False,
            "error": f"No tenemos información sobre requisitos para {destination}"
        }

    base_info = {
        "country": destination_obj.country_name_es,
        "requirements": destination_obj.requirements,
        "notes": destination_obj.notes_es,
        "official_link": destination_obj.official_link
    }

    if pet_id and travel_date:
        pet = Pet.objects.get(id=pet_id)
        date = datetime.strptime(travel_date, "%Y-%m-%d").date()
        checker = TravelRequirementsChecker()
        check_result = checker.check_requirements(pet, destination_obj, date)
        base_info["pet_status"] = check_result

    return {"success": True, **base_info}
```

### Test Cases
- [ ] Destination requirements load
- [ ] Requirements checker works
- [ ] Rabies timing validated
- [ ] PDF generates correctly
- [ ] QR code verification works
- [ ] AI tools return correct info
- [ ] Travel plan workflow works

### Definition of Done
- [ ] Requirements database seeded
- [ ] Checker accurate
- [ ] PDF generation working
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-024: Pet Profile Models
- T-010: Tool Calling Framework
