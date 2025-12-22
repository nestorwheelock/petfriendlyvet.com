# Project Charter: Pet-Friendly Veterinary Clinic Website

## Project Overview

**Project Name:** petfriendlyvet.com
**Client:** Pet-Friendly (Dr. Pablo Rojo Mendoza)
**Location:** Puerto Morelos, Quintana Roo, Mexico
**Version:** v2.2.0 (Complete SPEC - 26 User Stories, 9 Modules)

## What We're Building

An **AI-first** multilingual platform for Pet-Friendly veterinary clinic that transforms how pet owners interact with veterinary services. Unlike traditional websites, conversation is the primary interface.

**Multilingual Support:** Core languages (Spanish, English, German, French, Italian) with AI-powered on-demand translation for 100+ additional languages - perfect for Puerto Morelos' diverse expat and tourist community.

### Core Concept: AI-First Design

Instead of navigating menus and filling forms, users **talk** to the website:
- "I need to bring my dog Luna in for her vaccines"
- "What's the best flea medicine for a 10kg cat?"
- "Do you have Hills Science Diet in stock?"
- "When is Dr. Pablo available this week?"

The AI understands context, remembers pet information, and handles everything from information queries to appointments to purchases.

### Three Service Lines

Based on the logo and business, Pet-Friendly offers:

1. **Clínica (Veterinary Clinic)** - PRIMARY
   - General consultations and wellness exams
   - Vaccinations and preventive care
   - Surgery and procedures
   - Emergency services
   - Laboratory diagnostics

2. **Farmacia (Pet Pharmacy)**
   - Prescription medications
   - Flea/tick prevention
   - Supplements and vitamins
   - Prescription fulfillment

3. **Tienda (Pet Store)**
   - Premium pet food
   - Toys and accessories
   - Grooming supplies
   - Carriers and travel gear

## Why This Matters

### Market Opportunity

Based on our competitor research:
- **No veterinary clinic in Puerto Morelos has a real website** - only directory listings and social media
- Growing expat community needs bilingual services
- Tourism brings English-speaking pet owners needing urgent care
- Current communication via WhatsApp is chaotic and untracked

### Competitive Advantages

| Feature | Pet-Friendly | Competitors |
|---------|--------------|-------------|
| Website | AI-powered | None |
| Online Booking | AI chat | None |
| E-commerce | Full store | None |
| Bilingual | Native ES/EN | Limited |
| Pet Records | Owner access | None |
| Communication | Unified inbox | WhatsApp chaos |

## Technical Approach

### Architecture: Modular Pip-Installable Packages

We're building **9 reusable Django packages** that can be used across other businesses:

| Module | Description | Reusable For |
|--------|-------------|--------------|
| **django-multilingual** | AI-powered translation, language management | Any multilingual site |
| **django-appointments** | Service booking, calendar, reminders | Salons, dentists, consultants |
| **django-simple-store** | Products, cart, checkout, orders, inventory | Any small business e-commerce |
| **django-ai-assistant** | Chat interface, tool calling, knowledge base | Any AI-powered site |
| **django-crm-lite** | Contact profiles, communication history | Any business CRM |
| **django-omnichannel** | Email, SMS, WhatsApp, voice | Any customer communication |
| **django-competitive-intel** | Competitor tracking, pricing, visitor intelligence | Any competitive business |
| **django-vet-clinic** | Pet profiles, medical records, travel certificates | Veterinary practices |
| **django-accounting** | Double-entry accounting, AP/AR, bank reconciliation | Any business needing financials |

### Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Framework | Django 5.x | Built-in admin, ORM, auth, i18n, security |
| Frontend | HTMX + Alpine.js | Server-driven, no build step, SEO-friendly |
| Styling | Tailwind CSS | Utility-first, mobile-responsive |
| Database | PostgreSQL | Production-grade, Django-native |
| AI Provider | OpenRouter (Claude) | Multi-model, tool calling |
| Payments | Stripe | Available in Mexico, modern API |
| Communications | Twilio + WhatsApp Business API | Omnichannel messaging |

### Key Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Multi-tenant | No (separate installs) | Safer, simpler, modules reusable |
| Auth | Google OAuth + email/phone | Frictionless, proven |
| Admin | Custom mobile-first | Django admin is desktop-centric |
| AI Approach | Chat as primary interface | Not an add-on feature |
| Auditing | Compliance-level | Immutable logs, exportable |

## AI Capabilities

### Customer-Facing AI Agent

Pet owners can:
- Learn about clinic, services, hours, location
- Ask pet care questions (answers from Dr. Pablo's knowledge base)
- Book and manage appointments via natural conversation
- Order and reorder products
- Access their pet's information and records
- Upload documents and photos
- Communicate with the clinic (replaces WhatsApp)

### Admin/Staff AI Agent

Dr. Pablo and staff can:
- Perform all CRUD operations via natural language
- Create and manage content
- Search across all data instantly
- Manage appointments and scheduling
- Process uploaded documents with OCR/vision
- Manage inventory and orders
- View reports and analytics

## Scope Boundaries

### IN SCOPE (v2.2 - 26 User Stories)

**Epoch 1: Foundation + AI Core (4 Stories)**
- S-001: Django modular architecture, auth, multilingual
- S-002: AI chat interface (customer + admin)
- S-011: Knowledge base admin for AI content
- S-023: **CRITICAL** Data migration from OkVet.co

**Epoch 2: Appointments + Pets (6 Stories)**
- S-003: Pet profiles with medical records
- S-004: Appointment booking via AI conversation
- S-012: Notifications and reminders (vaccination, appointments)
- S-013: Document management with OCR/vision
- S-021: External services (outsourced grooming, boarding referrals)
- S-022: International travel certificates

**Epoch 3: E-Commerce + Billing (4 Stories)**
- S-005: Product catalog, cart, checkout
- S-010: Pharmacy management (prescriptions, controlled substances)
- S-020: Billing & invoicing (Stripe, CFDI, B2B accounts)
- S-024: Inventory management (stock, expiry, reorder)

**Epoch 4: Communications Hub (3 Stories)**
- S-006: Omnichannel communications (WhatsApp, SMS, email)
- S-015: Emergency services (after-hours triage, on-call)
- S-025: Referral network (specialists, visiting vets)

**Epoch 5: CRM + Intelligence + Marketing (6 Stories)**
- S-007: CRM and intelligence (owner profiles)
- S-009: Competitive intelligence (competitor tracking)
- S-014: Reviews and testimonials
- S-016: Loyalty and rewards program
- S-018: SEO and content marketing
- S-019: Email marketing campaigns

**Epoch 6: Practice Management (3 Stories)**
- S-008: Practice management (staff tools, compliance)
- S-017: Reports and analytics dashboards
- S-026: Full double-entry accounting (AP/AR, bank reconciliation)

### OUT OF SCOPE (Future versions)

- Native mobile app
- Real-time video consultations
- Full EMR system (beyond current medical records)
- Multi-location support

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| WhatsApp API approval | High | Apply early, have SMS fallback |
| AI response quality | High | Knowledge base curation, human escalation |
| Payment processing MX | Medium | Stripe available, PayPal backup |
| Content not provided | Medium | Placeholder structure, iterate |
| Translation quality | Medium | Native speaker review |
| Complex integration | Medium | Modular architecture, incremental delivery |

## Success Criteria

### Technical Metrics
- [ ] >95% test coverage across all modules
- [ ] <200ms API response (95th percentile)
- [ ] <2s page load time
- [ ] 99.9% uptime

### Business Metrics
- [ ] 50% reduction in phone inquiries (measured vs baseline)
- [ ] Online appointments adopted by 30% of clients within 3 months
- [ ] E-commerce generating revenue within 1 month of launch
- [ ] Positive client feedback on AI interactions

### User Experience
- [ ] Users can complete common tasks via chat
- [ ] Bilingual content quality approved by native speakers
- [ ] Mobile-first design works on all devices
- [ ] AI provides accurate, helpful responses

## Information Needed from Client

### Required (Before Epoch 1)
1. Full list of veterinary services offered
2. Business hours (regular and emergency)
3. Complete address (for maps and SEO)
4. Phone number(s) and email
5. Dr. Pablo's bio and professional photo
6. Payment preferences (Stripe account setup)

### Required (Before Epoch 2)
7. Service pricing (if public)
8. Appointment types and durations
9. Pet intake questionnaire content

### Required (Before Epoch 3)
10. Product inventory list (or initial categories)
11. Product images and descriptions
12. Shipping/pickup policies

### Desired (Can Add Incrementally)
- Photos of clinic, staff, facility
- Client testimonials
- FAQ content for AI knowledge base
- Social media links
- Common pet care questions and answers

## Epoch-Based Timeline

| Epoch | Focus | Stories | Deliverable |
|-------|-------|---------|-------------|
| 1 | Foundation + AI Core | 4 | Site with AI chat, data migration from OkVet.co |
| 2 | Appointments + Pets | 6 | Booking, pet records, travel certificates, external services |
| 3 | E-Commerce + Billing | 4 | Store, pharmacy, CFDI billing, inventory management |
| 4 | Communications Hub | 3 | WhatsApp, SMS, emergency services, referral network |
| 5 | CRM + Intelligence + Marketing | 6 | CRM, reviews, loyalty program, SEO, email marketing |
| 6 | Practice Management | 3 | Staff tools, reports/analytics, full accounting |

**Total: 26 User Stories across 6 Epochs**

**Note:** Epochs are delivered incrementally. Each epoch is a complete, working system.

## Competitor Research Reference

See the master plan document for detailed competitor analysis:
- 6 veterinary software platforms analyzed (OkVet, ezyVet, Digitail, etc.)
- 5 local Puerto Morelos competitors documented
- Market opportunity assessment
- Competitive positioning strategy

**Key Finding:** First mover advantage - no local competitor has a real website.

## Approval

This Project Charter requires client approval before proceeding to BUILD phase.

---

**Prepared by:** Nestor Wheelock - South City Computer
**Date:** December 21, 2025
**Status:** AWAITING CLIENT APPROVAL
**Previous Version:** v2.1.0 (AI-First + Billing/Marketing)
**Current Version:** v2.2.0 (Complete SPEC - 26 Stories, 9 Modules)
