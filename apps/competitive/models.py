"""Competitive Intelligence models."""
from django.db import models
from decimal import Decimal


class Competitor(models.Model):
    """Competitor veterinary clinic."""

    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    website = models.URLField(blank=True)
    email = models.EmailField(blank=True)

    # Location
    latitude = models.DecimalField(
        max_digits=10, decimal_places=7,
        null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=10, decimal_places=7,
        null=True, blank=True
    )
    distance_km = models.DecimalField(
        max_digits=6, decimal_places=2,
        null=True, blank=True
    )

    # Operating info
    hours = models.JSONField(default=dict, blank=True)
    services_offered = models.JSONField(default=list, blank=True)
    species_treated = models.JSONField(default=list, blank=True)

    # Social
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    google_maps_url = models.URLField(blank=True)

    # Notes
    notes = models.TextField(blank=True)
    strengths = models.TextField(blank=True)
    weaknesses = models.TextField(blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['distance_km', 'name']

    def __str__(self):
        return self.name


class CompetitorService(models.Model):
    """Service offered by a competitor with pricing."""

    competitor = models.ForeignKey(
        Competitor,
        on_delete=models.CASCADE,
        related_name='services'
    )
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)

    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    previous_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True
    )
    currency = models.CharField(max_length=3, default='MXN')
    price_updated_at = models.DateTimeField(auto_now=True)

    # Comparison to our price
    our_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True
    )
    price_difference = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ['competitor', 'name']

    def __str__(self):
        return f"{self.competitor.name}: {self.name}"

    def save(self, *args, **kwargs):
        if self.our_price and self.price:
            self.price_difference = self.price - self.our_price
        super().save(*args, **kwargs)


class CompetitorReview(models.Model):
    """Review/rating snapshot for a competitor."""

    PLATFORM_CHOICES = [
        ('google', 'Google'),
        ('facebook', 'Facebook'),
        ('yelp', 'Yelp'),
        ('other', 'Other'),
    ]

    competitor = models.ForeignKey(
        Competitor,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    rating = models.DecimalField(max_digits=2, decimal_places=1)
    review_count = models.IntegerField(default=0)
    sample_review = models.TextField(blank=True)

    # Tracking changes
    previous_rating = models.DecimalField(
        max_digits=2, decimal_places=1,
        null=True, blank=True
    )
    previous_review_count = models.IntegerField(null=True, blank=True)

    captured_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-captured_at']

    def __str__(self):
        return f"{self.competitor.name} - {self.platform}: {self.rating}"


class MarketTrend(models.Model):
    """Market trends and observations."""

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

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    impact_level = models.CharField(max_length=20, choices=IMPACT_CHOICES)
    source = models.CharField(max_length=200, blank=True)

    # Related competitors
    competitors = models.ManyToManyField(
        Competitor,
        blank=True,
        related_name='trends'
    )

    # Action items
    recommended_action = models.TextField(blank=True)
    action_taken = models.TextField(blank=True)
    action_date = models.DateField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.category}: {self.title}"


class PriceHistory(models.Model):
    """Historical price tracking."""

    service = models.ForeignKey(
        CompetitorService,
        on_delete=models.CASCADE,
        related_name='price_history'
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    captured_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-captured_at']

    def __str__(self):
        return f"{self.service}: {self.price} on {self.captured_at}"
