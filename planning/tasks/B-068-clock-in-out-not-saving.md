# B-068: Clock In/Out Not Saving Time Entries

**Severity**: High
**Affected Component**: apps/practice/views.py (clock_in, clock_out)
**Discovered**: 2025-12-26

## Bug Description

When a staff member clicks "Clock In" or "Clock Out" in the Time Tracking section, the time entry is not being saved.

## Steps to Reproduce

1. Log in as a staff member
2. Navigate to Practice > Time Tracking
3. Click "Clock In" button
4. Click "Clock In Now" on the confirmation page
5. Observe: No time entry is created

## Expected Behavior

A new TimeEntry should be created with clock_in set to the current time.

## Actual Behavior

Nothing happens - no time entry is saved to the database.

## Root Cause Analysis

**Confirmed Root Cause**: Django messages were not being displayed in the Staff Portal.

The `templates/base_staff.html` template was overriding the `{% block messages %}` from `base.html` with an empty block:
```html
{% block messages %}{% endblock %}
```

This meant that when `messages.error()`, `messages.success()`, or `messages.warning()` were called in views, the messages were never rendered on the page. Users with no StaffProfile were silently redirected without seeing the error message.

The view logic in `apps/practice/views.py` was working correctly - it properly created TimeEntry records when the user had a valid StaffProfile. The issue was purely in the template not displaying feedback.

## Environment

- Django 5.2.9
- Python 3.12.1

## Fix Applied

**File Modified**: `templates/base_staff.html`

Added message rendering inside the main content area before `{% block staff_content %}`:
```html
{% if messages %}
<div class="mb-4 space-y-2">
    {% for message in messages %}
    <div class="rounded-lg p-4 {% if message.tags == 'error' %}bg-red-100...">
        {{ message }}
    </div>
    {% endfor %}
</div>
{% endif %}
```

## Test Coverage

Added test: `test_clock_in_without_staff_profile_shows_error` in `apps/practice/tests.py`

All 44 practice module tests pass.

## Status

**FIXED** - 2025-12-26
