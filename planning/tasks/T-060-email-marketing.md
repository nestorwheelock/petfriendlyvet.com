# T-060: Email Marketing System

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md and [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Full Stack Developer
**Objective**: Implement email marketing with campaigns, automation, and analytics
**Related Story**: S-019
**Epoch**: 5
**Estimate**: 6 hours

### Constraints
**Allowed File Paths**: apps/marketing/, apps/communications/
**Forbidden Paths**: None

### Deliverables
- [ ] Newsletter subscription model
- [ ] Campaign builder
- [ ] Segmentation engine
- [ ] Automated sequences
- [ ] Email analytics
- [ ] Unsubscribe handling

### Wireframe Reference
See: `planning/wireframes/19-crm-dashboard.txt`

### Implementation Details

#### Models
```python
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField

User = get_user_model()


class NewsletterSubscription(models.Model):
    """Email subscription management."""

    owner = models.OneToOneField(
        User, on_delete=models.CASCADE,
        null=True, blank=True, related_name='newsletter'
    )

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, blank=True)

    # Subscription status
    STATUS_CHOICES = [
        ('pending', 'Pendiente confirmación'),
        ('active', 'Activo'),
        ('unsubscribed', 'Dado de baja'),
        ('bounced', 'Rebotado'),
        ('complained', 'Marcado spam'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Preferences
    frequency = models.CharField(max_length=20, default='weekly')
    # weekly, monthly, important_only
    topics = models.JSONField(default=list)
    # ['promotions', 'pet_tips', 'news', 'reminders']
    language = models.CharField(max_length=5, default='es')

    # Double opt-in
    confirmation_token = models.CharField(max_length=100, blank=True)
    confirmed_at = models.DateTimeField(null=True)

    # Tracking
    source = models.CharField(max_length=100, blank=True)
    # website, checkout, appointment, referral
    ip_address = models.GenericIPAddressField(null=True)

    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(null=True)

    class Meta:
        ordering = ['-subscribed_at']


class EmailTemplate(models.Model):
    """Reusable email templates."""

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    TEMPLATE_TYPES = [
        ('campaign', 'Campaña'),
        ('transactional', 'Transaccional'),
        ('automated', 'Automatizado'),
    ]
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES)

    # Content
    subject = models.CharField(max_length=200)
    preview_text = models.CharField(max_length=200, blank=True)
    html_content = models.TextField()
    text_content = models.TextField(blank=True)

    # Design
    header_image = models.ImageField(upload_to='email/headers/', null=True, blank=True)
    footer_html = models.TextField(blank=True)

    # Personalization tokens available
    available_tokens = models.JSONField(default=list)
    # ['{{owner_name}}', '{{pet_name}}', '{{unsubscribe_url}}']

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class CustomerSegment(models.Model):
    """Dynamic customer segments for targeting."""

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    # Rules (JSON query format)
    rules = models.JSONField(default=dict)
    # {
    #   "operator": "AND",
    #   "conditions": [
    #     {"field": "pets__species", "op": "eq", "value": "dog"},
    #     {"field": "last_visit_date", "op": "gte", "value": "-90d"},
    #     {"field": "lifetime_value", "op": "gte", "value": 1000}
    #   ]
    # }

    # Cached member count
    member_count = models.IntegerField(default=0)
    last_calculated = models.DateTimeField(null=True)

    is_dynamic = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def get_members(self):
        """Get current segment members."""
        from apps.marketing.services.segmentation import SegmentationService
        return SegmentationService().get_segment_members(self)


class EmailCampaign(models.Model):
    """Email marketing campaigns."""

    name = models.CharField(max_length=200)

    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('scheduled', 'Programado'),
        ('sending', 'Enviando'),
        ('sent', 'Enviado'),
        ('cancelled', 'Cancelado'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Content
    template = models.ForeignKey(
        EmailTemplate, on_delete=models.SET_NULL,
        null=True, blank=True
    )
    subject = models.CharField(max_length=200)
    preview_text = models.CharField(max_length=200, blank=True)
    html_content = models.TextField()
    text_content = models.TextField(blank=True)

    # Targeting
    segment = models.ForeignKey(
        CustomerSegment, on_delete=models.SET_NULL,
        null=True, blank=True
    )
    recipient_count = models.IntegerField(default=0)

    # Scheduling
    scheduled_at = models.DateTimeField(null=True)
    started_at = models.DateTimeField(null=True)
    completed_at = models.DateTimeField(null=True)

    # A/B Testing
    is_ab_test = models.BooleanField(default=False)
    ab_variant = models.CharField(max_length=1, blank=True)  # A or B
    ab_subject_b = models.CharField(max_length=200, blank=True)
    ab_test_percent = models.IntegerField(default=20)  # % to test before sending winner

    # Analytics
    sent_count = models.IntegerField(default=0)
    delivered_count = models.IntegerField(default=0)
    open_count = models.IntegerField(default=0)
    click_count = models.IntegerField(default=0)
    bounce_count = models.IntegerField(default=0)
    unsubscribe_count = models.IntegerField(default=0)
    complaint_count = models.IntegerField(default=0)

    # Revenue attribution
    revenue_attributed = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def open_rate(self):
        if self.delivered_count == 0:
            return 0
        return (self.open_count / self.delivered_count) * 100

    @property
    def click_rate(self):
        if self.delivered_count == 0:
            return 0
        return (self.click_count / self.delivered_count) * 100


class EmailSend(models.Model):
    """Individual email send records."""

    campaign = models.ForeignKey(
        EmailCampaign, on_delete=models.CASCADE,
        null=True, blank=True, related_name='sends'
    )
    sequence_step = models.ForeignKey(
        'SequenceStep', on_delete=models.CASCADE,
        null=True, blank=True
    )

    # Recipient
    subscription = models.ForeignKey(
        NewsletterSubscription, on_delete=models.SET_NULL,
        null=True, related_name='email_sends'
    )
    owner = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, related_name='email_sends'
    )
    email_address = models.EmailField()

    # Status
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('sent', 'Enviado'),
        ('delivered', 'Entregado'),
        ('opened', 'Abierto'),
        ('clicked', 'Clic'),
        ('bounced', 'Rebotado'),
        ('complained', 'Spam'),
        ('unsubscribed', 'Dado de baja'),
        ('failed', 'Fallido'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # AWS SES tracking
    ses_message_id = models.CharField(max_length=200, blank=True)

    # Timestamps
    sent_at = models.DateTimeField(null=True)
    delivered_at = models.DateTimeField(null=True)
    opened_at = models.DateTimeField(null=True)
    clicked_at = models.DateTimeField(null=True)
    bounced_at = models.DateTimeField(null=True)

    # Error tracking
    error_message = models.TextField(blank=True)
    bounce_type = models.CharField(max_length=50, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class EmailEvent(models.Model):
    """Detailed email events for analytics."""

    send = models.ForeignKey(
        EmailSend, on_delete=models.CASCADE,
        related_name='events'
    )

    EVENT_TYPES = [
        ('send', 'Enviado'),
        ('delivery', 'Entregado'),
        ('open', 'Abierto'),
        ('click', 'Clic'),
        ('bounce', 'Rebote'),
        ('complaint', 'Queja'),
        ('unsubscribe', 'Baja'),
    ]
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)

    # Click details
    link_url = models.URLField(blank=True)
    link_tag = models.CharField(max_length=100, blank=True)

    # Device info
    user_agent = models.CharField(max_length=500, blank=True)
    ip_address = models.GenericIPAddressField(null=True)

    timestamp = models.DateTimeField(auto_now_add=True)


class AutomatedSequence(models.Model):
    """Automated email sequences (drip campaigns)."""

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    TRIGGER_TYPES = [
        ('signup', 'Nueva suscripción'),
        ('purchase', 'Compra realizada'),
        ('appointment', 'Cita completada'),
        ('abandoned_cart', 'Carrito abandonado'),
        ('inactivity', 'Inactividad'),
        ('birthday', 'Cumpleaños mascota'),
        ('vaccination_due', 'Vacuna pendiente'),
        ('custom', 'Evento personalizado'),
    ]
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_TYPES)

    # Trigger conditions
    trigger_conditions = models.JSONField(default=dict)
    # e.g., {"days_inactive": 90, "min_purchases": 1}

    # Targeting
    segment = models.ForeignKey(
        CustomerSegment, on_delete=models.SET_NULL,
        null=True, blank=True
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']


class SequenceStep(models.Model):
    """Individual steps in an automated sequence."""

    sequence = models.ForeignKey(
        AutomatedSequence, on_delete=models.CASCADE,
        related_name='steps'
    )

    step_number = models.IntegerField()

    # Timing
    delay_days = models.IntegerField(default=0)
    delay_hours = models.IntegerField(default=0)
    send_time = models.TimeField(null=True)  # Preferred send time

    # Content
    template = models.ForeignKey(
        EmailTemplate, on_delete=models.SET_NULL,
        null=True, blank=True
    )
    subject = models.CharField(max_length=200)
    html_content = models.TextField()

    # Conditions
    skip_if = models.JSONField(default=dict)
    # {"already_purchased": true, "unsubscribed": true}

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sequence', 'step_number']
        unique_together = ['sequence', 'step_number']


class SequenceEnrollment(models.Model):
    """Track users enrolled in sequences."""

    sequence = models.ForeignKey(
        AutomatedSequence, on_delete=models.CASCADE,
        related_name='enrollments'
    )
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='sequence_enrollments'
    )

    current_step = models.IntegerField(default=0)
    next_send_at = models.DateTimeField(null=True)

    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('paused', 'Pausado'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)

    class Meta:
        unique_together = ['sequence', 'owner']
```

#### Email Marketing Service
```python
from django.conf import settings
from django.template import Template, Context
from django.utils import timezone
from datetime import timedelta
import boto3


class EmailMarketingService:
    """Email marketing operations."""

    def __init__(self):
        self.ses_client = boto3.client(
            'ses',
            region_name=settings.AWS_SES_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )

    def send_campaign(self, campaign: EmailCampaign) -> int:
        """Send campaign to all recipients."""

        from apps.marketing.tasks import send_campaign_batch

        # Get recipients from segment
        if campaign.segment:
            recipients = campaign.segment.get_members()
        else:
            recipients = NewsletterSubscription.objects.filter(
                status='active'
            )

        # Create send records
        sends = []
        for recipient in recipients:
            send = EmailSend.objects.create(
                campaign=campaign,
                subscription=recipient,
                owner=recipient.owner,
                email_address=recipient.email,
                status='pending'
            )
            sends.append(send.id)

        campaign.recipient_count = len(sends)
        campaign.status = 'sending'
        campaign.started_at = timezone.now()
        campaign.save()

        # Queue batch sends
        batch_size = 50
        for i in range(0, len(sends), batch_size):
            batch = sends[i:i + batch_size]
            send_campaign_batch.delay(campaign.id, batch)

        return len(sends)

    def send_single_email(self, send: EmailSend) -> bool:
        """Send a single email."""

        campaign = send.campaign
        subscription = send.subscription

        # Personalize content
        context = self._build_context(subscription)
        subject = self._render_template(campaign.subject, context)
        html_content = self._render_template(campaign.html_content, context)
        text_content = self._render_template(
            campaign.text_content or self._html_to_text(html_content),
            context
        )

        try:
            response = self.ses_client.send_email(
                Source=settings.DEFAULT_FROM_EMAIL,
                Destination={'ToAddresses': [send.email_address]},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {
                        'Html': {'Data': html_content},
                        'Text': {'Data': text_content}
                    }
                },
                ConfigurationSetName=settings.AWS_SES_CONFIGURATION_SET
            )

            send.ses_message_id = response['MessageId']
            send.status = 'sent'
            send.sent_at = timezone.now()
            send.save()

            return True

        except Exception as e:
            send.status = 'failed'
            send.error_message = str(e)
            send.save()
            return False

    def _build_context(self, subscription: NewsletterSubscription) -> dict:
        """Build personalization context."""

        owner = subscription.owner
        context = {
            'email': subscription.email,
            'first_name': subscription.first_name or 'Amigo',
            'unsubscribe_url': self._get_unsubscribe_url(subscription),
        }

        if owner:
            context.update({
                'owner_name': owner.first_name,
                'owner_full_name': owner.get_full_name(),
            })

            # Add pet info
            pets = owner.pets.all()
            if pets.exists():
                context['pet_name'] = pets.first().name
                context['pet_names'] = ', '.join([p.name for p in pets])

        return context

    def _render_template(self, content: str, context: dict) -> str:
        """Render template with context."""
        template = Template(content)
        return template.render(Context(context))

    def _get_unsubscribe_url(self, subscription: NewsletterSubscription) -> str:
        """Generate unsubscribe URL."""
        import hashlib
        token = hashlib.sha256(
            f"{subscription.email}{settings.SECRET_KEY}".encode()
        ).hexdigest()[:32]
        return f"{settings.SITE_URL}/email/unsubscribe/{subscription.id}/{token}/"

    def process_webhook(self, event_type: str, data: dict):
        """Process SES webhook events."""

        message_id = data.get('mail', {}).get('messageId')
        if not message_id:
            return

        try:
            send = EmailSend.objects.get(ses_message_id=message_id)
        except EmailSend.DoesNotExist:
            return

        # Create event record
        EmailEvent.objects.create(
            send=send,
            event_type=event_type,
            ip_address=data.get('ipAddress'),
            user_agent=data.get('userAgent', '')
        )

        # Update send status
        if event_type == 'delivery':
            send.status = 'delivered'
            send.delivered_at = timezone.now()
            send.campaign.delivered_count += 1

        elif event_type == 'open':
            if send.status != 'opened':
                send.status = 'opened'
                send.opened_at = timezone.now()
                send.campaign.open_count += 1

        elif event_type == 'click':
            if send.status != 'clicked':
                send.status = 'clicked'
                send.clicked_at = timezone.now()
                send.campaign.click_count += 1

        elif event_type == 'bounce':
            send.status = 'bounced'
            send.bounced_at = timezone.now()
            send.bounce_type = data.get('bounce', {}).get('bounceType', '')
            send.campaign.bounce_count += 1

            # Update subscription status
            if send.subscription:
                send.subscription.status = 'bounced'
                send.subscription.save()

        elif event_type == 'complaint':
            send.status = 'complained'
            send.campaign.complaint_count += 1

            if send.subscription:
                send.subscription.status = 'complained'
                send.subscription.save()

        send.save()
        send.campaign.save()


class SequenceService:
    """Automated sequence operations."""

    def enroll(self, owner, sequence: AutomatedSequence):
        """Enroll user in sequence."""

        # Check if already enrolled
        if SequenceEnrollment.objects.filter(
            sequence=sequence, owner=owner
        ).exists():
            return None

        # Calculate first send time
        first_step = sequence.steps.filter(is_active=True).first()
        if not first_step:
            return None

        next_send = timezone.now() + timedelta(
            days=first_step.delay_days,
            hours=first_step.delay_hours
        )

        enrollment = SequenceEnrollment.objects.create(
            sequence=sequence,
            owner=owner,
            current_step=0,
            next_send_at=next_send
        )

        return enrollment

    def process_sequences(self):
        """Process all due sequence sends."""

        from apps.marketing.tasks import send_sequence_email

        due_enrollments = SequenceEnrollment.objects.filter(
            status='active',
            next_send_at__lte=timezone.now()
        ).select_related('sequence', 'owner')

        for enrollment in due_enrollments:
            send_sequence_email.delay(enrollment.id)

    def send_step(self, enrollment: SequenceEnrollment):
        """Send current step and advance."""

        step = enrollment.sequence.steps.filter(
            step_number=enrollment.current_step + 1,
            is_active=True
        ).first()

        if not step:
            # Sequence complete
            enrollment.status = 'completed'
            enrollment.completed_at = timezone.now()
            enrollment.save()
            return

        # Check skip conditions
        if self._should_skip(enrollment.owner, step.skip_if):
            self._advance_to_next(enrollment, step)
            return

        # Create and send email
        send = EmailSend.objects.create(
            sequence_step=step,
            owner=enrollment.owner,
            email_address=enrollment.owner.email,
            status='pending'
        )

        EmailMarketingService().send_single_email(send)

        # Advance to next step
        self._advance_to_next(enrollment, step)

    def _advance_to_next(self, enrollment, current_step):
        """Advance to next step."""

        next_step = enrollment.sequence.steps.filter(
            step_number__gt=current_step.step_number,
            is_active=True
        ).first()

        if next_step:
            enrollment.current_step = current_step.step_number
            enrollment.next_send_at = timezone.now() + timedelta(
                days=next_step.delay_days,
                hours=next_step.delay_hours
            )
        else:
            enrollment.status = 'completed'
            enrollment.completed_at = timezone.now()

        enrollment.save()

    def _should_skip(self, owner, conditions: dict) -> bool:
        """Check if step should be skipped."""

        if conditions.get('already_purchased'):
            if owner.orders.filter(status='completed').exists():
                return True

        if conditions.get('has_appointment'):
            if owner.appointments.filter(
                start_time__gte=timezone.now()
            ).exists():
                return True

        return False
```

#### Celery Tasks
```python
from celery import shared_task


@shared_task
def send_campaign_batch(campaign_id: int, send_ids: list):
    """Send batch of campaign emails."""

    from apps.marketing.models import EmailCampaign, EmailSend
    from apps.marketing.services.email_marketing import EmailMarketingService

    campaign = EmailCampaign.objects.get(id=campaign_id)
    service = EmailMarketingService()

    for send_id in send_ids:
        send = EmailSend.objects.get(id=send_id)
        if send.status == 'pending':
            service.send_single_email(send)
            campaign.sent_count += 1
            campaign.save()

    # Check if campaign is complete
    pending = EmailSend.objects.filter(
        campaign=campaign, status='pending'
    ).count()

    if pending == 0:
        campaign.status = 'sent'
        campaign.completed_at = timezone.now()
        campaign.save()


@shared_task
def send_sequence_email(enrollment_id: int):
    """Send sequence email for enrollment."""

    from apps.marketing.models import SequenceEnrollment
    from apps.marketing.services.email_marketing import SequenceService

    enrollment = SequenceEnrollment.objects.get(id=enrollment_id)
    SequenceService().send_step(enrollment)


@shared_task
def process_automated_sequences():
    """Process all due automated sequences."""

    from apps.marketing.services.email_marketing import SequenceService
    SequenceService().process_sequences()


@shared_task
def update_segment_counts():
    """Update member counts for all segments."""

    from apps.marketing.models import CustomerSegment

    for segment in CustomerSegment.objects.filter(is_active=True):
        segment.member_count = segment.get_members().count()
        segment.last_calculated = timezone.now()
        segment.save()
```

### Test Cases
- [ ] Newsletter subscription double opt-in
- [ ] Campaign sends to segment
- [ ] Personalization tokens work
- [ ] Open/click tracking records
- [ ] Bounce handling updates status
- [ ] Unsubscribe works
- [ ] Automated sequence enrollment
- [ ] Sequence step progression
- [ ] A/B testing selects winner

### Definition of Done
- [ ] Full email marketing system
- [ ] Automated sequences working
- [ ] Analytics tracking complete
- [ ] SES webhooks configured
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-045: Email Integration (SES)
- T-054: CRM Owner Models
