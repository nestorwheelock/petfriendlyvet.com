"""HR forms for CRUD operations."""
from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Department, Position, Employee, TimeEntry, Shift


class DepartmentForm(forms.ModelForm):
    """Form for creating and editing departments."""

    class Meta:
        model = Department
        fields = ['name', 'code', 'description', 'parent', 'cost_center', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': _('e.g., Clinical Services'),
            }),
            'code': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': _('e.g., clinical'),
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
                'placeholder': _('Department description...'),
            }),
            'parent': forms.Select(attrs={
                'class': 'select select-bordered w-full',
            }),
            'cost_center': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': _('e.g., CC-001'),
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['parent'].queryset = Department.objects.exclude(
                pk=self.instance.pk
            )


class PositionForm(forms.ModelForm):
    """Form for creating and editing positions."""

    class Meta:
        model = Position
        fields = [
            'title', 'code', 'description', 'department',
            'min_salary', 'max_salary', 'is_exempt', 'is_active'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': _('e.g., Veterinarian'),
            }),
            'code': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': _('e.g., vet'),
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
                'placeholder': _('Position description...'),
            }),
            'department': forms.Select(attrs={
                'class': 'select select-bordered w-full',
            }),
            'min_salary': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'step': '0.01',
                'placeholder': '0.00',
            }),
            'max_salary': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'step': '0.01',
                'placeholder': '0.00',
            }),
            'is_exempt': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary',
            }),
        }


class EmployeeForm(forms.ModelForm):
    """Form for creating and editing employees."""

    class Meta:
        model = Employee
        fields = [
            'employee_id', 'department', 'position', 'manager',
            'employment_type', 'status', 'hire_date', 'termination_date',
            'work_email', 'work_phone',
            'emergency_contact_name', 'emergency_contact_phone', 'notes'
        ]
        widgets = {
            'employee_id': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': _('e.g., EMP001'),
            }),
            'department': forms.Select(attrs={
                'class': 'select select-bordered w-full',
            }),
            'position': forms.Select(attrs={
                'class': 'select select-bordered w-full',
            }),
            'manager': forms.Select(attrs={
                'class': 'select select-bordered w-full',
            }),
            'employment_type': forms.Select(attrs={
                'class': 'select select-bordered w-full',
            }),
            'status': forms.Select(attrs={
                'class': 'select select-bordered w-full',
            }),
            'hire_date': forms.DateInput(attrs={
                'class': 'input input-bordered w-full',
                'type': 'date',
            }),
            'termination_date': forms.DateInput(attrs={
                'class': 'input input-bordered w-full',
                'type': 'date',
            }),
            'work_email': forms.EmailInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': _('work@example.com'),
            }),
            'work_phone': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': _('(555) 123-4567'),
            }),
            'emergency_contact_name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': _('Emergency contact name'),
            }),
            'emergency_contact_phone': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': _('Emergency contact phone'),
            }),
            'notes': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
                'placeholder': _('Notes about this employee...'),
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['manager'].queryset = Employee.objects.exclude(
                pk=self.instance.pk
            )


class TimeEntryForm(forms.ModelForm):
    """Form for creating and editing time entries."""

    class Meta:
        model = TimeEntry
        fields = ['date', 'clock_in', 'clock_out', 'break_minutes', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'input input-bordered w-full',
                'type': 'date',
            }),
            'clock_in': forms.DateTimeInput(attrs={
                'class': 'input input-bordered w-full',
                'type': 'datetime-local',
            }),
            'clock_out': forms.DateTimeInput(attrs={
                'class': 'input input-bordered w-full',
                'type': 'datetime-local',
            }),
            'break_minutes': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'min': 0,
                'placeholder': '0',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 2,
                'placeholder': _('Notes...'),
            }),
        }


class ShiftForm(forms.ModelForm):
    """Form for creating and editing shifts."""

    class Meta:
        model = Shift
        fields = [
            'employee', 'date', 'start_time', 'end_time',
            'shift_type', 'department', 'status', 'notes'
        ]
        widgets = {
            'employee': forms.Select(attrs={
                'class': 'select select-bordered w-full',
            }),
            'date': forms.DateInput(attrs={
                'class': 'input input-bordered w-full',
                'type': 'date',
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'input input-bordered w-full',
                'type': 'time',
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'input input-bordered w-full',
                'type': 'time',
            }),
            'shift_type': forms.Select(attrs={
                'class': 'select select-bordered w-full',
            }),
            'department': forms.Select(attrs={
                'class': 'select select-bordered w-full',
            }),
            'status': forms.Select(attrs={
                'class': 'select select-bordered w-full',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 2,
                'placeholder': _('Notes...'),
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(
            status='active'
        ).select_related('user')
