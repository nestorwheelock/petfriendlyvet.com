# Task Index - Pet-Friendly Veterinary Clinic Website

**Total Tasks:** 65
**Total Estimated Effort:** ~280 hours
**Epochs:** 6

---

## Quick Reference by Epoch

| Epoch | Focus | Tasks | Hours |
|-------|-------|-------|-------|
| 1 | Foundation + AI Core | T-001 to T-023 | ~80h |
| 2 | Appointments + Pets | T-024 to T-035 | ~48h |
| 3 | E-Commerce | T-036 to T-043 | ~40h |
| 4 | Communications | T-044 to T-053 | ~48h |
| 5 | CRM + Marketing | T-054 to T-060 | ~36h |
| 6 | Practice Management | T-061 to T-065 | ~28h |

---

## Epoch 1: Foundation + AI Core

### Project Setup & Infrastructure
| Task | Title | Story | Hours | Dependencies |
|------|-------|-------|-------|--------------|
| T-001 | Django Project Setup | S-001 | 4h | None |
| T-002 | Base Templates & Layout | S-001 | 4h | T-001 |
| T-003 | Authentication System | S-001 | 6h | T-001, T-002 |
| T-004 | Multilingual System | S-001 | 6h | T-001 |

### Static Pages
| Task | Title | Story | Hours | Dependencies |
|------|-------|-------|-------|--------------|
| T-005 | Homepage | S-001 | 4h | T-002 |
| T-006 | About Page | S-001 | 3h | T-002 |
| T-007 | Services Page | S-001 | 4h | T-002 |
| T-008 | Contact Page | S-001 | 4h | T-002 |

### AI System
| Task | Title | Story | Hours | Dependencies |
|------|-------|-------|-------|--------------|
| T-009 | AI Service Layer | S-002 | 6h | T-001 |
| T-010 | Tool Calling Framework | S-002 | 6h | T-009 |
| T-011 | Customer Chat Widget | S-002 | 6h | T-009, T-010 |
| T-012 | Admin Chat Interface | S-002 | 6h | T-009, T-010 |
| T-013 | Chat History & Sessions | S-002 | 4h | T-009 |

### Knowledge Base
| Task | Title | Story | Hours | Dependencies |
|------|-------|-------|-------|--------------|
| T-014 | Knowledge Base Models | S-011 | 4h | T-001 |
| T-015 | Knowledge Admin Interface | S-011 | 4h | T-014 |
| T-016 | AI Context Injection | S-011 | 4h | T-014, T-009 |

### Data Migration (OkVet.co)
| Task | Title | Story | Hours | Dependencies |
|------|-------|-------|-------|--------------|
| T-017 | OkVet Export Research | S-023 | 4h | None |
| T-018 | Migration Models | S-023 | 4h | T-001, T-017 |
| T-019 | Client Import | S-023 | 4h | T-018, T-003 |
| T-020 | Pet Import | S-023 | 4h | T-018, T-024 |
| T-021 | Medical Records Import | S-023 | 4h | T-018, T-025 |
| T-022 | Vaccination Import | S-023 | 3h | T-018, T-025 |
| T-023 | Migration Verification | S-023 | 3h | T-019, T-020, T-021, T-022 |

---

## Epoch 2: Appointments + Pets

### Pet Profiles
| Task | Title | Story | Hours | Dependencies |
|------|-------|-------|-------|--------------|
| T-024 | Pet Models | S-003 | 4h | T-001, T-003 |
| T-025 | Medical Records Models | S-003 | 6h | T-024 |
| T-026 | Pet Profile Views | S-003 | 6h | T-024, T-025, T-002 |

### Appointments
| Task | Title | Story | Hours | Dependencies |
|------|-------|-------|-------|--------------|
| T-027 | Appointment Models | S-004 | 6h | T-001, T-024 |
| T-028 | AI Booking Tools | S-004 | 6h | T-027, T-009, T-010 |
| T-029 | Appointment Views | S-004 | 6h | T-027, T-002 |

### Notifications
| Task | Title | Story | Hours | Dependencies |
|------|-------|-------|-------|--------------|
| T-030 | Reminder Models | S-012 | 4h | T-027 |
| T-031 | Reminder Tasks (Celery) | S-012 | 4h | T-030 |

### Documents
| Task | Title | Story | Hours | Dependencies |
|------|-------|-------|-------|--------------|
| T-032 | Document Models | S-013 | 4h | T-024 |
| T-033 | OCR/Vision Integration | S-013 | 4h | T-032, T-009 |

### External Services
| Task | Title | Story | Hours | Dependencies |
|------|-------|-------|-------|--------------|
| T-034 | External Services Models | S-021 | 3h | T-001 |
| T-035 | Travel Certificates | S-022 | 4h | T-024, T-025 |

---

## Epoch 3: E-Commerce

### Product Catalog
| Task | Title | Story | Hours | Dependencies |
|------|-------|-------|-------|--------------|
| T-036 | Product Models | S-005 | 6h | T-001 |
| T-037 | Shopping Cart | S-005 | 6h | T-036, T-003 |
| T-038 | Checkout with Stripe | S-005 | 8h | T-037 |

### Pharmacy
| Task | Title | Story | Hours | Dependencies |
|------|-------|-------|-------|--------------|
| T-039 | Pharmacy Models | S-010 | 6h | T-036, T-024 |

### Billing
| Task | Title | Story | Hours | Dependencies |
|------|-------|-------|-------|--------------|
| T-040 | Billing & Invoicing | S-020 | 8h | T-038 |

### Inventory
| Task | Title | Story | Hours | Dependencies |
|------|-------|-------|-------|--------------|
| T-041 | Inventory Management | S-024 | 6h | T-036 |

### Store Views
| Task | Title | Story | Hours | Dependencies |
|------|-------|-------|-------|--------------|
| T-042 | Store Catalog Views | S-005 | 6h | T-036, T-002 |
| T-043 | AI Shopping Tools | S-005 | 6h | T-036, T-009, T-010 |

---

## Epoch 4: Communications

### Communication Models
| Task | Title | Story | Hours | Dependencies |
|------|-------|-------|-------|--------------|
| T-044 | Communication Models | S-006 | 6h | T-001, T-003 |

### Email
| Task | Title | Story | Hours | Dependencies |
|------|-------|-------|-------|--------------|
| T-045 | Email Integration (SES) | S-006 | 6h | T-044 |

### SMS
| Task | Title | Story | Hours | Dependencies |
|------|-------|-------|-------|--------------|
| T-046 | SMS Integration (Twilio) | S-006 | 4h | T-044 |

### WhatsApp
| Task | Title | Story | Hours | Dependencies |
|------|-------|-------|-------|--------------|
| T-047 | WhatsApp Integration | S-006 | 8h | T-044 |

### Unified Communications
| Task | Title | Story | Hours | Dependencies |
|------|-------|-------|-------|--------------|
| T-048 | Unified Inbox | S-006 | 6h | T-044, T-045, T-046, T-047 |
| T-049 | Escalation Engine | S-006 | 6h | T-044 |

### Emergency
| Task | Title | Story | Hours | Dependencies |
|------|-------|-------|-------|--------------|
| T-050 | Emergency Models | S-015 | 4h | T-001, T-024 |
| T-051 | Emergency Triage AI | S-015 | 6h | T-050, T-009, T-010 |

### Referrals
| Task | Title | Story | Hours | Dependencies |
|------|-------|-------|-------|--------------|
| T-052 | Referral Network Models | S-025 | 4h | T-001, T-024 |
| T-053 | Referral Views | S-025 | 4h | T-052, T-002 |

---

## Epoch 5: CRM + Marketing

### CRM
| Task | Title | Story | Hours | Dependencies |
|------|-------|-------|-------|--------------|
| T-054 | CRM Owner Models | S-007 | 6h | T-003 |
| T-055 | CRM Dashboard Views | S-007 | 6h | T-054, T-002 |

### Competitive Intelligence
| Task | Title | Story | Hours | Dependencies |
|------|-------|-------|-------|--------------|
| T-056 | Competitive Intel Models | S-009 | 4h | T-001 |

### Reviews
| Task | Title | Story | Hours | Dependencies |
|------|-------|-------|-------|--------------|
| T-057 | Reviews & Testimonials | S-014 | 4h | T-003, T-024 |

### Loyalty
| Task | Title | Story | Hours | Dependencies |
|------|-------|-------|-------|--------------|
| T-058 | Loyalty Program | S-016 | 6h | T-003, T-054 |

### Marketing
| Task | Title | Story | Hours | Dependencies |
|------|-------|-------|-------|--------------|
| T-059 | SEO & Content | S-018 | 4h | T-001 |
| T-060 | Email Marketing | S-019 | 6h | T-045, T-054 |

---

## Epoch 6: Practice Management

### Staff
| Task | Title | Story | Hours | Dependencies |
|------|-------|-------|-------|--------------|
| T-061 | Staff Management | S-008 | 6h | T-003 |

### Clinical
| Task | Title | Story | Hours | Dependencies |
|------|-------|-------|-------|--------------|
| T-062 | Clinical Notes | S-008 | 6h | T-024, T-025, T-061 |

### Reports
| Task | Title | Story | Hours | Dependencies |
|------|-------|-------|-------|--------------|
| T-063 | Reports & Analytics | S-017 | 8h | T-027, T-036, T-044, T-054 |

### Accounting
| Task | Title | Story | Hours | Dependencies |
|------|-------|-------|-------|--------------|
| T-064 | Accounting Models | S-026 | 8h | T-040 |
| T-065 | Accounting Views | S-026 | 6h | T-064, T-002 |

---

## Story to Task Mapping

| Story | Title | Tasks |
|-------|-------|-------|
| S-001 | Foundation + AI Core | T-001, T-002, T-003, T-004, T-005, T-006, T-007, T-008 |
| S-002 | AI Chat Interface | T-009, T-010, T-011, T-012, T-013 |
| S-003 | Pet Profiles + Medical Records | T-024, T-025, T-026 |
| S-004 | Appointment Booking | T-027, T-028, T-029 |
| S-005 | E-Commerce Store | T-036, T-037, T-038, T-042, T-043 |
| S-006 | Omnichannel Communications | T-044, T-045, T-046, T-047, T-048, T-049 |
| S-007 | CRM + Intelligence | T-054, T-055 |
| S-008 | Practice Management | T-061, T-062 |
| S-009 | Competitive Intelligence | T-056 |
| S-010 | Pharmacy Management | T-039 |
| S-011 | Knowledge Base | T-014, T-015, T-016 |
| S-012 | Notifications & Reminders | T-030, T-031 |
| S-013 | Document Management | T-032, T-033 |
| S-014 | Reviews & Testimonials | T-057 |
| S-015 | Emergency Services | T-050, T-051 |
| S-016 | Loyalty & Rewards | T-058 |
| S-017 | Reports & Analytics | T-063 |
| S-018 | SEO & Content | T-059 |
| S-019 | Email Marketing | T-060 |
| S-020 | Billing & Invoicing | T-040 |
| S-021 | External Services | T-034 |
| S-022 | Travel Certificates | T-035 |
| S-023 | Data Migration | T-017, T-018, T-019, T-020, T-021, T-022, T-023 |
| S-024 | Inventory Management | T-041 |
| S-025 | Referral Network | T-052, T-053 |
| S-026 | Accounting | T-064, T-065 |

---

## Critical Path

The following tasks are on the critical path and must be completed in order:

```
T-001 (Project Setup)
    │
    ├─> T-002 (Templates) ──> T-005 to T-008 (Pages)
    │
    ├─> T-003 (Auth) ──> T-024 (Pets) ──> T-027 (Appointments)
    │                                      │
    │                                      └─> T-028 (AI Booking)
    │
    ├─> T-009 (AI Service) ──> T-010 (Tool Calling) ──> T-011 (Chat)
    │
    ├─> T-036 (Products) ──> T-037 (Cart) ──> T-038 (Checkout)
    │                                          │
    │                                          └─> T-040 (Billing)
    │
    └─> T-044 (Comms) ──> T-045/46/47 (Email/SMS/WA) ──> T-048 (Inbox)
```

---

## Module Ownership

| Module | Tasks | Primary Owner |
|--------|-------|---------------|
| core | T-001, T-002, T-005-T-008 | Backend + Frontend |
| accounts | T-003, T-019 | Backend |
| multilingual | T-004 | Backend |
| ai_assistant | T-009-T-016 | Backend + AI |
| pets | T-024-T-026, T-032-T-035 | Backend |
| appointments | T-027-T-031 | Backend |
| store | T-036-T-043 | Backend + Frontend |
| pharmacy | T-039 | Backend |
| communications | T-044-T-049 | Backend |
| crm | T-054-T-060 | Backend |
| practice | T-061-T-065 | Backend |

---

## Files Per Task

Each task file contains:
- AI Coding Brief (role, objective, constraints)
- Deliverables checklist
- Implementation Details with code
- Test Cases
- Definition of Done
- Dependencies

Location: `planning/tasks/T-XXX-*.md`

---

*Last Updated: December 2025*
