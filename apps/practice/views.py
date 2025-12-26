"""Practice management views."""
from datetime import date, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from django.shortcuts import render, get_object_or_404, redirect

from apps.billing.models import SATProductCode, SATUnitCode
from .models import (
    StaffProfile, Shift, TimeEntry, Task, ClinicSettings,
    ProcedureCategory, VetProcedure
)


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


# ============================================
# Procedure Category Views
# ============================================

@staff_member_required
def category_list(request):
    """List all procedure categories."""
    categories = ProcedureCategory.objects.annotate(
        procedure_count=Count('procedures')
    ).order_by('sort_order', 'name')

    context = {
        'categories': categories,
    }
    return render(request, 'practice/category_list.html', context)


@staff_member_required
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
            return redirect('practice:category_create')

        if ProcedureCategory.objects.filter(code=code).exists():
            messages.error(request, f'Category with code "{code}" already exists.')
            return redirect('practice:category_create')

        ProcedureCategory.objects.create(
            code=code,
            name=name,
            name_es=name_es or name,
            description=description,
            icon=icon,
            sort_order=sort_order,
        )
        messages.success(request, f'Category "{name}" created successfully.')
        return redirect('practice:category_list')

    context = {
        'max_sort_order': ProcedureCategory.objects.count(),
    }
    return render(request, 'practice/category_form.html', context)


@staff_member_required
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
            return redirect('practice:category_edit', pk=pk)

        category.save()
        messages.success(request, f'Category "{category.name}" updated successfully.')
        return redirect('practice:category_list')

    context = {
        'category': category,
        'editing': True,
    }
    return render(request, 'practice/category_form.html', context)


@staff_member_required
def category_delete(request, pk):
    """Delete a procedure category."""
    category = get_object_or_404(ProcedureCategory, pk=pk)

    if request.method == 'POST':
        if category.procedures.exists():
            messages.error(
                request,
                f'Cannot delete "{category.name}" - it has {category.procedures.count()} procedures.'
            )
            return redirect('practice:category_list')

        name = category.name
        category.delete()
        messages.success(request, f'Category "{name}" deleted successfully.')
        return redirect('practice:category_list')

    context = {
        'category': category,
    }
    return render(request, 'practice/category_confirm_delete.html', context)


# ============================================
# VetProcedure Views
# ============================================

@staff_member_required
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


@staff_member_required
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
            return redirect('practice:procedure_create')

        if VetProcedure.objects.filter(code=code).exists():
            messages.error(request, f'Procedure with code "{code}" already exists.')
            return redirect('practice:procedure_create')

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
        return redirect('practice:procedure_list')

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


@staff_member_required
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
            return redirect('practice:procedure_edit', pk=pk)

        procedure.save()
        messages.success(request, f'Procedure "{procedure.name}" updated successfully.')
        return redirect('practice:procedure_list')

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


@staff_member_required
def procedure_delete(request, pk):
    """Delete a veterinary procedure."""
    procedure = get_object_or_404(VetProcedure, pk=pk)

    if request.method == 'POST':
        name = procedure.name
        procedure.delete()
        messages.success(request, f'Procedure "{name}" deleted successfully.')
        return redirect('practice:procedure_list')

    context = {
        'procedure': procedure,
    }
    return render(request, 'practice/procedure_confirm_delete.html', context)
