# S-019: Email Marketing

**Story Type:** User Story
**Priority:** Medium
**Epoch:** 5 (with CRM)
**Status:** PENDING
**Module:** django-crm-lite + django-omnichannel

## User Story

**As a** clinic owner
**I want to** send targeted email campaigns to pet owners
**So that** I can increase engagement, retention, and revenue

**As a** pet owner
**I want to** receive relevant email updates about my pets
**So that** I stay informed about their health and clinic offerings

**As a** marketing manager
**I want to** automate email sequences based on customer behavior
**So that** the right message reaches the right person at the right time

## Acceptance Criteria

### Newsletter System
- [ ] Double opt-in subscription flow
- [ ] Preference center for frequency and topics
- [ ] One-click unsubscribe in every email
- [ ] GDPR/CAN-SPAM compliance
- [ ] Subscription status visible in owner profiles

### Campaign Builder
- [ ] Pre-built templates (appointment reminder, promotion, newsletter)
- [ ] Personalization tokens ({{pet_name}}, {{owner_name}}, etc.)
- [ ] Preview and test send before launch
- [ ] Schedule campaigns for future delivery
- [ ] A/B testing for subject lines

### Segmentation
- [ ] Segment by pet species (dog owners, cat owners)
- [ ] Segment by service history (surgery clients, regular checkups)
- [ ] Segment by engagement level (active, lapsed, VIP)
- [ ] Segment by location
- [ ] Segment by spending tier (from loyalty program)
- [ ] Custom segment builder with rules

### Automated Sequences
- [ ] Welcome series for new clients
- [ ] Re-engagement for inactive clients (6+ months)
- [ ] Post-visit follow-up
- [ ] Pet birthday sequences
- [ ] Abandoned cart recovery
- [ ] Vaccination due reminders

### Email Analytics
- [ ] Open rates and click rates
- [ ] Bounce and unsubscribe tracking
- [ ] A/B testing results
- [ ] Revenue attribution
- [ ] Engagement scoring

## Technical Requirements

### Email Service Provider

**Recommendation: Amazon SES**

| Provider | Cost | Pros | Cons |
|----------|------|------|------|
| **Amazon SES** | $0.10/1,000 emails | Cheapest, AWS integration | Requires more setup |
| **SendGrid** | Free tier + $15+/mo | Easy setup | Expensive at scale |
| **Mailgun** | $0.80/1,000 emails | Good API | Less marketing features |

**Why Amazon SES:**
- Best cost for small clinic (~$0.10 per 1,000 = essentially free)
- Excellent deliverability
- Django integration via django-ses
- If hosting on AWS, seamless integration

### Models

```python
class NewsletterSubscription(models.Model):
    """Email subscription preferences"""
    owner = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField()

    # Status
    STATUS_CHOICES = [
        ('pending', 'Pending Confirmation'),
        ('active', 'Active'),
        ('unsubscribed', 'Unsubscribed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Preferences
    frequency = models.CharField(max_length=20, default='weekly')
    # 'daily', 'weekly', 'monthly', 'important_only'

    topics = models.JSONField(default=list)
    # ['promotions', 'pet_tips', 'appointments', 'new_products']

    # Tracking
    subscribed_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True)
    unsubscribed_at = models.DateTimeField(null=True)

    # Token for double opt-in
    confirmation_token = models.UUIDField(default=uuid.uuid4)

    class Meta:
        ordering = ['-subscribed_at']


class EmailTemplate(models.Model):
    """Reusable email templates"""
    TEMPLATE_TYPES = [
        ('newsletter', 'Newsletter'),
        ('promotion', 'Promotion'),
        ('reminder', 'Reminder'),
        ('transactional', 'Transactional'),
        ('sequence', 'Automation Sequence'),
    ]

    name = models.CharField(max_length=200)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES)

    # Content
    subject = models.CharField(max_length=200)
    subject_es = models.CharField(max_length=200)

    html_content = models.TextField()
    html_content_es = models.TextField()

    text_content = models.TextField(blank=True)  # Plain text version

    # Design
    thumbnail = models.ImageField(upload_to='email_templates/', null=True)

    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Segment(models.Model):
    """Audience segments for targeting"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Rules (JSON query builder format)
    rules = models.JSONField(default=dict)
    # Example: {"all": [{"field": "pet_species", "op": "eq", "value": "dog"}]}

    # Cached count
    member_count = models.IntegerField(default=0)
    last_calculated = models.DateTimeField(null=True)

    # Metadata
    is_dynamic = models.BooleanField(default=True)  # Auto-update membership
    created_at = models.DateTimeField(auto_now_add=True)

    def calculate_members(self):
        """Calculate segment membership based on rules"""
        pass  # Implement rule evaluation


class EmailCampaign(models.Model):
    """Email campaign/blast"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    ]

    name = models.CharField(max_length=200)

    # Content
    template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True)
    subject = models.CharField(max_length=200)
    subject_es = models.CharField(max_length=200, blank=True)

    # Custom content (overrides template)
    html_content = models.TextField(blank=True)

    # Targeting
    segment = models.ForeignKey(Segment, on_delete=models.SET_NULL, null=True)

    # Scheduling
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    scheduled_at = models.DateTimeField(null=True)
    sent_at = models.DateTimeField(null=True)

    # A/B Testing
    ab_test_enabled = models.BooleanField(default=False)
    ab_subject_variant = models.CharField(max_length=200, blank=True)
    ab_winner_selected_at = models.DateTimeField(null=True)

    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class EmailSend(models.Model):
    """Individual email send record"""
    campaign = models.ForeignKey(EmailCampaign, on_delete=models.CASCADE, related_name='sends')
    sequence_step = models.ForeignKey('SequenceStep', on_delete=models.CASCADE, null=True)

    # Recipient
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField()

    # Personalization data (snapshot at send time)
    personalization = models.JSONField(default=dict)

    # SES tracking
    ses_message_id = models.CharField(max_length=100, blank=True)

    # Status
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('bounced', 'Bounced'),
        ('complained', 'Complained'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')

    # Timestamps
    sent_at = models.DateTimeField(null=True)
    delivered_at = models.DateTimeField(null=True)

    class Meta:
        ordering = ['-sent_at']


class EmailEvent(models.Model):
    """Email engagement events"""
    EVENT_TYPES = [
        ('open', 'Opened'),
        ('click', 'Clicked'),
        ('bounce', 'Bounced'),
        ('complaint', 'Complained'),
        ('unsubscribe', 'Unsubscribed'),
    ]

    send = models.ForeignKey(EmailSend, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)

    # Event data
    timestamp = models.DateTimeField()
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)

    # For clicks
    url_clicked = models.URLField(blank=True)

    # For bounces
    bounce_type = models.CharField(max_length=20, blank=True)
    # 'hard', 'soft', 'transient'

    class Meta:
        ordering = ['-timestamp']


class AutomatedSequence(models.Model):
    """Automated email sequence (drip campaign)"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Trigger
    TRIGGER_TYPES = [
        ('signup', 'New Signup'),
        ('first_visit', 'First Appointment'),
        ('inactive', 'Inactive Period'),
        ('birthday', 'Pet Birthday'),
        ('cart_abandoned', 'Cart Abandoned'),
        ('vaccination_due', 'Vaccination Due'),
        ('post_visit', 'Post Visit'),
        ('manual', 'Manual Enrollment'),
    ]
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_TYPES)
    trigger_config = models.JSONField(default=dict)
    # e.g., {"inactive_days": 180}

    # Status
    is_active = models.BooleanField(default=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class SequenceStep(models.Model):
    """Step in an automated sequence"""
    sequence = models.ForeignKey(AutomatedSequence, on_delete=models.CASCADE, related_name='steps')

    order = models.PositiveIntegerField()

    # Delay from previous step (or trigger)
    delay_days = models.PositiveIntegerField(default=0)
    delay_hours = models.PositiveIntegerField(default=0)

    # Content
    template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True)
    subject = models.CharField(max_length=200)
    html_content = models.TextField(blank=True)

    # Conditions (optional)
    conditions = models.JSONField(default=dict)
    # e.g., {"skip_if": {"opened_previous": true}}

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sequence', 'order']


class SequenceEnrollment(models.Model):
    """User enrolled in an automated sequence"""
    sequence = models.ForeignKey(AutomatedSequence, on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)

    # Status
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('exited', 'Exited Early'),
        ('paused', 'Paused'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    # Progress
    current_step = models.PositiveIntegerField(default=0)
    next_send_at = models.DateTimeField(null=True)

    # Timestamps
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)
    exited_at = models.DateTimeField(null=True)
    exit_reason = models.TextField(blank=True)

    class Meta:
        unique_together = ['sequence', 'recipient']
```

### AI Tools

```python
EMAIL_TOOLS = [
    {
        "name": "create_email_campaign",
        "description": "Create a new email campaign",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "subject": {"type": "string"},
                "content_topic": {"type": "string"},
                "segment_id": {"type": "integer"},
                "schedule": {"type": "string"}
            },
            "required": ["name", "subject", "content_topic"]
        }
    },
    {
        "name": "suggest_subject_lines",
        "description": "Generate A/B test subject line variants",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
                "tone": {"type": "string"},
                "num_variants": {"type": "integer"}
            },
            "required": ["topic"]
        }
    },
    {
        "name": "analyze_campaign_performance",
        "description": "Analyze email campaign metrics",
        "parameters": {
            "type": "object",
            "properties": {
                "campaign_id": {"type": "integer"},
                "compare_to_average": {"type": "boolean"}
            },
            "required": ["campaign_id"]
        }
    },
    {
        "name": "recommend_segment",
        "description": "Recommend best segment for a campaign goal",
        "parameters": {
            "type": "object",
            "properties": {
                "goal": {"type": "string"},
                "product_or_service": {"type": "string"}
            },
            "required": ["goal"]
        }
    },
    {
        "name": "generate_email_content",
        "description": "Generate email content with AI",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
                "tone": {"type": "string"},
                "include_cta": {"type": "boolean"},
                "language": {"type": "string"}
            },
            "required": ["topic"]
        }
    },
    {
        "name": "get_email_stats",
        "description": "Get email marketing statistics",
        "parameters": {
            "type": "object",
            "properties": {
                "period": {"type": "string"},
                "metric": {"type": "string"}
            }
        }
    }
]
```

## Example AI Conversations

### Creating a Campaign
```
Dr. Pablo: I want to send an email about our new dental cleaning special

AI: Great! Let me help you create that campaign.

    For the dental cleaning special, I recommend:

    📧 Campaign: Dental Cleaning Promo

    Subject line options (A/B test):
    A: "Smile! 20% off dental cleaning for your pet"
    B: "Your pet's teeth need love too - Special offer inside"

    Best segment: "Active clients with dogs/cats"
    (342 subscribers match)

    Timing: Tuesday 10am tends to have best open rates

    Would you like me to:
    1. Draft the email content
    2. Use an existing template
    3. Schedule for next Tuesday

Dr. Pablo: Draft the content

AI: Here's a draft for the dental cleaning promo:

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Subject: Smile! 20% off dental cleaning
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    Hola {{owner_name}}!

    Did you know that dental disease affects 80% of
    dogs and 70% of cats by age 3?

    This month at Pet-Friendly, we're offering
    20% off professional dental cleanings for
    {{pet_name}}.

    What's included:
    ✓ Pre-anesthetic bloodwork
    ✓ Full dental exam
    ✓ Ultrasonic scaling & polishing
    ✓ Fluoride treatment

    Regular price: $2,800 MXN
    Your price: $2,240 MXN (save $560!)

    [BOOK NOW]

    Offer valid through January 31, 2026.

    - Dr. Pablo
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    Should I schedule this for Tuesday at 10am?
```

### Campaign Analytics
```
Dr. Pablo: How did last month's emails perform?

AI: Here's your email marketing report for December:

    📊 DECEMBER 2025 EMAIL PERFORMANCE
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    Campaigns Sent: 4
    Total Emails: 1,847

    Key Metrics:
    • Open Rate: 42.3% (industry avg: 28%)
    • Click Rate: 8.7% (industry avg: 4%)
    • Unsubscribes: 3 (0.16%)
    • Bounces: 12 (0.65%)

    Top Performing Campaign:
    "Holiday Hours Reminder" - 58% open rate

    Revenue Attributed: $12,450 MXN
    (from clicks → appointments/purchases)

    📈 Your list is healthy! Open rates are
    50% above industry average.

    Recommendation: Your vaccination reminder
    sequence has 67% open rate. Consider
    adding more automated sequences.

    Want details on a specific campaign?
```

## SES Setup Requirements

### Domain Verification
```
1. Add SPF record to DNS:
   v=spf1 include:amazonses.com ~all

2. Add DKIM records (3 CNAME records from AWS console)

3. Add DMARC record:
   v=DMARC1; p=quarantine; rua=mailto:admin@petfriendly.mx
```

### Production Access
- Request production access in AWS console
- Exit sandbox mode (default limits: 200 emails/day)
- Set up SNS for bounce/complaint handling

### Django Configuration
```python
# settings.py
EMAIL_BACKEND = 'django_ses.SESBackend'
AWS_SES_REGION_NAME = 'us-east-1'
AWS_SES_REGION_ENDPOINT = 'email.us-east-1.amazonaws.com'

# SNS endpoints for tracking
AWS_SES_SNS_NOTIFICATION_TOPIC = 'arn:aws:sns:...'
```

## Definition of Done

- [ ] Newsletter subscription with double opt-in
- [ ] Preference center for subscribers
- [ ] Email templates (3+ built-in)
- [ ] Segment builder with rules engine
- [ ] Campaign creation and scheduling
- [ ] A/B testing for subject lines
- [ ] Automated sequences (3+ types)
- [ ] Real-time analytics dashboard
- [ ] Amazon SES integration
- [ ] Bounce/complaint handling
- [ ] Unsubscribe processing
- [ ] Tests written and passing (>95% coverage)
- [ ] Documentation updated

## Dependencies

- S-007: CRM + Intelligence (owner profiles)
- S-016: Loyalty & Rewards (spending tiers)
- S-005: E-Commerce Store (abandoned cart)
- S-004: Appointment Booking (post-visit)

## Notes

- Start with Amazon SES for cost efficiency
- Build simple drag-and-drop editor or use pre-built templates
- Integrate with CRM for personalization data
- Consider email deliverability best practices
- Set up proper unsubscribe handling to avoid spam complaints
- Monitor sender reputation in AWS console

## Development Process

**Before implementing this story**, review and follow the **23-Step TDD Cycle** in:
- `CLAUDE.md` - Global development workflow
- `planning/TASK_BREAKDOWN.md` - Specific tasks for this story

Tests must be written before implementation. >95% coverage required.
