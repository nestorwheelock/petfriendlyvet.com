# Services Module

The `apps.services` module manages veterinary services, external partner directory, and referrals to partner businesses like groomers, boarding facilities, and trainers.

## Table of Contents

- [Overview](#overview)
- [Models](#models)
  - [Service](#service)
  - [ExternalPartner](#externalpartner)
  - [Referral](#referral)
- [Views](#views)
- [URL Patterns](#url-patterns)
- [Workflows](#workflows)
  - [Service Management](#service-management)
  - [Partner Directory](#partner-directory)
  - [Partner Referrals](#partner-referrals)
- [Service Categories](#service-categories)
- [Mexican Tax Compliance](#mexican-tax-compliance)
- [Integration Points](#integration-points)
- [Query Examples](#query-examples)
- [Testing](#testing)

## Overview

The services module handles:

- **Veterinary Services** - Clinic service catalog with pricing
- **External Partners** - Directory of partner businesses
- **Partner Referrals** - Track referrals to groomers, boarding, etc.
- **SAT Compliance** - Mexican tax codes for invoicing

```
┌─────────────────┐                    ┌─────────────────┐
│    Service      │                    │ ExternalPartner │
│   (catalog)     │                    │   (directory)   │
└─────────────────┘                    └────────┬────────┘
                                                │
                                                ▼
                                       ┌─────────────────┐
                                       │    Referral     │
                                       │   (tracking)    │
                                       └─────────────────┘
```

## Models

### Service

Location: `apps/services/models.py`

Veterinary services offered by the clinic.

```python
SERVICE_CATEGORIES = [
    ('consultation', 'Consultation'),
    ('vaccination', 'Vaccination'),
    ('surgery', 'Surgery'),
    ('dental', 'Dental'),
    ('laboratory', 'Laboratory'),
    ('imaging', 'Imaging'),
    ('grooming', 'Grooming'),
    ('emergency', 'Emergency'),
    ('preventive', 'Preventive Care'),
    ('other', 'Other'),
]

class Service(models.Model):
    name = models.CharField(max_length=200)
    name_es = models.CharField(max_length=200, blank=True)  # Spanish name
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=SERVICE_CATEGORIES, default='consultation')

    # Pricing
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    duration_minutes = models.PositiveIntegerField(default=30)

    # SAT codes for CFDI (Mexican tax compliance)
    clave_producto_sat = models.CharField(max_length=10, blank=True)
    clave_unidad_sat = models.CharField(max_length=5, default='E48')  # Unit of service

    # Status
    is_active = models.BooleanField(default=True)
    requires_appointment = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `name_es` | CharField | Spanish translation for bilingual support |
| `base_price` | Decimal | Service price in MXN |
| `duration_minutes` | Integer | Expected service duration |
| `clave_producto_sat` | CharField | SAT product code for CFDI |
| `requires_appointment` | Boolean | Whether appointment is needed |

### ExternalPartner

External service partners (grooming, boarding, etc.).

```python
PARTNER_TYPES = [
    ('grooming', 'Grooming'),
    ('boarding', 'Boarding'),
    ('training', 'Training'),
    ('daycare', 'Daycare'),
    ('pet_sitting', 'Pet Sitting'),
    ('transport', 'Pet Transport'),
    ('other', 'Other'),
]

class ExternalPartner(models.Model):
    name = models.CharField(max_length=200)
    partner_type = models.CharField(max_length=20, choices=PARTNER_TYPES)

    # Contact information
    contact_name = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    address = models.TextField(blank=True)

    # Details
    description = models.TextField(blank=True)
    services_offered = models.TextField(blank=True)
    hours_of_operation = models.TextField(blank=True)
    price_range = models.CharField(max_length=100, blank=True)

    # Rating and status
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_preferred = models.BooleanField(default=False)

    # Notes for staff
    internal_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Referral

Track referrals to external partners.

```python
REFERRAL_STATUS = [
    ('pending', 'Pending'),
    ('contacted', 'Contacted'),
    ('scheduled', 'Scheduled'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
]

class Referral(models.Model):
    pet = models.ForeignKey('pets.Pet', on_delete=models.CASCADE, related_name='referrals')
    partner = models.ForeignKey(ExternalPartner, on_delete=models.CASCADE, related_name='referrals')
    referred_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    service_type = models.CharField(max_length=20, choices=PARTNER_TYPES)
    status = models.CharField(max_length=20, choices=REFERRAL_STATUS, default='pending')

    # Scheduling
    preferred_date = models.DateField(null=True, blank=True)
    scheduled_date = models.DateField(null=True, blank=True)

    # Notes and feedback
    notes = models.TextField(blank=True)
    feedback = models.TextField(blank=True)
    rating = models.IntegerField(null=True, blank=True)  # 1-5

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
```

## Views

Location: `apps/services/views.py`

### PartnerListView

List external service partners with type filtering.

```python
class PartnerListView(LoginRequiredMixin, ListView):
    model = ExternalPartner
    template_name = 'services/partner_list.html'

    def get_queryset(self):
        qs = ExternalPartner.objects.filter(is_active=True)
        partner_type = self.request.GET.get('type')
        if partner_type:
            qs = qs.filter(partner_type=partner_type)
        return qs.order_by('-is_preferred', 'name')
```

### PartnerDetailView

View individual partner details.

```python
class PartnerDetailView(LoginRequiredMixin, DetailView):
    model = ExternalPartner
    template_name = 'services/partner_detail.html'

    def get_queryset(self):
        return ExternalPartner.objects.filter(is_active=True)
```

### ReferralCreateView

Create a referral to a partner.

```python
class ReferralCreateView(LoginRequiredMixin, CreateView):
    model = Referral
    form_class = ReferralForm
    template_name = 'services/referral_form.html'

    def form_valid(self, form):
        partner = self.get_partner()
        form.instance.partner = partner
        form.instance.referred_by = self.request.user
        form.instance.service_type = partner.partner_type
        return super().form_valid(form)
```

### ReferralListView

List user's referrals.

```python
class ReferralListView(LoginRequiredMixin, ListView):
    model = Referral
    template_name = 'services/referral_list.html'

    def get_queryset(self):
        return Referral.objects.filter(
            pet__owner=self.request.user
        ).select_related('pet', 'partner').order_by('-created_at')
```

## URL Patterns

Location: `apps/services/urls.py`

```python
app_name = 'services'

urlpatterns = [
    # Partner directory
    path('partners/', views.PartnerListView.as_view(), name='partner_list'),
    path('partners/<int:pk>/', views.PartnerDetailView.as_view(), name='partner_detail'),

    # Referrals
    path('partners/<int:partner_pk>/refer/', views.ReferralCreateView.as_view(), name='referral_create'),
    path('referrals/', views.ReferralListView.as_view(), name='referral_list'),
]
```

## Workflows

### Service Management

```python
from apps.services.models import Service
from decimal import Decimal

# Create service
service = Service.objects.create(
    name='Dental Cleaning',
    name_es='Limpieza Dental',
    description='Professional dental cleaning under anesthesia',
    category='dental',
    base_price=Decimal('2500.00'),
    duration_minutes=60,
    clave_producto_sat='85121800',  # Healthcare services
    clave_unidad_sat='E48',
    is_active=True,
    requires_appointment=True,
)

# Deactivate service
service.is_active = False
service.save()
```

### Partner Directory

```python
from apps.services.models import ExternalPartner

# Add partner
partner = ExternalPartner.objects.create(
    name='Pet Spa Condesa',
    partner_type='grooming',
    contact_name='María González',
    phone='55-1234-5678',
    email='info@petspa.com',
    website='https://petspa.com',
    address='Av. Tamaulipas 123, Condesa, CDMX',
    description='Premium pet grooming services',
    services_offered='Bath, haircut, nail trim, teeth cleaning, spa treatments',
    hours_of_operation='Mon-Sat 9am-7pm, Sun 10am-4pm',
    price_range='$300-$1200 MXN',
    is_active=True,
    is_preferred=True,
)

# Mark as preferred
partner.is_preferred = True
partner.save()
```

### Partner Referrals

```python
from apps.services.models import Referral
from django.utils import timezone

# Create referral
referral = Referral.objects.create(
    pet=pet,
    partner=grooming_partner,
    referred_by=staff_user,
    service_type='grooming',
    status='pending',
    preferred_date=date.today() + timedelta(days=3),
    notes='Full grooming requested. Owner prefers morning appointment.',
)

# Update status as it progresses
referral.status = 'contacted'
referral.save()

referral.status = 'scheduled'
referral.scheduled_date = date.today() + timedelta(days=3)
referral.save()

# Complete referral
referral.status = 'completed'
referral.completed_at = timezone.now()
referral.feedback = 'Great service, dog looks beautiful!'
referral.rating = 5
referral.save()
```

## Service Categories

### Veterinary Services

| Category | Description | Examples |
|----------|-------------|----------|
| `consultation` | General exams and consultations | Wellness exam, sick visit |
| `vaccination` | Immunizations | Rabies, DHPP, FVRCP |
| `surgery` | Surgical procedures | Spay/neuter, tumor removal |
| `dental` | Dental care | Cleaning, extractions |
| `laboratory` | Lab work | Blood panel, urinalysis |
| `imaging` | Diagnostic imaging | X-rays, ultrasound |
| `grooming` | Grooming services | Bath, haircut, nails |
| `emergency` | Emergency care | After-hours emergencies |
| `preventive` | Preventive care | Parasite prevention, wellness plans |

### Partner Types

| Type | Description | Examples |
|------|-------------|----------|
| `grooming` | Pet grooming services | Bath, haircut, nail trim |
| `boarding` | Overnight pet boarding | Kennels, pet hotels |
| `training` | Dog training | Obedience, behavior modification |
| `daycare` | Daytime pet care | Dog daycare facilities |
| `pet_sitting` | In-home pet sitting | Pet sitters, house visits |
| `transport` | Pet transportation | Pet taxis, airport transport |

## Mexican Tax Compliance

### SAT Codes

For CFDI (electronic invoicing), services must include:

| Field | Description | Example |
|-------|-------------|---------|
| `clave_producto_sat` | Product/service code | `85121800` (Healthcare services) |
| `clave_unidad_sat` | Unit of measure code | `E48` (Unit of service) |

### Common SAT Codes for Veterinary

| Code | Description |
|------|-------------|
| `85121800` | Healthcare services |
| `85121801` | Medical consultation |
| `85121802` | Medical treatment |
| `42201700` | Veterinary equipment |
| `42201800` | Veterinary instruments |

## Integration Points

### With Appointments Module

```python
from apps.appointments.models import ServiceType
from apps.services.models import Service

# Services are used in appointment booking
# Note: The appointments module has its own ServiceType model
# This module's Service is for the service catalog
```

### With Billing Module

```python
from apps.billing.models import InvoiceLineItem
from apps.services.models import Service

# Create invoice line item from service
service = Service.objects.get(name='Dental Cleaning')
line_item = InvoiceLineItem.objects.create(
    invoice=invoice,
    description=service.name,
    quantity=1,
    unit_price=service.base_price,
    subtotal=service.base_price,
    sat_code=service.clave_producto_sat,
    sat_unit=service.clave_unidad_sat,
)
```

### With Pets Module

```python
from apps.services.models import Referral
from apps.pets.models import Pet

# Get all referrals for a pet
pet = Pet.objects.get(pk=pet_id)
referrals = pet.referrals.select_related('partner').order_by('-created_at')
```

## Query Examples

### Service Queries

```python
from apps.services.models import Service
from django.db.models import Count

# Active services by category
by_category = Service.objects.filter(
    is_active=True
).values('category').annotate(
    count=Count('id')
).order_by('category')

# Services requiring appointments
appointment_services = Service.objects.filter(
    is_active=True,
    requires_appointment=True
)

# Search services
query = 'dental'
results = Service.objects.filter(
    is_active=True
).filter(
    Q(name__icontains=query) | Q(description__icontains=query)
)
```

### Partner Queries

```python
from apps.services.models import ExternalPartner

# Active partners by type
groomers = ExternalPartner.objects.filter(
    is_active=True,
    partner_type='grooming'
).order_by('-is_preferred', 'name')

# Preferred partners
preferred = ExternalPartner.objects.filter(
    is_active=True,
    is_preferred=True
)

# Top-rated partners
top_rated = ExternalPartner.objects.filter(
    is_active=True,
    average_rating__isnull=False
).order_by('-average_rating')[:5]
```

### Referral Queries

```python
from apps.services.models import Referral
from django.db.models import Count, Avg

# Pending referrals
pending = Referral.objects.filter(
    status='pending'
).select_related('pet', 'partner')

# Referrals by partner
partner_stats = Referral.objects.values(
    'partner__name'
).annotate(
    total=Count('id'),
    avg_rating=Avg('rating')
).order_by('-total')

# Completed referrals this month
from datetime import date

completed_this_month = Referral.objects.filter(
    status='completed',
    completed_at__month=date.today().month,
    completed_at__year=date.today().year
)
```

## Testing

### Unit Tests

Location: `tests/test_services.py`

```bash
# Run services unit tests
python -m pytest tests/test_services.py -v
```

### Browser Tests

Location: `tests/e2e/browser/test_services.py`

```bash
# Run services browser tests
python -m pytest tests/e2e/browser/test_services.py -v

# Run with visible browser
python -m pytest tests/e2e/browser/test_services.py -v --headed --slowmo=500
```

### Key Test Scenarios

1. **Service Catalog**
   - Create service with pricing
   - Category filtering
   - SAT code assignment

2. **Partner Directory**
   - Add partner with details
   - Type filtering
   - Preferred partner marking

3. **Referrals**
   - Create referral
   - Status transitions
   - Rating and feedback
