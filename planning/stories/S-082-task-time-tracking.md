# S-082: Task Time Tracking

> **REQUIRED READING:** Before implementation, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md)

**Story Type:** User Story
**Priority:** Medium
**Epoch:** 4
**Status:** COMPLETED

## User Story

**As a** staff member
**I want to** track time spent on specific tasks
**So that** project costs can be accurately calculated

**As a** team lead
**I want to** see time spent on each task
**So that** I can track project costs and resource allocation

**As a** practice manager
**I want to** generate time reports by task
**So that** I can bill clients accurately and analyze productivity

## Acceptance Criteria

### Task Time Clock Widget
- [x] Clock in button on task detail page
- [x] Clock out button when clocked in for task
- [x] Shows "Tracking" indicator when clocked in
- [x] Displays total hours for task
- [x] Shows time log of entries for task

### Time Entry Association
- [x] Clock in creates TimeEntry linked to task
- [x] Clock out updates existing entry
- [x] TimeEntry stores task foreign key
- [x] Task can access related time entries

### Timesheet Integration
- [x] Task column in timesheet table
- [x] Filter dropdown to show entries by task
- [x] Clear filter option
- [x] Link from filtered view to task detail

### Aggregation
- [x] Total hours displayed on task detail
- [ ] Hours by employee breakdown
- [ ] Cost calculation (hours x rate)
- [ ] Export time data per task

## Technical Implementation

### Model Changes (apps/hr/models.py)

```python
class TimeEntry(models.Model):
    # ... existing fields ...
    task = models.ForeignKey(
        'practice.Task',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='time_entries',
        verbose_name=_('task'),
        help_text=_('Optional task this time entry is associated with'),
    )
```

### View Changes (apps/hr/views.py)

```python
@login_required
def clock_in_view(request):
    # ... existing logic ...
    task = None
    task_id = request.POST.get('task_id')
    if task_id:
        from apps.practice.models import Task
        task = Task.objects.get(pk=task_id)

    TimeEntry.objects.create(
        employee=employee,
        date=now.date(),
        clock_in=now,
        task=task,
    )
```

```python
@login_required
def timesheet_view(request):
    # ... existing logic ...
    task_id = request.GET.get('task')
    if task_id:
        entries = entries.filter(task_id=task_id)
```

### Template Changes

**Task Detail (templates/practice/task_detail.html):**
- Time tracking section with clock in/out buttons
- Time log table showing entries
- Total hours display

**Timesheet (templates/hr/timesheet.html):**
- Task filter dropdown
- Task column in entries table
- Link to task from entries

## Test Cases

```python
class TimeEntryTaskLinkTests(TestCase):
    def test_timeentry_has_task_field(self):
        """TimeEntry should have an optional task ForeignKey."""

    def test_timeentry_can_link_to_task(self):
        """TimeEntry can be linked to a Task."""

    def test_task_can_access_time_entries(self):
        """Task can reverse-access its TimeEntries."""

    def test_task_total_hours(self):
        """Task can calculate total hours from TimeEntries."""

class TaskClockInOutViewTests(TestCase):
    def test_clock_in_for_task(self):
        """User can clock in for a specific task."""

    def test_clock_out_for_task(self):
        """User can clock out from a task."""

class TimesheetTaskFilterTests(TestCase):
    def test_timesheet_shows_task_column(self):
        """Timesheet view should show task column."""

    def test_timesheet_filter_by_task(self):
        """Timesheet can be filtered by task."""
```

## Related Tasks

- T-097g: Task Time Clock Integration

## GitHub Issues

- #13: T-097g Add time clock integration to tasks/projects

## Definition of Done

- [x] Task FK added to TimeEntry model
- [x] Migration created and applied
- [x] Clock in/out views accept task_id
- [x] Task detail shows time tracking widget
- [x] Timesheet shows task column
- [x] Timesheet filterable by task
- [x] All 11 HR tests passing
- [x] Committed to repository

## Dependencies

- S-081: HR Time Tracking
- T-097c: Time Tracking in HR

## Notes

- Time entries can exist without a task (general clock in/out)
- Tasks with time entries show total hours
- Future: Add project-level time aggregation
- Future: Billable vs non-billable time distinction
