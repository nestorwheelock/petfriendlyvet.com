# T-007: Services Page

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Full Stack Developer
**Objective**: Implement comprehensive Services page with all service offerings
**Related Story**: S-001
**Estimate**: 2 hours

### Constraints
**Allowed File Paths**: apps/pages/, templates/pages/, apps/services/
**Forbidden Paths**: apps/store/, apps/pharmacy/

### Deliverables
- [ ] Services page view and URL routing
- [ ] Service category models
- [ ] Service detail models
- [ ] Category navigation
- [ ] Service cards with pricing
- [ ] Emergency services section
- [ ] CTA to book appointment

### Wireframe Reference
See: `planning/wireframes/03-services.txt`

### Implementation Details

#### Models
```python
class ServiceCategory(models.Model):
    name = models.CharField(max_length=100)
    name_es = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50)  # Font Awesome or Heroicons
    description = models.TextField()
    order = models.IntegerField(default=0)

class Service(models.Model):
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    name_es = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200)
    description = models.TextField()
    description_es = models.TextField()
    description_en = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    price_text = models.CharField(max_length=100, blank=True)  # "Starting from..."
    duration_minutes = models.IntegerField(null=True)
    requires_appointment = models.BooleanField(default=True)
    is_emergency = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
```

#### Categories
1. **Clínica** (Clinic)
   - Consultations
   - Vaccinations
   - Surgery
   - Dental care
   - Lab work

2. **Farmacia** (Pharmacy)
   - Prescription medications
   - Flea/tick prevention
   - Supplements
   - Specialty diets

3. **Tienda** (Store)
   - Pet food
   - Accessories
   - Toys
   - Grooming supplies

4. **Emergencias** (Emergency)
   - After-hours care
   - Emergency surgery
   - Critical care

#### Page Layout
- Category tabs at top
- Grid of service cards
- Each card: icon, name, description, price, "Book" button
- Emergency section highlighted

### Test Cases
- [ ] All categories load
- [ ] Services filter by category
- [ ] Prices display correctly
- [ ] Bilingual content works
- [ ] Emergency section visible
- [ ] Book buttons work
- [ ] Mobile responsive

### Definition of Done
- [ ] All service categories implemented
- [ ] Admin can manage services
- [ ] Prices editable
- [ ] Responsive design
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-001: Django Project Setup
- T-002: Base Templates
- T-004: Multilingual System
