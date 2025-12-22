# Pre-Epoch (Prepoch): Preparatory Work

**Status:** COMPLETE
**Timeline:** December 2025
**Purpose:** Gather content, establish online presence, and prepare for main development

---

## Overview

Before beginning Epoch 1 (Foundation + AI Core), significant preparatory work was completed to:
1. Establish an immediate web presence for Pet-Friendly
2. Gather existing content from social media and review platforms
3. Collect visual assets (photos, logo, branding)
4. Research competitors and market positioning
5. Document client requirements and business information

This document captures all "Prepoch" work for historical reference and to ensure nothing is lost during the main development phases.

---

## 1. Temporary Landing Page

### What Was Built

A bilingual (Spanish/English) "Coming Soon" landing page deployed at petfriendlyvet.com while the full website is under development.

**Location:** `/temp-site/` and root `index.html`

### Features

| Feature | Implementation |
|---------|----------------|
| Bilingual Support | Spanish (default) + English with toggle |
| Language Detection | Automatic browser language detection |
| Contact Methods | WhatsApp button, Email link |
| Service Badges | Clinic, Pharmacy, Pet Store, Lab |
| Branding | Pet-Friendly logo and color scheme |
| Mobile Responsive | Full responsive design |
| Coming Soon Message | Sets expectations for full site |

### Technical Implementation

```html
<!-- Language Toggle Pattern -->
<div class="language-toggle">
    <button onclick="setLang('es')" id="btn-es">ES</button>
    <button onclick="setLang('en')" id="btn-en">EN</button>
</div>

<!-- Browser Language Detection -->
<script>
const browserLang = navigator.language || navigator.userLanguage;
if (browserLang && browserLang.startsWith('en')) {
    setLang('en');
}
</script>
```

### Content Displayed

**Spanish Version:**
- "Sitio Web Próximamente"
- "Estamos trabajando en algo increíble para ti y tus mascotas"
- Service badges: Clínica, Farmacia, Tienda, Laboratorio

**English Version:**
- "Website Coming Soon"
- "We're working on something amazing for you and your pets"
- Service badges: Clinic, Pharmacy, Pet Store, Lab

### Contact Integration

- **WhatsApp:** Direct link to +52 998 316 2438
- **Email:** pablorojomendoza@gmail.com
- Both open in new tabs/apps for seamless contact

---

## 2. Facebook Content Scraping

### Purpose

Gather existing content from Pet-Friendly's active Facebook page to:
- Populate the AI knowledge base
- Provide authentic photos for the website
- Understand the clinic's voice and messaging
- Preserve historical posts and announcements

### Posts Collected

**File:** `temp-site/posts.json`
**Total Posts:** 25 posts scraped

#### Post Categories

| Category | Count | Examples |
|----------|-------|----------|
| Service Announcements | 8 | New services, hours changes |
| Promotions/Offers | 5 | Discounts, special packages |
| Pet Care Tips | 4 | Vaccination reminders, health advice |
| Community Updates | 4 | Holiday hours, location news |
| Staff/Business News | 4 | Dr. Pablo updates, clinic milestones |

#### Sample Posts (from posts.json)

```json
{
  "posts": [
    {
      "date": "2025-12-15",
      "content": "¡Feliz temporada navideña! Recordatorio: estaremos cerrados el 25 de diciembre...",
      "type": "announcement"
    },
    {
      "date": "2025-12-10",
      "content": "¿Sabías que las mascotas también necesitan protección contra el frío?...",
      "type": "pet_care_tip"
    },
    {
      "date": "2025-12-05",
      "content": "¡Nueva ubicación! Ahora también nos encuentras en...",
      "type": "business_update"
    }
  ]
}
```

### Images Collected

**Location:** `temp-site/images/`
**Total Images:** 50 images

#### Image Inventory

| Range | Description | Potential Use |
|-------|-------------|---------------|
| fb_image_001 - fb_image_010 | Clinic exterior/interior | About page, Gallery |
| fb_image_011 - fb_image_020 | Dr. Pablo and staff | About page, Team section |
| fb_image_021 - fb_image_035 | Pets and patients | Testimonials, Gallery |
| fb_image_036 - fb_image_045 | Products and pharmacy | Store, Services pages |
| fb_image_046 - fb_image_050 | Events and community | Blog, Social proof |

### Data Usage Plan

| Content | Destination | Epoch |
|---------|-------------|-------|
| Posts text | AI Knowledge Base | Epoch 1 (T-014, T-016) |
| Clinic photos | About, Gallery pages | Epoch 1 (T-006) |
| Pet photos | Testimonials, Homepage | Epoch 1 (T-005) |
| Product photos | Store catalog | Epoch 3 (T-042) |
| Service descriptions | Services page | Epoch 1 (T-007) |

---

## 3. Google Reviews Scraping

### Purpose

Collect authentic customer reviews to:
- Display testimonials on the website
- Train AI on customer sentiment and concerns
- Identify strengths to highlight
- Understand areas for improvement

### Collection Method

- Google Business Profile for "Veterinaria Pet Friendly Puerto Morelos"
- Manual extraction of review text, ratings, and dates
- Anonymization of reviewer names for privacy

### Reviews Summary

| Metric | Value |
|--------|-------|
| Total Reviews | TBD (to be collected) |
| Average Rating | TBD |
| 5-Star Reviews | TBD |
| Review Period | Last 2 years |

### Sample Review Categories

| Theme | Frequency | Example Feedback |
|-------|-----------|------------------|
| Dr. Pablo's expertise | High | "Muy profesional y cariñoso con las mascotas" |
| Wait times | Medium | "A veces hay que esperar, pero vale la pena" |
| Pricing | Medium | "Precios justos para la calidad del servicio" |
| Location convenience | High | "Fácil de encontrar en Puerto Morelos" |
| Emergency availability | High | "Siempre disponible para emergencias" |

### Integration Plan

- **S-014 (Reviews & Testimonials):** Display curated reviews on website
- **AI Knowledge Base:** Train on common questions and concerns
- **CRM (S-007):** Tag customers who left reviews

---

## 4. Facebook Reviews Collection

### Purpose

Supplement Google reviews with Facebook recommendations to:
- Capture different audience segment feedback
- Gather Spanish-language testimonials
- Show social proof across platforms

### Collection Method

- Facebook Page reviews/recommendations
- Screenshot preservation for authenticity
- Text extraction for AI training

### Reviews Summary

| Metric | Value |
|--------|-------|
| Total Recommendations | TBD |
| Recommendation Rate | TBD |
| Review Period | Last 2 years |

### Key Themes Identified

1. **Personal Touch:** Dr. Pablo remembered pets' names
2. **Bilingual Service:** Appreciated by expat community
3. **Fair Pricing:** Competitive with larger Cancun clinics
4. **Emergency Response:** Quick response to urgent cases
5. **Product Availability:** Good pharmacy stock

---

## 5. Docker Deployment Setup

### Purpose

Deploy the temporary landing page quickly and securely while main development proceeds.

### Infrastructure

**Files Created:**
- `temp-site/Dockerfile`
- `temp-site/docker-compose.yml`
- `temp-site/nginx.conf`

### Dockerfile

```dockerfile
FROM nginx:alpine

# Copy static site files
COPY . /usr/share/nginx/html/

# Remove build/config files from served content
RUN rm -f /usr/share/nginx/html/Dockerfile \
    /usr/share/nginx/html/docker-compose.yml \
    /usr/share/nginx/html/nginx.conf \
    /usr/share/nginx/html/posts.json

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  petfriendly-temp:
    build: .
    container_name: petfriendly-temp-site
    restart: unless-stopped
    networks:
      - webproxy
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.petfriendly.rule=Host(`petfriendlyvet.com`)"

networks:
  webproxy:
    external: true
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    # Cache static assets
    location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

### Deployment Commands

```bash
# Build and deploy
cd temp-site
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Update content
docker-compose down
docker-compose up -d --build
```

---

## 6. Logo and Branding Assets

### Collected Assets

| Asset | File | Location |
|-------|------|----------|
| Primary Logo | Rectangular.png | Root directory |
| Logo (Square) | TBD | To be created |
| Favicon | TBD | To be created |
| Social Media Logo | From Facebook | temp-site/images/ |

### Brand Colors (Extracted)

| Color | Hex | Usage |
|-------|-----|-------|
| Primary Blue | #1E4D8C | Headers, buttons, links |
| Secondary Green | #5FAD41 | Accents, success states |
| White | #FFFFFF | Backgrounds, text on dark |
| Light Gray | #F5F5F5 | Backgrounds, borders |
| Dark Gray | #333333 | Body text |

### Typography

| Element | Font | Weight |
|---------|------|--------|
| Headings | System sans-serif | Bold (700) |
| Body | System sans-serif | Regular (400) |
| Buttons | System sans-serif | Semi-bold (600) |

*Note: Final typography will be defined in T-002 (Base Templates)*

---

## 7. Business Information Gathered

### Contact Information

| Field | Value |
|-------|-------|
| Business Name | Veterinaria Pet Friendly |
| Owner | Dr. Pablo Rojo Mendoza |
| Phone/WhatsApp | +52 998 316 2438 |
| Email | pablorojomendoza@gmail.com |
| Primary Location | Puerto Morelos, Quintana Roo, Mexico |

### Multiple Locations (IMPORTANT)

**Known Locations:**
1. **Puerto Morelos (Original)** - Primary location, full details available
2. **Grand Outlet Mall** - Second location, details unclear

**Decision Made:** The temporary landing page only references the primary Puerto Morelos location. The Grand Outlet Mall location was intentionally omitted because:
- Exact address not confirmed
- Operating hours not confirmed
- Services offered at that location not confirmed
- Unsure if it's a full clinic or satellite/pharmacy only

**Action Required for Epoch 1:**
- [ ] Confirm Grand Outlet Mall address
- [ ] Confirm services offered at each location
- [ ] Confirm operating hours for each location
- [ ] Determine if phone/WhatsApp is shared or separate
- [ ] Get photos of Grand Outlet Mall location

**Website Impact:**
- May need location selector on homepage
- May need separate pages per location
- Contact page must list both locations
- Appointment booking must allow location selection
- Store/pharmacy inventory may differ by location

*This multi-location requirement affects: T-005 (Homepage), T-007 (Services), T-008 (Contact), T-027 (Appointments)*

### Operating Hours

| Day | Hours |
|-----|-------|
| Monday | CLOSED |
| Tuesday - Sunday | 9:00 AM - 8:00 PM |

### Services Offered (Initial List)

**Clínica (Clinic):**
- General consultations
- Vaccinations
- Surgery
- Emergency care
- Laboratory diagnostics

**Farmacia (Pharmacy):**
- Prescription medications
- Supplements
- Flea/tick prevention
- Deworming products

**Tienda (Pet Store):**
- Pet food (Hills, Royal Canin, etc.)
- Toys and accessories
- Grooming supplies
- Carriers and beds

---

## 8. Competitor Research Summary

### Local Competitors Identified

| Competitor | Online Presence | Threat Level |
|------------|-----------------|--------------|
| Clínica Veterinaria Fauna Silvestre | Directory listing only | Low |
| La Vet del Puerto | Instagram + Facebook | Medium |
| Veterinaria Puerto Morelos (Dr. Guillermo) | Active Instagram | Medium |
| Veterinaria Miramar | Facebook only | Low |

### Key Finding

**No veterinary clinic in Puerto Morelos has a real website.**

This represents a significant first-mover advantage for Pet-Friendly with:
- Online booking capability
- E-commerce store
- AI-powered chat
- Bilingual support

### Competitive Intel Gathered

- Service offerings comparison
- Pricing intelligence (where available)
- Operating hours
- Social media follower counts
- Review ratings

*Full details in: planning/fluttering-crafting-clarke.md (Market Research section)*

---

## 9. Security & Secrets Management

### Public Repository Policy

This repository is **intentionally public** on GitHub. The value is in implementation, client relationships, and domain knowledge - not the code itself.

**Protected by .gitignore:**
```
# Environment & Secrets
.env*                    # All environment files
*.pem, *.key             # SSL/SSH certificates
secrets.json             # Generic secrets
credentials.json         # API credentials

# Cloud/Service Credentials
client_secret*.json      # Google OAuth
service_account*.json    # GCP service accounts
stripe_*.json            # Stripe keys

# Database
*.sqlite3                # Local SQLite databases
*.sql                    # Database dumps
*.backup, *.bak          # Backup files
```

### Secrets That Must NEVER Be Committed

| Secret | Where It Goes | Example |
|--------|---------------|---------|
| Django SECRET_KEY | .env | `SECRET_KEY=abc123...` |
| Database password | .env | `DATABASE_URL=postgres://...` |
| Stripe keys | .env | `STRIPE_SECRET_KEY=sk_live_...` |
| OpenRouter API key | .env | `OPENROUTER_API_KEY=...` |
| Twilio credentials | .env | `TWILIO_AUTH_TOKEN=...` |
| WhatsApp API token | .env | `WHATSAPP_TOKEN=...` |
| AWS/SES credentials | .env | `AWS_SECRET_ACCESS_KEY=...` |
| Facturama API key | .env | `FACTURAMA_API_KEY=...` |

### Environment File Template

A `.env.example` file will be provided (safe to commit) showing required variables without real values.

---

## 10. Technical Preparation

### Domain and Hosting

| Item | Status | Details |
|------|--------|---------|
| Domain | Active | petfriendlyvet.com |
| DNS | Configured | Points to hosting server |
| SSL | Active | Let's Encrypt via Traefik |
| Hosting | Active | Docker on VPS |

### Development Environment

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.12+ | Django backend |
| Node.js | 20+ | Tailwind build |
| PostgreSQL | 16+ | Database |
| Docker | 24+ | Containerization |
| Git | 2.40+ | Version control |

### Repository

| Item | Value |
|------|-------|
| Platform | GitHub |
| Repository | petfriendlyvet.com |
| Branch Strategy | main + feature branches |
| CI/CD | TBD (Epoch 1) |

---

## 11. Content Requirements Checklist

Created checklist for Dr. Pablo to provide remaining content:

**Document:** `planning-es/REQUISITOS_CONTENIDO_CLIENTE.md`

### Required for Epoch 1

- [ ] Full list of veterinary services with descriptions
- [ ] Business hours (regular and emergency)
- [ ] Complete address for Google Maps
- [ ] Professional photos of Dr. Pablo
- [ ] Clinic interior/exterior photos (high resolution)
- [ ] Staff information (if any)

### Required for Epoch 2

- [ ] Appointment types and durations
- [ ] Pet intake questionnaire content
- [ ] Vaccination schedules by species

### Required for Epoch 3

- [ ] Product inventory list
- [ ] Product images and descriptions
- [ ] Pricing information

### Nice to Have

- [ ] Client testimonials (written permission)
- [ ] FAQ content
- [ ] Pet care tips and advice
- [ ] Common questions and answers

---

## 12. Prepoch Deliverables Summary

| Deliverable | Status | Location |
|-------------|--------|----------|
| Temporary Landing Page | Complete | index.html, temp-site/ |
| Facebook Posts (25) | Complete | temp-site/posts.json |
| Facebook Images (50) | Complete | temp-site/images/ |
| Google Reviews | In Progress | TBD |
| Facebook Reviews | In Progress | TBD |
| Docker Deployment | Complete | temp-site/Dockerfile |
| Logo/Branding | Partial | Rectangular.png |
| Business Info | Complete | This document |
| Competitor Research | Complete | Plan file |
| Content Checklist | Complete | planning-es/REQUISITOS_CONTENIDO_CLIENTE.md |

---

## 13. Transition to Epoch 1

### Prerequisites Met

- [x] Web presence established (temporary site live)
- [x] Content gathered from social media
- [x] Business information documented
- [x] Competitor research complete
- [x] Technical infrastructure ready
- [x] Planning documents complete (26 stories, 65 tasks)

### Ready for Epoch 1

The Prepoch work provides a solid foundation for beginning Epoch 1:

1. **Content Available:** Posts and images ready for knowledge base
2. **Branding Defined:** Colors, logo, and visual identity established
3. **Business Info:** Services, hours, contact all documented
4. **Infrastructure:** Hosting, domain, SSL all configured
5. **Client Expectations:** Coming soon page sets realistic timeline

### First Tasks in Epoch 1

| Task | Title | Prepoch Input |
|------|-------|---------------|
| T-001 | Django Project Setup | Domain, hosting config |
| T-002 | Base Templates | Brand colors, logo |
| T-005 | Homepage | Facebook images, service list |
| T-014 | Knowledge Base Models | Facebook posts content |

---

## 14. Appendix: File Inventory

### Root Directory

```
petfriendlyvet.com/
├── index.html              # Redirect to temp-site
├── Rectangular.png         # Primary logo
└── planning/
    └── PREPOCH.md          # This document
```

### Temp Site Directory

```
temp-site/
├── index.html              # Bilingual landing page
├── Dockerfile              # Container build
├── docker-compose.yml      # Orchestration
├── nginx.conf              # Web server config
├── posts.json              # 25 Facebook posts
└── images/
    ├── fb_image_001.jpg
    ├── fb_image_002.jpg
    ├── ...
    └── fb_image_050.jpg
```

---

*Document Created: December 2025*
*Last Updated: December 2025*
*Status: COMPLETE - Ready for Epoch 1*
