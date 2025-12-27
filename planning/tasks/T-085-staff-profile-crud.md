# T-085: Staff Profile CRUD Operations

> **STOP! READ THIS FIRST:**
> Before writing ANY code, complete the [TDD STOP GATE](../TDD_STOP_GATE.md)
>
> You must output the confirmation block and write failing tests
> BEFORE any implementation code.

---

**Story**: S-008 Practice Management
**Priority**: High
**Status**: Pending
**Estimate**: 4 hours
**Dependencies**: None

---

## AI Coding Brief

**Role**: Backend/Frontend Developer
**Objective**: Add create, edit, and deactivate operations for staff profiles
**User Request**: "we need to make staff" - ability to create staff members from practice module

### Context

Currently:
- Staff can only be viewed (list/detail) in Practice module
- Creating staff requires Superadmin access (separate workflow)
- No forms.py exists in the practice app
- StaffProfile requires a User account (OneToOne relationship)

### Constraints

**Allowed File Paths**:
- `apps/practice/forms.py` (CREATE)
- `apps/practice/views.py` (MODIFY)
- `apps/practice/urls.py` (MODIFY)
- `templates/practice/staff_form.html` (CREATE)
- `templates/practice/staff_confirm_deactivate.html` (CREATE)
- `apps/practice/tests/test_staff_crud.py` (CREATE)

**Forbidden Paths**: None

### Deliverables

- [ ] `StaffCreateForm` - Combined User + StaffProfile creation
- [ ] `StaffEditForm` - Edit StaffProfile fields (not password)
- [ ] `staff_create` view - Create new staff member
- [ ] `staff_edit` view - Edit existing staff member
- [ ] `staff_deactivate` view - Soft delete (set is_active=False)
- [ ] `staff_form.html` template
- [ ] `staff_confirm_deactivate.html` template
- [ ] URL routes added

### URL Routes

```python
path('staff/add/', views.staff_create, name='staff_create'),
path('staff/<int:pk>/edit/', views.staff_edit, name='staff_edit'),
path('staff/<int:pk>/deactivate/', views.staff_deactivate, name='staff_deactivate'),
```

### Form Fields

**StaffCreateForm** (User + StaffProfile):
```python
# User fields
email = forms.EmailField(required=True)
first_name = forms.CharField(max_length=150)
last_name = forms.CharField(max_length=150)
password1 = forms.CharField(widget=forms.PasswordInput)
password2 = forms.CharField(widget=forms.PasswordInput)

# StaffProfile fields
role = forms.ChoiceField(choices=StaffProfile.ROLE_CHOICES)
title = forms.CharField(max_length=100, required=False)
phone = forms.CharField(max_length=20, required=False)
emergency_phone = forms.CharField(max_length=20, required=False)
hire_date = forms.DateField(required=False)
dea_number = forms.CharField(max_length=20, required=False)
dea_expiration = forms.DateField(required=False)
```

**StaffEditForm** (StaffProfile only):
```python
# Same as above minus password fields
# User email/name fields are read-only or not included
```

### Definition of Done

- [ ] forms.py created with StaffCreateForm, StaffEditForm
- [ ] Views created: staff_create, staff_edit, staff_deactivate
- [ ] URLs added to practice/urls.py
- [ ] Templates created with proper styling
- [ ] Templates use `/staff-{{ staff_token }}/operations/practice/...` URLs
- [ ] Validation errors displayed properly
- [ ] Success messages shown after actions
- [ ] Tests written FIRST (>95% coverage)
- [ ] All tests passing

### Test Cases

```python
class StaffCRUDTests(TestCase):
    """Test staff CRUD operations."""

    def test_staff_create_page_loads(self):
        """Staff create page is accessible to staff."""
        pass

    def test_staff_create_valid_form(self):
        """Valid form creates User and StaffProfile."""
        pass

    def test_staff_create_duplicate_email(self):
        """Duplicate email shows error."""
        pass

    def test_staff_create_password_mismatch(self):
        """Mismatched passwords show error."""
        pass

    def test_staff_edit_page_loads(self):
        """Staff edit page loads with existing data."""
        pass

    def test_staff_edit_valid_form(self):
        """Valid edit updates StaffProfile."""
        pass

    def test_staff_deactivate(self):
        """Deactivate sets is_active=False."""
        pass

    def test_staff_deactivate_confirmation_required(self):
        """Deactivate requires POST confirmation."""
        pass
```

### Notes

- Use `@staff_member_required` decorator on all views
- Follow existing procedure_create pattern in views.py
- Deactivate instead of delete (preserve data integrity)
- Consider adding "Reactivate" link on inactive staff list
