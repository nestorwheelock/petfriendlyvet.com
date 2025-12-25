# Practice Module

The `apps.practice` module manages clinic operations including staff profiles, scheduling, time tracking, tasks, clinical notes, and clinic settings.

## Table of Contents

- [Overview](#overview)
- [Models](#models)
  - [StaffProfile](#staffprofile)
  - [Shift](#shift)
  - [TimeEntry](#timeentry)
  - [ClinicSettings](#clinicsettings)
  - [ClinicalNote](#clinicalnote)
  - [Task](#task)
- [Views](#views)
- [URL Patterns](#url-patterns)
- [Workflows](#workflows)
  - [Staff Management](#staff-management)
  - [Scheduling](#scheduling)
  - [Time Tracking](#time-tracking)
  - [Task Management](#task-management)
  - [Clinical Notes](#clinical-notes)
- [Role-Based Permissions](#role-based-permissions)
- [Integration Points](#integration-points)
- [Query Examples](#query-examples)
- [Testing](#testing)

## Overview

The practice module handles:

- **Staff Profiles** - Employee information and credentials
- **Scheduling** - Shift management and weekly schedules
- **Time Tracking** - Clock in/out and hours calculation
- **Task Management** - Staff task assignment and tracking
- **Clinical Notes** - SOAP notes and patient documentation
- **Clinic Settings** - Practice configuration and branding

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  StaffProfile   │────▶│     Shifts      │────▶│   TimeEntry     │
│   (employee)    │     │   (schedule)    │     │  (clock in/out) │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │
        │              ┌─────────────────┐
        └─────────────▶│     Tasks       │
                       │  (assignments)  │
                       └─────────────────┘
```

## Models

### StaffProfile

Location: `apps/practice/models.py`

Employee profile linked to user account.

```python
class StaffProfile(models.Model):
    ROLE_CHOICES = [
        ('veterinarian', 'Veterinarian'),
        ('vet_tech', 'Veterinary Technician'),
        ('pharmacy_tech', 'Pharmacy Technician'),
        ('receptionist', 'Receptionist'),
        ('manager', 'Manager'),
        ('admin', 'Administrator'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='staff_profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    title = models.CharField(max_length=100, blank=True)

    # Permissions (auto-set based on role)
    can_prescribe = models.BooleanField(default=False)
    can_dispense = models.BooleanField(default=False)
    can_handle_controlled = models.BooleanField(default=False)

    # DEA credentials (for controlled substances)
    dea_number = models.CharField(max_length=20, blank=True)
    dea_expiration = models.DateField(null=True, blank=True)

    # Contact
    phone = models.CharField(max_length=20, blank=True)
    emergency_phone = models.CharField(max_length=20, blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    hire_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Auto-Permission Logic:**

```python
def save(self, *args, **kwargs):
    # Auto-set permissions based on role
    if self.role == 'veterinarian':
        self.can_prescribe = True
        self.can_dispense = True
        self.can_handle_controlled = True
    elif self.role == 'pharmacy_tech':
        self.can_dispense = True
    super().save(*args, **kwargs)
```

### Shift

Staff work shift scheduling.

```python
class Shift(models.Model):
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE,
                              related_name='shifts')

    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    is_confirmed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'start_time']
        unique_together = ['staff', 'date', 'start_time']
```

### TimeEntry

Clock in/out time tracking.

```python
class TimeEntry(models.Model):
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE,
                              related_name='time_entries')
    shift = models.ForeignKey(Shift, on_delete=models.SET_NULL,
                              null=True, blank=True)

    clock_in = models.DateTimeField()
    clock_out = models.DateTimeField(null=True, blank=True)

    break_minutes = models.IntegerField(default=0)
    notes = models.TextField(blank=True)

    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                    null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def hours_worked(self):
        """Calculate hours worked minus breaks."""
        if self.clock_out:
            delta = self.clock_out - self.clock_in
            hours = (delta.total_seconds() / 3600) - (self.break_minutes / 60)
            return round(hours, 2)
        return 0
```

### ClinicSettings

Practice configuration and branding.

```python
class ClinicSettings(models.Model):
    name = models.CharField(max_length=200)
    legal_name = models.CharField(max_length=200, blank=True)
    tax_id = models.CharField(max_length=50, blank=True)

    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    website = models.URLField(blank=True)

    # Hours
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    days_open = models.JSONField(default=list)  # ['mon', 'tue', 'wed', ...]

    # Emergency
    emergency_phone = models.CharField(max_length=20, blank=True)
    emergency_available = models.BooleanField(default=False)

    # Social
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    google_maps_url = models.URLField(blank=True)

    # Branding
    logo = models.ImageField(upload_to='clinic/', blank=True, null=True)
    primary_color = models.CharField(max_length=7, default='#2563eb')

    updated_at = models.DateTimeField(auto_now=True)
```

### ClinicalNote

Patient clinical documentation with SOAP structure.

```python
class ClinicalNote(models.Model):
    NOTE_TYPES = [
        ('soap', 'SOAP Note'),
        ('progress', 'Progress Note'),
        ('procedure', 'Procedure Note'),
        ('lab', 'Lab Results'),
        ('phone', 'Phone Consultation'),
        ('internal', 'Internal Note'),
    ]

    pet = models.ForeignKey('pets.Pet', on_delete=models.CASCADE,
                            related_name='practice_notes')
    appointment = models.ForeignKey('appointments.Appointment',
                                    on_delete=models.SET_NULL, null=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    note_type = models.CharField(max_length=20, choices=NOTE_TYPES)

    # SOAP structure
    subjective = models.TextField(blank=True)   # S - Owner's concerns
    objective = models.TextField(blank=True)    # O - Exam findings
    assessment = models.TextField(blank=True)   # A - Diagnosis/differential
    plan = models.TextField(blank=True)         # P - Treatment plan

    # General content (for non-SOAP notes)
    content = models.TextField(blank=True)

    # Metadata
    is_confidential = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    locked_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Task

Staff task assignment and tracking.

```python
class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    assigned_to = models.ForeignKey(StaffProfile, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='assigned_tasks')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    priority = models.CharField(max_length=10, default='medium')
    status = models.CharField(max_length=20, default='pending')

    due_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Related entities
    pet = models.ForeignKey('pets.Pet', on_delete=models.SET_NULL,
                            null=True, blank=True)
    appointment = models.ForeignKey('appointments.Appointment',
                                    on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority', 'due_date', '-created_at']
```

## Views

Location: `apps/practice/views.py`

All views require staff member access (`@staff_member_required`).

### Dashboard

Practice management overview.

```python
@staff_member_required
def dashboard(request):
    """Practice management dashboard."""
    today = date.today()
    context = {
        'staff_count': StaffProfile.objects.filter(is_active=True).count(),
        'today_shifts': Shift.objects.filter(date=today).count(),
        'pending_tasks': Task.objects.filter(status='pending').count(),
        'urgent_tasks': Task.objects.filter(
            status__in=['pending', 'in_progress'],
            priority='urgent'
        ).count(),
        'today_schedule': Shift.objects.filter(date=today).select_related(
            'staff', 'staff__user'
        ).order_by('start_time'),
        'recent_tasks': Task.objects.filter(
            status__in=['pending', 'in_progress']
        ).select_related('assigned_to', 'assigned_to__user').order_by(
            '-priority', 'due_date'
        )[:5],
    }
    return render(request, 'practice/dashboard.html', context)
```

### Staff Views

```python
@staff_member_required
def staff_list(request):
    """List all staff members with role filtering."""

@staff_member_required
def staff_detail(request, pk):
    """View staff details, shifts, time entries, tasks."""
```

### Schedule Views

```python
@staff_member_required
def schedule(request):
    """Weekly schedule view with week navigation."""

@staff_member_required
def shift_list(request):
    """List shifts (today/upcoming/past)."""
```

### Time Tracking

```python
@staff_member_required
def time_tracking(request):
    """View time entries (today/week/month)."""
```

### Task Views

```python
@staff_member_required
def task_list(request):
    """List tasks with status/priority filters."""

@staff_member_required
def task_detail(request, pk):
    """View task details."""
```

### Settings

```python
@staff_member_required
def clinic_settings(request):
    """View clinic settings."""
```

## URL Patterns

Location: `apps/practice/urls.py`

```python
app_name = 'practice'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Staff
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/<int:pk>/', views.staff_detail, name='staff_detail'),

    # Schedule
    path('schedule/', views.schedule, name='schedule'),
    path('shifts/', views.shift_list, name='shift_list'),

    # Time Tracking
    path('time/', views.time_tracking, name='time_tracking'),

    # Tasks
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/<int:pk>/', views.task_detail, name='task_detail'),

    # Settings
    path('settings/', views.clinic_settings, name='clinic_settings'),
]
```

## Workflows

### Staff Management

```python
from apps.practice.models import StaffProfile

# Create staff profile for new employee
staff = StaffProfile.objects.create(
    user=user,
    role='veterinarian',
    title='Associate Veterinarian',
    dea_number='AB1234567',
    dea_expiration=date(2025, 12, 31),
    phone='555-1234',
    hire_date=date.today(),
)

# Permissions are auto-set:
# staff.can_prescribe = True
# staff.can_dispense = True
# staff.can_handle_controlled = True

# Deactivate staff member
staff.is_active = False
staff.save()
```

### Scheduling

```python
from apps.practice.models import Shift
from datetime import date, time

# Create shift
shift = Shift.objects.create(
    staff=staff_profile,
    date=date(2024, 2, 15),
    start_time=time(9, 0),
    end_time=time(17, 0),
    is_confirmed=False,
    notes='Covering for Dr. Martinez',
)

# Confirm shift
shift.is_confirmed = True
shift.save()

# Get weekly schedule
week_start = date.today() - timedelta(days=date.today().weekday())
week_end = week_start + timedelta(days=6)

week_schedule = Shift.objects.filter(
    date__gte=week_start,
    date__lte=week_end
).select_related('staff', 'staff__user').order_by('date', 'start_time')
```

### Time Tracking

```python
from apps.practice.models import TimeEntry
from django.utils import timezone

# Clock in
entry = TimeEntry.objects.create(
    staff=staff_profile,
    shift=shift,  # Optional link to scheduled shift
    clock_in=timezone.now(),
)

# Clock out
entry.clock_out = timezone.now()
entry.break_minutes = 30
entry.save()

# Calculate hours
print(f"Hours worked: {entry.hours_worked}")  # e.g., 7.5

# Approve time entry
entry.is_approved = True
entry.approved_by = manager_user
entry.save()
```

### Task Management

```python
from apps.practice.models import Task
from django.utils import timezone

# Create task
task = Task.objects.create(
    title='Follow up on Lab Results',
    description='Call owner about bloodwork results for Max',
    assigned_to=staff_profile,
    created_by=request.user,
    priority='high',
    status='pending',
    due_date=timezone.now() + timedelta(hours=4),
    pet=pet,
)

# Start working
task.status = 'in_progress'
task.save()

# Complete task
task.status = 'completed'
task.completed_at = timezone.now()
task.save()
```

### Clinical Notes

```python
from apps.practice.models import ClinicalNote

# Create SOAP note
note = ClinicalNote.objects.create(
    pet=pet,
    appointment=appointment,
    author=request.user,
    note_type='soap',
    subjective="Owner reports decreased appetite for 3 days. Lethargy noted.",
    objective="T: 102.5F, HR: 120, RR: 24. Mild dehydration. Abdomen soft, non-painful.",
    assessment="Suspected viral gastroenteritis. R/O pancreatitis.",
    plan="1. SC fluids 100ml. 2. Cerenia 1mg/kg SQ. 3. Bland diet. 4. Recheck if not eating in 48h.",
)

# Lock note (prevent further edits)
note.is_locked = True
note.locked_at = timezone.now()
note.save()
```

## Role-Based Permissions

| Role | Can Prescribe | Can Dispense | Handle Controlled |
|------|---------------|--------------|-------------------|
| Veterinarian | Yes | Yes | Yes |
| Vet Tech | No | No | No |
| Pharmacy Tech | No | Yes | No |
| Receptionist | No | No | No |
| Manager | No | No | No |
| Admin | No | No | No |

**Note:** Individual permissions can be overridden after profile creation:

```python
# Grant pharmacy tech controlled substance handling
pharmacy_tech.can_handle_controlled = True
pharmacy_tech.save()
```

## Integration Points

### With Pharmacy Module

```python
from apps.pharmacy.models import Prescription
from apps.practice.models import StaffProfile

# Check if staff can prescribe
staff = request.user.staff_profile
if staff.can_prescribe:
    prescription = Prescription.objects.create(
        pet=pet,
        medication=medication,
        prescribed_by=staff.user,
        ...
    )

# Check DEA credentials for controlled substances
if medication.is_controlled:
    if not staff.dea_number or staff.dea_expiration < date.today():
        raise PermissionError("Valid DEA number required")
```

### With Appointments Module

```python
from apps.appointments.models import Appointment
from apps.practice.models import ClinicalNote

# Create clinical note from appointment
def complete_appointment(appointment):
    appointment.status = 'completed'
    appointment.save()

    # Create SOAP note
    note = ClinicalNote.objects.create(
        pet=appointment.pet,
        appointment=appointment,
        author=appointment.veterinarian,
        note_type='soap',
    )
    return note
```

### With Audit Module

Practice pages are logged by AuditMiddleware:

| Path | Resource Type | Sensitivity |
|------|---------------|-------------|
| `/practice/` | `practice.dashboard` | normal |
| `/practice/staff/` | `practice.staff` | normal |
| `/practice/schedule/` | `practice.schedule` | normal |
| `/practice/settings/` | `practice.settings` | **high** |

## Query Examples

### Staff Queries

```python
from apps.practice.models import StaffProfile

# Active veterinarians
vets = StaffProfile.objects.filter(
    role='veterinarian',
    is_active=True
).select_related('user')

# Staff with prescribing privileges
prescribers = StaffProfile.objects.filter(
    can_prescribe=True,
    is_active=True
)

# Staff with expiring DEA credentials
from datetime import timedelta

expiring_dea = StaffProfile.objects.filter(
    dea_number__isnull=False,
    dea_expiration__lte=date.today() + timedelta(days=90)
)
```

### Shift Queries

```python
from apps.practice.models import Shift
from django.db.models import Count

# Today's coverage
today_coverage = Shift.objects.filter(
    date=date.today()
).select_related('staff', 'staff__user')

# Staff shift counts this month
shift_counts = Shift.objects.filter(
    date__month=date.today().month,
    date__year=date.today().year
).values('staff__user__first_name', 'staff__user__last_name').annotate(
    total_shifts=Count('id')
).order_by('-total_shifts')

# Unconfirmed upcoming shifts
unconfirmed = Shift.objects.filter(
    date__gte=date.today(),
    is_confirmed=False
)
```

### Time Entry Queries

```python
from apps.practice.models import TimeEntry
from django.db.models import Sum
from django.db.models.functions import TruncDate

# Hours worked this week by staff
week_start = date.today() - timedelta(days=date.today().weekday())

# Get approved entries and calculate in Python
entries = TimeEntry.objects.filter(
    clock_in__date__gte=week_start,
    clock_out__isnull=False,
    is_approved=True
).select_related('staff')

staff_hours = {}
for entry in entries:
    staff_name = entry.staff.user.get_full_name()
    staff_hours[staff_name] = staff_hours.get(staff_name, 0) + entry.hours_worked

# Unapproved time entries
pending_approval = TimeEntry.objects.filter(
    is_approved=False,
    clock_out__isnull=False
).select_related('staff', 'staff__user')
```

### Task Queries

```python
from apps.practice.models import Task
from django.db.models import Count

# Overdue tasks
overdue = Task.objects.filter(
    status__in=['pending', 'in_progress'],
    due_date__lt=timezone.now()
)

# Urgent pending tasks
urgent = Task.objects.filter(
    priority='urgent',
    status__in=['pending', 'in_progress']
).order_by('due_date')

# Task load by staff
task_load = Task.objects.filter(
    status__in=['pending', 'in_progress']
).values('assigned_to__user__first_name').annotate(
    task_count=Count('id')
).order_by('-task_count')

# Completed tasks today
completed_today = Task.objects.filter(
    status='completed',
    completed_at__date=date.today()
)
```

### Clinical Note Queries

```python
from apps.practice.models import ClinicalNote

# Patient history
patient_notes = ClinicalNote.objects.filter(
    pet=pet
).select_related('author', 'appointment').order_by('-created_at')

# SOAP notes by veterinarian
vet_notes = ClinicalNote.objects.filter(
    author=vet_user,
    note_type='soap'
).order_by('-created_at')[:20]

# Unlocked notes (editable)
editable_notes = ClinicalNote.objects.filter(
    is_locked=False
)
```

## Testing

### Unit Tests

Location: `tests/test_practice.py`

```bash
# Run practice unit tests
python -m pytest tests/test_practice.py -v
```

### Browser Tests

Location: `tests/e2e/browser/test_practice.py`

```bash
# Run practice browser tests
python -m pytest tests/e2e/browser/test_practice.py -v

# Run with visible browser
python -m pytest tests/e2e/browser/test_practice.py -v --headed --slowmo=500
```

### Key Test Scenarios

1. **Staff Profiles**
   - Create profile with role
   - Verify auto-permissions by role
   - DEA credential validation

2. **Scheduling**
   - Create and confirm shifts
   - Weekly schedule navigation
   - Shift conflicts detection

3. **Time Tracking**
   - Clock in/out flow
   - Hours calculation
   - Approval workflow

4. **Tasks**
   - Create and assign tasks
   - Priority ordering
   - Status transitions
   - Due date handling

5. **Clinical Notes**
   - SOAP note creation
   - Note locking
   - Patient history queries
