# S-015: Emergency Services

> **REQUIRED READING:** Before implementation, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md)

**Story Type:** User Story
**Priority:** High
**Epoch:** 4 (with Communications)
**Status:** PENDING
**Module:** django-omnichannel + django-appointments

## User Story

**As a** pet owner with an emergency
**I want to** quickly reach the clinic and get help
**So that** my pet receives urgent care when needed

**As a** clinic owner
**I want to** manage after-hours emergencies efficiently
**So that** I can provide emergency care without burnout

**As a** pet owner
**I want to** know what constitutes an emergency
**So that** I can make informed decisions about my pet's care

## Acceptance Criteria

### Emergency Detection
- [ ] AI recognizes emergency keywords and urgency
- [ ] Triage questions to assess severity
- [ ] Auto-escalate critical situations
- [ ] Clear emergency vs. non-emergency guidance
- [ ] Species-specific emergency recognition

### Emergency Contact Flow
- [ ] Prominent emergency button/number on website
- [ ] 24/7 AI triage available
- [ ] After-hours routing to on-call vet
- [ ] WhatsApp emergency channel
- [ ] Phone callback for critical emergencies

### Emergency Triage
- [ ] Symptom assessment questionnaire
- [ ] Severity classification (Critical/Urgent/Can Wait)
- [ ] First aid instructions while traveling
- [ ] Photo/video upload for assessment
- [ ] Location-based directions to clinic

### After-Hours Protocol
- [ ] On-call schedule management
- [ ] Escalation to backup vet
- [ ] Emergency fee disclosure
- [ ] Clinic opening for emergencies
- [ ] Referral to 24-hour hospitals

### Emergency Records
- [ ] Log all emergency contacts
- [ ] Track outcomes
- [ ] Integrate with regular records
- [ ] Emergency visit notes template
- [ ] Billing for after-hours services

## Technical Requirements

### Models

```python
class EmergencyContact(models.Model):
    """Emergency contact attempt"""
    STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('triaging', 'Triaging'),
        ('escalated', 'Escalated to Staff'),
        ('resolved', 'Resolved'),
        ('referred', 'Referred Elsewhere'),
        ('no_response', 'No Response'),
    ]

    SEVERITY_CHOICES = [
        ('critical', 'Critical - Life Threatening'),
        ('urgent', 'Urgent - Needs Same-Day Care'),
        ('moderate', 'Moderate - Can Wait'),
        ('low', 'Low - Schedule Appointment'),
    ]

    # Contact info
    owner = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    pet = models.ForeignKey(
        'vet_clinic.Pet', on_delete=models.SET_NULL, null=True, blank=True
    )
    phone = models.CharField(max_length=20)
    channel = models.CharField(max_length=20)  # web, whatsapp, phone, sms

    # Emergency details
    reported_symptoms = models.TextField()
    pet_species = models.CharField(max_length=50)
    pet_age = models.CharField(max_length=50, blank=True)

    # Triage
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, null=True)
    triage_notes = models.TextField(blank=True)
    ai_assessment = models.JSONField(default=dict)

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='initiated')

    # Staff handling
    handled_by = models.ForeignKey(
        'practice.StaffProfile', on_delete=models.SET_NULL, null=True, blank=True
    )
    response_time_seconds = models.IntegerField(null=True)

    # Resolution
    resolution = models.TextField(blank=True)
    outcome = models.CharField(max_length=50, blank=True)
    # seen_at_clinic, referred, advice_given, false_alarm, etc.

    # Related records
    appointment = models.ForeignKey(
        'appointments.Appointment', on_delete=models.SET_NULL, null=True, blank=True
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    escalated_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']


class EmergencySymptom(models.Model):
    """Known emergency symptoms for triage"""
    keyword = models.CharField(max_length=100)
    keywords_es = models.JSONField(default=list)  # Spanish variations
    keywords_en = models.JSONField(default=list)  # English variations

    species = models.JSONField(default=list)  # ["dog", "cat", "all"]

    severity = models.CharField(max_length=20)
    description = models.TextField()

    # Triage questions
    follow_up_questions = models.JSONField(default=list)

    # First aid
    first_aid_instructions = models.TextField(blank=True)
    warning_signs = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)


class OnCallSchedule(models.Model):
    """After-hours on-call schedule"""
    staff = models.ForeignKey('practice.StaffProfile', on_delete=models.CASCADE)
    date = models.DateField()

    start_time = models.TimeField()
    end_time = models.TimeField()

    # Contact methods in order
    contact_phone = models.CharField(max_length=20)
    backup_phone = models.CharField(max_length=20, blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    swap_requested = models.BooleanField(default=False)
    swap_with = models.ForeignKey(
        'practice.StaffProfile', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='swap_requests'
    )

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['date', 'start_time']
        unique_together = ['staff', 'date']


class EmergencyReferral(models.Model):
    """Emergency referral hospitals"""
    name = models.CharField(max_length=200)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    whatsapp = models.CharField(max_length=20, blank=True)

    # Location
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    distance_km = models.FloatField(null=True)  # From Pet-Friendly

    # Hours
    is_24_hours = models.BooleanField(default=False)
    hours = models.JSONField(default=dict)

    # Capabilities
    services = models.JSONField(default=list)
    # ["surgery", "xray", "blood_work", "oxygen", "icu"]

    species_treated = models.JSONField(default=list)

    # Status
    is_active = models.BooleanField(default=True)
    last_verified = models.DateField(null=True)

    notes = models.TextField(blank=True)


class EmergencyFirstAid(models.Model):
    """First aid instructions for common emergencies"""
    title = models.CharField(max_length=200)
    title_es = models.CharField(max_length=200)

    condition = models.CharField(max_length=100)
    species = models.JSONField(default=list)

    # Content
    description = models.TextField()
    description_es = models.TextField()

    steps = models.JSONField(default=list)
    # [{"step": 1, "instruction": "...", "instruction_es": "..."}, ...]

    warnings = models.JSONField(default=list)
    do_not = models.JSONField(default=list)  # What NOT to do

    # Media
    video_url = models.URLField(blank=True)
    images = models.JSONField(default=list)

    # Related
    related_symptoms = models.ManyToManyField(EmergencySymptom, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### AI Tools

```python
EMERGENCY_TOOLS = [
    {
        "name": "triage_emergency",
        "description": "Assess emergency severity based on symptoms",
        "parameters": {
            "type": "object",
            "properties": {
                "symptoms": {"type": "string"},
                "species": {"type": "string"},
                "pet_age": {"type": "string"},
                "symptom_duration": {"type": "string"}
            },
            "required": ["symptoms", "species"]
        }
    },
    {
        "name": "escalate_to_oncall",
        "description": "Escalate emergency to on-call veterinarian",
        "parameters": {
            "type": "object",
            "properties": {
                "emergency_contact_id": {"type": "integer"},
                "urgency": {"type": "string"},
                "callback_number": {"type": "string"}
            },
            "required": ["emergency_contact_id", "callback_number"]
        }
    },
    {
        "name": "get_first_aid_instructions",
        "description": "Get first aid instructions for a condition",
        "parameters": {
            "type": "object",
            "properties": {
                "condition": {"type": "string"},
                "species": {"type": "string"}
            },
            "required": ["condition"]
        }
    },
    {
        "name": "get_oncall_status",
        "description": "Get current on-call veterinarian",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_emergency_referrals",
        "description": "Get nearby emergency veterinary hospitals",
        "parameters": {
            "type": "object",
            "properties": {
                "is_24_hours": {"type": "boolean"},
                "species": {"type": "string"}
            }
        }
    },
    {
        "name": "create_emergency_appointment",
        "description": "Create an emergency appointment slot",
        "parameters": {
            "type": "object",
            "properties": {
                "emergency_contact_id": {"type": "integer"},
                "time": {"type": "string"}
            },
            "required": ["emergency_contact_id"]
        }
    },
    {
        "name": "log_emergency_resolution",
        "description": "Log how an emergency was resolved",
        "parameters": {
            "type": "object",
            "properties": {
                "emergency_contact_id": {"type": "integer"},
                "outcome": {"type": "string"},
                "notes": {"type": "string"}
            },
            "required": ["emergency_contact_id", "outcome"]
        }
    }
]
```

## Example AI Conversations

### Critical Emergency Detection
```
Owner: My dog is not breathing right and collapsed!

AI: 🚨 This sounds like a critical emergency.

    I need quick answers to help you:

    1. Is your dog conscious? (eyes open, responsive)
    2. Is there any breathing at all?
    3. What color are the gums? (pink, white, blue)

Owner: She's barely conscious, breathing is very shallow,
       gums look pale

AI: 🚨 CRITICAL - This needs immediate veterinary care.

    📞 CALLING DR. PABLO NOW

    While waiting (1-2 minutes for callback):

    ✓ Keep your dog lying on her side
    ✓ Keep her warm with a blanket
    ✓ Don't give food or water
    ✓ Note the time this started

    If no callback in 2 minutes, call directly:
    📱 998-316-2438

    🏥 Nearest 24-hour hospital (if we can't reach you):
    Hospital Veterinario Cancún
    Av. Tulum, Cancún (25 min drive)
    📞 998-884-5678

    Stay calm - help is on the way.
```

### After-Hours Non-Emergency
```
Owner (11:30 PM): My cat has been vomiting

AI: I understand you're worried. Let me help assess
    the situation.

    A few quick questions:

    1. How many times has your cat vomited?
    2. When did it start?
    3. Is there blood in the vomit?
    4. Is your cat still eating/drinking?
    5. Is your cat acting normal otherwise?

Owner: Twice in the last hour. No blood.
       She ate dinner normally. Seems tired now.

AI: Based on what you've described, this appears to be
    a moderate concern - not immediately life-threatening,
    but should be monitored.

    My Assessment: ⚠️ MONITOR TONIGHT

    This could be:
    • Eating too fast
    • Hairball
    • Mild stomach upset

    ✅ Watch Tonight:
    • Remove food for 2-3 hours
    • Offer small amounts of water
    • Monitor for more vomiting

    🚨 Go to Emergency If:
    • Vomiting continues (>3 more times)
    • Blood appears in vomit
    • She becomes lethargic/unresponsive
    • Abdomen seems painful or bloated

    📅 Recommended: Schedule checkup for tomorrow if
    vomiting continues or she's not eating by morning.

    Would you like me to:
    1. Book first available appointment tomorrow
    2. Get callback from Dr. Pablo tonight
    3. Get directions to 24-hour hospital
```

### On-Call Management (Staff)
```
Dr. Pablo: Who's on call this weekend?

AI: On-Call Schedule for this weekend:

    Friday Night (Dec 20):
    • 6 PM - 8 AM: Dr. Pablo (you)
    • Backup: Dr. García (998-555-1234)

    Saturday (Dec 21):
    • 8 AM - 8 PM: Clinic Open (normal hours)
    • 8 PM - 8 AM: Dr. García

    Sunday (Dec 22):
    • All day/night: Dr. Pablo

    Emergency Stats (Last 7 Days):
    • Total emergency contacts: 4
    • Escalated to vet: 2
    • Came to clinic: 1
    • Referred elsewhere: 0
    • Avg response time: 3.2 minutes

    Would you like to:
    1. Swap a shift
    2. Add backup coverage
    3. View recent emergencies
```

## Emergency Symptom Database

### Critical (Life-Threatening)
- Difficulty breathing / not breathing
- Unconscious / collapsed
- Severe bleeding
- Suspected poisoning
- Seizures lasting >3 minutes
- Suspected bloat (distended abdomen)
- Unable to urinate (especially male cats)
- Hit by car / major trauma

### Urgent (Same-Day)
- Vomiting blood
- Bloody diarrhea
- Eye injury
- Limping / unable to walk
- Not eating >24 hours
- Difficulty giving birth
- Snake/spider bite

### Moderate (Within 24-48 Hours)
- Repeated vomiting (no blood)
- Diarrhea (no blood)
- Mild limping
- Ear infection signs
- Skin wounds (not bleeding heavily)

## Definition of Done

- [ ] Emergency keyword detection in chat
- [ ] Triage questionnaire flow
- [ ] Severity classification
- [ ] Auto-escalation for critical
- [ ] On-call schedule management
- [ ] First aid instructions database
- [ ] Emergency referral directory
- [ ] Phone callback integration
- [ ] Emergency logging and tracking
- [ ] Staff alerts for emergencies
- [ ] Tests written and passing (>95% coverage)

## Dependencies

- S-002: AI Chat (emergency detection)
- S-006: Omnichannel (escalation calls)
- S-008: Practice Management (staff schedules)

## Notes

- Consider integration with answering service
- May need Twilio Voice for automated callbacks
- First aid content should be reviewed by vet
- 24-hour hospital info should be verified regularly
- Consider panic button in mobile app (future)

## Development Process

**Before implementing this story**, review and follow the **23-Step TDD Cycle** in:
- `CLAUDE.md` - Global development workflow
- `planning/TASK_BREAKDOWN.md` - Specific tasks for this story

Tests must be written before implementation. >95% coverage required.
