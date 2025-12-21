# S-006: Omnichannel Communications

**Story Type:** User Story
**Priority:** Medium
**Epoch:** 4
**Status:** PENDING

## User Story

**As a** pet owner
**I want to** receive appointment reminders and order updates via my preferred channel
**So that** I never miss important communications about my pet

**As a** clinic staff member
**I want to** manage all customer communications in one place
**So that** I can respond efficiently without juggling multiple apps

## Acceptance Criteria

### Multi-Channel Support
- [ ] Email notifications working
- [ ] SMS notifications via Twilio
- [ ] WhatsApp Business API integration
- [ ] User can set channel preferences

### Reminder System
- [ ] Appointment reminders sent 24h before
- [ ] Appointment reminders sent 2h before
- [ ] Vaccination due reminders
- [ ] Prescription refill reminders
- [ ] Order status updates

### Escalation Logic
- [ ] If no confirmation via email, escalate to SMS
- [ ] If no response to SMS, escalate to WhatsApp
- [ ] Track delivery and read status
- [ ] Flag unresponsive contacts for follow-up

### Unified Inbox
- [ ] All incoming messages in one view
- [ ] Staff can respond from unified inbox
- [ ] Conversation history preserved
- [ ] AI can assist with responses

### AI Integration
- [ ] AI can send messages via any channel
- [ ] AI can check message delivery status
- [ ] AI can manage reminder schedules
- [ ] Customers can text/WhatsApp and AI responds

## Technical Requirements

### Package: django-omnichannel

```python
# models.py

class CommunicationChannel(models.Model):
    CHANNEL_TYPES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
        ('voice', 'Voice Call'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    channel_type = models.CharField(max_length=20, choices=CHANNEL_TYPES)
    identifier = models.CharField(max_length=255)  # email address or phone number
    is_verified = models.BooleanField(default=False)
    is_primary = models.BooleanField(default=False)
    preferences = models.JSONField(default=dict)  # notification preferences
    created_at = models.DateTimeField(auto_now_add=True)


class MessageTemplate(models.Model):
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=50)  # appointment_reminder, order_update, etc.
    subject_es = models.CharField(max_length=200, blank=True)
    subject_en = models.CharField(max_length=200, blank=True)
    body_es = models.TextField()
    body_en = models.TextField()
    channels = models.JSONField(default=list)  # ['email', 'sms', 'whatsapp']
    is_active = models.BooleanField(default=True)


class Message(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
    ]

    DIRECTION_CHOICES = [
        ('outbound', 'Outbound'),
        ('inbound', 'Inbound'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    channel = models.CharField(max_length=20)
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES)
    recipient = models.CharField(max_length=255)  # phone or email
    subject = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    external_id = models.CharField(max_length=255, blank=True)  # Twilio SID, etc.
    metadata = models.JSONField(default=dict)
    sent_at = models.DateTimeField(null=True)
    delivered_at = models.DateTimeField(null=True)
    read_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Link to related objects
    content_type = models.ForeignKey(ContentType, null=True, on_delete=models.SET_NULL)
    object_id = models.PositiveIntegerField(null=True)
    related_object = GenericForeignKey('content_type', 'object_id')


class ReminderSchedule(models.Model):
    REMINDER_TYPES = [
        ('appointment', 'Appointment Reminder'),
        ('vaccination', 'Vaccination Due'),
        ('prescription', 'Prescription Refill'),
        ('followup', 'Follow-up Visit'),
    ]

    reminder_type = models.CharField(max_length=50, choices=REMINDER_TYPES)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    related_object = GenericForeignKey('content_type', 'object_id')
    scheduled_for = models.DateTimeField()
    sent = models.BooleanField(default=False)
    channels_attempted = models.JSONField(default=list)
    confirmed = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True)


class EscalationRule(models.Model):
    reminder_type = models.CharField(max_length=50)
    step = models.IntegerField()
    channel = models.CharField(max_length=20)
    wait_hours = models.IntegerField()  # Hours to wait before escalating
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['reminder_type', 'step']
```

### Channel Services

```python
# services/channels.py

class EmailService:
    def send(self, to: str, subject: str, body: str, **kwargs) -> Message:
        # Use Django email backend
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [to])
        return Message.objects.create(
            channel='email',
            direction='outbound',
            recipient=to,
            subject=subject,
            body=body,
            status='sent'
        )


class SMSService:
    def __init__(self):
        self.client = TwilioClient(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )

    def send(self, to: str, body: str, **kwargs) -> Message:
        message = self.client.messages.create(
            body=body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=to
        )
        return Message.objects.create(
            channel='sms',
            direction='outbound',
            recipient=to,
            body=body,
            status='sent',
            external_id=message.sid
        )


class WhatsAppService:
    def __init__(self):
        self.client = WhatsAppBusinessAPI(
            settings.WHATSAPP_BUSINESS_ID,
            settings.WHATSAPP_ACCESS_TOKEN
        )

    def send(self, to: str, body: str, template: str = None, **kwargs) -> Message:
        if template:
            response = self.client.send_template(to, template, kwargs.get('template_params'))
        else:
            response = self.client.send_message(to, body)

        return Message.objects.create(
            channel='whatsapp',
            direction='outbound',
            recipient=to,
            body=body,
            status='sent',
            external_id=response['message_id']
        )


class OmnichannelService:
    def __init__(self):
        self.channels = {
            'email': EmailService(),
            'sms': SMSService(),
            'whatsapp': WhatsAppService(),
        }

    def send(self, user: User, message_type: str, context: dict, channel: str = None):
        """Send message via preferred or specified channel"""
        if channel:
            channels_to_try = [channel]
        else:
            channels_to_try = self._get_preferred_channels(user, message_type)

        template = MessageTemplate.objects.get(template_type=message_type)

        for channel in channels_to_try:
            try:
                service = self.channels[channel]
                return service.send(
                    to=self._get_identifier(user, channel),
                    subject=self._render(template.subject_es, context),
                    body=self._render(template.body_es, context)
                )
            except Exception as e:
                logger.error(f"Failed to send via {channel}: {e}")
                continue

        raise AllChannelsFailedError("Could not send via any channel")
```

### AI Tools (Epoch 4)

```python
COMMUNICATION_TOOLS = [
    {
        "name": "send_message",
        "description": "Send a message to a user via their preferred channel",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
                "message": {"type": "string"},
                "channel": {"type": "string", "enum": ["email", "sms", "whatsapp"]}
            },
            "required": ["user_id", "message"]
        }
    },
    {
        "name": "get_unread_messages",
        "description": "Get unread incoming messages",
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "name": "schedule_reminder",
        "description": "Schedule a reminder for a user",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
                "reminder_type": {"type": "string"},
                "scheduled_for": {"type": "string", "format": "date-time"},
                "message": {"type": "string"}
            },
            "required": ["user_id", "reminder_type", "scheduled_for"]
        }
    },
    {
        "name": "check_message_status",
        "description": "Check delivery status of a sent message",
        "parameters": {
            "type": "object",
            "properties": {
                "message_id": {"type": "integer"}
            },
            "required": ["message_id"]
        }
    },
    {
        "name": "get_conversation_history",
        "description": "Get message history with a user",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
                "limit": {"type": "integer", "default": 20}
            },
            "required": ["user_id"]
        }
    }
]
```

## Escalation Flow Example

```
Appointment Reminder for Tomorrow:

Step 1: 24 hours before
├── Send email reminder
├── Wait 2 hours
└── Check: Confirmed? → Done

Step 2: 22 hours before (if not confirmed)
├── Send SMS reminder
├── Wait 2 hours
└── Check: Confirmed? → Done

Step 3: 20 hours before (if not confirmed)
├── Send WhatsApp message
├── Wait until 2 hours before
└── Check: Confirmed? → Done

Step 4: 2 hours before (if not confirmed)
├── Send final WhatsApp reminder
├── Flag for staff attention
└── Staff may call directly
```

## Definition of Done

- [ ] Email notifications working
- [ ] SMS via Twilio working
- [ ] WhatsApp Business API integrated
- [ ] User can set communication preferences
- [ ] Escalation logic implemented
- [ ] Unified inbox displays all messages
- [ ] Staff can respond from inbox
- [ ] AI can send messages and check status
- [ ] Webhook handlers for delivery receipts
- [ ] Tests written and passing (>95% coverage)

## Dependencies

- S-001: Foundation + AI Core
- S-002: AI Chat Interface
- S-004: Appointment Booking (for reminders)
- Twilio account configured
- WhatsApp Business API approved

## Notes

- WhatsApp Business API requires Facebook Business verification
- Template messages required for WhatsApp (pre-approved)
- SMS costs ~$0.05 per message in Mexico
- Consider rate limiting to avoid spam flags

## Development Process

**Before implementing this story**, review and follow the **23-Step TDD Cycle** in:
- `CLAUDE.md` - Global development workflow
- `planning/TASK_BREAKDOWN.md` - Specific tasks for this story

Tests must be written before implementation. >95% coverage required.
