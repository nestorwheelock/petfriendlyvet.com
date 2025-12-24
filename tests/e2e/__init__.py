"""End-to-end tests for the Pet-Friendly Vet application.

These tests exercise the full application stack through actual interfaces
(Django views, REST APIs) rather than direct database manipulation.

Test Categories:
- Order flows: Checkout → Invoice → Payment
- Appointment flows: Booking → Completion → Invoice → Payment
- Delivery lifecycle: Order → Delivery → Driver updates → Proof → Rating
- Staff workflows: Customer notes, interactions, tags
- CRM operations: Follow-ups, reminders, reports
"""
