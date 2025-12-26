# B-055: Missing Email Address Change Functionality

**Severity**: High
**Affected Component**: apps/accounts
**Type**: Missing Feature (CRUD Gap)
**Status**: Open
**Correlates With Error Tracker**: No direct correlation

## Bug Description

Users cannot change their email address from the customer portal. The email is set at registration and cannot be modified, even through the profile edit page.

## Steps to Reproduce

1. Log in as a customer
2. Navigate to /accounts/profile/edit/
3. View editable fields
4. Email field is not present or is read-only
5. No way to change email address

## Expected Behavior

Users should be able to:
- Request email change from profile settings
- Receive verification email at NEW address
- Confirm change by clicking verification link
- Optionally receive notification at OLD address
- Have email updated after verification

## Actual Behavior

- ProfileEditForm does not include email field
- No email change view or URL
- Users must contact support to change email
- No self-service email update option

## Impact

- Users stuck with old/invalid email addresses
- Cannot receive important notifications
- Account recovery issues if email is compromised
- Poor user experience
- Support burden for manual email changes

## Proposed Solution

1. Create `EmailChangeRequestView` with new email input
2. Send verification email to NEW address with token
3. Create `EmailChangeConfirmView` to process token
4. Optionally notify OLD email of pending change
5. Update email after verification
6. Log email change for audit trail

## Files to Modify

- `apps/accounts/views.py` - Add EmailChangeRequestView, EmailChangeConfirmView
- `apps/accounts/forms.py` - Add EmailChangeForm
- `apps/accounts/urls.py` - Add email change routes
- `apps/accounts/models.py` - Add EmailChangeRequest model (optional)
- `templates/accounts/email_change.html` - Request form
- `templates/accounts/email_change_sent.html` - Confirmation sent
- `templates/accounts/email_change_confirm.html` - Verified
- `templates/emails/email_change_verification.html` - Email template
- `tests/test_accounts_views.py` - Add tests

## Security Considerations

1. **Verification Required**: Never change email without verification
2. **Token Expiration**: Tokens should expire in 24-48 hours
3. **Rate Limiting**: Limit email change requests (e.g., once per day)
4. **Notification**: Notify old email of change (optional but recommended)
5. **Audit Logging**: Log all email changes for security audit

## Flow

```
1. User requests email change -> enters new email
2. System generates verification token
3. System sends verification email to NEW address
4. (Optional) System notifies OLD address
5. User clicks verification link
6. System validates token (not expired, not used)
7. System updates email address
8. System invalidates token
9. User sees confirmation
10. (Optional) Final confirmation email to NEW address
```

## Definition of Done

- [ ] EmailChangeRequestView with form
- [ ] Verification token generation
- [ ] Verification email sent to new address
- [ ] EmailChangeConfirmView processes token
- [ ] Token expiration validation
- [ ] Email updated in database
- [ ] Audit log entry created
- [ ] Notification to old email (optional)
- [ ] Tests with >95% coverage
- [ ] Manual testing complete
