# Communications Module

The `apps.communications` module provides omnichannel messaging capabilities including email, SMS, WhatsApp, voice calls, message templates, and reminder scheduling.

## Table of Contents

- [Overview](#overview)
- [Models](#models)
  - [CommunicationChannel](#communicationchannel)
  - [MessageTemplate](#messagetemplate)
  - [Message](#message)
  - [ReminderSchedule](#reminderschedule)
  - [EscalationRule](#escalationrule)
- [Workflows](#workflows)
- [Integration Points](#integration-points)
- [Query Examples](#query-examples)
- [Testing](#testing)

## Overview

The communications module provides:

- **Channel Management** - User preferences for contact channels
- **Message Templates** - Bilingual templates for notifications
- **Message Tracking** - Track sent/delivered/read status
- **Reminder Scheduling** - Automated reminder delivery
- **Escalation Rules** - Multi-channel escalation

## Models

Location: `apps/communications/models.py`

### CommunicationChannel

User communication channel preferences.

```python
CHANNEL_TYPES = [
    ('email', 'Email'),
    ('sms', 'SMS'),
    ('whatsapp', 'WhatsApp'),
    ('voice', 'Voice Call'),
]

class CommunicationChannel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='communication_channels')
    channel_type = models.CharField(max_length=20, choices=CHANNEL_TYPES)
    identifier = models.CharField(max_length=255)  # Email or phone
    is_verified = models.BooleanField(default=False)
    is_primary = models.BooleanField(default=False)
    preferences = models.JSONField(default=dict)
```

### MessageTemplate

Bilingual message templates.

```python
class MessageTemplate(models.Model):
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=50)
    subject_es = models.CharField(max_length=200, blank=True)
    subject_en = models.CharField(max_length=200, blank=True)
    body_es = models.TextField()
    body_en = models.TextField()
    channels = models.JSONField(default=list)  # Supported channels
    is_active = models.BooleanField(default=True)
```

### Message

Individual message record with tracking.

```python
STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('sent', 'Sent'),
    ('delivered', 'Delivered'),
    ('read', 'Read'),
    ('failed', 'Failed'),
]

class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES)
    recipient = models.CharField(max_length=255)
    subject = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    external_id = models.CharField(max_length=255, blank=True)  # Provider ID
    metadata = models.JSONField(default=dict)

    sent_at = models.DateTimeField(null=True)
    delivered_at = models.DateTimeField(null=True)
    read_at = models.DateTimeField(null=True)

    # Generic relation to related object
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True)
    object_id = models.PositiveIntegerField(null=True)
    related_object = GenericForeignKey('content_type', 'object_id')
```

### ReminderSchedule

Scheduled reminders with confirmation tracking.

```python
REMINDER_TYPES = [
    ('appointment', 'Appointment Reminder'),
    ('vaccination', 'Vaccination Due'),
    ('prescription', 'Prescription Refill'),
    ('followup', 'Follow-up Visit'),
]

class ReminderSchedule(models.Model):
    reminder_type = models.CharField(max_length=50, choices=REMINDER_TYPES)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    related_object = GenericForeignKey('content_type', 'object_id')

    scheduled_for = models.DateTimeField()
    sent = models.BooleanField(default=False)
    channels_attempted = models.JSONField(default=list)
    confirmed = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True)

    message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
```

### EscalationRule

Multi-channel escalation configuration.

```python
class EscalationRule(models.Model):
    reminder_type = models.CharField(max_length=50)
    step = models.IntegerField()  # 1, 2, 3...
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    wait_hours = models.IntegerField()  # Hours before next step
    is_active = models.BooleanField(default=True)
```

## Workflows

### Sending a Message

```python
from apps.communications.models import Message
from django.utils import timezone

message = Message.objects.create(
    user=customer,
    channel='whatsapp',
    direction='outbound',
    recipient='+52 55 1234 5678',
    body='Your appointment is confirmed for tomorrow at 10 AM.',
    status='pending',
)

# After sending
message.status = 'sent'
message.sent_at = timezone.now()
message.external_id = 'whatsapp_msg_123'
message.save()
```

### Scheduling Reminders

```python
from apps.communications.models import ReminderSchedule
from datetime import timedelta
from django.utils import timezone

ReminderSchedule.objects.create(
    reminder_type='appointment',
    content_type=ContentType.objects.get_for_model(Appointment),
    object_id=appointment.pk,
    scheduled_for=appointment.date - timedelta(hours=24),
    message='Reminder: Appointment tomorrow at {time}',
)
```

### Escalation Flow

```python
# Define escalation rules
EscalationRule.objects.create(reminder_type='appointment', step=1, channel='email', wait_hours=24)
EscalationRule.objects.create(reminder_type='appointment', step=2, channel='sms', wait_hours=12)
EscalationRule.objects.create(reminder_type='appointment', step=3, channel='whatsapp', wait_hours=6)
EscalationRule.objects.create(reminder_type='appointment', step=4, channel='voice', wait_hours=2)
```

## Integration Points

### With Appointments

```python
from apps.appointments.models import Appointment

# Schedule reminder when appointment created
def on_appointment_created(appointment):
    ReminderSchedule.objects.create(
        reminder_type='appointment',
        content_type=ContentType.objects.get_for_model(Appointment),
        object_id=appointment.pk,
        scheduled_for=appointment.datetime - timedelta(hours=24),
    )
```

### With Vaccinations

```python
# Vaccination due reminders
from apps.pets.models import Vaccination

due_soon = Vaccination.objects.filter(next_due_date__lte=date.today() + timedelta(days=14))
for vacc in due_soon:
    ReminderSchedule.objects.create(
        reminder_type='vaccination',
        content_type=ContentType.objects.get_for_model(Vaccination),
        object_id=vacc.pk,
        scheduled_for=timezone.now() + timedelta(hours=1),
    )
```

## Query Examples

```python
from apps.communications.models import Message, ReminderSchedule
from django.utils import timezone
from datetime import timedelta

# Pending reminders to send
due = ReminderSchedule.objects.filter(
    sent=False,
    scheduled_for__lte=timezone.now()
)

# Unconfirmed reminders (may need escalation)
unconfirmed = ReminderSchedule.objects.filter(
    sent=True,
    confirmed=False,
    scheduled_for__lte=timezone.now() - timedelta(hours=24)
)

# Failed messages
failed = Message.objects.filter(status='failed')

# User's primary channel
primary = CommunicationChannel.objects.filter(user=user, is_primary=True).first()

# Message delivery rate
from django.db.models import Count
delivery_stats = Message.objects.filter(direction='outbound').values('status').annotate(
    count=Count('id')
)
```

## Testing

Location: `tests/test_communications.py`

```bash
python -m pytest tests/test_communications.py -v
```
