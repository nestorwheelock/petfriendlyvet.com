# Role-Based Access Control (RBAC) System

This document describes the permission system implemented in the Pet-Friendly Vet application.

## Overview

The RBAC system provides:
- **Flexible Custom Roles**: Create roles like "Manager 1" (schedules) vs "Manager 2" (accounting)
- **Hierarchical Permissions**: Users can only manage those with lower hierarchy levels
- **Module-Based Access**: Permissions organized by application module
- **Django Integration**: Uses Django's built-in Groups and Permissions framework

## Architecture

### Core Models

| Model | Purpose |
|-------|---------|
| `Role` | Custom roles with hierarchy levels |
| `Permission` | Module-based permission definitions |
| `UserRole` | Links users to roles (many-to-many) |

### Hierarchy Levels

```
Level 100: Superuser (system admin)
Level 80:  Administrator (clinic admin)
Level 60:  Manager (team leads)
Level 40:  Senior Staff (veterinarians)
Level 20-30: Staff (technicians, receptionists)
Level 10:  Customer (pet owners)
```

**Rule**: Users can only manage users with LOWER hierarchy levels.

## Default Roles

| Role | Slug | Level | Description |
|------|------|-------|-------------|
| Pet Owner | pet-owner | 10 | Pet owners/customers |
| Receptionist | receptionist | 20 | Front desk staff |
| Veterinary Technician | vet-tech | 30 | Vet technicians |
| Veterinarian | veterinarian | 40 | Licensed veterinarians |
| Practice Manager | practice-manager | 60 | Practice management |
| Finance Manager | finance-manager | 60 | Financial operations |
| Administrator | administrator | 80 | Full system access |

## Module Permissions

Permissions follow the format: `{module}.{action}`

### Available Modules

| Module | Description |
|--------|-------------|
| practice | Staff, schedules, time tracking |
| inventory | Stock, orders, suppliers |
| accounting | Bills, payments, journals |
| pharmacy | Prescriptions, controlled substances |
| appointments | Booking, calendar |
| delivery | Drivers, zones |
| crm | Customers, interactions |
| reports | Analytics, exports |
| billing | Invoices, payments |
| superadmin | System settings, users |
| audit | Audit logs |
| email_marketing | Campaigns, newsletters |
| core | Staff hub access |

### Available Actions

| Action | Description |
|--------|-------------|
| view | Read-only access |
| create | Add new records |
| edit | Modify existing |
| delete | Remove records |
| approve | Authorize actions |
| manage | Full control |

## Usage

### Class-Based Views (CBV)

```python
from apps.accounts.mixins import ModulePermissionMixin

class MyPermissionMixin(ModulePermissionMixin):
    required_module = 'practice'
    required_action = 'view'

class MyView(MyPermissionMixin, TemplateView):
    template_name = 'my_template.html'
```

### Function-Based Views (FBV)

```python
from django.contrib.auth.decorators import login_required
from apps.accounts.decorators import require_permission

@login_required
@require_permission('practice', 'view')
def my_view(request):
    return render(request, 'my_template.html')
```

### Checking Permissions in Code

```python
# Check if user has module permission
if user.has_module_permission('practice', 'manage'):
    # Allow action

# Check if user can manage another user (hierarchy)
if user.can_manage_user(other_user):
    # Allow management action

# Get roles user can assign to others
assignable_roles = user.get_manageable_roles()
```

### Template Permission Checks

```django
{% if user.is_superuser %}
    {# Superuser content #}
{% endif %}

{% if perms.accounts.practice_view %}
    {# Show practice link #}
{% endif %}
```

## Adding New Permissions

### 1. Create Django Permission

```python
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from apps.accounts.models import User

content_type = ContentType.objects.get_for_model(User)
permission = Permission.objects.create(
    codename='mymodule.myaction',
    name='Can do action in mymodule',
    content_type=content_type
)
```

### 2. Assign to Role's Group

```python
from apps.accounts.models import Role

role = Role.objects.get(slug='practice-manager')
role.group.permissions.add(permission)
```

### 3. Create Module Mixin

```python
# In apps/mymodule/views.py
from apps.accounts.mixins import ModulePermissionMixin

class MyModulePermissionMixin(ModulePermissionMixin):
    required_module = 'mymodule'
    required_action = 'view'
```

## Superadmin Role Management

Superusers can manage roles via the Superadmin panel:

- **URL**: `/superadmin/roles/`
- **Features**:
  - List all roles with hierarchy levels and user counts
  - Create new custom roles
  - Edit role settings (name, hierarchy level, description)
  - Roles automatically create linked Django Groups

## Migration Strategy

### From Old System

The migration (`0005_populate_default_roles.py`) automatically:
1. Creates 7 default roles
2. Maps existing `User.role` values to new Role system:
   - `owner` -> Pet Owner
   - `staff` -> Receptionist
   - `vet` -> Veterinarian
   - `admin` -> Administrator

### Data Model

```
User.role (old)  →  UserRole.role (new)
User.is_staff    →  hierarchy_level >= 20
User.is_superuser → hierarchy_level = 100
```

## Testing

Run RBAC tests:

```bash
# All RBAC tests
pytest tests/test_rbac.py -v

# Unit tests
pytest apps/accounts/tests.py -v

# All permission-related tests
pytest apps/accounts/tests.py apps/practice/tests.py tests/test_rbac.py -v
```

### Test Coverage

- **99 total tests** covering:
  - Role model creation and constraints
  - User hierarchy calculations
  - Permission checking (module + action)
  - Decorator and mixin functionality
  - Default roles and migrations
  - Integration workflows
  - Privilege escalation prevention

## Security Considerations

1. **Hierarchy Enforcement**: Users cannot manage peers or superiors
2. **Privilege Escalation Prevention**: Users can only assign roles below their level
3. **Superuser Protection**: Superusers have level 100, cannot be managed by non-superusers
4. **Permission Caching**: Django caches permissions; clear after role changes
5. **Audit Logging**: Permission denials should be logged (see audit module)

## API Reference

### User Model Methods

| Method | Description |
|--------|-------------|
| `user.hierarchy_level` | Highest level from all user's roles |
| `user.can_manage_user(other)` | True if can manage other user |
| `user.has_module_permission(module, action)` | True if has permission |
| `user.get_manageable_roles()` | QuerySet of assignable roles |

### Role Model

| Field | Type | Description |
|-------|------|-------------|
| name | CharField | Display name |
| slug | SlugField | URL-friendly identifier |
| hierarchy_level | IntegerField | 10-100, higher = more authority |
| is_active | BooleanField | Whether role can be assigned |
| group | FK(Group) | Linked Django Group for permissions |

### UserRole Model

| Field | Type | Description |
|-------|------|-------------|
| user | FK(User) | User with this role |
| role | FK(Role) | The assigned role |
| assigned_by | FK(User) | Who assigned the role |
| assigned_at | DateTimeField | When assigned |
| is_primary | BooleanField | User's main role |
