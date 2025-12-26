# B-051: Missing Appointment Reschedule/Update Functionality

**Severity**: High
**Affected Component**: apps/appointments
**Type**: Missing Feature (CRUD Gap)
**Status**: Open
**Correlates With Error Tracker**: No direct correlation

## Bug Description

Users can book and cancel appointments but cannot reschedule them. To change an appointment time, users must cancel and create a new booking, losing their original slot.

## Steps to Reproduce

1. Log in as a customer
2. Navigate to /appointments/my/
3. View an upcoming appointment
4. Attempt to change date/time
5. No reschedule option exists - only cancel

## Expected Behavior

Users should be able to:
- Reschedule appointments to a different date/time
- Change the service type if needed
- Update appointment notes/special requests
- See available slots for rescheduling

## Actual Behavior

- Only "Cancel" option available
- No way to modify existing appointments
- Must cancel and rebook (may lose preferred slot)
- Cannot update notes after booking

## Impact

- Poor user experience - common need to reschedule
- Users may lose preferred time slots
- Increases cancellation rate
- More support requests for manual rescheduling

## Proposed Solution

1. Create `AppointmentRescheduleView` with date/time picker
2. Reuse `available_slots` AJAX endpoint for new times
3. Add reschedule button to appointment_detail.html
4. Validate: can only reschedule future appointments with status 'scheduled' or 'confirmed'
5. Add `AppointmentUpdateView` for notes editing

## Files to Modify

- `apps/appointments/views.py` - Add RescheduleView, UpdateView
- `apps/appointments/forms.py` - Add RescheduleForm, UpdateForm
- `apps/appointments/urls.py` - Add reschedule/update routes
- `templates/appointments/appointment_detail.html` - Add buttons
- `templates/appointments/reschedule.html` - New template
- `tests/test_appointments_views.py` - Add tests

## Definition of Done

- [ ] AppointmentRescheduleView with form
- [ ] Date/time picker showing available slots
- [ ] Validation for reschedule eligibility
- [ ] AppointmentUpdateView for notes
- [ ] Reschedule button in templates
- [ ] Email notification on reschedule
- [ ] Tests with >95% coverage
- [ ] Manual testing complete
