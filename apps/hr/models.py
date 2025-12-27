"""HR models for employment, department, position, and time tracking.

Employment is handled via PartyRelationship in accounts.
This module provides HR-specific extensions and time tracking.
"""
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
        settings.AUTH_USER_MODEL,
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


class EmploymentDetails(models.Model):
    """HR-specific details for employment/contractor relationships.

    This extends a PartyRelationship with HR-specific data like
    department, position, payroll info, etc.
    """

    relationship = models.OneToOneField(
        'parties.PartyRelationship',
        on_delete=models.CASCADE,
        related_name='employment_details',
        verbose_name=_('relationship'),
        help_text=_('The employment relationship this extends'),
    )

    # Employment identifiers
    employee_id = models.CharField(
        _('employee/contractor ID'),
        max_length=20,
        unique=True,
    )

    # Organizational assignment
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employment_details',
        verbose_name=_('department'),
    )
    position = models.ForeignKey(
        Position,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employment_details',
        verbose_name=_('position'),
    )
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='direct_reports',
        verbose_name=_('manager'),
    )

    # Work contact
    work_email = models.EmailField(_('work email'), blank=True)
    work_phone = models.CharField(_('work phone'), max_length=20, blank=True)

    # Mexico-specific tax/payroll (for W-2 equivalents)
    rfc = models.CharField(
        _('RFC'),
        max_length=13,
        blank=True,
        help_text=_('Tax ID (Mexico)'),
    )
    curp = models.CharField(
        _('CURP'),
        max_length=18,
        blank=True,
        help_text=_('Personal ID (Mexico)'),
    )
    imss_number = models.CharField(
        _('IMSS number'),
        max_length=20,
        blank=True,
        help_text=_('Social security number (Mexico)'),
    )

    # Compensation (for employees, not contractors - contractors use rate on relationship)
    salary = models.DecimalField(
        _('salary'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    pay_frequency = models.CharField(
        _('pay frequency'),
        max_length=20,
        choices=[
            ('weekly', _('Weekly')),
            ('biweekly', _('Biweekly')),
            ('semimonthly', _('Semi-monthly')),
            ('monthly', _('Monthly')),
        ],
        default='biweekly',
        blank=True,
    )

    # Contractor-specific
    rate_type = models.CharField(
        _('rate type'),
        max_length=20,
        choices=[
            ('hourly', _('Hourly')),
            ('daily', _('Daily')),
            ('per_job', _('Per Job')),
            ('fixed_monthly', _('Fixed Monthly')),
        ],
        blank=True,
    )
    rate_amount = models.DecimalField(
        _('rate amount'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    payment_terms = models.CharField(
        _('payment terms'),
        max_length=30,
        choices=[
            ('immediate', _('Immediate')),
            ('net_7', _('Net 7')),
            ('net_15', _('Net 15')),
            ('net_30', _('Net 30')),
            ('on_completion', _('On Completion')),
        ],
        blank=True,
    )

    # Emergency contact
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

    # Documents and notes
    contract_documents = models.JSONField(
        _('contract documents'),
        default=list,
        blank=True,
    )
    sops = models.JSONField(
        _('SOPs'),
        default=list,
        blank=True,
        help_text=_('Standard Operating Procedures'),
    )
    notes = models.TextField(_('notes'), blank=True)

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('employment details')
        verbose_name_plural = _('employment details')

    def __str__(self):
        return f'{self.employee_id} - {self.relationship}'

    @property
    def person(self):
        """Get the person from the relationship."""
        return self.relationship.from_person

    @property
    def organization(self):
        """Get the organization from the relationship."""
        return self.relationship.to_organization


class TimeEntry(models.Model):
    """Time tracking entry for a person."""

    APPROVAL_STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    ]

    person = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,  # Temporarily nullable for migration
        blank=True,
        related_name='time_entries',
        verbose_name=_('person'),
    )
    organization = models.ForeignKey(
        'parties.Organization',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='time_entries',
        verbose_name=_('organization'),
        help_text=_('Which organization this time is for (if multi-org)'),
    )
    task = models.ForeignKey(
        'practice.Task',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='time_entries',
        verbose_name=_('task'),
        help_text=_('Optional task this time entry is associated with'),
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
        return f'{self.person} - {self.date}'

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
    """Scheduled work shift for a person."""

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

    person = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,  # Temporarily nullable for migration
        blank=True,
        related_name='shifts',
        verbose_name=_('person'),
    )
    organization = models.ForeignKey(
        'parties.Organization',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='shifts',
        verbose_name=_('organization'),
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
        unique_together = ['person', 'date', 'start_time']

    def __str__(self):
        return f'{self.person} - {self.date} {self.start_time}'

    @property
    def duration_hours(self):
        """Calculate shift duration in hours."""
        from datetime import datetime, timedelta
        start = datetime.combine(self.date, self.start_time)
        end = datetime.combine(self.date, self.end_time)
        if end < start:
            end += timedelta(days=1)
        return (end - start).total_seconds() / 3600


# =============================================================================
# Backwards Compatibility - DEPRECATED
# =============================================================================

class Employee(models.Model):
    """DEPRECATED: Use PartyRelationship + EmploymentDetails instead.

    This model is kept temporarily for backwards compatibility during migration.
    Will be removed in a future version.
    """

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
        related_name='old_direct_reports',
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
        verbose_name = _('employee (deprecated)')
        verbose_name_plural = _('employees (deprecated)')
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
        return self.old_direct_reports.filter(status='active').count()
