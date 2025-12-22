# Wireframes: Pet-Friendly Website

## Overview

This document contains ASCII wireframes for all pages of the Pet-Friendly website. These wireframes define the layout, components, and user flows before implementation.

## Pages Covered

### Existing Wireframes

| Wireframe File | Page(s) | Epoch |
|---------------|---------|-------|
| 01-homepage.txt | Homepage (desktop + mobile) | 1 |
| 02-about.txt | About Dr. Pablo & Clinic | 1 |
| 03-services.txt | Veterinary Services | 1 |
| 04-contact.txt | Contact & Location | 1 |
| 05-appointment.txt | Appointment Booking Form | 2 |
| 06-store.txt | Store Catalog & Product Pages | 3 |
| 07-cart-checkout.txt | Shopping Cart & Checkout | 3 |
| 08-pharmacy.txt | Pharmacy Information | 3 |
| 09-ai-chat.txt | AI Chat Interface (customer + admin) | 1 |
| 10-competitive-intelligence.txt | Competitor Map & Analysis | 5 |
| 11-pet-profile.txt | Pet Profile Dashboard | 2 |
| 12-travel-certificates.txt | Travel Certificate Request Flow | 2 |
| 13-external-services.txt | Partner Directory & Referrals | 2 |

### Wireframes Needed (To Be Created)

| Wireframe File | Page(s) | Epoch | Story |
|---------------|---------|-------|-------|
| 14-inventory-admin.txt | Inventory Management Dashboard | 3 | S-024 |
| 15-billing-admin.txt | Billing & Invoice Management | 3 | S-020 |
| 16-communications-inbox.txt | Unified Inbox (WhatsApp, SMS, Email) | 4 | S-006 |
| 17-emergency-triage.txt | Emergency Services Flow | 4 | S-015 |
| 18-referral-network.txt | Specialists & Visiting Vets | 4 | S-025 |
| 19-crm-dashboard.txt | CRM Owner Profiles | 5 | S-007 |
| 20-loyalty-program.txt | Loyalty Points & Rewards | 5 | S-016 |
| 21-reports-dashboard.txt | Reports & Analytics | 6 | S-017 |
| 22-accounting-dashboard.txt | Accounting Overview | 6 | S-026 |

## Design Patterns

### Color Scheme (from logo)
- **Primary Blue:** #1E4D8C (PET-FRIENDLY text)
- **Secondary Green:** #5FAD41 (CLÍNICA FARMACIA TIENDA)
- **White/Light:** Background, cards
- **Dark Text:** #333333

### Typography
- Headings: Bold sans-serif (similar to logo)
- Body: Clean sans-serif (Inter, Open Sans, or similar)

### Component Patterns

**Header (All Pages)**
- Logo (left)
- Navigation (center)
- Language toggle + Cart icon (right)

**Footer (All Pages)**
- Contact info
- Quick links
- Social media
- Copyright

**Buttons**
- Primary: Blue background, white text
- Secondary: Green background, white text
- Outline: White background, colored border

### Responsive Breakpoints
- Desktop: > 1024px
- Tablet: 768px - 1024px
- Mobile: < 768px

## User Flows

### AI Chat Flow (Primary Interface)
```
Any Page → Chat Widget → Conversation → AI Handles Request
    ├── Information Query → AI Responds
    ├── Appointment Request → AI Books → Confirmation
    ├── Product Question → AI Shows Products → Add to Cart
    └── Pet Question → AI Retrieves Records → Display Info
```

### Appointment Booking Flow
```
Homepage → Services → Book Appointment → Fill Form → Confirmation
    or
Homepage → Book Now CTA → Fill Form → Confirmation
    or
AI Chat → "I need an appointment" → AI Schedules → Confirmation
```

### Shopping Flow
```
Homepage → Store → Category → Product → Add to Cart →
Cart → Checkout → Payment → Order Confirmation
    or
AI Chat → "I need flea medicine" → AI Shows Options → Add to Cart
```

### Travel Certificate Flow
```
Pet Profile → Travel Plans → Select Destination →
Requirements Checklist → Schedule Exam → Certificate Issued
```

### Emergency Flow
```
Homepage → Emergency Button → Triage Questions →
Severity Assessment → Action (Escalate/Advice/Schedule)
```

### Referral Flow
```
Pet Record → Referral Needed → Find Specialist →
Create Referral → Send → Track Status → Receive Report
```

### Information Flow
```
Homepage → About/Services/Contact/Pharmacy → Details
```

## Accessibility Notes

- All images need alt text
- Form fields need labels
- Color contrast must meet WCAG AA
- Keyboard navigation support
- Screen reader friendly structure

## Implementation Notes

- Use Tailwind CSS for styling
- HTMX for dynamic interactions
- Alpine.js for cart state and UI state
- All text must support multilingual (ES/EN/DE/FR/IT + AI on-demand)
- AI Chat widget present on all pages (bottom-right corner)
- Mobile-first design approach
- Admin wireframes should support mobile access (Dr. Pablo uses phone)

---

**Version:** 2.2.0
**Stories Covered:** 26 user stories across 6 epochs
**Date:** December 21, 2025
