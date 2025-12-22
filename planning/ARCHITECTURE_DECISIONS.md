# Architecture Decision Records (ADR)

This document captures significant architectural decisions made during the development of Pet-Friendly.

---

## ADR-001: Monorepo with Extractable Packages

**Date:** December 2025
**Status:** Accepted
**Decision Makers:** Nestor Wheelock

### Context

Pet-Friendly requires 9 reusable Django packages that could benefit other projects:
- django-multilingual
- django-appointments
- django-simple-store
- django-ai-assistant
- django-crm-lite
- django-omnichannel
- django-competitive-intel
- django-vet-clinic
- django-accounting

We needed to decide whether to:
- **Option A**: Build each package in its own repository from the start (9+ repos)
- **Option B**: Build everything together and extract packages later (1 repo)

### Decision

**Build together first (monorepo), extract packages later.**

### Rationale

1. **Ship faster** - Client needs a working website, not a package ecosystem
2. **Learn boundaries** - Real usage reveals correct package interfaces
3. **Simpler CI/CD** - One repo, one test suite, one deployment pipeline
4. **Django philosophy** - Django apps are designed to be extractable
5. **Pragmatic** - Avoid over-engineering before knowing real needs
6. **Iteration** - Easier to refactor boundaries when everything is in one place

### Project Structure

```
petfriendly/
├── config/                    # Django project settings
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
│
├── packages/                  # Future pip-installable packages
│   ├── multilingual/          # → django-multilingual
│   ├── appointments/          # → django-appointments
│   ├── simple_store/          # → django-simple-store
│   ├── ai_assistant/          # → django-ai-assistant
│   ├── crm_lite/              # → django-crm-lite
│   ├── omnichannel/           # → django-omnichannel
│   ├── competitive_intel/     # → django-competitive-intel
│   ├── vet_clinic/            # → django-vet-clinic
│   └── accounting/            # → django-accounting
│
├── apps/
│   └── website/               # Pet-Friendly specific code ONLY
│
├── templates/
├── static/
├── locale/
├── media/
└── manage.py
```

### Rules (Discipline Required)

#### 1. No Cross-Package Internal Imports

```python
# BAD - Direct import from another package
from packages.crm_lite.models import Owner
from packages.vet_clinic.models import Pet

# GOOD - Use Django's get_model for loose coupling
from django.apps import apps
Owner = apps.get_model('crm_lite', 'Owner')
Pet = apps.get_model('vet_clinic', 'Pet')
```

#### 2. Explicit Interfaces Between Packages

Each package defines a `services.py` with its public API:

```python
# packages/appointments/services.py
class AppointmentService:
    @staticmethod
    def get_available_slots(date, service_type):
        """Public API for checking availability."""
        pass

    @staticmethod
    def book_appointment(owner_id, pet_id, slot, service):
        """Public API for booking."""
        pass
```

Other packages import from services, never directly from models:

```python
# GOOD
from packages.appointments.services import AppointmentService

# BAD
from packages.appointments.models import Appointment
```

#### 3. Pet-Friendly Specific Code in apps/website/

Business logic specific to the veterinary clinic goes in `apps/website/`:

```python
# apps/website/services.py
class PetFriendlyService:
    """Pet-Friendly specific business logic."""

    def process_travel_certificate(self, pet, destination):
        # Uses vet_clinic package but adds PF-specific logic
        pass
```

Packages remain generic and reusable for other businesses.

#### 4. Each Package is Self-Contained

Each package in `packages/` contains:
```
packages/appointments/
├── __init__.py
├── admin.py           # Own admin configuration
├── apps.py            # Django app config
├── models.py          # Own models
├── views.py           # Own views
├── urls.py            # Own URL patterns
├── services.py        # Public API
├── forms.py           # Own forms
├── templates/         # Own templates
│   └── appointments/
├── static/            # Own static files
│   └── appointments/
├── tests/             # Own test suite
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_views.py
│   └── test_services.py
└── migrations/        # Own migrations
```

#### 5. Dependency Direction

```
┌─────────────────────────────────────────┐
│           apps/website/                  │
│      (Pet-Friendly specific)            │
│                                          │
│   Can import from ANY package            │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│            packages/                     │
│                                          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │ appoint │ │  store  │ │   ai    │   │
│  │ ments   │ │         │ │assistant│   │
│  └─────────┘ └─────────┘ └─────────┘   │
│                                          │
│  Packages should NOT import each other   │
│  Use interfaces/signals instead          │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│     Django + Python Standard Library     │
└─────────────────────────────────────────┘
```

### Extraction Criteria

A package is ready for extraction to its own repository when:

- [ ] Has comprehensive test coverage (>95%)
- [ ] Has zero imports from other `packages/` directories
- [ ] Has documented public API (services.py)
- [ ] Has been used in production for 1+ month
- [ ] Has README with installation and usage instructions
- [ ] Has pyproject.toml or setup.py ready
- [ ] All migrations are stable (no more schema changes expected)

### Extraction Process

When ready to extract a package:

1. Create new repository (e.g., `django-appointments`)
2. Copy package directory to new repo
3. Add packaging files (pyproject.toml, README, LICENSE)
4. Publish to PyPI (or private index)
5. In petfriendly, replace `packages/appointments/` with pip install
6. Update imports if needed
7. Archive the package from monorepo

### Consequences

**Positive:**
- Faster initial development velocity
- Real-world validated interfaces before extraction
- Simpler development workflow (one repo)
- Easier refactoring during early development

**Negative:**
- Requires discipline to maintain boundaries
- Must actively enforce import rules in code review
- Risk of coupling if rules are ignored

**Risks & Mitigations:**
- "Extract later" becomes tech debt → Review extraction readiness after each Epoch
- Boundaries get blurry → Automated linting for cross-package imports
- Tight coupling develops → Regular architecture reviews

### Review Schedule

Review package extraction readiness at:
- End of Epoch 2 (after appointments + pets working)
- End of Epoch 4 (after communications hub)
- End of Epoch 6 (final review before any extraction)

---

## Future ADRs

As new architectural decisions are made, they will be added here:

- ADR-002: (Reserved)
- ADR-003: (Reserved)
