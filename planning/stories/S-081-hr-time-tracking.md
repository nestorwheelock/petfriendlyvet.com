# S-081: HR Time Tracking

> **REQUIRED READING:** Before implementation, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md)

**Story Type:** User Story
**Priority:** Medium
**Epoch:** 4
**Status:** IN PROGRESS

## User Story

**As a** staff member
**I want to** clock in/out and track my work hours
**So that** my time is recorded for payroll and reporting

**As a** manager
**I want to** approve or reject time entries
**So that** hours are accurately recorded before payroll processing

**As a** HR administrator
**I want to** view and manage all employee time entries
**So that** I can generate accurate payroll and labor reports

## Acceptance Criteria

### Clock In/Out
- [x] Staff can clock in from timesheet page
- [x] Staff can clock out from timesheet page
- [x] Clock in/out from task detail page (links time to task)
- [x] System records clock in/out timestamp
- [x] System shows current clocked-in status
- [x] Cannot clock in if already clocked in
- [x] Cannot clock out if not clocked in

### Timesheet View
- [x] Staff can view their time entries
- [x] Entries show date, clock in/out times, break, hours
- [x] Entries show associated task (if any)
- [x] Pending entries show "Pending" status
- [x] Approved entries show "Approved" status
- [x] Filter by date range
- [x] Filter by task

### Time Entry Management
- [ ] Managers can approve time entries
- [ ] Managers can reject time entries with reason
- [ ] Staff notified when entries approved/rejected
- [ ] Manual time entry creation for missed punches
- [ ] Time entry editing with audit trail

### Reporting
- [ ] Hours worked per employee (daily/weekly/monthly)
- [ ] Hours worked per department
- [ ] Hours worked per task/project
- [ ] Overtime calculations
- [ ] Export to CSV/Excel

## Technical Implementation

### Models (apps/hr/models.py)

```python
class TimeEntry(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField()
    clock_in = models.DateTimeField()
    clock_out = models.DateTimeField(null=True, blank=True)
    break_minutes = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, null=True, blank=True)
    approval_status = models.CharField(max_length=20, default='pending')
    task = models.ForeignKey('practice.Task', null=True, blank=True, related_name='time_entries')

    @property
    def hours_worked(self):
        if self.clock_out:
            delta = self.clock_out - self.clock_in
            hours = Decimal(delta.total_seconds()) / 3600
            break_hours = Decimal(self.break_minutes) / 60
            return (hours - break_hours).quantize(Decimal('0.01'))
        return Decimal('0.00')
```

### Views (apps/hr/views.py)

- `timesheet_view` - Display employee's time entries with filters
- `clock_in_view` - POST to clock in (accepts optional task_id)
- `clock_out_view` - POST to clock out current entry

### Templates

- `templates/hr/timesheet.html` - Timesheet display with filter
- `templates/practice/task_detail.html` - Time clock widget

## Related Tasks

- T-097c: Time Tracking in HR (COMPLETED)
- T-097g: Task Time Clock Integration (COMPLETED)

## GitHub Issues

- #11: T-088 Time Entry Clock In/Out
- #13: T-097g Task Time Clock Integration

## Definition of Done

- [x] Clock in/out from timesheet
- [x] Clock in/out from task detail page
- [x] Time entries stored with employee and optional task
- [x] Timesheet shows task column
- [x] Timesheet filterable by task
- [ ] Approval workflow implemented
- [ ] Manager approval view created
- [ ] Reporting dashboards created
- [x] Tests written and passing (>95% coverage)
- [ ] Documentation updated

## Dependencies

- T-097a: HR Module Foundation (COMPLETED)
- T-097b: Employee Model (COMPLETED)

## Notes

- TimeEntry now links to practice.Task for project-based time tracking
- StaffProfile links to Employee for unified HR tracking
- Consider integrating with payroll system in future epoch
