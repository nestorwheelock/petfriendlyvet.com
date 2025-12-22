# S-025: Referral Network & Visiting Specialists

> **REQUIRED READING:** Before implementation, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md)

**Story Type:** User Story
**Priority:** Medium
**Epoch:** 4 (with Communications)
**Status:** PENDING
**Module:** django-vet-clinic + django-crm-lite

## User Story

**As a** veterinarian
**I want to** refer patients to specialists when needed
**So that** pets get the specialized care they require

**As a** clinic owner
**I want to** host visiting specialists at my clinic
**So that** I can offer advanced services without owning equipment

**As a** pet owner
**I want to** access specialist care through my regular vet
**So that** I have continuity of care and convenience

**As a** referring veterinarian (external)
**I want to** send patients to Pet-Friendly for services
**So that** my patients get quality lab work and diagnostics

## Acceptance Criteria

### Specialist Directory
- [ ] Specialist veterinarians (oncology, cardiology, orthopedics, ophthalmology, dermatology)
- [ ] Emergency hospitals (24-hour facilities)
- [ ] Imaging centers (X-ray, MRI, CT, ultrasound)
- [ ] Laboratories (reference labs)
- [ ] Rehabilitation/physical therapy centers
- [ ] Behaviorists
- [ ] Contact information and availability
- [ ] Services offered and pricing (if known)
- [ ] Quality ratings based on referral outcomes

### Outbound Referrals
- [ ] Create referral with patient information
- [ ] Include relevant medical history
- [ ] Send referral electronically (email, fax, portal)
- [ ] Track referral status (sent, seen, report received)
- [ ] Receive feedback/reports from specialist
- [ ] Integrate specialist findings into pet records

### Visiting Specialists
- [ ] Schedule specialists who come TO Pet-Friendly
- [ ] Define visiting days/hours per specialist
- [ ] Equipment they bring (portable ultrasound, etc.)
- [ ] Book appointments with visiting specialist
- [ ] Revenue sharing/fee arrangements
- [ ] Results integration into pet records
- [ ] Client communication about visiting specialist availability

### Incoming Referrals
- [ ] Track patients referred TO Pet-Friendly from other vets
- [ ] Record referring veterinarian information
- [ ] Communicate results back to referring vet
- [ ] Thank you/follow-up workflow
- [ ] Link to B2B professional accounts (S-020)

### Reporting
- [ ] Referrals by specialist type
- [ ] Visiting specialist revenue
- [ ] Referral volume trends
- [ ] Outcome tracking
- [ ] Partner relationship health

## Technical Requirements

### Models

```python
class Specialist(models.Model):
    """Specialist veterinarian or facility"""
    SPECIALIST_TYPES = [
        ('oncology', 'Oncology'),
        ('cardiology', 'Cardiology'),
        ('orthopedics', 'Orthopedics'),
        ('ophthalmology', 'Ophthalmology'),
        ('dermatology', 'Dermatology'),
        ('neurology', 'Neurology'),
        ('surgery', 'Surgery'),
        ('internal_medicine', 'Internal Medicine'),
        ('emergency', 'Emergency/Critical Care'),
        ('imaging', 'Imaging/Radiology'),
        ('laboratory', 'Laboratory'),
        ('rehabilitation', 'Rehabilitation'),
        ('behavior', 'Behavior'),
        ('exotics', 'Exotic Animals'),
        ('dentistry', 'Dentistry'),
        ('other', 'Other'),
    ]

    # Basic info
    name = models.CharField(max_length=200)
    specialty = models.CharField(max_length=50, choices=SPECIALIST_TYPES)
    credentials = models.CharField(max_length=200, blank=True)
    # e.g., "DACVIM (Oncology)", "Diplomate ACVS"

    # Individual or facility
    is_facility = models.BooleanField(default=False)
    # True for hospitals, labs, imaging centers

    clinic_name = models.CharField(max_length=200, blank=True)
    # If individual, their clinic name

    # Contact
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20)
    fax = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)

    # Location
    address = models.TextField()
    city = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    distance_km = models.FloatField(null=True, blank=True)

    # Hours
    is_24_hours = models.BooleanField(default=False)
    hours = models.JSONField(default=dict)

    # Services
    services = models.JSONField(default=list)
    # ["chemotherapy", "radiation", "surgery"]

    species_treated = models.JSONField(default=list)
    # ["dog", "cat", "exotic"]

    # Visiting specialist info
    is_visiting = models.BooleanField(default=False)
    # Comes to Pet-Friendly to provide services

    visiting_services = models.JSONField(default=list)
    # Services provided when visiting

    equipment_provided = models.JSONField(default=list)
    # ["portable_ultrasound", "endoscope"]

    # Relationship
    relationship_status = models.CharField(max_length=20, default='active')
    # active, inactive, pending

    referral_agreement = models.TextField(blank=True)
    revenue_share_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    # For visiting specialists

    # Stats
    total_referrals_sent = models.IntegerField(default=0)
    total_referrals_received = models.IntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)

    # Notes
    notes = models.TextField(blank=True)
    referral_instructions = models.TextField(blank=True)
    # How to send referrals to this specialist

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']


class VisitingSchedule(models.Model):
    """Schedule for visiting specialists"""
    specialist = models.ForeignKey(Specialist, on_delete=models.CASCADE, related_name='visiting_schedules')

    # When
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    # Recurring
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(max_length=50, blank=True)
    # "weekly", "biweekly", "monthly_first_tuesday", etc.

    # Capacity
    max_appointments = models.IntegerField(null=True, blank=True)
    appointments_booked = models.IntegerField(default=0)

    # Services available this visit
    services_available = models.JSONField(default=list)

    # Equipment
    equipment_bringing = models.JSONField(default=list)

    # Status
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    cancellation_reason = models.TextField(blank=True)

    # Notes
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'start_time']


class Referral(models.Model):
    """Referral to/from specialist"""
    DIRECTION_CHOICES = [
        ('outbound', 'Outbound (To Specialist)'),
        ('inbound', 'Inbound (From Other Vet)'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('received', 'Received by Specialist'),
        ('scheduled', 'Appointment Scheduled'),
        ('seen', 'Patient Seen'),
        ('report_pending', 'Awaiting Report'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('declined', 'Declined by Specialist'),
    ]

    URGENCY_CHOICES = [
        ('routine', 'Routine'),
        ('urgent', 'Urgent (Within Week)'),
        ('emergency', 'Emergency (Same Day)'),
    ]

    # Direction
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)

    # Referral number
    referral_number = models.CharField(max_length=50, unique=True)

    # Patient
    pet = models.ForeignKey('vet_clinic.Pet', on_delete=models.CASCADE, related_name='referrals')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pet_referrals')

    # Specialist (for outbound) or referring vet (for inbound)
    specialist = models.ForeignKey(
        Specialist, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='referrals_received'
    )

    # For inbound referrals
    referring_vet_name = models.CharField(max_length=200, blank=True)
    referring_clinic = models.CharField(max_length=200, blank=True)
    referring_contact = models.CharField(max_length=200, blank=True)
    referring_professional_account = models.ForeignKey(
        'billing.ProfessionalAccount', on_delete=models.SET_NULL, null=True, blank=True
    )

    # Reason
    reason = models.TextField()
    clinical_summary = models.TextField(blank=True)
    # Relevant history for the specialist

    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, default='routine')
    requested_services = models.JSONField(default=list)
    # ["consultation", "ultrasound", "surgery"]

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Dates
    sent_at = models.DateTimeField(null=True, blank=True)
    appointment_date = models.DateTimeField(null=True, blank=True)
    seen_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Results
    specialist_findings = models.TextField(blank=True)
    specialist_diagnosis = models.TextField(blank=True)
    specialist_recommendations = models.TextField(blank=True)
    follow_up_needed = models.BooleanField(default=False)
    follow_up_instructions = models.TextField(blank=True)

    # Outcome
    OUTCOME_CHOICES = [
        ('successful', 'Successful Treatment'),
        ('ongoing', 'Ongoing Treatment'),
        ('referred_again', 'Referred to Another Specialist'),
        ('no_treatment', 'No Treatment Possible'),
        ('client_declined', 'Client Declined Treatment'),
        ('euthanasia', 'Euthanasia'),
        ('unknown', 'Unknown'),
    ]
    outcome = models.CharField(max_length=20, choices=OUTCOME_CHOICES, blank=True)
    outcome_notes = models.TextField(blank=True)

    # Feedback
    client_satisfaction = models.IntegerField(null=True, blank=True)
    # 1-5 rating

    quality_rating = models.IntegerField(null=True, blank=True)
    # Internal rating of specialist 1-5

    # Staff
    referred_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='referrals_created'
    )

    # Billing
    invoice = models.ForeignKey(
        'billing.Invoice', on_delete=models.SET_NULL, null=True, blank=True
    )

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']


class ReferralDocument(models.Model):
    """Documents attached to referral"""
    referral = models.ForeignKey(Referral, on_delete=models.CASCADE, related_name='documents')

    DOCUMENT_TYPES = [
        ('referral_letter', 'Referral Letter'),
        ('medical_history', 'Medical History'),
        ('lab_results', 'Lab Results'),
        ('imaging', 'Imaging (X-ray, Ultrasound)'),
        ('specialist_report', 'Specialist Report'),
        ('prescription', 'Prescription'),
        ('other', 'Other'),
    ]

    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='referrals/')
    description = models.TextField(blank=True)

    # Source
    is_outgoing = models.BooleanField(default=True)
    # True = sent with referral, False = received from specialist

    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)


class ReferralNote(models.Model):
    """Communication notes on referral"""
    referral = models.ForeignKey(Referral, on_delete=models.CASCADE, related_name='notes_list')

    note = models.TextField()
    is_internal = models.BooleanField(default=True)
    # Internal notes vs shared with specialist/owner

    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class VisitingAppointment(models.Model):
    """Appointment with visiting specialist"""
    schedule = models.ForeignKey(VisitingSchedule, on_delete=models.CASCADE, related_name='appointments')
    specialist = models.ForeignKey(Specialist, on_delete=models.CASCADE)

    pet = models.ForeignKey('vet_clinic.Pet', on_delete=models.CASCADE, related_name='visiting_appointments')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='visiting_appointments')

    # Time slot
    appointment_time = models.TimeField()
    duration_minutes = models.IntegerField(default=30)

    # Service
    service = models.CharField(max_length=100)
    reason = models.TextField()

    # Status
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked In'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('no_show', 'No Show'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')

    # Results
    findings = models.TextField(blank=True)
    diagnosis = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)

    # Documents
    report_file = models.FileField(upload_to='visiting_reports/', null=True, blank=True)
    images = models.JSONField(default=list)
    # Ultrasound images, etc.

    # Billing
    fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pet_friendly_share = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    invoice = models.ForeignKey('billing.Invoice', on_delete=models.SET_NULL, null=True, blank=True)

    # Follow-up
    follow_up_needed = models.BooleanField(default=False)
    follow_up_notes = models.TextField(blank=True)

    # Related referral (if from referral workflow)
    referral = models.ForeignKey(Referral, on_delete=models.SET_NULL, null=True, blank=True)

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['schedule__date', 'appointment_time']
```

### AI Tools

```python
REFERRAL_NETWORK_TOOLS = [
    {
        "name": "find_specialist",
        "description": "Find specialists by type and location",
        "parameters": {
            "type": "object",
            "properties": {
                "specialty": {"type": "string"},
                "species": {"type": "string"},
                "urgent": {"type": "boolean"}
            },
            "required": ["specialty"]
        }
    },
    {
        "name": "get_visiting_schedule",
        "description": "Get schedule for visiting specialists",
        "parameters": {
            "type": "object",
            "properties": {
                "specialty": {"type": "string"},
                "date_from": {"type": "string"},
                "date_to": {"type": "string"}
            }
        }
    },
    {
        "name": "create_referral",
        "description": "Create a referral to a specialist",
        "parameters": {
            "type": "object",
            "properties": {
                "pet_id": {"type": "integer"},
                "specialist_id": {"type": "integer"},
                "reason": {"type": "string"},
                "urgency": {"type": "string"},
                "services_requested": {"type": "array"}
            },
            "required": ["pet_id", "specialist_id", "reason"]
        }
    },
    {
        "name": "book_visiting_specialist",
        "description": "Book appointment with visiting specialist",
        "parameters": {
            "type": "object",
            "properties": {
                "pet_id": {"type": "integer"},
                "schedule_id": {"type": "integer"},
                "service": {"type": "string"},
                "reason": {"type": "string"},
                "preferred_time": {"type": "string"}
            },
            "required": ["pet_id", "schedule_id", "service"]
        }
    },
    {
        "name": "update_referral_status",
        "description": "Update status of a referral",
        "parameters": {
            "type": "object",
            "properties": {
                "referral_id": {"type": "integer"},
                "status": {"type": "string"},
                "notes": {"type": "string"}
            },
            "required": ["referral_id", "status"]
        }
    },
    {
        "name": "record_specialist_report",
        "description": "Record specialist findings and recommendations",
        "parameters": {
            "type": "object",
            "properties": {
                "referral_id": {"type": "integer"},
                "findings": {"type": "string"},
                "diagnosis": {"type": "string"},
                "recommendations": {"type": "string"}
            },
            "required": ["referral_id"]
        }
    },
    {
        "name": "get_referral_status",
        "description": "Check status of a referral",
        "parameters": {
            "type": "object",
            "properties": {
                "referral_id": {"type": "integer"}
            },
            "required": ["referral_id"]
        }
    }
]
```

## Example AI Conversations

### Finding a Specialist
```
Dr. Pablo: I need an oncologist for Max. He has a suspicious mass.

AI: 🏥 ONCOLOGY SPECIALISTS
    ━━━━━━━━━━━━━━━━━━━━━━━

    1. Dr. Ana Martínez - Veterinary Oncology
       📍 Hospital Veterinario Cancún (25 km)
       📞 998-884-5678
       ⭐ 4.8 rating (23 referrals)
       Services: Consultation, Chemotherapy, Surgery
       Next available: January 3, 2026

    2. Dr. Carlos Vega - DACVIM (Oncology)
       📍 Playa del Carmen (45 km)
       📞 984-873-2345
       ⭐ 4.9 rating (15 referrals)
       Services: Consultation, Chemotherapy, Radiation
       Next available: January 8, 2026

    3. 🏥 VISITING SPECIALIST
       Dr. Roberto Sánchez - Oncology
       📍 Comes to Pet-Friendly!
       Next visit: December 28, 2025
       Services: Consultation, Staging, Chemotherapy planning

    Based on Max's case, I recommend:
    • If urgent: Dr. Martínez (soonest availability)
    • For convenience: Dr. Sánchez visiting Dec 28

    Would you like to:
    1. Create a referral to Dr. Martínez
    2. Book with visiting oncologist (Dec 28)
    3. See more specialists
```

### Creating an Outbound Referral
```
Dr. Pablo: Create a referral to Dr. Martínez for Max

AI: 📋 CREATING REFERRAL
    ━━━━━━━━━━━━━━━━━━━━━

    Patient: Max (Golden Retriever, 8 years)
    Owner: Roberto García
    Specialist: Dr. Ana Martínez (Oncology)

    Reason for referral: Suspicious mass evaluation

    I'll include from Max's records:
    ✓ Recent exam findings
    ✓ Lab results (CBC, Chemistry from Dec 15)
    ✓ X-ray images from Dec 18
    ✓ Current medications

    Clinical summary (please confirm):
    "8-year-old MN Golden Retriever with firm
    subcutaneous mass on left flank, first noticed
    2 weeks ago. FNA pending. No weight loss or
    appetite changes. Otherwise healthy."

    Urgency level: Urgent (recommend within 1 week)

    Send referral?

Dr. Pablo: Yes, also note he had a mast cell tumor removed 2 years ago

AI: ✅ Referral REF-2025-0234 created and sent!

    📧 Sent to: Dr. Ana Martínez
    📄 Includes:
    • Referral letter with clinical summary
    • Previous mast cell tumor history (2023)
    • Lab results (Dec 15)
    • X-ray images (Dec 18)

    📞 Client notification sent to Roberto García
    with specialist contact info.

    I'll track this referral and notify you when:
    • Appointment is scheduled
    • Report is received

    Next: Await specialist confirmation
```

### Booking with Visiting Specialist
```
Owner: Can Luna see the cardiologist when they visit?

AI: 🏥 VISITING CARDIOLOGIST
    ━━━━━━━━━━━━━━━━━━━━━━━━

    Dr. María López - Veterinary Cardiology
    Next visit: January 5, 2026 (Sunday)
    Time: 9:00 AM - 3:00 PM
    Location: Pet-Friendly clinic

    Services available:
    • Cardiac consultation
    • Echocardiogram (portable ultrasound)
    • ECG
    • Blood pressure

    For Luna's heart murmur, I recommend:
    • Full cardiac consultation + Echo
    • Duration: ~45 minutes
    • Fee: $2,500 MXN

    Available slots:
    • 9:00 AM ✓
    • 10:00 AM ✓
    • 11:00 AM ✓
    • 1:00 PM ✓
    • 2:00 PM ✓

    Would you like to book?

Owner: 10am please

AI: ✅ Appointment booked!

    📅 Sunday, January 5, 2026 at 10:00 AM
    👨‍⚕️ Dr. María López (Cardiology)
    🐕 Patient: Luna
    📍 Pet-Friendly clinic

    What to expect:
    • Please arrive 10 min early
    • Luna should be fasted 8 hours before
    • Bring any previous cardiac records if available
    • Duration: ~45 minutes

    📱 Reminder will be sent:
    • 3 days before
    • 1 day before

    Total: $2,500 MXN (payable at visit)
```

### Receiving Specialist Report
```
AI: 📬 SPECIALIST REPORT RECEIVED
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    Referral: REF-2025-0234
    Patient: Max (García)
    Specialist: Dr. Ana Martínez (Oncology)
    Date seen: January 4, 2026

    📋 SUMMARY:
    Diagnosis: Mast Cell Tumor Grade II
    Recommendations: Wide surgical excision,
    followed by adjuvant chemotherapy

    📄 Full report attached
    🖼️ Cytology images attached

    Recommended actions:
    1. Review full report
    2. Schedule follow-up with owner
    3. Discuss treatment options

    Mark as reviewed?

Dr. Pablo: Yes, schedule owner callback

AI: ✅ Report marked as reviewed

    📞 Callback scheduled:
    • Roberto García (Max's owner)
    • Suggested: Tomorrow 10:00 AM
    • Topic: Oncology results and treatment options

    Reminder set for tomorrow at 9:45 AM.

    I've added the specialist findings to
    Max's medical record.
```

## Definition of Done

- [ ] Specialist directory with full details
- [ ] Visiting specialist schedule management
- [ ] Outbound referral workflow
- [ ] Inbound referral tracking
- [ ] Document attachment and sharing
- [ ] Referral status tracking
- [ ] Visiting appointment booking
- [ ] Results integration into pet records
- [ ] Revenue sharing tracking for visiting specialists
- [ ] AI tools for referral management
- [ ] Reporting dashboard
- [ ] Tests written and passing (>95% coverage)

## Dependencies

- S-003: Pet Profiles (patient records)
- S-004: Appointments (for visiting appointments)
- S-006: Omnichannel (referral communications)
- S-020: Billing (B2B accounts, visiting fees)

## Notes

- Build relationships with specialists in Cancún/Playa del Carmen
- Visiting specialists provide significant value (oncology, cardiology, imaging)
- Consider patient transport partnerships for non-mobile patients
- HIPAA-equivalent privacy for shared medical records
- PDF generation for referral letters
- Consider specialist portal for direct communication (future)

## Development Process

**Before implementing this story**, review and follow the **23-Step TDD Cycle** in:
- `CLAUDE.md` - Global development workflow
- `planning/TASK_BREAKDOWN.md` - Specific tasks for this story

Tests must be written before implementation. >95% coverage required.
