# S-002: Appointment Booking System

**Story Type:** User Story
**Priority:** High
**Estimate:** 4 days
**Sprint:** Sprint 1
**Status:** PENDING

## User Story

**As a** pet owner
**I want to** request a veterinary appointment online
**So that** I don't have to call during business hours and can book at my convenience

## Acceptance Criteria

- [ ] When I click "Book Appointment", I see an appointment request form
- [ ] When I fill out the form, I can select service type, preferred date/time, and provide pet info
- [ ] When I submit the form, I receive a confirmation message
- [ ] When I submit the form, the clinic receives an email notification
- [ ] When the clinic confirms my appointment, I receive an email confirmation

## Form Fields

### Required
- Owner name
- Email address
- Phone number (WhatsApp preferred)
- Pet name
- Pet type (Dog, Cat, Bird, Other)
- Service type (dropdown: Consultation, Vaccination, Surgery, Emergency, Other)
- Preferred date
- Preferred time slot (Morning, Afternoon, specific times TBD)
- Reason for visit (text area)

### Optional
- Pet age
- Pet breed
- Existing client? (Yes/No)
- Additional notes

## Workflow

1. Customer submits appointment request
2. System sends confirmation email to customer
3. System sends notification to clinic admin
4. Admin reviews request in Django admin
5. Admin confirms/reschedules via admin interface
6. System sends confirmation email to customer with final details

## Definition of Done

- [ ] Appointment request form implemented
- [ ] Form validation (required fields, email format, future dates only)
- [ ] Database model for appointments
- [ ] Django admin interface for managing appointments
- [ ] Email notifications (customer confirmation, admin notification)
- [ ] Appointment status workflow (Pending, Confirmed, Completed, Cancelled)
- [ ] Bilingual form and emails
- [ ] Tests written and passing (>95% coverage)
- [ ] Documentation updated

## Technical Notes

- Use Django forms with HTMX for dynamic validation
- Email via Django's email backend (configure SMTP)
- Consider calendar integration in future version
- Admin should be able to view appointments by date
