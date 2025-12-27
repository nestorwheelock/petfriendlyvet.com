# T-067: Delivery App Structure

> **REQUIRED READING:** Before implementation, review [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)

> **STOP! READ THIS FIRST:**
> Before writing ANY code, complete the [TDD STOP GATE](../TDD_STOP_GATE.md)
>
> You must output the confirmation block and write failing tests
> BEFORE any implementation code.

---

**Story**: S-027 - Delivery Module Core
**Priority**: High
**Status**: Pending
**Estimate**: 1 hour
**Dependencies**: T-066 (StoreSettings)

---

## Objective

Create the delivery app structure with basic configuration.

---

## Deliverables

### App Structure

```
apps/delivery/
├── __init__.py
├── apps.py
├── models.py
├── admin.py
├── views.py
├── urls.py
├── tests.py
└── migrations/
    └── __init__.py
```

### Configuration

1. Create app with `python manage.py startapp delivery apps/delivery`
2. Add to INSTALLED_APPS in settings
3. Create basic URL configuration

---

## Test Cases

```python
class DeliveryAppConfigTests(TestCase):
    """Tests for delivery app configuration."""

    def test_app_is_installed(self):
        """Delivery app should be in installed apps."""
        from django.apps import apps
        self.assertTrue(apps.is_installed('apps.delivery'))

    def test_urls_are_configured(self):
        """Delivery URLs should be configured."""
        from django.urls import reverse
        # Will be expanded when views are added
```

---

## Definition of Done

- [ ] App created at apps/delivery/
- [ ] App added to INSTALLED_APPS
- [ ] Basic apps.py configured
- [ ] Empty tests.py with basic test
- [ ] Migration folder created
