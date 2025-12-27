# T-091: Permission Infrastructure

> **REQUIRED READING:** Before implementation, review [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)

**Story**: S-010 Role-Based Access Control System
**Priority**: HIGH (blocking)
**Estimate**: 3 hours
**Status**: COMPLETED - 2025-12-26

## Objective

Create centralized permission checking infrastructure for views.

## Deliverables

- [x] `has_module_permission()` method on User model
- [x] `@require_permission()` decorator for function-based views
- [x] `ModulePermissionMixin` for class-based views
- [x] `HierarchyPermissionMixin` for user management views
- [x] `CombinedPermissionMixin` for views needing both checks

## Files Created/Modified

- `apps/accounts/models.py` - Added `has_module_permission()` method
- `apps/accounts/decorators.py` - Created with `@require_permission` decorator
- `apps/accounts/mixins.py` - Created with permission mixins
- `apps/accounts/tests.py` - Added 7 TDD tests (now 21 total)

## Test Cases Implemented

```python
# PermissionMixinTests (3 tests)
def test_has_module_permission_returns_false_without_permission():
    """User without permission returns False."""

def test_has_module_permission_returns_true_with_permission():
    """User with permission returns True."""

def test_superuser_has_all_permissions():
    """Superuser has all module permissions."""

# RequirePermissionDecoratorTests (2 tests)
def test_decorator_denies_without_permission():
    """Decorator raises PermissionDenied without required permission."""

def test_decorator_allows_superuser():
    """Decorator allows superuser without explicit permission."""

# ModulePermissionMixinTests (2 tests)
def test_mixin_denies_without_permission():
    """Mixin test_func returns False without required permission."""

def test_mixin_allows_superuser():
    """Mixin allows superuser access."""
```

## Implementation Summary

### has_module_permission(module, action)

Checks if user has a Django Permission with codename `{module}.{action}` via their Role's Group.

```python
def has_module_permission(self, module, action='view'):
    if self.is_superuser:
        return True
    codename = f"{module}.{action}"
    role_group_ids = self.user_roles.values_list('role__group_id', flat=True)
    return DjangoPermission.objects.filter(
        group__id__in=role_group_ids,
        codename=codename
    ).exists()
```

### @require_permission Decorator

For function-based views:

```python
@require_permission('practice', 'manage')
def staff_create(request):
    ...
```

### ModulePermissionMixin

For class-based views:

```python
class StaffListView(ModulePermissionMixin, ListView):
    required_module = 'practice'
    required_action = 'view'
```

### HierarchyPermissionMixin

For views managing other users:

```python
class StaffEditView(HierarchyPermissionMixin, UpdateView):
    def get_target_user(self):
        return self.get_object().user
```

## Test Results

```
Ran 21 tests in 0.316s
OK
```

All 68 tests (accounts + practice) pass.
