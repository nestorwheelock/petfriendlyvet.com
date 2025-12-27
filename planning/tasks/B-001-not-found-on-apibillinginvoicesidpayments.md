# B-001: Not Found on /api/billing/invoices/{id}/payments/

> **REQUIRED READING:** Before implementation, review [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)

**Severity**: Low
**Status**: Open
**Error Type**: not_found
**Status Code**: 404

## Description

HTTP 404 error detected on URL pattern: /api/billing/invoices/{id}/payments/

## Steps to Reproduce

1. Navigate to URL pattern: `/api/billing/invoices/{id}/payments/`
2. The error occurs automatically

## Technical Details

- **Fingerprint**: `2c423d8195342bea`
- **Error Type**: not_found
- **HTTP Status**: 404

## Definition of Done

- [ ] Root cause identified
- [ ] Fix implemented
- [ ] Tests written to prevent regression
- [ ] Fix verified in production
