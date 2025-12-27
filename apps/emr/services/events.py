"""ClinicalEvent service functions.

Business logic for ClinicalEvent operations.
ClinicalEvent is APPEND-ONLY. No edits, only error correction.
"""
from django.utils import timezone

from apps.emr.models import ClinicalEvent, Encounter


def log_encounter_created(encounter: Encounter, user) -> ClinicalEvent:
    """Log that an encounter was created.

    Args:
        encounter: The newly created encounter.
        user: The user who created it.

    Returns:
        The created ClinicalEvent.
    """
    return ClinicalEvent.objects.create(
        patient=encounter.patient,
        encounter=encounter,
        location=encounter.location,
        event_type='encounter_created',
        occurred_at=timezone.now(),
        recorded_by=user,
        summary=f"Encounter created: {encounter.get_encounter_type_display()} - {encounter.chief_complaint[:100] if encounter.chief_complaint else 'No complaint specified'}",
        is_significant=True,
    )


def log_state_transition(
    encounter: Encounter,
    old_state: str,
    new_state: str,
    user,
) -> ClinicalEvent:
    """Log a pipeline state transition.

    Args:
        encounter: The encounter that transitioned.
        old_state: The previous state.
        new_state: The new state.
        user: The user who performed the transition.

    Returns:
        The created ClinicalEvent.
    """
    # Get display names
    state_display = dict(Encounter.PIPELINE_STATES)
    old_display = state_display.get(old_state, old_state)
    new_display = state_display.get(new_state, new_state)

    return ClinicalEvent.objects.create(
        patient=encounter.patient,
        encounter=encounter,
        location=encounter.location,
        event_type='state_change',
        event_subtype=f"{old_state}_to_{new_state}",
        occurred_at=timezone.now(),
        recorded_by=user,
        summary=f"Status changed: {old_display} → {new_display}",
        is_significant=new_state in ('in_exam', 'completed', 'cancelled'),
    )


def log_problem_added(problem, user) -> ClinicalEvent:
    """Log that a problem was added to a patient.

    Args:
        problem: The PatientProblem that was added.
        user: The user who added it.

    Returns:
        The created ClinicalEvent.
    """
    return ClinicalEvent.objects.create(
        patient=problem.patient,
        patient_problem=problem,
        event_type='problem_added',
        occurred_at=timezone.now(),
        recorded_by=user,
        summary=f"Problem added: {problem.name} ({problem.get_problem_type_display()})",
        is_significant=problem.is_alert,
    )


def log_problem_resolved(problem, user) -> ClinicalEvent:
    """Log that a problem was resolved.

    Args:
        problem: The PatientProblem that was resolved.
        user: The user who resolved it.

    Returns:
        The created ClinicalEvent.
    """
    return ClinicalEvent.objects.create(
        patient=problem.patient,
        patient_problem=problem,
        event_type='problem_resolved',
        occurred_at=timezone.now(),
        recorded_by=user,
        summary=f"Problem resolved: {problem.name}",
        is_significant=True,
    )


def log_clinical_note(patient, user, note_text: str, encounter=None) -> ClinicalEvent:
    """Log a clinical note.

    Args:
        patient: The patient.
        user: The user adding the note.
        note_text: The note content.
        encounter: Optional encounter context.

    Returns:
        The created ClinicalEvent.
    """
    return ClinicalEvent.objects.create(
        patient=patient,
        encounter=encounter,
        location=encounter.location if encounter else None,
        event_type='note',
        occurred_at=timezone.now(),
        recorded_by=user,
        summary=note_text[:500],  # Truncate to field max
        is_significant=False,
    )
