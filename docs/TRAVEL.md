# Travel Module

The `apps.travel` module manages pet travel documentation including health certificates, destination requirements, and travel plans.

## Table of Contents

- [Overview](#overview)
- [Models](#models)
  - [TravelDestination](#traveldestination)
  - [HealthCertificate](#healthcertificate)
  - [CertificateRequirement](#certificaterequirement)
  - [TravelPlan](#travelplan)
- [Workflows](#workflows)
- [Integration Points](#integration-points)
- [Query Examples](#query-examples)
- [Testing](#testing)

## Overview

The travel module provides:

- **Destination Database** - Country-specific travel requirements
- **Health Certificates** - Generate and track travel health certificates
- **Requirement Verification** - Track completion of travel requirements
- **Travel Plans** - Organize pet travel with all documents

## Models

Location: `apps/travel/models.py`

### TravelDestination

Country/destination with pet travel requirements.

```python
class TravelDestination(models.Model):
    country_code = models.CharField(max_length=3, unique=True)  # ISO code
    country_name = models.CharField(max_length=100)
    requirements = models.JSONField(default=dict)  # Structured requirements
    certificate_validity_days = models.IntegerField(default=10)
    quarantine_required = models.BooleanField(default=False)
    quarantine_days = models.IntegerField(null=True)
    airline_requirements = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `country_code` | CharField | ISO 3166 country code (USA, MEX, CAN) |
| `requirements` | JSONField | Structured list of requirements |
| `certificate_validity_days` | Integer | How long certificate is valid |
| `quarantine_required` | Boolean | If destination requires quarantine |

**Example requirements JSON:**
```json
{
    "vaccinations": ["rabies", "distemper"],
    "tests": ["rabies_titer"],
    "timing": {
        "rabies_min_days": 30,
        "rabies_max_days": 365,
        "certificate_before_travel": 10
    },
    "documents": ["microchip_certificate", "vaccination_record"]
}
```

### HealthCertificate

Health certificate for international pet travel.

```python
CERTIFICATE_STATUS = [
    ('pending', 'Pending'),
    ('in_review', 'In Review'),
    ('issued', 'Issued'),
    ('expired', 'Expired'),
    ('cancelled', 'Cancelled'),
]

class HealthCertificate(models.Model):
    pet = models.ForeignKey('pets.Pet', on_delete=models.CASCADE, related_name='health_certificates')
    destination = models.ForeignKey(TravelDestination, on_delete=models.PROTECT)
    travel_date = models.DateField()
    issue_date = models.DateField(null=True)
    expiry_date = models.DateField(null=True)
    status = models.CharField(max_length=20, choices=CERTIFICATE_STATUS, default='pending')
    certificate_number = models.CharField(max_length=50, blank=True)
    issued_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    pdf_document = models.FileField(upload_to='travel_certificates/', null=True)
    notes = models.TextField(blank=True)

    def calculate_expiry(self):
        """Calculate expiry date based on issue date and destination validity."""
        if self.issue_date:
            self.expiry_date = self.issue_date + timedelta(
                days=self.destination.certificate_validity_days
            )
            self.save(update_fields=['expiry_date'])
```

### CertificateRequirement

Individual requirement for a health certificate.

```python
class CertificateRequirement(models.Model):
    certificate = models.ForeignKey(HealthCertificate, on_delete=models.CASCADE, related_name='requirements')
    requirement_type = models.CharField(max_length=50)  # vaccination, test, microchip
    description = models.TextField()
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    verified_at = models.DateField(null=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        status = '✓' if self.is_verified else '○'
        return f"{status} {self.requirement_type}"
```

### TravelPlan

Complete travel plan for a pet.

```python
TRAVEL_PLAN_STATUS = [
    ('planning', 'Planning'),
    ('documents_pending', 'Documents Pending'),
    ('ready', 'Ready to Travel'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
]

class TravelPlan(models.Model):
    pet = models.ForeignKey('pets.Pet', on_delete=models.CASCADE, related_name='travel_plans')
    destination = models.ForeignKey(TravelDestination, on_delete=models.PROTECT)
    departure_date = models.DateField()
    return_date = models.DateField(null=True)
    airline = models.CharField(max_length=100, blank=True)
    flight_number = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=TRAVEL_PLAN_STATUS, default='planning')
    certificate = models.ForeignKey(HealthCertificate, null=True, on_delete=models.SET_NULL)
    notes = models.TextField(blank=True)
```

## Workflows

### Creating a Travel Plan

```python
from apps.travel.models import TravelDestination, TravelPlan, HealthCertificate
from datetime import date, timedelta

# Get destination
destination = TravelDestination.objects.get(country_code='USA')

# Create travel plan
plan = TravelPlan.objects.create(
    pet=pet,
    destination=destination,
    departure_date=date.today() + timedelta(days=30),
    return_date=date.today() + timedelta(days=45),
    airline='Aeromexico',
    flight_number='AM456',
    status='planning',
)

# Create associated health certificate
certificate = HealthCertificate.objects.create(
    pet=pet,
    destination=destination,
    travel_date=plan.departure_date,
    status='pending',
)

plan.certificate = certificate
plan.status = 'documents_pending'
plan.save()
```

### Adding Requirements to Certificate

```python
from apps.travel.models import CertificateRequirement

# Based on destination requirements
requirements_data = [
    {'type': 'vaccination', 'description': 'Rabies vaccination (within 12 months)'},
    {'type': 'vaccination', 'description': 'Distemper vaccination (within 12 months)'},
    {'type': 'test', 'description': 'Rabies titer test (if required)'},
    {'type': 'microchip', 'description': 'ISO microchip implanted and registered'},
    {'type': 'exam', 'description': 'Physical examination by licensed veterinarian'},
]

for req in requirements_data:
    CertificateRequirement.objects.create(
        certificate=certificate,
        requirement_type=req['type'],
        description=req['description'],
    )
```

### Verifying Requirements

```python
from apps.travel.models import CertificateRequirement
from datetime import date

requirement = CertificateRequirement.objects.get(pk=requirement_id)
requirement.is_verified = True
requirement.verified_by = vet_user
requirement.verified_at = date.today()
requirement.save()

# Check if all requirements are verified
certificate = requirement.certificate
all_verified = not certificate.requirements.filter(is_verified=False).exists()

if all_verified:
    certificate.status = 'in_review'
    certificate.save()
```

### Issuing a Certificate

```python
from apps.travel.models import HealthCertificate
from datetime import date
from django.utils import timezone

certificate = HealthCertificate.objects.get(pk=certificate_id)

# Issue certificate
certificate.status = 'issued'
certificate.issue_date = date.today()
certificate.certificate_number = f'HC-{timezone.now().strftime("%Y%m%d")}-{certificate.pk:05d}'
certificate.issued_by = vet_user
certificate.calculate_expiry()
certificate.save()

# Update travel plan
plan = certificate.travel_plans.first()
if plan:
    plan.status = 'ready'
    plan.save()
```

## Integration Points

### With Pets Module

```python
from apps.pets.models import Pet, Vaccination

def check_vaccination_requirements(pet, destination):
    """Check if pet meets destination's vaccination requirements."""
    requirements = destination.requirements.get('vaccinations', [])
    issues = []

    for vax_type in requirements:
        vaccination = pet.vaccinations.filter(
            vaccine_type__icontains=vax_type,
            expiry_date__gte=date.today()
        ).first()

        if not vaccination:
            issues.append(f'Missing or expired: {vax_type}')

    return issues
```

### With Appointments

```python
# Schedule travel exam appointment
from apps.appointments.models import Appointment

def schedule_travel_exam(travel_plan):
    # Schedule exam before travel date
    exam_date = travel_plan.departure_date - timedelta(days=7)

    appointment = Appointment.objects.create(
        pet=travel_plan.pet,
        owner=travel_plan.pet.owner,
        appointment_type='travel_exam',
        date=exam_date,
        notes=f'Travel exam for {travel_plan.destination.country_name}',
    )
    return appointment
```

### With Reminders

```python
# Create reminders for travel preparation
from apps.communications.models import ReminderSchedule

def create_travel_reminders(travel_plan):
    reminders = [
        (30, 'Start travel documentation process'),
        (14, 'Schedule travel health exam'),
        (7, 'Complete all vaccinations'),
        (3, 'Confirm health certificate is ready'),
        (1, 'Final travel checklist'),
    ]

    for days_before, message in reminders:
        ReminderSchedule.objects.create(
            reminder_type='travel',
            content_type=ContentType.objects.get_for_model(TravelPlan),
            object_id=travel_plan.pk,
            scheduled_for=travel_plan.departure_date - timedelta(days=days_before),
            message=message,
        )
```

## Query Examples

```python
from apps.travel.models import (
    TravelDestination, HealthCertificate, TravelPlan, CertificateRequirement
)
from datetime import date, timedelta

# Active destinations
destinations = TravelDestination.objects.filter(is_active=True).order_by('country_name')

# Destinations requiring quarantine
quarantine_countries = TravelDestination.objects.filter(
    quarantine_required=True,
    is_active=True
)

# Pending certificates
pending = HealthCertificate.objects.filter(
    status='pending'
).select_related('pet', 'destination')

# Certificates expiring soon
expiring = HealthCertificate.objects.filter(
    status='issued',
    expiry_date__lte=date.today() + timedelta(days=7),
    expiry_date__gte=date.today()
)

# Upcoming travel
upcoming = TravelPlan.objects.filter(
    departure_date__gte=date.today(),
    status__in=['planning', 'documents_pending', 'ready']
).order_by('departure_date')

# Incomplete requirements by certificate
from django.db.models import Count
incomplete = HealthCertificate.objects.annotate(
    pending_count=Count('requirements', filter=Q(requirements__is_verified=False))
).filter(pending_count__gt=0)

# Popular destinations
popular = TravelDestination.objects.annotate(
    certificate_count=Count('certificates')
).order_by('-certificate_count')[:10]

# Travel history for a pet
pet_travel = TravelPlan.objects.filter(
    pet=pet,
    status='completed'
).order_by('-departure_date')
```

## Testing

Location: `tests/test_travel.py`

```bash
python -m pytest tests/test_travel.py -v
```
