# T-090: RBAC Core Models

> **REQUIRED READING:** Before implementation, review [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)

**Story**: S-010 Role-Based Access Control System
**Priority**: HIGH (blocking)
**Estimate**: 4 hours
**Status**: COMPLETED - 2025-12-26

## Objective

Create the core data models for the RBAC system in the accounts app.

## Deliverables

- [x] `Role` model with name, slug, hierarchy_level, group FK
- [x] `Permission` model with module, action, resource, codename
- [x] `UserRole` model linking users to roles with metadata
- [x] Helper methods on User: `hierarchy_level`, `can_manage_user()`, `get_manageable_roles()`

## Files Modified

- `apps/accounts/models.py` - Added Role, Permission, UserRole models
- `apps/accounts/tests.py` - Added 14 TDD tests
- `apps/accounts/migrations/0004_rbac_models.py` - Created migration

## Test Cases Implemented

```python
# RoleModelTests (3 tests)
def test_role_creation():
    """Role can be created with hierarchy level."""

def test_role_str_method():
    """Role string representation is the name."""

def test_role_unique_slug():
    """Role slugs must be unique."""

# PermissionModelTests (2 tests)
def test_permission_creation():
    """Permission can be created with module/action/resource."""

def test_permission_unique_codename():
    """Permission codenames must be unique."""

# UserRoleModelTests (3 tests)
def test_user_role_assignment():
    """User can be assigned a role."""

def test_user_role_unique_together():
    """User cannot have same role twice."""

def test_user_role_tracks_assigned_by():
    """UserRole tracks who assigned the role."""

# UserHierarchyTests (6 tests)
def test_user_hierarchy_level():
    """User.hierarchy_level returns highest from all roles."""

def test_superuser_hierarchy_level():
    """Superuser has hierarchy level 100."""

def test_user_with_no_roles_hierarchy_level():
    """User with no roles has hierarchy level 0."""

def test_can_manage_user_hierarchy():
    """User can only manage users with lower hierarchy."""

def test_multiple_roles_per_user():
    """User can have multiple roles with combined permissions."""

def test_get_manageable_roles():
    """User can only see roles below their hierarchy."""
```

## Model Summary

### Role Model
- `name` - Unique display name (e.g., "Manager 1", "Manager 2")
- `slug` - URL-friendly unique identifier
- `description` - Optional description
- `hierarchy_level` - Authority level (10-100, higher = more authority)
- `is_active` - Whether role can be assigned
- `group` - OneToOne link to Django's auth.Group for permissions

### Permission Model
- `module` - Which module (practice, inventory, accounting, etc.)
- `action` - What action (view, create, edit, delete, approve, manage)
- `resource` - Specific resource (staff, schedules, bills)
- `codename` - Unique identifier (e.g., "practice.manage_staff")
- `name` - Human-readable description

### UserRole Model
- `user` - FK to User
- `role` - FK to Role
- `assigned_by` - FK to User who assigned the role
- `assigned_at` - Timestamp
- `is_primary` - Whether this is user's main role

### User Model Additions
- `hierarchy_level` property - Returns highest level from all roles (100 for superusers)
- `can_manage_user(other)` - Returns True if can manage other user
- `get_manageable_roles()` - Returns roles below user's level

## Test Results

```
Ran 14 tests in 0.042s
OK
```

All 61 tests (accounts + practice) pass.
