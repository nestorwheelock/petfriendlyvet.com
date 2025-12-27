# T-083: Add Dev Navigation Sections to All Module Dashboards

> **REQUIRED READING:** Before implementation, review [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)

## AI Coding Brief
**Role**: Frontend Developer
**Objective**: Add temporary dev navigation sections to all module dashboards showing all available URLs
**User Request**: "let's do the same for the other modules" (referring to dev navigation sections)

### Context
Already implemented dev navigation sections for:
- Inventory Dashboard
- Practice Dashboard

Need to add similar sections to:
- CRM Dashboard
- Accounting Dashboard
- Reports Dashboard
- Pets Dashboard
- Loyalty Dashboard
- Referrals Dashboard
- Email Marketing Dashboard
- Audit Dashboard
- Superadmin Dashboard

### Constraints
**Allowed File Paths**:
- templates/*/dashboard.html

**Forbidden Paths**: None

### Deliverables
- [x] CRM Dashboard dev section
- [x] Accounting Dashboard dev section
- [x] Reports Dashboard dev section
- [x] Pets Dashboard - SKIPPED (customer portal, not staff)
- [x] Loyalty Dashboard - SKIPPED (customer portal, not staff)
- [x] Referrals Dashboard dev section
- [x] Email Marketing Dashboard dev section
- [x] Audit Dashboard dev section
- [x] Superadmin Dashboard dev section

### Definition of Done
- [x] All module dashboards have dev navigation sections
- [x] All URLs for each module are listed
- [x] Sections are styled consistently (yellow dashed border, TEMPORARY badge)
- [x] Links use correct staff_token URL pattern (or /superadmin/ for superadmin)
- [x] No broken links - also fixed existing {% url %} tags that caused 404s

### Test Cases
Manual verification:
- Each dashboard loads without errors
- All links in dev sections work correctly

### Notes
- These are temporary dev sections for easier navigation during development
- Should be removed before production deployment
- Use consistent styling across all modules
