# B-054: Missing Prescription Refill Request Cancellation

**Severity**: High
**Affected Component**: apps/pharmacy
**Type**: Missing Feature (CRUD Gap)
**Status**: Open
**Correlates With Error Tracker**: No direct correlation

## Bug Description

Users can submit prescription refill requests but cannot cancel them. Once submitted, there is no way to cancel a refill request even if it was submitted by mistake or is no longer needed.

## Steps to Reproduce

1. Log in as a customer
2. Navigate to /pharmacy/prescriptions/
3. Request a refill for a prescription
4. Navigate to /pharmacy/refills/
5. View the pending refill request
6. Attempt to cancel it
7. No cancel option exists

## Expected Behavior

Users should be able to:
- Cancel refill requests with status 'pending'
- Cancel requests with status 'approved' (before fulfillment)
- See cancellation confirmation
- Receive email confirmation of cancellation

## Actual Behavior

- No cancel button on refill detail page
- No cancel view or URL
- Users cannot stop unwanted refills
- Must contact pharmacy staff to cancel

## Impact

- Unwanted medications may be prepared
- Wasted pharmacy staff time
- Users may refuse pickup (inventory issues)
- Poor user experience

## Proposed Solution

1. Create `RefillRequestCancelView` with confirmation
2. Validate: can only cancel 'pending' or 'approved' requests
3. Add cancel button to refill_detail.html
4. Update refill status to 'cancelled'
5. Send cancellation notification email

## Files to Modify

- `apps/pharmacy/views.py` - Add RefillRequestCancelView
- `apps/pharmacy/urls.py` - Add cancel route
- `templates/pharmacy/refill_detail.html` - Add cancel button
- `templates/pharmacy/refill_cancel_confirm.html` - New template
- `tests/test_pharmacy_views.py` - Add tests

## Business Rules

```
Refill Status   | Cancel Allowed | Notes
----------------|----------------|------------------
pending         | Yes            | Not yet reviewed
approved        | Yes            | Reviewed but not filled
in_progress     | No             | Being prepared
ready           | No             | Ready for pickup
completed       | No             | Already dispensed
cancelled       | N/A            | Already cancelled
rejected        | N/A            | Not applicable
```

## Definition of Done

- [ ] RefillRequestCancelView with status validation
- [ ] Confirmation page
- [ ] Cancel button on refill_detail.html (conditional)
- [ ] Status updated to 'cancelled'
- [ ] Cancellation reason captured
- [ ] Email notification sent
- [ ] Tests with >95% coverage
- [ ] Manual testing complete
