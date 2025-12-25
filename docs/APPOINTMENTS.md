# Appointments Module

The `apps.appointments` module manages appointment booking, service types, staff scheduling, and appointment lifecycle for the veterinary clinic.

## Table of Contents

- [Overview](#overview)
- [Models](#models)
  - [ServiceType](#servicetype)
  - [ScheduleBlock](#scheduleblock)
  - [Appointment](#appointment)
- [Views](#views)
- [URL Patterns](#url-patterns)
- [Workflows](#workflows)
  - [Booking Flow](#booking-flow)
  - [Appointment Lifecycle](#appointment-lifecycle)
  - [Cancellation Flow](#cancellation-flow)
- [Service Categories](#service-categories)
- [Time Slot Management](#time-slot-management)
- [Integration Points](#integration-points)
- [Query Examples](#query-examples)
- [Testing](#testing)

## Overview

The appointments module handles:

- **Service Types** - Clinic services with duration and pricing
- **Schedule Blocks** - Staff availability by day/time
- **Appointment Booking** - Customer self-service booking
- **Appointment Management** - Status tracking and reminders
- **Cancellation Handling** - With reason tracking

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   ServiceType   │────▶│   Appointment   │◀────│     Owner       │
│  (what/price)   │     │   (booking)     │     │    (customer)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│      Pet        │    │  Veterinarian   │    │ ScheduleBlock   │
│   (patient)     │    │   (assigned)    │    │  (availability) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Models

### ServiceType

Location: `apps/appointments/models.py`

Types of services offered by the clinic.

```python
SERVICE_CATEGORIES = [
    ('clinic', 'Clinic'),
    ('grooming', 'Grooming'),
    ('lab', 'Laboratory'),
    ('surgery', 'Surgery'),
    ('dental', 'Dental'),
    ('emergency', 'Emergency'),
    ('other', 'Other'),
]

class ServiceType(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=20, choices=SERVICE_CATEGORIES, default='clinic')
    is_active = models.BooleanField(default=True)
    requires_pet = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']
```

**Example Services:**

| Service | Category | Duration | Price |
|---------|----------|----------|-------|
| Wellness Exam | clinic | 30 min | $50 |
| Vaccination | clinic | 15 min | $35 |
| Full Grooming | grooming | 60 min | $75 |
| Blood Work | lab | 15 min | $85 |
| Dental Cleaning | dental | 45 min | $200 |
| Spay/Neuter | surgery | 90 min | $350 |

### ScheduleBlock

Staff availability blocks for scheduling.

```python
WEEKDAY_CHOICES = [
    (0, 'Monday'),
    (1, 'Tuesday'),
    (2, 'Wednesday'),
    (3, 'Thursday'),
    (4, 'Friday'),
    (5, 'Saturday'),
    (6, 'Sunday'),
]

class ScheduleBlock(models.Model):
    staff = models.ForeignKey(User, on_delete=models.CASCADE,
                              related_name='schedule_blocks')
    day_of_week = models.IntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['day_of_week', 'start_time']
```

### Appointment

Appointment booking records.

```python
APPOINTMENT_STATUS = [
    ('scheduled', 'Scheduled'),
    ('confirmed', 'Confirmed'),
    ('in_progress', 'In Progress'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
    ('no_show', 'No Show'),
]

class Appointment(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE,
                              related_name='appointments')
    pet = models.ForeignKey('pets.Pet', on_delete=models.CASCADE,
                            related_name='appointments', null=True, blank=True)
    service = models.ForeignKey(ServiceType, on_delete=models.PROTECT,
                                related_name='appointments')
    veterinarian = models.ForeignKey(User, on_delete=models.SET_NULL,
                                     null=True, blank=True,
                                     related_name='appointments_as_vet')

    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()

    status = models.CharField(max_length=20, choices=APPOINTMENT_STATUS,
                              default='scheduled')
    notes = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)

    confirmed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    reminder_sent = models.BooleanField(default=False)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_start']
```

## Views

Location: `apps/appointments/views.py`

### ServiceListView

List available services grouped by category.

```python
class ServiceListView(ListView):
    """List available services for booking."""
    model = ServiceType
    template_name = 'appointments/service_list.html'

    def get_queryset(self):
        return ServiceType.objects.filter(is_active=True).order_by('category', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Group by category
        services_by_category = {}
        for service in context['services']:
            cat = service.get_category_display()
            if cat not in services_by_category:
                services_by_category[cat] = []
            services_by_category[cat].append(service)
        context['services_by_category'] = services_by_category
        return context
```

### BookAppointmentView

Book a new appointment with date/time selection.

```python
class BookAppointmentView(LoginRequiredMixin, CreateView):
    """Book a new appointment."""
    model = Appointment
    form_class = AppointmentBookingForm
    template_name = 'appointments/book_appointment.html'
    success_url = reverse_lazy('appointments:my_appointments')

    def form_valid(self, form):
        form.instance.owner = self.request.user

        # Parse date and time
        date = form.cleaned_data['date']
        time_str = form.cleaned_data['time_slot']
        hour, minute = map(int, time_str.split(':'))

        # Create datetime
        scheduled_start = timezone.make_aware(
            datetime.combine(date, datetime.min.time().replace(hour=hour, minute=minute))
        )

        # Calculate end time based on service duration
        service = form.cleaned_data['service']
        scheduled_end = scheduled_start + timedelta(minutes=service.duration_minutes)

        form.instance.scheduled_start = scheduled_start
        form.instance.scheduled_end = scheduled_end

        messages.success(self.request, 'Your appointment has been booked!')
        return super().form_valid(form)
```

### MyAppointmentsView

List user's appointments (upcoming and past).

```python
class MyAppointmentsView(LoginRequiredMixin, ListView):
    """List user's appointments."""
    model = Appointment
    template_name = 'appointments/my_appointments.html'

    def get_queryset(self):
        return Appointment.objects.filter(
            owner=self.request.user
        ).select_related('pet', 'service', 'veterinarian')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        context['upcoming'] = [a for a in context['appointments'] if a.scheduled_start > now]
        context['past'] = [a for a in context['appointments'] if a.scheduled_start <= now]
        return context
```

### CancelAppointmentView

Cancel an appointment with reason tracking.

```python
class CancelAppointmentView(LoginRequiredMixin, TemplateView):
    """Cancel an appointment."""

    def post(self, request, *args, **kwargs):
        appointment = get_object_or_404(Appointment, pk=self.kwargs['pk'], owner=request.user)
        reason = request.POST.get('reason', '')

        appointment.status = 'cancelled'
        appointment.cancelled_at = timezone.now()
        appointment.cancellation_reason = reason
        appointment.save()

        messages.info(request, 'Your appointment has been cancelled.')
        return redirect('appointments:my_appointments')
```

### AvailableSlotsView

AJAX endpoint for fetching available time slots.

```python
class AvailableSlotsView(LoginRequiredMixin, TemplateView):
    """AJAX view to get available time slots for a date."""

    def get_context_data(self, **kwargs):
        date_str = self.request.GET.get('date')
        service_id = self.request.GET.get('service')

        if date_str and service_id:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            service = ServiceType.objects.get(pk=service_id)

            # Generate available slots (check existing bookings in production)
            slots = []
            for hour in range(9, 18):
                for minute in [0, 30]:
                    slots.append({
                        'value': f'{hour:02d}:{minute:02d}',
                        'display': f'{hour:02d}:{minute:02d}',
                        'available': True,
                    })
            context['slots'] = slots

        return context
```

## URL Patterns

Location: `apps/appointments/urls.py`

```python
app_name = 'appointments'

urlpatterns = [
    path('services/', views.ServiceListView.as_view(), name='services'),
    path('book/', views.BookAppointmentView.as_view(), name='book'),
    path('my-appointments/', views.MyAppointmentsView.as_view(), name='my_appointments'),
    path('<int:pk>/', views.AppointmentDetailView.as_view(), name='detail'),
    path('<int:pk>/cancel/', views.CancelAppointmentView.as_view(), name='cancel'),
    path('available-slots/', views.AvailableSlotsView.as_view(), name='available_slots'),
]
```

## Workflows

### Booking Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Select Service  │───▶│  Select Date    │───▶│  Select Time    │
│  /services/     │    │   + Pet         │    │    Slot         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                      │
                                                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Confirmation   │◀───│  Add Notes      │◀───│  Review         │
│     Page        │    │  (optional)     │    │   Details       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**Booking an Appointment:**

```python
from apps.appointments.models import Appointment, ServiceType
from django.utils import timezone
from datetime import datetime, timedelta

# Get service
service = ServiceType.objects.get(name='Wellness Exam')

# Create appointment
appointment = Appointment.objects.create(
    owner=user,
    pet=pet,
    service=service,
    scheduled_start=timezone.make_aware(datetime(2024, 2, 15, 10, 0)),
    scheduled_end=timezone.make_aware(datetime(2024, 2, 15, 10, 30)),
    status='scheduled',
    notes='Annual checkup',
)
```

### Appointment Lifecycle

```
┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐
│ SCHEDULED │───▶│ CONFIRMED │───▶│IN_PROGRESS│───▶│ COMPLETED │
└───────────┘    └───────────┘    └───────────┘    └───────────┘
      │                │                │
      │                │                │
      ▼                ▼                ▼
┌───────────┐    ┌───────────┐    ┌───────────┐
│ CANCELLED │    │  NO_SHOW  │    │           │
└───────────┘    └───────────┘    └───────────┘
```

**Status Transitions:**

| From | To | Trigger |
|------|-----|---------|
| scheduled | confirmed | Customer or staff confirms |
| scheduled | cancelled | Customer cancels |
| confirmed | in_progress | Patient arrives |
| confirmed | no_show | Patient doesn't show |
| confirmed | cancelled | Late cancellation |
| in_progress | completed | Service finished |

**Updating Status:**

```python
from django.utils import timezone

# Confirm appointment
appointment.status = 'confirmed'
appointment.confirmed_at = timezone.now()
appointment.save()

# Start appointment
appointment.status = 'in_progress'
appointment.save()

# Complete appointment
appointment.status = 'completed'
appointment.completed_at = timezone.now()
appointment.save()
```

### Cancellation Flow

```python
from django.utils import timezone

# Cancel with reason
appointment.status = 'cancelled'
appointment.cancelled_at = timezone.now()
appointment.cancellation_reason = 'Pet is feeling better, will reschedule if needed'
appointment.save()
```

## Service Categories

| Category | Description | Typical Duration |
|----------|-------------|------------------|
| `clinic` | General clinic services | 15-45 min |
| `grooming` | Bathing, haircuts, nail trims | 30-90 min |
| `lab` | Blood work, urinalysis, diagnostics | 15-30 min |
| `surgery` | Spay/neuter, mass removal, etc. | 60-180 min |
| `dental` | Cleanings, extractions | 45-90 min |
| `emergency` | Urgent/emergency care | Variable |
| `other` | Other services | Variable |

## Time Slot Management

### Generating Available Slots

```python
from datetime import time, timedelta

def get_available_slots(date, service, staff=None):
    """Get available time slots for a date and service."""
    slots = []
    slot_duration = timedelta(minutes=30)

    # Business hours
    start_time = time(9, 0)
    end_time = time(18, 0)

    # Get existing appointments
    existing = Appointment.objects.filter(
        scheduled_start__date=date,
        status__in=['scheduled', 'confirmed', 'in_progress']
    )

    if staff:
        existing = existing.filter(veterinarian=staff)

    # Generate slots
    current = datetime.combine(date, start_time)
    end = datetime.combine(date, end_time)

    while current < end:
        slot_end = current + timedelta(minutes=service.duration_minutes)

        # Check for conflicts
        conflict = existing.filter(
            scheduled_start__lt=slot_end,
            scheduled_end__gt=current
        ).exists()

        slots.append({
            'start': current.time(),
            'end': slot_end.time(),
            'available': not conflict,
        })

        current += slot_duration

    return slots
```

### Staff Schedule Blocks

```python
from apps.appointments.models import ScheduleBlock

# Create schedule block (vet works Mon-Fri 9am-5pm)
for day in range(0, 5):  # Monday to Friday
    ScheduleBlock.objects.create(
        staff=veterinarian,
        day_of_week=day,
        start_time=time(9, 0),
        end_time=time(17, 0),
        is_active=True,
    )

# Check if staff is available
def is_staff_available(staff, date, start_time, end_time):
    day_of_week = date.weekday()
    return ScheduleBlock.objects.filter(
        staff=staff,
        day_of_week=day_of_week,
        start_time__lte=start_time,
        end_time__gte=end_time,
        is_active=True
    ).exists()
```

## Integration Points

### With Pets Module

```python
from apps.pets.models import Pet
from apps.appointments.models import Appointment

# Get upcoming appointments for a pet
pet = Pet.objects.get(pk=pet_id)
upcoming = pet.appointments.filter(
    scheduled_start__gte=timezone.now(),
    status__in=['scheduled', 'confirmed']
)
```

### With Billing Module

```python
from apps.billing.services import InvoiceService
from apps.appointments.models import Appointment

def complete_appointment(appointment):
    """Complete appointment and create invoice."""
    appointment.status = 'completed'
    appointment.completed_at = timezone.now()
    appointment.save()

    # Create invoice (using billing service)
    invoice = InvoiceService.create_from_appointment(appointment)
    return invoice
```

### With Practice Module

```python
from apps.practice.models import ClinicalNote
from apps.appointments.models import Appointment

def create_clinical_note(appointment, soap_data):
    """Create clinical note from appointment."""
    return ClinicalNote.objects.create(
        pet=appointment.pet,
        appointment=appointment,
        author=appointment.veterinarian,
        note_type='soap',
        subjective=soap_data.get('subjective', ''),
        objective=soap_data.get('objective', ''),
        assessment=soap_data.get('assessment', ''),
        plan=soap_data.get('plan', ''),
    )
```

### With CRM Module

```python
from apps.crm.models import OwnerProfile, Interaction

def on_appointment_completed(appointment):
    """Update CRM after appointment."""
    try:
        profile = appointment.owner.owner_profile
        profile.total_visits += 1
        profile.last_visit_date = timezone.now().date()
        profile.save()

        # Log interaction
        Interaction.objects.create(
            owner_profile=profile,
            interaction_type='visit',
            channel='in_person',
            direction='inbound',
            subject=f'Appointment: {appointment.service.name}',
        )
    except OwnerProfile.DoesNotExist:
        pass
```

## Query Examples

### Appointment Queries

```python
from apps.appointments.models import Appointment
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

# Today's appointments
today = timezone.now().date()
today_appointments = Appointment.objects.filter(
    scheduled_start__date=today
).select_related('pet', 'service', 'owner', 'veterinarian')

# Upcoming appointments this week
week_end = today + timedelta(days=7)
this_week = Appointment.objects.filter(
    scheduled_start__date__gte=today,
    scheduled_start__date__lte=week_end,
    status__in=['scheduled', 'confirmed']
)

# Appointments needing reminders
reminder_cutoff = timezone.now() + timedelta(hours=24)
needs_reminder = Appointment.objects.filter(
    scheduled_start__lte=reminder_cutoff,
    scheduled_start__gte=timezone.now(),
    reminder_sent=False,
    status='scheduled'
)

# No-show rate
total = Appointment.objects.filter(status__in=['completed', 'no_show']).count()
no_shows = Appointment.objects.filter(status='no_show').count()
no_show_rate = (no_shows / total * 100) if total > 0 else 0

# Appointments by status
status_counts = Appointment.objects.values('status').annotate(
    count=Count('id')
).order_by('status')

# Cancellation reasons
cancellations = Appointment.objects.filter(
    status='cancelled'
).values('cancellation_reason').annotate(
    count=Count('id')
).order_by('-count')
```

### Service Queries

```python
from apps.appointments.models import ServiceType, Appointment
from django.db.models import Count, Sum

# Popular services
popular = ServiceType.objects.annotate(
    booking_count=Count('appointments')
).order_by('-booking_count')[:10]

# Revenue by service
from django.db.models import F

service_revenue = Appointment.objects.filter(
    status='completed'
).values('service__name').annotate(
    revenue=Sum('service__price'),
    count=Count('id')
).order_by('-revenue')
```

### Schedule Queries

```python
from apps.appointments.models import ScheduleBlock

# Staff availability for a day
day_of_week = 1  # Tuesday
available_staff = ScheduleBlock.objects.filter(
    day_of_week=day_of_week,
    is_active=True
).select_related('staff')

# Vet schedule for the week
vet_schedule = ScheduleBlock.objects.filter(
    staff=veterinarian,
    is_active=True
).order_by('day_of_week', 'start_time')
```

## Testing

### Unit Tests

Location: `tests/test_appointments.py`

```bash
# Run appointments unit tests
python -m pytest tests/test_appointments.py -v
```

### Browser Tests

Location: `tests/e2e/browser/test_appointments.py`

```bash
# Run appointments browser tests
python -m pytest tests/e2e/browser/test_appointments.py -v

# Run with visible browser
python -m pytest tests/e2e/browser/test_appointments.py -v --headed --slowmo=500
```

### Key Test Scenarios

1. **Service Types**
   - Create service with pricing
   - Category filtering
   - Active/inactive toggle

2. **Booking Flow**
   - Select service and date
   - Time slot availability
   - Pet selection
   - Confirmation

3. **Appointment Lifecycle**
   - Status transitions
   - Cancellation with reason
   - No-show handling
   - Completion flow

4. **Reminders**
   - Send reminders 24h before
   - Track reminder status
   - Multiple reminder prevention

5. **Schedule Blocks**
   - Staff availability
   - Conflict detection
   - Recurring schedules
