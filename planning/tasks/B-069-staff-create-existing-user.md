# B-069: Cannot Create Staff Profile for Existing User

**Severity**: High
**Affected Component**: apps/practice/forms.py (StaffCreateForm)
**Discovered**: 2025-12-26

## Bug Description

When trying to create a staff member using an email that already exists as a User, the form shows "A user with this email already exists" and refuses to proceed.

This is problematic because an existing customer (User) may be hired as staff - they need a StaffProfile created for their existing account, not a duplicate User.

## Steps to Reproduce

1. Have an existing User with email "john@example.com"
2. Navigate to Practice > Staff > Add Staff
3. Enter email "john@example.com"
4. Fill other required fields
5. Submit form
6. Observe: Error "A user with this email already exists"

## Expected Behavior

The form should either:
1. Detect the existing user and create only a StaffProfile for them, OR
2. Offer a way to link an existing user to a new StaffProfile

## Actual Behavior

Form validation fails with an error when email already exists.

## Root Cause Analysis

The `clean_email()` method in StaffCreateForm raises ValidationError for any existing email:
```python
def clean_email(self):
    email = self.cleaned_data.get('email')
    if User.objects.filter(email=email).exists():
        raise ValidationError('A user with this email already exists.')
    return email
```

## Environment

- Django 5.2.9
- Python 3.12.1

## Fix Applied

**File Modified**: `apps/practice/forms.py` (StaffCreateForm)

Changes made:
1. Added `__init__` method to track existing user
2. Updated `clean_email()` to:
   - Check if user exists and already has StaffProfile → error
   - Check if user exists without StaffProfile → store for reuse
   - If user doesn't exist → proceed normally (create new user)
3. Made password fields optional (`required=False`)
4. Updated `clean()` to only require passwords for new users
5. Updated `save()` to use existing user if available, updating their `is_staff=True`

## Test Coverage

Added tests in `apps/practice/tests.py`:
- `test_form_allows_existing_user_without_profile` - validates form accepts existing email
- `test_form_rejects_user_with_existing_profile` - validates rejection of duplicate profiles
- `test_form_save_creates_profile_for_existing_user` - validates save links to existing user

All 47 practice module tests pass.

## Status

**FIXED** - 2025-12-26

