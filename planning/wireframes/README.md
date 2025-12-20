# Wireframes: Pet-Friendly Website

## Overview

This document contains ASCII wireframes for all pages of the Pet-Friendly website. These wireframes define the layout, components, and user flows before implementation.

## Pages Covered

| Wireframe File | Page(s) |
|---------------|---------|
| 01-homepage.txt | Homepage (desktop + mobile) |
| 02-about.txt | About Dr. Pablo & Clinic |
| 03-services.txt | Veterinary Services |
| 04-contact.txt | Contact & Location |
| 05-appointment.txt | Appointment Booking Form |
| 06-store.txt | Store Catalog & Product Pages |
| 07-cart-checkout.txt | Shopping Cart & Checkout |
| 08-pharmacy.txt | Pharmacy Information |

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

### Appointment Booking Flow
```
Homepage → Services → Book Appointment → Fill Form → Confirmation
    or
Homepage → Book Now CTA → Fill Form → Confirmation
```

### Shopping Flow
```
Homepage → Store → Category → Product → Add to Cart →
Cart → Checkout → Payment → Order Confirmation
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
- Alpine.js for cart state
- All text must support bilingual (ES/EN)
