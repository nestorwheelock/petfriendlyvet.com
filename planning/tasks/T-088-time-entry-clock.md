# T-088: Time Entry Clock In/Out

> **STOP! READ THIS FIRST:**
> Before writing ANY code, complete the [TDD STOP GATE](../TDD_STOP_GATE.md)
>
> You must output the confirmation block and write failing tests
> BEFORE any implementation code.

---

**Story**: S-008 Practice Management
**Priority**: Low
**Status**: Pending
**Estimate**: 3 hours
**Dependencies**: T-085 (Staff CRUD)

---

## AI Coding Brief

**Role**: Backend/Frontend Developer
**Objective**: Add clock in/out functionality for staff time tracking
**User Request**: Time tracking for staff

### Context

Currently:
- TimeEntry can only be listed (time_tracking view exists)
- No clock in/out functionality
- TimeEntry model has: staff, clock_in, clock_out, break_minutes, is_approved

### Constraints

**Allowed File Paths**:
- `apps/practice/forms.py` (MODIFY - add TimeEntryForm)
- `apps/practice/views.py` (MODIFY)
- `apps/practice/urls.py` (MODIFY)
- `templates/practice/time_entry_form.html` (CREATE)
- `apps/practice/tests/test_time_entry.py` (CREATE)

**Forbidden Paths**: None

### Deliverables

- [ ] `TimeEntryForm` - Edit time entries
- [ ] `clock_in` view - Start a time entry
- [ ] `clock_out` view - End current time entry
- [ ] `time_entry_edit` view - Adjust time entry
- [ ] `time_entry_approve` view - Manager approval
- [ ] Templates for clock in/out
- [ ] URL routes added

### URL Routes

```python
path('time/clock-in/', views.clock_in, name='clock_in'),
path('time/clock-out/', views.clock_out, name='clock_out'),
path('time/<int:pk>/edit/', views.time_entry_edit, name='time_entry_edit'),
path('time/<int:pk>/approve/', views.time_entry_approve, name='time_entry_approve'),
```

### View Logic

```python
def clock_in(request):
    """Create new TimeEntry with clock_in = now."""
    staff = request.user.staff_profile
    # Check no open entries
    open_entry = TimeEntry.objects.filter(staff=staff, clock_out__isnull=True).first()
    if open_entry:
        messages.error(request, "Already clocked in")
        return redirect(...)
    TimeEntry.objects.create(staff=staff, clock_in=timezone.now())
    messages.success(request, "Clocked in successfully")
    return redirect(...)

def clock_out(request):
    """Set clock_out on current open entry."""
    staff = request.user.staff_profile
    open_entry = TimeEntry.objects.filter(staff=staff, clock_out__isnull=True).first()
    if not open_entry:
        messages.error(request, "Not clocked in")
        return redirect(...)
    open_entry.clock_out = timezone.now()
    open_entry.save()
    messages.success(request, f"Clocked out. Worked: {open_entry.hours_worked} hours")
    return redirect(...)
```

### Definition of Done

- [ ] Clock in/out buttons on dashboard
- [ ] Current status shown (clocked in/out)
- [ ] Time entry editing for managers
- [ ] Approval workflow
- [ ] Tests written FIRST (>95% coverage)
- [ ] All tests passing

### Test Cases

```python
class TimeEntryCRUDTests(TestCase):
    """Test time entry operations."""

    def test_clock_in_creates_entry(self):
        pass

    def test_clock_in_when_already_clocked_in(self):
        """Cannot clock in twice."""
        pass

    def test_clock_out_closes_entry(self):
        pass

    def test_clock_out_when_not_clocked_in(self):
        """Cannot clock out without being clocked in."""
        pass

    def test_hours_worked_calculation(self):
        pass

    def test_time_entry_edit_by_manager(self):
        pass

    def test_time_entry_approve(self):
        pass
```

### Notes

- Show clock in/out status on practice dashboard
- Consider break tracking (start break / end break)
- Weekly timesheet view as future enhancement
