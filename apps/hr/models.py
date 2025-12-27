"""HR models for employee, department, position, and time tracking."""
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Department(models.Model):
    """Organizational department with hierarchy support."""

    name = models.CharField(_('name'), max_length=100)
    code = models.SlugField(_('code'), unique=True, max_length=50)
    description = models.TextField(_('description'), blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('parent department'),
    )
    manager = models.ForeignKey(
        'Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_departments',
        verbose_name=_('department manager'),
    )
    cost_center = models.CharField(_('cost center'), max_length=20, blank=True)
    is_active = models.BooleanField(_('active'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('department')
        verbose_name_plural = _('departments')
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_ancestors(self):
        """Return list of parent departments up to root."""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors

    def get_full_path(self):
        """Return full hierarchical path as string."""
        ancestors = self.get_ancestors()
        path = [a.name for a in reversed(ancestors)] + [self.name]
        return ' > '.join(path)


class Position(models.Model):
    """Job position/title with optional salary range."""

    title = models.CharField(_('title'), max_length=100)
    code = models.SlugField(_('code'), unique=True, max_length=50)
    description = models.TextField(_('description'), blank=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='positions',
        verbose_name=_('department'),
    )
    min_salary = models.DecimalField(
        _('minimum salary'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    max_salary = models.DecimalField(
        _('maximum salary'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    is_exempt = models.BooleanField(
        _('exempt from overtime'),
        default=False,
        help_text=_('Exempt employees are not eligible for overtime pay'),
    )
    is_active = models.BooleanField(_('active'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('position')
        verbose_name_plural = _('positions')
        ordering = ['title']

    def __str__(self):
        return self.title


class Employee(models.Model):
    """Employee record linked to user account."""

    EMPLOYMENT_TYPE_CHOICES = [
        ('full_time', _('Full Time')),
        ('part_time', _('Part Time')),
        ('contractor', _('Contractor')),
        ('intern', _('Intern')),
        ('temporary', _('Temporary')),
    ]

    STATUS_CHOICES = [
        ('active', _('Active')),
        ('on_leave', _('On Leave')),
        ('suspended', _('Suspended')),
        ('terminated', _('Terminated')),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employee',
        verbose_name=_('user account'),
    )
    employee_id = models.CharField(
        _('employee ID'),
        max_length=20,
        unique=True,
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees',
        verbose_name=_('department'),
    )
    position = models.ForeignKey(
        Position,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees',
        verbose_name=_('position'),
    )
    manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='direct_reports',
        verbose_name=_('manager'),
    )
    employment_type = models.CharField(
        _('employment type'),
        max_length=20,
        choices=EMPLOYMENT_TYPE_CHOICES,
        default='full_time',
    )
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
    )
    hire_date = models.DateField(_('hire date'))
    termination_date = models.DateField(
        _('termination date'),
        null=True,
        blank=True,
    )
    work_email = models.EmailField(_('work email'), blank=True)
    work_phone = models.CharField(_('work phone'), max_length=20, blank=True)
    emergency_contact_name = models.CharField(
        _('emergency contact name'),
        max_length=100,
        blank=True,
    )
    emergency_contact_phone = models.CharField(
        _('emergency contact phone'),
        max_length=20,
        blank=True,
    )
    notes = models.TextField(_('notes'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('employee')
        verbose_name_plural = _('employees')
        ordering = ['user__last_name', 'user__first_name']

    def __str__(self):
        name = self.user.get_full_name() or self.user.email
        return f'{name} ({self.employee_id})'

    @property
    def is_active(self):
        """Check if employee is currently active."""
        return self.status == 'active' and self.termination_date is None

    def get_direct_reports_count(self):
        """Return count of direct reports."""
        return self.direct_reports.filter(status='active').count()


class TimeEntry(models.Model):
    """Time tracking entry for an employee."""

    APPROVAL_STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='time_entries',
        verbose_name=_('employee'),
    )
    date = models.DateField(_('date'))
    clock_in = models.DateTimeField(_('clock in'))
    clock_out = models.DateTimeField(_('clock out'), null=True, blank=True)
    break_minutes = models.PositiveIntegerField(
        _('break minutes'),
        default=0,
    )
    notes = models.TextField(_('notes'), blank=True)
    is_approved = models.BooleanField(_('approved'), default=False)
    approval_status = models.CharField(
        _('approval status'),
        max_length=20,
        choices=APPROVAL_STATUS_CHOICES,
        default='pending',
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_time_entries',
        verbose_name=_('approved by'),
    )
    approved_at = models.DateTimeField(_('approved at'), null=True, blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('time entry')
        verbose_name_plural = _('time entries')
        ordering = ['-date', '-clock_in']

    def __str__(self):
        return f'{self.employee} - {self.date}'

    @property
    def hours_worked(self):
        """Calculate hours worked minus breaks."""
        if not self.clock_out:
            return Decimal('0')
        total_seconds = (self.clock_out - self.clock_in).total_seconds()
        break_seconds = self.break_minutes * 60
        net_seconds = max(0, total_seconds - break_seconds)
        return Decimal(str(net_seconds / 3600)).quantize(Decimal('0.01'))

    @property
    def is_complete(self):
        """Check if time entry has both clock in and out."""
        return self.clock_in and self.clock_out


class Shift(models.Model):
    """Scheduled work shift for an employee."""

    SHIFT_TYPE_CHOICES = [
        ('regular', _('Regular')),
        ('overtime', _('Overtime')),
        ('on_call', _('On Call')),
        ('training', _('Training')),
    ]

    STATUS_CHOICES = [
        ('scheduled', _('Scheduled')),
        ('confirmed', _('Confirmed')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
        ('no_show', _('No Show')),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='shifts',
        verbose_name=_('employee'),
    )
    date = models.DateField(_('date'))
    start_time = models.TimeField(_('start time'))
    end_time = models.TimeField(_('end time'))
    shift_type = models.CharField(
        _('shift type'),
        max_length=20,
        choices=SHIFT_TYPE_CHOICES,
        default='regular',
    )
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled',
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shifts',
        verbose_name=_('department'),
    )
    notes = models.TextField(_('notes'), blank=True)
    is_confirmed = models.BooleanField(_('confirmed'), default=False)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('shift')
        verbose_name_plural = _('shifts')
        ordering = ['date', 'start_time']
        unique_together = ['employee', 'date', 'start_time']

    def __str__(self):
        return f'{self.employee} - {self.date} {self.start_time}'

    @property
    def duration_hours(self):
        """Calculate shift duration in hours."""
        from datetime import datetime, timedelta
        start = datetime.combine(self.date, self.start_time)
        end = datetime.combine(self.date, self.end_time)
        if end < start:
            end += timedelta(days=1)
        return (end - start).total_seconds() / 3600
