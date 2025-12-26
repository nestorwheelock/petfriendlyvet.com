# CRUD Gap Analysis Summary

**Date**: 2025-12-25
**Reviewed By**: Claude Code

## Overview

Comprehensive audit of customer portal CRUD (Create, Read, Update, Delete) functionality across 8 modules identified 6 HIGH priority gaps and several MEDIUM/LOW priority enhancements.

---

## HIGH Priority Bugs (New)

| Bug ID | Module | Gap | Impact |
|--------|--------|-----|--------|
| B-050 | Pets | Delete/Archive pet | Users stuck with inactive/deceased pets |
| B-051 | Appointments | Reschedule appointments | Must cancel & rebook to change time |
| B-052 | Store | Cancel orders | No self-service order cancellation |
| B-053 | Billing | Pay invoices | Cannot pay invoices online |
| B-054 | Pharmacy | Cancel refill requests | Cannot stop unwanted refills |
| B-055 | Accounts | Change email address | Email locked after registration |
| B-056 | Pets | Photo upload 500 + management | Cannot upload/remove/manage pet photos |

---

## Correlation with Error Tracker (apps/error_tracking)

### Direct Correlations Found

| Error Tracker | Status | Related CRUD Gap | Notes |
|---------------|--------|------------------|-------|
| B-047 | resolved | Portal 500 error | **FIXED** - was template URL issue (order_number vs pk) |
| B-031 | open | /en/pets/add/ 500 | **B-056** - Pet photo upload causing 500 error |
| B-049 | open | /en/pets/{id}/edit/ 500 | **B-056** - Same photo upload issue on edit |
| B-034 | open | /en/pets/dashboard/ 404 | Pets dashboard routing issue |

### No Direct Correlation (CRUD gaps are missing features, not errors)

The CRUD gaps (B-050 through B-055) are **missing functionality**, not runtime errors. They won't appear in the error tracker because:
- No 404/500 errors occur - the routes simply don't exist
- Users don't see error pages - they see no action buttons
- These are feature gaps, not bugs in existing code

### Error Tracker Bugs to Resolve

```
Status: wontfix (intended behavior)
- B-010: /delivery/zones/ - Staff only
- B-011: /reports/ - Staff only
- B-023: /delivery/driver/dashboard/ - Driver only
- B-009: /delivery/ - Staff only
- B-005: /dashboard - Deprecated route
- B-013: /delivery - Missing trailing slash
- B-012: /chat/ - POST only endpoint

Status: open (need investigation)
- B-031: Server Error on /en/pets/add/ - Form error?
- B-048: Method Not Allowed /accounts/logout/ - Should be POST
- B-037: Server Error on /delivery/ - Staff access issue?
- B-033: Not Found /es/ - Language routing
- B-030: Not Found /en/dashboard - Deprecated
- B-047: Server Error /portal/ - FIXED
- B-046: Not Found /portal - Missing trailing slash
- B-035: Method Not Allowed /en/chat/ - POST only
- B-034: Not Found /en/pets/dashboard/ - Routing issue
```

---

## MEDIUM Priority Gaps (Not Filed as Bugs)

These are enhancements that would improve UX but are not critical:

| Module | Gap | Recommendation |
|--------|-----|----------------|
| Pets | Edit document metadata | Add DocumentUpdateView |
| Pets | Update medical records | Add forms if vet allows |
| Appointments | Update notes after booking | Add AppointmentUpdateView |
| Appointments | Capture cancellation reason | Update CancelView |
| Store | Clear entire cart | Add clear_cart endpoint |
| Store | Modify order details | Add OrderUpdateView |
| Billing | Download invoice PDF | Add PDF generation |
| Billing | Show payment history | Enhance invoice detail |
| Loyalty | Cancel redemptions | Add RedemptionCancelView |
| Pharmacy | Update refill notes | Add RefillUpdateView |
| Emergency | Delete old contacts | Add privacy controls |
| Accounts | Profile photo upload | Add avatar support |
| Accounts | Address management | Add saved addresses |

---

## Implementation Priority

### Phase 1: Critical Path (Immediate)
1. **B-053**: Invoice Payment - Revenue impact
2. **B-052**: Order Cancellation - Customer service impact
3. **B-051**: Appointment Reschedule - High frequency need

### Phase 2: User Experience (Next Sprint)
4. **B-050**: Pet Archive - Quality of life
5. **B-054**: Refill Cancellation - Pharmacy efficiency
6. **B-055**: Email Change - Account management

### Phase 3: Enhancements (Backlog)
- MEDIUM priority items above

---

## Files Created

```
planning/bugs/
├── B-050-missing-pet-delete-archive.md
├── B-051-missing-appointment-reschedule.md
├── B-052-missing-order-cancellation.md
├── B-053-missing-invoice-payment.md
├── B-054-missing-refill-cancellation.md
├── B-055-missing-email-change.md
├── B-056-pet-photo-upload-issues.md
└── CRUD-GAP-SUMMARY.md (this file)
```

---

## Next Steps

1. Review and prioritize with stakeholders
2. Create user stories for approved bugs
3. Add to sprint planning
4. Implement following TDD workflow
5. Update error tracker status for resolved issues
