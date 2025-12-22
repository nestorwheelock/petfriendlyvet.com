# Coding Standards & Rules

**IMPORTANT:** All tasks and user stories MUST follow these standards. Reference this document before starting any implementation work.

---

## Quick Reference Checklist

Before writing ANY code, verify:

- [ ] **TDD**: Writing test FIRST? (Red → Green → Refactor)
- [ ] **Architecture**: Code in correct location? (packages/ vs apps/website/)
- [ ] **Imports**: Using `apps.get_model()` for cross-package models?
- [ ] **Services**: Public API in `services.py`, not direct model access?
- [ ] **Tests**: >95% coverage target?

---

## 1. Test-Driven Development (TDD) Rules

### The TDD Cycle (MANDATORY)

```
1. RED    → Write a failing test first
2. GREEN  → Write minimal code to pass the test
3. REFACTOR → Clean up while keeping tests green
4. REPEAT
```

### TDD Enforcement

**NEVER write implementation code before tests.**

```python
# CORRECT ORDER:
# 1. Write test
def test_appointment_can_be_created():
    appointment = Appointment.objects.create(...)
    assert appointment.id is not None

# 2. Run test - it FAILS (Red)
# 3. Write minimal code to pass
# 4. Run test - it PASSES (Green)
# 5. Refactor if needed
```

### Test Coverage Requirements

| Type | Minimum Coverage |
|------|------------------|
| Models | 95% |
| Views | 95% |
| Services | 95% |
| API Endpoints | 95% |
| Overall Project | 95% |

### Test File Structure

```
packages/appointments/
└── tests/
    ├── __init__.py
    ├── test_models.py      # Model tests
    ├── test_views.py       # View tests
    ├── test_services.py    # Service layer tests
    ├── test_forms.py       # Form tests
    └── test_api.py         # API endpoint tests
```

---

## 2. Architecture Rules (ADR-001)

### Package Boundaries

**See:** [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md) for full context.

### Rule 1: No Cross-Package Internal Imports

```python
# ❌ BAD - Direct import from another package
from packages.crm_lite.models import Owner
from packages.vet_clinic.models import Pet

# ✅ GOOD - Use Django's get_model for loose coupling
from django.apps import apps
Owner = apps.get_model('crm_lite', 'Owner')
Pet = apps.get_model('vet_clinic', 'Pet')
```

### Rule 2: Use Service Interfaces

```python
# ❌ BAD - Direct model manipulation from another package
from packages.appointments.models import Appointment
appointment = Appointment.objects.create(...)

# ✅ GOOD - Use the service interface
from packages.appointments.services import AppointmentService
appointment = AppointmentService.create_appointment(...)
```

### Rule 3: Code Location

| Code Type | Location | Example |
|-----------|----------|---------|
| Reusable/Generic | `packages/<name>/` | Appointment booking logic |
| Pet-Friendly Specific | `apps/website/` | Dr. Pablo's custom workflows |
| Project Config | `config/` | Settings, URLs, WSGI |

```python
# packages/appointments/services.py - GENERIC
class AppointmentService:
    """Works for any business that books appointments."""
    pass

# apps/website/services.py - SPECIFIC
class PetFriendlyAppointmentService:
    """Pet-Friendly specific appointment logic."""
    pass
```

### Rule 4: Dependency Direction

```
apps/website/  →  can import from  →  packages/*
packages/*     →  can import from  →  Django, stdlib
packages/*     →  CANNOT import    →  other packages/*
```

### Rule 5: Self-Contained Packages

Each package must have:
- Own `models.py`
- Own `services.py` (public API)
- Own `tests/` directory
- Own `templates/<package_name>/`
- Own `static/<package_name>/`
- Own `migrations/`

---

## 3. Code Style

### Python

- Follow PEP 8
- Use type hints
- Docstrings for public methods
- Max line length: 100 characters

```python
def create_appointment(
    owner_id: int,
    pet_id: int,
    service_type: str,
    scheduled_at: datetime
) -> Appointment:
    """
    Create a new appointment.

    Args:
        owner_id: The pet owner's ID
        pet_id: The pet's ID
        service_type: Type of service requested
        scheduled_at: Appointment datetime

    Returns:
        The created Appointment instance

    Raises:
        ValidationError: If slot is not available
    """
    pass
```

### Django

- Use class-based views (prefer)
- Fat models, thin views
- Business logic in services, not views
- Use Django's ORM, avoid raw SQL

### Templates

- Use template inheritance
- Components in `templates/components/`
- Partials in `templates/partials/`
- Package-specific in `templates/<package_name>/`

---

## 4. Git Commit Standards

### Commit Message Format

```
type(scope): brief description

Detailed explanation if needed.

Closes #X (for tasks)
Addresses #X (for bugs - NO auto-close)
```

### Types

| Type | When |
|------|------|
| `feat` | New feature |
| `fix` | Bug fix |
| `test` | Adding/updating tests |
| `docs` | Documentation |
| `refactor` | Code change that doesn't fix/add |
| `style` | Formatting, linting |
| `chore` | Maintenance tasks |

### Examples

```bash
# Feature
feat(appointments): add slot availability checking

# Bug fix (does NOT auto-close)
fix(store): correct cart total calculation

Addresses #B-003

# Test
test(crm): add owner profile service tests
```

---

## 5. Pre-Implementation Checklist

Copy this checklist before starting any task:

```markdown
## Pre-Implementation Checklist

### Architecture
- [ ] I know which package/app this code belongs in
- [ ] I'm not importing directly from other packages
- [ ] I'm using services.py for cross-package communication

### TDD
- [ ] I will write tests FIRST
- [ ] I have a test file created
- [ ] I understand what "done" looks like

### Standards
- [ ] I've reviewed the acceptance criteria
- [ ] I know the Definition of Done
- [ ] I've checked for existing patterns to follow
```

---

## 6. Definition of Done (Global)

A task is DONE when:

- [ ] All acceptance criteria met
- [ ] Tests written and passing (>95% coverage)
- [ ] No cross-package import violations
- [ ] Code follows style guide
- [ ] Documentation updated
- [ ] Committed with proper message
- [ ] PR reviewed (if applicable)

---

## References

- [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md) - Full ADR-001 details
- [TASK_INDEX.md](TASK_INDEX.md) - All tasks with dependencies
- [MODULE_INTERFACES.md](MODULE_INTERFACES.md) - Package API contracts
