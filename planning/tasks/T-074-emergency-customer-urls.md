# T-074: Emergency App Customer-Facing URLs

> **REQUIRED READING:** Before implementation, review [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)

**Story Type**: Task
**Priority**: Critical (Safety-related)
**Estimate**: 4 hours
**Status**: Pending
**Discovered By**: QA Browser Tests (2025-12-25)

## Objective

Create customer-facing views and URLs for the Emergency app so pet owners can access emergency information, contact forms, and triage tools without needing admin access.

## Background

Browser E2E tests revealed that the Emergency app only has Django admin interfaces. Pet owners cannot:
- View emergency contact information
- Submit emergency contact forms
- Use self-triage questionnaires
- Find nearby 24-hour hospitals

## Required URLs

| URL | View | Description |
|-----|------|-------------|
| `/emergency/` | `emergency_info` | Emergency phone, hours, what to do |
| `/emergency/contact/` | `emergency_contact_form` | Report symptoms, request callback |
| `/emergency/triage/` | `triage_questionnaire` | Self-triage questions |
| `/emergency/hospitals/` | `referral_hospitals` | 24-hour hospitals nearby |

## Deliverables

### Files to Create
- [ ] `apps/emergency/urls.py` - URL patterns
- [ ] `apps/emergency/views.py` - View functions/classes
- [ ] `templates/emergency/info.html` - Main info page
- [ ] `templates/emergency/contact_form.html` - Contact form
- [ ] `templates/emergency/triage.html` - Triage questionnaire
- [ ] `templates/emergency/hospitals.html` - Hospital directory

### Files to Modify
- [ ] `config/urls.py` - Include emergency URLs

## Definition of Done

- [ ] All 4 URLs accessible to anonymous users
- [ ] Emergency info page displays current on-call information
- [ ] Contact form submits and creates EmergencyContact record
- [ ] Triage questionnaire uses EmergencySymptom model
- [ ] Hospital list shows EmergencyReferral hospitals
- [ ] Tests written with >95% coverage
- [ ] Browser tests updated to validate customer URLs
- [ ] Mobile-responsive templates

## Technical Notes

- Use existing models: `EmergencyContact`, `OnCallSchedule`, `EmergencySymptom`, `EmergencyReferral`
- Contact form should trigger notification to on-call staff
- Triage should integrate with symptom severity levels
- Hospital list should show distance if location available

## Related

- QA Discovery: `planning/issues/MISSING_CUSTOMER_URLS.md`
- Existing models: `apps/emergency/models.py`
- Existing admin: `apps/emergency/admin.py`
