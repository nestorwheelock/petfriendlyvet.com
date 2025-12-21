# S-004: Appointment Booking via AI

**Story Type:** User Story
**Priority:** High
**Epoch:** 2
**Status:** PENDING

## User Story

**As a** pet owner
**I want to** book veterinary appointments through natural conversation
**So that** I can schedule visits without calling during business hours

**As a** clinic staff member
**I want to** manage appointments through the AI admin interface
**So that** I can efficiently handle scheduling from my phone

## Acceptance Criteria

### Booking via AI Chat
- [ ] User can request an appointment through conversation
- [ ] AI asks for necessary information (pet, service, preferred time)
- [ ] AI shows available time slots
- [ ] User confirms booking through chat
- [ ] Confirmation displayed and sent via email/SMS

### Availability Management
- [ ] Calendar shows available slots
- [ ] Blocked times (lunch, closed days) respected
- [ ] Service duration affects slot availability
- [ ] Buffer time between appointments configurable

### Appointment Management
- [ ] User can view upcoming appointments
- [ ] User can request to reschedule or cancel
- [ ] Staff receives notifications for new/changed appointments
- [ ] Reminders sent 24 hours and 2 hours before

### Admin Capabilities
- [ ] Staff can view daily/weekly schedule
- [ ] Staff can confirm, reschedule, or cancel appointments
- [ ] Staff can block time for breaks/meetings
- [ ] Staff can add walk-in appointments

## Example AI Conversations

### New Appointment
```
User: I need to bring Luna in for a checkup
AI: I'd be happy to help schedule a checkup for Luna! 🐕

    What type of visit does Luna need?
    • General checkup
    • Vaccination
    • Sick visit
    • Follow-up

User: General checkup
AI: Great! Let me check Dr. Pablo's availability for a general checkup
    (approximately 30 minutes).

    Here are the next available slots:
    📅 Tomorrow (Saturday, Dec 21):
       • 10:00 AM
       • 11:30 AM
       • 3:00 PM

    📅 Monday, Dec 23:
       • 9:00 AM
       • 10:30 AM
       • 2:00 PM
       • 4:30 PM

    Which time works best for you?

User: Tomorrow at 10am
AI: Perfect! I've scheduled Luna's general checkup:

    ✅ **Appointment Confirmed**
    📅 Saturday, December 21, 2025
    ⏰ 10:00 AM
    🐕 Luna (Golden Retriever)
    📍 Pet-Friendly, Puerto Morelos

    You'll receive a confirmation email and a reminder 24 hours before.

    Is there anything specific you'd like Dr. Pablo to check during the visit?
```

### Rescheduling
```
User: I need to change Luna's appointment tomorrow
AI: I see Luna has an appointment scheduled for:
    📅 Saturday, December 21 at 10:00 AM - General checkup

    Would you like to:
    • Reschedule to a different time
    • Cancel the appointment

User: Reschedule please
AI: No problem! Here are other available times:

    📅 Saturday, Dec 21:
       • 11:30 AM
       • 3:00 PM

    📅 Monday, Dec 23:
       • 9:00 AM
       • 10:30 AM

    Which time would you prefer?
```

### Staff View
```
Dr. Pablo: Show me tomorrow's schedule
AI: Here's your schedule for Saturday, December 21:

    🗓️ **Saturday, Dec 21, 2025**

    9:00 AM  - Max (Poodle) - Vaccination
              Owner: María García | 📱 998-123-4567

    10:00 AM - Luna (Golden Retriever) - General checkup
              Owner: John Smith | 📱 998-234-5678

    11:30 AM - [Available]

    12:00 PM - 2:00 PM [LUNCH BREAK]

    2:00 PM  - Whiskers (Cat) - Sick visit
              Owner: Ana López | 📱 998-345-6789
              Note: Not eating for 2 days

    3:00 PM  - [Available]
    3:30 PM  - [Available]
    4:00 PM  - [Available]

    Would you like to block any times or add appointments?
```

## Technical Requirements

### Package: django-appointments

```python
# models.py

class ServiceType(models.Model):
    name = models.CharField(max_length=100)
    name_es = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    duration_minutes = models.IntegerField(default=30)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    requires_pet = models.BooleanField(default=True)


class ScheduleBlock(models.Model):
    """Recurring schedule (e.g., open hours, lunch breaks)"""
    day_of_week = models.IntegerField()  # 0=Monday, 6=Sunday
    start_time = models.TimeField()
    end_time = models.TimeField()
    block_type = models.CharField(max_length=20)  # 'available', 'break', 'closed'


class ScheduleException(models.Model):
    """One-time schedule changes (holidays, special hours)"""
    date = models.DateField()
    is_closed = models.BooleanField(default=False)
    start_time = models.TimeField(null=True)
    end_time = models.TimeField(null=True)
    reason = models.CharField(max_length=200, blank=True)


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Confirmation'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]

    pet = models.ForeignKey('vet_clinic.Pet', on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    service_type = models.ForeignKey(ServiceType, on_delete=models.PROTECT)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)  # Internal notes
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_via = models.CharField(max_length=20, default='ai_chat')  # ai_chat, admin, phone

    class Meta:
        ordering = ['date', 'start_time']

    def save(self, *args, **kwargs):
        if not self.end_time:
            self.end_time = (
                datetime.combine(self.date, self.start_time) +
                timedelta(minutes=self.service_type.duration_minutes)
            ).time()
        super().save(*args, **kwargs)


class AppointmentReminder(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    reminder_type = models.CharField(max_length=20)  # email, sms, whatsapp
    scheduled_for = models.DateTimeField()
    sent_at = models.DateTimeField(null=True)
    status = models.CharField(max_length=20, default='pending')
```

### Availability Service

```python
# services/availability.py

class AvailabilityService:
    def get_available_slots(self, date: date, service_type: ServiceType) -> list[time]:
        """Get available time slots for a given date and service."""
        duration = service_type.duration_minutes

        # Get base schedule for day of week
        day_schedule = self._get_day_schedule(date)
        if not day_schedule:
            return []  # Clinic closed

        # Get existing appointments
        existing = Appointment.objects.filter(
            date=date,
            status__in=['pending', 'confirmed']
        )

        # Calculate available slots
        slots = []
        current_time = day_schedule['start']

        while current_time < day_schedule['end']:
            end_time = self._add_minutes(current_time, duration)

            if self._is_slot_available(current_time, end_time, existing, day_schedule):
                slots.append(current_time)

            current_time = self._add_minutes(current_time, 30)  # 30-min increments

        return slots

    def _is_slot_available(self, start, end, existing_appointments, schedule):
        # Check against existing appointments
        for apt in existing_appointments:
            if self._times_overlap(start, end, apt.start_time, apt.end_time):
                return False

        # Check against breaks
        for break_period in schedule.get('breaks', []):
            if self._times_overlap(start, end, break_period['start'], break_period['end']):
                return False

        return True
```

### AI Tools (Epoch 2 additions)

```python
APPOINTMENT_TOOLS = [
    {
        "name": "check_availability",
        "description": "Check available appointment slots for a date range",
        "parameters": {
            "type": "object",
            "properties": {
                "service_type": {"type": "string"},
                "start_date": {"type": "string", "format": "date"},
                "end_date": {"type": "string", "format": "date"}
            },
            "required": ["service_type"]
        }
    },
    {
        "name": "book_appointment",
        "description": "Book an appointment for a pet",
        "parameters": {
            "type": "object",
            "properties": {
                "pet_id": {"type": "integer"},
                "service_type": {"type": "string"},
                "date": {"type": "string", "format": "date"},
                "time": {"type": "string", "format": "time"},
                "reason": {"type": "string"}
            },
            "required": ["pet_id", "service_type", "date", "time"]
        }
    },
    {
        "name": "get_user_appointments",
        "description": "Get upcoming appointments for the current user",
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "name": "cancel_appointment",
        "description": "Cancel an appointment",
        "parameters": {
            "type": "object",
            "properties": {
                "appointment_id": {"type": "integer"},
                "reason": {"type": "string"}
            },
            "required": ["appointment_id"]
        }
    },
    {
        "name": "reschedule_appointment",
        "description": "Reschedule an existing appointment",
        "parameters": {
            "type": "object",
            "properties": {
                "appointment_id": {"type": "integer"},
                "new_date": {"type": "string", "format": "date"},
                "new_time": {"type": "string", "format": "time"}
            },
            "required": ["appointment_id", "new_date", "new_time"]
        }
    }
]

# Admin-only appointment tools
ADMIN_APPOINTMENT_TOOLS = [
    {
        "name": "get_daily_schedule",
        "description": "Get all appointments for a specific date",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "format": "date"}
            }
        }
    },
    {
        "name": "confirm_appointment",
        "description": "Confirm a pending appointment",
        "parameters": {
            "type": "object",
            "properties": {
                "appointment_id": {"type": "integer"}
            },
            "required": ["appointment_id"]
        }
    },
    {
        "name": "block_time",
        "description": "Block a time slot (for breaks, meetings, etc.)",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "format": "date"},
                "start_time": {"type": "string", "format": "time"},
                "end_time": {"type": "string", "format": "time"},
                "reason": {"type": "string"}
            },
            "required": ["date", "start_time", "end_time"]
        }
    }
]
```

## Definition of Done

- [ ] AI can check availability and book appointments
- [ ] Users can view/cancel/reschedule their appointments
- [ ] Staff can view daily schedule via AI
- [ ] Email confirmations sent on booking
- [ ] Reminders sent 24h and 2h before
- [ ] Calendar respects business hours and breaks
- [ ] Walk-in appointments can be added by staff
- [ ] Tests written and passing (>95% coverage)
- [ ] Documentation updated

## Dependencies

- S-001: Foundation + AI Core
- S-002: AI Chat Interface
- S-003: Pet Profiles (to link appointments to pets)
- Email service configured

## Notes

- SMS/WhatsApp reminders added in Epoch 4
- Consider calendar sync (Google Calendar) for future epoch
- Time zone handling important for tourist clients

## Development Process

**Before implementing this story**, review and follow the **23-Step TDD Cycle** in:
- `CLAUDE.md` - Global development workflow
- `planning/TASK_BREAKDOWN.md` - Specific tasks for this story

Tests must be written before implementation. >95% coverage required.
