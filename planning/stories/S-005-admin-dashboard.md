# S-005: Admin Dashboard & Content Management

**Story Type:** User Story
**Priority:** High
**Estimate:** 2 days
**Sprint:** Sprint 1
**Status:** PENDING

## User Story

**As a** clinic administrator
**I want to** manage website content, appointments, and orders from a dashboard
**So that** I can keep the website updated and handle customer requests

## Acceptance Criteria

### Authentication
- [ ] When I visit /admin, I see a login page
- [ ] When I enter valid credentials, I access the admin dashboard
- [ ] When I log out, I'm returned to the public site

### Appointment Management
- [ ] When I view appointments, I see a list with status filters
- [ ] When I click an appointment, I see full details
- [ ] When I confirm an appointment, customer receives email
- [ ] When I cancel an appointment, customer receives email
- [ ] When I view calendar view, I see appointments by date

### Order Management
- [ ] When I view orders, I see a list with status filters
- [ ] When I click an order, I see full details and items
- [ ] When I update order status, customer receives email
- [ ] When I search orders, I can find by customer name or order number

### Product Management
- [ ] When I add a product, it appears in the store
- [ ] When I edit a product, changes appear immediately
- [ ] When I mark a product inactive, it's hidden from store
- [ ] When I update inventory, stock levels update

### Content Management
- [ ] When I edit page content, changes appear on the site
- [ ] When I update service descriptions, they update on Services page
- [ ] When I add/edit staff profiles, About page updates

## Admin Sections

1. **Dashboard** - Overview with recent appointments, orders, low stock alerts
2. **Appointments** - List, calendar view, status management
3. **Orders** - List, detail view, status management
4. **Products** - CRUD, inventory, categories
5. **Categories** - Product category management
6. **Services** - Veterinary service descriptions
7. **Pages** - Static page content (About, Contact info, etc.)
8. **Users** - Staff account management

## Definition of Done

- [ ] Django admin customized for all models
- [ ] Dashboard overview page
- [ ] Appointment management with email triggers
- [ ] Order management with email triggers
- [ ] Product CRUD with image upload
- [ ] Bilingual content fields in admin
- [ ] Admin user roles (if needed)
- [ ] Tests written and passing (>95% coverage)
- [ ] Documentation updated

## Technical Notes

- Leverage Django's built-in admin
- Customize with django-admin-interface or similar for UX
- Use Django signals for email triggers
- Consider django-import-export for bulk product uploads
- Image handling with django-storages (for production)
