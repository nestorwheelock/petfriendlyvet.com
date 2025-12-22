# SPEC Summary: Pet-Friendly Website v2.2

## Quick Reference

| Epoch | Title | Stories | Priority | Deliverable |
|-------|-------|---------|----------|-------------|
| 1 | Foundation + AI Core | 4 | Critical | Site with AI chat, data migration |
| 2 | Appointments + Pets | 6 | Critical | Booking, pet records, travel certs |
| 3 | E-Commerce + Billing | 4 | High | Store, pharmacy, billing, inventory |
| 4 | Communications Hub | 3 | High | WhatsApp, SMS, emergency, referrals |
| 5 | CRM + Intelligence + Marketing | 6 | Medium | CRM, reviews, loyalty, SEO, email |
| 6 | Practice Management | 3 | Medium | Staff tools, reports, accounting |

**Total: 26 User Stories across 6 Epochs**

## Epoch Roadmap

### Epoch 1: Foundation + AI Core
**Stories:** S-001, S-002, S-011, S-023
**Deliverable:** Functional bilingual website with AI chat and migrated data

- S-001: Django modular architecture (9 packages), auth, multilingual
- S-002: AI chat interface (customer + admin)
- S-011: Knowledge base admin for AI content management
- S-023: **CRITICAL** Data migration from OkVet.co (clients, pets, records)

**Key Features:**
- Authentication (Google OAuth + email/phone)
- Multilingual system (ES/EN/DE/FR/IT + AI on-demand)
- AI service layer (OpenRouter, tool calling)
- Knowledge base models + custom admin
- Chat interface (customer + admin)
- Basic info pages (Home, About, Services, Contact)

### Epoch 2: Appointments + Pets
**Stories:** S-003, S-004, S-012, S-013, S-021, S-022
**Deliverable:** Full appointment system with pet records and travel support

- S-003: Pet profiles with medical records, vaccinations, conditions
- S-004: Appointment booking via AI conversation
- S-012: Notifications and reminders (vaccination, appointment)
- S-013: Document management with OCR/vision processing
- S-021: External services (outsourced grooming, boarding referrals)
- S-022: International travel certificates (USDA, EU formats)

### Epoch 3: E-Commerce + Billing
**Stories:** S-005, S-010, S-020, S-024
**Deliverable:** Full e-commerce with pharmacy, billing, and inventory

- S-005: Product catalog, shopping cart, Stripe checkout
- S-010: Pharmacy management (prescriptions, refills, controlled substances)
- S-020: Billing & invoicing (Stripe, CFDI Mexican tax, B2B accounts, discounts)
- S-024: Inventory management (stock tracking, expiry, batch/lot, reorder alerts)

### Epoch 4: Communications Hub
**Stories:** S-006, S-015, S-025
**Deliverable:** Unified communications with emergency and referral support

- S-006: Omnichannel communications (WhatsApp, SMS, email, unified inbox)
- S-015: Emergency services (after-hours triage, on-call management)
- S-025: Referral network (specialists, visiting vets, imaging centers)

### Epoch 5: CRM + Intelligence + Marketing
**Stories:** S-007, S-009, S-014, S-016, S-018, S-019
**Deliverable:** Full CRM with marketing automation

- S-007: CRM and intelligence (owner profiles, marketing data)
- S-009: Competitive intelligence (competitor tracking, pricing)
- S-014: Reviews and testimonials (Google integration)
- S-016: Loyalty and rewards program (points, tiers, referrals)
- S-018: SEO and content marketing (blog, landing pages)
- S-019: Email marketing campaigns (segmentation, automation)

### Epoch 6: Practice Management
**Stories:** S-008, S-017, S-026
**Deliverable:** Complete practice management with accounting

- S-008: Practice management (staff scheduling, compliance)
- S-017: Reports and analytics dashboards
- S-026: Full double-entry accounting (AP/AR, bank reconciliation, budgeting)

## Technical Architecture

> **Key Documents:**
> - [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md) - ADR-001: Monorepo with extractable packages
> - [CODING_STANDARDS.md](CODING_STANDARDS.md) - TDD rules, import rules, code style

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐  │
│  │    HTMX     │ │  Alpine.js  │ │  Tailwind   │ │ AI Chat   │  │
│  │ (Requests)  │ │ (Cart/UI)   │ │   (CSS)     │ │   (UI)    │  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AI SERVICE LAYER                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐  │
│  │  OpenRouter │ │    Tool     │ │  Knowledge  │ │  Vision/  │  │
│  │   (Claude)  │ │   Calling   │ │    Base     │ │    OCR    │  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND (Django 5.x)                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   MODULAR PACKAGES                       │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐     │    │
│  │  │   django-    │ │   django-    │ │   django-    │     │    │
│  │  │ multilingual │ │ appointments │ │ simple-store │     │    │
│  │  └──────────────┘ └──────────────┘ └──────────────┘     │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐     │    │
│  │  │   django-    │ │   django-    │ │   django-    │     │    │
│  │  │ ai-assistant │ │   crm-lite   │ │ omnichannel  │     │    │
│  │  └──────────────┘ └──────────────┘ └──────────────┘     │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐     │    │
│  │  │   django-    │ │   django-    │ │   django-    │     │    │
│  │  │  vet-clinic  │ │ competitive- │ │  accounting  │     │    │
│  │  │              │ │    intel     │ │              │     │    │
│  │  └──────────────┘ └──────────────┘ └──────────────┘     │    │
│  │                                         (9 packages)     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐  │
│  │   Custom    │ │    Email    │ │  Payments   │ │  Audit    │  │
│  │   Admin     │ │   (SMTP)    │ │  (Stripe)   │ │   Logs    │  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    COMMUNICATIONS                                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐  │
│  │    Email    │ │     SMS     │ │  WhatsApp   │ │   Voice   │  │
│  │   (SMTP)    │ │  (Twilio)   │ │ (Business)  │ │ (Escalate)│  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       DATABASE                                   │
│                      PostgreSQL                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │   Users  │ │   Pets   │ │ Appoint- │ │ Products │ │ Orders │ │
│  │ +Owners  │ │ +Records │ │  ments   │ │ +Cart    │ │        │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │Knowledge │ │  Audit   │ │ Communi- │ │   CRM    │            │
│  │   Base   │ │   Logs   │ │ cations  │ │ Profiles │            │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

## Package Structure

```
petfriendly/
├── config/                     # Django project settings
│   ├── settings/
│   │   ├── base.py            # Shared settings
│   │   ├── development.py     # Local dev settings
│   │   └── production.py      # Production settings
│   ├── urls.py
│   └── wsgi.py
│
├── apps/                       # Project-specific apps
│   └── website/               # Pet-Friendly specific content
│
├── packages/                   # Reusable pip-installable packages (9 total)
│   ├── django-multilingual/   # AI translation, language management
│   ├── django-appointments/   # Booking system
│   ├── django-simple-store/   # E-commerce + inventory
│   ├── django-ai-assistant/   # AI chat + tools
│   ├── django-crm-lite/       # Contact management
│   ├── django-omnichannel/    # Communications
│   ├── django-competitive-intel/  # Competitor tracking + intelligence
│   ├── django-vet-clinic/     # Pet profiles + records + travel certs
│   └── django-accounting/     # Double-entry accounting, AP/AR
│
├── templates/                  # HTML templates
├── static/                     # CSS, JS, images
├── locale/                     # Translation files (ES/EN)
├── media/                      # User uploads
└── manage.py
```

## Key Dependencies

| Package | Purpose | Epoch |
|---------|---------|-------|
| Django 5.x | Web framework | 1 |
| django-htmx | HTMX integration | 1 |
| django-tailwind | Tailwind CSS | 1 |
| django-allauth | OAuth + email auth | 1 |
| anthropic / openai | AI API clients | 1 |
| Pillow | Image handling | 1 |
| psycopg2 | PostgreSQL adapter | 1 |
| python-dotenv | Environment variables | 1 |
| stripe | Payment processing | 3 |
| twilio | SMS integration | 4 |
| python-whatsapp-business | WhatsApp API | 4 |

## AI Tool Schema (Epoch 1)

The AI assistant uses tool calling to perform actions:

```python
# Example tools available to customer AI agent
CUSTOMER_TOOLS = [
    {
        "name": "get_clinic_info",
        "description": "Get clinic information (hours, location, services)",
        "parameters": {"topic": "hours|location|services|about"}
    },
    {
        "name": "search_products",
        "description": "Search for products in the store",
        "parameters": {"query": "string", "category": "optional"}
    },
    {
        "name": "check_appointment_availability",
        "description": "Check available appointment slots",
        "parameters": {"service_type": "string", "date_range": "optional"}
    },
    {
        "name": "book_appointment",
        "description": "Book an appointment for a pet",
        "parameters": {"pet_id": "int", "service": "string", "datetime": "ISO8601"}
    },
    {
        "name": "get_pet_info",
        "description": "Get information about user's pet",
        "parameters": {"pet_id": "int"}
    },
    {
        "name": "add_to_cart",
        "description": "Add a product to shopping cart",
        "parameters": {"product_id": "int", "quantity": "int"}
    }
]

# Admin tools extend customer tools with:
ADMIN_TOOLS = CUSTOMER_TOOLS + [
    {
        "name": "create_record",
        "description": "Create any record in the system",
        "parameters": {"model": "string", "data": "object"}
    },
    {
        "name": "update_record",
        "description": "Update any record",
        "parameters": {"model": "string", "id": "int", "data": "object"}
    },
    {
        "name": "search_all",
        "description": "Search across all data",
        "parameters": {"query": "string", "models": "optional array"}
    },
    {
        "name": "generate_report",
        "description": "Generate business reports",
        "parameters": {"report_type": "string", "date_range": "object"}
    }
]
```

## Risks Summary

| Risk | Impact | Mitigation |
|------|--------|------------|
| WhatsApp API approval delay | High | Apply early, SMS fallback |
| AI response quality | High | Knowledge base curation, human escalation |
| Payment processing in MX | Medium | Stripe available, PayPal backup |
| Content not provided | Medium | Placeholder structure, iterate |
| Translation quality | Medium | Native speaker review |
| Complex integration | Medium | Modular architecture |

## Complete Story Index

| Story | Title | Epoch | Module |
|-------|-------|-------|--------|
| S-001 | Foundation + AI Core | 1 | Core + django-multilingual |
| S-002 | AI Chat Interface | 1 | django-ai-assistant |
| S-003 | Pet Profiles + Medical Records | 2 | django-vet-clinic |
| S-004 | Appointment Booking via AI | 2 | django-appointments |
| S-005 | E-Commerce Store | 3 | django-simple-store |
| S-006 | Omnichannel Communications | 4 | django-omnichannel |
| S-007 | CRM + Intelligence | 5 | django-crm-lite |
| S-008 | Practice Management | 6 | django-vet-clinic |
| S-009 | Competitive Intelligence | 5 | django-competitive-intel |
| S-010 | Pharmacy Management | 3 | django-vet-clinic |
| S-011 | Knowledge Base Admin | 1 | django-ai-assistant |
| S-012 | Notifications & Reminders | 2 | django-omnichannel |
| S-013 | Document Management | 2 | django-vet-clinic |
| S-014 | Reviews & Testimonials | 5 | django-crm-lite |
| S-015 | Emergency Services | 4 | django-omnichannel |
| S-016 | Loyalty & Rewards | 5 | django-crm-lite |
| S-017 | Reports & Analytics | 6 | Core |
| S-018 | SEO & Content Marketing | 5 | django-crm-lite |
| S-019 | Email Marketing | 5 | django-omnichannel |
| S-020 | Billing & Invoicing | 3 | django-simple-store |
| S-021 | External Services | 2 | django-vet-clinic |
| S-022 | Travel Certificates | 2 | django-vet-clinic |
| S-023 | Data Migration | 1 | Core |
| S-024 | Inventory Management | 3 | django-simple-store |
| S-025 | Referral Network | 4 | django-vet-clinic |
| S-026 | Accounting | 6 | django-accounting |

## Next Steps

1. Approve this SPEC and PROJECT_CHARTER
2. Begin OkVet.co data migration research (S-023 - CRITICAL)
3. Set up Django project skeleton (Epoch 1)
4. Implement authentication and bilingual system
5. Build AI service layer and chat interface
6. Gather content from client incrementally

---

**Status:** AWAITING CLIENT APPROVAL
**Version:** 2.2.0 (Complete SPEC - 26 Stories, 9 Modules)
**Date:** December 21, 2025
