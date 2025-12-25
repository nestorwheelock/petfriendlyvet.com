# Email Marketing Module

The `apps.email_marketing` module provides newsletter management, email campaigns, automated sequences, and engagement tracking.

## Table of Contents

- [Overview](#overview)
- [Models](#models)
  - [NewsletterSubscription](#newslettersubscription)
  - [EmailSegment](#emailsegment)
  - [EmailTemplate](#emailtemplate)
  - [EmailCampaign](#emailcampaign)
  - [EmailSend](#emailsend)
  - [EmailLink](#emaillink)
  - [AutomatedSequence](#automatedsequence)
  - [SequenceStep](#sequencestep)
  - [SequenceEnrollment](#sequenceenrollment)
- [Workflows](#workflows)
- [Integration Points](#integration-points)
- [Query Examples](#query-examples)
- [Testing](#testing)

## Overview

The email marketing module provides:

- **Newsletter Subscriptions** - Double opt-in subscription management
- **Segmentation** - Dynamic and static audience segments
- **Templates** - Reusable bilingual email templates
- **Campaigns** - One-time email blasts with tracking
- **Automation** - Triggered email sequences
- **Analytics** - Open, click, bounce tracking

## Models

Location: `apps/email_marketing/models.py`

### NewsletterSubscription

Newsletter subscription with double opt-in.

```python
STATUS_CHOICES = [
    ('pending', 'Pending Confirmation'),
    ('active', 'Active'),
    ('unsubscribed', 'Unsubscribed'),
    ('bounced', 'Bounced'),
]

class NewsletterSubscription(models.Model):
    email = models.EmailField(unique=True)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    confirmation_token = models.CharField(max_length=100, unique=True)
    confirmed_at = models.DateTimeField(null=True)
    preferences = models.JSONField(default=dict)
    tags = models.JSONField(default=list)
    source = models.CharField(max_length=50, blank=True)
    ip_address = models.GenericIPAddressField(null=True)
    unsubscribed_at = models.DateTimeField(null=True)
    unsubscribe_reason = models.TextField(blank=True)
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `confirmation_token` | CharField | UUID for double opt-in |
| `preferences` | JSONField | Email preferences (frequency, topics) |
| `tags` | JSONField | List of tags for segmentation |
| `source` | CharField | Where they subscribed (website, checkout) |

### EmailSegment

Audience segment for targeting.

```python
class EmailSegment(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    rules = models.JSONField(default=list)  # Segment rules
    is_dynamic = models.BooleanField(default=True)
    subscriber_count = models.IntegerField(default=0)
    last_computed = models.DateTimeField(null=True)
    is_active = models.BooleanField(default=True)
```

### EmailTemplate

Reusable email template.

```python
TEMPLATE_TYPES = [
    ('newsletter', 'Newsletter'),
    ('promotional', 'Promotional'),
    ('transactional', 'Transactional'),
    ('reminder', 'Reminder'),
    ('welcome', 'Welcome'),
]

class EmailTemplate(models.Model):
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES)
    subject = models.CharField(max_length=200)
    subject_es = models.CharField(max_length=200, blank=True)
    html_content = models.TextField()
    html_content_es = models.TextField(blank=True)
    text_content = models.TextField(blank=True)
    text_content_es = models.TextField(blank=True)
    variables = models.JSONField(default=list)  # Available merge tags
    is_active = models.BooleanField(default=True)
```

### EmailCampaign

Email campaign with tracking.

```python
STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('scheduled', 'Scheduled'),
    ('sending', 'Sending'),
    ('sent', 'Sent'),
    ('cancelled', 'Cancelled'),
]

class EmailCampaign(models.Model):
    name = models.CharField(max_length=200)
    template = models.ForeignKey(EmailTemplate, null=True, on_delete=models.SET_NULL)
    subject = models.CharField(max_length=200)
    subject_es = models.CharField(max_length=200, blank=True)
    preview_text = models.CharField(max_length=200, blank=True)
    html_content = models.TextField()
    text_content = models.TextField(blank=True)
    from_name = models.CharField(max_length=100)
    from_email = models.EmailField()
    reply_to = models.EmailField(blank=True)
    segment = models.ForeignKey(EmailSegment, null=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    scheduled_at = models.DateTimeField(null=True)
    sent_at = models.DateTimeField(null=True)

    # Metrics
    total_recipients = models.IntegerField(default=0)
    total_sent = models.IntegerField(default=0)
    total_delivered = models.IntegerField(default=0)
    total_opened = models.IntegerField(default=0)
    total_clicked = models.IntegerField(default=0)
    total_bounced = models.IntegerField(default=0)
    total_unsubscribed = models.IntegerField(default=0)

    # A/B testing
    ab_test_enabled = models.BooleanField(default=False)
    ab_test_subject_b = models.CharField(max_length=200, blank=True)

    @property
    def open_rate(self):
        if self.total_delivered > 0:
            return (self.total_opened / self.total_delivered) * 100
        return 0

    @property
    def click_rate(self):
        if self.total_delivered > 0:
            return (self.total_clicked / self.total_delivered) * 100
        return 0
```

### EmailSend

Individual email send record.

```python
STATUS_CHOICES = [
    ('queued', 'Queued'),
    ('sent', 'Sent'),
    ('delivered', 'Delivered'),
    ('opened', 'Opened'),
    ('clicked', 'Clicked'),
    ('bounced', 'Bounced'),
    ('complained', 'Complained'),
    ('failed', 'Failed'),
]

class EmailSend(models.Model):
    campaign = models.ForeignKey(EmailCampaign, on_delete=models.CASCADE, related_name='sends')
    subscription = models.ForeignKey(NewsletterSubscription, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    sent_at = models.DateTimeField(null=True)
    delivered_at = models.DateTimeField(null=True)
    opened_at = models.DateTimeField(null=True)
    clicked_at = models.DateTimeField(null=True)
    open_count = models.IntegerField(default=0)
    click_count = models.IntegerField(default=0)
    bounce_type = models.CharField(max_length=20, blank=True)
    bounce_reason = models.TextField(blank=True)
    message_id = models.CharField(max_length=200, blank=True)
```

### EmailLink

Track clicks on links in emails.

```python
class EmailLink(models.Model):
    campaign = models.ForeignKey(EmailCampaign, on_delete=models.CASCADE, related_name='links')
    original_url = models.URLField()
    tracking_url = models.CharField(max_length=100, unique=True)
    click_count = models.IntegerField(default=0)
```

### AutomatedSequence

Automated email sequence (drip campaign).

```python
TRIGGER_TYPES = [
    ('signup', 'Newsletter Signup'),
    ('purchase', 'After Purchase'),
    ('appointment', 'After Appointment'),
    ('inactivity', 'Inactivity'),
    ('birthday', 'Birthday'),
    ('custom', 'Custom Trigger'),
]

class AutomatedSequence(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_TYPES)
    is_active = models.BooleanField(default=True)
    total_enrolled = models.IntegerField(default=0)
    total_completed = models.IntegerField(default=0)
```

### SequenceStep

Step in an automated sequence.

```python
class SequenceStep(models.Model):
    sequence = models.ForeignKey(AutomatedSequence, on_delete=models.CASCADE, related_name='steps')
    step_number = models.IntegerField()
    template = models.ForeignKey(EmailTemplate, on_delete=models.PROTECT)
    delay_days = models.IntegerField(default=0)
    delay_hours = models.IntegerField(default=0)
    subject_override = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['sequence', 'step_number']
```

### SequenceEnrollment

Track user enrollment in sequence.

```python
STATUS_CHOICES = [
    ('active', 'Active'),
    ('completed', 'Completed'),
    ('paused', 'Paused'),
    ('exited', 'Exited'),
]

class SequenceEnrollment(models.Model):
    sequence = models.ForeignKey(AutomatedSequence, on_delete=models.CASCADE)
    subscription = models.ForeignKey(NewsletterSubscription, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    current_step = models.IntegerField(default=1)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)
    next_email_at = models.DateTimeField(null=True)

    class Meta:
        unique_together = ['sequence', 'subscription']
```

## Workflows

### Subscribing to Newsletter

```python
from apps.email_marketing.models import NewsletterSubscription

# Create pending subscription
subscription = NewsletterSubscription.objects.create(
    email='user@example.com',
    status='pending',
    source='website_footer',
    ip_address='192.168.1.1',
)

# Send confirmation email with token...

# Confirm subscription
subscription.status = 'active'
subscription.confirmed_at = timezone.now()
subscription.save()
```

### Creating and Sending a Campaign

```python
from apps.email_marketing.models import EmailCampaign, EmailSegment, EmailSend

# Create campaign
campaign = EmailCampaign.objects.create(
    name='December Newsletter',
    subject='Holiday Pet Care Tips',
    subject_es='Consejos para el cuidado de mascotas en fiestas',
    html_content='<html>...</html>',
    from_name='Pet Friendly Vet',
    from_email='news@petfriendlyvet.com',
    segment=EmailSegment.objects.get(name='Active Subscribers'),
    status='draft',
)

# Queue sends for segment
subscribers = NewsletterSubscription.objects.filter(
    status='active',
    tags__contains=['newsletter']
)
for sub in subscribers:
    EmailSend.objects.create(
        campaign=campaign,
        subscription=sub,
        status='queued',
    )

# Schedule campaign
campaign.scheduled_at = timezone.now() + timedelta(days=1)
campaign.status = 'scheduled'
campaign.total_recipients = subscribers.count()
campaign.save()
```

### Setting Up an Automated Sequence

```python
from apps.email_marketing.models import (
    AutomatedSequence, SequenceStep, EmailTemplate
)

# Create welcome sequence
sequence = AutomatedSequence.objects.create(
    name='Welcome Series',
    trigger_type='signup',
    is_active=True,
)

# Add steps
SequenceStep.objects.create(
    sequence=sequence,
    step_number=1,
    template=EmailTemplate.objects.get(name='Welcome Email'),
    delay_days=0,
    delay_hours=0,  # Immediately
)
SequenceStep.objects.create(
    sequence=sequence,
    step_number=2,
    template=EmailTemplate.objects.get(name='Introduction to Services'),
    delay_days=3,
)
SequenceStep.objects.create(
    sequence=sequence,
    step_number=3,
    template=EmailTemplate.objects.get(name='First Visit Offer'),
    delay_days=7,
)
```

## Integration Points

### With Accounts (User Registration)

```python
from apps.email_marketing.models import NewsletterSubscription, AutomatedSequence

def on_user_registered(user, subscribe_newsletter=True):
    if subscribe_newsletter:
        sub = NewsletterSubscription.objects.create(
            email=user.email,
            user=user,
            status='active',  # Skip confirmation for registered users
            confirmed_at=timezone.now(),
            source='registration',
        )
        # Enroll in welcome sequence
        enroll_in_sequence(sub, 'signup')
```

### With Appointments

```python
# After appointment, trigger follow-up sequence
def on_appointment_completed(appointment):
    sub = NewsletterSubscription.objects.filter(
        user=appointment.owner,
        status='active'
    ).first()
    if sub:
        enroll_in_sequence(sub, 'appointment')
```

## Query Examples

```python
from apps.email_marketing.models import (
    NewsletterSubscription, EmailCampaign, EmailSend, AutomatedSequence
)
from django.db.models import Count, Avg

# Active subscribers
active = NewsletterSubscription.objects.filter(status='active')

# Subscribers by source
by_source = NewsletterSubscription.objects.values('source').annotate(
    count=Count('id')
).order_by('-count')

# Campaign performance
campaigns = EmailCampaign.objects.filter(status='sent').order_by('-sent_at')
for c in campaigns:
    print(f'{c.name}: Open {c.open_rate:.1f}%, Click {c.click_rate:.1f}%')

# Best performing links
top_links = EmailLink.objects.filter(
    campaign=campaign
).order_by('-click_count')[:10]

# Emails due to send (for automation)
due_emails = SequenceEnrollment.objects.filter(
    status='active',
    next_email_at__lte=timezone.now()
).select_related('subscription', 'sequence')

# Bounced emails to clean
bounced = NewsletterSubscription.objects.filter(status='bounced')

# Unsubscribe reasons
reasons = NewsletterSubscription.objects.filter(
    status='unsubscribed'
).exclude(unsubscribe_reason='').values('unsubscribe_reason')
```

## Testing

Location: `tests/test_email_marketing.py`

```bash
python -m pytest tests/test_email_marketing.py -v
```
