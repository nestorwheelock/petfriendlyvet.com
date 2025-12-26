# B-052: Missing Order Cancellation Functionality

**Severity**: High
**Affected Component**: apps/store
**Type**: Missing Feature (CRUD Gap)
**Status**: Open
**Correlates With Error Tracker**: No direct correlation

## Bug Description

Users cannot cancel orders from the customer portal. Once an order is placed, there is no self-service option to cancel it, even if the order is still pending or unpaid.

## Steps to Reproduce

1. Log in as a customer
2. Place an order via /store/checkout/
3. Navigate to /store/orders/
4. View order details
5. Attempt to cancel the order
6. No cancel option exists

## Expected Behavior

Users should be able to:
- Cancel orders with status 'pending' (unpaid)
- Request cancellation for 'paid' orders before shipping
- See cancellation confirmation with refund info
- Receive email confirmation of cancellation

## Actual Behavior

- No cancel button or option on order detail page
- Order model supports 'cancelled' status but no UI
- Users must contact support for cancellations
- No self-service refund initiation

## Impact

- Poor user experience
- Increased support burden
- Users may dispute charges instead of cancelling
- No transparency in cancellation process

## Proposed Solution

1. Create `OrderCancelView` with confirmation
2. Validate cancellation rules:
   - 'pending': Allow immediate cancel
   - 'paid'/'preparing': Allow cancel request (needs staff approval)
   - 'shipped'/'delivered': Redirect to return request
3. Add cancel button to order_detail.html
4. Send cancellation confirmation email
5. If paid, initiate refund process (or flag for manual refund)

## Files to Modify

- `apps/store/views.py` - Add OrderCancelView
- `apps/store/urls.py` - Add cancel route
- `templates/store/order_detail.html` - Add cancel button
- `templates/store/order_cancel_confirm.html` - New template
- `apps/store/emails.py` - Add cancellation email (if exists)
- `tests/test_store_views.py` - Add tests

## Business Rules

```
Order Status    | Cancel Allowed | Action
----------------|----------------|------------------
pending         | Yes            | Immediate cancel, no refund needed
paid            | Yes (request)  | Flag for staff, initiate refund
preparing       | Yes (request)  | Flag for staff, may have restocking
ready           | No             | Must pickup or request return
shipped         | No             | Must wait for delivery, then return
delivered       | No             | Use return/refund flow
cancelled       | N/A            | Already cancelled
refunded        | N/A            | Already refunded
```

## Definition of Done

- [ ] OrderCancelView with status validation
- [ ] Confirmation page with cancel reason input
- [ ] Cancel button on order_detail.html (conditional)
- [ ] Status updated to 'cancelled' or 'cancellation_requested'
- [ ] Email notification sent
- [ ] Refund initiation for paid orders
- [ ] Tests with >95% coverage
- [ ] Manual testing complete
