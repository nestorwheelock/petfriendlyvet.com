# B-001: CSRF Trusted Origins Not Configured for dev.petfriendlyvet.com

**Severity**: Critical
**Affected Component**: config/settings/production.py
**Discovered**: 2023-12-23
**Status**: Fix Implemented - Awaiting Human Verification

## Bug Description

POST requests to `https://dev.petfriendlyvet.com` fail with CSRF error:
```
Prohibido (403)
La verificación CSRF ha fallado. Solicitud abortada.

Reason given for failure:
    Origin checking failed - https://dev.petfriendlyvet.com does not match any trusted origins.
```

## Steps to Reproduce

1. Navigate to https://dev.petfriendlyvet.com
2. Submit any form (login, contact, etc.)
3. Observe 403 CSRF error

## Expected Behavior

POST forms should work correctly with valid CSRF token.

## Actual Behavior

All POST requests fail with CSRF origin mismatch error.

## Root Cause

Django 4.0+ requires `CSRF_TRUSTED_ORIGINS` setting for HTTPS origins. The production settings have:
- `CORS_ALLOWED_ORIGINS` configured (but only for petfriendlyvet.com, not dev subdomain)
- `CSRF_TRUSTED_ORIGINS` is NOT configured at all

## Fix Required

Add `CSRF_TRUSTED_ORIGINS` to `config/settings/production.py`:
```python
CSRF_TRUSTED_ORIGINS = [
    'https://petfriendlyvet.com',
    'https://www.petfriendlyvet.com',
    'https://dev.petfriendlyvet.com',
]
```

Also update `CORS_ALLOWED_ORIGINS` to include the dev subdomain.

## Environment

- Django: 5.x
- Python: 3.11+
- Server: https://dev.petfriendlyvet.com (subdirectory deployment)

## Test Cases

1. **Test CSRF token form submission**: POST to any form on dev.petfriendlyvet.com should succeed
2. **Test login**: User can log in without CSRF errors
3. **Test all subdomains**: Both www and dev subdomains work

## Definition of Done

- [x] `CSRF_TRUSTED_ORIGINS` added to production settings
- [x] `CORS_ALLOWED_ORIGINS` updated to include dev subdomain
- [x] Failing test written first (reproduces the issue)
- [ ] Manual verification on dev.petfriendlyvet.com
- [ ] Human closes issue after verification
