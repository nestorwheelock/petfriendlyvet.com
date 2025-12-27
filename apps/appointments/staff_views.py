"""Staff views for appointment management."""
import calendar
from collections import defaultdict
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from apps.accounts.decorators import require_permission
from apps.emr.models import Encounter
from apps.emr.services import encounters as encounter_service
from apps.locations.models import Location

from .forms import StaffAppointmentForm
from .models import Appointment, ServiceType


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
@require_permission('appointments', 'view')
def staff_list(request):
    """Staff appointment list with multiple view modes."""
    from datetime import date, datetime

    today = timezone.now().date()
    view_mode = request.GET.get('view', 'day')  # day, week, month
    date_str = request.GET.get('date', str(today))
    status_filter = request.GET.get('status', '')
    location_filter = request.GET.get('location', '')  # Location filter

    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = today

    # Get locations for filters and check-in
    locations = Location.objects.filter(is_active=True)

    # Parse location filter
    selected_location = None
    if location_filter:
        try:
            selected_location = Location.objects.get(id=int(location_filter), is_active=True)
        except (ValueError, Location.DoesNotExist):
            pass

    context = {
        'view_mode': view_mode,
        'selected_date': selected_date,
        'status_filter': status_filter,
        'location_filter': location_filter,
        'selected_location': selected_location,
        'today': today,
        'locations': locations,
    }

    if view_mode == 'month':
        # Monthly calendar view
        context.update(_get_month_view_context(selected_date, status_filter, selected_location))
        return render(request, 'appointments/staff_calendar.html', context)

    elif view_mode == 'week':
        # Weekly view
        context.update(_get_week_view_context(selected_date, status_filter, selected_location))
        return render(request, 'appointments/staff_week.html', context)

    else:
        # Daily view (default)
        context.update(_get_day_view_context(selected_date, status_filter, selected_location))
        return render(request, 'appointments/staff_day.html', context)


def _get_day_view_context(selected_date, status_filter, location=None):
    """Get context for daily view."""
    appointments = Appointment.objects.filter(
        scheduled_start__date=selected_date
    ).select_related(
        'owner', 'pet', 'service', 'veterinarian', 'location'
    ).order_by('scheduled_start')

    if status_filter:
        appointments = appointments.filter(status=status_filter)

    if location:
        appointments = appointments.filter(location=location)

    # Get encounters in one query
    apt_list = list(appointments)
    apt_ids = [apt.id for apt in apt_list]
    encounters_by_apt = {
        enc.appointment_id: enc
        for enc in Encounter.objects.filter(appointment_id__in=apt_ids)
    }

    # Group by hour for timeline display
    hours = defaultdict(list)
    for apt in apt_list:
        hour = apt.scheduled_start.hour
        hours[hour].append({
            'appointment': apt,
            'encounter': encounters_by_apt.get(apt.id),
        })

    # Create time slots from 7am to 8pm
    time_slots = []
    for hour in range(7, 21):
        time_slots.append({
            'hour': hour,
            'label': f'{hour:02d}:00',
            'appointments': hours.get(hour, []),
        })

    return {
        'time_slots': time_slots,
        'appointments_data': [
            {'appointment': apt, 'encounter': encounters_by_apt.get(apt.id)}
            for apt in apt_list
        ],
        'total_count': len(apt_list),
    }


def _get_week_view_context(selected_date, status_filter, location=None):
    """Get context for weekly view."""
    # Get start of week (Monday)
    start_of_week = selected_date - timedelta(days=selected_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    appointments = Appointment.objects.filter(
        scheduled_start__date__gte=start_of_week,
        scheduled_start__date__lte=end_of_week,
    ).select_related(
        'owner', 'pet', 'service', 'veterinarian', 'location'
    ).order_by('scheduled_start')

    if status_filter:
        appointments = appointments.filter(status=status_filter)

    if location:
        appointments = appointments.filter(location=location)

    apt_list = list(appointments)
    apt_ids = [apt.id for apt in apt_list]
    encounters_by_apt = {
        enc.appointment_id: enc
        for enc in Encounter.objects.filter(appointment_id__in=apt_ids)
    }

    # Group by day
    days = []
    for i in range(7):
        day_date = start_of_week + timedelta(days=i)
        day_apts = [
            {'appointment': apt, 'encounter': encounters_by_apt.get(apt.id)}
            for apt in apt_list
            if apt.scheduled_start.date() == day_date
        ]
        days.append({
            'date': day_date,
            'day_name': day_date.strftime('%A'),
            'is_today': day_date == timezone.now().date(),
            'appointments': day_apts,
            'count': len(day_apts),
        })

    return {
        'week_days': days,
        'start_of_week': start_of_week,
        'end_of_week': end_of_week,
        'total_count': len(apt_list),
    }


def _get_month_view_context(selected_date, status_filter, location=None):
    """Get context for monthly calendar view."""
    year = selected_date.year
    month = selected_date.month

    # Get first and last day of month
    first_day = selected_date.replace(day=1)
    if month == 12:
        last_day = selected_date.replace(year=year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last_day = selected_date.replace(month=month + 1, day=1) - timedelta(days=1)

    # Get appointments for the month
    appointments = Appointment.objects.filter(
        scheduled_start__date__gte=first_day,
        scheduled_start__date__lte=last_day,
    ).select_related('pet', 'service', 'location')

    if status_filter:
        appointments = appointments.filter(status=status_filter)

    if location:
        appointments = appointments.filter(location=location)

    # Count by date
    apt_by_date = defaultdict(list)
    for apt in appointments:
        apt_by_date[apt.scheduled_start.date()].append(apt)

    # Build calendar weeks
    cal = calendar.Calendar(firstweekday=0)  # Monday first
    weeks = []
    for week in cal.monthdatescalendar(year, month):
        week_data = []
        for day in week:
            day_apts = apt_by_date.get(day, [])
            week_data.append({
                'date': day,
                'in_month': day.month == month,
                'is_today': day == timezone.now().date(),
                'count': len(day_apts),
                'appointments': day_apts[:3],  # First 3 for preview
                'has_more': len(day_apts) > 3,
            })
        weeks.append(week_data)

    # Previous/next month
    if month == 1:
        prev_month = selected_date.replace(year=year - 1, month=12, day=1)
    else:
        prev_month = selected_date.replace(month=month - 1, day=1)

    if month == 12:
        next_month = selected_date.replace(year=year + 1, month=1, day=1)
    else:
        next_month = selected_date.replace(month=month + 1, day=1)

    return {
        'calendar_weeks': weeks,
        'month_name': selected_date.strftime('%B %Y'),
        'prev_month': prev_month,
        'next_month': next_month,
        'total_count': len(list(appointments)),
    }


@login_required
@require_permission('appointments', 'view')
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
@require_permission('appointments', 'edit')
def staff_edit(request, pk):
    """Edit an existing appointment."""
    appointment = get_object_or_404(Appointment, pk=pk)

    if request.method == 'POST':
        form = StaffAppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            messages.success(request, _('Appointment updated successfully.'))
            return staff_redirect(request, f'operations/appointments/{pk}/')
    else:
        form = StaffAppointmentForm(instance=appointment)

    return render(request, 'appointments/staff_form.html', {
        'form': form,
        'appointment': appointment,
        'is_edit': True,
    })


@login_required
@require_permission('appointments', 'create')
def staff_create(request):
    """Create a new appointment."""
    if request.method == 'POST':
        form = StaffAppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save()
            messages.success(request, _('Appointment created successfully.'))
            return staff_redirect(request, f'operations/appointments/{appointment.pk}/')
    else:
        form = StaffAppointmentForm()

    return render(request, 'appointments/staff_form.html', {
        'form': form,
        'is_edit': False,
    })


@login_required
@require_permission('emr', 'create')
@require_POST
def check_in(request, pk):
    """Check in appointment and create encounter.

    Uses EMR service function which is idempotent - if encounter already
    exists, returns existing one.
    """
    appointment = get_object_or_404(Appointment, pk=pk)

    # Get location - from appointment, POST, session, or auto-default if only one
    location = appointment.location
    if not location:
        location_id = request.POST.get('location_id')
        if not location_id:
            location_id = request.session.get('emr_selected_location_id')

        if not location_id:
            # Auto-default if only one active location exists
            active_locations = Location.objects.filter(is_active=True)
            if active_locations.count() == 1:
                location = active_locations.first()
            else:
                return HttpResponseBadRequest("Location required for check-in")
        else:
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

    # Set session location to encounter's location for whiteboard
    request.session['emr_selected_location_id'] = encounter.location.id

    # Redirect to whiteboard
    return staff_redirect(request, 'operations/clinical/')


@login_required
@require_permission('appointments', 'edit')
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
@require_permission('appointments', 'edit')
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


@login_required
@require_permission('appointments', 'edit')
@require_POST
def bulk_action(request):
    """Handle bulk actions on multiple appointments."""
    action = request.POST.get('action')
    appointment_ids = request.POST.getlist('appointment_ids')

    if not action or not appointment_ids:
        return HttpResponseBadRequest("Action and appointments required")

    appointments = Appointment.objects.filter(id__in=appointment_ids)
    count = 0

    if action == 'check_in':
        # Bulk check-in
        location = None
        location_id = request.POST.get('location_id') or request.session.get('emr_selected_location_id')

        if location_id:
            try:
                location = Location.objects.get(id=location_id, is_active=True)
            except Location.DoesNotExist:
                pass

        if not location:
            active_locations = Location.objects.filter(is_active=True)
            if active_locations.count() == 1:
                location = active_locations.first()
            else:
                return HttpResponseBadRequest("Location required for bulk check-in")

        for apt in appointments.filter(status__in=['scheduled', 'confirmed']):
            try:
                encounter_service.check_in_appointment(
                    appointment=apt,
                    location=apt.location or location,
                    user=request.user,
                )
                count += 1
            except ValueError:
                continue

        if location:
            request.session['emr_selected_location_id'] = location.id

    elif action == 'no_show':
        for apt in appointments.exclude(status__in=['completed', 'cancelled']):
            apt.status = 'no_show'
            apt.save(update_fields=['status', 'updated_at'])
            count += 1

    elif action == 'confirm':
        for apt in appointments.filter(status='scheduled'):
            apt.status = 'confirmed'
            apt.save(update_fields=['status', 'updated_at'])
            count += 1

    elif action == 'cancel':
        for apt in appointments.exclude(status__in=['completed', 'no_show']):
            apt.status = 'cancelled'
            apt.save(update_fields=['status', 'updated_at'])
            count += 1

    return staff_redirect(request, 'operations/appointments/')
