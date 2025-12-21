# Task Breakdown: Pet-Friendly Website v2.2

## Overview

This document provides a high-level task breakdown organized by epoch.
Detailed task specifications will be created as each epoch begins.

**Total: 26 User Stories across 6 Epochs**
**Reusable Modules: 9 pip-installable Django packages**

---

## Epoch 1: Foundation + AI Core

**Stories:** S-001, S-002, S-011, S-023
**Priority:** Critical
**Deliverable:** Functional bilingual website with AI chat and migrated data

### S-001: Foundation + AI Core
| Task | Title | Estimate | Status |
|------|-------|----------|--------|
| T-001 | Django project setup (9 packages) | 4h | Pending |
| T-002 | Base templates & Tailwind layout | 4h | Pending |
| T-003 | Authentication (Google OAuth + email) | 4h | Pending |
| T-004 | Multilingual system (5 core languages) | 4h | Pending |
| T-005 | Homepage implementation | 4h | Pending |
| T-006 | About page | 2h | Pending |
| T-007 | Services page | 2h | Pending |
| T-008 | Contact page with map | 3h | Pending |

### S-002: AI Chat Interface
| Task | Title | Estimate | Status |
|------|-------|----------|--------|
| T-009 | AI service layer (OpenRouter) | 6h | Pending |
| T-010 | Tool calling framework | 6h | Pending |
| T-011 | Customer chat widget | 4h | Pending |
| T-012 | Admin chat interface | 4h | Pending |
| T-013 | Chat history persistence | 3h | Pending |

### S-011: Knowledge Base Admin
| Task | Title | Estimate | Status |
|------|-------|----------|--------|
| T-014 | Knowledge base models | 3h | Pending |
| T-015 | Custom admin for content | 4h | Pending |
| T-016 | AI context injection | 3h | Pending |

### S-023: Data Migration (CRITICAL)
| Task | Title | Estimate | Status |
|------|-------|----------|--------|
| T-017 | OkVet.co export research | 4h | Pending |
| T-018 | Migration models & tracking | 4h | Pending |
| T-019 | Client import command | 4h | Pending |
| T-020 | Pet import command | 4h | Pending |
| T-021 | Medical records import | 6h | Pending |
| T-022 | Vaccination import | 3h | Pending |
| T-023 | Migration verification | 4h | Pending |

**Epoch 1 Subtotal:** ~82 hours

---

## Epoch 2: Appointments + Pets

**Stories:** S-003, S-004, S-012, S-013, S-021, S-022
**Priority:** Critical
**Deliverable:** Booking, pet records, travel certificates, external services

### S-003: Pet Profiles + Medical Records
- Pet model with medical history
- Vaccination tracking
- Conditions and allergies
- Weight history
- Pet profile dashboard

### S-004: Appointment Booking via AI
- Appointment models
- Service types and durations
- Calendar integration
- AI booking conversation flow
- Confirmation workflow

### S-012: Notifications & Reminders
- Reminder models and scheduling
- Vaccination due reminders
- Appointment reminders
- Multi-channel delivery (email, SMS, WhatsApp)

### S-013: Document Management
- Document upload models
- OCR/vision processing
- File organization
- Integration with pet records

### S-021: External Services
- Partner directory models
- Referral tracking
- Boarding stay tracking
- Medication handoff workflow

### S-022: Travel Certificates
- Destination requirements database
- Travel plan tracking
- Health certificate generation (PDF)
- Certificate verification

**Epoch 2 Estimate:** ~100 hours

---

## Epoch 3: E-Commerce + Billing

**Stories:** S-005, S-010, S-020, S-024
**Priority:** High
**Deliverable:** Store, pharmacy, billing, inventory

### S-005: E-Commerce Store
- Product and category models
- Store catalog pages
- Shopping cart (Alpine.js)
- Stripe checkout
- Order management

### S-010: Pharmacy Management
- Prescription models
- Refill workflows
- Controlled substance tracking
- AI prescription assistance

### S-020: Billing & Invoicing
- Invoice models
- Payment processing (Stripe, cash, card)
- CFDI (Mexican tax) integration
- B2B professional accounts
- Discounts and coupons
- Prepaid packages and wellness plans

### S-024: Inventory Management
- Stock level tracking
- Batch/lot and expiry management
- Reorder alerts
- Purchase orders
- Stock counts and adjustments

**Epoch 3 Estimate:** ~120 hours

---

## Epoch 4: Communications Hub

**Stories:** S-006, S-015, S-025
**Priority:** High
**Deliverable:** WhatsApp, SMS, emergency, referrals

### S-006: Omnichannel Communications
- WhatsApp Business API integration
- SMS integration (Twilio)
- Unified inbox
- Message threading
- Template management

### S-015: Emergency Services
- Emergency detection in AI
- Triage questionnaire
- On-call schedule management
- Escalation workflow
- First aid instructions database

### S-025: Referral Network
- Specialist directory
- Visiting specialist schedules
- Outbound referral workflow
- Incoming referral tracking
- Results integration

**Epoch 4 Estimate:** ~80 hours

---

## Epoch 5: CRM + Intelligence + Marketing

**Stories:** S-007, S-009, S-014, S-016, S-018, S-019
**Priority:** Medium
**Deliverable:** CRM, reviews, loyalty, SEO, email

### S-007: CRM + Intelligence
- Owner profile enhancement
- Communication preferences
- Purchase history analysis
- Social media enrichment

### S-009: Competitive Intelligence
- Competitor tracking
- Pricing monitoring
- Visitor IP intelligence
- Market analysis reports

### S-014: Reviews & Testimonials
- Review collection system
- Google Business integration
- Review moderation
- Testimonial display

### S-016: Loyalty & Rewards
- Points system
- Tier management
- Referral program
- Rewards redemption

### S-018: SEO & Content Marketing
- Blog system
- Landing pages
- Schema.org markup
- Sitemap generation

### S-019: Email Marketing
- Newsletter subscriptions
- Campaign builder
- Segmentation
- Automated sequences
- Analytics

**Epoch 5 Estimate:** ~100 hours

---

## Epoch 6: Practice Management

**Stories:** S-008, S-017, S-026
**Priority:** Medium
**Deliverable:** Staff tools, reports, accounting

### S-008: Practice Management
- Staff profiles
- Scheduling
- Clinical notes
- Compliance tracking
- Audit logs

### S-017: Reports & Analytics
- Revenue reports
- Patient statistics
- Appointment analytics
- Inventory reports
- Custom dashboards

### S-026: Accounting
- Chart of accounts
- General ledger
- Accounts payable workflow
- Accounts receivable integration
- Bank reconciliation
- Financial statements
- Budget tracking

**Epoch 6 Estimate:** ~90 hours

---

## Project Summary

| Epoch | Stories | Estimate | Priority |
|-------|---------|----------|----------|
| 1 | 4 | ~82h | Critical |
| 2 | 6 | ~100h | Critical |
| 3 | 4 | ~120h | High |
| 4 | 3 | ~80h | High |
| 5 | 6 | ~100h | Medium |
| 6 | 3 | ~90h | Medium |
| **Total** | **26** | **~572h** | |

### Additional Overhead

| Activity | Estimate |
|----------|----------|
| Testing & QA | 60h |
| Documentation | 20h |
| Deployment & DevOps | 20h |
| Project Management | 20h |
| **Overhead Total** | **120h** |

### Grand Total

**Human-equivalent effort:** ~692 hours
**Estimated AI execution:** 40-60 hours actual work

---

## Pricing (Using AI-Native Workflow)

```
Traditional Development Cost:
692 hours × $50/hour = $34,600.00

AI Automation Discount (65%):
$34,600.00 × 0.65 = -$22,490.00

Final Amount Due: $12,110.00

Client Savings: $22,490.00 (65% off traditional)
```

---

**Version:** 2.2.0
**Stories:** 26
**Modules:** 9
**Date:** December 21, 2025
