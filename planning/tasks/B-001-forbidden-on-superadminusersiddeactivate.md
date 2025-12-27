# B-001: Forbidden on /superadmin/users/{id}/deactivate/

> **REQUIRED READING:** Before implementation, review [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)

**Severity**: Medium
**Status**: Open
**Error Type**: forbidden
**Status Code**: 403

## Description

HTTP 403 error detected on URL pattern: /superadmin/users/{id}/deactivate/

## Steps to Reproduce

1. Navigate to URL pattern: `/superadmin/users/{id}/deactivate/`
2. The error occurs automatically

## Technical Details

- **Fingerprint**: `bee275795d672e7b`
- **Error Type**: forbidden
- **HTTP Status**: 403

## Definition of Done

- [ ] Root cause identified
- [ ] Fix implemented
- [ ] Tests written to prevent regression
- [ ] Fix verified in production
