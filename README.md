<p align="center">
  <img src="Rectangular.png" alt="Pet-Friendly Veterinary Clinic" width="400">
</p>

# Pet-Friendly Veterinary Clinic (SPEC Phase - Awaiting Approval)

**STATUS**: This project is in SPEC phase. No code has been written yet.
This README guides you through the approval process.

---

## What This Will Be

An **AI-first** multilingual platform for **Pet-Friendly**, Dr. Pablo's veterinary clinic in Puerto Morelos, Quintana Roo, Mexico.

**Languages:** Spanish, English, German, French, Italian built-in - plus AI-powered translation for 100+ additional languages on-demand.

### The Vision: Conversation as Interface

Instead of navigating menus and filling forms, users **talk** to the website:

> "I need to bring my dog Luna in for her vaccines"
> "What's the best flea medicine for a 10kg cat?"
> "Do you have Hills Science Diet in stock?"
> "When is Dr. Pablo available this week?"

The AI understands context, remembers pet information, and handles everything from questions to appointments to purchases.

### Three Service Lines

1. **Clínica** - Veterinary consultations, vaccinations, surgery, emergency care
2. **Farmacia** - Prescription medications, supplements, flea/tick prevention
3. **Tienda** - Pet food, toys, accessories, grooming supplies

### Key Features

| Feature | Description |
|---------|-------------|
| AI Chat Interface | Natural language for all interactions |
| Multilingual | 5 core + AI translation for 100+ languages |
| Online Appointments | Book via conversation with AI |
| E-Commerce Store | Full product catalog and checkout |
| Pet Records | Owners can access their pet's information |
| Omnichannel | WhatsApp, SMS, email - unified inbox |
| Mobile-First Admin | Custom dashboard for Dr. Pablo |

### Technology Stack

- **Backend**: Django 5.x (Python)
- **Frontend**: HTMX + Alpine.js + Tailwind CSS
- **AI**: OpenRouter (Claude) with tool calling
- **Database**: PostgreSQL
- **Payments**: Stripe
- **Communications**: Twilio + WhatsApp Business API

### Architecture: Reusable Modules

Built as **9 pip-installable packages** that can be reused across other businesses:

| Package | Purpose |
|---------|---------|
| django-multilingual | AI-powered translation |
| django-appointments | Service booking |
| django-simple-store | E-commerce + inventory |
| django-ai-assistant | AI chat + tools |
| django-crm-lite | Contact management |
| django-omnichannel | Multi-channel communications |
| django-competitive-intel | Competitor tracking + intelligence |
| django-vet-clinic | Pet profiles + medical records |
| django-accounting | Full double-entry accounting |

---

## SPEC Documents for Review

Please review these planning documents before approving:

### Core Documents
- **[Project Charter](planning/PROJECT_CHARTER.md)** - What, Why, How, Success Criteria, Risks
- **[SPEC Summary](planning/SPEC_SUMMARY.md)** - Architecture overview and epoch roadmap

### User Stories (Features by Epoch)

**Epoch 1: Foundation + AI Core**
- **[S-001: Foundation + AI Core](planning/stories/S-001-foundation-ai-core.md)** - Django setup, auth, multilingual, AI service
- **[S-002: AI Chat Interface](planning/stories/S-002-ai-chat-interface.md)** - Customer and admin chat widgets
- **[S-011: Knowledge Base Admin](planning/stories/S-011-knowledge-base-admin.md)** - AI content management
- **[S-023: Data Migration](planning/stories/S-023-data-migration.md)** - OkVet.co import (CRITICAL)

**Epoch 2: Appointments + Pets**
- **[S-003: Pet Profiles + Medical Records](planning/stories/S-003-pet-profiles-medical-records.md)** - Pet data and health records
- **[S-004: Appointment Booking via AI](planning/stories/S-004-appointment-booking-ai.md)** - Conversational scheduling
- **[S-012: Notifications & Reminders](planning/stories/S-012-notifications-reminders.md)** - Vaccination, appointment reminders
- **[S-013: Document Management](planning/stories/S-013-document-management.md)** - Upload, OCR, medical documents
- **[S-021: External Services](planning/stories/S-021-external-services.md)** - Outsourced grooming, boarding referrals
- **[S-022: Travel Certificates](planning/stories/S-022-travel-certificates.md)** - International health certificates

**Epoch 3: E-Commerce + Billing**
- **[S-005: E-Commerce Store](planning/stories/S-005-ecommerce-store.md)** - Product catalog and checkout
- **[S-010: Pharmacy Management](planning/stories/S-010-pharmacy-management.md)** - Prescriptions, refills, controlled substances
- **[S-020: Billing & Invoicing](planning/stories/S-020-billing-invoicing.md)** - Stripe, CFDI, B2B accounts, discounts
- **[S-024: Inventory Management](planning/stories/S-024-inventory-management.md)** - Stock tracking, expiry, reorder alerts

**Epoch 4: Communications Hub**
- **[S-006: Omnichannel Communications](planning/stories/S-006-omnichannel-communications.md)** - WhatsApp, SMS, unified inbox
- **[S-015: Emergency Services](planning/stories/S-015-emergency-services.md)** - After-hours triage, on-call management
- **[S-025: Referral Network](planning/stories/S-025-referral-network.md)** - Specialists, visiting vets, referral tracking

**Epoch 5: CRM + Intelligence + Marketing**
- **[S-007: CRM + Intelligence](planning/stories/S-007-crm-intelligence.md)** - Owner profiles, marketing
- **[S-009: Competitive Intelligence](planning/stories/S-009-competitive-intelligence.md)** - Competitor tracking, market analysis
- **[S-014: Reviews & Testimonials](planning/stories/S-014-reviews-testimonials.md)** - Client reviews, Google integration
- **[S-016: Loyalty & Rewards](planning/stories/S-016-loyalty-rewards.md)** - Points, tiers, referral program
- **[S-018: SEO & Content Marketing](planning/stories/S-018-seo-content-marketing.md)** - Blog, landing pages, technical SEO
- **[S-019: Email Marketing](planning/stories/S-019-email-marketing.md)** - Campaigns, segmentation, automation

**Epoch 6: Practice Management**
- **[S-008: Practice Management](planning/stories/S-008-practice-management.md)** - Staff tools, compliance
- **[S-017: Reports & Analytics](planning/stories/S-017-reports-analytics.md)** - Business intelligence, dashboards
- **[S-026: Accounting](planning/stories/S-026-accounting.md)** - Full double-entry accounting, AP/AR, bank reconciliation

### Wireframes (Visual Layouts)
- **[Wireframes Overview](planning/wireframes/README.md)** - Design patterns and color scheme
- **[Homepage](planning/wireframes/01-homepage.txt)** - Desktop and mobile layouts
- **[About Page](planning/wireframes/02-about.txt)** - Dr. Pablo bio and clinic info
- **[Appointment Form](planning/wireframes/05-appointment.txt)** - AI-powered booking flow
- **[Store & Products](planning/wireframes/06-store.txt)** - Product catalog
- **[Cart & Checkout](planning/wireframes/07-cart-checkout.txt)** - Shopping flow
- **[Competitive Intelligence](planning/wireframes/10-competitive-intelligence.txt)** - Competitor map, pricing, visitor tracking

### Technical Documentation
- **[Architecture Decisions](planning/ARCHITECTURE_DECISIONS.md)** - ADR-001: Monorepo with extractable packages
- **[Coding Standards](planning/CODING_STANDARDS.md)** - TDD rules, import rules, code style (REQUIRED READING)
- **[Task Index](planning/TASK_INDEX.md)** - Master reference of all 65 tasks with dependencies
- **[Dependencies](planning/DEPENDENCIES.md)** - Build order and execution phases
- **[Database Schema](planning/DATABASE_SCHEMA.md)** - Complete schema with ~75 tables
- **[AI Tool Schemas](planning/AI_TOOL_SCHEMAS.md)** - 113 AI tools across all modules
- **[Module Interfaces](planning/MODULE_INTERFACES.md)** - API contracts between 9 packages
- **[Prepoch Documentation](planning/PREPOCH.md)** - Pre-Epoch 1 work (temp site, content scraping, assets)

### Spanish Documentation (Documentos en Español)
- **[README (Español)](planning-es/README.md)** - Resumen del proyecto
- **[PROJECT CHARTER (Español)](planning-es/PROJECT_CHARTER.md)** - Carta del proyecto
- **[SPEC SUMMARY (Español)](planning-es/SPEC_SUMMARY.md)** - Resumen de especificaciones
- **[Client Content Requirements](planning-es/REQUISITOS_CONTENIDO_CLIENTE.md)** - Lista de contenido para Dr. Pablo
- **[User Stories (Español)](planning-es/stories/)** - Historias de usuario S-001 a S-006

---

## Scope Summary

### IN SCOPE (6 Epochs, 26 Stories)

| Epoch | Focus | Stories | Deliverable |
|-------|-------|---------|-------------|
| 1 | Foundation + AI Core | 4 | Site with AI chat, data migration |
| 2 | Appointments + Pets | 6 | Booking, pet records, travel certs |
| 3 | E-Commerce + Billing | 4 | Store, pharmacy, billing, inventory |
| 4 | Communications Hub | 3 | WhatsApp, SMS, emergency, referrals |
| 5 | CRM + Intelligence + Marketing | 6 | CRM, reviews, loyalty, SEO, email |
| 6 | Practice Management | 3 | Staff tools, reports, accounting |

### OUT OF SCOPE (Future Versions)
- Native mobile app
- Real-time video consultations
- Full EMR system (beyond basic records)
- Automated inventory management
- Multi-location support

---

## Market Opportunity

Based on our competitor research:

| Competitor | Website | Online Booking | E-Commerce |
|------------|---------|----------------|------------|
| Pet-Friendly | **AI-Powered** | **AI Chat** | **Full Store** |
| Fauna Silvestre | None | None | None |
| La Vet del Puerto | None | None | None |
| Dr. Guillermo | None | None | None |
| Veterinaria Miramar | None | None | None |

**Key Finding:** No veterinary clinic in Puerto Morelos has a real website.

---

## Information Needed from Client

Before BUILD phase begins, please provide:

### Required for Epoch 1
1. Full list of veterinary services offered
2. Business hours (regular and emergency)
3. Complete address for Google Maps
4. Phone number(s) and email
5. Dr. Pablo's bio and professional photo
6. Payment preferences (Stripe account setup)

### Required for Epoch 2
7. Appointment types and durations
8. Pet intake questionnaire content

### Required for Epoch 3
9. Product inventory list (or initial categories)
10. Product images and descriptions

### Desired (Can Add Later)
- Photos of clinic, staff, facility
- Client testimonials
- FAQ content for AI knowledge base
- Social media links
- Common pet care questions and answers

---

## Approval Process

1. Review all SPEC documents linked above
2. Ask questions or request changes
3. Provide required information (services, hours, contact, etc.)
4. Approve the SPEC to begin BUILD phase

### Questions?

Contact the development team with any questions about the scope, features, or technical approach.

---

## What Happens After Approval

Once approved:
- Scope is locked (changes require new approval)
- Development begins following TDD practices
- Epochs are delivered incrementally
- Each epoch is a complete, working system
- Regular progress updates provided

---

**Prepared by**: Nestor Wheelock - South City Computer
**Date**: December 22, 2025
**Status**: AWAITING CLIENT APPROVAL
**Version**: 2.3.0 (Complete SPEC - 26 User Stories, 65 Tasks, 9 Modules)
