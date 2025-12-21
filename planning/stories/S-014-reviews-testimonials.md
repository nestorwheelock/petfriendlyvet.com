# S-014: Reviews & Testimonials

**Story Type:** User Story
**Priority:** Medium
**Epoch:** 5 (with CRM)
**Status:** PENDING
**Module:** django-crm-lite

## User Story

**As a** pet owner
**I want to** share my experience with the clinic
**So that** others can learn about the quality of care

**As a** clinic owner
**I want to** collect and display client testimonials
**So that** I can build trust with potential clients

**As a** potential client
**I want to** read reviews from other pet owners
**So that** I can make an informed decision about choosing this clinic

## Acceptance Criteria

### Review Collection
- [ ] Request reviews after appointments (automated)
- [ ] Simple rating system (1-5 stars)
- [ ] Written review with optional photo
- [ ] Review specific aspects (service, staff, facility, value)
- [ ] Pet-specific reviews (link to pet and service)
- [ ] Multi-language review support

### Review Display
- [ ] Display reviews on website
- [ ] Filter by rating, date, service type
- [ ] Featured/pinned reviews
- [ ] Photo gallery from reviews
- [ ] Average rating display
- [ ] Review count and breakdown

### Google Integration
- [ ] Push reviews to Google Business Profile
- [ ] Import Google reviews
- [ ] Respond to Google reviews from dashboard
- [ ] Monitor new Google reviews

### Review Management
- [ ] Approve reviews before publishing
- [ ] Flag inappropriate content
- [ ] Respond to reviews publicly
- [ ] Private follow-up for negative reviews
- [ ] Review analytics and trends

### Social Proof
- [ ] Testimonial widgets for website
- [ ] Share reviews on social media
- [ ] Review badges/certificates
- [ ] "Verified client" badge

## Technical Requirements

### Models

```python
class ReviewRequest(models.Model):
    """Automated review request tracking"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('completed', 'Completed'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    pet = models.ForeignKey('vet_clinic.Pet', on_delete=models.CASCADE)
    appointment = models.ForeignKey(
        'appointments.Appointment', on_delete=models.CASCADE
    )

    # Request tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    token = models.CharField(max_length=64, unique=True)

    # Timing
    send_after = models.DateTimeField()  # e.g., 24 hours after appointment
    sent_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()

    # Result
    review = models.ForeignKey(
        'Review', on_delete=models.SET_NULL, null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)


class Review(models.Model):
    """Client review"""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('hidden', 'Hidden'),
    ]

    # Author
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    pet = models.ForeignKey(
        'vet_clinic.Pet', on_delete=models.SET_NULL, null=True, blank=True
    )
    is_verified = models.BooleanField(default=False)  # Verified client

    # Rating
    overall_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    service_rating = models.IntegerField(null=True, blank=True)
    staff_rating = models.IntegerField(null=True, blank=True)
    facility_rating = models.IntegerField(null=True, blank=True)
    value_rating = models.IntegerField(null=True, blank=True)

    # Content
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    language = models.CharField(max_length=10, default='es')

    # Context
    service_type = models.CharField(max_length=100, blank=True)
    # consultation, vaccination, surgery, grooming, etc.
    visit_date = models.DateField(null=True, blank=True)

    # Media
    photos = models.JSONField(default=list)  # List of photo URLs

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    moderated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='moderated_reviews'
    )
    moderated_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    # Display
    is_featured = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)

    # Engagement
    helpful_count = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']


class ReviewPhoto(models.Model):
    """Photos attached to reviews"""
    review = models.ForeignKey(Review, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='reviews/photos/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class ReviewResponse(models.Model):
    """Clinic response to a review"""
    review = models.OneToOneField(Review, on_delete=models.CASCADE)
    content = models.TextField()
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class GoogleReview(models.Model):
    """Imported Google Business reviews"""
    google_review_id = models.CharField(max_length=100, unique=True)
    author_name = models.CharField(max_length=200)
    author_photo_url = models.URLField(blank=True)
    rating = models.IntegerField()
    text = models.TextField(blank=True)
    language = models.CharField(max_length=10)
    time = models.DateTimeField()

    # Response
    reply_text = models.TextField(blank=True)
    reply_time = models.DateTimeField(null=True, blank=True)
    reply_synced = models.BooleanField(default=False)

    # Matching
    matched_owner = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    # Sync tracking
    last_synced_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ReviewStats(models.Model):
    """Aggregated review statistics (cached)"""
    date = models.DateField(unique=True)

    total_reviews = models.IntegerField(default=0)
    average_rating = models.FloatField(default=0)

    # By rating
    rating_5_count = models.IntegerField(default=0)
    rating_4_count = models.IntegerField(default=0)
    rating_3_count = models.IntegerField(default=0)
    rating_2_count = models.IntegerField(default=0)
    rating_1_count = models.IntegerField(default=0)

    # By aspect
    avg_service_rating = models.FloatField(null=True)
    avg_staff_rating = models.FloatField(null=True)
    avg_facility_rating = models.FloatField(null=True)
    avg_value_rating = models.FloatField(null=True)

    # By service type
    ratings_by_service = models.JSONField(default=dict)

    updated_at = models.DateTimeField(auto_now=True)


class TestimonialWidget(models.Model):
    """Configurable testimonial display widgets"""
    name = models.CharField(max_length=100)
    widget_type = models.CharField(max_length=50)
    # carousel, grid, single, sidebar

    # Content selection
    filter_min_rating = models.IntegerField(default=4)
    filter_verified_only = models.BooleanField(default=False)
    filter_with_photos = models.BooleanField(default=False)
    filter_service_types = models.JSONField(default=list)
    max_reviews = models.IntegerField(default=6)

    # Display options
    show_photos = models.BooleanField(default=True)
    show_pet_name = models.BooleanField(default=True)
    show_service_type = models.BooleanField(default=True)
    show_date = models.BooleanField(default=True)
    auto_rotate = models.BooleanField(default=True)
    rotation_speed_ms = models.IntegerField(default=5000)

    # Styling
    custom_css = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### AI Tools

```python
REVIEW_TOOLS = [
    {
        "name": "get_review_stats",
        "description": "Get review statistics and ratings overview",
        "parameters": {
            "type": "object",
            "properties": {
                "date_range": {"type": "string"},
                "service_type": {"type": "string"}
            }
        }
    },
    {
        "name": "get_recent_reviews",
        "description": "Get recent reviews",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 10},
                "min_rating": {"type": "integer"},
                "status": {"type": "string"}
            }
        }
    },
    {
        "name": "respond_to_review",
        "description": "Respond to a client review",
        "parameters": {
            "type": "object",
            "properties": {
                "review_id": {"type": "integer"},
                "response": {"type": "string"},
                "is_public": {"type": "boolean", "default": True}
            },
            "required": ["review_id", "response"]
        }
    },
    {
        "name": "moderate_review",
        "description": "Approve or reject a pending review",
        "parameters": {
            "type": "object",
            "properties": {
                "review_id": {"type": "integer"},
                "action": {"type": "string", "enum": ["approve", "reject", "hide"]},
                "reason": {"type": "string"}
            },
            "required": ["review_id", "action"]
        }
    },
    {
        "name": "feature_review",
        "description": "Mark a review as featured",
        "parameters": {
            "type": "object",
            "properties": {
                "review_id": {"type": "integer"},
                "featured": {"type": "boolean"}
            },
            "required": ["review_id", "featured"]
        }
    },
    {
        "name": "sync_google_reviews",
        "description": "Sync reviews from Google Business Profile",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "analyze_review_sentiment",
        "description": "Analyze sentiment trends in reviews",
        "parameters": {
            "type": "object",
            "properties": {
                "date_range": {"type": "string"}
            }
        }
    }
]
```

## Example AI Conversations

### Review Request (Customer)
```
AI (WhatsApp, 24hr after appointment):
    Hola Maria! 🐕

    Thank you for bringing Luna in yesterday for her
    vaccination. We hope everything went well!

    Would you mind sharing your experience?
    Your feedback helps other pet owners and helps
    us improve our service.

    [Leave a Review ⭐] [Not Now]

Owner: [Clicks Leave a Review]

AI: Thank you for taking the time!

    How would you rate your experience?
    ⭐⭐⭐⭐⭐

Owner: ⭐⭐⭐⭐⭐

AI: Wonderful! 5 stars!

    Would you like to add a few words about your
    experience? (Optional but really appreciated!)

Owner: Dr. Pablo was so gentle with Luna. She usually
       hates the vet but she was calm the whole time.
       The clinic is clean and the staff are very friendly.

AI: Thank you so much for the kind words, Maria!

    📸 Would you like to add a photo of Luna?
    (Photos help other pet owners connect with your story)

    [Add Photo] [Skip]

Owner: [Adds photo]

AI: Your review has been submitted!

    ⭐⭐⭐⭐⭐
    "Dr. Pablo was so gentle with Luna..."

    Thank you for being a valued client at Pet-Friendly!
    Luna is lucky to have such a caring owner. 🐕💚
```

### Managing Reviews (Admin)
```
Dr. Pablo: Show me recent reviews

AI: Here are your reviews from the past 30 days:

    📊 Overview:
    • Total: 12 reviews
    • Average: 4.8 ⭐
    • Pending moderation: 2

    ⭐⭐⭐⭐⭐ (8 reviews)
    ⭐⭐⭐⭐ (3 reviews)
    ⭐⭐⭐ (1 review)

    Recent Reviews:

    1. Maria G. - 5⭐ - Yesterday
       "Dr. Pablo was so gentle with Luna..."
       Status: Approved ✓

    2. Carlos M. - 5⭐ - 2 days ago
       "Best vet in Puerto Morelos!"
       Status: Pending ⏳

    3. Susan T. - 3⭐ - 5 days ago
       "Good service but had to wait 30 minutes"
       Status: Approved ✓ | No response yet

    Would you like to:
    1. Approve pending reviews
    2. Respond to a review
    3. See detailed analytics

Dr. Pablo: Respond to Susan's review

AI: Here's Susan's full review:

    ⭐⭐⭐ (January 18, 2026)
    Pet: Whiskers (cat)
    Service: Checkup

    "Good service but had to wait 30 minutes past
    my appointment time. Dr. Pablo was great once
    we got in, but the wait was frustrating with
    a nervous cat."

    Suggested response:
    "Dear Susan, thank you for your feedback and
    we sincerely apologize for the wait. We had an
    emergency that day that caused delays. We're
    working on better communication when this happens.
    We hope Whiskers is doing well!"

    Would you like to:
    1. Use this response
    2. Edit and customize
    3. Write your own
```

### Review Analytics
```
Dr. Pablo: How are we doing on reviews?

AI: 📊 Review Analytics (Last 90 Days)

    Overall Performance:
    ⭐ 4.8 average (from 45 reviews)
    📈 Up from 4.6 last quarter

    Rating Breakdown:
    ⭐⭐⭐⭐⭐  ████████████  34 (76%)
    ⭐⭐⭐⭐    ████          8 (18%)
    ⭐⭐⭐      █             2 (4%)
    ⭐⭐        -             1 (2%)
    ⭐         -             0 (0%)

    Aspect Ratings:
    • Staff friendliness: 4.9 ⭐
    • Veterinary care: 4.8 ⭐
    • Facility cleanliness: 4.7 ⭐
    • Value for money: 4.5 ⭐
    • Wait time: 4.2 ⭐ ⚠️

    Top Mentioned Keywords:
    ✓ "gentle" (12 mentions)
    ✓ "professional" (10 mentions)
    ✓ "friendly" (9 mentions)
    ⚠️ "wait" (5 mentions)

    Insight: Wait time is your lowest-rated aspect.
    Consider improving scheduling or communication
    about delays.

    Google Reviews:
    • 4.9 ⭐ on Google (66 reviews)
    • Last synced: Today at 9:00 AM
    • 2 new Google reviews to respond to
```

## Review Request Automation

### Trigger Rules
```python
REVIEW_REQUEST_RULES = {
    'vaccination': {
        'delay_hours': 24,
        'min_days_since_last_request': 90,
    },
    'consultation': {
        'delay_hours': 48,
        'min_days_since_last_request': 60,
    },
    'surgery': {
        'delay_hours': 72,  # Wait for recovery
        'min_days_since_last_request': 180,
    },
    'emergency': {
        'delay_hours': 72,
        'min_days_since_last_request': 90,
    },
}
```

## Definition of Done

- [ ] Review request automation
- [ ] Review submission flow
- [ ] Multi-aspect ratings
- [ ] Photo uploads with reviews
- [ ] Review moderation queue
- [ ] Public responses
- [ ] Google Business integration
- [ ] Review widgets for website
- [ ] Analytics dashboard
- [ ] Sentiment analysis
- [ ] Tests written and passing (>95% coverage)

## Dependencies

- S-004: Appointments (trigger reviews)
- S-006: Omnichannel (send requests)
- S-007: CRM (owner profiles)

## Notes

- Google Business API requires verification
- Consider incentives for reviews (carefully - against Google TOS)
- Respond to negative reviews promptly
- Feature diverse reviews (different pets, services)
- Consider video testimonials (future)
