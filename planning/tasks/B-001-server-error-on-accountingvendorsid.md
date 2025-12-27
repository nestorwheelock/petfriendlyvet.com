# B-001: Server Error on /accounting/vendors/{id}/

> **REQUIRED READING:** Before implementation, review [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)

**Severity**: High
**Status**: Open
**Error Type**: server_error
**Status Code**: 500

## Description

HTTP 500 error detected on URL pattern: /accounting/vendors/{id}/

## Steps to Reproduce

1. Navigate to URL pattern: `/accounting/vendors/{id}/`
2. The error occurs automatically

## Technical Details

- **Fingerprint**: `1f44d75359d1f14f`
- **Error Type**: server_error
- **HTTP Status**: 500

## Definition of Done

- [ ] Root cause identified
- [ ] Fix implemented
- [ ] Tests written to prevent regression
- [ ] Fix verified in production
