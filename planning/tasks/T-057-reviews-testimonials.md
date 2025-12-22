# T-057: Reviews & Testimonials System

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Full Stack Developer
**Objective**: Implement review collection and display system
**Related Story**: S-014
**Epoch**: 5
**Estimate**: 4 hours

### Constraints
**Allowed File Paths**: apps/reviews/, templates/
**Forbidden Paths**: None

### Deliverables
- [ ] Review model
- [ ] Review request workflow
- [ ] Review display widget
- [ ] Google/Facebook sync (read)
- [ ] Moderation interface

### Implementation Details

#### Models
```python
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Review(models.Model):
    """Customer reviews."""

    PLATFORMS = [
        ('internal', 'Sitio web'),
        ('google', 'Google'),
        ('facebook', 'Facebook'),
    ]

    # Author
    owner = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reviews_written'
    )
    reviewer_name = models.CharField(max_length=200)
    reviewer_email = models.EmailField(blank=True)

    # Platform
    platform = models.CharField(max_length=20, choices=PLATFORMS, default='internal')
    external_id = models.CharField(max_length=200, blank=True)

    # Rating and content
    rating = models.IntegerField()  # 1-5
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField()

    # Response
    response = models.TextField(blank=True)
    responded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+'
    )
    responded_at = models.DateTimeField(null=True)

    # Related
    pet = models.ForeignKey(
        'vet_clinic.Pet', on_delete=models.SET_NULL,
        null=True, blank=True
    )
    service = models.ForeignKey(
        'appointments.ServiceType', on_delete=models.SET_NULL,
        null=True, blank=True
    )
    product = models.ForeignKey(
        'store.Product', on_delete=models.SET_NULL,
        null=True, blank=True
    )

    # Moderation
    is_approved = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    moderated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+'
    )
    moderated_at = models.DateTimeField(null=True)
    moderation_notes = models.TextField(blank=True)

    # Display
    show_on_homepage = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)

    review_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-review_date']


class ReviewRequest(models.Model):
    """Request for review after service."""

    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    pet = models.ForeignKey('vet_clinic.Pet', on_delete=models.SET_NULL, null=True)
    appointment = models.ForeignKey(
        'appointments.Appointment', on_delete=models.SET_NULL,
        null=True, blank=True
    )
    order = models.ForeignKey(
        'store.Order', on_delete=models.SET_NULL,
        null=True, blank=True
    )

    # Request tracking
    requested_at = models.DateTimeField(auto_now_add=True)
    request_channel = models.CharField(max_length=20)  # email, sms, whatsapp
    message = models.ForeignKey(
        'communications.Message', on_delete=models.SET_NULL,
        null=True, blank=True
    )

    # Response
    review = models.ForeignKey(
        Review, on_delete=models.SET_NULL,
        null=True, blank=True
    )
    responded_at = models.DateTimeField(null=True)
    clicked_google = models.BooleanField(default=False)
    clicked_facebook = models.BooleanField(default=False)

    # Follow-up
    reminder_sent = models.BooleanField(default=False)
    reminder_sent_at = models.DateTimeField(null=True)


class Testimonial(models.Model):
    """Curated testimonials for marketing."""

    review = models.OneToOneField(
        Review, on_delete=models.SET_NULL,
        null=True, blank=True
    )

    # Or manual entry
    client_name = models.CharField(max_length=200)
    pet_name = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    photo = models.ImageField(upload_to='testimonials/', null=True, blank=True)

    # Display
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    show_on_homepage = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_order']
```

#### Review Request Service
```python
class ReviewRequestService:
    """Send review requests after service."""

    def request_review(
        self,
        owner,
        pet=None,
        appointment=None,
        order=None,
        delay_hours: int = 24
    ):
        """Schedule review request."""

        from apps.reviews.tasks import send_review_request

        request = ReviewRequest.objects.create(
            owner=owner,
            pet=pet,
            appointment=appointment,
            order=order,
            request_channel='email'  # or determine from preferences
        )

        # Schedule for later
        send_review_request.apply_async(
            args=[request.id],
            countdown=delay_hours * 3600
        )

        return request

    def get_review_links(self, request: ReviewRequest) -> dict:
        """Get review links for request."""
        return {
            'internal': f'/reviews/submit/?request={request.id}',
            'google': 'https://g.page/r/...',  # Pet-Friendly's Google review link
            'facebook': 'https://facebook.com/petfriendly/reviews/'
        }


@shared_task
def send_review_request(request_id: int):
    """Send review request email."""
    from apps.reviews.models import ReviewRequest
    from apps.communications.services.email import EmailService

    request = ReviewRequest.objects.get(id=request_id)

    service = ReviewRequestService()
    links = service.get_review_links(request)

    # Send email
    EmailService().send_template(
        to_email=request.owner.email,
        template_name='review_request',
        context={
            'owner_name': request.owner.first_name,
            'pet_name': request.pet.name if request.pet else '',
            'internal_link': links['internal'],
            'google_link': links['google'],
            'facebook_link': links['facebook'],
        }
    )

    request.requested_at = timezone.now()
    request.save()
```

#### Views
```python
class ReviewSubmitView(CreateView):
    """Public review submission."""

    model = Review
    template_name = 'reviews/submit.html'
    fields = ['rating', 'title', 'content']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request_id = self.request.GET.get('request')
        if request_id:
            context['review_request'] = ReviewRequest.objects.get(id=request_id)
        return context

    def form_valid(self, form):
        request_id = self.request.GET.get('request')
        if request_id:
            review_request = ReviewRequest.objects.get(id=request_id)
            form.instance.owner = review_request.owner
            form.instance.reviewer_name = review_request.owner.get_full_name()
            form.instance.pet = review_request.pet

            review_request.responded_at = timezone.now()
            review_request.save()

        form.instance.platform = 'internal'
        form.instance.review_date = timezone.now().date()

        return super().form_valid(form)


class ReviewModerationView(LoginRequiredMixin, UpdateView):
    """Moderate pending reviews."""

    model = Review
    template_name = 'admin/reviews/moderate.html'
    fields = ['is_approved', 'is_featured', 'response', 'moderation_notes']

    def form_valid(self, form):
        form.instance.moderated_by = self.request.user
        form.instance.moderated_at = timezone.now()
        if form.cleaned_data.get('response'):
            form.instance.responded_by = self.request.user
            form.instance.responded_at = timezone.now()
        return super().form_valid(form)
```

### Test Cases
- [ ] Review submission works
- [ ] Review request sends
- [ ] Moderation works
- [ ] Featured reviews display
- [ ] Response saves correctly
- [ ] Link tracking works

### Definition of Done
- [ ] Full review workflow
- [ ] Email templates created
- [ ] Moderation interface complete
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-045: Email Integration
- T-024: Pet Models
