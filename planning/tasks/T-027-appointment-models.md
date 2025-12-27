# T-027: Appointment Models

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md and [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement appointment scheduling models
**Related Story**: S-004
**Epoch**: 2
**Estimate**: 4 hours

### Constraints
**Allowed File Paths**: apps/appointments/models/
**Forbidden Paths**: apps/store/

### Deliverables
- [ ] ServiceType model
- [ ] Appointment model
- [ ] TimeSlot/availability model
- [ ] Staff schedule model
- [ ] Appointment status workflow
- [ ] Recurring appointment support

### Implementation Details

#### Models
```python
class ServiceType(models.Model):
    """Types of services offered."""

    name = models.CharField(max_length=200)
    name_es = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200)

    category = models.CharField(max_length=50, choices=[
        ('clinic', 'Clínica'),
        ('surgery', 'Cirugía'),
        ('grooming', 'Estética'),
        ('lab', 'Laboratorio'),
        ('emergency', 'Emergencia'),
    ])

    description = models.TextField(blank=True)
    description_es = models.TextField(blank=True)
    description_en = models.TextField(blank=True)

    duration_minutes = models.IntegerField(default=30)
    buffer_minutes = models.IntegerField(default=0)  # Time between appointments

    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    price_text = models.CharField(max_length=100, blank=True)  # "Desde $500"

    # Availability
    is_bookable_online = models.BooleanField(default=True)
    requires_deposit = models.BooleanField(default=False)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    # Staff requirements
    requires_vet = models.BooleanField(default=True)
    requires_technician = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']


class StaffSchedule(models.Model):
    """Staff availability schedule."""

    staff = models.ForeignKey(User, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.IntegerField(choices=[
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ])
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['staff', 'day_of_week']


class ScheduleException(models.Model):
    """Exceptions to regular schedule (days off, vacations)."""

    staff = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField()
    is_closed = models.BooleanField(default=True)  # Full day off
    start_time = models.TimeField(null=True)  # Partial availability
    end_time = models.TimeField(null=True)
    reason = models.CharField(max_length=200, blank=True)
    affects_all_staff = models.BooleanField(default=False)  # Clinic closure

    class Meta:
        ordering = ['date']


class Appointment(models.Model):
    """Scheduled appointment."""

    STATUS_CHOICES = [
        ('requested', 'Solicitada'),
        ('confirmed', 'Confirmada'),
        ('checked_in', 'Llegó'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
        ('no_show', 'No Asistió'),
    ]

    # Core fields
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='appointments')
    service = models.ForeignKey(ServiceType, on_delete=models.PROTECT)

    # Scheduling
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    end_time = models.TimeField()  # Calculated from duration
    duration_minutes = models.IntegerField()

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')

    # Staff
    assigned_vet = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='vet_appointments'
    )

    # Details
    reason = models.TextField(blank=True)  # Why client is coming
    notes = models.TextField(blank=True)  # Internal notes
    client_notes = models.TextField(blank=True)  # Client's additional info

    # Confirmation
    confirmed_at = models.DateTimeField(null=True)
    confirmed_via = models.CharField(max_length=20, blank=True)  # sms, email, whatsapp, phone

    # Completion
    checked_in_at = models.DateTimeField(null=True)
    completed_at = models.DateTimeField(null=True)
    cancelled_at = models.DateTimeField(null=True)
    cancellation_reason = models.TextField(blank=True)

    # Billing
    deposit_paid = models.BooleanField(default=False)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    # Links
    medical_record = models.OneToOneField(
        'vet_clinic.MedicalRecord',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Booking source
    booked_via = models.CharField(max_length=20, choices=[
        ('ai_chat', 'AI Chat'),
        ('website', 'Website Form'),
        ('phone', 'Phone'),
        ('whatsapp', 'WhatsApp'),
        ('walk_in', 'Walk-in'),
        ('admin', 'Admin'),
    ])

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_appointments'
    )

    class Meta:
        ordering = ['scheduled_date', 'scheduled_time']

    @property
    def datetime(self) -> datetime:
        """Return combined datetime."""
        return datetime.combine(self.scheduled_date, self.scheduled_time)

    def save(self, *args, **kwargs):
        # Auto-calculate end time
        if not self.end_time:
            start = datetime.combine(self.scheduled_date, self.scheduled_time)
            end = start + timedelta(minutes=self.duration_minutes)
            self.end_time = end.time()
        super().save(*args, **kwargs)


class RecurringAppointment(models.Model):
    """Template for recurring appointments."""

    pet = models.ForeignKey(Pet, on_delete=models.CASCADE)
    service = models.ForeignKey(ServiceType, on_delete=models.PROTECT)

    frequency = models.CharField(max_length=20, choices=[
        ('weekly', 'Weekly'),
        ('biweekly', 'Every 2 Weeks'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Every 3 Months'),
        ('annually', 'Annually'),
    ])

    day_of_week = models.IntegerField(null=True)  # For weekly
    day_of_month = models.IntegerField(null=True)  # For monthly
    preferred_time = models.TimeField()

    start_date = models.DateField()
    end_date = models.DateField(null=True)

    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
```

### Availability Calculation
```python
class AvailabilityService:
    """Calculate available appointment slots."""

    def get_available_slots(
        self,
        date: date,
        service: ServiceType,
        vet: User = None
    ) -> list[time]:
        """Get available time slots for a date."""

        # Get base schedule
        day = date.weekday()
        schedules = StaffSchedule.objects.filter(
            day_of_week=day,
            is_active=True
        )
        if vet:
            schedules = schedules.filter(staff=vet)

        # Check exceptions
        exceptions = ScheduleException.objects.filter(date=date)

        # Get existing appointments
        existing = Appointment.objects.filter(
            scheduled_date=date,
            status__in=['confirmed', 'checked_in', 'in_progress']
        )

        # Calculate available slots
        slots = []
        for schedule in schedules:
            current = datetime.combine(date, schedule.start_time)
            end = datetime.combine(date, schedule.end_time)

            while current + timedelta(minutes=service.duration_minutes) <= end:
                if self._is_slot_available(current.time(), service, existing):
                    slots.append(current.time())
                current += timedelta(minutes=15)  # 15-minute intervals

        return slots
```

### Test Cases
- [ ] Service types CRUD
- [ ] Appointments create with validation
- [ ] Availability calculates correctly
- [ ] Schedule exceptions apply
- [ ] Status transitions valid
- [ ] End time auto-calculated
- [ ] Recurring appointments generate

### Definition of Done
- [ ] All models migrated
- [ ] Availability algorithm working
- [ ] Status workflow enforced
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-024: Pet Profile Models
