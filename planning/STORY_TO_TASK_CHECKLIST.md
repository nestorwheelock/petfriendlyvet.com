# Story-to-Task Breakdown Checklist (MANDATORY)

**Purpose**: Ensure ALL user-facing functionality is built during initial development, not discovered as missing during QA.

**Created**: 2025-12-25
**Reason**: QA discovered multiple apps with models/admin but no customer-facing URLs (see `planning/issues/MISSING_CUSTOMER_URLS.md`)

---

## CRITICAL RULE

**Build views WITH models, not after.**

When creating any Django app, the MINIMUM deliverables are:
1. `models.py` - Data layer
2. `admin.py` - Admin interface
3. `urls.py` - URL patterns (NEVER skip this)
4. `views.py` - View functions (NEVER skip this)
5. `templates/` - HTML templates (NEVER skip this)

**Browser tests should find BUGS in views, not MISSING views.**

---

## Task Creation Rule: Models + Views Together

**NEVER create a model task without a corresponding views task in the SAME sprint.**

### Correct Pattern:
```
Sprint N:
  T-XXX: [App] Models           ← Data layer
  T-XXX: [App] Admin            ← Admin interface
  T-XXX: [App] Views & URLs     ← Customer/staff views (SAME SPRINT)
  T-XXX: [App] Templates        ← HTML templates (SAME SPRINT)
```

### Incorrect Pattern (What We Did - DO NOT REPEAT):
```
Sprint 1:
  T-XXX: [App] Models           ← Built
  T-XXX: [App] Admin            ← Built

Sprint 2: (or never)
  T-XXX: [App] Views & URLs     ← Forgotten!
  T-XXX: [App] Templates        ← Forgotten!
```

---

## Mandatory Task Categories

When breaking down ANY user story, ensure tasks exist for ALL applicable categories:

### 1. Data Layer (Backend)
- [ ] **Models** - Database schema, fields, relationships
- [ ] **Migrations** - Schema changes applied
- [ ] **Signals** - Post-save automation (invoices, notifications)
- [ ] **Services** - Business logic layer

### 2. Admin Interface
- [ ] **Admin classes** - ModelAdmin registration
- [ ] **Admin actions** - Bulk operations
- [ ] **Inline models** - Related object editing

### 3. Customer-Facing URLs (CRITICAL - Previously Missed)
- [ ] **urls.py** - URL patterns for customer views
- [ ] **views.py** - View functions/classes
- [ ] **Templates** - HTML templates for each view
- [ ] **Forms** - Django forms for user input

### 4. Staff-Facing URLs (If applicable)
- [ ] **Staff dashboard** - Overview/summary views
- [ ] **Staff actions** - Management interfaces
- [ ] **Staff templates** - Staff-specific UI

### 5. API Layer (If applicable)
- [ ] **Serializers** - API data formatting
- [ ] **ViewSets/APIViews** - API endpoints
- [ ] **Permissions** - Access control

### 6. Testing
- [ ] **Unit tests** - Model/service logic
- [ ] **Integration tests** - Cross-component flows
- [ ] **Browser tests** - Customer URL accessibility
- [ ] **API tests** - Endpoint validation

### 7. Documentation
- [ ] **Wireframes** - Visual layouts (before implementation)
- [ ] **API docs** - Endpoint documentation
- [ ] **User guide** - How to use the feature

---

## URL Checklist Template

For EVERY app with user interaction, explicitly answer:

```markdown
### [App Name] URL Checklist

**Customer URLs Required?** YES / NO
If YES, list URLs:
| URL Pattern | View Name | Template | Task # |
|-------------|-----------|----------|--------|
| /[app]/ | dashboard | [app]/dashboard.html | T-XXX |
| /[app]/[action]/ | [action] | [app]/[action].html | T-XXX |

**Staff URLs Required?** YES / NO
If YES, list URLs:
| URL Pattern | View Name | Template | Task # |
|-------------|-----------|----------|--------|
| /staff/[app]/ | staff_dashboard | [app]/staff_dashboard.html | T-XXX |

**API Endpoints Required?** YES / NO
If YES, list endpoints:
| Endpoint | Method | Serializer | Task # |
|----------|--------|------------|--------|
| /api/[app]/ | GET, POST | [Model]Serializer | T-XXX |
```

---

## Pre-Sprint Validation

Before starting any sprint, verify:

1. **Every user story has explicit URL tasks**
   - Not just "models" and "admin"
   - Customer-facing views are separate tasks

2. **Wireframes exist for all customer pages**
   - Created BEFORE implementation
   - Approved by stakeholder

3. **Browser tests are planned**
   - Test files created (can be empty stubs)
   - URL accessibility tests defined

---

## Red Flags to Watch For

These patterns indicate missing work:

| Red Flag | What's Missing |
|----------|----------------|
| `apps/X/models.py` exists but no `apps/X/urls.py` | Customer URLs |
| `apps/X/admin.py` exists but no `apps/X/views.py` | Customer views |
| Wireframe exists but no corresponding templates | Implementation |
| User story says "user can..." but no browser test | E2E validation |

---

## Example: Correct Task Breakdown

**User Story**: "As a customer, I want to view my loyalty points"

### Incorrect (What we did):
- T-054: Loyalty Models ✅
- T-055: Loyalty Admin ✅
- (Missing customer views!)

### Correct (What we should do):
- T-054: Loyalty Models
- T-055: Loyalty Admin
- T-056: **Loyalty Customer URLs** (`/loyalty/`, `/loyalty/rewards/`, etc.)
- T-057: **Loyalty Templates** (dashboard.html, rewards.html, etc.)
- T-058: **Loyalty Browser Tests** (verify customer can access pages)

---

## Enforcement

1. **Story Review Gate**: Before approving any user story, verify URL tasks exist
2. **Sprint Planning**: Use this checklist during task breakdown
3. **QA Validation**: Browser tests must verify ALL customer URLs load (not 404)

---

## Related Documents

- `planning/issues/MISSING_CUSTOMER_URLS.md` - Current gaps discovered
- `planning/tasks/T-074-*.md` through `T-078-*.md` - Remediation tasks
- `planning/wireframes/` - Visual layouts for implementation
