"""Practice management views."""
from datetime import date, timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from django.shortcuts import render, get_object_or_404

from .models import StaffProfile, Shift, TimeEntry, Task, ClinicSettings


@staff_member_required
def dashboard(request):
    """Practice management dashboard."""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    # Summary stats
    staff_count = StaffProfile.objects.filter(is_active=True).count()
    today_shifts = Shift.objects.filter(date=today).count()

    pending_tasks = Task.objects.filter(status='pending').count()
    urgent_tasks = Task.objects.filter(
        status__in=['pending', 'in_progress'],
        priority='urgent'
    ).count()

    # Today's schedule
    today_schedule = Shift.objects.filter(date=today).select_related(
        'staff', 'staff__user'
    ).order_by('start_time')

    # Recent tasks
    recent_tasks = Task.objects.filter(
        status__in=['pending', 'in_progress']
    ).select_related('assigned_to', 'assigned_to__user').order_by(
        '-priority', 'due_date'
    )[:5]

    context = {
        'staff_count': staff_count,
        'today_shifts': today_shifts,
        'pending_tasks': pending_tasks,
        'urgent_tasks': urgent_tasks,
        'today_schedule': today_schedule,
        'recent_tasks': recent_tasks,
    }
    return render(request, 'practice/dashboard.html', context)


@staff_member_required
def staff_list(request):
    """List all staff members."""
    role = request.GET.get('role', '')

    staff = StaffProfile.objects.select_related('user').filter(is_active=True)

    if role:
        staff = staff.filter(role=role)

    staff = staff.order_by('user__first_name', 'user__last_name')

    context = {
        'staff': staff,
        'role_choices': StaffProfile.ROLE_CHOICES,
        'current_role': role,
    }
    return render(request, 'practice/staff_list.html', context)


@staff_member_required
def staff_detail(request, pk):
    """View staff member details."""
    staff = get_object_or_404(StaffProfile.objects.select_related('user'), pk=pk)

    # Recent shifts
    recent_shifts = staff.shifts.filter(
        date__gte=date.today() - timedelta(days=7)
    ).order_by('-date')[:10]

    # Recent time entries
    recent_time = staff.time_entries.select_related('shift').order_by('-clock_in')[:10]

    # Assigned tasks
    assigned_tasks = staff.assigned_tasks.filter(
        status__in=['pending', 'in_progress']
    ).order_by('-priority', 'due_date')[:5]

    context = {
        'staff': staff,
        'recent_shifts': recent_shifts,
        'recent_time': recent_time,
        'assigned_tasks': assigned_tasks,
    }
    return render(request, 'practice/staff_detail.html', context)


@staff_member_required
def schedule(request):
    """Weekly schedule view."""
    today = date.today()
    week_offset = int(request.GET.get('week', 0))

    # Calculate week range
    week_start = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    week_end = week_start + timedelta(days=6)

    # Get shifts for the week
    shifts = Shift.objects.filter(
        date__gte=week_start,
        date__lte=week_end
    ).select_related('staff', 'staff__user').order_by('date', 'start_time')

    # Group by date
    schedule_by_day = {}
    for i in range(7):
        day = week_start + timedelta(days=i)
        schedule_by_day[day] = []

    for shift in shifts:
        schedule_by_day[shift.date].append(shift)

    context = {
        'week_start': week_start,
        'week_end': week_end,
        'week_offset': week_offset,
        'schedule_by_day': schedule_by_day,
    }
    return render(request, 'practice/schedule.html', context)


@staff_member_required
def shift_list(request):
    """List shifts with filtering."""
    today = date.today()
    period = request.GET.get('period', 'upcoming')

    shifts = Shift.objects.select_related('staff', 'staff__user')

    if period == 'today':
        shifts = shifts.filter(date=today)
    elif period == 'upcoming':
        shifts = shifts.filter(date__gte=today).order_by('date', 'start_time')
    elif period == 'past':
        shifts = shifts.filter(date__lt=today).order_by('-date', '-start_time')
    else:
        shifts = shifts.order_by('-date', '-start_time')

    shifts = shifts[:50]

    context = {
        'shifts': shifts,
        'current_period': period,
    }
    return render(request, 'practice/shift_list.html', context)


@staff_member_required
def time_tracking(request):
    """View time entries."""
    period = request.GET.get('period', 'today')
    today = date.today()

    entries = TimeEntry.objects.select_related('staff', 'staff__user', 'shift')

    if period == 'today':
        entries = entries.filter(clock_in__date=today)
    elif period == 'week':
        week_start = today - timedelta(days=today.weekday())
        entries = entries.filter(clock_in__date__gte=week_start)
    elif period == 'month':
        month_start = today.replace(day=1)
        entries = entries.filter(clock_in__date__gte=month_start)

    entries = entries.order_by('-clock_in')[:50]

    context = {
        'entries': entries,
        'current_period': period,
    }
    return render(request, 'practice/time_tracking.html', context)


@staff_member_required
def task_list(request):
    """List all tasks."""
    status = request.GET.get('status', '')
    priority = request.GET.get('priority', '')

    tasks = Task.objects.select_related(
        'assigned_to', 'assigned_to__user', 'created_by'
    )

    if status:
        tasks = tasks.filter(status=status)
    if priority:
        tasks = tasks.filter(priority=priority)

    tasks = tasks.order_by('-priority', 'due_date', '-created_at')[:50]

    context = {
        'tasks': tasks,
        'status_choices': Task.STATUS_CHOICES,
        'priority_choices': Task.PRIORITY_CHOICES,
        'current_status': status,
        'current_priority': priority,
    }
    return render(request, 'practice/task_list.html', context)


@staff_member_required
def task_detail(request, pk):
    """View task details."""
    task = get_object_or_404(
        Task.objects.select_related(
            'assigned_to', 'assigned_to__user', 'created_by', 'pet', 'appointment'
        ),
        pk=pk
    )

    context = {
        'task': task,
    }
    return render(request, 'practice/task_detail.html', context)


@staff_member_required
def clinic_settings(request):
    """View clinic settings."""
    settings = ClinicSettings.objects.first()

    context = {
        'settings': settings,
    }
    return render(request, 'practice/clinic_settings.html', context)
