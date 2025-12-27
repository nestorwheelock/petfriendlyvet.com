# T-030: Reminder & Notification Models

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md and [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement reminder and notification system models
**Related Story**: S-012
**Epoch**: 2
**Estimate**: 3 hours

### Constraints
**Allowed File Paths**: apps/notifications/models/
**Forbidden Paths**: None

### Deliverables
- [ ] NotificationTemplate model
- [ ] ScheduledReminder model
- [ ] NotificationLog model
- [ ] User preferences model
- [ ] Reminder rules engine

### Implementation Details

#### Models
```python
class NotificationTemplate(models.Model):
    """Templates for notifications."""

    CHANNELS = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
        ('push', 'Push Notification'),
    ]

    TRIGGER_TYPES = [
        ('appointment_reminder', 'Appointment Reminder'),
        ('appointment_confirmation', 'Appointment Confirmation'),
        ('appointment_cancelled', 'Appointment Cancelled'),
        ('vaccination_due', 'Vaccination Due'),
        ('vaccination_overdue', 'Vaccination Overdue'),
        ('order_confirmation', 'Order Confirmation'),
        ('order_shipped', 'Order Shipped'),
        ('prescription_ready', 'Prescription Ready'),
        ('payment_reminder', 'Payment Reminder'),
        ('review_request', 'Review Request'),
        ('birthday', 'Pet Birthday'),
        ('custom', 'Custom'),
    ]

    name = models.CharField(max_length=200)
    trigger_type = models.CharField(max_length=50, choices=TRIGGER_TYPES)
    channel = models.CharField(max_length=20, choices=CHANNELS)

    # Content
    subject = models.CharField(max_length=200, blank=True)  # For email
    subject_es = models.CharField(max_length=200, blank=True)
    subject_en = models.CharField(max_length=200, blank=True)

    body = models.TextField()
    body_es = models.TextField()
    body_en = models.TextField()

    # Template variables: {{ pet_name }}, {{ owner_name }}, {{ date }}, etc.

    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['trigger_type', 'channel']


class NotificationPreference(models.Model):
    """User notification preferences."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_prefs')

    # Channel preferences
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=True)
    whatsapp_enabled = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=True)

    # Preferred channel order
    preferred_channel = models.CharField(max_length=20, default='whatsapp')

    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(default=time(22, 0))
    quiet_hours_end = models.TimeField(default=time(8, 0))

    # Frequency limits
    max_per_day = models.IntegerField(default=10)

    # Category preferences
    appointment_reminders = models.BooleanField(default=True)
    vaccination_reminders = models.BooleanField(default=True)
    promotional = models.BooleanField(default=True)
    order_updates = models.BooleanField(default=True)

    updated_at = models.DateTimeField(auto_now=True)


class ScheduledReminder(models.Model):
    """Scheduled reminders to send."""

    STATUS = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('skipped', 'Skipped'),
    ]

    # What to remind about
    reminder_type = models.CharField(max_length=50)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    # Who to remind
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reminders')
    channel = models.CharField(max_length=20)

    # When
    scheduled_for = models.DateTimeField(db_index=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    sent_at = models.DateTimeField(null=True)
    failed_at = models.DateTimeField(null=True)
    error_message = models.TextField(blank=True)

    # Retry tracking
    attempt_count = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    next_retry = models.DateTimeField(null=True)

    # Content
    subject = models.CharField(max_length=200, blank=True)
    body = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scheduled_for']
        indexes = [
            models.Index(fields=['status', 'scheduled_for']),
        ]


class NotificationLog(models.Model):
    """Log of sent notifications."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    channel = models.CharField(max_length=20)
    notification_type = models.CharField(max_length=50)

    # Content
    subject = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    recipient = models.CharField(max_length=255)  # Email, phone, etc.

    # Status
    status = models.CharField(max_length=20)  # sent, delivered, failed, bounced
    external_id = models.CharField(max_length=255, blank=True)  # Provider message ID

    # Tracking
    sent_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True)
    opened_at = models.DateTimeField(null=True)
    clicked_at = models.DateTimeField(null=True)
    bounced_at = models.DateTimeField(null=True)

    # Cost tracking
    cost = models.DecimalField(max_digits=10, decimal_places=4, null=True)

    class Meta:
        ordering = ['-sent_at']


class ReminderRule(models.Model):
    """Rules for automatic reminder creation."""

    name = models.CharField(max_length=200)
    trigger_type = models.CharField(max_length=50)  # vaccination_due, appointment_upcoming

    # Timing
    days_before = models.IntegerField(default=0)
    hours_before = models.IntegerField(default=0)

    # Escalation
    escalation_days = models.JSONField(default=list)
    # e.g., [7, 3, 1] = remind 7 days, 3 days, 1 day before

    # Template
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE)

    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)

    class Meta:
        ordering = ['priority']
```

### Reminder Engine
```python
class ReminderEngine:
    """Engine for creating and managing reminders."""

    def create_appointment_reminders(self, appointment: Appointment):
        """Create reminders for an appointment."""

        rules = ReminderRule.objects.filter(
            trigger_type='appointment_upcoming',
            is_active=True
        )

        for rule in rules:
            for days in rule.escalation_days:
                remind_at = appointment.datetime - timedelta(days=days)

                if remind_at > timezone.now():
                    ScheduledReminder.objects.create(
                        reminder_type='appointment_reminder',
                        content_object=appointment,
                        user=appointment.pet.owner,
                        channel=rule.template.channel,
                        scheduled_for=remind_at,
                        subject=self.render_subject(rule.template, appointment),
                        body=self.render_body(rule.template, appointment)
                    )

    def create_vaccination_reminders(self, vaccination: Vaccination):
        """Create reminders for upcoming vaccinations."""

        if not vaccination.next_due_date:
            return

        rules = ReminderRule.objects.filter(
            trigger_type='vaccination_due',
            is_active=True
        )

        for rule in rules:
            for days in rule.escalation_days:
                remind_at = datetime.combine(
                    vaccination.next_due_date,
                    time(10, 0)  # 10 AM
                ) - timedelta(days=days)

                if remind_at > timezone.now():
                    ScheduledReminder.objects.create(
                        reminder_type='vaccination_due',
                        content_object=vaccination,
                        user=vaccination.pet.owner,
                        channel=rule.template.channel,
                        scheduled_for=remind_at,
                        subject=self.render_subject(rule.template, vaccination),
                        body=self.render_body(rule.template, vaccination)
                    )
```

### Test Cases
- [ ] Templates render correctly
- [ ] Preferences respected
- [ ] Reminders scheduled
- [ ] Logs created
- [ ] Escalation logic works
- [ ] Quiet hours respected

### Definition of Done
- [ ] All models migrated
- [ ] Engine creates reminders
- [ ] Preferences respected
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-027: Appointment Models
- T-024: Pet Profile Models
