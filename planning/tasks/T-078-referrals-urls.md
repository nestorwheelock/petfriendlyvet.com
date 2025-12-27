# T-078: Referrals App URLs

> **REQUIRED READING:** Before implementation, review [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)

**Story Type**: Task
**Priority**: Medium (Specialist Workflow)
**Estimate**: 5 hours
**Status**: Pending
**Discovered By**: QA Browser Tests (2025-12-25)

## Objective

Create staff and specialist-facing views and URLs for the Referrals app so staff can manage referrals efficiently and specialists can access their portal.

## Background

Browser E2E tests revealed that the Referrals app only has Django admin interfaces. Staff cannot manage referrals efficiently and specialists have no portal to:
- View all referrals
- See pending referrals requiring action
- Create new referrals
- Find specialists
- Manage inbound referrals
- View referral details

## Required URLs

| URL | View | Description |
|-----|------|-------------|
| `/referrals/` | `referral_list` | All referrals |
| `/referrals/pending/` | `pending_referrals` | Awaiting action |
| `/referrals/create/` | `create_referral` | New referral form |
| `/referrals/specialists/` | `specialist_directory` | Find specialists |
| `/referrals/inbound/` | `inbound_referrals` | Referrals TO us |
| `/referrals/<id>/` | `referral_detail` | Single referral detail |

## Deliverables

### Files to Create
- [ ] `apps/referrals/urls.py` - URL patterns
- [ ] `apps/referrals/views.py` - View functions/classes
- [ ] `templates/referrals/list.html` - All referrals list
- [ ] `templates/referrals/pending.html` - Pending referrals
- [ ] `templates/referrals/create.html` - New referral form
- [ ] `templates/referrals/specialists.html` - Specialist directory
- [ ] `templates/referrals/inbound.html` - Inbound referrals
- [ ] `templates/referrals/detail.html` - Referral detail view

### Files to Modify
- [ ] `config/urls.py` - Include referrals URLs

## Definition of Done

- [ ] All 6 URLs accessible to staff users
- [ ] Referral list shows all Referral records
- [ ] Pending view filters by status
- [ ] Create form links to Specialist and creates Referral
- [ ] Specialist directory shows Specialist records
- [ ] Inbound view shows referrals where we are the recipient
- [ ] Detail view shows full referral with ReferralDocument attachments
- [ ] Tests written with >95% coverage
- [ ] Browser tests updated to validate staff URLs
- [ ] Mobile-responsive templates

## Technical Notes

- Use existing models: `Referral`, `Specialist`, `ReferralDocument`, `VisitingAppointment`
- All views require @staff_member_required decorator
- Create form should support document uploads
- Consider status workflow: pending -> scheduled -> completed
- Detail view should show timeline of status changes

## Related

- QA Discovery: `planning/issues/MISSING_CUSTOMER_URLS.md`
- Existing models: `apps/referrals/models.py`
- Existing admin: `apps/referrals/admin.py`
