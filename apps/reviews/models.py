"""Reviews and Testimonials models."""
from django.conf import settings
from django.db import models


class Review(models.Model):
    """Customer review/testimonial."""

    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('featured', 'Featured'),
        ('rejected', 'Rejected'),
    ]

    PLATFORM_CHOICES = [
        ('internal', 'Website'),
        ('google', 'Google'),
        ('facebook', 'Facebook'),
        ('yelp', 'Yelp'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviews'
    )
    pet = models.ForeignKey(
        'pets.Pet',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviews'
    )

    # Review details
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    platform = models.CharField(
        max_length=20,
        choices=PLATFORM_CHOICES,
        default='internal'
    )

    # Author info (for external or anonymous)
    author_name = models.CharField(max_length=100, blank=True)
    author_location = models.CharField(max_length=100, blank=True)

    # Media
    photo = models.ImageField(upload_to='reviews/', blank=True, null=True)
    video_url = models.URLField(blank=True)

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    is_verified_purchase = models.BooleanField(default=False)

    # Response
    response = models.TextField(blank=True)
    response_date = models.DateTimeField(null=True, blank=True)
    responded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='review_responses'
    )

    # SEO
    display_on_homepage = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        author = self.author_name or (self.user.get_full_name() if self.user else 'Anonymous')
        return f"{author}: {self.rating} stars"

    @property
    def author(self):
        if self.author_name:
            return self.author_name
        if self.user:
            return self.user.get_full_name() or self.user.email
        return 'Anonymous'


class ReviewRequest(models.Model):
    """Request for review from customer."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('completed', 'Completed'),
        ('declined', 'Declined'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='review_requests'
    )
    pet = models.ForeignKey(
        'pets.Pet',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Related to appointment or service
    appointment = models.ForeignKey(
        'appointments.Appointment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    service_description = models.CharField(max_length=200, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # Tracking
    sent_at = models.DateTimeField(null=True, blank=True)
    sent_channel = models.CharField(max_length=20, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    review = models.ForeignKey(
        Review,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Token for anonymous review submission
    token = models.CharField(max_length=100, unique=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review request for {self.user.email}"

    def save(self, *args, **kwargs):
        if not self.token:
            import uuid
            self.token = str(uuid.uuid4())
        super().save(*args, **kwargs)


class Testimonial(models.Model):
    """Curated testimonial for marketing."""

    review = models.OneToOneField(
        Review,
        on_delete=models.CASCADE,
        related_name='testimonial',
        null=True,
        blank=True
    )

    # Can be manually created without linked review
    author_name = models.CharField(max_length=100)
    author_title = models.CharField(max_length=100, blank=True)
    author_photo = models.ImageField(upload_to='testimonials/', blank=True, null=True)

    quote = models.TextField()
    short_quote = models.CharField(max_length=200, blank=True)

    # Display settings
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    show_on_homepage = models.BooleanField(default=False)
    show_on_services = models.BooleanField(default=False)

    # Tags for filtering
    tags = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', '-created_at']

    def __str__(self):
        return f"{self.author_name}: {self.short_quote or self.quote[:50]}"
