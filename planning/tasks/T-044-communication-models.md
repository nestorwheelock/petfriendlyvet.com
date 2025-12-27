# T-044: Communication Channel Models

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md and [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement models for unified multi-channel communications
**Related Story**: S-006
**Epoch**: 4
**Estimate**: 4 hours

### Constraints
**Allowed File Paths**: apps/communications/
**Forbidden Paths**: None

### Deliverables
- [ ] Message model
- [ ] Conversation model
- [ ] Channel configuration models
- [ ] Template models
- [ ] Delivery tracking

### Implementation Details

#### Models
```python
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

User = get_user_model()


class Channel(models.Model):
    """Communication channel configuration."""

    CHANNEL_TYPES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
        ('push', 'Push Notification'),
        ('voice', 'Voice Call'),
    ]

    name = models.CharField(max_length=100)
    channel_type = models.CharField(max_length=20, choices=CHANNEL_TYPES)

    # Configuration
    is_active = models.BooleanField(default=True)
    config = models.JSONField(default=dict)
    # Email: {'smtp_host', 'smtp_port', 'from_email', ...}
    # SMS: {'provider': 'twilio', 'account_sid', 'auth_token', ...}
    # WhatsApp: {'phone_number_id', 'access_token', ...}

    # Rate limits
    rate_limit_per_hour = models.IntegerField(default=100)
    rate_limit_per_day = models.IntegerField(default=1000)

    # Cost tracking
    cost_per_message = models.DecimalField(
        max_digits=10, decimal_places=4, default=0
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Conversation(models.Model):
    """Threaded conversation with a contact."""

    STATUS_CHOICES = [
        ('active', 'Activa'),
        ('pending', 'Pendiente respuesta'),
        ('resolved', 'Resuelta'),
        ('archived', 'Archivada'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Baja'),
        ('normal', 'Normal'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]

    # Participants
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='conversations'
    )
    assigned_to = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_conversations'
    )

    # Context
    subject = models.CharField(max_length=500, blank=True)
    pet = models.ForeignKey(
        'vet_clinic.Pet', on_delete=models.SET_NULL,
        null=True, blank=True
    )
    appointment = models.ForeignKey(
        'appointments.Appointment', on_delete=models.SET_NULL,
        null=True, blank=True
    )
    order = models.ForeignKey(
        'store.Order', on_delete=models.SET_NULL,
        null=True, blank=True
    )

    # Status
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='active'
    )
    priority = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, default='normal'
    )

    # Tracking
    last_message_at = models.DateTimeField(null=True)
    last_customer_message_at = models.DateTimeField(null=True)
    last_staff_message_at = models.DateTimeField(null=True)
    unread_count = models.IntegerField(default=0)

    # Tags for organization
    tags = models.JSONField(default=list)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_message_at']


class Message(models.Model):
    """Individual message in any channel."""

    DIRECTION_CHOICES = [
        ('inbound', 'Entrante'),
        ('outbound', 'Saliente'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('queued', 'En cola'),
        ('sent', 'Enviado'),
        ('delivered', 'Entregado'),
        ('read', 'Leído'),
        ('failed', 'Fallido'),
    ]

    # Conversation link
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE,
        related_name='messages'
    )

    # Channel
    channel = models.ForeignKey(Channel, on_delete=models.PROTECT)

    # Direction
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)

    # Sender/Recipient
    from_user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='sent_messages'
    )
    to_contact = models.CharField(max_length=200)  # email, phone, etc.

    # Content
    subject = models.CharField(max_length=500, blank=True)
    body = models.TextField()
    body_html = models.TextField(blank=True)

    # Attachments
    attachments = models.JSONField(default=list)
    # [{"name": "file.pdf", "url": "...", "type": "application/pdf"}]

    # Template used
    template = models.ForeignKey(
        'MessageTemplate', on_delete=models.SET_NULL,
        null=True, blank=True
    )

    # Status tracking
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending'
    )
    error_message = models.TextField(blank=True)

    # External IDs
    external_id = models.CharField(max_length=255, blank=True, db_index=True)
    # Twilio SID, SendGrid ID, WhatsApp message ID, etc.

    # Delivery tracking
    sent_at = models.DateTimeField(null=True)
    delivered_at = models.DateTimeField(null=True)
    read_at = models.DateTimeField(null=True)
    failed_at = models.DateTimeField(null=True)

    # Metadata
    metadata = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']


class MessageTemplate(models.Model):
    """Reusable message templates."""

    TEMPLATE_TYPES = [
        ('appointment_reminder', 'Recordatorio de cita'),
        ('appointment_confirmation', 'Confirmación de cita'),
        ('vaccination_reminder', 'Recordatorio de vacuna'),
        ('order_confirmation', 'Confirmación de pedido'),
        ('order_ready', 'Pedido listo'),
        ('payment_reminder', 'Recordatorio de pago'),
        ('welcome', 'Bienvenida'),
        ('follow_up', 'Seguimiento'),
        ('marketing', 'Marketing'),
        ('custom', 'Personalizado'),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES)

    # Channel support
    channels = models.JSONField(default=list)
    # ['email', 'sms', 'whatsapp']

    # Content by channel
    subject = models.CharField(max_length=500, blank=True)  # For email
    body_text = models.TextField()  # Plain text / SMS
    body_html = models.TextField(blank=True)  # Email HTML

    # WhatsApp specific
    whatsapp_template_name = models.CharField(max_length=100, blank=True)
    whatsapp_template_id = models.CharField(max_length=100, blank=True)

    # Variables
    variables = models.JSONField(default=list)
    # ['owner_name', 'pet_name', 'appointment_date', ...]

    # Settings
    is_active = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=False)

    # Translations
    translations = models.JSONField(default=dict)
    # {'en': {'subject': '...', 'body_text': '...'}, 'es': {...}}

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ContactPreference(models.Model):
    """User communication preferences."""

    owner = models.OneToOneField(User, on_delete=models.CASCADE)

    # Preferred channel
    preferred_channel = models.CharField(
        max_length=20,
        choices=Channel.CHANNEL_TYPES,
        default='whatsapp'
    )

    # Contact details by channel
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    whatsapp = models.CharField(max_length=20, blank=True)

    # Opt-ins by type
    appointment_reminders = models.BooleanField(default=True)
    vaccination_reminders = models.BooleanField(default=True)
    order_updates = models.BooleanField(default=True)
    marketing = models.BooleanField(default=False)
    promotions = models.BooleanField(default=False)

    # Quiet hours
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)

    # Language
    language = models.CharField(max_length=5, default='es')

    # Escalation
    escalation_after_minutes = models.IntegerField(default=60)
    escalation_channels = models.JSONField(default=list)
    # ['sms', 'voice']

    updated_at = models.DateTimeField(auto_now=True)


class DeliveryAttempt(models.Model):
    """Track delivery attempts for a message."""

    message = models.ForeignKey(
        Message, on_delete=models.CASCADE,
        related_name='delivery_attempts'
    )

    attempt_number = models.IntegerField()
    channel = models.ForeignKey(Channel, on_delete=models.PROTECT)

    status = models.CharField(max_length=20)
    response = models.JSONField(default=dict)
    error = models.TextField(blank=True)

    attempted_at = models.DateTimeField(auto_now_add=True)


class MessageEvent(models.Model):
    """Webhook events for message status updates."""

    EVENT_TYPES = [
        ('delivered', 'Entregado'),
        ('read', 'Leído'),
        ('clicked', 'Click'),
        ('bounced', 'Rebotado'),
        ('complained', 'Marcado spam'),
        ('unsubscribed', 'Desuscrito'),
    ]

    message = models.ForeignKey(
        Message, on_delete=models.CASCADE,
        related_name='events'
    )

    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    payload = models.JSONField(default=dict)

    occurred_at = models.DateTimeField()
    received_at = models.DateTimeField(auto_now_add=True)
```

### Test Cases
- [ ] Channel CRUD works
- [ ] Conversation creation
- [ ] Message creation with conversation
- [ ] Template rendering
- [ ] Preference saving
- [ ] Delivery attempt tracking
- [ ] Event webhook handling

### Definition of Done
- [ ] All models migrated
- [ ] Admin registered
- [ ] Relationships correct
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-001: Django Project Setup
