# SPEC Summary: Pet-Friendly Website

## Quick Reference

| Story | Title | Priority | Estimate | Sprint |
|-------|-------|----------|----------|--------|
| S-001 | Bilingual Public Website | High | 3 days | Sprint 1 |
| S-002 | Appointment Booking System | High | 4 days | Sprint 1 |
| S-003 | E-Commerce Pet Store | High | 6 days | Sprint 2 |
| S-004 | Pharmacy Information | Medium | 1 day | Sprint 2 |
| S-005 | Admin Dashboard | High | 2 days | Sprint 1 |

**Total Estimate:** 16 days (~128 hours human-equivalent)

## Sprint Plan

### Sprint 1: Core Website + Appointments (9 days)
- S-001: Bilingual Public Website
- S-002: Appointment Booking System
- S-005: Admin Dashboard

**Deliverable:** Functional bilingual website with appointment requests

### Sprint 2: E-Commerce + Pharmacy (7 days)
- S-003: E-Commerce Pet Store
- S-004: Pharmacy Information

**Deliverable:** Full e-commerce functionality and pharmacy info

## Technical Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │
│  │   HTMX      │ │  Alpine.js  │ │  Tailwind   │        │
│  │ (AJAX/Forms)│ │ (Cart State)│ │   (CSS)     │        │
│  └─────────────┘ └─────────────┘ └─────────────┘        │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    BACKEND (Django)                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │
│  │    Views    │ │   Models    │ │    i18n     │        │
│  │ (Templates) │ │  (ORM/DB)   │ │ (ES/EN)     │        │
│  └─────────────┘ └─────────────┘ └─────────────┘        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │
│  │   Admin     │ │   Email     │ │  Payments   │        │
│  │ (Dashboard) │ │  (SMTP)     │ │  (Stripe)   │        │
│  └─────────────┘ └─────────────┘ └─────────────┘        │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    DATABASE                              │
│                   PostgreSQL                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │Appointments│ │ Products │ │  Orders  │ │  Users   │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Django Apps Structure

```
petfriendly/
├── config/              # Django project settings
├── apps/
│   ├── core/           # Shared models, utilities
│   ├── pages/          # Static pages (Home, About, Contact, Services)
│   ├── appointments/   # Appointment booking system
│   ├── store/          # E-commerce (Products, Cart, Orders)
│   └── pharmacy/       # Pharmacy information
├── templates/          # HTML templates
├── static/             # CSS, JS, images
├── locale/             # Translation files (ES/EN)
└── manage.py
```

## Key Dependencies

| Package | Purpose |
|---------|---------|
| Django | Web framework |
| django-htmx | HTMX integration |
| django-tailwind | Tailwind CSS |
| django-modeltranslation | Bilingual models |
| stripe | Payment processing |
| Pillow | Image handling |
| psycopg2 | PostgreSQL adapter |
| python-dotenv | Environment variables |

## Risks Summary

1. **Content not ready** - Mitigate with placeholder content
2. **Payment setup** - May need merchant account setup time
3. **Translation quality** - Need native speaker review
4. **Image assets** - Need clinic photos or stock images

## Next Steps

1. Review and approve this SPEC
2. Set up Django project skeleton
3. Begin Sprint 1 development
4. Gather content from client as development progresses

---

**Status:** AWAITING CLIENT APPROVAL
