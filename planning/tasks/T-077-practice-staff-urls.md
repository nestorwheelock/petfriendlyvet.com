# T-077: Practice App Staff URLs

> **REQUIRED READING:** Before implementation, review [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)

**Story Type**: Task
**Priority**: Medium (Internal Efficiency)
**Estimate**: 5 hours
**Status**: Pending
**Discovered By**: QA Browser Tests (2025-12-25)

## Objective

Create staff-facing views and URLs for the Practice app so clinic staff can access their dashboard, schedule, time tracking, and task management.

## Background

Browser E2E tests revealed that the Practice app has an empty `urls.py` file. Staff have no dashboard, time tracking, or task management UI. They need:
- Daily schedule overview
- Shift calendar
- Time clock (clock in/out)
- Timesheet review
- Task assignments

## Required URLs

| URL | View | Description |
|-----|------|-------------|
| `/staff/dashboard/` | `staff_dashboard` | Today's schedule, tasks |
| `/staff/schedule/` | `schedule_view` | Shift calendar |
| `/staff/timeclock/` | `time_clock` | Clock in/out |
| `/staff/timesheet/` | `timesheet` | Hours worked |
| `/staff/tasks/` | `task_list` | Assigned tasks |

## Deliverables

### Files to Modify
- [ ] `apps/practice/urls.py` - Add URL patterns (file exists but empty)
- [ ] `apps/practice/views.py` - View functions/classes

### Files to Create
- [ ] `templates/practice/dashboard.html` - Staff dashboard
- [ ] `templates/practice/schedule.html` - Shift calendar
- [ ] `templates/practice/timeclock.html` - Clock in/out
- [ ] `templates/practice/timesheet.html` - Hours review
- [ ] `templates/practice/tasks.html` - Task list

### Files to Modify
- [ ] `config/urls.py` - Verify practice URLs included

## Definition of Done

- [ ] All 5 URLs accessible to staff users only
- [ ] Dashboard shows today's appointments and tasks
- [ ] Schedule shows weekly/monthly view
- [ ] Time clock allows clock in/out with timestamps
- [ ] Timesheet shows hours worked summary
- [ ] Task list shows assigned StaffTask items
- [ ] Tests written with >95% coverage
- [ ] Browser tests updated to validate staff URLs
- [ ] Mobile-responsive templates (especially timeclock)

## Technical Notes

- Check existing models in `apps/practice/models.py`
- All views require @staff_member_required decorator
- Time clock should prevent double clock-in
- Dashboard should integrate with appointments
- Consider real-time updates for task assignments

## Related

- QA Discovery: `planning/issues/MISSING_CUSTOMER_URLS.md`
- Existing models: `apps/practice/models.py`
- Existing admin: `apps/practice/admin.py`
