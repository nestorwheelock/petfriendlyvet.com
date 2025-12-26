# B-053: Missing Invoice Payment Functionality

**Severity**: High
**Affected Component**: apps/billing
**Type**: Missing Feature (CRUD Gap)
**Status**: Open
**Correlates With Error Tracker**: No direct correlation

## Bug Description

Users can view invoices but cannot pay them through the customer portal. There is no payment UI or integration, requiring users to pay through other channels (in-person, phone).

## Steps to Reproduce

1. Log in as a customer with unpaid invoices
2. Navigate to /billing/invoices/
3. View invoice details
4. Attempt to pay the invoice
5. No payment option exists

## Expected Behavior

Users should be able to:
- View invoice with "Pay Now" button for unpaid invoices
- Pay via credit card (Stripe integration)
- See payment confirmation
- Receive email receipt
- View payment history on invoice

## Actual Behavior

- Invoice detail page is read-only
- No payment button or form
- No Stripe/payment gateway integration on billing
- Users must pay through external channels
- No payment status tracking visible to customers

## Impact

- Major friction in payment collection
- Delayed payments
- Increased accounts receivable
- Poor customer experience
- Staff time spent on manual payment processing

## Proposed Solution

1. Create `PayInvoiceView` with Stripe Checkout/Elements
2. Add "Pay Now" button to invoice_detail.html for unpaid invoices
3. Create payment confirmation page
4. Record payment in database
5. Send payment receipt email
6. Update invoice status to 'paid'

## Files to Modify

- `apps/billing/views.py` - Add PayInvoiceView, PaymentSuccessView
- `apps/billing/urls.py` - Add payment routes
- `apps/billing/forms.py` - Add PaymentForm (if needed)
- `templates/billing/invoice_detail.html` - Add pay button
- `templates/billing/pay_invoice.html` - New payment page
- `templates/billing/payment_success.html` - Confirmation
- `apps/billing/models.py` - Add Payment model if not exists
- `tests/test_billing_views.py` - Add tests

## Technical Considerations

1. **Stripe Integration**:
   - Use Stripe Checkout for simplicity
   - Or Stripe Elements for custom form
   - Store payment_intent_id on invoice

2. **Partial Payments**:
   - Decide if partial payments allowed
   - If yes, need InvoicePayment model to track multiple payments

3. **Webhook Handling**:
   - Set up Stripe webhook for payment confirmation
   - Handle failed payments gracefully

## Definition of Done

- [ ] PayInvoiceView with Stripe integration
- [ ] Pay button on invoice_detail.html (conditional on status)
- [ ] Payment processing with error handling
- [ ] Payment recorded in database
- [ ] Invoice status updated to 'paid'
- [ ] Email receipt sent
- [ ] Payment confirmation page
- [ ] Stripe webhook handling
- [ ] Tests with >95% coverage
- [ ] Manual testing with test Stripe keys
