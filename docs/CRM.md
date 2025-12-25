# CRM Module

The `apps.crm` module provides Customer Relationship Management functionality for tracking customer profiles, interactions, segmentation, and analytics.

## Table of Contents

- [Overview](#overview)
- [Models](#models)
  - [CustomerTag](#customertag)
  - [CustomerSegment](#customersegment)
  - [OwnerProfile](#ownerprofile)
  - [Interaction](#interaction)
  - [CustomerNote](#customernote)
- [Workflows](#workflows)
  - [Customer Lifecycle](#customer-lifecycle)
  - [Interaction Tracking](#interaction-tracking)
  - [Segmentation](#segmentation)
  - [Referral Tracking](#referral-tracking)
- [Analytics](#analytics)
- [Integration Points](#integration-points)
- [Query Examples](#query-examples)
- [Testing](#testing)

## Overview

The CRM module handles:

- **Customer Profiles** - Extended owner information and preferences
- **Tags & Segments** - Categorization and dynamic grouping
- **Interaction Tracking** - Communication history across channels
- **Analytics** - Visit tracking, spending, lifetime value
- **Referrals** - Customer referral tracking
- **Notes** - Internal staff notes about customers

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│      User       │────▶│  OwnerProfile   │────▶│   CustomerTag   │
│   (accounts)    │     │   (CRM data)    │     │  (categories)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Interaction   │    │  CustomerNote   │    │ CustomerSegment │
│  (touchpoints)  │    │  (staff notes)  │    │   (grouping)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Models

### CustomerTag

Location: `apps/crm/models.py`

Tags for categorizing customers.

```python
class CustomerTag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#6c757d')  # Hex color
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Common Tags:**

| Tag | Color | Description |
|-----|-------|-------------|
| VIP | `#ffc107` | High-value customers |
| New Customer | `#28a745` | First-time visitors |
| Breeder | `#17a2b8` | Professional breeders |
| Rescue | `#6f42c1` | Animal rescue organizations |
| Multiple Pets | `#fd7e14` | Owners with 3+ pets |
| Senior Discount | `#6c757d` | Eligible for senior pricing |

### CustomerSegment

Dynamic customer segments based on criteria.

```python
class CustomerSegment(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    criteria = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Criteria Schema:**

```json
{
  "min_visits": 5,
  "min_spent": 500.00,
  "max_days_since_visit": 90,
  "tags_include": ["VIP"],
  "tags_exclude": ["Inactive"],
  "has_pets_species": ["dog", "cat"]
}
```

### OwnerProfile

Extended profile for pet owners with CRM data.

```python
class OwnerProfile(models.Model):
    LANGUAGE_CHOICES = [
        ('es', 'Spanish'),
        ('en', 'English'),
    ]

    CONTACT_METHOD_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
        ('phone', 'Phone Call'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='owner_profile')

    # Preferences
    preferred_language = models.CharField(max_length=5, default='es')
    preferred_contact_method = models.CharField(max_length=20, default='whatsapp')
    marketing_preferences = models.JSONField(default=dict)

    # CRM data
    tags = models.ManyToManyField(CustomerTag, blank=True, related_name='profiles')
    notes = models.TextField(blank=True)

    # Analytics
    first_visit_date = models.DateField(null=True, blank=True)
    last_visit_date = models.DateField(null=True, blank=True)
    total_visits = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    lifetime_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Referral tracking
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='referrals')
    referral_source = models.CharField(max_length=100, blank=True)

    # Social
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Marketing Preferences Schema:**

```json
{
  "email_newsletters": true,
  "sms_promotions": false,
  "appointment_reminders": true,
  "vaccination_reminders": true,
  "birthday_messages": true
}
```

### Interaction

Customer interaction/touchpoint records.

```python
class Interaction(models.Model):
    INTERACTION_TYPES = [
        ('call', 'Phone Call'),
        ('email', 'Email'),
        ('chat', 'Chat'),
        ('visit', 'In-Person Visit'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
    ]

    CHANNEL_CHOICES = [
        ('phone', 'Phone'),
        ('email', 'Email'),
        ('chat', 'Chat'),
        ('in_person', 'In Person'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
        ('social', 'Social Media'),
    ]

    DIRECTION_CHOICES = [
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound'),
    ]

    owner_profile = models.ForeignKey(OwnerProfile, on_delete=models.CASCADE,
                                      related_name='interactions')
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES)

    subject = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)

    handled_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, blank=True,
                                   related_name='handled_interactions')

    duration_minutes = models.IntegerField(null=True, blank=True)

    outcome = models.CharField(max_length=100, blank=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### CustomerNote

Internal notes about customers.

```python
class CustomerNote(models.Model):
    owner_profile = models.ForeignKey(OwnerProfile, on_delete=models.CASCADE,
                                      related_name='customer_notes')
    author = models.ForeignKey(User, on_delete=models.SET_NULL,
                               null=True, related_name='authored_notes')
    content = models.TextField()
    is_pinned = models.BooleanField(default=False)
    is_private = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']
```

## Workflows

### Customer Lifecycle

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    Lead     │───▶│ First Visit │───▶│   Active    │───▶│    VIP      │
│             │    │             │    │  Customer   │    │  Customer   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                             │
                                             ▼
                                      ┌─────────────┐
                                      │   At Risk   │
                                      │(no visits)  │
                                      └─────────────┘
                                             │
                                             ▼
                                      ┌─────────────┐
                                      │   Churned   │
                                      │             │
                                      └─────────────┘
```

**Creating Customer Profile:**

```python
from apps.crm.models import OwnerProfile, CustomerTag

# Create profile for new user
profile = OwnerProfile.objects.create(
    user=user,
    preferred_language='es',
    preferred_contact_method='whatsapp',
    referral_source='Google',
    first_visit_date=date.today(),
    marketing_preferences={
        'email_newsletters': True,
        'sms_promotions': True,
        'appointment_reminders': True,
    }
)

# Add tags
new_customer_tag = CustomerTag.objects.get(name='New Customer')
profile.tags.add(new_customer_tag)
```

### Interaction Tracking

```python
from apps.crm.models import Interaction

# Log phone call
interaction = Interaction.objects.create(
    owner_profile=profile,
    interaction_type='call',
    channel='phone',
    direction='inbound',
    subject='Appointment inquiry',
    notes='Asked about vaccination schedule for new puppy',
    handled_by=request.user,
    duration_minutes=5,
    outcome='Appointment booked',
    follow_up_required=False,
)

# Log WhatsApp message
interaction = Interaction.objects.create(
    owner_profile=profile,
    interaction_type='whatsapp',
    channel='whatsapp',
    direction='outbound',
    subject='Appointment reminder',
    notes='Sent reminder for tomorrow appointment at 10am',
    handled_by=request.user,
)
```

### Segmentation

```python
from apps.crm.models import CustomerSegment, OwnerProfile
from django.db.models import Q

# Create VIP segment
vip_segment = CustomerSegment.objects.create(
    name='VIP Customers',
    description='High-value customers with multiple visits',
    criteria={
        'min_visits': 10,
        'min_spent': 5000.00,
    }
)

# Query customers matching segment
def get_segment_customers(segment):
    criteria = segment.criteria
    queryset = OwnerProfile.objects.all()

    if 'min_visits' in criteria:
        queryset = queryset.filter(total_visits__gte=criteria['min_visits'])

    if 'min_spent' in criteria:
        queryset = queryset.filter(total_spent__gte=criteria['min_spent'])

    if 'max_days_since_visit' in criteria:
        cutoff = date.today() - timedelta(days=criteria['max_days_since_visit'])
        queryset = queryset.filter(last_visit_date__gte=cutoff)

    if 'tags_include' in criteria:
        for tag_name in criteria['tags_include']:
            queryset = queryset.filter(tags__name=tag_name)

    if 'tags_exclude' in criteria:
        queryset = queryset.exclude(tags__name__in=criteria['tags_exclude'])

    return queryset
```

### Referral Tracking

```python
from apps.crm.models import OwnerProfile

# Track referral
new_customer_profile = OwnerProfile.objects.create(
    user=new_user,
    referred_by=existing_customer_profile,
    referral_source='Friend recommendation',
)

# Get referral count for customer
referral_count = existing_customer_profile.referrals.count()

# Get all referrals
referrals = existing_customer_profile.referrals.select_related('user')
```

## Analytics

### Updating Customer Metrics

```python
from apps.crm.models import OwnerProfile
from django.db.models import Sum

def update_customer_metrics(profile, visit_amount=None):
    """Update customer analytics after visit."""
    # Update visit count
    profile.total_visits += 1
    profile.last_visit_date = date.today()

    # Update spending
    if visit_amount:
        profile.total_spent += visit_amount

    # Calculate lifetime value (simplified)
    # LTV = Average Order Value * Purchase Frequency * Customer Lifespan
    if profile.total_visits > 0:
        avg_order = profile.total_spent / profile.total_visits
        # Assume 3-year average customer lifespan
        projected_visits = profile.total_visits * 3
        profile.lifetime_value = avg_order * projected_visits

    profile.save()
```

### Customer Scoring

```python
def calculate_customer_score(profile):
    """Calculate customer engagement score (0-100)."""
    score = 0

    # Recency (30 points max)
    if profile.last_visit_date:
        days_since_visit = (date.today() - profile.last_visit_date).days
        if days_since_visit <= 30:
            score += 30
        elif days_since_visit <= 90:
            score += 20
        elif days_since_visit <= 180:
            score += 10

    # Frequency (30 points max)
    if profile.total_visits >= 12:
        score += 30
    elif profile.total_visits >= 6:
        score += 20
    elif profile.total_visits >= 3:
        score += 10

    # Monetary (40 points max)
    if profile.total_spent >= 10000:
        score += 40
    elif profile.total_spent >= 5000:
        score += 30
    elif profile.total_spent >= 1000:
        score += 20
    elif profile.total_spent >= 500:
        score += 10

    return score
```

## Integration Points

### With Appointments Module

```python
from apps.appointments.models import Appointment
from apps.crm.models import OwnerProfile, Interaction

def on_appointment_completed(appointment):
    """Update CRM when appointment completes."""
    profile = appointment.pet.owner.owner_profile

    # Update visit metrics
    profile.total_visits += 1
    profile.last_visit_date = date.today()
    profile.save()

    # Log interaction
    Interaction.objects.create(
        owner_profile=profile,
        interaction_type='visit',
        channel='in_person',
        direction='inbound',
        subject=f'Appointment: {appointment.service.name}',
        notes=f'Pet: {appointment.pet.name}',
    )
```

### With Billing Module

```python
from apps.billing.models import Invoice
from apps.crm.models import OwnerProfile

def on_invoice_paid(invoice):
    """Update CRM spending when invoice is paid."""
    try:
        profile = invoice.customer.owner_profile
        profile.total_spent += invoice.total
        profile.save()
    except OwnerProfile.DoesNotExist:
        pass
```

### With Pets Module

```python
from apps.pets.models import Pet
from apps.crm.models import OwnerProfile, CustomerTag

def on_pet_added(pet):
    """Update CRM tags based on pet count."""
    try:
        profile = pet.owner.owner_profile
        pet_count = pet.owner.pets.count()

        if pet_count >= 3:
            multi_pet_tag, _ = CustomerTag.objects.get_or_create(
                name='Multiple Pets',
                defaults={'color': '#fd7e14'}
            )
            profile.tags.add(multi_pet_tag)
    except OwnerProfile.DoesNotExist:
        pass
```

### With Audit Module

CRM pages are logged by AuditMiddleware:

| Path | Resource Type | Sensitivity |
|------|---------------|-------------|
| `/crm/` | `crm.dashboard` | normal |
| `/crm/customers/` | `crm.customer` | **high** |
| `/crm/customers/<id>/` | `crm.customer` | **high** |

## Query Examples

### Customer Queries

```python
from apps.crm.models import OwnerProfile, CustomerTag
from django.db.models import Q, Count, Sum
from datetime import date, timedelta

# VIP customers
vip_tag = CustomerTag.objects.get(name='VIP')
vip_customers = OwnerProfile.objects.filter(tags=vip_tag)

# High-value customers (>$5000 spent)
high_value = OwnerProfile.objects.filter(total_spent__gte=5000)

# At-risk customers (no visit in 90+ days)
cutoff = date.today() - timedelta(days=90)
at_risk = OwnerProfile.objects.filter(
    last_visit_date__lt=cutoff
).exclude(
    last_visit_date__isnull=True
)

# New customers this month
first_of_month = date.today().replace(day=1)
new_customers = OwnerProfile.objects.filter(
    first_visit_date__gte=first_of_month
)

# Customers preferring WhatsApp
whatsapp_customers = OwnerProfile.objects.filter(
    preferred_contact_method='whatsapp'
)

# Top referrers
top_referrers = OwnerProfile.objects.annotate(
    referral_count=Count('referrals')
).filter(
    referral_count__gt=0
).order_by('-referral_count')[:10]
```

### Interaction Queries

```python
from apps.crm.models import Interaction
from django.db.models import Count
from django.db.models.functions import TruncDate

# Today's interactions
today_interactions = Interaction.objects.filter(
    created_at__date=date.today()
).select_related('owner_profile', 'handled_by')

# Interactions requiring follow-up
follow_ups = Interaction.objects.filter(
    follow_up_required=True,
    follow_up_date__lte=date.today()
)

# Interaction volume by channel
channel_volume = Interaction.objects.values('channel').annotate(
    count=Count('id')
).order_by('-count')

# Staff interaction counts
staff_counts = Interaction.objects.values(
    'handled_by__first_name', 'handled_by__last_name'
).annotate(
    count=Count('id')
).order_by('-count')

# Daily interaction trend
daily_trend = Interaction.objects.annotate(
    date=TruncDate('created_at')
).values('date').annotate(
    count=Count('id')
).order_by('-date')[:30]
```

### Segment Queries

```python
from apps.crm.models import CustomerSegment, OwnerProfile

# Get all active segments
segments = CustomerSegment.objects.filter(is_active=True)

# Count customers in each segment
for segment in segments:
    customers = get_segment_customers(segment)
    print(f"{segment.name}: {customers.count()} customers")
```

### Analytics Queries

```python
from apps.crm.models import OwnerProfile
from django.db.models import Avg, Sum, Count

# Customer lifetime value stats
ltv_stats = OwnerProfile.objects.aggregate(
    avg_ltv=Avg('lifetime_value'),
    total_ltv=Sum('lifetime_value'),
    customer_count=Count('id')
)

# Average spending per customer
avg_spending = OwnerProfile.objects.aggregate(
    avg_spent=Avg('total_spent')
)

# Visit frequency distribution
visit_distribution = OwnerProfile.objects.values('total_visits').annotate(
    customer_count=Count('id')
).order_by('total_visits')
```

## Testing

### Unit Tests

Location: `tests/test_crm.py`

```bash
# Run CRM unit tests
python -m pytest tests/test_crm.py -v
```

### Key Test Scenarios

1. **Customer Profiles**
   - Create profile with preferences
   - Tag assignment
   - Referral tracking
   - Analytics updates

2. **Interactions**
   - Log different interaction types
   - Track follow-ups
   - Staff assignment

3. **Segments**
   - Create segment with criteria
   - Query matching customers
   - Dynamic segment updates

4. **Notes**
   - Create and pin notes
   - Private note visibility
   - Note ordering

### Browser Tests

Location: `tests/e2e/browser/test_crm.py`

```bash
# Run CRM browser tests
python -m pytest tests/e2e/browser/test_crm.py -v

# Run with visible browser
python -m pytest tests/e2e/browser/test_crm.py -v --headed --slowmo=500
```
