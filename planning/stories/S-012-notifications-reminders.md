# S-012: Notifications & Reminders

**Story Type:** User Story
**Priority:** High
**Epoch:** 2 (with Appointments)
**Status:** PENDING
**Module:** django-omnichannel

## User Story

**As a** pet owner
**I want to** receive timely reminders about my pet's care
**So that** I never miss important appointments or preventive care

**As a** clinic owner
**I want to** automatically send reminders to clients
**So that** I reduce no-shows and ensure pets receive timely care

**As a** pet owner
**I want to** choose how I receive notifications
**So that** I get information through my preferred channels

## Acceptance Criteria

### Reminder Types
- [ ] Appointment reminders (24hr, 2hr before)
- [ ] Vaccination due reminders
- [ ] Medication refill reminders
- [ ] Follow-up care reminders
- [ ] Annual checkup reminders
- [ ] Preventive care reminders (flea/tick, heartworm)
- [ ] Birthday greetings (pet birthdays)
- [ ] Post-visit follow-up

### Delivery Channels
- [ ] Email notifications
- [ ] SMS text messages
- [ ] WhatsApp messages
- [ ] Push notifications (future)
- [ ] In-app notifications

### User Preferences
- [ ] Choose preferred channel(s)
- [ ] Set quiet hours (no notifications)
- [ ] Opt-out of specific reminder types
- [ ] Frequency preferences
- [ ] Language preference per channel
- [ ] Unsubscribe with one click

### Confirmation Tracking
- [ ] Track delivery status (sent, delivered, read)
- [ ] Track responses (confirmed, rescheduled, cancelled)
- [ ] Automatic follow-up if no response
- [ ] Escalation to phone call for critical reminders

### Smart Scheduling
- [ ] Optimal send time based on user behavior
- [ ] Timezone awareness
- [ ] Avoid duplicate reminders across channels
- [ ] Batch similar reminders together
- [ ] Respect channel-specific rate limits

### Templates & Personalization
- [ ] Customizable message templates
- [ ] Personalized with pet/owner names
- [ ] Multilingual support
- [ ] Include relevant links (reschedule, directions)
- [ ] Clinic branding

## Technical Requirements

### Models

```python
class NotificationPreference(models.Model):
    """User notification preferences"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Channel preferences
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)
    whatsapp_enabled = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=True)

    # Primary channel
    primary_channel = models.CharField(max_length=20, default='whatsapp')

    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_start = models.TimeField(null=True, blank=True)  # e.g., 22:00
    quiet_end = models.TimeField(null=True, blank=True)  # e.g., 08:00
    timezone = models.CharField(max_length=50, default='America/Cancun')

    # Reminder types (opt-out list)
    disabled_reminder_types = models.JSONField(default=list)
    # ["birthday", "marketing", ...]

    # Language
    preferred_language = models.CharField(max_length=10, default='es')

    updated_at = models.DateTimeField(auto_now=True)


class ReminderType(models.Model):
    """Types of reminders the system can send"""
    code = models.CharField(max_length=50, unique=True)
    # appointment_24h, vaccination_due, refill_reminder, etc.

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # Timing
    default_advance_days = models.IntegerField(default=0)
    default_advance_hours = models.IntegerField(default=0)

    # Priority
    priority = models.CharField(max_length=20, default='normal')
    # critical, high, normal, low
    is_transactional = models.BooleanField(default=True)
    # Transactional = always send, Marketing = respect opt-out

    # Escalation
    requires_confirmation = models.BooleanField(default=False)
    escalation_enabled = models.BooleanField(default=False)
    escalation_hours = models.IntegerField(default=4)  # Hours before escalating

    # Status
    is_active = models.BooleanField(default=True)


class NotificationTemplate(models.Model):
    """Message templates for notifications"""
    reminder_type = models.ForeignKey(ReminderType, on_delete=models.CASCADE)
    channel = models.CharField(max_length=20)  # email, sms, whatsapp
    language = models.CharField(max_length=10, default='es')

    # Content
    subject = models.CharField(max_length=200, blank=True)  # For email
    body = models.TextField()
    # Supports variables: {{pet_name}}, {{owner_name}}, {{appointment_date}}, etc.

    # For WhatsApp templates
    whatsapp_template_name = models.CharField(max_length=100, blank=True)
    whatsapp_template_id = models.CharField(max_length=100, blank=True)

    # Actions
    include_confirm_button = models.BooleanField(default=False)
    include_reschedule_link = models.BooleanField(default=False)
    include_cancel_link = models.BooleanField(default=False)
    include_directions_link = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['reminder_type', 'channel', 'language']


class ScheduledReminder(models.Model):
    """Reminders scheduled to be sent"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    # References
    reminder_type = models.ForeignKey(ReminderType, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pet = models.ForeignKey(
        'vet_clinic.Pet', on_delete=models.CASCADE, null=True, blank=True
    )

    # Related objects (polymorphic reference)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    object_id = models.PositiveIntegerField(null=True)
    related_object = GenericForeignKey('content_type', 'object_id')
    # Could be Appointment, Vaccination, Prescription, etc.

    # Scheduling
    scheduled_for = models.DateTimeField()
    channel = models.CharField(max_length=20)

    # Content (pre-rendered)
    subject = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    language = models.CharField(max_length=10)

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)

    # External IDs for tracking
    external_id = models.CharField(max_length=100, blank=True)
    # Message ID from Twilio, SendGrid, etc.

    # Retry tracking
    attempt_count = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    next_retry_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['scheduled_for']
        indexes = [
            models.Index(fields=['status', 'scheduled_for']),
            models.Index(fields=['user', 'status']),
        ]


class ReminderResponse(models.Model):
    """Responses to reminders that require confirmation"""
    RESPONSE_TYPES = [
        ('confirmed', 'Confirmed'),
        ('rescheduled', 'Rescheduled'),
        ('cancelled', 'Cancelled'),
        ('no_response', 'No Response'),
    ]

    reminder = models.ForeignKey(ScheduledReminder, on_delete=models.CASCADE)
    response_type = models.CharField(max_length=20, choices=RESPONSE_TYPES)
    response_text = models.TextField(blank=True)  # If they replied with text
    response_channel = models.CharField(max_length=20)

    # For rescheduled
    new_datetime = models.DateTimeField(null=True, blank=True)

    received_at = models.DateTimeField(auto_now_add=True)


class ReminderEscalation(models.Model):
    """Escalation when reminder not responded to"""
    ESCALATION_TYPES = [
        ('retry_same', 'Retry Same Channel'),
        ('try_alternate', 'Try Alternate Channel'),
        ('phone_call', 'Phone Call Required'),
        ('staff_alert', 'Alert Staff'),
    ]

    reminder = models.ForeignKey(ScheduledReminder, on_delete=models.CASCADE)
    escalation_type = models.CharField(max_length=20, choices=ESCALATION_TYPES)
    escalated_at = models.DateTimeField(auto_now_add=True)

    # Result
    result = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    handled_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    handled_at = models.DateTimeField(null=True, blank=True)


class VaccinationReminder(models.Model):
    """Specific tracking for vaccination due reminders"""
    pet = models.ForeignKey('vet_clinic.Pet', on_delete=models.CASCADE)
    vaccination_type = models.CharField(max_length=100)

    # Due date calculation
    last_vaccination_date = models.DateField(null=True)
    due_date = models.DateField()
    grace_period_days = models.IntegerField(default=14)
    overdue_date = models.DateField()

    # Reminder schedule
    reminder_30_days = models.ForeignKey(
        ScheduledReminder, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+'
    )
    reminder_7_days = models.ForeignKey(
        ScheduledReminder, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+'
    )
    reminder_due = models.ForeignKey(
        ScheduledReminder, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+'
    )
    reminder_overdue = models.ForeignKey(
        ScheduledReminder, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+'
    )

    # Status
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    appointment = models.ForeignKey(
        'appointments.Appointment', on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ['due_date']
```

### AI Tools

```python
NOTIFICATION_TOOLS = [
    {
        "name": "get_notification_preferences",
        "description": "Get user's notification preferences",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"}
            }
        }
    },
    {
        "name": "update_notification_preferences",
        "description": "Update user's notification preferences",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
                "email_enabled": {"type": "boolean"},
                "sms_enabled": {"type": "boolean"},
                "whatsapp_enabled": {"type": "boolean"},
                "primary_channel": {"type": "string"},
                "quiet_hours_enabled": {"type": "boolean"},
                "quiet_start": {"type": "string"},
                "quiet_end": {"type": "string"}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "get_upcoming_reminders",
        "description": "Get upcoming scheduled reminders for a user",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
                "days_ahead": {"type": "integer", "default": 30}
            }
        }
    },
    {
        "name": "get_vaccination_schedule",
        "description": "Get vaccination due dates for a pet",
        "parameters": {
            "type": "object",
            "properties": {
                "pet_id": {"type": "integer"}
            },
            "required": ["pet_id"]
        }
    },
    {
        "name": "send_reminder_now",
        "description": "Send an immediate reminder (staff only)",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
                "reminder_type": {"type": "string"},
                "message": {"type": "string"},
                "channel": {"type": "string"}
            },
            "required": ["user_id", "reminder_type", "message"]
        }
    },
    {
        "name": "get_unconfirmed_appointments",
        "description": "Get appointments awaiting confirmation",
        "parameters": {
            "type": "object",
            "properties": {
                "date_range": {"type": "string"}
            }
        }
    },
    {
        "name": "escalate_reminder",
        "description": "Escalate an unresponded reminder",
        "parameters": {
            "type": "object",
            "properties": {
                "reminder_id": {"type": "integer"},
                "escalation_type": {"type": "string"}
            },
            "required": ["reminder_id", "escalation_type"]
        }
    }
]
```

## Example AI Conversations

### Setting Preferences (Customer)
```
Owner: I don't want text messages, just WhatsApp

AI: I'll update your notification preferences.

    Current settings for Maria Garcia:

    ✓ WhatsApp: Enabled (Primary)
    ✗ SMS: Disabled
    ✓ Email: Enabled
    ✗ Quiet Hours: Not set

    You'll receive reminders through WhatsApp for:
    • Appointment reminders
    • Vaccination due dates
    • Prescription refills
    • Follow-up care

    Is there anything else you'd like to adjust?

Owner: Actually, no notifications after 9pm

AI: Updated! I've set quiet hours from 9:00 PM to 8:00 AM.

    During quiet hours, we'll hold non-urgent notifications
    and send them in the morning.

    Emergency notifications (like urgent prescription issues)
    will still come through immediately.
```

### Vaccination Reminder
```
AI (WhatsApp): Hola Maria! 🐕

    Luna's rabies vaccination is due in 30 days
    (January 15, 2026).

    Would you like to schedule her appointment now?

    [Book Appointment] [Remind Me Later] [Already Scheduled]

Owner: Book Appointment

AI: I can help you book Luna's vaccination appointment.

    Available times for rabies vaccination:
    • Mon Jan 13: 10:00 AM, 2:00 PM, 4:00 PM
    • Tue Jan 14: 9:00 AM, 11:00 AM, 3:00 PM
    • Wed Jan 15: 10:00 AM, 1:00 PM

    Which works best for you?
```

### Appointment Confirmation Flow
```
AI (WhatsApp, 24 hours before):
    Recordatorio de cita 📅

    Mañana tienes cita en Pet-Friendly:

    Mascota: Luna
    Servicio: Vacunación antirrábica
    Fecha: Miércoles, 15 de enero
    Hora: 10:00 AM

    [Confirmar] [Reprogramar] [Cancelar]

--- No response after 4 hours ---

AI (SMS fallback):
    Pet-Friendly: Cita mañana 10AM para Luna.
    Confirma respondiendo SI o llama 998-316-2438

--- Still no response after 2 more hours ---

AI → Staff Alert:
    ⚠️ Unconfirmed appointment requiring attention

    Owner: Maria Garcia
    Pet: Luna
    Appointment: Tomorrow 10:00 AM
    Reminders sent: WhatsApp (no read), SMS (delivered)

    Action needed: Phone call recommended

    [Mark Confirmed] [Cancel Appointment] [Call Now]
```

## Reminder Schedule Configuration

### Default Reminder Timing

| Reminder Type | Timing | Channels |
|---------------|--------|----------|
| Appointment | 24hr, 2hr before | WhatsApp, SMS, Email |
| Vaccination Due | 30 days, 7 days, due date, overdue | WhatsApp, Email |
| Refill Reminder | 7 days before empty | WhatsApp |
| Annual Checkup | 11 months after last | Email |
| Follow-up | Per vet instructions | WhatsApp |
| Birthday | Day of | WhatsApp |

### Escalation Logic

```
Appointment Confirmation:
├── T-24h: Send reminder (primary channel)
│   └── If no response after 4h:
│       ├── T-20h: Retry on alternate channel
│       │   └── If no response after 4h:
│       │       ├── T-16h: Alert staff for phone call
│       │       └── If critical: Auto-call with IVR
└── T-2h: Final reminder (always send)
```

## Definition of Done

- [ ] NotificationPreference model and UI
- [ ] ReminderType configuration
- [ ] Template system with variables
- [ ] Multi-channel delivery (Email, SMS, WhatsApp)
- [ ] Scheduled reminder processing (Celery)
- [ ] Confirmation tracking and responses
- [ ] Escalation workflow
- [ ] Vaccination reminder automation
- [ ] Quiet hours respect
- [ ] Unsubscribe functionality
- [ ] Delivery status webhooks
- [ ] Tests written and passing (>95% coverage)

## Dependencies

- S-001: Foundation (user model)
- S-003: Pet Profiles (pet reference)
- S-004: Appointments (appointment reminders)
- S-006: Omnichannel (delivery channels)
- S-010: Pharmacy (refill reminders)

## Notes

- WhatsApp Business API requires pre-approved templates
- SMS costs per message - consider batching
- Celery Beat for scheduled reminder processing
- Consider time zone edge cases
- GDPR/consent requirements for marketing messages
