"""Appointment availability and booking services."""
from datetime import datetime, time, timedelta
from typing import Optional

from django.db.models import Q
from django.utils import timezone

from .models import Appointment, ScheduleBlock, ServiceType


class AvailabilityService:
    """Service for managing appointment availability and booking."""

    # Statuses that block a time slot
    BLOCKING_STATUSES = ['scheduled', 'confirmed', 'in_progress']

    @classmethod
    def get_available_slots(
        cls,
        date: datetime.date,
        service: ServiceType,
        staff=None
    ) -> list[dict]:
        """Get available time slots for a given date.

        Args:
            date: The date to check availability for
            service: The service type being booked
            staff: Optional specific staff member. If None, returns slots
                   from any available staff.

        Returns:
            List of dicts with 'time' and 'staff_id' keys
        """
        day_of_week = date.weekday()
        duration = timedelta(minutes=service.duration_minutes)

        # Get active schedule blocks for this day
        blocks_query = ScheduleBlock.objects.filter(
            day_of_week=day_of_week,
            is_active=True
        )
        if staff:
            blocks_query = blocks_query.filter(staff=staff)

        blocks = blocks_query.order_by('staff', 'start_time')

        if not blocks.exists():
            return []

        # Get existing appointments for this date
        date_start = timezone.make_aware(datetime.combine(date, time.min))
        date_end = timezone.make_aware(datetime.combine(date, time.max))

        existing_appointments = Appointment.objects.filter(
            scheduled_start__gte=date_start,
            scheduled_start__lte=date_end,
            status__in=cls.BLOCKING_STATUSES
        )
        if staff:
            existing_appointments = existing_appointments.filter(
                veterinarian=staff
            )

        # Build list of booked time ranges per staff
        booked_ranges = {}
        for appt in existing_appointments:
            staff_id = appt.veterinarian_id
            if staff_id not in booked_ranges:
                booked_ranges[staff_id] = []
            booked_ranges[staff_id].append(
                (appt.scheduled_start, appt.scheduled_end)
            )

        # Generate available slots
        available_slots = []

        for block in blocks:
            block_staff_id = block.staff_id
            staff_booked = booked_ranges.get(block_staff_id, [])

            # Generate slots within this block
            current_time = datetime.combine(date, block.start_time)
            block_end = datetime.combine(date, block.end_time)

            while current_time + duration <= block_end:
                slot_start = timezone.make_aware(current_time)
                slot_end = slot_start + duration

                # Check if slot overlaps with any booked appointment
                is_available = True
                for booked_start, booked_end in staff_booked:
                    if cls._times_overlap(
                        slot_start, slot_end, booked_start, booked_end
                    ):
                        is_available = False
                        break

                if is_available:
                    available_slots.append({
                        'time': current_time.time(),
                        'staff_id': block_staff_id
                    })

                current_time += duration

        return available_slots

    @classmethod
    def is_slot_available(
        cls,
        start_time: datetime,
        service: ServiceType,
        staff
    ) -> bool:
        """Check if a specific time slot is available.

        Args:
            start_time: The proposed start time (timezone-aware datetime)
            service: The service type being booked
            staff: The staff member

        Returns:
            True if slot is available, False otherwise
        """
        date = start_time.date()
        day_of_week = date.weekday()
        slot_time = start_time.time()
        duration = timedelta(minutes=service.duration_minutes)
        end_time = start_time + duration

        # Check if there's an active schedule block covering this time
        matching_blocks = ScheduleBlock.objects.filter(
            staff=staff,
            day_of_week=day_of_week,
            is_active=True,
            start_time__lte=slot_time,
        )

        # Filter blocks where the slot fits within the block
        slot_end_time = (
            datetime.combine(date, slot_time) + duration
        ).time()

        valid_block = False
        for block in matching_blocks:
            if block.end_time >= slot_end_time:
                valid_block = True
                break

        if not valid_block:
            return False

        # Check for conflicting appointments
        conflicting = Appointment.objects.filter(
            veterinarian=staff,
            status__in=cls.BLOCKING_STATUSES
        ).filter(
            Q(scheduled_start__lt=end_time) & Q(scheduled_end__gt=start_time)
        )

        return not conflicting.exists()

    @classmethod
    def book_appointment(
        cls,
        owner,
        pet,
        service: ServiceType,
        staff,
        start_time: datetime,
        notes: str = ''
    ) -> Appointment:
        """Book an appointment.

        Args:
            owner: The pet owner (User)
            pet: The pet (can be None if service doesn't require pet)
            service: The service type
            staff: The veterinarian/staff member
            start_time: The appointment start time
            notes: Optional notes

        Returns:
            The created Appointment

        Raises:
            ValueError: If slot is not available or pet is required but not provided
        """
        # Check if pet is required
        if service.requires_pet and pet is None:
            raise ValueError(
                'A pet is required for this service.'
            )

        # Check availability
        if not cls.is_slot_available(start_time, service, staff):
            raise ValueError(
                'The requested time slot is not available.'
            )

        # Calculate end time
        end_time = start_time + timedelta(minutes=service.duration_minutes)

        # Create appointment
        appointment = Appointment.objects.create(
            owner=owner,
            pet=pet,
            service=service,
            veterinarian=staff,
            scheduled_start=start_time,
            scheduled_end=end_time,
            status='scheduled',
            notes=notes
        )

        return appointment

    @staticmethod
    def _times_overlap(
        start1: datetime,
        end1: datetime,
        start2: datetime,
        end2: datetime
    ) -> bool:
        """Check if two time ranges overlap."""
        return start1 < end2 and end1 > start2
