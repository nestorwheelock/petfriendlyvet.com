# S-022: Travel Certificates

**Story Type:** User Story
**Priority:** Medium
**Epoch:** 2 (with Pets)
**Status:** PENDING
**Module:** django-vet-clinic

## User Story

**As a** pet owner planning international travel
**I want to** get proper health certificates for my pet
**So that** I can travel without issues at customs/immigration

**As a** veterinarian
**I want to** generate compliant health certificates
**So that** I can help clients travel internationally with their pets

**As a** clinic staff member
**I want to** know the requirements for each destination
**So that** I can ensure pets are properly prepared for travel

## Acceptance Criteria

### Travel Requirements Database
- [ ] Database of requirements by destination country
- [ ] Required vaccinations per destination
- [ ] Timing requirements (e.g., rabies 30 days before)
- [ ] Microchip requirements
- [ ] Parasite treatment requirements
- [ ] Quarantine rules
- [ ] Airline-specific requirements
- [ ] Regular updates when regulations change

### Health Certificate Generation
- [ ] PDF generation with official format
- [ ] Support for USDA-style certificates
- [ ] EU Pet Passport requirements format
- [ ] QR code for verification
- [ ] Multiple languages (Spanish, English)
- [ ] Digital signature capability
- [ ] Expiration tracking (usually 10 days for travel)
- [ ] Clinic letterhead and branding

### Travel Preparation Workflow
- [ ] Client requests certificate for destination
- [ ] System shows requirements checklist
- [ ] Tracks completion of each requirement
- [ ] Vet verifies all requirements met
- [ ] Certificate generated and signed
- [ ] Copy stored in pet's records
- [ ] Delivery (print, email, download)

### Reminders & Alerts
- [ ] Upcoming travel date reminders
- [ ] Certificate expiration warnings
- [ ] Missing requirement alerts
- [ ] Vaccination timing reminders
- [ ] Pre-travel checkup scheduling

### Integration
- [ ] Link to pet medical records
- [ ] Vaccination verification from records
- [ ] Microchip verification
- [ ] Appointment booking for travel exam
- [ ] Invoice for travel certificate services

## Technical Requirements

### Models

```python
class TravelDestination(models.Model):
    """Country/region with travel requirements"""
    name = models.CharField(max_length=200)
    name_es = models.CharField(max_length=200)
    iso_code = models.CharField(max_length=3)  # ISO 3166-1 alpha-3

    # Requirements
    requirements = models.JSONField(default=dict)
    # {
    #     "rabies": {"required": true, "min_days_before": 30, "max_days_before": 365},
    #     "microchip": {"required": true, "iso_standard": "11784/11785"},
    #     "health_certificate": {"validity_days": 10},
    #     "parasite_treatment": {"required": true, "days_before": 5},
    #     "blood_tests": {"rabies_titer": {"required": false}},
    #     "quarantine": {"days": 0, "notes": "No quarantine for compliant pets"},
    # }

    # Species-specific
    species_requirements = models.JSONField(default=dict)
    # {"dog": {...}, "cat": {...}, "bird": {...}}

    # Banned breeds (if applicable)
    banned_breeds = models.JSONField(default=list)

    # Documents needed
    required_documents = models.JSONField(default=list)
    # ["health_certificate", "vaccination_record", "microchip_registration"]

    # Entry points
    entry_requirements = models.JSONField(default=dict)
    # Special requirements for specific ports of entry

    # Source & updates
    official_source_url = models.URLField(blank=True)
    last_verified = models.DateField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    notes = models.TextField(blank=True)
    notes_es = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class AirlineRequirement(models.Model):
    """Airline-specific pet travel requirements"""
    name = models.CharField(max_length=200)
    iata_code = models.CharField(max_length=3)

    # General policy
    allows_cabin = models.BooleanField(default=True)
    allows_cargo = models.BooleanField(default=True)
    max_weight_cabin_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Requirements
    requirements = models.JSONField(default=dict)
    # {
    #     "health_certificate_max_days": 10,
    #     "crate_requirements": "IATA compliant",
    #     "breed_restrictions": ["brachycephalic"],
    #     "temperature_restrictions": true,
    # }

    # Fees
    cabin_fee = models.JSONField(default=dict)
    # {"domestic": 125, "international": 200, "currency": "USD"}

    cargo_fee = models.JSONField(default=dict)

    # Booking
    booking_url = models.URLField(blank=True)
    booking_phone = models.CharField(max_length=50, blank=True)
    advance_notice_hours = models.IntegerField(default=48)

    notes = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    last_verified = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['name']


class TravelPlan(models.Model):
    """Pet travel plan and preparation tracking"""
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('preparing', 'In Preparation'),
        ('ready', 'Ready to Travel'),
        ('completed', 'Travel Completed'),
        ('cancelled', 'Cancelled'),
    ]

    # Who
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='travel_plans')
    pet = models.ForeignKey('vet_clinic.Pet', on_delete=models.CASCADE, related_name='travel_plans')

    # Where
    destination = models.ForeignKey(TravelDestination, on_delete=models.PROTECT)
    destination_address = models.TextField(blank=True)

    # When
    departure_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)

    # How
    airline = models.ForeignKey(AirlineRequirement, on_delete=models.SET_NULL, null=True, blank=True)
    travel_method = models.CharField(max_length=50, default='air')
    # air, land, sea

    cabin_or_cargo = models.CharField(max_length=20, blank=True)
    # cabin, cargo, checked

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')

    # Requirements tracking
    requirements_checklist = models.JSONField(default=dict)
    # {
    #     "rabies_vaccine": {"required": true, "completed": true, "date": "2025-11-15"},
    #     "microchip": {"required": true, "completed": true, "number": "123456789"},
    #     "health_exam": {"required": true, "completed": false, "due_date": "2025-12-18"},
    #     "certificate": {"required": true, "completed": false},
    # }

    # Related records
    health_certificate = models.ForeignKey(
        'HealthCertificate', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='travel_plans'
    )
    appointment = models.ForeignKey(
        'appointments.Appointment', on_delete=models.SET_NULL, null=True, blank=True
    )

    # Notes
    notes = models.TextField(blank=True)
    special_requirements = models.TextField(blank=True)

    # Staff
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='travel_plans_created'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-departure_date']


class HealthCertificate(models.Model):
    """International health certificate for travel"""
    CERTIFICATE_TYPES = [
        ('usda', 'USDA APHIS 7001'),
        ('eu', 'EU Pet Passport Style'),
        ('generic', 'Generic International'),
        ('domestic', 'Domestic Travel'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_review', 'Pending Vet Review'),
        ('signed', 'Signed'),
        ('delivered', 'Delivered to Client'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]

    # Certificate identification
    certificate_number = models.CharField(max_length=50, unique=True)
    certificate_type = models.CharField(max_length=20, choices=CERTIFICATE_TYPES)

    # Subject
    pet = models.ForeignKey('vet_clinic.Pet', on_delete=models.CASCADE, related_name='health_certificates')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='health_certificates')

    # Travel details
    destination = models.ForeignKey(TravelDestination, on_delete=models.PROTECT)
    departure_date = models.DateField()

    # Validity
    issue_date = models.DateField()
    expiry_date = models.DateField()

    # Examination
    examination_date = models.DateField()
    examining_vet = models.ForeignKey(
        'practice.StaffProfile', on_delete=models.PROTECT, related_name='certificates_issued'
    )

    # Health status
    health_status = models.TextField()
    # "The animal described above was examined and found to be healthy and
    # free from evidence of communicable disease..."

    # Verified requirements
    verified_requirements = models.JSONField(default=dict)
    # {
    #     "rabies_vaccine": {"verified": true, "date": "2025-11-15", "lot": "ABC123", "manufacturer": "Nobivac"},
    #     "microchip": {"verified": true, "number": "123456789012345", "location": "left shoulder"},
    #     "parasite_treatment": {"verified": true, "date": "2025-12-15", "product": "NexGard"},
    # }

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Signature
    signed_at = models.DateTimeField(null=True, blank=True)
    digital_signature = models.TextField(blank=True)  # Base64 signature image or digital signature

    # Documents
    pdf_file = models.FileField(upload_to='certificates/', null=True, blank=True)
    qr_code = models.ImageField(upload_to='certificates/qr/', null=True, blank=True)

    # Verification
    verification_code = models.CharField(max_length=20, unique=True)
    # Short code for QR/verification

    # Delivery
    delivered_at = models.DateTimeField(null=True, blank=True)
    delivery_method = models.CharField(max_length=20, blank=True)
    # email, print, pickup

    # Billing
    invoice = models.ForeignKey(
        'billing.Invoice', on_delete=models.SET_NULL, null=True, blank=True
    )

    # Notes
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-issue_date']

    def is_valid(self):
        from django.utils import timezone
        return self.status == 'signed' and self.expiry_date >= timezone.now().date()


class CertificateRequirement(models.Model):
    """Individual requirement verification for a certificate"""
    certificate = models.ForeignKey(
        HealthCertificate, on_delete=models.CASCADE, related_name='requirements'
    )

    REQUIREMENT_TYPES = [
        ('vaccination', 'Vaccination'),
        ('microchip', 'Microchip'),
        ('parasite', 'Parasite Treatment'),
        ('blood_test', 'Blood Test'),
        ('exam', 'Physical Examination'),
        ('other', 'Other'),
    ]

    requirement_type = models.CharField(max_length=20, choices=REQUIREMENT_TYPES)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Verification
    is_verified = models.BooleanField(default=False)
    verified_date = models.DateField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    # Details (varies by type)
    details = models.JSONField(default=dict)
    # Vaccination: {"vaccine": "Rabies", "date": "...", "lot": "...", "manufacturer": "..."}
    # Microchip: {"number": "...", "location": "...", "iso_compliant": true}
    # Blood test: {"test": "Rabies titer", "result": "...", "lab": "..."}

    # Related medical record
    medical_record = models.ForeignKey(
        'vet_clinic.MedicalRecord', on_delete=models.SET_NULL, null=True, blank=True
    )

    notes = models.TextField(blank=True)


class TravelReminder(models.Model):
    """Reminders for travel preparation"""
    travel_plan = models.ForeignKey(TravelPlan, on_delete=models.CASCADE, related_name='reminders')

    REMINDER_TYPES = [
        ('requirement', 'Requirement Due'),
        ('exam', 'Travel Exam'),
        ('certificate', 'Certificate Pickup'),
        ('departure', 'Departure'),
        ('expiry', 'Certificate Expiring'),
    ]

    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()

    due_date = models.DateField()

    # Notification
    sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    channel = models.CharField(max_length=20, blank=True)
    # email, sms, whatsapp

    created_at = models.DateTimeField(auto_now_add=True)
```

### AI Tools

```python
TRAVEL_CERTIFICATE_TOOLS = [
    {
        "name": "check_travel_requirements",
        "description": "Get travel requirements for a destination country",
        "parameters": {
            "type": "object",
            "properties": {
                "destination": {"type": "string"},
                "species": {"type": "string"},
                "pet_id": {"type": "integer"},
                "travel_date": {"type": "string"}
            },
            "required": ["destination", "species"]
        }
    },
    {
        "name": "create_travel_plan",
        "description": "Create a travel preparation plan for a pet",
        "parameters": {
            "type": "object",
            "properties": {
                "pet_id": {"type": "integer"},
                "destination": {"type": "string"},
                "departure_date": {"type": "string"},
                "return_date": {"type": "string"},
                "airline": {"type": "string"}
            },
            "required": ["pet_id", "destination", "departure_date"]
        }
    },
    {
        "name": "get_travel_checklist",
        "description": "Get the current checklist status for a travel plan",
        "parameters": {
            "type": "object",
            "properties": {
                "travel_plan_id": {"type": "integer"}
            },
            "required": ["travel_plan_id"]
        }
    },
    {
        "name": "generate_health_certificate",
        "description": "Generate a health certificate for travel",
        "parameters": {
            "type": "object",
            "properties": {
                "pet_id": {"type": "integer"},
                "destination": {"type": "string"},
                "travel_date": {"type": "string"},
                "certificate_type": {"type": "string"}
            },
            "required": ["pet_id", "destination", "travel_date"]
        }
    },
    {
        "name": "verify_certificate_requirement",
        "description": "Verify a requirement for a health certificate",
        "parameters": {
            "type": "object",
            "properties": {
                "certificate_id": {"type": "integer"},
                "requirement_type": {"type": "string"},
                "details": {"type": "object"}
            },
            "required": ["certificate_id", "requirement_type"]
        }
    },
    {
        "name": "get_certificate_status",
        "description": "Check the status of a health certificate",
        "parameters": {
            "type": "object",
            "properties": {
                "certificate_id": {"type": "integer"}
            },
            "required": ["certificate_id"]
        }
    },
    {
        "name": "get_airline_requirements",
        "description": "Get pet travel requirements for a specific airline",
        "parameters": {
            "type": "object",
            "properties": {
                "airline": {"type": "string"},
                "pet_weight_kg": {"type": "number"},
                "species": {"type": "string"}
            },
            "required": ["airline"]
        }
    }
]
```

## Example AI Conversations

### Planning International Travel
```
Owner: I'm taking Luna to the United States next month.
       What do I need?

AI: Great! I can help you prepare Luna for travel to the USA.

    🇺🇸 USA ENTRY REQUIREMENTS FOR DOGS
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    ✅ REQUIRED:
    • Valid rabies vaccination (30+ days before travel)
    • Health certificate (within 10 days of departure)
    • Microchip (ISO 11784/11785 recommended)

    Let me check Luna's records...

    📋 LUNA'S STATUS:
    ✅ Rabies vaccine: Current (expires March 2026)
    ✅ Microchip: 941000024681234 (ISO compliant)
    ⏳ Health certificate: Needs to be issued

    When exactly are you traveling?

Owner: January 15th, coming back February 5th

AI: Perfect! I've created a travel plan for Luna.

    📅 TRAVEL PREPARATION TIMELINE
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    ✅ Already done:
    • Rabies vaccine (current)
    • Microchip registered

    📆 January 5-10 (window for health exam):
    • Schedule travel health exam
    • I recommend January 8th (7 days before)

    📆 January 8 (at appointment):
    • Physical examination
    • Health certificate issued
    • Certificate valid until January 18

    📆 January 15:
    • Departure to USA
    • Bring: Health certificate, vaccination records

    Would you like me to:
    1. Book the travel exam appointment for January 8
    2. Check airline requirements (which airline?)
    3. Email you the full checklist
```

### Health Certificate Issuance (Staff View)
```
Staff: I need to issue a health certificate for Luna,
       traveling to USA on January 15

AI: I'll prepare Luna's health certificate.

    📋 CERTIFICATE PREPARATION
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━

    Pet: Luna (Golden Retriever)
    Owner: María García
    Destination: United States
    Departure: January 15, 2026

    REQUIREMENTS VERIFICATION:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━

    ✅ Rabies Vaccination
       Date: November 15, 2025
       Vaccine: Nobivac Rabies
       Lot: RB2025-1234
       Valid through: March 2026

    ✅ Microchip
       Number: 941000024681234
       Location: Left shoulder
       ISO 11784/11785: Yes

    ✅ Physical Examination
       Date: Today (January 8, 2026)
       Examiner: Dr. Pablo Rojo

    ⏳ Pending: Vet signature

    Certificate details:
    • Number: PF-2026-0047
    • Type: Generic International
    • Issue date: January 8, 2026
    • Valid through: January 18, 2026

    Ready to generate certificate?
    Dr. Pablo will need to review and sign.

Staff: Yes, generate it

AI: ✅ Certificate PF-2026-0047 generated!

    📄 Draft certificate ready for review
    📧 Sent to Dr. Pablo for digital signature

    Next steps:
    1. Dr. Pablo reviews and signs
    2. PDF generated with QR code
    3. Client can pick up or receive by email

    The certificate includes:
    • Clinic letterhead
    • QR code for verification
    • All vaccination details
    • Microchip confirmation
    • Physical exam findings

    Client pickup scheduled for: January 10
```

### Checking Destination Requirements
```
Owner: What do I need to take my cat to Europe?

AI: Taking a cat to Europe (EU) has specific requirements.
    Which country are you traveling to?

Owner: Spain

AI: 🇪🇸 SPAIN (EU) ENTRY REQUIREMENTS FOR CATS
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    ✅ REQUIRED:
    1. Microchip (ISO 11784/11785) - MUST be done before
       rabies vaccine
    2. Rabies vaccination (21+ days before travel)
    3. EU-format health certificate (within 10 days)
    4. Tapeworm treatment (1-5 days before arrival)
       - Only for dogs, NOT required for cats ✓

    📋 IMPORTANT TIMING:
    • Microchip → THEN rabies vaccine → wait 21 days → travel

    ⚠️ SPECIAL NOTES FOR EU:
    • Mexico is NOT on the EU "favorable" country list
    • Additional rabies blood test (titer) may be required
    • Consult with official SENASICA for endorsement

    Let me check your cat's records...

    Which cat is traveling?

Owner: Michi

AI: 📋 MICHI'S STATUS FOR SPAIN TRAVEL:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    ✅ Microchip: 985121012345678 (ISO compliant)
       Implanted: March 2023

    ✅ Rabies vaccine: Current
       Date: October 10, 2025
       (After microchip - correct order ✓)

    ⚠️ May need: Rabies titer blood test
       - Takes 2-4 weeks for results
       - Must show adequate antibodies

    ⏳ Need: Health certificate (within 10 days of travel)

    When are you planning to travel?
```

## Common Destinations Quick Reference

### United States (from Mexico)
- Rabies vaccine: Required (30+ days before)
- Microchip: Recommended (ISO)
- Health certificate: Within 10 days
- CDC requirements vary by state

### European Union (from Mexico)
- Microchip: Required (before rabies vaccine)
- Rabies vaccine: 21+ days before
- Rabies titer test: Often required (non-favorable country)
- EU health certificate format
- SENASICA endorsement

### Canada
- Rabies vaccine: Required (30+ days before)
- Health certificate: Within 10 days
- No quarantine if compliant

## Definition of Done

- [ ] TravelDestination model with requirements database
- [ ] AirlineRequirement model
- [ ] TravelPlan model with checklist tracking
- [ ] HealthCertificate model with PDF generation
- [ ] QR code generation for verification
- [ ] Certificate verification endpoint
- [ ] AI tools for requirement lookup
- [ ] Reminder system for preparation timeline
- [ ] Integration with pet medical records
- [ ] Multi-language support (Spanish/English)
- [ ] Tests written and passing (>95% coverage)

## Dependencies

- S-003: Pet Profiles (pet records, vaccinations)
- S-004: Appointments (travel exam booking)
- S-012: Notifications (reminders)
- S-020: Billing (certificate fees)

## Notes

- Keep destination requirements database updated regularly
- Consider SENASICA (Mexico) integration for official endorsement
- EU requirements are complex - may need specialized workflow
- Certificate validity is typically 10 days - timing is critical
- Store verification history for compliance
- Consider airline partnerships for streamlined process
