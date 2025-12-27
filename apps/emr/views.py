"""EMR views for Staff Panel → Clinical section.

These are thin views that:
1. Check permissions
2. Get selected location from session
3. Delegate to service functions
4. Render templates

All EMR writes go through apps/emr/services/ - no direct model .save() here.
"""
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from apps.locations.models import Location
from apps.practice.models import PatientRecord

from .models import Encounter, PatientProblem, ClinicalEvent
from .services import encounters, events


# Session key for selected location (namespaced to avoid collisions)
SESSION_LOCATION_KEY = 'emr_selected_location_id'


def get_selected_location(request):
    """Get the currently selected location from session.

    Returns:
        Location or None
    """
    location_id = request.session.get(SESSION_LOCATION_KEY)
    if location_id:
        try:
            return Location.objects.get(id=location_id, is_active=True)
        except Location.DoesNotExist:
            # Clear invalid session value
            del request.session[SESSION_LOCATION_KEY]
    return None


def staff_required(view_func):
    """Decorator requiring staff access."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Staff access required")
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@staff_required
def whiteboard(request):
    """Encounter whiteboard - Kanban board by pipeline state.

    If no location selected, shows location selector.
    Otherwise shows encounters filtered by location, grouped by state.
    """
    location = get_selected_location(request)
    locations = Location.objects.filter(is_active=True)

    if not location:
        # Show location selector
        return render(request, 'emr/whiteboard.html', {
            'location': None,
            'locations': locations,
            'needs_location': True,
        })

    # Get encounters grouped by pipeline state
    encounter_data = encounters.get_whiteboard_data(location)

    return render(request, 'emr/whiteboard.html', {
        'location': location,
        'locations': locations,
        'needs_location': False,
        'pipeline_states': Encounter.PIPELINE_STATES,
        'encounters_by_state': encounter_data,
    })


@login_required
@staff_required
@require_POST
def select_location(request):
    """Set selected location in session."""
    location_id = request.POST.get('location_id')

    if not location_id:
        return HttpResponseBadRequest("location_id required")

    try:
        location = Location.objects.get(id=location_id, is_active=True)
    except Location.DoesNotExist:
        return HttpResponseBadRequest("Invalid location")

    request.session[SESSION_LOCATION_KEY] = location.id

    # Check if HTMX request
    if request.headers.get('HX-Request'):
        return redirect('emr:whiteboard')

    return redirect('emr:whiteboard')


@login_required
@staff_required
def patient_summary(request, patient_id):
    """Patient clinical summary.

    Shows:
    - Active alerts (PatientProblem where is_alert=True)
    - Problem list grouped by status
    - Clinical timeline from ClinicalEvent
    """
    patient = get_object_or_404(PatientRecord, id=patient_id)
    location = get_selected_location(request)

    # Get alerts (is_alert=True, not resolved)
    alerts = PatientProblem.objects.filter(
        patient=patient,
        is_alert=True,
    ).exclude(status='resolved')

    # Get problems grouped by status
    problems_by_status = {}
    for status, label in PatientProblem.STATUS_CHOICES:
        problems = PatientProblem.objects.filter(
            patient=patient,
            status=status,
        ).order_by('-severity', 'name')
        if problems.exists():
            problems_by_status[label] = problems

    # Get clinical timeline
    timeline = ClinicalEvent.objects.filter(
        patient=patient,
        is_entered_in_error=False,
    ).select_related(
        'encounter', 'recorded_by', 'location'
    ).order_by('-occurred_at')[:50]

    # Get recent encounters
    recent_encounters = Encounter.objects.filter(
        patient=patient,
    ).select_related('location', 'assigned_vet').order_by('-created_at')[:10]

    return render(request, 'emr/patient_summary.html', {
        'patient': patient,
        'location': location,
        'locations': Location.objects.filter(is_active=True),
        'alerts': alerts,
        'problems_by_status': problems_by_status,
        'timeline': timeline,
        'recent_encounters': recent_encounters,
    })


@login_required
@staff_required
@require_POST
def transition_encounter(request, encounter_id):
    """Transition encounter to new pipeline state.

    Creates ClinicalEvent for audit trail.
    Returns updated encounter card partial for HTMX.
    """
    encounter = get_object_or_404(Encounter, id=encounter_id)
    new_state = request.POST.get('new_state')

    # Validate state
    valid_states = [s[0] for s in Encounter.PIPELINE_STATES]
    if new_state not in valid_states:
        return HttpResponseBadRequest("Invalid state")

    old_state = encounter.pipeline_state

    # Use service function to transition
    try:
        encounter = encounters.transition_state(
            encounter=encounter,
            new_state=new_state,
            user=request.user,
        )
    except ValueError as e:
        return HttpResponseBadRequest(str(e))

    # Check if HTMX request
    if request.headers.get('HX-Request'):
        return render(request, 'emr/partials/encounter_card.html', {
            'encounter': encounter,
        })

    return redirect('emr:whiteboard')
