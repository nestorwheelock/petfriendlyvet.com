# Sprint: URL Remediation

**Purpose**: Implement missing customer/staff-facing URLs discovered by QA
**Created**: 2025-12-25
**Priority**: High - Core functionality missing
**Estimated Effort**: 25 hours total

---

## Background

Browser E2E tests discovered that 5 apps have models and admin interfaces but no customer/staff-facing URLs. Users cannot access core functionality through the frontend.

**Discovery Document**: `planning/issues/MISSING_CUSTOMER_URLS.md`

---

## Sprint Goals

1. Implement customer-facing URLs for Emergency and Loyalty apps
2. Implement staff-facing URLs for Inventory, Practice, and Referrals apps
3. Create missing wireframe for Staff Dashboard
4. Update browser tests to validate new URLs
5. Prevent future gaps via process improvement

---

## Task Summary

| Task | App | Type | Priority | Estimate | Wireframe |
|------|-----|------|----------|----------|-----------|
| T-074 | Emergency | Customer | Critical | 4h | 17-emergency-triage.txt |
| T-075 | Loyalty | Customer | High | 5h | 20-loyalty-program.txt |
| T-076 | Inventory | Staff | High | 6h | 14-inventory-admin.txt |
| T-077 | Practice | Staff | Medium | 5h | **NEEDS CREATION** |
| T-078 | Referrals | Staff | Medium | 5h | 18-referral-network.txt |

**Total**: 25 hours

---

## Implementation Order

### Phase 1: Critical (Safety)

#### T-074: Emergency Customer URLs (4 hours)

**Wireframe**: `planning/wireframes/17-emergency-triage.txt`

**URLs to Create**:
```
/emergency/           → Emergency info, phone, hours
/emergency/contact/   → Report symptoms, request callback
/emergency/triage/    → Self-triage questionnaire
/emergency/hospitals/ → 24-hour hospitals nearby
```

**Files**:
- `apps/emergency/urls.py` (create)
- `apps/emergency/views.py` (create)
- `templates/emergency/*.html` (4 templates)

**Dependencies**: None (uses existing models)

---

### Phase 2: High Priority (Customer Engagement)

#### T-075: Loyalty Customer URLs (5 hours)

**Wireframe**: `planning/wireframes/20-loyalty-program.txt`

**URLs to Create**:
```
/loyalty/           → Points balance, tier, activity
/loyalty/rewards/   → Available rewards catalog
/loyalty/history/   → Transaction history
/loyalty/tiers/     → Tier benefits info
/loyalty/referrals/ → Referral link and stats
```

**Files**:
- `apps/loyalty/urls.py` (create)
- `apps/loyalty/views.py` (create)
- `templates/loyalty/*.html` (5 templates)

**Dependencies**: Requires authenticated user

---

### Phase 3: High Priority (Operations)

#### T-076: Inventory Staff URLs (6 hours)

**Wireframe**: `planning/wireframes/14-inventory-admin.txt`

**URLs to Create**:
```
/inventory/                 → Stock dashboard
/inventory/alerts/          → Low stock alerts
/inventory/purchase-orders/ → PO management
/inventory/batches/         → Batch tracking
/inventory/expiring/        → Expiring items
/inventory/movements/       → Movement log
/inventory/suppliers/       → Supplier directory
```

**Files**:
- `apps/inventory/urls.py` (create)
- `apps/inventory/views.py` (create)
- `templates/inventory/*.html` (7 templates)

**Dependencies**: Requires staff permission

---

### Phase 4: Medium Priority (Internal)

#### T-077: Practice Staff URLs (5 hours)

**Wireframe**: **NEEDS CREATION** → `planning/wireframes/23-staff-dashboard.txt`

**URLs to Create**:
```
/staff/dashboard/ → Today's schedule, tasks
/staff/schedule/  → Shift calendar
/staff/timeclock/ → Clock in/out
/staff/timesheet/ → Hours worked
/staff/tasks/     → Assigned tasks
```

**Files**:
- `apps/practice/urls.py` (update - exists but empty)
- `apps/practice/views.py` (create)
- `templates/practice/*.html` (5 templates)

**Pre-requisite**: Create wireframe first

---

#### T-078: Referrals Staff URLs (5 hours)

**Wireframe**: `planning/wireframes/18-referral-network.txt`

**URLs to Create**:
```
/referrals/             → All referrals
/referrals/pending/     → Awaiting action
/referrals/create/      → New referral form
/referrals/specialists/ → Specialist directory
/referrals/inbound/     → Referrals to us
/referrals/<id>/        → Referral detail
```

**Files**:
- `apps/referrals/urls.py` (create)
- `apps/referrals/views.py` (create)
- `templates/referrals/*.html` (6 templates)

**Dependencies**: Requires staff permission

---

## Acceptance Criteria

### Per-Task Criteria
- [ ] All URLs accessible (no 404s)
- [ ] Proper authentication/permission checks
- [ ] Templates render correctly
- [ ] Mobile-responsive design
- [ ] Tests pass with >95% coverage
- [ ] Browser tests validate URLs

### Sprint Completion Criteria
- [ ] All 5 apps have working customer/staff URLs
- [ ] Browser tests pass for all new URLs
- [ ] No 404 errors on customer-facing paths
- [ ] Documentation updated
- [ ] Process checklist in place for future sprints

---

## Test Plan

### Browser Tests to Update

| Test File | New Tests |
|-----------|-----------|
| `tests/e2e/browser/test_emergency.py` | Test customer URLs load |
| `tests/e2e/browser/test_loyalty.py` | Test customer URLs load |
| `tests/e2e/browser/test_inventory.py` | Test staff URLs load |
| `tests/e2e/browser/test_staff_management.py` | Test practice URLs load |
| `tests/e2e/browser/test_referrals.py` | Test staff URLs load |

### Test Pattern
```python
def test_[page]_loads(self, authenticated_page, live_server):
    """Verify [page] loads without 404."""
    page = authenticated_page
    page.goto(f"{live_server.url}/[app]/[path]/")
    # Verify NOT a 404
    expect(page.locator('h1')).not_to_contain_text('Not Found')
    # Verify expected content
    expect(page.locator('h1')).to_contain_text('[Expected Title]')
```

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Missing models/fields | Verify models exist before starting |
| Template styling mismatch | Follow existing base template patterns |
| Permission issues | Use consistent decorators (@staff_member_required) |
| Scope creep | Stick to URL/view creation only, no new features |

---

## Definition of Done

- [ ] All 5 task documents completed (T-074 through T-078)
- [ ] All URLs implemented and accessible
- [ ] Browser tests pass (no 404s)
- [ ] Code reviewed and committed
- [ ] `STORY_TO_TASK_CHECKLIST.md` added to prevent future gaps
- [ ] Sprint retrospective completed

---

## Related Documents

- `planning/issues/MISSING_CUSTOMER_URLS.md` - Original QA discovery
- `planning/STORY_TO_TASK_CHECKLIST.md` - Process fix
- `planning/tasks/T-074-*.md` through `T-078-*.md` - Individual tasks
- `planning/wireframes/` - Visual layouts
