# S-080: Profile Icon Portal Routing

> **REQUIRED READING:** Before implementation, review [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)

**Story Type**: User Story
**Priority**: High
**Estimate**: 1 day
**Sprint**: Current
**Status**: COMPLETED ✅

---

## User Story

**As a** logged-in user (customer, staff, or superadmin)
**I want to** click my profile icon and be routed to the appropriate portal based on my role
**So that** I can quickly access my dashboard without navigating through menus

---

## Problem Statement

Currently, clicking the profile icon in the navigation does not provide role-aware routing:
- Customers should go directly to their customer portal dashboard
- Staff members should go to the staff portal, with an option to access the customer portal
- Superadmins should have a choice between admin portal, staff portal, and customer portal

This creates a confusing UX where users must manually navigate to their appropriate dashboard.

---

## Acceptance Criteria

### AC-1: Customer Portal Routing
- [x] When a customer (non-staff, non-superuser) clicks the profile icon
- [x] They see dropdown with customer portal dashboard link
- [x] The dropdown menu shows: My Dashboard, Profile, Logout

### AC-2: Staff Portal Routing
- [x] When a staff member (is_staff=True, is_superuser=False) clicks the profile icon
- [x] The dropdown menu shows portal options:
  - Staff Portal → `/practice/dashboard/`
  - Customer Portal → `/portal/`
  - Profile, Logout
- [x] Staff sees both portal options

### AC-3: Superadmin Portal Routing
- [x] When a superadmin (is_superuser=True) clicks the profile icon
- [x] The dropdown menu shows all portal options:
  - Admin Dashboard → `/superadmin/`
  - Staff Portal → `/practice/dashboard/`
  - Customer Portal → `/portal/`
  - Profile, Logout
- [x] Superadmin sees all three portals

### AC-4: Visual Distinction
- [x] Each portal option has a distinct icon (shield/building/home)
- [x] Icons are color-coded (red/blue/green)
- [x] Role badge visible in dropdown (e.g., "ADMIN", "STAFF", "CUSTOMER")

### AC-5: Mobile Responsive
- [x] Dropdown works correctly on mobile devices
- [x] Touch-friendly tap targets via Alpine.js

---

## Technical Approach

### Components to Modify

1. **`templates/components/navbar.html`** (or equivalent header component)
   - Update profile dropdown to be role-aware
   - Add portal switching options based on user.is_staff and user.is_superuser

2. **`apps/core/context_processors.py`**
   - Ensure `is_superadmin`, `is_staff` flags available in templates
   - Add `default_portal_url` based on user role

3. **Template Logic**
   ```django
   {% if user.is_superuser %}
     <!-- Show Admin, Staff, Customer options -->
   {% elif user.is_staff %}
     <!-- Show Staff, Customer options -->
   {% else %}
     <!-- Show Customer options only -->
   {% endif %}
   ```

### URLs
- Customer Portal: `/portal/` (existing)
- Staff Portal: `/practice/dashboard/` (existing)
- Admin Portal: `/superadmin/` (existing)

---

## Out of Scope

- [ ] Role switching (becoming a different user type)
- [ ] Portal preference persistence (always show same portal)
- [ ] Deep linking to specific portal pages from dropdown

---

## Wireframe

```
┌─────────────────────────────────────────────────┐
│  [Logo]     Navigation            [Profile ▼]  │
└─────────────────────────────────────────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │  ┌─────────────────────────┐  │
                    │  │ 👤 admin@example.com    │  │
                    │  │    SUPERADMIN           │  │
                    │  └─────────────────────────┘  │
                    │  ─────────────────────────────│
                    │  🛡️  Admin Dashboard        │  │
                    │  📋  Staff Portal            │  │
                    │  🏠  Customer Portal         │  │
                    │  ─────────────────────────────│
                    │  👤  Profile                 │  │
                    │  ⚙️   Settings               │  │
                    │  🚪  Logout                  │  │
                    └───────────────────────────────┘
```

---

## Definition of Done

- [x] All acceptance criteria met
- [x] Tests written for each user role scenario (11 tests in test_profile_portal_routing.py)
- [x] Works on desktop and mobile
- [x] No JavaScript errors in console
- [x] Accessibility: keyboard navigation works (Alpine.js handles this)
- [x] Code reviewed
- [x] Documentation updated

---

## Test Scenarios

| Test | User Type | Expected Behavior |
|------|-----------|-------------------|
| T1 | Customer | Dropdown shows Customer options only |
| T2 | Staff | Dropdown shows Staff + Customer options |
| T3 | Superadmin | Dropdown shows Admin + Staff + Customer options |
| T4 | Anonymous | Profile icon not shown (login button instead) |
| T5 | Mobile | Dropdown renders correctly on small screens |

---

## Risks & Assumptions

**Assumptions:**
- User roles are correctly set (is_staff, is_superuser flags)
- All three portals exist and are functional
- Users have appropriate permissions for each portal

**Risks:**
- Staff accessing customer portal may see limited data (their own pets only)
- Superadmin in customer portal may have confusing experience

---

## 🚦 CLIENT APPROVAL GATE #1 (MANDATORY)

**Before implementation begins, client must approve:**

- [ ] User story accurately describes the desired behavior
- [ ] Acceptance criteria are complete and correct
- [ ] Technical approach is acceptable
- [ ] Out of scope items are agreed upon
- [ ] Wireframe reflects expected design

### Approval

```
═══════════════════════════════════════
CLIENT APPROVAL - SPEC PHASE
═══════════════════════════════════════
Story: S-080 - Profile Icon Portal Routing
Date: _______________

I have reviewed and approve:
□ User Story & Problem Statement
□ Acceptance Criteria
□ Technical Approach
□ Wireframe
□ Out of Scope items

I authorize development to proceed.

CLIENT SIGNATURE: ________________
DATE: ___________________________
═══════════════════════════════════════
```

---

## Related

- **Depends On**: S-079 (Audit Logging), Superadmin Control Panel
- **Related To**: Navigation context processor
- **Blocks**: None
