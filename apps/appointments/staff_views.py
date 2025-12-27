"""Staff views for appointment management."""
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.emr.models import Encounter
from apps.emr.services import encounters as encounter_service
from apps.locations.models import Location

from .models import Appointment


def staff_required(view_func):
    """Decorator requiring staff access."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Staff access required")
        return view_func(request, *args, **kwargs)
    return wrapper


def staff_redirect(request, path):
    """Redirect with staff token."""
    staff_token = request.session.get('staff_token', '')
    return HttpResponseRedirect(f'/staff-{staff_token}/{path}')


@login_required
@staff_required
def staff_list(request):
    """Staff appointment list - today's appointments by default."""
    today = timezone.now().date()
    date_filter = request.GET.get('date', str(today))
    status_filter = request.GET.get('status', '')

    appointments = Appointment.objects.filter(
        scheduled_start__date=date_filter
    ).select_related(
        'owner', 'pet', 'service', 'veterinarian', 'location'
    ).prefetch_related(
        'encounter_set'  # Get linked encounters
    ).order_by('scheduled_start')

    if status_filter:
        appointments = appointments.filter(status=status_filter)

    # Annotate with encounter info
    appointments_with_encounters = []
    for apt in appointments:
        encounter = Encounter.objects.filter(appointment=apt).first()
        appointments_with_encounters.append({
            'appointment': apt,
            'encounter': encounter,
        })

    # Get locations for check-in
    locations = Location.objects.filter(is_active=True)

    return render(request, 'appointments/staff_list.html', {
        'appointments_data': appointments_with_encounters,
        'date_filter': date_filter,
        'status_filter': status_filter,
        'today': today,
        'locations': locations,
    })


@login_required
@staff_required
def staff_detail(request, pk):
    """Staff appointment detail view."""
    appointment = get_object_or_404(
        Appointment.objects.select_related('owner', 'pet', 'service', 'veterinarian', 'location'),
        pk=pk
    )

    # Check if encounter already exists for this appointment
    encounter = Encounter.objects.filter(appointment=appointment).first()

    locations = Location.objects.filter(is_active=True)

    return render(request, 'appointments/staff_detail.html', {
        'appointment': appointment,
        'encounter': encounter,
        'locations': locations,
    })


@login_required
@staff_required
@require_POST
def check_in(request, pk):
    """Check in appointment and create encounter.

    Uses EMR service function which is idempotent - if encounter already
    exists, returns existing one.
    """
    appointment = get_object_or_404(Appointment, pk=pk)

    # Get location - from appointment, POST, or session
    location = appointment.location
    if not location:
        location_id = request.POST.get('location_id')
        if not location_id:
            location_id = request.session.get('emr_selected_location_id')

        if not location_id:
            return HttpResponseBadRequest("Location required for check-in")

        try:
            location = Location.objects.get(id=location_id, is_active=True)
        except Location.DoesNotExist:
            return HttpResponseBadRequest("Invalid location")

    # Use service function (idempotent)
    try:
        encounter, created = encounter_service.check_in_appointment(
            appointment=appointment,
            location=location,
            user=request.user,
        )
    except ValueError as e:
        return HttpResponseBadRequest(str(e))

    # Redirect to whiteboard
    return staff_redirect(request, 'operations/clinical/')


@login_required
@staff_required
@require_POST
def mark_no_show(request, pk):
    """Mark appointment as no-show."""
    appointment = get_object_or_404(Appointment, pk=pk)

    if appointment.status in ('completed', 'cancelled'):
        return HttpResponseBadRequest("Cannot mark as no-show")

    appointment.status = 'no_show'
    appointment.save(update_fields=['status', 'updated_at'])

    return staff_redirect(request, 'operations/appointments/')


@login_required
@staff_required
@require_POST
def mark_complete(request, pk):
    """Mark appointment as complete."""
    appointment = get_object_or_404(Appointment, pk=pk)

    if appointment.status == 'cancelled':
        return HttpResponseBadRequest("Cannot complete cancelled appointment")

    appointment.status = 'completed'
    appointment.completed_at = timezone.now()
    appointment.save(update_fields=['status', 'completed_at', 'updated_at'])

    return staff_redirect(request, 'operations/appointments/')
