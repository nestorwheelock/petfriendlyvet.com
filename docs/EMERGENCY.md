# Emergency Module

The `apps.emergency` module handles emergency triage, after-hours support, first aid resources, and referral hospital management for urgent pet care situations.

## Table of Contents

- [Overview](#overview)
- [Models](#models)
  - [EmergencySymptom](#emergencysymptom)
  - [EmergencyContact](#emergencycontact)
  - [OnCallSchedule](#oncallschedule)
  - [EmergencyReferral](#emergencyreferral)
  - [EmergencyFirstAid](#emergencyfirstaid)
- [Views](#views)
- [URL Patterns](#url-patterns)
- [Workflows](#workflows)
  - [Self-Triage Assessment](#self-triage-assessment)
  - [Emergency Contact Submission](#emergency-contact-submission)
  - [On-Call Staff Management](#on-call-staff-management)
  - [First Aid Resources](#first-aid-resources)
- [Severity Levels](#severity-levels)
- [Triage Algorithm](#triage-algorithm)
- [Integration Points](#integration-points)
- [Query Examples](#query-examples)
- [Testing](#testing)

## Overview

The emergency module provides critical services for pet emergencies:

- **Self-Triage System** - Assess symptom severity online
- **Emergency Contact** - Submit urgent requests via multiple channels
- **On-Call Scheduling** - Manage after-hours staff availability
- **Referral Hospitals** - Directory of 24-hour emergency facilities
- **First Aid Guides** - Step-by-step emergency instructions

```
┌─────────────────────────────────────────────────────────────┐
│                   EMERGENCY WORKFLOW                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌──────────────┐     ┌──────────────┐     ┌────────────┐  │
│   │   Symptoms   │────>│  Self-Triage │────>│  Severity  │  │
│   │   Reported   │     │  Assessment  │     │   Result   │  │
│   └──────────────┘     └──────────────┘     └─────┬──────┘  │
│                                                    │         │
│        ┌───────────────────────────────────────────┤         │
│        ▼                  ▼                        ▼         │
│   ┌──────────┐     ┌──────────────┐     ┌────────────────┐  │
│   │ Critical │     │    Urgent    │     │  Moderate/Low  │  │
│   │   ───>   │     │    ───>      │     │     ───>       │  │
│   │ Hospital │     │  Emergency   │     │   Schedule     │  │
│   │ Referral │     │   Contact    │     │   Appointment  │  │
│   └──────────┘     └──────────────┘     └────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Models

### EmergencySymptom

Location: `apps/emergency/models.py`

Known emergency symptoms for triage assessment.

```python
SEVERITY_CHOICES = [
    ('critical', 'Critical - Life Threatening'),
    ('urgent', 'Urgent - Needs Same-Day Care'),
    ('moderate', 'Moderate - Can Wait'),
    ('low', 'Low - Schedule Appointment'),
]

class EmergencySymptom(models.Model):
    keyword = models.CharField(max_length=100)
    keywords_es = models.JSONField(default=list)  # Spanish keywords
    keywords_en = models.JSONField(default=list)  # English keywords

    species = models.JSONField(default=list)  # Applicable species
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    description = models.TextField()

    follow_up_questions = models.JSONField(default=list)
    first_aid_instructions = models.TextField(blank=True)
    warning_signs = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `keyword` | CharField | Primary symptom keyword |
| `keywords_es` | JSONField | Spanish keyword variants |
| `keywords_en` | JSONField | English keyword variants |
| `species` | JSONField | Applicable species list |
| `severity` | CharField | Triage severity level |
| `first_aid_instructions` | TextField | Immediate care steps |
| `warning_signs` | TextField | Signs requiring escalation |

### EmergencyContact

Records of emergency contact attempts from pet owners.

```python
STATUS_CHOICES = [
    ('initiated', 'Initiated'),
    ('triaging', 'Triaging'),
    ('escalated', 'Escalated to Staff'),
    ('resolved', 'Resolved'),
    ('referred', 'Referred Elsewhere'),
    ('no_response', 'No Response'),
]

CHANNEL_CHOICES = [
    ('web', 'Website'),
    ('whatsapp', 'WhatsApp'),
    ('phone', 'Phone'),
    ('sms', 'SMS'),
]

class EmergencyContact(models.Model):
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    pet = models.ForeignKey('pets.Pet', on_delete=models.SET_NULL, null=True, blank=True)

    phone = models.CharField(max_length=20)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)

    reported_symptoms = models.TextField()
    pet_species = models.CharField(max_length=50)
    pet_age = models.CharField(max_length=50, blank=True)

    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, null=True)
    triage_notes = models.TextField(blank=True)
    ai_assessment = models.JSONField(default=dict)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='initiated')

    handled_by = models.ForeignKey('practice.StaffProfile', on_delete=models.SET_NULL, null=True)
    response_time_seconds = models.IntegerField(null=True, blank=True)

    resolution = models.TextField(blank=True)
    outcome = models.CharField(max_length=50, blank=True)

    appointment = models.ForeignKey('appointments.Appointment', on_delete=models.SET_NULL, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    escalated_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `channel` | CharField | Contact channel (web, WhatsApp, phone, SMS) |
| `reported_symptoms` | TextField | Description of symptoms |
| `ai_assessment` | JSONField | AI-generated triage assessment |
| `response_time_seconds` | IntegerField | Time to staff response |
| `handled_by` | ForeignKey | Staff member who handled |
| `appointment` | ForeignKey | Resulting appointment if any |

### OnCallSchedule

After-hours on-call staff scheduling.

```python
class OnCallSchedule(models.Model):
    staff = models.ForeignKey('practice.StaffProfile', on_delete=models.CASCADE)

    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    contact_phone = models.CharField(max_length=20)
    backup_phone = models.CharField(max_length=20, blank=True)

    is_active = models.BooleanField(default=True)
    swap_requested = models.BooleanField(default=False)
    swap_with = models.ForeignKey('practice.StaffProfile', on_delete=models.SET_NULL, null=True)

    notes = models.TextField(blank=True)
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `date` | DateField | On-call date |
| `start_time` / `end_time` | TimeField | On-call hours |
| `contact_phone` | CharField | Primary contact number |
| `backup_phone` | CharField | Backup contact number |
| `swap_requested` | Boolean | Whether swap is requested |
| `swap_with` | ForeignKey | Staff to swap with |

### EmergencyReferral

Directory of emergency hospitals and 24-hour facilities.

```python
class EmergencyReferral(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    whatsapp = models.CharField(max_length=20, blank=True)

    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    distance_km = models.FloatField(null=True, blank=True)

    is_24_hours = models.BooleanField(default=False)
    hours = models.JSONField(default=dict)

    services = models.JSONField(default=list)
    species_treated = models.JSONField(default=list)

    is_active = models.BooleanField(default=True)
    last_verified = models.DateField(null=True, blank=True)

    notes = models.TextField(blank=True)
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `latitude` / `longitude` | DecimalField | GPS coordinates |
| `distance_km` | FloatField | Distance from clinic |
| `is_24_hours` | Boolean | 24-hour availability |
| `hours` | JSONField | Operating hours by day |
| `services` | JSONField | Available services |
| `species_treated` | JSONField | Species they handle |
| `last_verified` | DateField | Last info verification date |

### EmergencyFirstAid

First aid instructions for common emergencies.

```python
class EmergencyFirstAid(models.Model):
    title = models.CharField(max_length=200)
    title_es = models.CharField(max_length=200)

    condition = models.CharField(max_length=100)
    species = models.JSONField(default=list)

    description = models.TextField()
    description_es = models.TextField()

    steps = models.JSONField(default=list)
    warnings = models.JSONField(default=list)
    do_not = models.JSONField(default=list)  # Things NOT to do

    video_url = models.URLField(blank=True)
    images = models.JSONField(default=list)

    related_symptoms = models.ManyToManyField(EmergencySymptom, blank=True)

    is_active = models.BooleanField(default=True)
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `title` / `title_es` | CharField | Bilingual titles |
| `condition` | CharField | Medical condition |
| `steps` | JSONField | Step-by-step instructions |
| `warnings` | JSONField | Warning signs |
| `do_not` | JSONField | Things to avoid doing |
| `video_url` | URLField | Instructional video |
| `related_symptoms` | M2M | Link to symptom database |

## Views

Location: `apps/emergency/views.py`

### emergency_home

Emergency landing page with quick access to all resources.

```python
def emergency_home(request):
    """Emergency landing page with quick access to all emergency resources."""
    return render(request, 'emergency/home.html')
```

### triage_form / triage_result

Self-triage assessment flow.

```python
def triage_form(request):
    """Self-triage form - describe symptoms to assess severity."""
    if request.method == 'POST':
        species = request.POST.get('species', '')
        symptoms_text = request.POST.get('symptoms', '')

        # Keyword matching for triage
        matched_symptoms = []
        for symptom in EmergencySymptom.objects.filter(is_active=True):
            if symptom.keyword.lower() in symptoms_text.lower():
                matched_symptoms.append(symptom)
            # Also check Spanish/English keyword variants

        # Determine severity from matched symptoms
        # Store result in session for result page
        request.session['triage_result'] = {...}
        return redirect('emergency:triage_result')

def triage_result(request):
    """Display triage assessment result with severity and recommendations."""
    result = request.session.get('triage_result')
    # Show severity-appropriate guidance and nearby hospitals
```

### first_aid_list / first_aid_detail

First aid guide browsing.

```python
def first_aid_list(request):
    """List of first aid guides for common emergencies."""
    guides = EmergencyFirstAid.objects.filter(is_active=True)
    # Optional species filter

def first_aid_detail(request, pk):
    """Detailed first aid instructions."""
    guide = get_object_or_404(EmergencyFirstAid, pk=pk, is_active=True)
```

### hospital_list

Emergency hospital directory.

```python
def hospital_list(request):
    """List of emergency hospitals and referral centers."""
    hospitals = EmergencyReferral.objects.filter(is_active=True)
    # Optional 24-hour filter
```

### emergency_contact / contact_success

Submit emergency contact request.

```python
def emergency_contact(request):
    """Submit emergency contact request."""
    if request.method == 'POST':
        contact = EmergencyContact.objects.create(
            owner=request.user if authenticated else None,
            phone=request.POST.get('phone'),
            channel=request.POST.get('channel', 'web'),
            reported_symptoms=request.POST.get('symptoms'),
            pet_species=request.POST.get('species'),
            status='initiated',
        )
        return redirect('emergency:contact_success')
```

### emergency_history

View past emergency contacts (authenticated users).

```python
@login_required
def emergency_history(request):
    """View past emergency contacts for authenticated user."""
    contacts = EmergencyContact.objects.filter(owner=request.user)
```

## URL Patterns

Location: `apps/emergency/urls.py`

```python
app_name = 'emergency'

urlpatterns = [
    # Emergency home
    path('', views.emergency_home, name='home'),

    # Self-triage
    path('triage/', views.triage_form, name='triage'),
    path('triage/result/', views.triage_result, name='triage_result'),

    # First aid guides
    path('first-aid/', views.first_aid_list, name='first_aid_list'),
    path('first-aid/<int:pk>/', views.first_aid_detail, name='first_aid_detail'),

    # Hospital directory
    path('hospitals/', views.hospital_list, name='hospitals'),

    # Emergency contact
    path('contact/', views.emergency_contact, name='contact'),
    path('contact/success/', views.contact_success, name='contact_success'),

    # History (authenticated)
    path('history/', views.emergency_history, name='history'),
]
```

## Workflows

### Self-Triage Assessment

```python
from apps.emergency.models import EmergencySymptom

# Step 1: User enters symptoms
symptoms_text = "My dog is bleeding from the nose and won't eat"
species = "dog"

# Step 2: Match against symptom database
matched = []
for symptom in EmergencySymptom.objects.filter(is_active=True):
    # Check main keyword
    if symptom.keyword.lower() in symptoms_text.lower():
        matched.append(symptom)
    # Check Spanish keywords
    for kw in symptom.keywords_es:
        if kw.lower() in symptoms_text.lower():
            matched.append(symptom)
            break
    # Check English keywords
    for kw in symptom.keywords_en:
        if kw.lower() in symptoms_text.lower():
            matched.append(symptom)
            break

# Step 3: Determine severity (highest severity wins)
severities = [s.severity for s in matched]
if 'critical' in severities:
    severity = 'critical'
elif 'urgent' in severities:
    severity = 'urgent'
elif 'moderate' in severities:
    severity = 'moderate'
else:
    severity = 'low'

# Step 4: Collect first aid tips
first_aid_tips = []
for symptom in matched:
    if symptom.first_aid_instructions:
        first_aid_tips.append({
            'symptom': symptom.keyword,
            'instructions': symptom.first_aid_instructions,
            'warning_signs': symptom.warning_signs,
        })
```

### Emergency Contact Submission

```python
from apps.emergency.models import EmergencyContact
from django.utils import timezone

# Create emergency contact
contact = EmergencyContact.objects.create(
    owner=user,  # None for anonymous
    pet=pet,  # Optional
    phone='55-1234-5678',
    channel='whatsapp',
    reported_symptoms='Dog ate chocolate, vomiting',
    pet_species='dog',
    pet_age='3 years',
    status='initiated',
)

# Staff picks up the case
contact.status = 'triaging'
contact.handled_by = staff_profile
contact.save()

# Add triage assessment
contact.severity = 'urgent'
contact.triage_notes = 'Chocolate toxicity suspected. Amount and type unknown.'
contact.ai_assessment = {
    'toxicity_risk': 'moderate',
    'recommended_action': 'induce_vomiting',
    'urgency': 'within_2_hours',
}
contact.save()

# Escalate to veterinarian
contact.status = 'escalated'
contact.escalated_at = timezone.now()
contact.save()

# Resolve with outcome
contact.status = 'resolved'
contact.resolved_at = timezone.now()
contact.resolution = 'Owner brought dog in. Induced vomiting, activated charcoal given.'
contact.outcome = 'recovered'
contact.response_time_seconds = (contact.resolved_at - contact.created_at).seconds
contact.save()
```

### On-Call Staff Management

```python
from apps.emergency.models import OnCallSchedule
from datetime import date, time

# Create on-call schedule
oncall = OnCallSchedule.objects.create(
    staff=vet_profile,
    date=date(2025, 12, 25),
    start_time=time(18, 0),  # 6 PM
    end_time=time(8, 0),     # 8 AM next day
    contact_phone='55-1234-5678',
    backup_phone='55-8765-4321',
    is_active=True,
    notes='Christmas evening shift',
)

# Request shift swap
oncall.swap_requested = True
oncall.swap_with = other_vet_profile
oncall.save()

# Find who's on call now
from datetime import datetime
now = datetime.now()
current_oncall = OnCallSchedule.objects.filter(
    date=now.date(),
    start_time__lte=now.time(),
    end_time__gte=now.time(),
    is_active=True,
).first()
```

### First Aid Resources

```python
from apps.emergency.models import EmergencyFirstAid, EmergencySymptom

# Create first aid guide
guide = EmergencyFirstAid.objects.create(
    title='Choking',
    title_es='Asfixia',
    condition='choking',
    species=['dog', 'cat'],
    description='What to do when your pet is choking',
    description_es='Qué hacer cuando su mascota se está asfixiando',
    steps=[
        'Stay calm and restrain your pet gently',
        'Open the mouth and look for the object',
        'If visible, try to remove with fingers or tweezers',
        'If not visible, perform modified Heimlich maneuver',
        'Seek veterinary care immediately',
    ],
    warnings=[
        'Pet may bite when panicked',
        'Do not push object further down',
    ],
    do_not=[
        'Do not perform CPR if pet is conscious',
        'Do not leave pet unattended',
    ],
    video_url='https://example.com/choking-video',
)

# Link to symptoms
choking_symptom = EmergencySymptom.objects.get(keyword='choking')
guide.related_symptoms.add(choking_symptom)
```

## Severity Levels

| Level | Description | Response Time | Action |
|-------|-------------|---------------|--------|
| `critical` | Life-threatening emergency | Immediate | Go to 24-hour hospital NOW |
| `urgent` | Needs same-day care | Within hours | Emergency appointment |
| `moderate` | Can wait 1-2 days | Schedule soon | Regular appointment |
| `low` | Non-urgent | Schedule when convenient | Routine check-up |

### Severity UI Indicators

```python
severity_info = {
    'critical': {
        'class': 'bg-red-100 text-red-800 border-red-500',
        'icon': '🚨',
        'title': 'Critical Emergency',
        'message': 'Seek immediate veterinary care.',
    },
    'urgent': {
        'class': 'bg-orange-100 text-orange-800 border-orange-500',
        'icon': '⚠️',
        'title': 'Urgent Care Needed',
        'message': 'Your pet needs attention today.',
    },
    'moderate': {
        'class': 'bg-yellow-100 text-yellow-800 border-yellow-500',
        'icon': '📋',
        'title': 'Monitor & Schedule',
        'message': 'Schedule an appointment soon.',
    },
    'low': {
        'class': 'bg-green-100 text-green-800 border-green-500',
        'icon': '✓',
        'title': 'Low Concern',
        'message': 'Schedule if symptoms persist.',
    },
}
```

## Triage Algorithm

The self-triage system uses keyword matching:

```
1. User enters free-text symptoms
2. System matches against EmergencySymptom database:
   - Primary keyword (exact match)
   - Spanish keywords (keywords_es)
   - English keywords (keywords_en)
3. All matched symptoms collected
4. Highest severity among matches determines result:
   critical > urgent > moderate > low
5. First aid tips aggregated from matched symptoms
6. Nearby 24-hour hospitals shown for critical/urgent
```

### Symptom Database Example

```python
# Critical symptom
EmergencySymptom.objects.create(
    keyword='not breathing',
    keywords_es=['no respira', 'sin respiracion'],
    keywords_en=['cant breathe', 'stopped breathing'],
    species=['dog', 'cat', 'bird', 'rabbit'],
    severity='critical',
    description='Pet is not breathing or having severe difficulty',
    first_aid_instructions='Clear airway. Begin pet CPR if trained.',
    warning_signs='Blue gums, unconsciousness, no pulse',
)

# Urgent symptom
EmergencySymptom.objects.create(
    keyword='bleeding',
    keywords_es=['sangrado', 'sangrando', 'hemorragia'],
    keywords_en=['blood', 'bleeding heavily'],
    species=['dog', 'cat'],
    severity='urgent',
    description='Active bleeding that won\'t stop',
    first_aid_instructions='Apply direct pressure with clean cloth.',
    warning_signs='Pale gums, weakness, rapid breathing',
)
```

## Integration Points

### With Pets Module

```python
from apps.emergency.models import EmergencyContact
from apps.pets.models import Pet

# Link emergency contact to pet
pet = Pet.objects.get(pk=pet_id)
contact = EmergencyContact.objects.create(
    owner=pet.owner,
    pet=pet,
    pet_species=pet.species,
    pet_age=f"{pet.age_years} years",
    reported_symptoms='...',
    ...
)

# Get pet's emergency history
emergency_history = pet.emergency_contacts.order_by('-created_at')
```

### With Appointments Module

```python
from apps.emergency.models import EmergencyContact
from apps.appointments.models import Appointment

# Emergency leads to appointment
contact = EmergencyContact.objects.get(pk=contact_id)
appointment = Appointment.objects.create(
    pet=contact.pet,
    owner=contact.owner,
    service_type=emergency_service,
    date=today,
    notes=f"Emergency: {contact.reported_symptoms}",
)

# Link appointment to contact
contact.appointment = appointment
contact.status = 'resolved'
contact.save()
```

### With Practice Module

```python
from apps.emergency.models import OnCallSchedule, EmergencyContact
from apps.practice.models import StaffProfile

# Get today's on-call vet
oncall = OnCallSchedule.objects.filter(
    date=today,
    is_active=True,
).first()
vet_on_call = oncall.staff if oncall else None

# Assign emergency to on-call vet
contact.handled_by = vet_on_call
contact.save()

# Get staff's handled emergencies
staff = StaffProfile.objects.get(pk=staff_id)
handled = staff.emergency_contacts_handled.count()
```

### With Notifications Module

```python
from apps.notifications.services import NotificationService
from apps.emergency.models import EmergencyContact

# Alert on-call staff of new emergency
contact = EmergencyContact.objects.create(...)

NotificationService.send_emergency_alert(
    to=oncall_staff,
    contact=contact,
    message=f"URGENT: {contact.pet_species} - {contact.reported_symptoms[:50]}",
)
```

## Query Examples

### Emergency Contact Queries

```python
from apps.emergency.models import EmergencyContact
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import timedelta

# Pending emergencies (need attention)
pending = EmergencyContact.objects.filter(
    status__in=['initiated', 'triaging']
).order_by('created_at')

# Critical emergencies today
critical_today = EmergencyContact.objects.filter(
    severity='critical',
    created_at__date=timezone.now().date()
)

# Average response time
avg_response = EmergencyContact.objects.filter(
    response_time_seconds__isnull=False
).aggregate(avg=Avg('response_time_seconds'))

# Emergencies by channel
by_channel = EmergencyContact.objects.values('channel').annotate(
    count=Count('id')
).order_by('-count')

# Unresolved emergencies older than 1 hour
stale = EmergencyContact.objects.filter(
    status__in=['initiated', 'triaging'],
    created_at__lt=timezone.now() - timedelta(hours=1)
)
```

### Symptom Queries

```python
from apps.emergency.models import EmergencySymptom

# Active critical symptoms
critical = EmergencySymptom.objects.filter(
    is_active=True,
    severity='critical'
)

# Symptoms for dogs
dog_symptoms = EmergencySymptom.objects.filter(
    is_active=True,
    species__contains='dog'
)

# Search symptoms by keyword
query = 'vomit'
matches = EmergencySymptom.objects.filter(
    is_active=True
).filter(
    models.Q(keyword__icontains=query) |
    models.Q(keywords_es__icontains=query) |
    models.Q(keywords_en__icontains=query)
)
```

### On-Call Schedule Queries

```python
from apps.emergency.models import OnCallSchedule
from datetime import date, time, datetime

# Who's on call today?
today_oncall = OnCallSchedule.objects.filter(
    date=date.today(),
    is_active=True
)

# Pending swap requests
swap_requests = OnCallSchedule.objects.filter(
    swap_requested=True,
    date__gte=date.today()
).select_related('staff', 'swap_with')

# Staff's upcoming on-call shifts
staff_shifts = OnCallSchedule.objects.filter(
    staff=staff_profile,
    date__gte=date.today(),
    is_active=True
).order_by('date')

# Find current on-call (considers time)
now = datetime.now()
current = OnCallSchedule.objects.filter(
    date=now.date(),
    start_time__lte=now.time(),
    is_active=True
).first()
```

### Hospital Queries

```python
from apps.emergency.models import EmergencyReferral

# 24-hour hospitals
always_open = EmergencyReferral.objects.filter(
    is_active=True,
    is_24_hours=True
)

# Nearest hospitals
nearest = EmergencyReferral.objects.filter(
    is_active=True,
    distance_km__isnull=False
).order_by('distance_km')[:5]

# Hospitals treating specific species
exotic_hospitals = EmergencyReferral.objects.filter(
    is_active=True,
    species_treated__contains='bird'
)

# Recently verified hospitals
from datetime import timedelta
recent = EmergencyReferral.objects.filter(
    is_active=True,
    last_verified__gte=date.today() - timedelta(days=90)
)
```

### First Aid Guide Queries

```python
from apps.emergency.models import EmergencyFirstAid

# All active guides
guides = EmergencyFirstAid.objects.filter(is_active=True)

# Guides for cats
cat_guides = [g for g in guides if 'cat' in g.species]

# Guides with videos
with_video = EmergencyFirstAid.objects.filter(
    is_active=True
).exclude(video_url='')

# Guides related to a symptom
symptom = EmergencySymptom.objects.get(keyword='choking')
related_guides = symptom.first_aid_guides.filter(is_active=True)
```

## Testing

### Unit Tests

Location: `tests/test_emergency.py`

```bash
# Run emergency unit tests
python -m pytest tests/test_emergency.py -v
```

### Browser Tests

Location: `tests/e2e/browser/test_emergency.py`

```bash
# Run emergency browser tests
python -m pytest tests/e2e/browser/test_emergency.py -v

# Run with visible browser
python -m pytest tests/e2e/browser/test_emergency.py -v --headed --slowmo=500
```

### Key Test Scenarios

1. **Self-Triage Flow**
   - Submit symptoms
   - Verify severity detection
   - Check first aid tips displayed
   - Verify hospital recommendations

2. **Emergency Contact**
   - Submit contact request
   - Verify record creation
   - Test authenticated vs anonymous
   - Check success page

3. **First Aid Guides**
   - List all guides
   - Filter by species
   - View detailed guide
   - Check bilingual content

4. **Hospital Directory**
   - List all hospitals
   - Filter 24-hour only
   - View hospital details
   - Verify GPS coordinates

5. **Contact History**
   - View past contacts
   - Verify user isolation
   - Check status display
