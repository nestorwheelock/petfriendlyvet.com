# Epoch 7: Comprehensive Testing Framework

**Status**: IN PROGRESS
**Priority**: High - Quality Assurance
**Started**: 2025-12-25

---

## Overview

This epoch establishes a comprehensive testing framework that validates all application functionality through multiple testing layers: unit tests, integration tests, E2E journey tests, and Playwright browser tests.

---

## Goals

1. **Unit Test Coverage**: >95% coverage on all models, services, and utilities
2. **E2E Journey Tests**: Simulate complete user workflows via Django test client
3. **Browser Tests**: Validate actual UI rendering and JavaScript interactions
4. **QA Discovery**: Use tests to find missing functionality, not just bugs
5. **Process Improvement**: Ensure views are built with models, not after

---

## Test Architecture

```
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_models.py
│   ├── test_services.py
│   └── test_utils.py
│
├── integration/             # Integration tests (cross-component)
│   ├── test_billing_flow.py
│   ├── test_appointment_flow.py
│   └── test_order_flow.py
│
├── e2e/                     # End-to-end tests
│   ├── conftest.py          # E2E fixtures
│   ├── test_*_journey.py    # Journey tests (8 files)
│   │
│   └── browser/             # Playwright browser tests
│       ├── conftest.py      # Browser fixtures
│       └── test_*.py        # Browser tests (15+ files)
│
└── fixtures/                # Shared test data
    └── *.json
```

---

## Deliverables

### Completed

| Deliverable | Files | Tests | Status |
|-------------|-------|-------|--------|
| E2E Journey Tests | 8 files | 112 tests | DONE |
| Browser Test Infrastructure | conftest.py | - | DONE |
| Authentication Browser Tests | test_authentication.py | 20 tests | DONE |
| Appointment Browser Tests | test_appointment_booking.py | 28 tests | DONE |
| Billing Browser Tests | test_billing.py | 15 tests | DONE |
| Admin User Browser Tests | test_admin_users.py | 25 tests | DONE |
| Pet Profile Browser Tests | test_pet_profile.py | 20 tests | DONE |
| Store Browser Tests | test_store.py | 20 tests | DONE |

### In Progress

| Deliverable | Status | Notes |
|-------------|--------|-------|
| Loyalty Browser Tests | Admin only | Customer URLs missing |
| Emergency Browser Tests | Admin only | Customer URLs missing |
| Inventory Browser Tests | Admin only | Staff URLs missing |
| Referrals Browser Tests | Admin only | Staff URLs missing |
| Staff Management Tests | Admin only | Staff URLs missing |

### Planned

| Deliverable | Blocked By |
|-------------|------------|
| Full Loyalty Tests | T-075 (Loyalty URLs) |
| Full Emergency Tests | T-074 (Emergency URLs) |
| Full Inventory Tests | T-076 (Inventory URLs) |
| Full Referrals Tests | T-078 (Referrals URLs) |
| Full Staff Tests | T-077 (Practice URLs) |

---

## E2E Journey Tests

Journey tests simulate complete user workflows using Django's test client (no browser).

| Test File | Workflows Covered |
|-----------|-------------------|
| `test_appointment_journey.py` | Book → Confirm → Complete → Invoice |
| `test_billing_journey.py` | Invoice → Payment → Receipt |
| `test_clinical_notes_journey.py` | Appointment → Notes → Records |
| `test_delivery_journey.py` | Order → Delivery → Track → Complete |
| `test_emergency_journey.py` | Triage → Contact → Schedule |
| `test_inventory_journey.py` | Stock → Reorder → Receive → Track |
| `test_loyalty_journey.py` | Earn → Redeem → Tier Up |
| `test_referral_journey.py` | Create → Send → Receive → Complete |
| `test_staff_journey.py` | Clock In → Tasks → Clock Out |

**Total**: 112 journey tests

---

## Browser Tests (Playwright)

Browser tests validate actual UI rendering, JavaScript interactions, and user experience.

### Test Categories

| Category | Purpose | Auth Level |
|----------|---------|------------|
| Public | Anonymous user access | None |
| Customer | Authenticated customer flows | Login required |
| Staff | Staff dashboard operations | Staff required |
| Admin | Admin interface operations | Superuser required |

### Fixtures

```python
# Authentication fixtures
@pytest.fixture
def owner_user(db)           # Regular customer
@pytest.fixture
def staff_user(db)           # Staff member
@pytest.fixture
def admin_user(db)           # Superuser

# Authenticated page fixtures
@pytest.fixture
def authenticated_page(page, live_server, owner_user)
@pytest.fixture
def staff_page(page, live_server, staff_user)
@pytest.fixture
def admin_page(page, live_server, admin_user)

# Data fixtures
@pytest.fixture
def pet_with_owner(db, owner_user)
@pytest.fixture
def appointment_with_pet(db, pet_with_owner, staff_user)
@pytest.fixture
def invoice_for_user(db, owner_user)
```

### Test Patterns

**URL Accessibility Test**:
```python
def test_page_loads(self, authenticated_page, live_server):
    """Verify page loads without 404."""
    page = authenticated_page
    page.goto(f"{live_server.url}/path/")
    expect(page.locator('h1')).not_to_contain_text('Not Found')
    expect(page.locator('h1')).to_contain_text('Expected Title')
```

**Form Submission Test**:
```python
def test_form_submits(self, authenticated_page, live_server):
    """Verify form submission works."""
    page = authenticated_page
    page.goto(f"{live_server.url}/form/")
    page.fill('input[name="field"]', 'value')
    page.click('button[type="submit"]')
    expect(page.locator('.success')).to_be_visible()
```

**AJAX/HTMX Test**:
```python
def test_dynamic_update(self, authenticated_page, live_server):
    """Verify dynamic content updates."""
    page = authenticated_page
    page.goto(f"{live_server.url}/dynamic/")
    page.click('[data-action="update"]')
    page.wait_for_selector('.updated-content')
    expect(page.locator('.updated-content')).to_be_visible()
```

---

## QA Discovery Process

Browser tests revealed missing functionality:

| Discovery | Issue | Resolution |
|-----------|-------|------------|
| Loyalty URLs missing | `MISSING_CUSTOMER_URLS.md` | T-075 |
| Emergency URLs missing | `MISSING_CUSTOMER_URLS.md` | T-074 |
| Inventory URLs missing | `MISSING_CUSTOMER_URLS.md` | T-076 |
| Referrals URLs missing | `MISSING_CUSTOMER_URLS.md` | T-078 |
| Practice URLs empty | `MISSING_CUSTOMER_URLS.md` | T-077 |

### Lesson Learned

**Tests were passing 404 pages** because assertions only checked `expect(page.locator('body')).to_be_visible()` which is true even on error pages.

**Fix**: Always assert on expected content, not just page visibility:
```python
# BAD - passes on 404
expect(page.locator('body')).to_be_visible()

# GOOD - fails on 404
expect(page.locator('h1')).to_contain_text('Expected Title')
expect(page.locator('h1')).not_to_contain_text('Not Found')
```

---

## Process Improvements

### STORY_TO_TASK_CHECKLIST.md

New checklist ensures views are built with models:
- Models + Views in same sprint
- Browser tests planned during task creation
- URL accessibility tests for every customer path

### Browser Test Gate

Before marking any app complete:
1. Browser tests exist for all customer URLs
2. Tests verify content, not just page load
3. No 404s on any documented path

---

## Running Tests

```bash
# All tests
pytest

# E2E journey tests only
pytest tests/e2e/ -v --ignore=tests/e2e/browser/

# Browser tests only (headless)
pytest tests/e2e/browser/ -v

# Browser tests with visible browser
pytest tests/e2e/browser/ -v --headed

# Specific browser test file
pytest tests/e2e/browser/test_authentication.py -v

# With coverage
pytest --cov=apps --cov-report=html
```

---

## Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Unit test coverage | >95% | >95% |
| E2E journey tests | 112 | 150+ |
| Browser tests | 333 | 400+ |
| Customer URL coverage | 60% | 100% |
| Staff URL coverage | 40% | 100% |

---

## Dependencies

- pytest >= 8.0
- pytest-django >= 4.7
- pytest-playwright >= 0.7
- playwright >= 1.40

---

## Related Documents

- `planning/issues/MISSING_CUSTOMER_URLS.md` - QA discoveries
- `planning/STORY_TO_TASK_CHECKLIST.md` - Process fix
- `planning/SPRINT_URL_REMEDIATION.md` - Remediation plan
- `tests/e2e/browser/conftest.py` - Browser test fixtures
