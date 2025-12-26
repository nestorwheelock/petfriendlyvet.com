# B-083: Footer Shows for Staff and Superadmin Users

**Severity**: Medium
**Affected Component**: templates/base layouts
**Discovered**: 2025-12-26

## Bug Description

The public website footer shows when logged in as staff or superadmin users. These users should see only the app interface (sidebar + content area) without the public-facing footer, since they are inside the application, not browsing the public website.

## Steps to Reproduce

1. Log in as a staff user
2. Navigate to any staff page (e.g., `/staff/dashboard/`)
3. Observe: Public website footer appears below the staff app content

Or:

1. Log in as a superadmin user
2. Navigate to any superadmin page (e.g., `/superadmin/`)
3. Observe: Public website footer appears below the superadmin app content

## Expected Behavior

- **Public pages** (home, services, about, contact): Footer SHOULD show
- **Customer portal** (logged in customers): Footer SHOULD show
- **Staff/superadmin using profile switcher to customer view**: Footer SHOULD show
- **Staff pages**: Footer should NOT show (app has its own sidebar layout)
- **Superadmin pages**: Footer should NOT show (app has its own sidebar layout)

## Actual Behavior

Footer shows on all pages including staff and superadmin areas where it doesn't belong.

## Root Cause

In `templates/base.html`, the footer is included unconditionally outside the `{% block content %}`:

```html
<!-- Main Content -->
<main id="main-content" class="flex-grow">
    {% block content %}{% endblock %}
</main>

<!-- Footer -->
{% include "components/footer.html" %}
```

Both `base_staff.html` and `base_superadmin.html` extend `base.html` and override only `{% block content %}`. They don't override or suppress the footer include.

## Proposed Fix

Option A: Create a `{% block footer %}` wrapper in `base.html` that staff/superadmin templates can override to empty.

Option B: Conditionally include footer based on user role/template context variable.

Option C: Have staff/superadmin not extend `base.html` directly, but create their own independent base templates.

**Recommended**: Option A - Wrap footer in a block:

```html
<!-- base.html -->
{% block footer %}
{% include "components/footer.html" %}
{% endblock %}
```

```html
<!-- base_staff.html and base_superadmin.html -->
{% block footer %}{% endblock %}
```

## Files Affected

- `templates/base.html`
- `templates/base_staff.html`
- `templates/base_superadmin.html`

## Definition of Done

- [x] Footer wrapped in `{% block footer %}` in base.html
- [x] Staff template overrides footer block to empty
- [x] Superadmin template overrides footer block to empty
- [x] Customer portal still shows footer (if using base_portal.html)
- [x] Public pages still show footer
- [ ] Manual verification in browser for all user types

## Implementation Details

**Files Modified:**
- `templates/base.html` - Wrapped footer include in `{% block footer %}...{% endblock %}`
- `templates/base_staff.html` - Added `{% block footer %}{% endblock %}` to suppress footer
- `templates/base_superadmin.html` - Added `{% block footer %}{% endblock %}` to suppress footer

**Tests Added:**
- `tests/test_footer_visibility.py` - 9 tests covering:
  - Footer shows on public pages (home, services, about, contact)
  - Footer shows for logged-in customers
  - Footer hidden on staff hub
  - Footer hidden on superadmin pages (dashboard, users, settings)
