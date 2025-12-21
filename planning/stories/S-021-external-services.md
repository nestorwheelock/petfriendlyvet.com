# S-021: External Services (Grooming, Boarding, etc.)

**Story Type:** User Story
**Priority:** Medium
**Epoch:** 2 (with Appointments)
**Status:** PENDING
**Module:** django-vet-clinic + django-crm-lite

## User Story

**As a** pet owner
**I want to** get recommendations for grooming and boarding services
**So that** I can find trusted providers for my pet's needs

**As a** clinic staff member
**I want to** track referrals to external service providers
**So that** I can follow up on pet care and maintain partner relationships

**As a** clinic owner
**I want to** manage relationships with external service partners
**So that** I can offer comprehensive pet care through trusted referrals

## Important Note

**Grooming and boarding are OUTSOURCED to partner businesses, not done in-house.**

This story covers referral tracking and partner management, NOT direct service delivery.

## Acceptance Criteria

### Partner Directory
- [ ] Maintain directory of external service partners
- [ ] Categories: Grooming, Boarding, Daycare, Training, etc.
- [ ] Partner contact information and location
- [ ] Services offered with pricing (if shared)
- [ ] Operating hours and availability
- [ ] Quality ratings and notes
- [ ] Partner agreement tracking

### Referral Tracking
- [ ] Record when clients are referred to partners
- [ ] Track which service was recommended
- [ ] Follow up on client feedback
- [ ] Commission/kickback tracking (if applicable)
- [ ] Volume reporting by partner

### Client Convenience
- [ ] AI recommends partners based on client needs
- [ ] Provide partner contact information
- [ ] Optional: Schedule on behalf of client (if partner allows)
- [ ] Integration with pet records (note when pet is at boarding)

### Pet Record Integration
- [ ] Link referrals to pet profiles
- [ ] Note when pet is at external boarding
- [ ] Medication handoff documentation
- [ ] Special care instructions for partner

## Technical Requirements

### Models

```python
class ExternalPartner(models.Model):
    """External service partner (grooming, boarding, etc.)"""
    PARTNER_TYPES = [
        ('grooming', 'Grooming'),
        ('boarding', 'Boarding'),
        ('daycare', 'Daycare'),
        ('training', 'Training'),
        ('walking', 'Dog Walking'),
        ('sitting', 'Pet Sitting'),
        ('transport', 'Pet Transport'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active Partner'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending Approval'),
    ]

    # Basic info
    name = models.CharField(max_length=200)
    partner_type = models.CharField(max_length=20, choices=PARTNER_TYPES)
    description = models.TextField(blank=True)

    # Contact
    contact_name = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=20)
    whatsapp = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)

    # Location
    address = models.TextField()
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    distance_km = models.FloatField(null=True, blank=True)  # From Pet-Friendly

    # Services
    services_offered = models.JSONField(default=list)
    # e.g., ["bath", "haircut", "nail_trim", "teeth_cleaning"]

    species_accepted = models.JSONField(default=list)
    # e.g., ["dog", "cat"]

    # Hours
    hours = models.JSONField(default=dict)
    # {"monday": {"open": "09:00", "close": "18:00"}, ...}

    # Pricing (if shared by partner)
    pricing = models.JSONField(default=dict, blank=True)
    # {"bath_small": 150, "bath_medium": 200, ...}

    # Quality tracking
    rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    # Internal rating 1-5

    total_referrals = models.IntegerField(default=0)
    positive_feedback = models.IntegerField(default=0)
    negative_feedback = models.IntegerField(default=0)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)  # Internal notes

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_referral_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_partner_type_display()})"


class PartnerAgreement(models.Model):
    """Business agreement with external partner"""
    AGREEMENT_TYPES = [
        ('informal', 'Informal Referral'),
        ('commission', 'Commission-Based'),
        ('discount', 'Client Discount'),
        ('mutual', 'Mutual Referral'),
    ]

    partner = models.ForeignKey(ExternalPartner, on_delete=models.CASCADE, related_name='agreements')

    agreement_type = models.CharField(max_length=20, choices=AGREEMENT_TYPES, default='informal')

    # Terms
    commission_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    # Commission Pet-Friendly receives per referral

    client_discount_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    # Discount clients get when referred

    terms_notes = models.TextField(blank=True)

    # Validity
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    # Documents
    contract_file = models.FileField(upload_to='partner_contracts/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ExternalReferral(models.Model):
    """Record of referral to external partner"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('contacted', 'Client Contacted Partner'),
        ('scheduled', 'Appointment Scheduled'),
        ('completed', 'Service Completed'),
        ('cancelled', 'Cancelled'),
        ('no_response', 'No Response'),
    ]

    # Who
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='external_referrals')
    pet = models.ForeignKey('vet_clinic.Pet', on_delete=models.CASCADE, related_name='external_referrals')
    partner = models.ForeignKey(ExternalPartner, on_delete=models.PROTECT, related_name='referrals')

    # What
    service_type = models.CharField(max_length=50)
    service_details = models.TextField(blank=True)

    # Special instructions
    special_instructions = models.TextField(blank=True)
    # e.g., "Luna is nervous with nail trims, please be patient"

    medications_to_handoff = models.JSONField(default=list)
    # Medications that need to be given during boarding

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Scheduling
    scheduled_date = models.DateField(null=True, blank=True)
    scheduled_time = models.TimeField(null=True, blank=True)

    # Follow-up
    follow_up_date = models.DateField(null=True, blank=True)
    follow_up_completed = models.BooleanField(default=False)

    # Feedback
    FEEDBACK_CHOICES = [
        ('positive', 'Positive'),
        ('neutral', 'Neutral'),
        ('negative', 'Negative'),
    ]
    client_feedback = models.CharField(max_length=20, choices=FEEDBACK_CHOICES, null=True, blank=True)
    feedback_notes = models.TextField(blank=True)

    # Commission (if applicable)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    commission_paid = models.BooleanField(default=False)
    commission_paid_date = models.DateField(null=True, blank=True)

    # Staff
    referred_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='referrals_made'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']


class BoardingStay(models.Model):
    """Track when pet is at external boarding"""
    pet = models.ForeignKey('vet_clinic.Pet', on_delete=models.CASCADE, related_name='boarding_stays')
    partner = models.ForeignKey(ExternalPartner, on_delete=models.PROTECT)
    referral = models.ForeignKey(ExternalReferral, on_delete=models.SET_NULL, null=True, blank=True)

    # Dates
    check_in_date = models.DateField()
    check_in_time = models.TimeField(null=True, blank=True)
    expected_checkout = models.DateField()
    actual_checkout = models.DateTimeField(null=True, blank=True)

    # Status
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('checked_in', 'Currently Boarding'),
        ('checked_out', 'Checked Out'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')

    # Care instructions
    feeding_instructions = models.TextField(blank=True)
    medication_schedule = models.JSONField(default=list)
    # [{"medication": "Apoquel", "dose": "1 tablet", "frequency": "daily", "time": "morning"}]

    special_needs = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=200, blank=True)
    emergency_phone = models.CharField(max_length=20, blank=True)

    # Handoff
    medications_provided = models.JSONField(default=list)
    belongings = models.JSONField(default=list)
    # ["bed", "favorite toy", "food (2kg bag)"]

    # Notes
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-check_in_date']
        verbose_name_plural = 'Boarding stays'
```

### AI Tools

```python
EXTERNAL_SERVICES_TOOLS = [
    {
        "name": "find_partner",
        "description": "Find external service partners by type and availability",
        "parameters": {
            "type": "object",
            "properties": {
                "partner_type": {"type": "string", "enum": ["grooming", "boarding", "daycare", "training"]},
                "species": {"type": "string"},
                "date_needed": {"type": "string"},
                "service": {"type": "string"}
            },
            "required": ["partner_type"]
        }
    },
    {
        "name": "create_referral",
        "description": "Create a referral to an external partner",
        "parameters": {
            "type": "object",
            "properties": {
                "pet_id": {"type": "integer"},
                "partner_id": {"type": "integer"},
                "service_type": {"type": "string"},
                "special_instructions": {"type": "string"},
                "scheduled_date": {"type": "string"}
            },
            "required": ["pet_id", "partner_id", "service_type"]
        }
    },
    {
        "name": "record_boarding_stay",
        "description": "Record that a pet is staying at external boarding",
        "parameters": {
            "type": "object",
            "properties": {
                "pet_id": {"type": "integer"},
                "partner_id": {"type": "integer"},
                "check_in_date": {"type": "string"},
                "expected_checkout": {"type": "string"},
                "medications": {"type": "array"},
                "special_instructions": {"type": "string"}
            },
            "required": ["pet_id", "partner_id", "check_in_date", "expected_checkout"]
        }
    },
    {
        "name": "get_boarding_status",
        "description": "Check if a pet is currently at boarding",
        "parameters": {
            "type": "object",
            "properties": {
                "pet_id": {"type": "integer"}
            },
            "required": ["pet_id"]
        }
    },
    {
        "name": "record_referral_feedback",
        "description": "Record client feedback on external service",
        "parameters": {
            "type": "object",
            "properties": {
                "referral_id": {"type": "integer"},
                "feedback": {"type": "string", "enum": ["positive", "neutral", "negative"]},
                "notes": {"type": "string"}
            },
            "required": ["referral_id", "feedback"]
        }
    },
    {
        "name": "get_partner_stats",
        "description": "Get referral statistics for a partner",
        "parameters": {
            "type": "object",
            "properties": {
                "partner_id": {"type": "integer"},
                "date_range": {"type": "string"}
            },
            "required": ["partner_id"]
        }
    }
]
```

## Example AI Conversations

### Finding Grooming Services
```
Owner: Luna needs a bath and haircut, do you have recommendations?

AI: I can recommend some great groomers we work with!

    Based on Luna's needs (medium dog, standard coat):

    🐕 RECOMMENDED GROOMERS
    ━━━━━━━━━━━━━━━━━━━━━━

    1. Pet Spa Puerto Morelos ⭐ 4.8
       📍 2 km from Pet-Friendly
       💰 Bath + haircut: ~$350-450 MXN
       📞 998-555-1234
       ✨ Clients love their gentle handling

    2. Doggy Style Grooming ⭐ 4.6
       📍 3 km away
       💰 Bath + haircut: ~$300-400 MXN
       📞 998-555-5678
       ✨ Great for nervous dogs

    Would you like me to:
    1. Give you their contact info to call directly
    2. Note any special instructions for Luna
    3. Add this to Luna's record for follow-up

Owner: Can you give me Pet Spa's info and note that Luna
       doesn't like her nails trimmed

AI: ✅ Here's the info for Pet Spa Puerto Morelos:

    📞 Phone: 998-555-1234
    📱 WhatsApp: 998-555-1234
    📍 Av. Javier Rojo Gómez, Puerto Morelos
    🕐 Hours: Mon-Sat 9am-6pm

    I've noted in Luna's referral:
    "Luna is nervous with nail trims - please be
    patient and gentle, or skip if too stressed."

    When you schedule, mention you were referred
    by Pet-Friendly for a 10% discount!

    Shall I set a reminder to ask how it went?
```

### Boarding Coordination
```
Owner: I'm traveling next week. Can you recommend
       somewhere to board Max?

AI: Of course! Let me find the best options for Max.

    Max's profile:
    • Golden Retriever, 5 years, 30kg
    • Current medications: Apoquel (daily)
    • No special diet

    🏠 RECOMMENDED BOARDING
    ━━━━━━━━━━━━━━━━━━━━━━━

    1. Happy Tails Boarding ⭐ 4.9
       📍 5 km from clinic
       💰 $350/night (includes walks)
       ✅ Can administer medications
       📞 998-555-9999

    2. Casa Canina ⭐ 4.7
       📍 8 km away
       💰 $280/night
       ✅ Large outdoor area
       📞 998-555-8888

    Important: Max takes Apoquel daily. I can prepare
    his medication doses for the boarding stay.

    What are your travel dates?

Owner: December 26 to January 2

AI: Perfect! For Max's 7-night stay (Dec 26 - Jan 2):

    📋 BOARDING PREPARATION CHECKLIST
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    Medication prep:
    ✅ 7 doses of Apoquel prepared
    ✅ Instructions: 1 tablet with breakfast

    I recommend:
    1. Call Happy Tails to reserve (998-555-9999)
    2. Pick up Max's medication pack from us Dec 24-25
    3. Bring his bed/blanket for comfort

    Should I:
    1. Create a medication handoff document
    2. Set reminder for Dec 24 to pick up meds
    3. Schedule a post-boarding checkup for Jan 3
```

### Staff View - Partner Management
```
Staff: Show me our grooming partner statistics

AI: 📊 Grooming Partner Statistics (Last 90 Days)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    Pet Spa Puerto Morelos
    • Referrals: 28
    • Positive feedback: 26 (93%)
    • Negative feedback: 1 (4%)
    • Commission earned: $840 MXN

    Doggy Style Grooming
    • Referrals: 15
    • Positive feedback: 13 (87%)
    • Negative feedback: 0
    • Commission earned: $450 MXN

    Pending Feedback:
    • 5 referrals awaiting client feedback

    📈 Trend: Referrals up 20% from last quarter

    Would you like to:
    1. View detailed feedback comments
    2. Update partner information
    3. Add a new partner
```

## Definition of Done

- [ ] Partner model with full directory fields
- [ ] Partner agreement tracking
- [ ] Referral creation and tracking
- [ ] Boarding stay tracking with medication handoff
- [ ] AI tools for partner recommendations
- [ ] Client feedback collection
- [ ] Commission tracking (if applicable)
- [ ] Integration with pet records
- [ ] Staff partner management views
- [ ] Tests written and passing (>95% coverage)

## Dependencies

- S-003: Pet Profiles (link referrals to pets)
- S-004: Appointment system (for scheduling)
- S-007: CRM (owner profiles)
- S-010: Pharmacy (medication handoff)

## Notes

- Focus on referral tracking, NOT direct service management
- Partners manage their own scheduling and operations
- Pet-Friendly's role is recommendation and coordination
- Medication handoff is critical for boarding stays
- Commission tracking is optional (depends on agreements)
- Consider adding partner portal in future version

## Development Process

**Before implementing this story**, review and follow the **23-Step TDD Cycle** in:
- `CLAUDE.md` - Global development workflow
- `planning/TASK_BREAKDOWN.md` - Specific tasks for this story

Tests must be written before implementation. >95% coverage required.
