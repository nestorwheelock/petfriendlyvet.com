"""Practice management views."""
from datetime import date, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render, get_object_or_404, redirect

from apps.accounts.decorators import require_permission
from apps.billing.models import SATProductCode, SATUnitCode
from apps.core.utils import staff_redirect
from apps.inventory.models import InventoryItem
from django.utils import timezone

from .forms import StaffCreateForm, StaffEditForm, ShiftForm, TaskForm, TimeEntryForm
from .models import (
    StaffProfile, Shift, TimeEntry, Task, ClinicSettings,
    ProcedureCategory, VetProcedure, ProcedureConsumable
)


@login_required
@require_permission('practice', 'view')
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


@login_required
@require_permission('practice', 'view')
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


@login_required
@require_permission('practice', 'view')
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


@login_required
@require_permission('practice', 'manage')
def staff_create(request):
    """Create a new staff member (User + StaffProfile)."""
    if request.method == 'POST':
        form = StaffCreateForm(request.POST)
        if form.is_valid():
            profile = form.save()
            messages.success(
                request,
                f'Staff member "{profile.user.get_full_name()}" created successfully.'
            )
            return staff_redirect(request, 'practice:staff_list')
    else:
        form = StaffCreateForm()

    context = {
        'form': form,
        'title': 'Add Staff Member',
    }
    return render(request, 'practice/staff_form.html', context)


@login_required
@require_permission('practice', 'manage')
def staff_edit(request, pk):
    """Edit an existing staff member's profile."""
    staff = get_object_or_404(StaffProfile.objects.select_related('user'), pk=pk)

    if request.method == 'POST':
        form = StaffEditForm(request.POST, instance=staff)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Staff member "{staff.user.get_full_name()}" updated successfully.'
            )
            return staff_redirect(request, 'practice:staff_list')
    else:
        form = StaffEditForm(instance=staff)

    context = {
        'form': form,
        'staff': staff,
        'title': f'Edit {staff.user.get_full_name()}',
        'editing': True,
    }
    return render(request, 'practice/staff_form.html', context)


@login_required
@require_permission('practice', 'manage')
def staff_deactivate(request, pk):
    """Deactivate a staff member (soft delete)."""
    staff = get_object_or_404(StaffProfile.objects.select_related('user'), pk=pk)

    if request.method == 'POST':
        staff.is_active = False
        staff.user.is_active = False
        staff.save()
        staff.user.save()
        messages.success(
            request,
            f'Staff member "{staff.user.get_full_name()}" has been deactivated.'
        )
        return staff_redirect(request, 'practice:staff_list')

    context = {
        'staff': staff,
    }
    return render(request, 'practice/staff_confirm_deactivate.html', context)


@login_required
@require_permission('practice', 'view')
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


@login_required
@require_permission('practice', 'view')
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


@login_required
@require_permission('practice', 'view')
def shift_detail(request, pk):
    """View shift details."""
    shift = get_object_or_404(
        Shift.objects.select_related('staff', 'staff__user'),
        pk=pk
    )
    time_entries = TimeEntry.objects.filter(shift=shift).select_related('staff', 'staff__user').order_by('clock_in')

    context = {
        'shift': shift,
        'time_entries': time_entries,
    }
    return render(request, 'practice/shift_detail.html', context)


@login_required
@require_permission('practice', 'view')
def shift_create(request):
    """Create a new shift."""
    if request.method == 'POST':
        form = ShiftForm(request.POST)
        if form.is_valid():
            shift = form.save()
            messages.success(request, f'Shift for {shift.staff.user.get_full_name()} created successfully.')
            return staff_redirect(request, 'practice:shift_list')
    else:
        form = ShiftForm()

    staff_profiles = StaffProfile.objects.filter(is_active=True).select_related('user').order_by('user__first_name')

    context = {
        'form': form,
        'staff_profiles': staff_profiles,
        'title': 'Add Shift',
    }
    return render(request, 'practice/shift_form.html', context)


@login_required
@require_permission('practice', 'view')
def shift_edit(request, pk):
    """Edit an existing shift."""
    shift = get_object_or_404(Shift.objects.select_related('staff', 'staff__user'), pk=pk)

    if request.method == 'POST':
        form = ShiftForm(request.POST, instance=shift)
        if form.is_valid():
            form.save()
            messages.success(request, f'Shift for {shift.staff.user.get_full_name()} updated successfully.')
            return staff_redirect(request, 'practice:shift_list')
    else:
        form = ShiftForm(instance=shift)

    staff_profiles = StaffProfile.objects.filter(is_active=True).select_related('user').order_by('user__first_name')

    context = {
        'form': form,
        'shift': shift,
        'staff_profiles': staff_profiles,
        'title': f'Edit Shift - {shift.date}',
        'editing': True,
    }
    return render(request, 'practice/shift_form.html', context)


@login_required
@require_permission('practice', 'view')
def shift_delete(request, pk):
    """Delete a shift."""
    shift = get_object_or_404(Shift.objects.select_related('staff', 'staff__user'), pk=pk)

    if request.method == 'POST':
        staff_name = shift.staff.user.get_full_name()
        shift_date = shift.date
        shift.delete()
        messages.success(request, f'Shift for {staff_name} on {shift_date} deleted successfully.')
        return staff_redirect(request, 'practice:shift_list')

    context = {
        'shift': shift,
    }
    return render(request, 'practice/shift_confirm_delete.html', context)


@login_required
@require_permission('practice', 'view')
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


@login_required
@require_permission('practice', 'view')
def clock_in(request):
    """Clock in for current user."""
    if request.method == 'POST':
        # Get or create staff profile for current user
        try:
            staff = request.user.staff_profile
        except StaffProfile.DoesNotExist:
            messages.error(request, 'You do not have a staff profile.')
            return staff_redirect(request, 'practice:time_tracking')

        # Check if already clocked in
        open_entry = TimeEntry.objects.filter(staff=staff, clock_out__isnull=True).first()
        if open_entry:
            messages.warning(request, 'You are already clocked in.')
            return staff_redirect(request, 'practice:time_tracking')

        # Create new time entry
        TimeEntry.objects.create(
            staff=staff,
            clock_in=timezone.now(),
        )
        messages.success(request, 'Clocked in successfully.')
        return staff_redirect(request, 'practice:time_tracking')

    return render(request, 'practice/clock_in.html')


@login_required
@require_permission('practice', 'view')
def clock_out(request):
    """Clock out for current user."""
    if request.method == 'POST':
        try:
            staff = request.user.staff_profile
        except StaffProfile.DoesNotExist:
            messages.error(request, 'You do not have a staff profile.')
            return staff_redirect(request, 'practice:time_tracking')

        # Find open time entry
        open_entry = TimeEntry.objects.filter(staff=staff, clock_out__isnull=True).first()
        if not open_entry:
            messages.warning(request, 'You are not clocked in.')
            return staff_redirect(request, 'practice:time_tracking')

        # Clock out
        open_entry.clock_out = timezone.now()
        open_entry.save()
        messages.success(request, 'Clocked out successfully.')
        return staff_redirect(request, 'practice:time_tracking')

    return render(request, 'practice/clock_out.html')


@login_required
@require_permission('practice', 'view')
def time_entry_edit(request, pk):
    """Edit a time entry."""
    entry = get_object_or_404(TimeEntry.objects.select_related('staff', 'staff__user'), pk=pk)

    if request.method == 'POST':
        form = TimeEntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            messages.success(request, 'Time entry updated successfully.')
            return staff_redirect(request, 'practice:time_tracking')
    else:
        form = TimeEntryForm(instance=entry)

    context = {
        'form': form,
        'entry': entry,
        'title': 'Edit Time Entry',
    }
    return render(request, 'practice/time_entry_form.html', context)


@login_required
@require_permission('practice', 'view')
def time_entry_approve(request, pk):
    """Approve a time entry."""
    entry = get_object_or_404(TimeEntry.objects.select_related('staff'), pk=pk)

    if request.method == 'POST':
        entry.is_approved = True
        entry.approved_by = request.user
        entry.save()
        messages.success(request, f'Time entry for {entry.staff.user.get_full_name()} approved.')
        return staff_redirect(request, 'practice:time_tracking')

    context = {
        'entry': entry,
    }
    return render(request, 'practice/time_entry_confirm_approve.html', context)


@login_required
@require_permission('practice', 'view')
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


@login_required
@require_permission('practice', 'view')
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

    # Add time tracking context if user has an Employee record
    try:
        from apps.hr.models import TimeEntry as HRTimeEntry
        employee = request.user.employee

        # Check for open time entry (for this task or any)
        open_entry = HRTimeEntry.objects.filter(
            employee=employee,
            clock_out__isnull=True
        ).first()
        context['open_entry'] = open_entry
        context['is_clocked_in_for_task'] = open_entry and open_entry.task_id == task.pk

        # Get time entries for this task
        task_entries = HRTimeEntry.objects.filter(
            task=task
        ).select_related('employee__user').order_by('-date', '-clock_in')[:10]
        context['task_time_entries'] = task_entries

        # Calculate total hours for this task
        from decimal import Decimal
        total_hours = sum(
            e.hours_worked for e in task.time_entries.filter(clock_out__isnull=False)
        )
        context['task_total_hours'] = total_hours
        context['has_employee'] = True
    except Exception:
        context['has_employee'] = False

    return render(request, 'practice/task_detail.html', context)


@login_required
@require_permission('practice', 'view')
def task_create(request):
    """Create a new task."""
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            messages.success(request, f'Task "{task.title}" created successfully.')
            return staff_redirect(request, 'practice:task_list')
    else:
        form = TaskForm()

    staff_profiles = StaffProfile.objects.filter(is_active=True).select_related('user').order_by('user__first_name')

    context = {
        'form': form,
        'staff_profiles': staff_profiles,
        'title': 'Add Task',
    }
    return render(request, 'practice/task_form.html', context)


@login_required
@require_permission('practice', 'view')
def task_edit(request, pk):
    """Edit an existing task."""
    task = get_object_or_404(Task.objects.select_related('assigned_to', 'created_by'), pk=pk)

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, f'Task "{task.title}" updated successfully.')
            return staff_redirect(request, 'practice:task_list')
    else:
        form = TaskForm(instance=task)

    staff_profiles = StaffProfile.objects.filter(is_active=True).select_related('user').order_by('user__first_name')

    context = {
        'form': form,
        'task': task,
        'staff_profiles': staff_profiles,
        'title': f'Edit Task',
        'editing': True,
    }
    return render(request, 'practice/task_form.html', context)


@login_required
@require_permission('practice', 'view')
def task_delete(request, pk):
    """Delete a task."""
    task = get_object_or_404(Task, pk=pk)

    if request.method == 'POST':
        title = task.title
        task.delete()
        messages.success(request, f'Task "{title}" deleted successfully.')
        return staff_redirect(request, 'practice:task_list')

    context = {
        'task': task,
    }
    return render(request, 'practice/task_confirm_delete.html', context)


@login_required
@require_permission('practice', 'view')
def clinic_settings(request):
    """View clinic settings."""
    settings = ClinicSettings.objects.first()

    context = {
        'settings': settings,
    }
    return render(request, 'practice/clinic_settings.html', context)


# ============================================
# Procedure Category Views
# ============================================

@login_required
@require_permission('practice', 'view')
def category_list(request):
    """List all procedure categories."""
    categories = ProcedureCategory.objects.annotate(
        procedure_count=Count('procedures')
    ).order_by('sort_order', 'name')

    context = {
        'categories': categories,
    }
    return render(request, 'practice/category_list.html', context)


@login_required
@require_permission('practice', 'edit')
def category_create(request):
    """Create a new procedure category."""
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().lower().replace(' ', '-')
        name = request.POST.get('name', '').strip()
        name_es = request.POST.get('name_es', '').strip()
        description = request.POST.get('description', '').strip()
        icon = request.POST.get('icon', '').strip()
        sort_order = int(request.POST.get('sort_order', 0))

        if not code or not name:
            messages.error(request, 'Code and name are required.')
            return staff_redirect(request, 'practice:category_create')

        if ProcedureCategory.objects.filter(code=code).exists():
            messages.error(request, f'Category with code "{code}" already exists.')
            return staff_redirect(request, 'practice:category_create')

        ProcedureCategory.objects.create(
            code=code,
            name=name,
            name_es=name_es or name,
            description=description,
            icon=icon,
            sort_order=sort_order,
        )
        messages.success(request, f'Category "{name}" created successfully.')
        return staff_redirect(request, 'practice:category_list')

    context = {
        'max_sort_order': ProcedureCategory.objects.count(),
    }
    return render(request, 'practice/category_form.html', context)


@login_required
@require_permission('practice', 'edit')
def category_edit(request, pk):
    """Edit a procedure category."""
    category = get_object_or_404(ProcedureCategory, pk=pk)

    if request.method == 'POST':
        category.code = request.POST.get('code', '').strip().lower().replace(' ', '-')
        category.name = request.POST.get('name', '').strip()
        category.name_es = request.POST.get('name_es', '').strip()
        category.description = request.POST.get('description', '').strip()
        category.icon = request.POST.get('icon', '').strip()
        category.sort_order = int(request.POST.get('sort_order', 0))
        category.is_active = request.POST.get('is_active') == 'on'

        if not category.code or not category.name:
            messages.error(request, 'Code and name are required.')
            return staff_redirect(request, 'practice:category_edit', pk=pk)

        category.save()
        messages.success(request, f'Category "{category.name}" updated successfully.')
        return staff_redirect(request, 'practice:category_list')

    context = {
        'category': category,
        'editing': True,
    }
    return render(request, 'practice/category_form.html', context)


@login_required
@require_permission('practice', 'edit')
def category_delete(request, pk):
    """Delete a procedure category."""
    category = get_object_or_404(ProcedureCategory, pk=pk)

    if request.method == 'POST':
        if category.procedures.exists():
            messages.error(
                request,
                f'Cannot delete "{category.name}" - it has {category.procedures.count()} procedures.'
            )
            return staff_redirect(request, 'practice:category_list')

        name = category.name
        category.delete()
        messages.success(request, f'Category "{name}" deleted successfully.')
        return staff_redirect(request, 'practice:category_list')

    context = {
        'category': category,
    }
    return render(request, 'practice/category_confirm_delete.html', context)


# ============================================
# VetProcedure Views
# ============================================

@login_required
@require_permission('practice', 'view')
def procedure_list(request):
    """List all veterinary procedures."""
    category_id = request.GET.get('category', '')

    procedures = VetProcedure.objects.select_related('category').order_by(
        'category__sort_order', 'name'
    )

    if category_id:
        procedures = procedures.filter(category_id=category_id)

    categories = ProcedureCategory.objects.order_by('sort_order', 'name')

    context = {
        'procedures': procedures,
        'categories': categories,
        'current_category': category_id,
    }
    return render(request, 'practice/procedure_list.html', context)


@login_required
@require_permission('practice', 'edit')
def procedure_create(request):
    """Create a new veterinary procedure."""
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper().replace(' ', '-')
        name = request.POST.get('name', '').strip()
        name_es = request.POST.get('name_es', '').strip()
        description = request.POST.get('description', '').strip()
        category_id = request.POST.get('category')
        base_price = Decimal(request.POST.get('base_price', '0') or '0')
        duration_minutes = int(request.POST.get('duration_minutes', '30') or '30')

        # Boolean fields
        requires_appointment = request.POST.get('requires_appointment') == 'on'
        requires_hospitalization = request.POST.get('requires_hospitalization') == 'on'
        requires_anesthesia = request.POST.get('requires_anesthesia') == 'on'
        requires_vet_license = request.POST.get('requires_vet_license') == 'on'
        is_visible_online = request.POST.get('is_visible_online') == 'on'

        # SAT codes
        sat_product_code_id = request.POST.get('sat_product_code') or None
        sat_unit_code_id = request.POST.get('sat_unit_code') or None

        if not code or not name or not category_id:
            messages.error(request, 'Code, name, and category are required.')
            return staff_redirect(request, 'practice:procedure_create')

        if VetProcedure.objects.filter(code=code).exists():
            messages.error(request, f'Procedure with code "{code}" already exists.')
            return staff_redirect(request, 'practice:procedure_create')

        VetProcedure.objects.create(
            code=code,
            name=name,
            name_es=name_es or name,
            description=description,
            category_id=category_id,
            base_price=base_price,
            duration_minutes=duration_minutes,
            requires_appointment=requires_appointment,
            requires_hospitalization=requires_hospitalization,
            requires_anesthesia=requires_anesthesia,
            requires_vet_license=requires_vet_license,
            is_visible_online=is_visible_online,
            sat_product_code_id=sat_product_code_id,
            sat_unit_code_id=sat_unit_code_id,
        )
        messages.success(request, f'Procedure "{name}" created successfully.')
        return staff_redirect(request, 'practice:procedure_list')

    categories = ProcedureCategory.objects.filter(is_active=True).order_by('sort_order')
    sat_product_codes = SATProductCode.objects.filter(
        code__startswith='851'  # Healthcare services
    ).order_by('code')
    sat_unit_codes = SATUnitCode.objects.all().order_by('code')

    context = {
        'categories': categories,
        'sat_product_codes': sat_product_codes,
        'sat_unit_codes': sat_unit_codes,
    }
    return render(request, 'practice/procedure_form.html', context)


@login_required
@require_permission('practice', 'edit')
def procedure_edit(request, pk):
    """Edit a veterinary procedure."""
    procedure = get_object_or_404(VetProcedure, pk=pk)

    if request.method == 'POST':
        procedure.code = request.POST.get('code', '').strip().upper().replace(' ', '-')
        procedure.name = request.POST.get('name', '').strip()
        procedure.name_es = request.POST.get('name_es', '').strip()
        procedure.description = request.POST.get('description', '').strip()
        procedure.category_id = request.POST.get('category')
        procedure.base_price = Decimal(request.POST.get('base_price', '0') or '0')
        procedure.duration_minutes = int(request.POST.get('duration_minutes', '30') or '30')

        # Boolean fields
        procedure.requires_appointment = request.POST.get('requires_appointment') == 'on'
        procedure.requires_hospitalization = request.POST.get('requires_hospitalization') == 'on'
        procedure.requires_anesthesia = request.POST.get('requires_anesthesia') == 'on'
        procedure.requires_vet_license = request.POST.get('requires_vet_license') == 'on'
        procedure.is_visible_online = request.POST.get('is_visible_online') == 'on'
        procedure.is_active = request.POST.get('is_active') == 'on'

        # SAT codes
        sat_product_code_id = request.POST.get('sat_product_code') or None
        sat_unit_code_id = request.POST.get('sat_unit_code') or None
        procedure.sat_product_code_id = sat_product_code_id
        procedure.sat_unit_code_id = sat_unit_code_id

        if not procedure.code or not procedure.name or not procedure.category_id:
            messages.error(request, 'Code, name, and category are required.')
            return staff_redirect(request, 'practice:procedure_edit', pk=pk)

        procedure.save()
        messages.success(request, f'Procedure "{procedure.name}" updated successfully.')
        return staff_redirect(request, 'practice:procedure_list')

    categories = ProcedureCategory.objects.filter(is_active=True).order_by('sort_order')
    sat_product_codes = SATProductCode.objects.filter(
        code__startswith='851'  # Healthcare services
    ).order_by('code')
    sat_unit_codes = SATUnitCode.objects.all().order_by('code')

    context = {
        'procedure': procedure,
        'categories': categories,
        'sat_product_codes': sat_product_codes,
        'sat_unit_codes': sat_unit_codes,
        'editing': True,
    }
    return render(request, 'practice/procedure_form.html', context)


@login_required
@require_permission('practice', 'edit')
def procedure_delete(request, pk):
    """Delete a veterinary procedure."""
    procedure = get_object_or_404(VetProcedure, pk=pk)

    if request.method == 'POST':
        name = procedure.name
        procedure.delete()
        messages.success(request, f'Procedure "{name}" deleted successfully.')
        return staff_redirect(request, 'practice:procedure_list')

    context = {
        'procedure': procedure,
    }
    return render(request, 'practice/procedure_confirm_delete.html', context)


# ============================================
# Qualified Providers Views
# ============================================

@login_required
@require_permission('practice', 'view')
def procedure_providers(request, pk):
    """View and manage qualified providers for a procedure."""
    procedure = get_object_or_404(VetProcedure.objects.prefetch_related('qualified_providers'), pk=pk)

    # Get all active staff profiles not already assigned
    available_providers = StaffProfile.objects.filter(
        is_active=True
    ).exclude(
        pk__in=procedure.qualified_providers.values_list('pk', flat=True)
    ).select_related('user').order_by('user__first_name', 'user__last_name')

    context = {
        'procedure': procedure,
        'qualified_providers': procedure.qualified_providers.select_related('user').order_by('user__first_name'),
        'available_providers': available_providers,
    }
    return render(request, 'practice/procedure_providers.html', context)


@login_required
@require_permission('practice', 'view')
def procedure_add_provider(request, pk):
    """Add a qualified provider to a procedure."""
    procedure = get_object_or_404(VetProcedure, pk=pk)

    if request.method == 'POST':
        staff_id = request.POST.get('staff_id')
        if staff_id:
            staff = get_object_or_404(StaffProfile, pk=staff_id)
            procedure.qualified_providers.add(staff)
            messages.success(request, f'{staff.user.get_full_name()} added as qualified provider.')

    return staff_redirect(request, 'practice:procedure_providers', pk=pk)


@login_required
@require_permission('practice', 'view')
def procedure_remove_provider(request, pk):
    """Remove a qualified provider from a procedure."""
    procedure = get_object_or_404(VetProcedure, pk=pk)

    if request.method == 'POST':
        staff_id = request.POST.get('staff_id')
        if staff_id:
            staff = get_object_or_404(StaffProfile, pk=staff_id)
            procedure.qualified_providers.remove(staff)
            messages.success(request, f'{staff.user.get_full_name()} removed from qualified providers.')

    return staff_redirect(request, 'practice:procedure_providers', pk=pk)


# ============================================
# Procedure Consumables Views
# ============================================

@login_required
@require_permission('practice', 'view')
def procedure_consumables(request, pk):
    """View and manage consumable items for a procedure."""
    procedure = get_object_or_404(VetProcedure, pk=pk)

    consumables = procedure.consumables.select_related(
        'inventory_item'
    ).order_by('inventory_item__name')

    # Calculate total consumable cost
    total_cost = sum(c.inventory_item.cost_price * c.quantity for c in consumables)

    # Available inventory items to add
    assigned_item_ids = consumables.values_list('inventory_item_id', flat=True)
    available_items = InventoryItem.objects.filter(
        item_type='consumable'
    ).exclude(
        pk__in=assigned_item_ids
    ).order_by('name')[:50]

    context = {
        'procedure': procedure,
        'consumables': consumables,
        'total_cost': total_cost,
        'available_items': available_items,
    }
    return render(request, 'practice/procedure_consumables.html', context)


@login_required
@require_permission('practice', 'view')
def procedure_add_consumable(request, pk):
    """Add a consumable item to a procedure."""
    procedure = get_object_or_404(VetProcedure, pk=pk)

    if request.method == 'POST':
        inventory_item_id = request.POST.get('inventory_item')
        quantity = request.POST.get('quantity', '1.00')
        is_required = request.POST.get('is_required') == 'on'
        notes = request.POST.get('notes', '').strip()

        if inventory_item_id:
            inventory_item = get_object_or_404(InventoryItem, pk=inventory_item_id)

            # Check if already exists
            if not procedure.consumables.filter(inventory_item=inventory_item).exists():
                ProcedureConsumable.objects.create(
                    procedure=procedure,
                    inventory_item=inventory_item,
                    quantity=Decimal(quantity),
                    is_required=is_required,
                    notes=notes,
                )
                messages.success(request, f'{inventory_item.name} added to consumables.')
            else:
                messages.warning(request, f'{inventory_item.name} is already a consumable for this procedure.')

    return staff_redirect(request, 'practice:procedure_consumables', pk=pk)


@login_required
@require_permission('practice', 'view')
def procedure_update_consumable(request, pk, consumable_pk):
    """Update a consumable item for a procedure."""
    procedure = get_object_or_404(VetProcedure, pk=pk)
    consumable = get_object_or_404(ProcedureConsumable, pk=consumable_pk, procedure=procedure)

    if request.method == 'POST':
        quantity = request.POST.get('quantity', '1.00')
        is_required = request.POST.get('is_required') == 'on'
        notes = request.POST.get('notes', '').strip()

        consumable.quantity = Decimal(quantity)
        consumable.is_required = is_required
        consumable.notes = notes
        consumable.save()

        messages.success(request, f'{consumable.inventory_item.name} updated.')

    return staff_redirect(request, 'practice:procedure_consumables', pk=pk)


@login_required
@require_permission('practice', 'view')
def procedure_remove_consumable(request, pk, consumable_pk):
    """Remove a consumable item from a procedure."""
    procedure = get_object_or_404(VetProcedure, pk=pk)
    consumable = get_object_or_404(ProcedureConsumable, pk=consumable_pk, procedure=procedure)

    if request.method == 'POST':
        item_name = consumable.inventory_item.name
        consumable.delete()
        messages.success(request, f'{item_name} removed from consumables.')

    return staff_redirect(request, 'practice:procedure_consumables', pk=pk)
