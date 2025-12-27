# B-001: Server Error on /operations/inventory/purchase-orders/{id}/lines/{id}/edit/

> **REQUIRED READING:** Before implementation, review [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)

**Severity**: High
**Status**: Open
**Error Type**: server_error
**Status Code**: 500

## Description

HTTP 500 error detected on URL pattern: /operations/inventory/purchase-orders/{id}/lines/{id}/edit/

## Steps to Reproduce

1. Navigate to URL pattern: `/operations/inventory/purchase-orders/{id}/lines/{id}/edit/`
2. The error occurs automatically

## Technical Details

- **Fingerprint**: `73a0965f422bce06`
- **Error Type**: server_error
- **HTTP Status**: 500

## Definition of Done

- [ ] Root cause identified
- [ ] Fix implemented
- [ ] Tests written to prevent regression
- [ ] Fix verified in production
