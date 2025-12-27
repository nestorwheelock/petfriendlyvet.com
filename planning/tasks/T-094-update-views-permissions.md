# T-094: Update Views to New Permission System

**Story**: S-010 Role-Based Access Control System
**Priority**: MEDIUM
**Estimate**: 4 hours
**Status**: COMPLETED - 2025-12-26

## Objective

Replace all duplicate StaffRequiredMixin definitions with centralized permission checks from the RBAC system.

## Deliverables

- [x] Remove StaffRequiredMixin from 7 apps
- [x] Update practice views to use @require_permission decorator
- [x] Update accounting views to use ModulePermissionMixin
- [x] Update other app views to use centralized mixins
- [x] Update practice tests to grant permissions

## Apps Updated

| App | Original Mixin | New Mixin | Permission |
|-----|---------------|-----------|------------|
| apps/practice | @staff_member_required | @require_permission | practice.view |
| apps/accounting | StaffRequiredMixin | AccountingPermissionMixin | accounting.view |
| apps/reports | StaffRequiredMixin | ReportsPermissionMixin | reports.view |
| apps/crm | StaffRequiredMixin | CRMPermissionMixin | crm.view |
| apps/audit | StaffRequiredMixin | AuditPermissionMixin | audit.view |
| apps/email_marketing | StaffRequiredMixin | MarketingPermissionMixin | email_marketing.view |
| apps/core | StaffRequiredMixin | CorePermissionMixin | core.view |
| apps/delivery | StaffRequiredMixin | DeliveryPermissionMixin | delivery.view |

## Test Cases Implemented

```python
# T094ViewPermissionTests (3 tests)
def test_practice_dashboard_requires_permission():
    """Practice dashboard requires practice.view permission."""

def test_accounting_requires_accounting_permission():
    """Accounting views require accounting module permission."""

def test_staff_create_checks_hierarchy():
    """Cannot create staff at higher hierarchy level."""
```

## Files Modified

### Permission Integration
- `apps/practice/views.py` - Changed from @staff_member_required to @require_permission
- `apps/accounting/views.py` - Created AccountingPermissionMixin
- `apps/reports/views.py` - Created ReportsPermissionMixin
- `apps/crm/views.py` - Created CRMPermissionMixin
- `apps/audit/views.py` - Created AuditPermissionMixin
- `apps/email_marketing/views.py` - Created MarketingPermissionMixin
- `apps/core/views.py` - Created CorePermissionMixin
- `apps/delivery/admin_views.py` - Created DeliveryPermissionMixin

### Test Updates
- `apps/accounts/tests.py` - Added T094ViewPermissionTests
- `apps/practice/tests.py` - Added grant_practice_permission helper, updated all test setUp methods

## Test Results

```
Ran 84 tests in 16.02s
OK
```

All tests pass including accounts (29), practice (47), and superadmin (8).

## Architecture Notes

Each app now has its own PermissionMixin that inherits from the centralized `ModulePermissionMixin`:

```python
from apps.accounts.mixins import ModulePermissionMixin

class AccountingPermissionMixin(ModulePermissionMixin):
    required_module = 'accounting'
    required_action = 'view'
```

For function-based views (practice), the @require_permission decorator is used:

```python
from apps.accounts.decorators import require_permission

@login_required
@require_permission('practice', 'view')
def dashboard(request):
    ...
```
