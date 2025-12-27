# T-092: Data Migration

**Story**: S-010 Role-Based Access Control System
**Priority**: HIGH (blocking)
**Estimate**: 3 hours
**Status**: COMPLETED - 2025-12-26

## Objective

Create migration to populate default roles and migrate existing users.

## Deliverables

- [x] Default roles created (Pet Owner, Receptionist, Vet Tech, Veterinarian, Practice Manager, Finance Manager, Administrator)
- [x] Default permissions created per module
- [x] Existing User.role values mapped to new Role system
- [x] Django Groups created for each Role

## Files Created/Modified

- `apps/accounts/migrations/0005_populate_default_roles.py` - Data migration
- `apps/accounts/tests.py` - Added 5 migration tests (now 26 total)

## Default Roles Created

| Role | Slug | Hierarchy Level | Description |
|------|------|-----------------|-------------|
| Pet Owner | pet-owner | 10 | Pet owners and customers |
| Receptionist | receptionist | 20 | Front desk and customer service |
| Veterinary Technician | vet-tech | 30 | Vet techs and assistants |
| Veterinarian | veterinarian | 40 | Licensed veterinarians |
| Practice Manager | practice-manager | 60 | Staff schedules and operations |
| Finance Manager | finance-manager | 60 | Accounting and financial operations |
| Administrator | administrator | 80 | Full system admin access |

## User Migration Mapping

| Old User.role | New Role Slug |
|---------------|---------------|
| owner | pet-owner |
| staff | receptionist |
| vet | veterinarian |
| admin | administrator |

## Test Cases Implemented

```python
# DefaultRolesTests (3 tests)
def test_default_roles_exist():
    """Default roles should exist after migration."""

def test_roles_have_correct_hierarchy():
    """Roles should have correct hierarchy levels."""

def test_roles_have_linked_groups():
    """Each role should have a linked Django Group."""

# UserRoleMigrationTests (2 tests)
def test_user_with_owner_role_gets_pet_owner():
    """User with role='owner' should get pet-owner Role."""

def test_user_with_staff_role_gets_receptionist():
    """User with role='staff' should get receptionist Role."""
```

## Test Results

```
Ran 73 tests in 1.046s
OK
```

All tests pass including accounts (26) and practice (47).
