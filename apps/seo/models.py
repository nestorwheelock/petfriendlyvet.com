"""SEO and content marketing models."""
from django.conf import settings
from django.db import models
from django.utils.text import slugify

from apps.core.storage import blog_image_path, og_image_path, landing_image_path


class BlogCategory(models.Model):
    """Blog post categories."""

    name = models.CharField(max_length=100)
    name_es = models.CharField(max_length=100, blank=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children'
    )

    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)

    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Blog Categories'
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class BlogPost(models.Model):
    """Blog post for content marketing."""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('scheduled', 'Scheduled'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    title = models.CharField(max_length=200)
    title_es = models.CharField(max_length=200, blank=True)
    slug = models.SlugField(unique=True, max_length=200)

    excerpt = models.TextField(blank=True, help_text="Short summary for listings")
    excerpt_es = models.TextField(blank=True)

    content = models.TextField()
    content_es = models.TextField(blank=True)

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='blog_posts'
    )
    category = models.ForeignKey(
        BlogCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posts'
    )
    tags = models.JSONField(default=list, blank=True)

    featured_image = models.ImageField(upload_to=blog_image_path, blank=True, null=True)
    featured_image_alt = models.CharField(max_length=200, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False)

    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=200, blank=True)

    og_title = models.CharField(max_length=100, blank=True, help_text="Open Graph title")
    og_description = models.CharField(max_length=200, blank=True)
    og_image = models.ImageField(upload_to=og_image_path, blank=True, null=True)

    canonical_url = models.URLField(blank=True)
    schema_markup = models.JSONField(default=dict, blank=True)

    view_count = models.IntegerField(default=0)
    reading_time_minutes = models.IntegerField(default=5)

    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        word_count = len(self.content.split())
        self.reading_time_minutes = max(1, word_count // 200)
        super().save(*args, **kwargs)


class LandingPage(models.Model):
    """Marketing landing pages."""

    PAGE_TYPES = [
        ('service', 'Service Page'),
        ('location', 'Location Page'),
        ('campaign', 'Campaign Page'),
        ('seasonal', 'Seasonal Page'),
    ]

    title = models.CharField(max_length=200)
    title_es = models.CharField(max_length=200, blank=True)
    slug = models.SlugField(unique=True)
    page_type = models.CharField(max_length=20, choices=PAGE_TYPES)

    headline = models.CharField(max_length=100)
    headline_es = models.CharField(max_length=100, blank=True)

    subheadline = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    content_es = models.TextField(blank=True)

    hero_image = models.ImageField(upload_to=landing_image_path, blank=True, null=True)
    cta_text = models.CharField(max_length=50, default='Get Started')
    cta_url = models.CharField(max_length=200, blank=True)

    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)

    schema_markup = models.JSONField(default=dict, blank=True)

    is_active = models.BooleanField(default=True)
    is_indexed = models.BooleanField(default=True)

    view_count = models.IntegerField(default=0)
    conversion_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class SEOMetadata(models.Model):
    """SEO metadata for any page."""

    path = models.CharField(max_length=200, unique=True, help_text="URL path like /services/")

    title = models.CharField(max_length=70)
    title_es = models.CharField(max_length=70, blank=True)

    description = models.CharField(max_length=160)
    description_es = models.CharField(max_length=160, blank=True)

    keywords = models.CharField(max_length=200, blank=True)
    canonical_url = models.URLField(blank=True)

    og_title = models.CharField(max_length=100, blank=True)
    og_description = models.CharField(max_length=200, blank=True)
    og_image = models.URLField(blank=True)

    twitter_card = models.CharField(max_length=20, default='summary_large_image')
    twitter_title = models.CharField(max_length=100, blank=True)
    twitter_description = models.CharField(max_length=200, blank=True)

    schema_markup = models.JSONField(default=dict, blank=True)
    robots = models.CharField(max_length=50, default='index, follow')

    priority = models.DecimalField(max_digits=2, decimal_places=1, default=0.5)
    changefreq = models.CharField(max_length=20, default='weekly')

    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'SEO Metadata'
        verbose_name_plural = 'SEO Metadata'

    def __str__(self):
        return f"{self.path}: {self.title}"


class ContentCalendarItem(models.Model):
    """Content calendar for planning."""

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

    title = models.CharField(max_length=200)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='idea')

    description = models.TextField(blank=True)
    target_keywords = models.JSONField(default=list, blank=True)
    target_audience = models.CharField(max_length=200, blank=True)

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_content'
    )

    planned_date = models.DateField(null=True, blank=True)
    published_date = models.DateField(null=True, blank=True)

    blog_post = models.ForeignKey(
        BlogPost,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    landing_page = models.ForeignKey(
        LandingPage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['planned_date', '-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_content_type_display()})"


class Redirect(models.Model):
    """URL redirects for SEO."""

    REDIRECT_TYPES = [
        (301, 'Permanent (301)'),
        (302, 'Temporary (302)'),
    ]

    old_path = models.CharField(max_length=500, unique=True)
    new_path = models.CharField(max_length=500)
    redirect_type = models.IntegerField(choices=REDIRECT_TYPES, default=301)

    is_active = models.BooleanField(default=True)
    hit_count = models.IntegerField(default=0)
    last_hit = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['old_path']

    def __str__(self):
        return f"{self.old_path} -> {self.new_path}"
