"""HR views for CRUD operations and time tracking."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from apps.accounts.mixins import ModulePermissionMixin
from apps.core.middleware.dynamic_urls import get_staff_token

from .forms import DepartmentForm, EmployeeForm, PositionForm, TimeEntryForm, ShiftForm
from .models import Department, Employee, Position, TimeEntry, Shift


class StaffTokenSuccessUrlMixin:
    """Mixin to build success URLs with staff token."""

    success_path = None  # Override in subclass, e.g., 'departments/'

    def get_success_url(self):
        token = get_staff_token(self.request)
        return f'/staff-{token}/operations/hr/{self.success_path}'


class HRDashboardView(ModulePermissionMixin, TemplateView):
    """HR Dashboard with KPIs and quick links."""

    template_name = 'hr/dashboard.html'
    required_module = 'hr'
    required_action = 'view'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()

        # KPIs
        context['total_employees'] = Employee.objects.filter(status='active').count()
        context['total_departments'] = Department.objects.filter(is_active=True).count()
        context['total_positions'] = Position.objects.filter(is_active=True).count()

        # Today's shifts
        context['shifts_today'] = Shift.objects.filter(date=today).count()

        # Pending time entries (not approved)
        context['pending_approvals'] = TimeEntry.objects.filter(is_approved=False).count()

        # Employees by status
        context['employees_by_status'] = Employee.objects.values('status').annotate(
            count=Count('id')
        ).order_by('-count')

        # Employees by department
        context['employees_by_dept'] = Department.objects.filter(
            is_active=True
        ).annotate(
            employee_count=Count('employees')
        ).order_by('-employee_count')[:5]

        # Recent hires (last 30 days)
        thirty_days_ago = today - timezone.timedelta(days=30)
        context['recent_hires'] = Employee.objects.filter(
            hire_date__gte=thirty_days_ago
        ).select_related('user', 'department', 'position').order_by('-hire_date')[:5]

        # Today's schedule
        context['todays_shifts'] = Shift.objects.filter(
            date=today
        ).select_related('employee__user', 'department').order_by('start_time')[:10]

        return context


class DepartmentListView(ModulePermissionMixin, ListView):
    """List all departments."""

    model = Department
    template_name = 'hr/department_list.html'
    context_object_name = 'departments'
    required_module = 'hr'
    required_action = 'view'

    def get_queryset(self):
        return Department.objects.select_related('parent', 'manager__user')


class DepartmentCreateView(StaffTokenSuccessUrlMixin, ModulePermissionMixin, CreateView):
    """Create a new department."""

    model = Department
    form_class = DepartmentForm
    template_name = 'hr/department_form.html'
    success_path = 'departments/'
    required_module = 'hr'
    required_action = 'create'

    def form_valid(self, form):
        messages.success(self.request, _('Department created successfully.'))
        return super().form_valid(form)


class DepartmentUpdateView(StaffTokenSuccessUrlMixin, ModulePermissionMixin, UpdateView):
    """Update an existing department."""

    model = Department
    form_class = DepartmentForm
    template_name = 'hr/department_form.html'
    success_path = 'departments/'
    required_module = 'hr'
    required_action = 'edit'

    def form_valid(self, form):
        messages.success(self.request, _('Department updated successfully.'))
        return super().form_valid(form)


class DepartmentDeleteView(StaffTokenSuccessUrlMixin, ModulePermissionMixin, DeleteView):
    """Delete a department."""

    model = Department
    template_name = 'hr/department_confirm_delete.html'
    success_path = 'departments/'
    required_module = 'hr'
    required_action = 'delete'

    def form_valid(self, form):
        messages.success(self.request, _('Department deleted successfully.'))
        return super().form_valid(form)


class PositionListView(ModulePermissionMixin, ListView):
    """List all positions."""

    model = Position
    template_name = 'hr/position_list.html'
    context_object_name = 'positions'
    required_module = 'hr'
    required_action = 'view'

    def get_queryset(self):
        return Position.objects.select_related('department')


class PositionCreateView(StaffTokenSuccessUrlMixin, ModulePermissionMixin, CreateView):
    """Create a new position."""

    model = Position
    form_class = PositionForm
    template_name = 'hr/position_form.html'
    success_path = 'positions/'
    required_module = 'hr'
    required_action = 'create'

    def form_valid(self, form):
        messages.success(self.request, _('Position created successfully.'))
        return super().form_valid(form)


class PositionUpdateView(StaffTokenSuccessUrlMixin, ModulePermissionMixin, UpdateView):
    """Update an existing position."""

    model = Position
    form_class = PositionForm
    template_name = 'hr/position_form.html'
    success_path = 'positions/'
    required_module = 'hr'
    required_action = 'edit'

    def form_valid(self, form):
        messages.success(self.request, _('Position updated successfully.'))
        return super().form_valid(form)


class PositionDeleteView(StaffTokenSuccessUrlMixin, ModulePermissionMixin, DeleteView):
    """Delete a position."""

    model = Position
    template_name = 'hr/position_confirm_delete.html'
    success_path = 'positions/'
    required_module = 'hr'
    required_action = 'delete'

    def form_valid(self, form):
        messages.success(self.request, _('Position deleted successfully.'))
        return super().form_valid(form)


class EmployeeListView(ModulePermissionMixin, ListView):
    """List all employees."""

    model = Employee
    template_name = 'hr/employee_list.html'
    context_object_name = 'employees'
    required_module = 'hr'
    required_action = 'view'

    def get_queryset(self):
        return Employee.objects.select_related(
            'user', 'department', 'position', 'manager__user'
        ).filter(status='active')


class EmployeeDetailView(ModulePermissionMixin, DetailView):
    """View employee details."""

    model = Employee
    template_name = 'hr/employee_detail.html'
    context_object_name = 'employee'
    required_module = 'hr'
    required_action = 'view'

    def get_queryset(self):
        return Employee.objects.select_related(
            'user', 'department', 'position', 'manager__user'
        )


class EmployeeCreateView(StaffTokenSuccessUrlMixin, ModulePermissionMixin, CreateView):
    """Create a new employee."""

    model = Employee
    form_class = EmployeeForm
    template_name = 'hr/employee_form.html'
    success_path = 'employees/'
    required_module = 'hr'
    required_action = 'create'

    def form_valid(self, form):
        messages.success(self.request, _('Employee created successfully.'))
        return super().form_valid(form)


class EmployeeUpdateView(StaffTokenSuccessUrlMixin, ModulePermissionMixin, UpdateView):
    """Update an existing employee."""

    model = Employee
    form_class = EmployeeForm
    template_name = 'hr/employee_form.html'
    success_path = 'employees/'
    required_module = 'hr'
    required_action = 'edit'

    def form_valid(self, form):
        messages.success(self.request, _('Employee updated successfully.'))
        return super().form_valid(form)


class EmployeeDeleteView(StaffTokenSuccessUrlMixin, ModulePermissionMixin, DeleteView):
    """Delete an employee."""

    model = Employee
    template_name = 'hr/employee_confirm_delete.html'
    success_path = 'employees/'
    required_module = 'hr'
    required_action = 'delete'

    def form_valid(self, form):
        messages.success(self.request, _('Employee deleted successfully.'))
        return super().form_valid(form)


def _get_timesheet_url(request):
    """Build timesheet URL with staff token."""
    token = get_staff_token(request)
    return f'/staff-{token}/operations/hr/time/'


@login_required
def timesheet_view(request):
    """View employee timesheet with optional task filter."""
    try:
        employee = request.user.employee
    except Employee.DoesNotExist:
        messages.error(request, _('No employee record found for your account.'))
        return redirect('core:dashboard')

    # Base queryset
    entries = TimeEntry.objects.filter(employee=employee)

    # Apply task filter if specified
    task_id = request.GET.get('task')
    selected_task = None
    if task_id:
        try:
            from apps.practice.models import Task
            selected_task = Task.objects.get(pk=task_id)
            entries = entries.filter(task=selected_task)
        except (ValueError, Task.DoesNotExist):
            pass

    entries = entries.order_by('-date', '-clock_in')[:30]

    open_entry = TimeEntry.objects.filter(
        employee=employee,
        clock_out__isnull=True
    ).first()

    # Get list of tasks that have time entries for this employee
    from apps.practice.models import Task
    tasks_with_entries = Task.objects.filter(
        time_entries__employee=employee
    ).distinct().order_by('title')

    return render(request, 'hr/timesheet.html', {
        'employee': employee,
        'entries': entries,
        'open_entry': open_entry,
        'tasks_with_entries': tasks_with_entries,
        'selected_task': selected_task,
    })


@login_required
def clock_in_view(request):
    """Clock in for the current employee, optionally for a specific task."""
    timesheet_url = _get_timesheet_url(request)

    if request.method != 'POST':
        return redirect(timesheet_url)

    try:
        employee = request.user.employee
    except Employee.DoesNotExist:
        messages.error(request, _('No employee record found for your account.'))
        return redirect('core:dashboard')

    open_entry = TimeEntry.objects.filter(
        employee=employee,
        clock_out__isnull=True
    ).exists()

    if open_entry:
        messages.warning(request, _('You are already clocked in.'))
        return redirect(timesheet_url)

    # Check for optional task_id
    task = None
    task_id = request.POST.get('task_id')
    if task_id:
        from apps.practice.models import Task
        try:
            task = Task.objects.get(pk=task_id)
        except Task.DoesNotExist:
            pass

    now = timezone.now()
    TimeEntry.objects.create(
        employee=employee,
        date=now.date(),
        clock_in=now,
        task=task,
    )
    if task:
        messages.success(request, _('Clocked in for task: %(task)s') % {'task': task.title})
    else:
        messages.success(request, _('Clocked in successfully.'))
    return redirect(timesheet_url)


@login_required
def clock_out_view(request):
    """Clock out for the current employee."""
    timesheet_url = _get_timesheet_url(request)

    if request.method != 'POST':
        return redirect(timesheet_url)

    try:
        employee = request.user.employee
    except Employee.DoesNotExist:
        messages.error(request, _('No employee record found for your account.'))
        return redirect('core:dashboard')

    open_entry = TimeEntry.objects.filter(
        employee=employee,
        clock_out__isnull=True
    ).first()

    if not open_entry:
        messages.warning(request, _('You are not currently clocked in.'))
        return redirect(timesheet_url)

    open_entry.clock_out = timezone.now()
    open_entry.save()
    messages.success(request, _('Clocked out successfully.'))
    return redirect(timesheet_url)


class ShiftListView(ModulePermissionMixin, ListView):
    """List all shifts (schedule view)."""

    model = Shift
    template_name = 'hr/shift_list.html'
    context_object_name = 'shifts'
    required_module = 'hr'
    required_action = 'view'

    def get_queryset(self):
        return Shift.objects.select_related(
            'employee__user', 'department'
        ).order_by('date', 'start_time')


class ShiftCreateView(StaffTokenSuccessUrlMixin, ModulePermissionMixin, CreateView):
    """Create a new shift."""

    model = Shift
    form_class = ShiftForm
    template_name = 'hr/shift_form.html'
    success_path = 'schedule/'
    required_module = 'hr'
    required_action = 'create'

    def form_valid(self, form):
        messages.success(self.request, _('Shift created successfully.'))
        return super().form_valid(form)


class ShiftUpdateView(StaffTokenSuccessUrlMixin, ModulePermissionMixin, UpdateView):
    """Update an existing shift."""

    model = Shift
    form_class = ShiftForm
    template_name = 'hr/shift_form.html'
    success_path = 'schedule/'
    required_module = 'hr'
    required_action = 'edit'

    def form_valid(self, form):
        messages.success(self.request, _('Shift updated successfully.'))
        return super().form_valid(form)


class ShiftDeleteView(StaffTokenSuccessUrlMixin, ModulePermissionMixin, DeleteView):
    """Delete a shift."""

    model = Shift
    template_name = 'hr/shift_confirm_delete.html'
    success_path = 'schedule/'
    required_module = 'hr'
    required_action = 'delete'

    def form_valid(self, form):
        messages.success(self.request, _('Shift deleted successfully.'))
        return super().form_valid(form)
