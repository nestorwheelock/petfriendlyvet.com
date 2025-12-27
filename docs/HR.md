# HR Module

The `apps.hr` module provides human resources management including employees, departments, positions, time tracking, and shift scheduling.

## Table of Contents

- [Overview](#overview)
- [Models](#models)
  - [Department](#department)
  - [Position](#position)
  - [Employee](#employee)
  - [TimeEntry](#timeentry)
  - [Shift](#shift)
- [Views](#views)
- [URL Patterns](#url-patterns)
- [Workflows](#workflows)
  - [Employee Management](#employee-management)
  - [Time Tracking](#time-tracking)
  - [Shift Scheduling](#shift-scheduling)
  - [Task Time Tracking](#task-time-tracking)
- [Integration with Practice Module](#integration-with-practice-module)
- [Role-Based Permissions](#role-based-permissions)
- [Query Examples](#query-examples)
- [Testing](#testing)

## Overview

The HR module handles:

- **Departments** - Organizational structure and hierarchy
- **Positions** - Job titles and salary ranges
- **Employees** - HR records linked to user accounts
- **Time Tracking** - Clock in/out with task association
- **Shift Scheduling** - Work schedule management

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Department    │────▶│    Position     │────▶│    Employee     │
│  (structure)    │     │   (job title)   │     │   (HR record)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                                               │
        │                                               │
        ▼                                               ▼
┌─────────────────┐                           ┌─────────────────┐
│     Shift       │                           │   TimeEntry     │
│   (schedule)    │                           │  (clock in/out) │
└─────────────────┘                           └─────────────────┘
                                                      │
                                                      ▼
                                              ┌─────────────────┐
                                              │  practice.Task  │
                                              │ (time per task) │
                                              └─────────────────┘
```

## Models

### Department

Location: `apps/hr/models.py`

Organizational unit for grouping employees.

```python
class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', null=True, blank=True,
                               related_name='children')
    manager = models.ForeignKey('Employee', null=True, blank=True,
                                related_name='managed_departments')
    is_active = models.BooleanField(default=True)
```

### Position

Location: `apps/hr/models.py`

Job title with optional salary range.

```python
class Position(models.Model):
    title = models.CharField(max_length=100)
    code = models.SlugField(unique=True)
    department = models.ForeignKey(Department, null=True, blank=True,
                                   related_name='positions')
    description = models.TextField(blank=True)
    min_salary = models.DecimalField(max_digits=10, decimal_places=2,
                                     null=True, blank=True)
    max_salary = models.DecimalField(max_digits=10, decimal_places=2,
                                     null=True, blank=True)
    is_active = models.BooleanField(default=True)
```

### Employee

Location: `apps/hr/models.py`

HR record linked to user account.

```python
class Employee(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('on_leave', 'On Leave'),
        ('terminated', 'Terminated'),
    ]

    EMPLOYMENT_TYPE_CHOICES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contractor', 'Contractor'),
        ('intern', 'Intern'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='employee')
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, null=True, blank=True,
                                   related_name='employees')
    position = models.ForeignKey(Position, null=True, blank=True,
                                 related_name='employees')
    manager = models.ForeignKey('self', null=True, blank=True,
                                related_name='direct_reports')
    hire_date = models.DateField()
    termination_date = models.DateField(null=True, blank=True)
    employment_type = models.CharField(max_length=20,
                                       choices=EMPLOYMENT_TYPE_CHOICES,
                                       default='full_time')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              default='active')
```

### TimeEntry

Location: `apps/hr/models.py`

Clock in/out record with optional task association.

```python
class TimeEntry(models.Model):
    APPROVAL_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE,
                                 related_name='time_entries')
    date = models.DateField()
    clock_in = models.DateTimeField()
    clock_out = models.DateTimeField(null=True, blank=True)
    break_minutes = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, null=True, blank=True,
                                    related_name='approved_time_entries')
    approval_status = models.CharField(max_length=20,
                                       choices=APPROVAL_STATUS_CHOICES,
                                       default='pending')
    task = models.ForeignKey('practice.Task', null=True, blank=True,
                             on_delete=models.SET_NULL,
                             related_name='time_entries')

    @property
    def hours_worked(self):
        """Calculate hours worked (excluding breaks)."""
        if self.clock_out:
            delta = self.clock_out - self.clock_in
            hours = Decimal(delta.total_seconds()) / 3600
            break_hours = Decimal(self.break_minutes) / 60
            return (hours - break_hours).quantize(Decimal('0.01'))
        return Decimal('0.00')
```

### Shift

Location: `apps/hr/models.py`

Scheduled work shift.

```python
class Shift(models.Model):
    SHIFT_TYPE_CHOICES = [
        ('regular', 'Regular'),
        ('overtime', 'Overtime'),
        ('on_call', 'On Call'),
        ('training', 'Training'),
        ('pto', 'PTO'),
    ]

    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE,
                                 related_name='shifts')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    shift_type = models.CharField(max_length=20,
                                  choices=SHIFT_TYPE_CHOICES,
                                  default='regular')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              default='scheduled')
    department = models.ForeignKey(Department, null=True, blank=True,
                                   related_name='shifts')
    notes = models.TextField(blank=True)
```

## Views

### Dashboard

- `HRDashboardView` - Dashboard with KPIs and quick links

### Department CRUD

- `DepartmentListView` - List all departments
- `DepartmentCreateView` - Create new department
- `DepartmentUpdateView` - Edit department
- `DepartmentDeleteView` - Delete department

### Position CRUD

- `PositionListView` - List all positions
- `PositionCreateView` - Create new position
- `PositionUpdateView` - Edit position
- `PositionDeleteView` - Delete position

### Employee CRUD

- `EmployeeListView` - List all employees
- `EmployeeDetailView` - View employee details
- `EmployeeCreateView` - Create new employee
- `EmployeeUpdateView` - Edit employee
- `EmployeeDeleteView` - Delete employee

### Time Tracking

- `timesheet_view` - View employee's timesheet with task filter
- `clock_in_view` - Clock in (accepts optional task_id)
- `clock_out_view` - Clock out current entry

### Shift Scheduling

- `ShiftListView` - List all shifts
- `ShiftCreateView` - Create new shift
- `ShiftUpdateView` - Edit shift
- `ShiftDeleteView` - Delete shift

## URL Patterns

Base URL: `/staff-{token}/operations/hr/`

```
/                          # HR Dashboard
/departments/              # Department list
/departments/add/          # Create department
/departments/<pk>/edit/    # Edit department
/departments/<pk>/delete/  # Delete department

/positions/                # Position list
/positions/add/            # Create position
/positions/<pk>/edit/      # Edit position
/positions/<pk>/delete/    # Delete position

/employees/                # Employee list
/employees/add/            # Create employee
/employees/<pk>/           # Employee detail
/employees/<pk>/edit/      # Edit employee
/employees/<pk>/delete/    # Delete employee

/time/                     # Timesheet
/time/?task=<pk>           # Timesheet filtered by task
/time/clock-in/            # Clock in (POST)
/time/clock-out/           # Clock out (POST)

/schedule/                 # Shift list
/schedule/add/             # Create shift
/schedule/<pk>/edit/       # Edit shift
/schedule/<pk>/delete/     # Delete shift
```

## Workflows

### Employee Management

```
1. Create Department → Create Position → Create Employee
2. Employee linked to User account via OneToOne
3. Optional: Link StaffProfile to Employee for unified tracking
```

### Time Tracking

```
1. Employee clicks "Clock In" on timesheet
2. System creates TimeEntry with current timestamp
3. Employee clicks "Clock Out" when done
4. System updates TimeEntry with clock_out time
5. hours_worked calculated automatically
6. Manager approves/rejects entries
```

### Shift Scheduling

```
1. Manager creates Shift for employee
2. Shift assigned to date/time and optional department
3. Employee can view their schedule
4. Manager can update/cancel shifts
```

### Task Time Tracking

```
1. Employee opens task detail page
2. Clicks "Start Tracking" button
3. TimeEntry created with task FK
4. Employee clicks "Stop" when done
5. Time log displayed on task detail
6. Total hours aggregated per task
7. Timesheet can filter by task
```

## Integration with Practice Module

### StaffProfile ↔ Employee Link

StaffProfile now has an optional FK to Employee:

```python
# In apps/practice/models.py
class StaffProfile(models.Model):
    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff_profiles'
    )
```

This allows:
- StaffProfile keeps veterinary-specific fields (DEA, license, permissions)
- Employee keeps generic HR fields (hire_date, department, position)
- Unified tracking when both are linked

### TimeEntry ↔ Task Link

HR TimeEntry links to practice.Task for project time tracking:

```python
# In apps/hr/models.py
class TimeEntry(models.Model):
    task = models.ForeignKey(
        'practice.Task',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='time_entries'
    )
```

Access from Task:
```python
task = Task.objects.get(pk=1)
total_hours = sum(e.hours_worked for e in task.time_entries.filter(clock_out__isnull=False))
```

## Role-Based Permissions

HR module uses the RBAC permission system:

| Action | Permission Required |
|--------|---------------------|
| View HR dashboard | `hr.view` |
| Manage departments | `hr.manage` |
| Manage positions | `hr.manage` |
| Manage employees | `hr.manage` |
| View timesheet | `hr.view` |
| Approve time entries | `hr.manage` |
| Manage shifts | `hr.manage` |

## Query Examples

### Get all active employees by department

```python
from apps.hr.models import Employee

employees = Employee.objects.filter(
    status='active',
    department__code='clinical'
).select_related('user', 'department', 'position')
```

### Get time entries for a task

```python
from apps.hr.models import TimeEntry

entries = TimeEntry.objects.filter(
    task=task
).select_related('employee__user').order_by('-date', '-clock_in')

total_hours = sum(e.hours_worked for e in entries if e.clock_out)
```

### Get employee's timesheet with task filter

```python
from apps.hr.models import TimeEntry

entries = TimeEntry.objects.filter(employee=employee)
if task_id:
    entries = entries.filter(task_id=task_id)
entries = entries.order_by('-date', '-clock_in')[:30]
```

### Get today's shifts

```python
from apps.hr.models import Shift
from django.utils import timezone

today = timezone.now().date()
shifts = Shift.objects.filter(
    date=today
).select_related('employee__user', 'department').order_by('start_time')
```

## Testing

Test file: `apps/hr/tests.py`

### Test Categories

1. **StaffProfileEmployeeLinkTests** - StaffProfile ↔ Employee FK
2. **TimeEntryTaskLinkTests** - TimeEntry ↔ Task FK
3. **TaskClockInOutViewTests** - Clock in/out from task
4. **TimesheetTaskFilterTests** - Timesheet task filter

### Running Tests

```bash
# Run all HR tests
python -m pytest apps/hr/tests.py -v

# Run specific test class
python -m pytest apps/hr/tests.py::TimeEntryTaskLinkTests -v

# Run with coverage
python -m pytest apps/hr/tests.py --cov=apps.hr
```

### Test Coverage

Current: 11 tests passing
- StaffProfileEmployeeLinkTests: 3 tests
- TimeEntryTaskLinkTests: 4 tests
- TaskClockInOutViewTests: 2 tests
- TimesheetTaskFilterTests: 2 tests
