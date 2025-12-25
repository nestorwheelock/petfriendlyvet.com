# Competitive Intelligence Module

The `apps.competitive` module tracks competitor information, pricing, reviews, and market trends for strategic analysis.

## Table of Contents

- [Overview](#overview)
- [Models](#models)
  - [Competitor](#competitor)
  - [CompetitorService](#competitorservice)
  - [CompetitorReview](#competitorreview)
  - [MarketTrend](#markettrend)
  - [PriceHistory](#pricehistory)
- [Workflows](#workflows)
- [Integration Points](#integration-points)
- [Query Examples](#query-examples)
- [Testing](#testing)

## Overview

The competitive intelligence module provides:

- **Competitor Profiles** - Track nearby veterinary clinics
- **Service Pricing** - Compare prices with competitors
- **Review Monitoring** - Track competitor ratings across platforms
- **Market Trends** - Document industry changes and responses
- **Price History** - Track competitor price changes over time

## Models

Location: `apps/competitive/models.py`

### Competitor

Competitor veterinary clinic information.

```python
class Competitor(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    website = models.URLField(blank=True)
    email = models.EmailField(blank=True)

    # Location
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True)
    distance_km = models.DecimalField(max_digits=6, decimal_places=2, null=True)

    # Operating info
    hours = models.JSONField(default=dict)
    services_offered = models.JSONField(default=list)
    species_treated = models.JSONField(default=list)

    # Social
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    google_maps_url = models.URLField(blank=True)

    # Analysis
    notes = models.TextField(blank=True)
    strengths = models.TextField(blank=True)
    weaknesses = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `distance_km` | Decimal | Distance from our clinic |
| `services_offered` | JSONField | List of services |
| `strengths` | TextField | Competitive advantages |
| `weaknesses` | TextField | Areas of opportunity |

### CompetitorService

Service offered by competitor with pricing comparison.

```python
class CompetitorService(models.Model):
    competitor = models.ForeignKey(Competitor, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)

    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    previous_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    currency = models.CharField(max_length=3, default='MXN')
    price_updated_at = models.DateTimeField(auto_now=True)

    # Comparison
    our_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    price_difference = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['competitor', 'name']

    def save(self, *args, **kwargs):
        if self.our_price and self.price:
            self.price_difference = self.price - self.our_price
        super().save(*args, **kwargs)
```

### CompetitorReview

Review/rating snapshot for competitor.

```python
PLATFORM_CHOICES = [
    ('google', 'Google'),
    ('facebook', 'Facebook'),
    ('yelp', 'Yelp'),
    ('other', 'Other'),
]

class CompetitorReview(models.Model):
    competitor = models.ForeignKey(Competitor, on_delete=models.CASCADE, related_name='reviews')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    rating = models.DecimalField(max_digits=2, decimal_places=1)
    review_count = models.IntegerField(default=0)
    sample_review = models.TextField(blank=True)

    # Track changes
    previous_rating = models.DecimalField(max_digits=2, decimal_places=1, null=True)
    previous_review_count = models.IntegerField(null=True)

    captured_at = models.DateTimeField(auto_now_add=True)
```

### MarketTrend

Market trends and strategic observations.

```python
CATEGORY_CHOICES = [
    ('pricing', 'Pricing'),
    ('service', 'Services'),
    ('marketing', 'Marketing'),
    ('technology', 'Technology'),
    ('regulation', 'Regulation'),
    ('other', 'Other'),
]

IMPACT_CHOICES = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
    ('critical', 'Critical'),
]

class MarketTrend(models.Model):
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    impact_level = models.CharField(max_length=20, choices=IMPACT_CHOICES)
    source = models.CharField(max_length=200, blank=True)

    competitors = models.ManyToManyField(Competitor, blank=True, related_name='trends')

    recommended_action = models.TextField(blank=True)
    action_taken = models.TextField(blank=True)
    action_date = models.DateField(null=True)

    is_active = models.BooleanField(default=True)
```

### PriceHistory

Historical price tracking.

```python
class PriceHistory(models.Model):
    service = models.ForeignKey(CompetitorService, on_delete=models.CASCADE, related_name='price_history')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    captured_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
```

## Workflows

### Adding a Competitor

```python
from apps.competitive.models import Competitor, CompetitorService

competitor = Competitor.objects.create(
    name='Veterinaria Central',
    address='Av. Principal 123, Colonia Centro',
    phone='+52 55 1234 5678',
    website='https://vetcentral.mx',
    latitude=Decimal('19.4326'),
    longitude=Decimal('-99.1332'),
    distance_km=Decimal('2.5'),
    hours={'Mon-Fri': '8:00-20:00', 'Sat': '9:00-14:00'},
    services_offered=['consultations', 'surgery', 'dental', 'grooming'],
    species_treated=['dogs', 'cats', 'birds'],
    strengths='Large facility, 24/7 emergency',
    weaknesses='Higher prices, long wait times',
)
```

### Tracking Competitor Pricing

```python
from apps.competitive.models import CompetitorService, PriceHistory

# Add service with pricing
service = CompetitorService.objects.create(
    competitor=competitor,
    name='General Consultation',
    category='Consultations',
    price=Decimal('650.00'),
    our_price=Decimal('500.00'),  # Auto-calculates price_difference
)

# Update price (creates history)
old_price = service.price
service.previous_price = old_price
service.price = Decimal('700.00')
service.save()

PriceHistory.objects.create(
    service=service,
    price=old_price,
    notes='Price increase noted',
)
```

### Recording Competitor Reviews

```python
from apps.competitive.models import CompetitorReview

# Capture current ratings
CompetitorReview.objects.create(
    competitor=competitor,
    platform='google',
    rating=Decimal('4.3'),
    review_count=156,
    sample_review='Good service but expensive...',
)
```

### Documenting Market Trends

```python
from apps.competitive.models import MarketTrend

trend = MarketTrend.objects.create(
    category='pricing',
    title='Competitors raising consultation prices',
    description='Three competitors increased prices by 10-15% this month.',
    impact_level='medium',
    source='Direct observation',
    recommended_action='Consider modest price increase, emphasize value',
)
trend.competitors.add(competitor1, competitor2)
```

## Integration Points

### With Services Module

```python
from apps.services.models import Service
from apps.competitive.models import CompetitorService

def update_price_comparison(service_name):
    """Update our_price field for all competitor services."""
    try:
        our_service = Service.objects.get(name__iexact=service_name)
        CompetitorService.objects.filter(
            name__iexact=service_name
        ).update(our_price=our_service.base_price)
    except Service.DoesNotExist:
        pass
```

### With Dashboard/Reports

```python
def get_competitive_summary():
    """Generate competitive analysis summary."""
    from apps.competitive.models import Competitor, CompetitorService
    from django.db.models import Avg

    return {
        'total_competitors': Competitor.objects.filter(is_active=True).count(),
        'avg_competitor_rating': CompetitorReview.objects.filter(
            platform='google'
        ).aggregate(avg=Avg('rating')),
        'cheaper_services': CompetitorService.objects.filter(
            price_difference__lt=0
        ).count(),
        'pricier_services': CompetitorService.objects.filter(
            price_difference__gt=0
        ).count(),
    }
```

## Query Examples

```python
from apps.competitive.models import (
    Competitor, CompetitorService, CompetitorReview, MarketTrend
)
from django.db.models import Avg, Count

# Nearest competitors
nearby = Competitor.objects.filter(
    is_active=True,
    distance_km__lte=5
).order_by('distance_km')

# Competitors with better Google ratings than us
our_rating = Decimal('4.5')
better_rated = CompetitorReview.objects.filter(
    platform='google',
    rating__gt=our_rating
).select_related('competitor')

# Services where we're cheaper
competitive_advantage = CompetitorService.objects.filter(
    price_difference__gt=0  # Competitor more expensive
).order_by('-price_difference')

# Services where we're more expensive
price_risk = CompetitorService.objects.filter(
    price_difference__lt=0  # Competitor cheaper
).order_by('price_difference')

# High-impact trends requiring action
urgent_trends = MarketTrend.objects.filter(
    impact_level__in=['high', 'critical'],
    is_active=True,
    action_taken=''
)

# Average competitor rating by platform
ratings_by_platform = CompetitorReview.objects.values('platform').annotate(
    avg_rating=Avg('rating'),
    count=Count('id')
)

# Price changes in last 30 days
recent_changes = PriceHistory.objects.filter(
    captured_at__gte=timezone.now() - timedelta(days=30)
).select_related('service__competitor')
```

## Testing

Location: `tests/test_competitive.py`

```bash
python -m pytest tests/test_competitive.py -v
```
