# T-080: Implement Profile Icon Portal Routing

> **REQUIRED READING:** Before implementation, review [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)

**Related Story**: S-080
**Estimate**: 4 hours
**Status**: Completed ✅
**Dependencies**: None

## Objective

Implement role-aware profile dropdown that routes users to appropriate portals based on their role (customer, staff, superadmin).

## Deliverables

1. **Update navbar profile dropdown** to show role-specific portal options
2. **Add context processor data** for default portal URL
3. **Write tests** for all role scenarios
4. **Ensure mobile responsiveness**

## Implementation Steps

### Step 1: Write Tests First (TDD)
- [x] Test customer sees only customer portal option
- [x] Test staff sees staff + customer portal options
- [x] Test superadmin sees all three portal options
- [x] Test anonymous user sees login button (no profile)

### Step 2: Update Context Processor
- [x] Add `default_portal_url` based on user role (handled in template)
- [x] Ensure `is_superadmin` flag available (via user.is_superuser)

### Step 3: Update Navbar Template
- [x] Modify profile dropdown for role-aware options
- [x] Add portal icons and role badge
- [x] Ensure accessibility (keyboard nav via Alpine.js)

### Step 4: Test Mobile Responsiveness
- [x] Verify dropdown works on mobile (Alpine.js responsive)
- [x] Touch-friendly tap targets

## Definition of Done

- [x] All tests passing (11 tests)
- [x] Works for customer, staff, superadmin roles
- [x] Mobile responsive
- [x] No console errors
- [x] Code reviewed
