# T-059: SEO & Content Marketing

## AI Coding Brief
**Role**: Full Stack Developer
**Objective**: Implement blog system and SEO optimization
**Related Story**: S-018
**Epoch**: 5
**Estimate**: 4 hours

### Constraints
**Allowed File Paths**: apps/content/, templates/blog/
**Forbidden Paths**: None

### Deliverables
- [ ] Blog models
- [ ] Blog views and templates
- [ ] SEO meta tags
- [ ] Schema.org markup
- [ ] Sitemap generation
- [ ] Social sharing

### Implementation Details

#### Models
```python
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify

User = get_user_model()


class BlogCategory(models.Model):
    """Blog post categories."""

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    # SEO
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)

    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='children'
    )

    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = 'Blog Categories'
        ordering = ['order', 'name']


class BlogPost(models.Model):
    """Blog articles."""

    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('review', 'En revisión'),
        ('published', 'Publicado'),
        ('archived', 'Archivado'),
    ]

    # Content
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    excerpt = models.TextField(blank=True)
    content = models.TextField()
    content_html = models.TextField(blank=True)  # Rendered HTML

    # Media
    featured_image = models.ImageField(upload_to='blog/', null=True, blank=True)
    featured_image_alt = models.CharField(max_length=200, blank=True)

    # Categorization
    category = models.ForeignKey(
        BlogCategory, on_delete=models.SET_NULL,
        null=True, related_name='posts'
    )
    tags = models.JSONField(default=list)
    species = models.JSONField(default=list)  # ['dog', 'cat', ...]

    # Author
    author = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, related_name='blog_posts'
    )
    author_bio = models.TextField(blank=True)  # Override for display

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # SEO
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    canonical_url = models.URLField(blank=True)
    no_index = models.BooleanField(default=False)

    # Social
    og_title = models.CharField(max_length=100, blank=True)
    og_description = models.CharField(max_length=200, blank=True)
    og_image = models.ImageField(upload_to='blog/og/', null=True, blank=True)
    twitter_title = models.CharField(max_length=100, blank=True)
    twitter_description = models.CharField(max_length=200, blank=True)

    # Reading
    reading_time_minutes = models.IntegerField(default=5)
    word_count = models.IntegerField(default=0)

    # Analytics
    view_count = models.IntegerField(default=0)
    share_count = models.IntegerField(default=0)

    # Scheduling
    published_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Translations
    translations = models.JSONField(default=dict)
    # {'en': {'title': '...', 'content': '...', 'meta_description': '...'}}

    class Meta:
        ordering = ['-published_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        # Calculate word count and reading time
        words = len(self.content.split())
        self.word_count = words
        self.reading_time_minutes = max(1, words // 200)

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return f'/blog/{self.slug}/'


class SEOMetadata(models.Model):
    """SEO metadata for any page."""

    # Generic relation
    content_type = models.ForeignKey(
        'contenttypes.ContentType', on_delete=models.CASCADE
    )
    object_id = models.PositiveIntegerField()

    # Meta tags
    meta_title = models.CharField(max_length=70)
    meta_description = models.CharField(max_length=160)
    meta_keywords = models.CharField(max_length=255, blank=True)

    # Open Graph
    og_title = models.CharField(max_length=100, blank=True)
    og_description = models.CharField(max_length=200, blank=True)
    og_image = models.ImageField(upload_to='seo/', null=True, blank=True)
    og_type = models.CharField(max_length=50, default='website')

    # Twitter
    twitter_card = models.CharField(max_length=20, default='summary_large_image')
    twitter_title = models.CharField(max_length=100, blank=True)
    twitter_description = models.CharField(max_length=200, blank=True)

    # Schema.org
    schema_type = models.CharField(max_length=50, blank=True)
    schema_data = models.JSONField(default=dict, blank=True)

    # Canonical
    canonical_url = models.URLField(blank=True)

    # Robots
    no_index = models.BooleanField(default=False)
    no_follow = models.BooleanField(default=False)

    class Meta:
        unique_together = ['content_type', 'object_id']
```

#### Blog Views
```python
class BlogListView(ListView):
    """Blog listing page."""

    model = BlogPost
    template_name = 'blog/list.html'
    context_object_name = 'posts'
    paginate_by = 12

    def get_queryset(self):
        queryset = BlogPost.objects.filter(
            status='published',
            published_at__lte=timezone.now()
        ).select_related('category', 'author')

        # Category filter
        category = self.kwargs.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)

        # Tag filter
        tag = self.request.GET.get('tag')
        if tag:
            queryset = queryset.filter(tags__contains=[tag])

        # Species filter
        species = self.request.GET.get('species')
        if species:
            queryset = queryset.filter(species__contains=[species])

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = BlogCategory.objects.filter(is_active=True)
        context['popular_posts'] = BlogPost.objects.filter(
            status='published'
        ).order_by('-view_count')[:5]
        return context


class BlogDetailView(DetailView):
    """Blog post detail."""

    model = BlogPost
    template_name = 'blog/detail.html'
    context_object_name = 'post'

    def get_queryset(self):
        return BlogPost.objects.filter(
            status='published',
            published_at__lte=timezone.now()
        )

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Increment view count
        BlogPost.objects.filter(pk=obj.pk).update(
            view_count=F('view_count') + 1
        )
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object

        # Related posts
        context['related_posts'] = BlogPost.objects.filter(
            status='published',
            category=post.category
        ).exclude(pk=post.pk)[:3]

        # Schema.org
        context['schema_data'] = self._generate_schema()

        return context

    def _generate_schema(self):
        post = self.object
        return {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": post.title,
            "description": post.meta_description or post.excerpt,
            "image": post.featured_image.url if post.featured_image else None,
            "author": {
                "@type": "Person",
                "name": post.author.get_full_name() if post.author else "Dr. Pablo"
            },
            "publisher": {
                "@type": "Organization",
                "name": "Pet-Friendly Veterinaria",
                "logo": {
                    "@type": "ImageObject",
                    "url": "https://petfriendlyvet.com/logo.png"
                }
            },
            "datePublished": post.published_at.isoformat() if post.published_at else None,
            "dateModified": post.updated_at.isoformat(),
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": post.get_absolute_url()
            }
        }
```

#### Sitemap
```python
from django.contrib.sitemaps import Sitemap


class BlogSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return BlogPost.objects.filter(
            status='published',
            no_index=False
        )

    def lastmod(self, obj):
        return obj.updated_at


class StaticSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.8

    def items(self):
        return ['home', 'about', 'services', 'contact', 'store']

    def location(self, item):
        return reverse(item)


class ServiceSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.6

    def items(self):
        from apps.appointments.models import ServiceType
        return ServiceType.objects.filter(is_active=True)


class ProductSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.5

    def items(self):
        from apps.store.models import Product
        return Product.objects.filter(is_active=True, is_published=True)
```

### Test Cases
- [ ] Blog list displays posts
- [ ] Category filtering works
- [ ] Post detail displays
- [ ] View count increments
- [ ] Schema.org generates correctly
- [ ] Sitemap generates
- [ ] SEO meta tags render

### Definition of Done
- [ ] Blog system complete
- [ ] SEO optimized
- [ ] Sitemap working
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-002: Base Templates
