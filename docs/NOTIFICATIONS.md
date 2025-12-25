# Notifications Module

The `apps.notifications` module manages in-app notifications, email delivery, user preferences, and automated reminders for appointments and vaccinations.

## Table of Contents

- [Overview](#overview)
- [Models](#models)
  - [Notification](#notification)
  - [NotificationPreference](#notificationpreference)
- [Services](#services)
  - [NotificationService](#notificationservice)
  - [VaccinationReminderService](#vaccinationreminderservice)
- [Views](#views)
- [URL Patterns](#url-patterns)
- [Workflows](#workflows)
  - [Creating Notifications](#creating-notifications)
  - [Email Delivery](#email-delivery)
  - [User Preferences](#user-preferences)
  - [Vaccination Reminders](#vaccination-reminders)
- [Notification Types](#notification-types)
- [Integration Points](#integration-points)
- [Query Examples](#query-examples)
- [Testing](#testing)

## Overview

The notifications module handles all user communication:

- **In-App Notifications** - Real-time notifications in the UI
- **Email Notifications** - Automated email delivery
- **User Preferences** - Granular control over notification settings
- **Reminder System** - Automated vaccination and appointment reminders

```
┌─────────────────────────────────────────────────────────────┐
│                   NOTIFICATION FLOW                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌──────────────┐                                          │
│   │    Event     │  (appointment, vaccination, promotion)   │
│   └──────┬───────┘                                          │
│          │                                                   │
│          ▼                                                   │
│   ┌──────────────────────────────────────────┐              │
│   │        NotificationService               │              │
│   │  ┌────────────────────────────────────┐  │              │
│   │  │ 1. Create Notification record      │  │              │
│   │  │ 2. Check user preferences          │  │              │
│   │  │ 3. Send email if enabled           │  │              │
│   │  └────────────────────────────────────┘  │              │
│   └──────────────┬───────────────────────────┘              │
│                  │                                           │
│        ┌─────────┴─────────┐                                │
│        ▼                   ▼                                │
│   ┌──────────┐      ┌──────────────┐                        │
│   │ In-App   │      │    Email     │                        │
│   │ (always) │      │ (if enabled) │                        │
│   └──────────┘      └──────────────┘                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Models

### Notification

Location: `apps/notifications/models.py`

Individual notification records for users.

```python
NOTIFICATION_TYPES = [
    ('appointment_reminder', 'Appointment Reminder'),
    ('appointment_confirmed', 'Appointment Confirmed'),
    ('appointment_cancelled', 'Appointment Cancelled'),
    ('vaccination_reminder', 'Vaccination Reminder'),
    ('vaccination_overdue', 'Vaccination Overdue'),
    ('general', 'General'),
    ('promotion', 'Promotion'),
    ('system', 'System'),
]

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES, default='general')
    title = models.CharField(max_length=200)
    message = models.TextField()

    # Related objects (optional)
    related_pet_id = models.IntegerField(null=True, blank=True)
    related_appointment_id = models.IntegerField(null=True, blank=True)

    # Read status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    # Email tracking
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `notification_type` | CharField | Type category for filtering/preferences |
| `related_pet_id` | IntegerField | Link to associated pet |
| `related_appointment_id` | IntegerField | Link to associated appointment |
| `is_read` | Boolean | Whether user has seen notification |
| `email_sent` | Boolean | Whether email was delivered |

**Database Indexes:**

```python
indexes = [
    models.Index(fields=['user', 'is_read']),      # Unread count queries
    models.Index(fields=['user', 'created_at']),  # Listing queries
]
```

### NotificationPreference

User preferences for notification delivery.

```python
class NotificationPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')

    # Email preferences by category
    email_appointments = models.BooleanField(default=True)
    email_vaccinations = models.BooleanField(default=True)
    email_promotions = models.BooleanField(default=False)  # Off by default
    email_system = models.BooleanField(default=True)

    # Reminder timing
    appointment_reminder_hours = models.IntegerField(default=24)  # Hours before
    vaccination_reminder_days = models.IntegerField(default=14)   # Days before

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `email_appointments` | Boolean | Receive appointment emails |
| `email_vaccinations` | Boolean | Receive vaccination emails |
| `email_promotions` | Boolean | Receive marketing emails |
| `appointment_reminder_hours` | Integer | Hours before appointment to remind |
| `vaccination_reminder_days` | Integer | Days before vaccination to remind |

## Services

Location: `apps/notifications/services.py`

### NotificationService

Main service for creating and managing notifications.

```python
class NotificationService:
    """Service for managing user notifications."""

    # Mapping of notification types to preference fields
    TYPE_TO_PREFERENCE = {
        'appointment_reminder': 'email_appointments',
        'appointment_confirmed': 'email_appointments',
        'appointment_cancelled': 'email_appointments',
        'vaccination_reminder': 'email_vaccinations',
        'vaccination_overdue': 'email_vaccinations',
        'promotion': 'email_promotions',
        'system': 'email_system',
        'general': 'email_system',
    }

    @classmethod
    def create_notification(
        cls,
        user,
        notification_type: str,
        title: str,
        message: str,
        send_email: bool = False,
        related_pet_id: Optional[int] = None,
        related_appointment_id: Optional[int] = None
    ) -> Notification:
        """Create a notification for a user."""

    @classmethod
    def _should_send_email(cls, user, notification_type: str) -> bool:
        """Check if email should be sent based on user preferences."""

    @classmethod
    def _send_notification_email(cls, notification: Notification) -> bool:
        """Send email for a notification."""

    @classmethod
    def get_user_notifications(cls, user, unread_only: bool = False, limit: int = 50):
        """Get notifications for a user."""

    @classmethod
    def get_unread_count(cls, user) -> int:
        """Get count of unread notifications."""

    @classmethod
    def mark_all_as_read(cls, user) -> int:
        """Mark all user notifications as read."""
```

### VaccinationReminderService

Automated vaccination reminder service.

```python
class VaccinationReminderService:
    """Service for vaccination reminders."""

    @classmethod
    def get_vaccinations_due_soon(cls, days_ahead: int = 30):
        """Get vaccinations due within specified days."""
        from apps.pets.models import Vaccination

        due_date = date.today() + timedelta(days=days_ahead)

        return Vaccination.objects.filter(
            next_due_date__lte=due_date,
            next_due_date__gte=date.today(),
            reminder_sent=False
        ).select_related('pet', 'pet__owner')

    @classmethod
    def get_overdue_vaccinations(cls):
        """Get overdue vaccinations."""

    @classmethod
    def send_reminder_email(cls, vaccination) -> bool:
        """Send reminder email for a vaccination."""
```

## Views

Location: `apps/notifications/views.py`

### NotificationListView

List user's notifications with pagination.

```python
class NotificationListView(LoginRequiredMixin, ListView):
    """List user's notifications."""
    model = Notification
    template_name = 'notifications/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
```

### MarkNotificationReadView

Mark a single notification as read.

```python
class MarkNotificationReadView(LoginRequiredMixin, View):
    """Mark a single notification as read."""

    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.mark_as_read()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('notifications:list')
```

### MarkAllReadView

Mark all notifications as read.

```python
class MarkAllReadView(LoginRequiredMixin, View):
    """Mark all notifications as read."""

    def post(self, request):
        count = NotificationService.mark_all_as_read(request.user)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'count': count})
        return redirect('notifications:list')
```

### UnreadCountView

JSON API for unread notification count.

```python
class UnreadCountView(LoginRequiredMixin, View):
    """Get unread notification count (JSON API)."""

    def get(self, request):
        count = NotificationService.get_unread_count(request.user)
        return JsonResponse({'count': count})
```

## URL Patterns

Location: `apps/notifications/urls.py`

```python
app_name = 'notifications'

urlpatterns = [
    # List all notifications
    path('', views.NotificationListView.as_view(), name='list'),

    # Mark single notification as read
    path('<int:pk>/read/', views.MarkNotificationReadView.as_view(), name='mark_read'),

    # Mark all as read
    path('mark-all-read/', views.MarkAllReadView.as_view(), name='mark_all_read'),

    # JSON API for unread count
    path('unread-count/', views.UnreadCountView.as_view(), name='unread_count'),
]
```

## Workflows

### Creating Notifications

```python
from apps.notifications.services import NotificationService

# Basic notification (in-app only)
notification = NotificationService.create_notification(
    user=user,
    notification_type='general',
    title='Welcome to Pet Friendly Vet!',
    message='Thank you for registering. Start by adding your pets.',
)

# Notification with email
notification = NotificationService.create_notification(
    user=user,
    notification_type='appointment_confirmed',
    title='Appointment Confirmed',
    message=f'Your appointment for {pet.name} on {date} has been confirmed.',
    send_email=True,
    related_pet_id=pet.pk,
    related_appointment_id=appointment.pk,
)

# Promotion notification (respects email_promotions preference)
notification = NotificationService.create_notification(
    user=user,
    notification_type='promotion',
    title='20% Off Dental Cleaning!',
    message='Book a dental cleaning this month and save 20%.',
    send_email=True,
)
```

### Email Delivery

```python
from apps.notifications.services import NotificationService

# Email is sent only if:
# 1. send_email=True is passed
# 2. User has email address
# 3. User preference for that notification type is enabled

notification = NotificationService.create_notification(
    user=user,
    notification_type='appointment_reminder',
    title='Appointment Tomorrow',
    message='...',
    send_email=True,  # Will check email_appointments preference
)

# After sending:
# notification.email_sent = True
# notification.email_sent_at = timezone.now()
```

### User Preferences

```python
from apps.notifications.models import NotificationPreference

# Get or create preferences
prefs, created = NotificationPreference.objects.get_or_create(
    user=user,
    defaults={
        'email_appointments': True,
        'email_vaccinations': True,
        'email_promotions': False,
        'appointment_reminder_hours': 24,
        'vaccination_reminder_days': 14,
    }
)

# Update preferences
prefs.email_promotions = True
prefs.appointment_reminder_hours = 48  # 2 days before
prefs.save()

# Check preference for a notification type
should_email = NotificationService._should_send_email(
    user=user,
    notification_type='vaccination_reminder'
)
```

### Vaccination Reminders

```python
from apps.notifications.services import VaccinationReminderService

# Get vaccinations due in next 30 days
due_soon = VaccinationReminderService.get_vaccinations_due_soon(days_ahead=30)

# Send reminders for each
for vaccination in due_soon:
    success = VaccinationReminderService.send_reminder_email(vaccination)
    if success:
        # Vaccination marked as reminded
        # In-app notification created
        # Email sent to owner
        print(f"Reminder sent for {vaccination.pet.name}")

# Get overdue vaccinations
overdue = VaccinationReminderService.get_overdue_vaccinations()
```

## Notification Types

| Type | Description | Email Preference |
|------|-------------|------------------|
| `appointment_reminder` | Upcoming appointment reminder | `email_appointments` |
| `appointment_confirmed` | Appointment booking confirmed | `email_appointments` |
| `appointment_cancelled` | Appointment was cancelled | `email_appointments` |
| `vaccination_reminder` | Vaccination coming due | `email_vaccinations` |
| `vaccination_overdue` | Vaccination is overdue | `email_vaccinations` |
| `general` | General notifications | `email_system` |
| `promotion` | Marketing/promotions | `email_promotions` |
| `system` | System announcements | `email_system` |

## Integration Points

### With Appointments Module

```python
from apps.notifications.services import NotificationService
from apps.appointments.models import Appointment

# On appointment creation
def on_appointment_created(appointment):
    NotificationService.create_notification(
        user=appointment.owner,
        notification_type='appointment_confirmed',
        title=f'Appointment Confirmed: {appointment.date}',
        message=f'Your appointment for {appointment.pet.name} is confirmed.',
        send_email=True,
        related_pet_id=appointment.pet.pk,
        related_appointment_id=appointment.pk,
    )

# On appointment cancellation
def on_appointment_cancelled(appointment):
    NotificationService.create_notification(
        user=appointment.owner,
        notification_type='appointment_cancelled',
        title='Appointment Cancelled',
        message=f'Your appointment on {appointment.date} has been cancelled.',
        send_email=True,
        related_appointment_id=appointment.pk,
    )
```

### With Pets Module

```python
from apps.notifications.services import NotificationService, VaccinationReminderService
from apps.pets.models import Vaccination

# Automated vaccination reminders (run daily via cron/celery)
def send_vaccination_reminders():
    due_soon = VaccinationReminderService.get_vaccinations_due_soon(days_ahead=14)

    for vaccination in due_soon:
        VaccinationReminderService.send_reminder_email(vaccination)

# On new pet added
def on_pet_created(pet):
    NotificationService.create_notification(
        user=pet.owner,
        notification_type='general',
        title=f'{pet.name} Added to Your Profile',
        message='You can now book appointments and track health records.',
        related_pet_id=pet.pk,
    )
```

### With Store Module

```python
from apps.notifications.services import NotificationService

# On order shipped
def on_order_shipped(order):
    NotificationService.create_notification(
        user=order.user,
        notification_type='system',
        title='Your Order Has Shipped!',
        message=f'Order {order.order_number} is on its way.',
        send_email=True,
    )
```

### With Emergency Module

```python
from apps.notifications.services import NotificationService

# Alert staff of new emergency
def alert_staff_emergency(contact, staff):
    NotificationService.create_notification(
        user=staff.user,
        notification_type='system',
        title='New Emergency Contact',
        message=f'Urgent: {contact.pet_species} - {contact.reported_symptoms[:100]}',
        send_email=True,
    )
```

## Query Examples

### Notification Queries

```python
from apps.notifications.models import Notification
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

# Unread notifications for user
unread = Notification.objects.filter(
    user=user,
    is_read=False
).order_by('-created_at')

# Notifications by type
by_type = Notification.objects.filter(user=user).values(
    'notification_type'
).annotate(count=Count('id')).order_by('-count')

# Recent notifications (last 7 days)
recent = Notification.objects.filter(
    user=user,
    created_at__gte=timezone.now() - timedelta(days=7)
)

# Notifications with related pet
pet_notifications = Notification.objects.filter(
    user=user,
    related_pet_id=pet.pk
)

# Emails that failed to send (null email_sent_at but should have sent)
failed_emails = Notification.objects.filter(
    email_sent=False,
    notification_type__in=['appointment_reminder', 'vaccination_reminder'],
    created_at__lt=timezone.now() - timedelta(hours=1)
)
```

### Preference Queries

```python
from apps.notifications.models import NotificationPreference

# Users who want promotions
promo_recipients = NotificationPreference.objects.filter(
    email_promotions=True
).select_related('user')

# Users with custom reminder timing
custom_timing = NotificationPreference.objects.exclude(
    appointment_reminder_hours=24
)

# Get user's preferences (with defaults)
def get_user_prefs(user):
    try:
        return user.notification_preferences
    except NotificationPreference.DoesNotExist:
        return NotificationPreference.objects.create(user=user)
```

### Analytics Queries

```python
from apps.notifications.models import Notification
from django.db.models import Count, Avg, F
from django.db.models.functions import TruncDate

# Notifications per day
daily_stats = Notification.objects.annotate(
    date=TruncDate('created_at')
).values('date').annotate(
    count=Count('id')
).order_by('-date')[:30]

# Read rate by notification type
read_rates = Notification.objects.values('notification_type').annotate(
    total=Count('id'),
    read=Count('id', filter=models.Q(is_read=True))
).annotate(
    read_rate=F('read') * 100.0 / F('total')
)

# Email delivery rate
email_stats = Notification.objects.filter(
    notification_type__in=['appointment_reminder', 'vaccination_reminder']
).aggregate(
    total=Count('id'),
    sent=Count('id', filter=models.Q(email_sent=True))
)

# Average time to read
from django.db.models import ExpressionWrapper, DurationField

read_time = Notification.objects.filter(
    is_read=True,
    read_at__isnull=False
).annotate(
    time_to_read=ExpressionWrapper(
        F('read_at') - F('created_at'),
        output_field=DurationField()
    )
).aggregate(avg_time=Avg('time_to_read'))
```

## Testing

### Unit Tests

Location: `tests/test_notifications.py`

```bash
# Run notification unit tests
python -m pytest tests/test_notifications.py -v
```

### Browser Tests

Location: `tests/e2e/browser/test_notifications.py`

```bash
# Run notification browser tests
python -m pytest tests/e2e/browser/test_notifications.py -v

# Run with visible browser
python -m pytest tests/e2e/browser/test_notifications.py -v --headed --slowmo=500
```

### Key Test Scenarios

1. **Notification Creation**
   - Create in-app notification
   - Create with email delivery
   - Respect user preferences
   - Handle missing email address

2. **Notification Listing**
   - View all notifications
   - Pagination works correctly
   - User isolation (can't see others')

3. **Read/Unread Handling**
   - Mark single as read
   - Mark all as read
   - Unread count API
   - AJAX endpoints work

4. **Email Delivery**
   - Email sent when enabled
   - Email skipped when disabled
   - Email tracking (sent_at)
   - Failure handling

5. **Vaccination Reminders**
   - Find due vaccinations
   - Find overdue vaccinations
   - Send reminder emails
   - Mark as reminded

6. **Preferences**
   - Create default preferences
   - Update preferences
   - Preference respected in delivery
