# B-001: Bad Request on /api/driver/deliveries/{id}/status/

> **REQUIRED READING:** Before implementation, review [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)

**Severity**: Medium
**Status**: Open
**Error Type**: bad_request
**Status Code**: 400

## Description

HTTP 400 error detected on URL pattern: /api/driver/deliveries/{id}/status/

## Steps to Reproduce

1. Navigate to URL pattern: `/api/driver/deliveries/{id}/status/`
2. The error occurs automatically

## Technical Details

- **Fingerprint**: `e79a13ea8d1a7a03`
- **Error Type**: bad_request
- **HTTP Status**: 400

## Definition of Done

- [ ] Root cause identified
- [ ] Fix implemented
- [ ] Tests written to prevent regression
- [ ] Fix verified in production
