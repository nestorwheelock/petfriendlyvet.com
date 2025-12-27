# T-005: Homepage Implementation

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md and [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Full Stack Developer
**Objective**: Implement responsive homepage with hero, services, and location
**Related Story**: S-001
**Estimate**: 4 hours

### Constraints
**Allowed File Paths**: apps/pages/, templates/pages/, static/
**Forbidden Paths**: apps/store/, apps/pharmacy/

### Deliverables
- [ ] Homepage view and URL routing
- [ ] Hero section with CTA
- [ ] Services overview grid
- [ ] About Dr. Pablo preview section
- [ ] Location with embedded map
- [ ] AI chat widget teaser
- [ ] Mobile-responsive layout

### Wireframe Reference
See: `planning/wireframes/01-homepage.txt`

### Implementation Details

#### Sections
1. **Hero**
   - Background image (clinic or pet)
   - Headline (bilingual)
   - Subheadline
   - CTA buttons: "Book Appointment", "Chat with AI"

2. **Services Overview**
   - 3-column grid (Clínica, Farmacia, Tienda)
   - Icon, title, brief description
   - "Learn More" links

3. **About Preview**
   - Dr. Pablo photo
   - Brief bio
   - "Read More" link

4. **Location**
   - Embedded Google Map
   - Address text
   - Hours
   - Contact buttons (call, WhatsApp)

5. **AI Chat Teaser**
   - "Ask our AI assistant" prompt
   - Example questions
   - Floating chat button

#### Template Structure
```html
{% extends "base.html" %}
{% load i18n %}

{% block content %}
<section id="hero">...</section>
<section id="services">...</section>
<section id="about">...</section>
<section id="location">...</section>
{% endblock %}

{% block chat_widget %}
{% include "components/chat_widget.html" %}
{% endblock %}
```

### Tailwind Classes
- Hero: `min-h-screen bg-cover bg-center`
- Services grid: `grid grid-cols-1 md:grid-cols-3 gap-6`
- Cards: `bg-white rounded-xl shadow-lg p-6`
- CTA buttons: `bg-primary hover:bg-primary-dark text-white rounded-full px-6 py-3`

### Test Cases
- [ ] Homepage loads without errors
- [ ] All sections render correctly
- [ ] Mobile layout stacks properly
- [ ] Bilingual content switches
- [ ] CTA buttons link correctly
- [ ] Map embed loads
- [ ] Chat widget appears
- [ ] Page passes accessibility audit

### Definition of Done
- [ ] All wireframe sections implemented
- [ ] Responsive on mobile, tablet, desktop
- [ ] Bilingual content working
- [ ] Performance optimized (< 3s load)
- [ ] Tests written and passing (>95% coverage)
- [ ] Documentation updated

### Dependencies
- T-001: Django Project Setup
- T-002: Base Templates
- T-004: Multilingual System
