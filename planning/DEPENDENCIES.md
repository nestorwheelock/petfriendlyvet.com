# Build Dependencies & Execution Order

This document defines the build order for tasks based on their dependencies.

---

## Dependency Graph (Simplified)

```
                                    T-001 (Project Setup)
                                           │
            ┌──────────────────────────────┼──────────────────────────────┐
            │                              │                              │
            ▼                              ▼                              ▼
      T-002 (Templates)              T-003 (Auth)                  T-009 (AI Service)
            │                              │                              │
    ┌───────┴───────┐              ┌───────┴───────┐              ┌───────┴───────┐
    │               │              │               │              │               │
    ▼               ▼              ▼               ▼              ▼               ▼
T-005-T-008    T-004 (i18n)   T-024 (Pets)   T-054 (CRM)   T-010 (Tools)   T-013 (History)
  (Pages)                          │                              │
                           ┌───────┴───────┐                      │
                           │               │                      ▼
                           ▼               ▼              T-011 (Customer Chat)
                     T-025 (Medical)  T-027 (Appts)       T-012 (Admin Chat)
                           │               │
                           ▼               ▼
                     T-026 (Views)    T-028 (AI Booking)
                                           │
                                           ▼
                                     T-029 (Appt Views)
```

---

## Execution Phases

### Phase 1: Foundation (Must Complete First)
```
Week 1: Core Infrastructure
├── T-001: Django Project Setup (4h) - NO DEPENDENCIES
├── T-002: Base Templates (4h) - After T-001
├── T-003: Authentication (6h) - After T-001, T-002
└── T-004: Multilingual (6h) - After T-001

Week 2: Static Pages + AI Foundation
├── T-005: Homepage (4h) - After T-002
├── T-006: About Page (3h) - After T-002
├── T-007: Services Page (4h) - After T-002
├── T-008: Contact Page (4h) - After T-002
└── T-009: AI Service Layer (6h) - After T-001
```

### Phase 2: AI & Knowledge Base
```
Week 3: AI Components
├── T-010: Tool Calling Framework (6h) - After T-009
├── T-011: Customer Chat Widget (6h) - After T-009, T-010
├── T-012: Admin Chat Interface (6h) - After T-009, T-010
└── T-013: Chat History (4h) - After T-009

Week 4: Knowledge Base
├── T-014: Knowledge Base Models (4h) - After T-001
├── T-015: Knowledge Admin (4h) - After T-014
└── T-016: AI Context Injection (4h) - After T-014, T-009
```

### Phase 3: Pets & Appointments (Epoch 2)
```
Week 5: Pet System
├── T-024: Pet Models (4h) - After T-001, T-003
├── T-025: Medical Records Models (6h) - After T-024
└── T-026: Pet Profile Views (6h) - After T-024, T-025, T-002

Week 6: Appointments
├── T-027: Appointment Models (6h) - After T-001, T-024
├── T-028: AI Booking Tools (6h) - After T-027, T-009, T-010
├── T-029: Appointment Views (6h) - After T-027, T-002
├── T-030: Reminder Models (4h) - After T-027
└── T-031: Reminder Tasks (4h) - After T-030
```

### Phase 4: Documents & External (Epoch 2 continued)
```
Week 7: Documents & Certificates
├── T-032: Document Models (4h) - After T-024
├── T-033: OCR/Vision (4h) - After T-032, T-009
├── T-034: External Services (3h) - After T-001
└── T-035: Travel Certificates (4h) - After T-024, T-025
```

### Phase 5: E-Commerce (Epoch 3)
```
Week 8: Products & Cart
├── T-036: Product Models (6h) - After T-001
├── T-037: Shopping Cart (6h) - After T-036, T-003
└── T-042: Store Catalog Views (6h) - After T-036, T-002

Week 9: Checkout & Billing
├── T-038: Checkout with Stripe (8h) - After T-037
├── T-039: Pharmacy Models (6h) - After T-036, T-024
├── T-040: Billing & Invoicing (8h) - After T-038
└── T-041: Inventory Management (6h) - After T-036

Week 10: AI Shopping
└── T-043: AI Shopping Tools (6h) - After T-036, T-009, T-010
```

### Phase 6: Communications (Epoch 4)
```
Week 11: Communication Foundation
├── T-044: Communication Models (6h) - After T-001, T-003
├── T-045: Email Integration (6h) - After T-044
├── T-046: SMS Integration (4h) - After T-044
└── T-047: WhatsApp Integration (8h) - After T-044

Week 12: Unified Communications
├── T-048: Unified Inbox (6h) - After T-044, T-045, T-046, T-047
└── T-049: Escalation Engine (6h) - After T-044
```

### Phase 7: Emergency & Referrals (Epoch 4 continued)
```
Week 13: Emergency & Referrals
├── T-050: Emergency Models (4h) - After T-001, T-024
├── T-051: Emergency Triage AI (6h) - After T-050, T-009, T-010
├── T-052: Referral Network Models (4h) - After T-001, T-024
└── T-053: Referral Views (4h) - After T-052, T-002
```

### Phase 8: CRM & Marketing (Epoch 5)
```
Week 14: CRM
├── T-054: CRM Owner Models (6h) - After T-003
├── T-055: CRM Dashboard Views (6h) - After T-054, T-002
└── T-056: Competitive Intel Models (4h) - After T-001

Week 15: Reviews & Loyalty
├── T-057: Reviews & Testimonials (4h) - After T-003, T-024
└── T-058: Loyalty Program (6h) - After T-003, T-054

Week 16: Marketing
├── T-059: SEO & Content (4h) - After T-001
└── T-060: Email Marketing (6h) - After T-045, T-054
```

### Phase 9: Practice Management (Epoch 6)
```
Week 17: Staff & Clinical
├── T-061: Staff Management (6h) - After T-003
├── T-062: Clinical Notes (6h) - After T-024, T-025, T-061
└── T-063: Reports & Analytics (8h) - After T-027, T-036, T-044, T-054

Week 18: Accounting
├── T-064: Accounting Models (8h) - After T-040
└── T-065: Accounting Views (6h) - After T-064, T-002
```

### Phase 10: Data Migration (Parallel Track)
```
Can run in parallel after T-001:
├── T-017: OkVet Export Research (4h) - After nothing
├── T-018: Migration Models (4h) - After T-001, T-017

After respective models exist:
├── T-019: Client Import (4h) - After T-018, T-003
├── T-020: Pet Import (4h) - After T-018, T-024
├── T-021: Medical Records Import (4h) - After T-018, T-025
├── T-022: Vaccination Import (3h) - After T-018, T-025

Final verification:
└── T-023: Migration Verification (3h) - After T-019, T-020, T-021, T-022
```

---

## Blocking Dependencies

These tasks block many others and should be prioritized:

| Task | Blocks | Priority |
|------|--------|----------|
| T-001 | ALL tasks | CRITICAL |
| T-002 | All views/templates | CRITICAL |
| T-003 | All user-related features | CRITICAL |
| T-009 | All AI features | HIGH |
| T-010 | All AI tools | HIGH |
| T-024 | All pet features | HIGH |
| T-036 | All store features | HIGH |
| T-044 | All communications | HIGH |

---

## Parallel Execution Opportunities

These task groups can run in parallel:

### Group A: Static Pages (after T-002)
- T-005, T-006, T-007, T-008 can all run simultaneously

### Group B: AI Components (after T-009, T-010)
- T-011 and T-012 can run in parallel

### Group C: Communication Channels (after T-044)
- T-045, T-046, T-047 can all run simultaneously

### Group D: CRM & Marketing (after respective deps)
- T-056, T-057, T-059 can run in parallel

### Group E: Data Migration (after T-018)
- T-019, T-020, T-021, T-022 can run in parallel after their model deps

---

## External Dependencies

### Third-Party Services (Required Before Certain Tasks)

| Task | External Dependency | Lead Time |
|------|---------------------|-----------|
| T-038 | Stripe merchant account | 1-3 days |
| T-045 | Amazon SES verified domain | 1-2 days |
| T-046 | Twilio account + Mexico number | 1 day |
| T-047 | WhatsApp Business API approval | 2-4 weeks |
| T-040 | Facturama CFDI account | 2-3 days |

**Recommendation:** Apply for WhatsApp Business API early (before Epoch 4).

---

## Testing Dependencies

All tasks require tests to pass before marking complete:

```
Unit Tests ─────────────> Integration Tests ─────────────> E2E Tests
    │                           │                              │
    ├── Model tests            ├── API tests                  ├── User flow tests
    ├── Service tests          ├── View tests                 ├── Checkout flow
    └── Utility tests          └── Template tests             └── Booking flow
```

---

## Database Migration Order

Migrations must run in this order to avoid foreign key issues:

1. **Core/Accounts** (T-001, T-003) - User model first
2. **Multilingual** (T-004) - Translation tables
3. **Knowledge Base** (T-014) - Before AI context
4. **Pets** (T-024, T-025) - Pet and medical records
5. **Appointments** (T-027) - Depends on pets
6. **Store** (T-036) - Products
7. **Pharmacy** (T-039) - Depends on store and pets
8. **Communications** (T-044) - Message models
9. **CRM** (T-054) - Owner profiles
10. **Practice** (T-061, T-064) - Staff and accounting

---

## Rollback Strategy

If a task fails, rollback in reverse order:

```
T-XXX fails
    │
    ├── 1. Revert code changes (git revert)
    ├── 2. Rollback migrations (python manage.py migrate app XXXX)
    ├── 3. Clear cache (redis-cli FLUSHALL)
    └── 4. Restore from backup if data affected
```

---

## Sprint Planning Guide

For 2-week sprints with 2 developers:

### Sprint 1 (Epoch 1 Start)
- Developer A: T-001, T-002, T-005, T-006
- Developer B: T-003, T-004, T-007, T-008

### Sprint 2 (Epoch 1 Cont.)
- Developer A: T-009, T-010, T-011
- Developer B: T-012, T-013, T-014

### Sprint 3 (Epoch 1 End + Epoch 2 Start)
- Developer A: T-015, T-016, T-024
- Developer B: T-017, T-018, T-025

### Sprint 4 (Epoch 2)
- Developer A: T-026, T-027, T-028
- Developer B: T-019, T-020, T-021, T-022

*Continue pattern for remaining epochs...*

---

*Last Updated: December 2025*
