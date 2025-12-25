# Reviews Module

The `apps.reviews` module manages customer reviews, testimonials, and review request workflows for reputation management.

## Table of Contents

- [Overview](#overview)
- [Models](#models)
  - [Review](#review)
  - [ReviewRequest](#reviewrequest)
  - [Testimonial](#testimonial)
- [Workflows](#workflows)
- [Integration Points](#integration-points)
- [Query Examples](#query-examples)
- [Testing](#testing)

## Overview

The reviews module provides:

- **Customer Reviews** - User-submitted ratings and feedback
- **Review Requests** - Automated review solicitation
- **Testimonials** - Curated quotes for marketing
- **Multi-Platform** - Internal and external reviews (Google, Facebook)

## Models

Location: `apps/reviews/models.py`

### Review

Customer review/testimonial.

```python
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

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    pet = models.ForeignKey('pets.Pet', on_delete=models.SET_NULL, null=True)

    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default='internal')

    author_name = models.CharField(max_length=100, blank=True)
    author_location = models.CharField(max_length=100, blank=True)

    photo = models.ImageField(upload_to='reviews/', blank=True)
    video_url = models.URLField(blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_verified_purchase = models.BooleanField(default=False)

    response = models.TextField(blank=True)
    response_date = models.DateTimeField(null=True)
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    display_on_homepage = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `rating` | Integer | 1-5 star rating |
| `platform` | CharField | Source (internal, Google, etc.) |
| `status` | CharField | Approval workflow |
| `is_verified_purchase` | Boolean | Had real appointment |
| `response` | TextField | Clinic's public response |

### ReviewRequest

Request for review from customer.

```python
class ReviewRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pet = models.ForeignKey('pets.Pet', on_delete=models.SET_NULL, null=True)
    appointment = models.ForeignKey('appointments.Appointment', on_delete=models.SET_NULL, null=True)
    service_description = models.CharField(max_length=200, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True)
    sent_channel = models.CharField(max_length=20, blank=True)
    completed_at = models.DateTimeField(null=True)
    review = models.ForeignKey(Review, on_delete=models.SET_NULL, null=True)

    token = models.CharField(max_length=100, unique=True, blank=True)  # Auto-generated
```

### Testimonial

Curated testimonial for marketing.

```python
class Testimonial(models.Model):
    review = models.OneToOneField(Review, on_delete=models.CASCADE, null=True)

    author_name = models.CharField(max_length=100)
    author_title = models.CharField(max_length=100, blank=True)
    author_photo = models.ImageField(upload_to='testimonials/', blank=True)

    quote = models.TextField()
    short_quote = models.CharField(max_length=200, blank=True)

    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    show_on_homepage = models.BooleanField(default=False)
    show_on_services = models.BooleanField(default=False)

    tags = models.JSONField(default=list)
```

## Workflows

### Submitting a Review

```python
from apps.reviews.models import Review

review = Review.objects.create(
    user=user,
    pet=pet,
    rating=5,
    title='Excellent care!',
    content='The staff treated our dog like family.',
    status='pending',  # Awaits approval
    is_verified_purchase=True,
)
```

### Request-Based Review

```python
from apps.reviews.models import ReviewRequest, Review
from django.utils import timezone

# Create request after appointment
request = ReviewRequest.objects.create(
    user=customer,
    pet=pet,
    appointment=appointment,
    service_description='Vaccination visit',
)

# Send request
request.status = 'sent'
request.sent_at = timezone.now()
request.sent_channel = 'email'
request.save()

# Customer completes review
review = Review.objects.create(user=customer, ...)
request.status = 'completed'
request.completed_at = timezone.now()
request.review = review
request.save()
```

### Responding to Reviews

```python
from django.utils import timezone

review = Review.objects.get(pk=review_id)
review.response = 'Thank you for your kind words!'
review.response_date = timezone.now()
review.responded_by = staff_user
review.save()
```

## Integration Points

### With Appointments

```python
# After appointment completed
def on_appointment_completed(appointment):
    ReviewRequest.objects.create(
        user=appointment.owner,
        pet=appointment.pet,
        appointment=appointment,
    )
```

### With Homepage

```python
# Featured reviews for homepage
featured = Review.objects.filter(
    status='featured',
    display_on_homepage=True
).order_by('display_order')
```

## Query Examples

```python
from apps.reviews.models import Review, ReviewRequest, Testimonial
from django.db.models import Avg, Count

# Average rating
avg_rating = Review.objects.filter(status='approved').aggregate(avg=Avg('rating'))

# Reviews by rating
by_rating = Review.objects.filter(status='approved').values('rating').annotate(
    count=Count('id')
)

# Pending reviews
pending = Review.objects.filter(status='pending')

# Homepage testimonials
testimonials = Testimonial.objects.filter(
    is_active=True,
    show_on_homepage=True
).order_by('display_order')

# Outstanding review requests
pending_requests = ReviewRequest.objects.filter(
    status='sent',
    review__isnull=True
)
```

## Testing

Location: `tests/test_reviews.py`

```bash
python -m pytest tests/test_reviews.py -v
```
