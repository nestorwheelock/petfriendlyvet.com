# Core Module

The `apps.core` module provides foundational abstract models, base classes, and public-facing pages (homepage, about, contact) for the Pet-Friendly Vet application.

## Table of Contents

- [Overview](#overview)
- [Abstract Models](#abstract-models)
  - [TimeStampedModel](#timestampedmodel)
  - [UUIDModel](#uuidmodel)
  - [SoftDeleteModel](#softdeletemodel)
  - [BaseModel](#basemodel)
- [Concrete Models](#concrete-models)
  - [ContactSubmission](#contactsubmission)
- [Views](#views)
- [URL Patterns](#url-patterns)
- [Workflows](#workflows)
  - [Contact Form Submission](#contact-form-submission)
  - [Soft Delete Pattern](#soft-delete-pattern)
- [Spam Prevention](#spam-prevention)
- [Integration Points](#integration-points)
- [Query Examples](#query-examples)
- [Testing](#testing)

## Overview

The core module provides:

- **Abstract Base Models** - Reusable model patterns (timestamps, UUIDs, soft delete)
- **Public Pages** - Homepage, about, services, contact
- **Contact Form** - Customer inquiries with spam prevention
- **Health Check** - Load balancer endpoint
- **CSRF Handler** - Custom CSRF failure page

```
┌─────────────────────────────────────────────────────────────┐
│                    CORE MODULE                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              ABSTRACT BASE MODELS                    │    │
│  ├─────────────┬─────────────┬─────────────────────────┤    │
│  │ Timestamped │   UUID      │    SoftDelete           │    │
│  │  Model      │  Model      │     Model               │    │
│  └──────┬──────┴──────┬──────┴──────────┬──────────────┘    │
│         │             │                 │                    │
│         └─────────────┴─────────────────┘                    │
│                       │                                      │
│                       ▼                                      │
│         ┌─────────────────────────┐                         │
│         │      BaseModel          │                         │
│         │  (Timestamps + Soft)    │                         │
│         └─────────────────────────┘                         │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                PUBLIC PAGES                          │    │
│  ├──────────┬──────────┬──────────┬───────────────────┤    │
│  │   Home   │  About   │ Services │     Contact        │    │
│  └──────────┴──────────┴──────────┴───────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Abstract Models

Location: `apps/core/models.py`

These abstract models are inherited by models throughout the application.

### TimeStampedModel

Adds automatic created/updated timestamps.

```python
class TimeStampedModel(models.Model):
    """Abstract base model with created/updated timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
```

**Usage:**

```python
from apps.core.models import TimeStampedModel

class MyModel(TimeStampedModel):
    name = models.CharField(max_length=100)

# Automatic fields:
# - created_at: Set once on creation
# - updated_at: Updated on every save
```

### UUIDModel

Uses UUID as primary key instead of auto-increment integer.

```python
class UUIDModel(models.Model):
    """Abstract base model with UUID primary key."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True
```

**Usage:**

```python
from apps.core.models import UUIDModel

class SecureModel(UUIDModel):
    data = models.TextField()

# Primary key is UUID:
# obj.pk = '550e8400-e29b-41d4-a716-446655440000'
```

### SoftDeleteModel

Implements soft delete pattern - records are marked as deleted rather than removed.

```python
class SoftDeleteManager(models.Manager):
    """Manager that excludes soft-deleted objects by default."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

    def with_deleted(self):
        """Include soft-deleted objects."""
        return super().get_queryset()

    def deleted_only(self):
        """Only soft-deleted objects."""
        return super().get_queryset().filter(deleted_at__isnull=False)


class SoftDeleteModel(models.Model):
    """Abstract base model with soft delete functionality."""

    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()  # Default: excludes deleted
    all_objects = models.Manager()  # All records including deleted

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """Soft delete the object."""
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    def hard_delete(self, using=None, keep_parents=False):
        """Permanently delete the object."""
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        """Restore a soft-deleted object."""
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])

    @property
    def is_deleted(self):
        """Check if object is soft-deleted."""
        return self.deleted_at is not None
```

**Usage:**

```python
from apps.core.models import SoftDeleteModel

class ImportantData(SoftDeleteModel):
    content = models.TextField()

# Soft delete (default)
obj.delete()  # Sets deleted_at, record remains in DB

# Query active records only (default)
ImportantData.objects.all()  # Excludes deleted

# Include deleted records
ImportantData.objects.with_deleted()

# Only deleted records
ImportantData.objects.deleted_only()

# Restore deleted record
obj.restore()

# Permanent deletion
obj.hard_delete()
```

### BaseModel

Combines timestamps and soft delete for standard models.

```python
class BaseModel(TimeStampedModel, SoftDeleteModel):
    """Standard base model combining timestamps and soft delete."""

    class Meta:
        abstract = True
```

**Usage:**

```python
from apps.core.models import BaseModel

class Customer(BaseModel):
    name = models.CharField(max_length=200)

# Has all features:
# - created_at, updated_at
# - deleted_at, soft delete methods
# - SoftDeleteManager
```

## Concrete Models

### ContactSubmission

Stores contact form submissions.

```python
class ContactSubmission(TimeStampedModel):
    """Model to store and track contact form submissions."""

    SUBJECT_CHOICES = [
        ('question', 'General Question'),
        ('appointment', 'Appointment Request'),
        ('emergency', 'Emergency'),
        ('pricing', 'Pricing Information'),
        ('feedback', 'Feedback'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('new', 'New'),
        ('read', 'Read'),
        ('responded', 'Responded'),
        ('archived', 'Archived'),
    ]

    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=50, choices=SUBJECT_CHOICES, default='question')
    message = models.TextField()

    # Tracking fields
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')

    # Response tracking
    responded_at = models.DateTimeField(null=True, blank=True)
    response_notes = models.TextField(blank=True)
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `subject` | CharField | Category of inquiry |
| `status` | CharField | Processing status |
| `ip_address` | IPField | Sender's IP for spam tracking |
| `user_agent` | TextField | Browser info |
| `responded_at` | DateTime | When staff responded |
| `response_notes` | TextField | Internal notes on response |

## Views

Location: `apps/core/views.py`

### HomeView

Landing page.

```python
class HomeView(TemplateView):
    """Homepage view."""
    template_name = 'core/home.html'
```

### AboutView

About the clinic.

```python
class AboutView(TemplateView):
    """About page view."""
    template_name = 'core/about.html'
```

### ServicesView

Services offered.

```python
class ServicesView(TemplateView):
    """Services page view."""
    template_name = 'core/services.html'
```

### ContactView

Contact form with spam prevention.

```python
class ContactView(View):
    """Contact page view with form handling."""

    def get(self, request):
        """Display the contact form."""
        return render(request, 'core/contact.html')

    def post(self, request):
        """Handle contact form submission."""
        # Check honeypot field (spam prevention)
        honeypot = request.POST.get('website', '').strip()
        if honeypot:
            # Silently redirect (don't reveal spam detection)
            logger.warning("Honeypot triggered from IP: %s", self.get_client_ip(request))
            messages.success(request, 'Gracias por tu mensaje.')
            return redirect('core:contact')

        # Validate required fields
        if not all([name, email, subject, message_text]):
            messages.error(request, 'Por favor completa todos los campos requeridos.')
            return render(request, self.template_name)

        # Save submission
        submission = ContactSubmission.objects.create(...)

        # Send email notification
        send_mail(...)

        messages.success(request, 'Gracias por tu mensaje. Te contactaremos pronto.')
        return redirect('core:contact')
```

### health_check

Load balancer health endpoint.

```python
def health_check(request):
    """Health check endpoint for load balancers."""
    return render(request, 'core/health.html', {'status': 'ok'})
```

### csrf_failure

Custom CSRF error page.

```python
def csrf_failure(request, reason=''):
    """Custom CSRF failure view with friendly error page."""
    return render(request, '403_csrf.html', {'reason': reason}, status=403)
```

## URL Patterns

Location: `apps/core/urls.py`

```python
app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('services/', views.ServicesView.as_view(), name='services'),
    path('contact/', views.ContactView.as_view(), name='contact'),
]
```

## Workflows

### Contact Form Submission

```python
from apps.core.models import ContactSubmission
from django.utils import timezone

# Form submission creates record
submission = ContactSubmission.objects.create(
    name='María García',
    email='maria@example.com',
    phone='+52 55 1234 5678',
    subject='appointment',
    message='Me gustaría programar una cita para mi perro.',
    ip_address='192.168.1.100',
    user_agent='Mozilla/5.0...',
)

# Staff reviews submission
submission.status = 'read'
submission.save()

# Staff responds
submission.status = 'responded'
submission.responded_at = timezone.now()
submission.response_notes = 'Called customer, scheduled for next Tuesday.'
submission.save()

# Archive old submissions
submission.status = 'archived'
submission.save()
```

### Soft Delete Pattern

```python
from apps.core.models import BaseModel

class Customer(BaseModel):
    name = models.CharField(max_length=200)
    email = models.EmailField()

# Create customer
customer = Customer.objects.create(name='Test', email='test@example.com')

# Soft delete
customer.delete()
print(customer.is_deleted)  # True
print(customer.deleted_at)  # 2025-12-25 10:30:00

# Customer not in default queries
Customer.objects.filter(name='Test').exists()  # False

# But still exists
Customer.objects.with_deleted().filter(name='Test').exists()  # True

# Restore customer
customer.restore()
Customer.objects.filter(name='Test').exists()  # True

# Permanently delete
customer.hard_delete()  # Gone forever
```

## Spam Prevention

The contact form uses a honeypot field for spam prevention:

```html
<!-- In template: hidden field that bots fill out -->
<input type="text" name="website" style="display: none;" tabindex="-1" autocomplete="off">
```

```python
# In view: check if honeypot was filled
honeypot = request.POST.get('website', '').strip()
if honeypot:
    # Bot detected - silently accept (don't reveal detection)
    logger.warning("Honeypot triggered from IP: %s", self.get_client_ip(request))
    messages.success(request, 'Gracias por tu mensaje.')
    return redirect('core:contact')
```

**How it works:**
1. Hidden field named "website" is invisible to users
2. Spam bots automatically fill all fields
3. If "website" has content, it's a bot
4. Bot receives success message (doesn't know it was detected)
5. Submission is not saved

## Integration Points

### Abstract Model Usage

```python
# In pets/models.py
from apps.core.models import BaseModel

class Pet(BaseModel):
    name = models.CharField(max_length=100)
    species = models.CharField(max_length=50)
    # Inherits: created_at, updated_at, deleted_at, soft delete

# In appointments/models.py
from apps.core.models import TimeStampedModel

class Appointment(TimeStampedModel):
    date = models.DateField()
    # Inherits: created_at, updated_at (no soft delete)

# In billing/models.py
from apps.core.models import UUIDModel, TimeStampedModel

class Invoice(UUIDModel, TimeStampedModel):
    amount = models.DecimalField(...)
    # Uses UUID as PK, has timestamps
```

### With CRM Module

```python
from apps.core.models import ContactSubmission
from apps.crm.models import Interaction

# Contact submission can trigger CRM interaction
def on_contact_submission(submission):
    # Check if email matches existing customer
    from apps.crm.models import OwnerProfile
    profile = OwnerProfile.objects.filter(
        user__email=submission.email
    ).first()

    if profile:
        Interaction.objects.create(
            customer=profile,
            interaction_type='inquiry',
            notes=f'Contact form: {submission.subject}\n{submission.message}',
        )
```

## Query Examples

### Contact Submission Queries

```python
from apps.core.models import ContactSubmission
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

# New submissions (unread)
new = ContactSubmission.objects.filter(status='new')

# Submissions needing response
pending = ContactSubmission.objects.filter(
    status__in=['new', 'read']
).order_by('created_at')

# Emergency submissions
emergencies = ContactSubmission.objects.filter(
    subject='emergency'
).order_by('-created_at')

# Submissions by subject
by_subject = ContactSubmission.objects.values('subject').annotate(
    count=Count('id')
).order_by('-count')

# Submissions from last 7 days
recent = ContactSubmission.objects.filter(
    created_at__gte=timezone.now() - timedelta(days=7)
)

# Submissions from specific IP (spam check)
from_ip = ContactSubmission.objects.filter(
    ip_address='192.168.1.100'
).count()
```

### Soft Delete Queries

```python
from apps.core.models import SoftDeleteModel

class MyModel(SoftDeleteModel):
    name = models.CharField(max_length=100)

# Active records only (default)
active = MyModel.objects.all()

# All records including deleted
all_records = MyModel.objects.with_deleted()

# Only deleted records
deleted = MyModel.objects.deleted_only()

# Records deleted in last 30 days
recently_deleted = MyModel.objects.deleted_only().filter(
    deleted_at__gte=timezone.now() - timedelta(days=30)
)

# Permanently delete old soft-deleted records
old_deleted = MyModel.objects.deleted_only().filter(
    deleted_at__lt=timezone.now() - timedelta(days=365)
)
for obj in old_deleted:
    obj.hard_delete()
```

## Testing

### Unit Tests

Location: `tests/test_core.py`

```bash
# Run core unit tests
python -m pytest tests/test_core.py -v
```

### Browser Tests

Location: `tests/e2e/browser/test_core.py`

```bash
# Run core browser tests
python -m pytest tests/e2e/browser/test_core.py -v

# Run with visible browser
python -m pytest tests/e2e/browser/test_core.py -v --headed --slowmo=500
```

### Key Test Scenarios

1. **Abstract Models**
   - TimeStampedModel sets created_at/updated_at
   - UUIDModel generates valid UUIDs
   - SoftDeleteModel soft deletes correctly
   - BaseModel combines all features

2. **Soft Delete Manager**
   - Default queryset excludes deleted
   - with_deleted() includes all
   - deleted_only() returns only deleted
   - restore() brings back deleted records

3. **Contact Form**
   - Valid submission creates record
   - Missing required fields rejected
   - Honeypot catches spam bots
   - Email notification sent

4. **Public Pages**
   - Homepage loads correctly
   - About page loads correctly
   - Services page loads correctly
   - Contact page displays form

5. **Health Check**
   - Returns 200 OK
   - Returns expected content
