# T-031: Reminder Processing Tasks

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement Celery tasks for processing and sending reminders
**Related Story**: S-012
**Epoch**: 2
**Estimate**: 4 hours

### Constraints
**Allowed File Paths**: apps/notifications/tasks/
**Forbidden Paths**: None

### Deliverables
- [ ] send_pending_reminders task
- [ ] process_reminder task
- [ ] retry_failed_reminders task
- [ ] create_vaccination_reminders task
- [ ] cleanup_old_notifications task

### Implementation Details

#### Celery Tasks
```python
# apps/notifications/tasks.py

@shared_task
def send_pending_reminders():
    """Process all pending reminders due now."""

    reminders = ScheduledReminder.objects.filter(
        status='pending',
        scheduled_for__lte=timezone.now()
    ).select_related('user')[:100]  # Process 100 at a time

    for reminder in reminders:
        process_reminder.delay(reminder.id)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=300  # 5 minutes
)
def process_reminder(self, reminder_id: int):
    """Process a single reminder."""

    try:
        reminder = ScheduledReminder.objects.get(id=reminder_id)

        # Check if still valid
        if reminder.status != 'pending':
            return

        # Check user preferences
        prefs = reminder.user.notification_prefs
        if not should_send(reminder, prefs):
            reminder.status = 'skipped'
            reminder.save()
            return

        # Send via appropriate channel
        if reminder.channel == 'email':
            result = send_email(reminder)
        elif reminder.channel == 'sms':
            result = send_sms(reminder)
        elif reminder.channel == 'whatsapp':
            result = send_whatsapp(reminder)
        else:
            raise ValueError(f"Unknown channel: {reminder.channel}")

        # Update status
        if result.success:
            reminder.status = 'sent'
            reminder.sent_at = timezone.now()

            # Log it
            NotificationLog.objects.create(
                user=reminder.user,
                channel=reminder.channel,
                notification_type=reminder.reminder_type,
                subject=reminder.subject,
                body=reminder.body,
                recipient=result.recipient,
                status='sent',
                external_id=result.message_id
            )
        else:
            reminder.attempt_count += 1
            if reminder.attempt_count >= reminder.max_attempts:
                reminder.status = 'failed'
                reminder.failed_at = timezone.now()
            else:
                reminder.next_retry = timezone.now() + timedelta(minutes=30)
            reminder.error_message = result.error

        reminder.save()

    except ScheduledReminder.DoesNotExist:
        pass
    except Exception as e:
        self.retry(exc=e)


@shared_task
def retry_failed_reminders():
    """Retry reminders that failed but have retries left."""

    reminders = ScheduledReminder.objects.filter(
        status='pending',
        next_retry__lte=timezone.now(),
        attempt_count__lt=F('max_attempts')
    )

    for reminder in reminders:
        process_reminder.delay(reminder.id)


@shared_task
def create_vaccination_reminders():
    """Daily task to create reminders for upcoming vaccinations."""

    # Find vaccinations due in the next 30 days
    upcoming = Vaccination.objects.filter(
        next_due_date__range=(
            timezone.now().date(),
            timezone.now().date() + timedelta(days=30)
        ),
        pet__is_active=True,
        pet__is_deceased=False
    ).select_related('pet', 'pet__owner')

    engine = ReminderEngine()
    for vaccination in upcoming:
        # Check if reminders already exist
        existing = ScheduledReminder.objects.filter(
            content_type=ContentType.objects.get_for_model(Vaccination),
            object_id=vaccination.id,
            status='pending'
        ).exists()

        if not existing:
            engine.create_vaccination_reminders(vaccination)


@shared_task
def cleanup_old_notifications():
    """Clean up old notification logs (keep 90 days)."""

    threshold = timezone.now() - timedelta(days=90)

    # Delete old logs
    deleted = NotificationLog.objects.filter(
        sent_at__lt=threshold
    ).delete()

    # Delete old completed reminders
    ScheduledReminder.objects.filter(
        status__in=['sent', 'cancelled', 'skipped'],
        scheduled_for__lt=threshold
    ).delete()

    return deleted
```

#### Helper Functions
```python
def should_send(reminder: ScheduledReminder, prefs: NotificationPreference) -> bool:
    """Check if reminder should be sent based on preferences."""

    # Channel enabled?
    channel_map = {
        'email': prefs.email_enabled,
        'sms': prefs.sms_enabled,
        'whatsapp': prefs.whatsapp_enabled,
    }
    if not channel_map.get(reminder.channel, False):
        return False

    # Category enabled?
    if 'appointment' in reminder.reminder_type and not prefs.appointment_reminders:
        return False
    if 'vaccination' in reminder.reminder_type and not prefs.vaccination_reminders:
        return False

    # Quiet hours?
    if prefs.quiet_hours_enabled:
        now = timezone.now().time()
        if prefs.quiet_hours_start <= now or now <= prefs.quiet_hours_end:
            return False

    # Rate limit?
    today_count = NotificationLog.objects.filter(
        user=reminder.user,
        sent_at__date=timezone.now().date()
    ).count()
    if today_count >= prefs.max_per_day:
        return False

    return True


def send_email(reminder: ScheduledReminder) -> SendResult:
    """Send reminder via email."""
    from django.core.mail import send_mail

    try:
        send_mail(
            subject=reminder.subject,
            message=reminder.body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[reminder.user.email],
            html_message=render_html_email(reminder)
        )
        return SendResult(success=True, recipient=reminder.user.email)
    except Exception as e:
        return SendResult(success=False, error=str(e))


def send_sms(reminder: ScheduledReminder) -> SendResult:
    """Send reminder via SMS using Twilio."""
    from twilio.rest import Client

    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    try:
        message = client.messages.create(
            body=reminder.body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=reminder.user.phone_number
        )
        return SendResult(
            success=True,
            recipient=reminder.user.phone_number,
            message_id=message.sid
        )
    except Exception as e:
        return SendResult(success=False, error=str(e))


def send_whatsapp(reminder: ScheduledReminder) -> SendResult:
    """Send reminder via WhatsApp using Twilio."""
    from twilio.rest import Client

    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    try:
        message = client.messages.create(
            body=reminder.body,
            from_=f"whatsapp:{settings.WHATSAPP_NUMBER}",
            to=f"whatsapp:{reminder.user.phone_number}"
        )
        return SendResult(
            success=True,
            recipient=reminder.user.phone_number,
            message_id=message.sid
        )
    except Exception as e:
        return SendResult(success=False, error=str(e))
```

#### Celery Beat Schedule
```python
# settings.py
CELERY_BEAT_SCHEDULE = {
    'send-pending-reminders': {
        'task': 'notifications.tasks.send_pending_reminders',
        'schedule': 60.0,  # Every minute
    },
    'retry-failed-reminders': {
        'task': 'notifications.tasks.retry_failed_reminders',
        'schedule': 300.0,  # Every 5 minutes
    },
    'create-vaccination-reminders': {
        'task': 'notifications.tasks.create_vaccination_reminders',
        'schedule': crontab(hour=6, minute=0),  # Daily at 6 AM
    },
    'cleanup-old-notifications': {
        'task': 'notifications.tasks.cleanup_old_notifications',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}
```

### Test Cases
- [ ] Pending reminders processed
- [ ] Preferences respected
- [ ] Email sending works
- [ ] SMS sending works
- [ ] WhatsApp sending works
- [ ] Retries scheduled
- [ ] Cleanup runs correctly
- [ ] Rate limiting works

### Definition of Done
- [ ] All tasks implemented
- [ ] Celery beat configured
- [ ] Channel integrations tested
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-030: Reminder & Notification Models
