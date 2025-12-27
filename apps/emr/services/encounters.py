"""Encounter service functions.

Business logic for Encounter operations.
All writes go through here, not directly from views.
"""
from collections import defaultdict

from django.db import transaction
from django.utils import timezone

from apps.emr.models import Encounter, ClinicalEvent
from apps.locations.models import Location
from apps.practice.models import PatientRecord

from . import events


def get_whiteboard_data(location: Location) -> dict:
    """Get encounters grouped by pipeline state for whiteboard display.

    Args:
        location: The location to filter by.

    Returns:
        Dict mapping state -> list of encounters
    """
    encounters_qs = Encounter.objects.filter(
        location=location,
    ).select_related(
        'patient__pet',
        'assigned_vet',
        'assigned_tech',
    ).order_by('created_at')

    # Only show active encounters (not completed/cancelled/no_show)
    active_states = [
        'scheduled', 'checked_in', 'roomed', 'in_exam',
        'pending_orders', 'awaiting_results', 'treatment', 'checkout'
    ]
    encounters_qs = encounters_qs.filter(pipeline_state__in=active_states)

    # Group by state
    by_state = defaultdict(list)
    for encounter in encounters_qs:
        by_state[encounter.pipeline_state].append(encounter)

    return dict(by_state)


def get_whiteboard_encounters(location: Location):
    """Get all active encounters for a location.

    Args:
        location: The location to filter by.

    Returns:
        QuerySet of active Encounters
    """
    active_states = [
        'scheduled', 'checked_in', 'roomed', 'in_exam',
        'pending_orders', 'awaiting_results', 'treatment', 'checkout'
    ]
    return Encounter.objects.filter(
        location=location,
        pipeline_state__in=active_states,
    ).select_related(
        'patient__pet',
        'assigned_vet',
        'assigned_tech',
    ).order_by('created_at')


@transaction.atomic
def create_encounter(
    patient: PatientRecord,
    location: Location,
    created_by,
    encounter_type: str = 'routine',
    chief_complaint: str = '',
    appointment=None,
    assigned_vet=None,
    assigned_tech=None,
) -> Encounter:
    """Create a new encounter.

    Args:
        patient: The patient for this encounter.
        location: Required - where the encounter takes place.
        created_by: User creating the encounter.
        encounter_type: Type of encounter (routine, urgent, etc.)
        chief_complaint: Reason for visit.
        appointment: Optional linked appointment.
        assigned_vet: Optional assigned veterinarian.
        assigned_tech: Optional assigned technician.

    Returns:
        The created Encounter.
    """
    encounter = Encounter.objects.create(
        patient=patient,
        location=location,
        created_by=created_by,
        encounter_type=encounter_type,
        chief_complaint=chief_complaint,
        appointment=appointment,
        assigned_vet=assigned_vet,
        assigned_tech=assigned_tech,
        pipeline_state='scheduled',
        scheduled_at=timezone.now(),
    )

    # Log clinical event
    events.log_encounter_created(encounter, created_by)

    return encounter


@transaction.atomic
def transition_state(encounter: Encounter, new_state: str, user) -> Encounter:
    """Transition encounter to a new pipeline state.

    Creates a ClinicalEvent for the audit trail.

    Args:
        encounter: The encounter to transition.
        new_state: The target state.
        user: The user performing the transition.

    Returns:
        The updated Encounter.

    Raises:
        ValueError: If the state transition is invalid.
    """
    valid_states = [s[0] for s in Encounter.PIPELINE_STATES]
    if new_state not in valid_states:
        raise ValueError(f"Invalid state: {new_state}")

    old_state = encounter.pipeline_state

    if old_state == new_state:
        return encounter  # No-op

    # Update state
    encounter.pipeline_state = new_state

    # Set timestamp for the new state
    now = timezone.now()
    state_timestamp_map = {
        'checked_in': 'checked_in_at',
        'roomed': 'roomed_at',
        'in_exam': 'exam_started_at',
        'completed': 'discharged_at',
    }
    if new_state in state_timestamp_map:
        setattr(encounter, state_timestamp_map[new_state], now)

    # Handle exam end timestamp
    if old_state == 'in_exam' and new_state != 'in_exam':
        encounter.exam_ended_at = now

    encounter.save()

    # Log clinical event
    events.log_state_transition(encounter, old_state, new_state, user)

    return encounter
