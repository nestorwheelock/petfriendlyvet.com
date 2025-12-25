# SEO Module

The `apps.seo` module provides content marketing and SEO tools including blog posts, landing pages, SEO metadata, content calendars, and URL redirects.

## Table of Contents

- [Overview](#overview)
- [Models](#models)
  - [BlogCategory](#blogcategory)
  - [BlogPost](#blogpost)
  - [LandingPage](#landingpage)
  - [SEOMetadata](#seometadata)
  - [ContentCalendarItem](#contentcalendaritem)
  - [Redirect](#redirect)
- [Workflows](#workflows)
- [Integration Points](#integration-points)
- [Query Examples](#query-examples)
- [Testing](#testing)

## Overview

The SEO module provides:

- **Blog Management** - Bilingual blog posts with SEO optimization
- **Landing Pages** - Marketing landing pages with conversion tracking
- **SEO Metadata** - Page-level meta tags, Open Graph, Schema.org
- **Content Calendar** - Plan and schedule content creation
- **URL Redirects** - Manage 301/302 redirects with tracking

## Models

Location: `apps/seo/models.py`

### BlogCategory

Blog post categories with SEO metadata.

```python
class BlogCategory(models.Model):
    name = models.CharField(max_length=100)
    name_es = models.CharField(max_length=100, blank=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', null=True, on_delete=models.SET_NULL, related_name='children')
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
```

### BlogPost

Blog post with full SEO optimization.

```python
STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('review', 'Under Review'),
    ('scheduled', 'Scheduled'),
    ('published', 'Published'),
    ('archived', 'Archived'),
]

class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    title_es = models.CharField(max_length=200, blank=True)
    slug = models.SlugField(unique=True, max_length=200)
    excerpt = models.TextField(blank=True)
    excerpt_es = models.TextField(blank=True)
    content = models.TextField()
    content_es = models.TextField(blank=True)
    author = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    category = models.ForeignKey(BlogCategory, null=True, on_delete=models.SET_NULL)
    tags = models.JSONField(default=list)

    # Images
    featured_image = models.ImageField(upload_to='blog/', blank=True)
    featured_image_alt = models.CharField(max_length=200, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False)

    # SEO
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=200, blank=True)

    # Open Graph
    og_title = models.CharField(max_length=100, blank=True)
    og_description = models.CharField(max_length=200, blank=True)
    og_image = models.ImageField(upload_to='blog/og/', blank=True)

    # Technical SEO
    canonical_url = models.URLField(blank=True)
    schema_markup = models.JSONField(default=dict)

    # Metrics
    view_count = models.IntegerField(default=0)
    reading_time_minutes = models.IntegerField(default=5)  # Auto-calculated

    published_at = models.DateTimeField(null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        # Auto-calculate reading time
        word_count = len(self.content.split())
        self.reading_time_minutes = max(1, word_count // 200)
        super().save(*args, **kwargs)
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `meta_title` | CharField | SEO title (max 70 chars) |
| `meta_description` | CharField | SEO description (max 160 chars) |
| `og_title` | CharField | Open Graph title for social sharing |
| `schema_markup` | JSONField | Structured data (JSON-LD) |
| `reading_time_minutes` | Integer | Auto-calculated from word count |

### LandingPage

Marketing landing pages with conversion tracking.

```python
PAGE_TYPES = [
    ('service', 'Service Page'),
    ('location', 'Location Page'),
    ('campaign', 'Campaign Page'),
    ('seasonal', 'Seasonal Page'),
]

class LandingPage(models.Model):
    title = models.CharField(max_length=200)
    title_es = models.CharField(max_length=200, blank=True)
    slug = models.SlugField(unique=True)
    page_type = models.CharField(max_length=20, choices=PAGE_TYPES)
    headline = models.CharField(max_length=100)
    headline_es = models.CharField(max_length=100, blank=True)
    subheadline = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    content_es = models.TextField(blank=True)
    hero_image = models.ImageField(upload_to='landing/', blank=True)
    cta_text = models.CharField(max_length=50, default='Get Started')
    cta_url = models.CharField(max_length=200, blank=True)
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    schema_markup = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    is_indexed = models.BooleanField(default=True)
    view_count = models.IntegerField(default=0)
    conversion_count = models.IntegerField(default=0)
```

### SEOMetadata

SEO metadata for any page in the site.

```python
class SEOMetadata(models.Model):
    path = models.CharField(max_length=200, unique=True)  # URL path like /services/

    # Basic meta
    title = models.CharField(max_length=70)
    title_es = models.CharField(max_length=70, blank=True)
    description = models.CharField(max_length=160)
    description_es = models.CharField(max_length=160, blank=True)
    keywords = models.CharField(max_length=200, blank=True)
    canonical_url = models.URLField(blank=True)

    # Open Graph
    og_title = models.CharField(max_length=100, blank=True)
    og_description = models.CharField(max_length=200, blank=True)
    og_image = models.URLField(blank=True)

    # Twitter
    twitter_card = models.CharField(max_length=20, default='summary_large_image')
    twitter_title = models.CharField(max_length=100, blank=True)
    twitter_description = models.CharField(max_length=200, blank=True)

    # Technical
    schema_markup = models.JSONField(default=dict)
    robots = models.CharField(max_length=50, default='index, follow')

    # Sitemap
    priority = models.DecimalField(max_digits=2, decimal_places=1, default=0.5)
    changefreq = models.CharField(max_length=20, default='weekly')

    is_active = models.BooleanField(default=True)
```

### ContentCalendarItem

Content calendar for planning.

```python
CONTENT_TYPES = [
    ('blog', 'Blog Post'),
    ('social', 'Social Media'),
    ('email', 'Email Campaign'),
    ('landing', 'Landing Page'),
]

STATUS_CHOICES = [
    ('idea', 'Idea'),
    ('planned', 'Planned'),
    ('in_progress', 'In Progress'),
    ('review', 'Under Review'),
    ('scheduled', 'Scheduled'),
    ('published', 'Published'),
]

class ContentCalendarItem(models.Model):
    title = models.CharField(max_length=200)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='idea')
    description = models.TextField(blank=True)
    target_keywords = models.JSONField(default=list)
    target_audience = models.CharField(max_length=200, blank=True)
    assigned_to = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    planned_date = models.DateField(null=True)
    published_date = models.DateField(null=True)
    blog_post = models.ForeignKey(BlogPost, null=True, on_delete=models.SET_NULL)
    landing_page = models.ForeignKey(LandingPage, null=True, on_delete=models.SET_NULL)
    notes = models.TextField(blank=True)
```

### Redirect

URL redirects with tracking.

```python
REDIRECT_TYPES = [
    (301, 'Permanent (301)'),
    (302, 'Temporary (302)'),
]

class Redirect(models.Model):
    old_path = models.CharField(max_length=500, unique=True)
    new_path = models.CharField(max_length=500)
    redirect_type = models.IntegerField(choices=REDIRECT_TYPES, default=301)
    is_active = models.BooleanField(default=True)
    hit_count = models.IntegerField(default=0)
    last_hit = models.DateTimeField(null=True)
```

## Workflows

### Creating a Blog Post

```python
from apps.seo.models import BlogPost, BlogCategory
from django.utils import timezone

post = BlogPost.objects.create(
    title='10 Tips for Keeping Your Pet Healthy',
    title_es='10 Consejos para Mantener a tu Mascota Saludable',
    slug='10-tips-keeping-pet-healthy',
    excerpt='Essential health tips every pet owner should know.',
    excerpt_es='Consejos esenciales de salud que todo dueño debe conocer.',
    content='Full article content here...',
    content_es='Contenido completo del artículo...',
    author=staff_user,
    category=BlogCategory.objects.get(slug='pet-health'),
    tags=['health', 'prevention', 'wellness'],
    status='draft',
    meta_title='10 Essential Pet Health Tips | Pet Friendly Vet',
    meta_description='Discover 10 expert tips for keeping your pet healthy and happy. From nutrition to exercise, learn what every pet owner needs to know.',
)

# Publish
post.status = 'published'
post.published_at = timezone.now()
post.save()
```

### Setting Up SEO for a Page

```python
from apps.seo.models import SEOMetadata

SEOMetadata.objects.create(
    path='/services/dental/',
    title='Pet Dental Services | Professional Teeth Cleaning',
    title_es='Servicios Dentales para Mascotas | Limpieza Dental Profesional',
    description='Professional dental care for dogs and cats. Teeth cleaning, extractions, and preventive care.',
    description_es='Cuidado dental profesional para perros y gatos. Limpieza, extracciones y cuidado preventivo.',
    og_title='Pet Dental Services',
    og_description='Keep your pet\'s teeth healthy with our professional dental services.',
    schema_markup={
        "@context": "https://schema.org",
        "@type": "Service",
        "name": "Pet Dental Services",
        "provider": {
            "@type": "VeterinaryClinic",
            "name": "Pet Friendly Vet"
        }
    },
    priority=Decimal('0.8'),
    changefreq='monthly',
)
```

### Managing Redirects

```python
from apps.seo.models import Redirect

# Create redirect for old URL
Redirect.objects.create(
    old_path='/old-services/dental-care/',
    new_path='/services/dental/',
    redirect_type=301,
)

# Track hit
def handle_redirect(path):
    try:
        redirect = Redirect.objects.get(old_path=path, is_active=True)
        redirect.hit_count += 1
        redirect.last_hit = timezone.now()
        redirect.save()
        return redirect
    except Redirect.DoesNotExist:
        return None
```

## Integration Points

### With Middleware (Redirect Handling)

```python
# middleware.py
from apps.seo.models import Redirect
from django.shortcuts import redirect

class RedirectMiddleware:
    def __call__(self, request):
        try:
            r = Redirect.objects.get(old_path=request.path, is_active=True)
            r.hit_count += 1
            r.last_hit = timezone.now()
            r.save()
            return redirect(r.new_path, permanent=(r.redirect_type == 301))
        except Redirect.DoesNotExist:
            pass
        return self.get_response(request)
```

### With Templates (Meta Tags)

```python
# views.py
from apps.seo.models import SEOMetadata

def get_seo_context(path):
    try:
        seo = SEOMetadata.objects.get(path=path, is_active=True)
        return {
            'meta_title': seo.title,
            'meta_description': seo.description,
            'og_title': seo.og_title or seo.title,
            'og_description': seo.og_description or seo.description,
            'schema_markup': seo.schema_markup,
        }
    except SEOMetadata.DoesNotExist:
        return {}
```

## Query Examples

```python
from apps.seo.models import (
    BlogPost, BlogCategory, LandingPage, SEOMetadata, ContentCalendarItem, Redirect
)
from django.db.models import Sum

# Published posts
published = BlogPost.objects.filter(
    status='published'
).order_by('-published_at')

# Featured posts for homepage
featured = BlogPost.objects.filter(
    status='published',
    is_featured=True
).order_by('-published_at')[:3]

# Posts by category
category_posts = BlogPost.objects.filter(
    category__slug='pet-health',
    status='published'
)

# Popular posts
popular = BlogPost.objects.filter(
    status='published'
).order_by('-view_count')[:10]

# Landing pages by type
service_pages = LandingPage.objects.filter(
    page_type='service',
    is_active=True
)

# Content calendar - upcoming
upcoming = ContentCalendarItem.objects.filter(
    status__in=['planned', 'in_progress'],
    planned_date__gte=date.today()
).order_by('planned_date')

# Frequently hit redirects
hot_redirects = Redirect.objects.filter(
    is_active=True
).order_by('-hit_count')[:20]

# Pages missing SEO metadata
from django.db.models import Q
all_paths = ['/services/', '/about/', '/contact/']  # Your site paths
covered = SEOMetadata.objects.filter(is_active=True).values_list('path', flat=True)
missing = [p for p in all_paths if p not in covered]
```

## Testing

Location: `tests/test_seo.py`

```bash
python -m pytest tests/test_seo.py -v
```
