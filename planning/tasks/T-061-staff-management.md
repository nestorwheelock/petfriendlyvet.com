# T-061: Staff Management & Scheduling

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md and [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Full Stack Developer
**Objective**: Implement staff profiles, scheduling, and time tracking
**Related Story**: S-008
**Epoch**: 6
**Estimate**: 5 hours

### Constraints
**Allowed File Paths**: apps/staff/, apps/appointments/
**Forbidden Paths**: None

### Deliverables
- [ ] StaffProfile model
- [ ] Schedule/shift management
- [ ] Time tracking
- [ ] Permission assignments
- [ ] Staff dashboard

### Implementation Details

#### Models
```python
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField

User = get_user_model()


class StaffProfile(models.Model):
    """Staff member profiles."""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name='staff_profile'
    )

    ROLE_CHOICES = [
        ('veterinarian', 'Veterinario'),
        ('technician', 'Técnico'),
        ('receptionist', 'Recepcionista'),
        ('groomer', 'Estilista'),
        ('assistant', 'Asistente'),
        ('admin', 'Administrador'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    # Professional info
    title = models.CharField(max_length=100, blank=True)
    license_number = models.CharField(max_length=50, blank=True)
    specializations = models.JSONField(default=list)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to='staff/', null=True, blank=True)

    # Contact
    phone = models.CharField(max_length=20, blank=True)
    emergency_contact = models.CharField(max_length=200, blank=True)

    # Employment
    hire_date = models.DateField()
    employment_type = models.CharField(max_length=20, default='full_time')
    # full_time, part_time, contract

    hourly_rate = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    salary = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    # Capabilities
    can_perform_surgery = models.BooleanField(default=False)
    can_prescribe = models.BooleanField(default=False)
    can_handle_emergencies = models.BooleanField(default=False)
    services_offered = models.ManyToManyField(
        'appointments.ServiceType', blank=True
    )

    # Status
    is_active = models.BooleanField(default=True)
    is_available_for_booking = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['role', 'user__first_name']


class WorkSchedule(models.Model):
    """Regular weekly work schedule."""

    staff = models.ForeignKey(
        StaffProfile, on_delete=models.CASCADE,
        related_name='schedules'
    )

    DAY_CHOICES = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    day_of_week = models.IntegerField(choices=DAY_CHOICES)

    start_time = models.TimeField()
    end_time = models.TimeField()

    # Break
    break_start = models.TimeField(null=True, blank=True)
    break_end = models.TimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['staff', 'day_of_week']
        ordering = ['day_of_week', 'start_time']


class ScheduleException(models.Model):
    """Schedule exceptions (time off, special hours)."""

    staff = models.ForeignKey(
        StaffProfile, on_delete=models.CASCADE,
        related_name='exceptions'
    )

    EXCEPTION_TYPES = [
        ('vacation', 'Vacaciones'),
        ('sick', 'Enfermedad'),
        ('personal', 'Personal'),
        ('training', 'Capacitación'),
        ('overtime', 'Horas extra'),
        ('special', 'Horario especial'),
    ]
    exception_type = models.CharField(max_length=20, choices=EXCEPTION_TYPES)

    date = models.DateField()
    start_time = models.TimeField(null=True)
    end_time = models.TimeField(null=True)
    is_full_day = models.BooleanField(default=True)

    reason = models.TextField(blank=True)

    # Approval
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+'
    )
    approved_at = models.DateTimeField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']


class TimeEntry(models.Model):
    """Clock in/out time tracking."""

    staff = models.ForeignKey(
        StaffProfile, on_delete=models.CASCADE,
        related_name='time_entries'
    )

    date = models.DateField()
    clock_in = models.DateTimeField()
    clock_out = models.DateTimeField(null=True)

    # Break tracking
    break_start = models.DateTimeField(null=True)
    break_end = models.DateTimeField(null=True)
    break_minutes = models.IntegerField(default=0)

    # Calculated
    hours_worked = models.DecimalField(
        max_digits=5, decimal_places=2, null=True
    )
    overtime_hours = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )

    notes = models.TextField(blank=True)

    # Approval
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-clock_in']
        unique_together = ['staff', 'date']

    def calculate_hours(self):
        """Calculate hours worked."""
        if not self.clock_out:
            return None

        total = (self.clock_out - self.clock_in).total_seconds() / 3600
        total -= self.break_minutes / 60
        self.hours_worked = round(total, 2)

        # Check for overtime (>8 hours)
        if self.hours_worked > 8:
            self.overtime_hours = self.hours_worked - 8

        return self.hours_worked


class StaffAssignment(models.Model):
    """Assign staff to appointments."""

    appointment = models.ForeignKey(
        'appointments.Appointment', on_delete=models.CASCADE,
        related_name='staff_assignments'
    )
    staff = models.ForeignKey(
        StaffProfile, on_delete=models.CASCADE,
        related_name='assignments'
    )

    ROLE_CHOICES = [
        ('primary', 'Principal'),
        ('assistant', 'Asistente'),
        ('observer', 'Observador'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='primary')

    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['appointment', 'staff']
```

#### Staff Service
```python
from datetime import date, datetime, timedelta
from django.utils import timezone


class StaffService:
    """Staff management operations."""

    def get_available_staff(
        self,
        date: date,
        start_time: datetime,
        end_time: datetime,
        service_type=None,
        role: str = None
    ):
        """Get available staff for time slot."""

        # Get day of week
        day_of_week = date.weekday()

        # Staff with schedule on this day
        available = StaffProfile.objects.filter(
            is_active=True,
            is_available_for_booking=True,
            schedules__day_of_week=day_of_week,
            schedules__start_time__lte=start_time.time(),
            schedules__end_time__gte=end_time.time()
        )

        # Filter by role
        if role:
            available = available.filter(role=role)

        # Filter by service capability
        if service_type:
            available = available.filter(services_offered=service_type)

        # Exclude those with exceptions
        available = available.exclude(
            exceptions__date=date,
            exceptions__is_full_day=True,
            exceptions__is_approved=True
        )

        # Exclude those with conflicting appointments
        available = available.exclude(
            assignments__appointment__date=date,
            assignments__appointment__start_time__lt=end_time,
            assignments__appointment__end_time__gt=start_time,
            assignments__appointment__status__in=['confirmed', 'in_progress']
        )

        return available

    def clock_in(self, staff: StaffProfile) -> TimeEntry:
        """Clock in staff member."""

        today = timezone.now().date()

        # Check if already clocked in
        existing = TimeEntry.objects.filter(
            staff=staff, date=today, clock_out__isnull=True
        ).first()

        if existing:
            raise ValueError("Ya registró entrada hoy")

        entry = TimeEntry.objects.create(
            staff=staff,
            date=today,
            clock_in=timezone.now()
        )

        return entry

    def clock_out(self, staff: StaffProfile) -> TimeEntry:
        """Clock out staff member."""

        entry = TimeEntry.objects.filter(
            staff=staff,
            clock_out__isnull=True
        ).order_by('-clock_in').first()

        if not entry:
            raise ValueError("No hay entrada activa")

        entry.clock_out = timezone.now()
        entry.calculate_hours()
        entry.save()

        return entry

    def get_payroll_summary(
        self,
        staff: StaffProfile,
        start_date: date,
        end_date: date
    ) -> dict:
        """Get payroll summary for period."""

        entries = TimeEntry.objects.filter(
            staff=staff,
            date__gte=start_date,
            date__lte=end_date,
            is_approved=True
        )

        regular_hours = sum(
            e.hours_worked - e.overtime_hours
            for e in entries if e.hours_worked
        )
        overtime_hours = sum(
            e.overtime_hours for e in entries
        )

        return {
            'staff': staff,
            'period_start': start_date,
            'period_end': end_date,
            'days_worked': entries.count(),
            'regular_hours': regular_hours,
            'overtime_hours': overtime_hours,
            'total_hours': regular_hours + overtime_hours,
            'regular_pay': regular_hours * float(staff.hourly_rate or 0),
            'overtime_pay': overtime_hours * float(staff.hourly_rate or 0) * 1.5,
        }
```

### Test Cases
- [ ] Staff profile CRUD works
- [ ] Schedule creation works
- [ ] Available staff returns correct results
- [ ] Exceptions block availability
- [ ] Clock in/out calculates hours
- [ ] Overtime calculated correctly
- [ ] Staff assignment to appointments works

### Definition of Done
- [ ] Staff management complete
- [ ] Scheduling system working
- [ ] Time tracking functional
- [ ] Payroll summaries accurate
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-020: Appointment Models
