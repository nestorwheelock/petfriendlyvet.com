# B-051: Server Error on /crm/customers/{id}/

> **REQUIRED READING:** Before implementation, review [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)

**Severity**: High
**Status**: Open
**Error Type**: server_error
**Status Code**: 500

## Description

HTTP 500 error detected on URL pattern: /crm/customers/{id}/

## Steps to Reproduce

1. Navigate to URL pattern: `/crm/customers/{id}/`
2. The error occurs automatically

## Technical Details

- **Fingerprint**: `0ccc5e8aaaf03890`
- **Error Type**: server_error
- **HTTP Status**: 500

## Definition of Done

- [ ] Root cause identified
- [ ] Fix implemented
- [ ] Tests written to prevent regression
- [ ] Fix verified in production
