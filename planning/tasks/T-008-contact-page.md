# T-008: Contact Page with Map

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Full Stack Developer
**Objective**: Implement Contact page with form, map, hours, and FAQ
**Related Story**: S-001
**Estimate**: 3 hours

### Constraints
**Allowed File Paths**: apps/pages/, templates/pages/, apps/contact/
**Forbidden Paths**: apps/store/, apps/pharmacy/

### Deliverables
- [ ] Contact page view and URL routing
- [ ] Contact form with validation
- [ ] Embedded Google Map
- [ ] Business hours display
- [ ] Click-to-call buttons
- [ ] WhatsApp chat link
- [ ] FAQ accordion
- [ ] Schema.org LocalBusiness markup

### Wireframe Reference
See: `planning/wireframes/04-contact.txt`

### Implementation Details

#### Contact Form
```python
class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    phone = forms.CharField(max_length=20, required=False)
    subject = forms.ChoiceField(choices=[
        ('general', 'General Inquiry'),
        ('appointment', 'Appointment Request'),
        ('emergency', 'Emergency'),
        ('feedback', 'Feedback'),
    ])
    message = forms.CharField(widget=forms.Textarea)
    preferred_contact = forms.ChoiceField(choices=[
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('whatsapp', 'WhatsApp'),
    ])
```

#### Business Hours Model
```python
class BusinessHours(models.Model):
    day = models.IntegerField()  # 0-6 (Mon-Sun)
    open_time = models.TimeField(null=True)
    close_time = models.TimeField(null=True)
    is_closed = models.BooleanField(default=False)
    special_note = models.CharField(max_length=200, blank=True)
```

#### Map Configuration
- Embed Google Maps with marker
- Clinic coordinates: [To be provided]
- Custom marker with clinic logo
- Directions link

#### FAQ Section
- Accordion with HTMX
- Categories: General, Appointments, Payments, Emergency
- Bilingual Q&A content

#### Schema.org Markup
```json
{
  "@context": "https://schema.org",
  "@type": "VeterinaryCare",
  "name": "Pet-Friendly Veterinary Clinic",
  "address": {...},
  "telephone": "+52-998-316-2438",
  "openingHours": [...],
  "priceRange": "$$"
}
```

### Test Cases
- [ ] Form submits successfully
- [ ] Form validation works
- [ ] Email sent on submission
- [ ] Map loads correctly
- [ ] Hours display based on current day
- [ ] "Open Now" indicator works
- [ ] WhatsApp link opens correctly
- [ ] FAQ accordion works
- [ ] Schema.org markup validates

### Definition of Done
- [ ] Form functional with email delivery
- [ ] Map embedded with correct location
- [ ] Hours dynamically displayed
- [ ] FAQ section populated
- [ ] SEO markup in place
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-001: Django Project Setup
- T-002: Base Templates
- T-004: Multilingual System

### Environment Variables
```
GOOGLE_MAPS_API_KEY=
CLINIC_ADDRESS=
CLINIC_LAT=
CLINIC_LNG=
CONTACT_EMAIL_TO=
```
