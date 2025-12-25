# Referrals Module

The `apps.referrals` module manages specialist referrals and visiting veterinarians for the veterinary clinic, enabling coordination with external specialists and tracking patient outcomes.

## Table of Contents

- [Overview](#overview)
- [Models](#models)
  - [Specialist](#specialist)
  - [VisitingSchedule](#visitingschedule)
  - [Referral](#referral)
  - [ReferralDocument](#referraldocument)
  - [ReferralNote](#referralnote)
  - [VisitingAppointment](#visitingappointment)
- [Views](#views)
- [URL Patterns](#url-patterns)
- [Workflows](#workflows)
  - [Outbound Referral Flow](#outbound-referral-flow)
  - [Inbound Referral Flow](#inbound-referral-flow)
  - [Visiting Specialist Flow](#visiting-specialist-flow)
- [Specialties](#specialties)
- [Integration Points](#integration-points)
- [Query Examples](#query-examples)
- [Testing](#testing)

## Overview

The referrals module handles:

- **Specialist Directory** - Database of external specialists and facilities
- **Outbound Referrals** - Sending patients to specialists
- **Inbound Referrals** - Receiving patients from other vets
- **Visiting Specialists** - Specialists who visit the clinic
- **Document Management** - Medical records, reports, imaging
- **Outcome Tracking** - Follow-up and treatment results

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Pet-Friendly │────▶│    Referral     │────▶│   Specialist    │
│   (Your Clinic) │     │   (tracking)    │     │   (external)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        │                       ▼                       │
        │              ┌─────────────────┐              │
        │              │   Documents &   │              │
        │              │     Notes       │              │
        │              └─────────────────┘              │
        │                                               │
        └───────────────────────────────────────────────┘
                    (Specialist Reports Back)
```

## Models

### Specialist

Location: `apps/referrals/models.py`

Directory of specialist veterinarians and facilities.

```python
class Specialist(models.Model):
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

    RELATIONSHIP_STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending'),
    ]

    # Basic info
    name = models.CharField(max_length=200)
    specialty = models.CharField(max_length=50, choices=SPECIALIST_TYPES)
    credentials = models.CharField(max_length=200, blank=True)

    # Individual or facility
    is_facility = models.BooleanField(default=False)
    clinic_name = models.CharField(max_length=200, blank=True)

    # Contact
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20)
    fax = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)

    # Location
    address = models.TextField()
    city = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True)
    distance_km = models.FloatField(null=True, blank=True)

    # Hours
    is_24_hours = models.BooleanField(default=False)
    hours = models.JSONField(default=dict)  # {"mon": "9-5", "tue": "9-5", ...}

    # Services
    services = models.JSONField(default=list)
    species_treated = models.JSONField(default=list)

    # Visiting specialist info
    is_visiting = models.BooleanField(default=False)
    visiting_services = models.JSONField(default=list)
    equipment_provided = models.JSONField(default=list)

    # Relationship
    relationship_status = models.CharField(max_length=20, default='active')
    referral_agreement = models.TextField(blank=True)
    revenue_share_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True)

    # Stats
    total_referrals_sent = models.IntegerField(default=0)
    total_referrals_received = models.IntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True)

    # Notes
    notes = models.TextField(blank=True)
    referral_instructions = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `specialty` | CharField | Medical specialty (oncology, cardiology, etc.) |
| `is_facility` | Boolean | True if facility, False if individual vet |
| `is_visiting` | Boolean | True if specialist visits your clinic |
| `is_24_hours` | Boolean | Emergency availability |
| `relationship_status` | CharField | Status of referral partnership |
| `revenue_share_percent` | Decimal | For visiting specialists |

### VisitingSchedule

Schedule for visiting specialists at your clinic.

```python
class VisitingSchedule(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    specialist = models.ForeignKey(Specialist, on_delete=models.CASCADE,
                                   related_name='visiting_schedules')

    # When
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    # Recurring
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(max_length=50, blank=True)

    # Capacity
    max_appointments = models.IntegerField(null=True, blank=True)
    appointments_booked = models.IntegerField(default=0)

    # Services available this visit
    services_available = models.JSONField(default=list)

    # Equipment
    equipment_bringing = models.JSONField(default=list)

    # Status
    status = models.CharField(max_length=20, default='scheduled')
    cancellation_reason = models.TextField(blank=True)

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Referral

Main referral tracking model for outbound and inbound referrals.

```python
class Referral(models.Model):
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

    OUTCOME_CHOICES = [
        ('successful', 'Successful Treatment'),
        ('ongoing', 'Ongoing Treatment'),
        ('referred_again', 'Referred to Another Specialist'),
        ('no_treatment', 'No Treatment Possible'),
        ('client_declined', 'Client Declined Treatment'),
        ('euthanasia', 'Euthanasia'),
        ('unknown', 'Unknown'),
    ]

    # Direction
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    referral_number = models.CharField(max_length=50, unique=True)

    # Patient
    pet = models.ForeignKey('pets.Pet', on_delete=models.CASCADE,
                            related_name='specialist_referrals')
    owner = models.ForeignKey(User, on_delete=models.CASCADE,
                              related_name='pet_referrals')

    # Specialist (for outbound)
    specialist = models.ForeignKey(Specialist, on_delete=models.SET_NULL,
                                   null=True, related_name='referrals_received')

    # For inbound referrals
    referring_vet_name = models.CharField(max_length=200, blank=True)
    referring_clinic = models.CharField(max_length=200, blank=True)
    referring_contact = models.CharField(max_length=200, blank=True)
    referring_professional_account = models.ForeignKey('billing.ProfessionalAccount',
                                                       on_delete=models.SET_NULL, null=True)

    # Reason
    reason = models.TextField()
    clinical_summary = models.TextField(blank=True)
    urgency = models.CharField(max_length=20, default='routine')
    requested_services = models.JSONField(default=list)

    # Status
    status = models.CharField(max_length=20, default='draft')

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
    outcome = models.CharField(max_length=20, blank=True)
    outcome_notes = models.TextField(blank=True)

    # Feedback
    client_satisfaction = models.IntegerField(null=True, blank=True)  # 1-5
    quality_rating = models.IntegerField(null=True, blank=True)  # 1-5

    # Staff
    referred_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                    null=True, related_name='referrals_created')

    # Billing
    invoice = models.ForeignKey('billing.Invoice', on_delete=models.SET_NULL,
                                null=True, blank=True)

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Referral Number Generation:**

```python
def _generate_referral_number(self):
    """Generate unique referral number: YYYY-XXXXXX"""
    year = timezone.now().year
    random_part = uuid.uuid4().hex[:6].upper()
    return f"{year}-{random_part}"
```

### ReferralDocument

Documents attached to referrals.

```python
class ReferralDocument(models.Model):
    DOCUMENT_TYPES = [
        ('referral_letter', 'Referral Letter'),
        ('medical_history', 'Medical History'),
        ('lab_results', 'Lab Results'),
        ('imaging', 'Imaging (X-ray, Ultrasound)'),
        ('specialist_report', 'Specialist Report'),
        ('prescription', 'Prescription'),
        ('other', 'Other'),
    ]

    referral = models.ForeignKey(Referral, on_delete=models.CASCADE,
                                 related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='referrals/')
    description = models.TextField(blank=True)

    is_outgoing = models.BooleanField(default=True)  # True = sent, False = received

    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
```

### ReferralNote

Communication notes on referrals.

```python
class ReferralNote(models.Model):
    referral = models.ForeignKey(Referral, on_delete=models.CASCADE,
                                 related_name='notes_list')
    note = models.TextField()
    is_internal = models.BooleanField(default=True)  # Internal vs shared with specialist

    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### VisitingAppointment

Appointments with visiting specialists.

```python
class VisitingAppointment(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked In'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('no_show', 'No Show'),
        ('cancelled', 'Cancelled'),
    ]

    schedule = models.ForeignKey(VisitingSchedule, on_delete=models.CASCADE,
                                 related_name='appointments')
    specialist = models.ForeignKey(Specialist, on_delete=models.CASCADE)

    pet = models.ForeignKey('pets.Pet', on_delete=models.CASCADE,
                            related_name='visiting_appointments')
    owner = models.ForeignKey(User, on_delete=models.CASCADE,
                              related_name='visiting_appointments')

    # Time slot
    appointment_time = models.TimeField()
    duration_minutes = models.IntegerField(default=30)

    # Service
    service = models.CharField(max_length=100)
    reason = models.TextField()

    # Status
    status = models.CharField(max_length=20, default='scheduled')

    # Results
    findings = models.TextField(blank=True)
    diagnosis = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)

    # Documents
    report_file = models.FileField(upload_to='visiting_reports/', null=True)
    images = models.JSONField(default=list)

    # Billing
    fee = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    pet_friendly_share = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    invoice = models.ForeignKey('billing.Invoice', on_delete=models.SET_NULL,
                                null=True, blank=True)

    # Follow-up
    follow_up_needed = models.BooleanField(default=False)
    follow_up_notes = models.TextField(blank=True)

    # Related referral (if from referral workflow)
    referral = models.ForeignKey(Referral, on_delete=models.SET_NULL,
                                 null=True, blank=True)

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

## Views

Location: `apps/referrals/views.py`

All views require staff member access (`@staff_member_required`).

### Dashboard

Main referrals dashboard with summary statistics.

```python
@staff_member_required
def dashboard(request):
    """Referral network dashboard."""
    context = {
        'active_specialists': Specialist.objects.filter(
            is_active=True, relationship_status='active'
        ).count(),
        'pending_referrals': Referral.objects.filter(
            status__in=['draft', 'sent', 'received']
        ).count(),
        'upcoming_visits': VisitingSchedule.objects.filter(
            date__gte=date.today(),
            status__in=['scheduled', 'confirmed']
        ).count(),
        'completed_this_month': Referral.objects.filter(
            status='completed',
            completed_at__month=date.today().month,
            completed_at__year=date.today().year
        ).count(),
        'recent_referrals': Referral.objects.select_related(
            'pet', 'owner', 'specialist'
        ).order_by('-created_at')[:5],
        'upcoming_schedules': VisitingSchedule.objects.filter(
            date__gte=date.today(),
            status__in=['scheduled', 'confirmed']
        ).select_related('specialist').order_by('date', 'start_time')[:5],
    }
    return render(request, 'referrals/dashboard.html', context)
```

### Specialist Views

```python
@staff_member_required
def specialist_list(request):
    """List all specialists with filtering."""
    # Filters: specialty, visiting (yes/no)

@staff_member_required
def specialist_detail(request, pk):
    """View specialist details, recent referrals, upcoming visits."""
```

### Referral Views

```python
@staff_member_required
def referral_list(request):
    """List referrals with status/direction filters."""

@staff_member_required
def referral_detail(request, pk):
    """View referral with documents and notes."""
```

### Visiting Schedule Views

```python
@staff_member_required
def visiting_schedule(request):
    """View visiting specialist schedules."""
    # Periods: today, week, upcoming, past

@staff_member_required
def visiting_detail(request, pk):
    """View schedule details with appointments."""
```

## URL Patterns

Location: `apps/referrals/urls.py`

```python
app_name = 'referrals'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Specialists Directory
    path('specialists/', views.specialist_list, name='specialist_list'),
    path('specialists/<int:pk>/', views.specialist_detail, name='specialist_detail'),

    # Referrals
    path('outbound/', views.referral_list, name='referral_list'),
    path('outbound/<int:pk>/', views.referral_detail, name='referral_detail'),

    # Visiting Specialists
    path('visiting/', views.visiting_schedule, name='visiting_schedule'),
    path('visiting/<int:pk>/', views.visiting_detail, name='visiting_detail'),
]
```

## Workflows

### Outbound Referral Flow

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  DRAFT  │───▶│  SENT   │───▶│RECEIVED │───▶│SCHEDULED│
└─────────┘    └─────────┘    └─────────┘    └─────────┘
                                                   │
                                                   ▼
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│COMPLETED│◀───│ REPORT  │◀───│  SEEN   │◀───│         │
│         │    │ PENDING │    │         │    │         │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
```

**Status Transitions:**

| From | To | Trigger |
|------|-----|---------|
| draft | sent | Referral sent to specialist |
| sent | received | Specialist acknowledges receipt |
| received | scheduled | Appointment scheduled |
| scheduled | seen | Patient seen by specialist |
| seen | report_pending | Awaiting specialist report |
| report_pending | completed | Report received, outcome recorded |
| any | cancelled | Referral cancelled |
| any | declined | Specialist declines referral |

**Creating an Outbound Referral:**

```python
from apps.referrals.models import Referral, ReferralDocument

# Create referral
referral = Referral.objects.create(
    direction='outbound',
    pet=pet,
    owner=pet.owner,
    specialist=specialist,
    reason="Suspected cardiac arrhythmia. ECG shows irregular rhythm.",
    clinical_summary="3yo Labrador, occasional syncope episodes...",
    urgency='urgent',
    requested_services=['echocardiogram', 'holter_monitor'],
    referred_by=request.user,
    status='draft',
)

# Attach medical history
ReferralDocument.objects.create(
    referral=referral,
    document_type='medical_history',
    title='Complete Medical History',
    file=medical_history_file,
    is_outgoing=True,
    uploaded_by=request.user,
)

# Send referral
referral.status = 'sent'
referral.sent_at = timezone.now()
referral.save()
```

### Inbound Referral Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  RECEIVED   │───▶│  SCHEDULED  │───▶│    SEEN     │
│ (from vet)  │    │(appointment)│    │ (treated)   │
└─────────────┘    └─────────────┘    └─────────────┘
                                             │
                                             ▼
                                      ┌─────────────┐
                                      │  COMPLETED  │
                                      │(report sent)│
                                      └─────────────┘
```

**Creating an Inbound Referral:**

```python
# Inbound referral from another vet
referral = Referral.objects.create(
    direction='inbound',
    pet=pet,
    owner=pet.owner,
    referring_vet_name='Dr. Martinez',
    referring_clinic='Clinica Veterinaria Centro',
    referring_contact='555-1234',
    reason="Second opinion on mass in abdomen",
    clinical_summary="5yo mixed breed, abdominal mass detected...",
    urgency='routine',
    status='received',
)

# Link to professional account for billing
if pro_account := ProfessionalAccount.objects.filter(
    business_name__icontains='Centro'
).first():
    referral.referring_professional_account = pro_account
    referral.save()
```

### Visiting Specialist Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  SCHEDULE   │───▶│   CONFIRM   │───▶│   VISIT     │
│  (create)   │    │   (verify)  │    │   (day of)  │
└─────────────┘    └─────────────┘    └─────────────┘
                                             │
        ┌────────────────────────────────────┘
        ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    BOOK     │───▶│   CONSULT   │───▶│   BILL      │
│(appointments)│   │  (perform)  │    │ (invoice)   │
└─────────────┘    └─────────────┘    └─────────────┘
```

**Scheduling a Visiting Specialist:**

```python
from apps.referrals.models import Specialist, VisitingSchedule, VisitingAppointment

# Get visiting specialist
cardiologist = Specialist.objects.get(
    specialty='cardiology',
    is_visiting=True,
    is_active=True
)

# Create schedule
schedule = VisitingSchedule.objects.create(
    specialist=cardiologist,
    date=date(2024, 2, 15),
    start_time=time(9, 0),
    end_time=time(17, 0),
    max_appointments=8,
    services_available=['echocardiogram', 'ECG', 'cardiac_consultation'],
    equipment_bringing=['portable_ultrasound', 'ECG_machine'],
    status='scheduled',
)

# Book an appointment
appointment = VisitingAppointment.objects.create(
    schedule=schedule,
    specialist=cardiologist,
    pet=pet,
    owner=pet.owner,
    appointment_time=time(10, 30),
    duration_minutes=45,
    service='echocardiogram',
    reason='Follow-up cardiac evaluation',
    status='scheduled',
)

# Update schedule capacity
schedule.appointments_booked += 1
schedule.save()
```

## Specialties

Available specialist types:

| Code | Specialty | Common Services |
|------|-----------|-----------------|
| `oncology` | Oncology | Chemotherapy, tumor surgery, radiation |
| `cardiology` | Cardiology | Echocardiogram, ECG, pacemakers |
| `orthopedics` | Orthopedics | Joint surgery, fracture repair, TPLO |
| `ophthalmology` | Ophthalmology | Cataract surgery, eye exams |
| `dermatology` | Dermatology | Allergy testing, skin biopsies |
| `neurology` | Neurology | MRI, seizure management, spine surgery |
| `surgery` | Surgery | Soft tissue, emergency surgery |
| `internal_medicine` | Internal Medicine | Endoscopy, complex diagnostics |
| `emergency` | Emergency/Critical Care | 24/7 emergency care |
| `imaging` | Imaging/Radiology | CT, MRI, ultrasound |
| `laboratory` | Laboratory | Specialized diagnostics |
| `rehabilitation` | Rehabilitation | Physical therapy, hydrotherapy |
| `behavior` | Behavior | Behavioral consultations |
| `exotics` | Exotic Animals | Birds, reptiles, pocket pets |
| `dentistry` | Dentistry | Root canals, extractions, cleanings |

## Integration Points

### With Pets Module

```python
from apps.pets.models import Pet
from apps.referrals.models import Referral

# Get all referrals for a pet
pet = Pet.objects.get(pk=pet_id)
referrals = pet.specialist_referrals.all()

# Emergency referral for pet
emergency_referral = Referral.objects.create(
    direction='outbound',
    pet=pet,
    owner=pet.owner,
    specialist=emergency_specialist,
    reason="Hit by car, suspected internal injuries",
    urgency='emergency',
    status='sent',
    sent_at=timezone.now(),
)
```

### With Billing Module

```python
from apps.billing.services import InvoiceService
from apps.referrals.models import VisitingAppointment

# Bill for visiting specialist appointment
appointment = VisitingAppointment.objects.get(pk=appointment_id)
appointment.status = 'completed'
appointment.fee = Decimal('1500.00')

# Calculate clinic's share (revenue sharing)
if appointment.specialist.revenue_share_percent:
    share = appointment.fee * (appointment.specialist.revenue_share_percent / 100)
    appointment.pet_friendly_share = appointment.fee - share
else:
    appointment.pet_friendly_share = appointment.fee

appointment.save()

# Create invoice
# (Would typically use InvoiceService)
```

### With Audit Module

Referral pages are automatically logged by AuditMiddleware:

| Path | Resource Type | Sensitivity |
|------|---------------|-------------|
| `/referrals/` | `referrals.dashboard` | normal |
| `/referrals/specialists/` | `referrals.specialist` | normal |
| `/referrals/outbound/` | `referrals.referral` | **high** |
| `/referrals/outbound/<id>/` | `referrals.referral` | **high** |
| `/referrals/visiting/` | `referrals.visiting` | normal |

## Query Examples

### Specialist Queries

```python
from apps.referrals.models import Specialist

# Find cardiologists
cardiologists = Specialist.objects.filter(
    specialty='cardiology',
    is_active=True,
    relationship_status='active'
)

# Find visiting specialists
visiting = Specialist.objects.filter(
    is_visiting=True,
    is_active=True
)

# Find 24-hour emergency facilities
emergency = Specialist.objects.filter(
    specialty='emergency',
    is_24_hours=True,
    is_active=True
)

# Find specialists by distance
nearby = Specialist.objects.filter(
    is_active=True,
    distance_km__lte=50
).order_by('distance_km')

# Top-rated specialists
top_rated = Specialist.objects.filter(
    is_active=True,
    average_rating__isnull=False
).order_by('-average_rating')[:10]
```

### Referral Queries

```python
from apps.referrals.models import Referral
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import timedelta

# Pending outbound referrals
pending = Referral.objects.filter(
    direction='outbound',
    status__in=['draft', 'sent', 'received', 'scheduled']
)

# Urgent referrals
urgent = Referral.objects.filter(
    urgency__in=['urgent', 'emergency'],
    status__in=['draft', 'sent']
)

# Awaiting specialist reports
awaiting_reports = Referral.objects.filter(
    status='report_pending'
).select_related('specialist', 'pet')

# Referrals this month by specialty
from django.db.models.functions import TruncMonth

monthly_by_specialty = Referral.objects.filter(
    created_at__month=timezone.now().month
).values('specialist__specialty').annotate(
    count=Count('id')
).order_by('-count')

# Average time to completion
completed = Referral.objects.filter(
    status='completed',
    completed_at__isnull=False,
    sent_at__isnull=False
)
# Calculate duration in application code

# Referrals by outcome
outcomes = Referral.objects.filter(
    status='completed'
).values('outcome').annotate(
    count=Count('id')
)
```

### Visiting Schedule Queries

```python
from apps.referrals.models import VisitingSchedule, VisitingAppointment
from datetime import date, timedelta

# Today's visiting specialists
today_visits = VisitingSchedule.objects.filter(
    date=date.today(),
    status__in=['scheduled', 'confirmed']
).select_related('specialist')

# This week's schedule
week_end = date.today() + timedelta(days=7)
this_week = VisitingSchedule.objects.filter(
    date__gte=date.today(),
    date__lte=week_end
).order_by('date', 'start_time')

# Available appointment slots
schedule = VisitingSchedule.objects.get(pk=schedule_id)
if schedule.max_appointments:
    available = schedule.max_appointments - schedule.appointments_booked
else:
    available = None  # Unlimited

# Appointments for a schedule
appointments = VisitingAppointment.objects.filter(
    schedule=schedule
).order_by('appointment_time')
```

### Reporting Queries

```python
from django.db.models import Count, Avg
from django.db.models.functions import TruncMonth

# Monthly referral volume
monthly_volume = Referral.objects.annotate(
    month=TruncMonth('created_at')
).values('month').annotate(
    outbound=Count('id', filter=Q(direction='outbound')),
    inbound=Count('id', filter=Q(direction='inbound'))
).order_by('month')

# Specialist utilization
specialist_stats = Specialist.objects.filter(
    is_active=True
).annotate(
    referral_count=Count('referrals_received'),
    avg_rating=Avg('referrals_received__quality_rating')
).order_by('-referral_count')

# Referral success rate
total = Referral.objects.filter(status='completed').count()
successful = Referral.objects.filter(
    status='completed',
    outcome='successful'
).count()
success_rate = (successful / total * 100) if total > 0 else 0
```

## Testing

### Unit Tests

Location: `tests/test_referrals.py`

```bash
# Run referrals unit tests
python -m pytest tests/test_referrals.py -v
```

### Browser Tests

Location: `tests/e2e/browser/test_referrals.py`

```bash
# Run referrals browser tests
python -m pytest tests/e2e/browser/test_referrals.py -v

# Run with visible browser
python -m pytest tests/e2e/browser/test_referrals.py -v --headed --slowmo=500
```

### Key Test Scenarios

1. **Specialist Management**
   - Create specialist with all fields
   - Filter by specialty
   - Toggle visiting status

2. **Referral Workflow**
   - Create outbound referral
   - Track status transitions
   - Attach documents
   - Record specialist findings
   - Complete with outcome

3. **Visiting Schedules**
   - Create recurring schedule
   - Book appointments
   - Check capacity limits
   - Complete appointments with billing

4. **Audit Logging**
   - Verify high-sensitivity logging for referral details
   - Check IP and user tracking
