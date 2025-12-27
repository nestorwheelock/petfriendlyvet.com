"""HR views for CRUD operations and time tracking."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from apps.accounts.mixins import ModulePermissionMixin

from .forms import DepartmentForm, EmployeeForm, PositionForm, TimeEntryForm, ShiftForm
from .models import Department, Employee, Position, TimeEntry, Shift


class DepartmentListView(ModulePermissionMixin, ListView):
    """List all departments."""

    model = Department
    template_name = 'hr/department_list.html'
    context_object_name = 'departments'
    required_module = 'hr'
    required_action = 'view'

    def get_queryset(self):
        return Department.objects.select_related('parent', 'manager__user')


class DepartmentCreateView(ModulePermissionMixin, CreateView):
    """Create a new department."""

    model = Department
    form_class = DepartmentForm
    template_name = 'hr/department_form.html'
    success_url = reverse_lazy('hr:department_list')
    required_module = 'hr'
    required_action = 'create'

    def form_valid(self, form):
        messages.success(self.request, _('Department created successfully.'))
        return super().form_valid(form)


class DepartmentUpdateView(ModulePermissionMixin, UpdateView):
    """Update an existing department."""

    model = Department
    form_class = DepartmentForm
    template_name = 'hr/department_form.html'
    success_url = reverse_lazy('hr:department_list')
    required_module = 'hr'
    required_action = 'edit'

    def form_valid(self, form):
        messages.success(self.request, _('Department updated successfully.'))
        return super().form_valid(form)


class DepartmentDeleteView(ModulePermissionMixin, DeleteView):
    """Delete a department."""

    model = Department
    template_name = 'hr/department_confirm_delete.html'
    success_url = reverse_lazy('hr:department_list')
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


class PositionCreateView(ModulePermissionMixin, CreateView):
    """Create a new position."""

    model = Position
    form_class = PositionForm
    template_name = 'hr/position_form.html'
    success_url = reverse_lazy('hr:position_list')
    required_module = 'hr'
    required_action = 'create'

    def form_valid(self, form):
        messages.success(self.request, _('Position created successfully.'))
        return super().form_valid(form)


class PositionUpdateView(ModulePermissionMixin, UpdateView):
    """Update an existing position."""

    model = Position
    form_class = PositionForm
    template_name = 'hr/position_form.html'
    success_url = reverse_lazy('hr:position_list')
    required_module = 'hr'
    required_action = 'edit'

    def form_valid(self, form):
        messages.success(self.request, _('Position updated successfully.'))
        return super().form_valid(form)


class PositionDeleteView(ModulePermissionMixin, DeleteView):
    """Delete a position."""

    model = Position
    template_name = 'hr/position_confirm_delete.html'
    success_url = reverse_lazy('hr:position_list')
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


class EmployeeCreateView(ModulePermissionMixin, CreateView):
    """Create a new employee."""

    model = Employee
    form_class = EmployeeForm
    template_name = 'hr/employee_form.html'
    success_url = reverse_lazy('hr:employee_list')
    required_module = 'hr'
    required_action = 'create'

    def form_valid(self, form):
        messages.success(self.request, _('Employee created successfully.'))
        return super().form_valid(form)


class EmployeeUpdateView(ModulePermissionMixin, UpdateView):
    """Update an existing employee."""

    model = Employee
    form_class = EmployeeForm
    template_name = 'hr/employee_form.html'
    success_url = reverse_lazy('hr:employee_list')
    required_module = 'hr'
    required_action = 'edit'

    def form_valid(self, form):
        messages.success(self.request, _('Employee updated successfully.'))
        return super().form_valid(form)


class EmployeeDeleteView(ModulePermissionMixin, DeleteView):
    """Delete an employee."""

    model = Employee
    template_name = 'hr/employee_confirm_delete.html'
    success_url = reverse_lazy('hr:employee_list')
    required_module = 'hr'
    required_action = 'delete'

    def form_valid(self, form):
        messages.success(self.request, _('Employee deleted successfully.'))
        return super().form_valid(form)


@login_required
def timesheet_view(request):
    """View employee timesheet."""
    try:
        employee = request.user.employee
    except Employee.DoesNotExist:
        messages.error(request, _('No employee record found for your account.'))
        return redirect('core:dashboard')

    entries = TimeEntry.objects.filter(employee=employee).order_by('-date', '-clock_in')[:30]
    open_entry = TimeEntry.objects.filter(
        employee=employee,
        clock_out__isnull=True
    ).first()

    return render(request, 'hr/timesheet.html', {
        'employee': employee,
        'entries': entries,
        'open_entry': open_entry,
    })


@login_required
def clock_in_view(request):
    """Clock in for the current employee."""
    if request.method != 'POST':
        return redirect('hr:timesheet')

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
        return redirect('hr:timesheet')

    now = timezone.now()
    TimeEntry.objects.create(
        employee=employee,
        date=now.date(),
        clock_in=now,
    )
    messages.success(request, _('Clocked in successfully.'))
    return redirect('hr:timesheet')


@login_required
def clock_out_view(request):
    """Clock out for the current employee."""
    if request.method != 'POST':
        return redirect('hr:timesheet')

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
        return redirect('hr:timesheet')

    open_entry.clock_out = timezone.now()
    open_entry.save()
    messages.success(request, _('Clocked out successfully.'))
    return redirect('hr:timesheet')


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


class ShiftCreateView(ModulePermissionMixin, CreateView):
    """Create a new shift."""

    model = Shift
    form_class = ShiftForm
    template_name = 'hr/shift_form.html'
    success_url = reverse_lazy('hr:shift_list')
    required_module = 'hr'
    required_action = 'create'

    def form_valid(self, form):
        messages.success(self.request, _('Shift created successfully.'))
        return super().form_valid(form)


class ShiftUpdateView(ModulePermissionMixin, UpdateView):
    """Update an existing shift."""

    model = Shift
    form_class = ShiftForm
    template_name = 'hr/shift_form.html'
    success_url = reverse_lazy('hr:shift_list')
    required_module = 'hr'
    required_action = 'edit'

    def form_valid(self, form):
        messages.success(self.request, _('Shift updated successfully.'))
        return super().form_valid(form)


class ShiftDeleteView(ModulePermissionMixin, DeleteView):
    """Delete a shift."""

    model = Shift
    template_name = 'hr/shift_confirm_delete.html'
    success_url = reverse_lazy('hr:shift_list')
    required_module = 'hr'
    required_action = 'delete'

    def form_valid(self, form):
        messages.success(self.request, _('Shift deleted successfully.'))
        return super().form_valid(form)
