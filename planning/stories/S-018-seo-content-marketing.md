# S-018: SEO & Content Marketing

> **REQUIRED READING:** Before implementation, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md)

**Story Type:** User Story
**Priority:** Medium
**Epoch:** 5 (with CRM)
**Status:** PENDING
**Module:** django-crm-lite + website app

## User Story

**As a** clinic owner
**I want to** publish pet care content and optimize for search engines
**So that** potential clients find me when searching online

**As a** pet owner
**I want to** find helpful pet care information on the clinic website
**So that** I can learn and trust the clinic's expertise

**As a** marketing manager
**I want to** plan and schedule content across channels
**So that** I maintain consistent online presence

## Acceptance Criteria

### Blog System
- [ ] Create and publish blog posts
- [ ] AI-assisted content generation
- [ ] Categories and tags for organization
- [ ] Author attribution (Dr. Pablo)
- [ ] Auto-translate to all 5 core languages
- [ ] Social sharing buttons
- [ ] Related posts suggestions
- [ ] Comments (optional, moderated)

### Landing Pages
- [ ] Service-specific landing pages
- [ ] Location-based pages (Puerto Morelos, Cancun area)
- [ ] Campaign landing pages with custom URLs
- [ ] A/B testing capability
- [ ] Conversion tracking

### Technical SEO
- [ ] Schema.org markup (LocalBusiness, VeterinaryCare, Product)
- [ ] Dynamic sitemap.xml generation
- [ ] Meta tags management (title, description)
- [ ] Open Graph and Twitter Card tags
- [ ] Canonical URLs for duplicate content
- [ ] robots.txt configuration
- [ ] Page speed optimization
- [ ] Mobile-friendly validation

### Google My Business Integration
- [ ] Sync business hours automatically
- [ ] Post updates to GMB
- [ ] Monitor and respond to Google reviews
- [ ] Q&A management
- [ ] Photo uploads

### Social Media Integration
- [ ] Auto-share new blog posts
- [ ] Instagram feed widget on website
- [ ] Facebook page integration
- [ ] Social proof widgets
- [ ] Share tracking analytics

### Content Calendar
- [ ] Plan posts weeks in advance
- [ ] Visual calendar view
- [ ] Seasonal campaign templates
- [ ] AI suggests content topics
- [ ] Multi-channel scheduling
- [ ] Team collaboration

## Technical Requirements

### Models

```python
class BlogCategory(models.Model):
    """Blog post categories"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    # Translations
    translations = models.JSONField(default=dict)
    # {"en": {"name": "...", "description": "..."}, ...}

    # Display
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=7, default='#4A90A4')
    order = models.IntegerField(default=0)

    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Blog Categories'


class BlogPost(models.Model):
    """Blog post / article"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('review', 'In Review'),
        ('scheduled', 'Scheduled'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    # Identity
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=250)
    excerpt = models.TextField(max_length=500)  # Short summary

    # Content
    content = models.TextField()  # Markdown supported
    featured_image = models.ImageField(upload_to='blog/images/', null=True, blank=True)
    featured_image_alt = models.CharField(max_length=200, blank=True)

    # Classification
    category = models.ForeignKey(BlogCategory, on_delete=models.SET_NULL, null=True)
    tags = models.JSONField(default=list)  # ["vaccination", "puppies", "health"]
    species = models.JSONField(default=list)  # ["dog", "cat", "all"]

    # Authorship
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    author_display_name = models.CharField(max_length=100, blank=True)
    # Override for "Dr. Pablo Rojo Mendoza"

    # Status & Publishing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    published_at = models.DateTimeField(null=True, blank=True)
    scheduled_for = models.DateTimeField(null=True, blank=True)

    # SEO
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    focus_keyword = models.CharField(max_length=100, blank=True)
    canonical_url = models.URLField(blank=True)

    # Translations
    translations = models.JSONField(default=dict)
    # {"en": {"title": "...", "excerpt": "...", "content": "..."}, ...}
    translations_auto_generated = models.BooleanField(default=True)

    # AI-generated
    ai_generated = models.BooleanField(default=False)
    ai_generation_prompt = models.TextField(blank=True)

    # Analytics
    view_count = models.IntegerField(default=0)
    share_count = models.IntegerField(default=0)
    avg_read_time_seconds = models.IntegerField(null=True)

    # Social sharing
    social_shared_at = models.JSONField(default=dict)
    # {"facebook": "2025-01-15T10:00:00", "instagram": null, ...}

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_at', '-created_at']


class LandingPage(models.Model):
    """Custom landing pages for campaigns/services"""
    PAGE_TYPES = [
        ('service', 'Service Page'),
        ('location', 'Location Page'),
        ('campaign', 'Campaign Page'),
        ('promotion', 'Promotion Page'),
    ]

    # Identity
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    page_type = models.CharField(max_length=20, choices=PAGE_TYPES)

    # Content
    hero_headline = models.CharField(max_length=200)
    hero_subheadline = models.TextField(max_length=500, blank=True)
    hero_image = models.ImageField(upload_to='landing/heroes/', null=True, blank=True)
    hero_cta_text = models.CharField(max_length=50, default='Book Now')
    hero_cta_url = models.CharField(max_length=200, blank=True)

    content_blocks = models.JSONField(default=list)
    # [{"type": "text", "content": "..."}, {"type": "cta", "text": "...", "url": "..."}, ...]

    # SEO
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    schema_type = models.CharField(max_length=50, blank=True)
    # VeterinaryCare, Service, LocalBusiness

    # Translations
    translations = models.JSONField(default=dict)

    # Tracking
    utm_source = models.CharField(max_length=100, blank=True)
    utm_medium = models.CharField(max_length=100, blank=True)
    utm_campaign = models.CharField(max_length=100, blank=True)

    # A/B Testing
    is_variant = models.BooleanField(default=False)
    variant_of = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True
    )
    variant_name = models.CharField(max_length=50, blank=True)  # "A", "B", "Control"
    variant_weight = models.IntegerField(default=50)  # Percentage

    # Analytics
    view_count = models.IntegerField(default=0)
    conversion_count = models.IntegerField(default=0)

    # Status
    is_active = models.BooleanField(default=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class SEOMetadata(models.Model):
    """SEO metadata for any page (generic relation)"""
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    # Basic SEO
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    focus_keyword = models.CharField(max_length=100, blank=True)
    secondary_keywords = models.JSONField(default=list)

    # Technical
    canonical_url = models.URLField(blank=True)
    robots = models.CharField(max_length=100, default='index, follow')
    # index,follow / noindex,nofollow / etc.

    # Social
    og_title = models.CharField(max_length=70, blank=True)
    og_description = models.CharField(max_length=200, blank=True)
    og_image = models.ImageField(upload_to='seo/og/', null=True, blank=True)
    twitter_card = models.CharField(max_length=20, default='summary_large_image')

    # Schema.org
    schema_type = models.CharField(max_length=50, blank=True)
    schema_data = models.JSONField(default=dict)

    # Analysis
    seo_score = models.IntegerField(null=True)  # 0-100
    last_analyzed_at = models.DateTimeField(null=True)
    analysis_results = models.JSONField(default=dict)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['content_type', 'object_id']


class ContentCalendarItem(models.Model):
    """Content calendar for planning"""
    CONTENT_TYPES = [
        ('blog', 'Blog Post'),
        ('social', 'Social Media Post'),
        ('email', 'Email Campaign'),
        ('gmb', 'Google My Business Post'),
    ]

    STATUS_CHOICES = [
        ('idea', 'Idea'),
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('review', 'In Review'),
        ('scheduled', 'Scheduled'),
        ('published', 'Published'),
    ]

    # Content
    title = models.CharField(max_length=200)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    description = models.TextField(blank=True)

    # Scheduling
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='idea')

    # Related content
    blog_post = models.ForeignKey(
        BlogPost, on_delete=models.SET_NULL, null=True, blank=True
    )
    email_campaign = models.ForeignKey(
        'EmailCampaign', on_delete=models.SET_NULL, null=True, blank=True
    )

    # Assignment
    assigned_to = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    # Campaign grouping
    campaign_name = models.CharField(max_length=100, blank=True)
    # "Summer Vaccination Drive", "Holiday Grooming", etc.

    # AI suggestions
    ai_suggested = models.BooleanField(default=False)
    ai_suggestion_reason = models.TextField(blank=True)

    # Notes
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['scheduled_date', 'scheduled_time']


class SocialShare(models.Model):
    """Track social media shares"""
    PLATFORMS = [
        ('facebook', 'Facebook'),
        ('twitter', 'Twitter/X'),
        ('instagram', 'Instagram'),
        ('whatsapp', 'WhatsApp'),
        ('linkedin', 'LinkedIn'),
    ]

    # Content
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    platform = models.CharField(max_length=20, choices=PLATFORMS)

    # Tracking
    shared_at = models.DateTimeField(auto_now_add=True)
    shared_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    share_url = models.URLField(blank=True)

    # Analytics (if available from platform)
    clicks = models.IntegerField(default=0)
    impressions = models.IntegerField(default=0)

    class Meta:
        ordering = ['-shared_at']


class GoogleMyBusinessPost(models.Model):
    """Posts to Google My Business"""
    POST_TYPES = [
        ('whats_new', "What's New"),
        ('event', 'Event'),
        ('offer', 'Offer'),
    ]

    post_type = models.CharField(max_length=20, choices=POST_TYPES)
    summary = models.TextField(max_length=1500)

    # Media
    image = models.ImageField(upload_to='gmb/posts/', null=True, blank=True)

    # CTA
    cta_type = models.CharField(max_length=20, blank=True)
    # BOOK, ORDER, LEARN_MORE, SIGN_UP, CALL
    cta_url = models.URLField(blank=True)

    # Event details
    event_title = models.CharField(max_length=200, blank=True)
    event_start = models.DateTimeField(null=True, blank=True)
    event_end = models.DateTimeField(null=True, blank=True)

    # Offer details
    offer_coupon_code = models.CharField(max_length=50, blank=True)
    offer_terms = models.TextField(blank=True)
    offer_start = models.DateTimeField(null=True, blank=True)
    offer_end = models.DateTimeField(null=True, blank=True)

    # Sync status
    gmb_post_id = models.CharField(max_length=100, blank=True)
    synced_at = models.DateTimeField(null=True, blank=True)
    sync_error = models.TextField(blank=True)

    # Status
    is_published = models.BooleanField(default=False)
    scheduled_for = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### AI Tools

```python
SEO_CONTENT_TOOLS = [
    {
        "name": "generate_blog_post",
        "description": "Generate a blog post using AI",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
                "tone": {"type": "string", "enum": ["professional", "friendly", "educational"]},
                "length": {"type": "string", "enum": ["short", "medium", "long"]},
                "species": {"type": "string"},
                "include_cta": {"type": "boolean", "default": True}
            },
            "required": ["topic"]
        }
    },
    {
        "name": "suggest_content_topics",
        "description": "Get AI suggestions for content topics",
        "parameters": {
            "type": "object",
            "properties": {
                "based_on": {"type": "string", "enum": ["trending", "questions", "seasonal", "gaps"]},
                "count": {"type": "integer", "default": 5}
            }
        }
    },
    {
        "name": "analyze_seo",
        "description": "Analyze a page's SEO and get suggestions",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "focus_keyword": {"type": "string"}
            },
            "required": ["url"]
        }
    },
    {
        "name": "optimize_meta_tags",
        "description": "Generate optimized meta title and description",
        "parameters": {
            "type": "object",
            "properties": {
                "page_content": {"type": "string"},
                "focus_keyword": {"type": "string"}
            },
            "required": ["page_content"]
        }
    },
    {
        "name": "get_content_calendar",
        "description": "Get upcoming content calendar items",
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string"},
                "end_date": {"type": "string"},
                "content_type": {"type": "string"}
            }
        }
    },
    {
        "name": "schedule_social_post",
        "description": "Schedule a social media post",
        "parameters": {
            "type": "object",
            "properties": {
                "platform": {"type": "string", "enum": ["facebook", "instagram", "gmb"]},
                "content": {"type": "string"},
                "image_url": {"type": "string"},
                "scheduled_for": {"type": "string"}
            },
            "required": ["platform", "content", "scheduled_for"]
        }
    },
    {
        "name": "create_gmb_post",
        "description": "Create a Google My Business post",
        "parameters": {
            "type": "object",
            "properties": {
                "post_type": {"type": "string", "enum": ["whats_new", "event", "offer"]},
                "summary": {"type": "string"},
                "cta_type": {"type": "string"},
                "cta_url": {"type": "string"}
            },
            "required": ["post_type", "summary"]
        }
    },
    {
        "name": "get_seo_report",
        "description": "Get SEO performance report",
        "parameters": {
            "type": "object",
            "properties": {
                "period": {"type": "string", "default": "last_30_days"}
            }
        }
    }
]
```

## Example AI Conversations

### Content Generation
```
Dr. Pablo: Write a blog post about summer pet safety

AI: I'll create a blog post about summer pet safety.

    📝 Blog Post Generated

    Title: "10 Essential Tips to Keep Your Pet Safe This Summer"

    Excerpt: Learn how to protect your furry friend from heat,
    dehydration, and other summer hazards in Puerto Morelos.

    Preview:
    ---
    Summer in Puerto Morelos brings beautiful weather, but also
    risks for our pets. Here are 10 essential tips...

    1. Never leave pets in parked cars
    2. Provide constant fresh water access
    3. Limit exercise during peak heat (11am-4pm)
    4. Watch for hot pavement...
    ---

    SEO Analysis:
    ✓ Focus keyword: "summer pet safety"
    ✓ Meta description: 158 characters (optimal)
    ✓ Readability: Grade 8 (accessible)
    ✓ Word count: 850 words

    Would you like to:
    1. Edit the content
    2. Translate to other languages
    3. Schedule for publishing
    4. Share to social media when published
```

### Content Calendar
```
Dr. Pablo: What should we post next month?

AI: Here are content suggestions for February 2026:

    📅 Suggested Content Calendar

    Week 1 (Feb 1-7):
    📝 Blog: "Valentine's Day: Pet-Safe Chocolate Alternatives"
       (Reason: Seasonal, high search volume)
    📱 Social: Share photo contest for cutest couples

    Week 2 (Feb 8-14):
    📝 Blog: "Signs of Heartworm: What Every Pet Owner Should Know"
       (Reason: Heartworm awareness month)
    📱 GMB: Valentine's grooming special promotion

    Week 3 (Feb 15-21):
    📝 Blog: "Spay/Neuter Benefits for Your Pet's Health"
       (Reason: National Spay/Neuter Awareness Month)
    📱 Social: Success story from sterilization campaign

    Week 4 (Feb 22-28):
    📝 Blog: "Dental Health Month: Keeping Your Pet's Teeth Clean"
       (Reason: Pet Dental Health Month)
    📱 GMB: Free dental check with any appointment

    Based on:
    • Seasonal relevance
    • National pet awareness days
    • Previous high-performing topics
    • Questions from your AI chat

    Would you like me to add these to the calendar?
```

### SEO Analysis
```
Dr. Pablo: How's our SEO doing?

AI: 📊 SEO Performance Report (Last 30 Days)

    **Overall Health: 78/100** 📈 (+5 from last month)

    🔍 Search Performance:
    • Impressions: 2,450
    • Clicks: 185
    • Average position: 12.3
    • Click-through rate: 7.5%

    🏆 Top Performing Pages:
    1. /servicios/vacunacion - Position 4
    2. /blog/cuidado-cachorro - Position 7
    3. /contacto - Position 8

    ⚠️ Issues to Fix:
    • 3 pages missing meta descriptions
    • 2 images without alt text
    • Mobile speed: 72/100 (could improve)

    💡 Opportunities:
    • "veterinario puerto morelos" - Position 15
      → With optimization, could reach top 10
    • "vacunas perros cancun" - Not ranking
      → Create targeted landing page

    📍 Local SEO:
    • Google Business rating: 4.8 ⭐ (23 reviews)
    • Competitor comparison: #2 in area
    • Missing: More recent photos

    Want me to create a task list for these improvements?
```

## Schema.org Implementation

### LocalBusiness + VeterinaryCare
```json
{
  "@context": "https://schema.org",
  "@type": "VeterinaryCare",
  "name": "Pet-Friendly Veterinaria",
  "image": "https://petfriendlyvet.com/images/clinic.jpg",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "...",
    "addressLocality": "Puerto Morelos",
    "addressRegion": "Quintana Roo",
    "postalCode": "77580",
    "addressCountry": "MX"
  },
  "telephone": "+52-998-316-2438",
  "openingHoursSpecification": [...],
  "priceRange": "$$",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.8",
    "reviewCount": "23"
  }
}
```

## Definition of Done

- [ ] Blog system with CRUD
- [ ] AI content generation
- [ ] Auto-translation to 5 languages
- [ ] Landing page builder
- [ ] SEO metadata management
- [ ] Schema.org markup
- [ ] Sitemap.xml generation
- [ ] Google My Business integration
- [ ] Social media auto-sharing
- [ ] Content calendar
- [ ] SEO analysis and scoring
- [ ] Tests written and passing (>95% coverage)

## Dependencies

- S-001: Foundation (multilingual)
- S-011: Knowledge Base (content management patterns)
- S-014: Reviews (Google reviews integration)

## Notes

- Use Google Search Console API for analytics
- Consider Yoast-like SEO scoring system
- GMB API requires business verification
- Schedule sitemap regeneration on content changes
- Consider AMP for blog posts (future)

## Development Process

**Before implementing this story**, review and follow the **23-Step TDD Cycle** in:
- `CLAUDE.md` - Global development workflow
- `planning/TASK_BREAKDOWN.md` - Specific tasks for this story

Tests must be written before implementation. >95% coverage required.
