# T-054: CRM Owner Profile Models

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement enhanced owner profiles with CRM data
**Related Story**: S-007
**Epoch**: 5
**Estimate**: 4 hours

### Constraints
**Allowed File Paths**: apps/crm/
**Forbidden Paths**: None

### Deliverables
- [ ] OwnerProfile model
- [ ] Interaction tracking
- [ ] Communication preferences
- [ ] Lifetime value calculation
- [ ] Segmentation fields

### Wireframe Reference
See: `planning/wireframes/19-crm-dashboard.txt`

### Implementation Details

#### Models
```python
from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count

User = get_user_model()


class OwnerProfile(models.Model):
    """Extended profile for pet owners (CRM data)."""

    owner = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name='crm_profile'
    )

    # Demographics
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, blank=True)
    occupation = models.CharField(max_length=200, blank=True)

    # Contact
    phone = models.CharField(max_length=20, blank=True)
    phone_secondary = models.CharField(max_length=20, blank=True)
    whatsapp = models.CharField(max_length=20, blank=True)

    # Address
    street_address = models.TextField(blank=True)
    neighborhood = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, default='Puerto Morelos')
    postal_code = models.CharField(max_length=10, blank=True)
    location_notes = models.TextField(blank=True)

    # How they found us
    SOURCE_CHOICES = [
        ('referral', 'Referido'),
        ('google', 'Google'),
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('walk_in', 'Pasó por aquí'),
        ('event', 'Evento'),
        ('other', 'Otro'),
    ]
    acquisition_source = models.CharField(
        max_length=20, choices=SOURCE_CHOICES, blank=True
    )
    acquisition_detail = models.CharField(max_length=200, blank=True)
    referred_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='referrals_made'
    )

    # Customer tier
    TIER_CHOICES = [
        ('new', 'Nuevo'),
        ('regular', 'Regular'),
        ('vip', 'VIP'),
        ('professional', 'Profesional'),
    ]
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='new')

    # Engagement scores
    engagement_score = models.IntegerField(default=0)
    # Calculated from visits, purchases, interactions
    last_engagement_date = models.DateField(null=True, blank=True)

    # Spending
    lifetime_value = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )
    average_order_value = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )

    # Dates
    first_visit_date = models.DateField(null=True, blank=True)
    last_visit_date = models.DateField(null=True, blank=True)
    total_visits = models.IntegerField(default=0)

    # Risk indicators
    churn_risk = models.CharField(max_length=20, choices=[
        ('low', 'Bajo'),
        ('medium', 'Medio'),
        ('high', 'Alto'),
    ], default='low')
    days_since_last_visit = models.IntegerField(null=True, blank=True)

    # Preferences
    preferred_language = models.CharField(max_length=5, default='es')
    preferred_contact_time = models.CharField(max_length=50, blank=True)
    # 'morning', 'afternoon', 'evening'

    # Marketing
    email_opt_in = models.BooleanField(default=False)
    sms_opt_in = models.BooleanField(default=False)
    whatsapp_opt_in = models.BooleanField(default=True)

    # Tags for segmentation
    tags = models.JSONField(default=list)
    # ['dog-owner', 'premium', 'boarder', ...]

    # Notes
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_lifetime_value(self):
        """Calculate LTV from orders and appointments."""
        from apps.store.models import Order
        from apps.billing.models import Invoice

        order_total = Order.objects.filter(
            user=self.owner,
            payment_status='paid'
        ).aggregate(total=Sum('total'))['total'] or 0

        invoice_total = Invoice.objects.filter(
            owner=self.owner,
            status='paid'
        ).aggregate(total=Sum('total'))['total'] or 0

        self.lifetime_value = order_total + invoice_total
        self.save(update_fields=['lifetime_value'])

    def calculate_engagement_score(self):
        """Calculate engagement score."""
        score = 0

        # Visits (up to 30 points)
        score += min(self.total_visits * 3, 30)

        # Recency (up to 30 points)
        if self.days_since_last_visit:
            if self.days_since_last_visit < 30:
                score += 30
            elif self.days_since_last_visit < 90:
                score += 20
            elif self.days_since_last_visit < 180:
                score += 10

        # Spending (up to 20 points)
        if self.lifetime_value > 10000:
            score += 20
        elif self.lifetime_value > 5000:
            score += 15
        elif self.lifetime_value > 1000:
            score += 10

        # Interactions (up to 20 points)
        interactions = OwnerInteraction.objects.filter(
            owner=self.owner
        ).count()
        score += min(interactions, 20)

        self.engagement_score = score
        self.save(update_fields=['engagement_score'])

    def update_churn_risk(self):
        """Update churn risk based on activity."""
        if self.days_since_last_visit:
            if self.days_since_last_visit > 180:
                self.churn_risk = 'high'
            elif self.days_since_last_visit > 90:
                self.churn_risk = 'medium'
            else:
                self.churn_risk = 'low'
        self.save(update_fields=['churn_risk'])


class OwnerInteraction(models.Model):
    """Track interactions with owners."""

    INTERACTION_TYPES = [
        ('visit', 'Visita'),
        ('call_in', 'Llamada entrante'),
        ('call_out', 'Llamada saliente'),
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
        ('sms', 'SMS'),
        ('ai_chat', 'Chat AI'),
        ('review', 'Reseña'),
        ('complaint', 'Queja'),
        ('feedback', 'Retroalimentación'),
        ('referral', 'Referido cliente'),
    ]

    owner = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='interactions'
    )

    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    direction = models.CharField(max_length=10, choices=[
        ('inbound', 'Entrante'),
        ('outbound', 'Saliente'),
    ], default='inbound')

    subject = models.CharField(max_length=500, blank=True)
    summary = models.TextField(blank=True)
    outcome = models.CharField(max_length=200, blank=True)

    # Related records
    pet = models.ForeignKey('vet_clinic.Pet', on_delete=models.SET_NULL, null=True, blank=True)
    appointment = models.ForeignKey('appointments.Appointment', on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey('store.Order', on_delete=models.SET_NULL, null=True, blank=True)
    conversation = models.ForeignKey('communications.Conversation', on_delete=models.SET_NULL, null=True, blank=True)

    # Sentiment
    sentiment = models.CharField(max_length=20, choices=[
        ('positive', 'Positivo'),
        ('neutral', 'Neutral'),
        ('negative', 'Negativo'),
    ], blank=True)

    # Staff
    handled_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+'
    )

    # Follow-up
    requires_follow_up = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    follow_up_completed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class CustomerSegment(models.Model):
    """Customer segments for marketing."""

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    # Rules (JSON for flexible filtering)
    rules = models.JSONField(default=dict)
    # {
    #   "tier": ["vip"],
    #   "tags": ["dog-owner"],
    #   "lifetime_value_min": 5000,
    #   "days_since_visit_max": 90,
    # }

    # Caching
    member_count = models.IntegerField(default=0)
    last_updated = models.DateTimeField(null=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_members(self):
        """Get owners matching segment rules."""
        queryset = OwnerProfile.objects.all()

        rules = self.rules

        if 'tier' in rules:
            queryset = queryset.filter(tier__in=rules['tier'])

        if 'tags' in rules:
            for tag in rules['tags']:
                queryset = queryset.filter(tags__contains=[tag])

        if 'lifetime_value_min' in rules:
            queryset = queryset.filter(
                lifetime_value__gte=rules['lifetime_value_min']
            )

        if 'lifetime_value_max' in rules:
            queryset = queryset.filter(
                lifetime_value__lte=rules['lifetime_value_max']
            )

        if 'days_since_visit_max' in rules:
            queryset = queryset.filter(
                days_since_last_visit__lte=rules['days_since_visit_max']
            )

        if 'churn_risk' in rules:
            queryset = queryset.filter(churn_risk__in=rules['churn_risk'])

        if 'email_opt_in' in rules:
            queryset = queryset.filter(email_opt_in=rules['email_opt_in'])

        return queryset

    def update_count(self):
        """Update cached member count."""
        self.member_count = self.get_members().count()
        self.last_updated = timezone.now()
        self.save(update_fields=['member_count', 'last_updated'])
```

### Test Cases
- [ ] Profile creation works
- [ ] LTV calculation accurate
- [ ] Engagement score calculated
- [ ] Churn risk updates
- [ ] Interaction logging works
- [ ] Segment rules filter correctly
- [ ] Referral tracking works

### Definition of Done
- [ ] All models migrated
- [ ] Signals for auto-updates
- [ ] Admin interface complete
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-001: Django Project Setup
