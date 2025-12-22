# T-056: Competitive Intelligence Models

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement competitor tracking and analysis
**Related Story**: S-009
**Epoch**: 5
**Estimate**: 3 hours

### Constraints
**Allowed File Paths**: apps/competitive/
**Forbidden Paths**: None

### Deliverables
- [ ] Competitor model
- [ ] PriceTracking model
- [ ] ReviewMonitor model
- [ ] MarketAlert model
- [ ] Visitor tracking

### Wireframe Reference
See: `planning/wireframes/10-competitive-intelligence.txt`

### Implementation Details

#### Models
```python
from django.db import models


class Competitor(models.Model):
    """Competing veterinary clinics."""

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)

    # Location
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True)
    distance_km = models.DecimalField(max_digits=6, decimal_places=1, null=True)

    # Contact
    phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    email = models.EmailField(blank=True)

    # Social
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    google_maps_url = models.URLField(blank=True)

    # Business info
    hours = models.JSONField(default=dict, blank=True)
    services = models.TextField(blank=True)

    # Ratings
    google_rating = models.DecimalField(
        max_digits=2, decimal_places=1, null=True
    )
    google_review_count = models.IntegerField(null=True)
    facebook_rating = models.DecimalField(
        max_digits=2, decimal_places=1, null=True
    )

    # Competitive positioning
    strengths = models.TextField(blank=True)
    weaknesses = models.TextField(blank=True)
    threat_level = models.CharField(max_length=20, choices=[
        ('low', 'Bajo'),
        ('medium', 'Medio'),
        ('high', 'Alto'),
    ], default='medium')

    is_active = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)


class CompetitorPrice(models.Model):
    """Track competitor pricing."""

    competitor = models.ForeignKey(
        Competitor, on_delete=models.CASCADE,
        related_name='prices'
    )

    service_name = models.CharField(max_length=200)
    our_service = models.ForeignKey(
        'appointments.ServiceType',
        on_delete=models.SET_NULL, null=True, blank=True
    )

    competitor_price = models.DecimalField(max_digits=10, decimal_places=2)
    our_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    price_difference = models.DecimalField(
        max_digits=10, decimal_places=2, null=True
    )
    price_difference_percent = models.DecimalField(
        max_digits=5, decimal_places=2, null=True
    )

    source = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)

    recorded_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_date']


class CompetitorReview(models.Model):
    """Monitor competitor reviews."""

    competitor = models.ForeignKey(
        Competitor, on_delete=models.CASCADE,
        related_name='reviews'
    )

    platform = models.CharField(max_length=20, choices=[
        ('google', 'Google'),
        ('facebook', 'Facebook'),
        ('yelp', 'Yelp'),
    ])

    rating = models.IntegerField()  # 1-5
    review_text = models.TextField()
    reviewer_name = models.CharField(max_length=200, blank=True)

    # Analysis
    sentiment = models.CharField(max_length=20, choices=[
        ('positive', 'Positivo'),
        ('neutral', 'Neutral'),
        ('negative', 'Negativo'),
    ], blank=True)
    key_themes = models.JSONField(default=list)
    # ['wait time', 'price', 'staff', 'cleanliness', ...]

    review_date = models.DateField()
    captured_at = models.DateTimeField(auto_now_add=True)


class MarketAlert(models.Model):
    """Alerts about competitor activity."""

    ALERT_TYPES = [
        ('new_service', 'Nuevo servicio'),
        ('price_change', 'Cambio de precio'),
        ('promotion', 'Promoción'),
        ('new_location', 'Nueva ubicación'),
        ('review_spike', 'Aumento en reseñas'),
        ('social_campaign', 'Campaña en redes'),
        ('other', 'Otro'),
    ]

    competitor = models.ForeignKey(
        Competitor, on_delete=models.CASCADE,
        null=True, blank=True, related_name='alerts'
    )

    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    title = models.CharField(max_length=500)
    description = models.TextField()
    source_url = models.URLField(blank=True)

    severity = models.CharField(max_length=20, choices=[
        ('info', 'Informativo'),
        ('watch', 'Vigilar'),
        ('action', 'Acción requerida'),
    ], default='info')

    is_read = models.BooleanField(default=False)
    is_actionable = models.BooleanField(default=False)
    action_taken = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class VisitorIntel(models.Model):
    """Track visitor information for competitive intel."""

    # Session
    session_key = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()

    # Location (from IP)
    city = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)

    # Organization (from IP)
    organization = models.CharField(max_length=200, blank=True)
    is_competitor = models.BooleanField(default=False)
    competitor = models.ForeignKey(
        Competitor, on_delete=models.SET_NULL,
        null=True, blank=True
    )

    # Behavior
    pages_viewed = models.JSONField(default=list)
    services_viewed = models.JSONField(default=list)
    products_viewed = models.JSONField(default=list)

    referrer = models.URLField(blank=True)
    user_agent = models.CharField(max_length=500, blank=True)

    first_visit = models.DateTimeField(auto_now_add=True)
    last_visit = models.DateTimeField(auto_now=True)
    visit_count = models.IntegerField(default=1)

    class Meta:
        ordering = ['-last_visit']
```

### Test Cases
- [ ] Competitor CRUD works
- [ ] Price tracking records
- [ ] Review capture works
- [ ] Alerts created correctly
- [ ] Visitor tracking records
- [ ] IP lookup works
- [ ] Competitor flagging works

### Definition of Done
- [ ] All models migrated
- [ ] Admin interface for management
- [ ] IP geolocation integrated
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-001: Django Project Setup
