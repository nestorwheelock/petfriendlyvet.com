# Knowledge Base Module

The `apps.knowledge` module provides a structured knowledge base for AI context injection, FAQs, and content management with version history.

## Table of Contents

- [Overview](#overview)
- [Models](#models)
  - [KnowledgeCategory](#knowledgecategory)
  - [KnowledgeArticle](#knowledgearticle)
  - [FAQ](#faq)
  - [ArticleVersion](#articleversion)
- [Workflows](#workflows)
- [Integration Points](#integration-points)
- [Query Examples](#query-examples)
- [Testing](#testing)

## Overview

The knowledge module provides:

- **Category Organization** - Hierarchical categories for content
- **Knowledge Articles** - Full bilingual articles with AI context
- **FAQs** - Frequently asked questions with view tracking
- **Version History** - Track article changes over time

## Models

Location: `apps/knowledge/models.py`

### KnowledgeCategory

Hierarchical categories for organizing knowledge content.

```python
class KnowledgeCategory(models.Model):
    name = models.CharField(max_length=100)
    name_es = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', null=True, on_delete=models.CASCADE, related_name='children')
    icon = models.CharField(max_length=50, blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `name_es`, `name_en` | CharField | Bilingual category names |
| `parent` | ForeignKey | Hierarchical parent category |
| `icon` | CharField | Icon identifier for UI |
| `order` | Integer | Display order |

### KnowledgeArticle

Full knowledge base articles with AI context injection support.

```python
class KnowledgeArticle(models.Model):
    category = models.ForeignKey(KnowledgeCategory, on_delete=models.CASCADE, related_name='articles')

    # Titles
    title = models.CharField(max_length=255)
    title_es = models.CharField(max_length=255)
    title_en = models.CharField(max_length=255)

    # Content
    content = models.TextField()
    content_es = models.TextField()
    content_en = models.TextField()

    # AI-specific fields
    ai_context = models.TextField(blank=True)  # Condensed for AI injection
    keywords = models.JSONField(default=list)

    # Metadata
    slug = models.SlugField(unique=True)
    is_published = models.BooleanField(default=False)
    priority = models.IntegerField(default=0)  # Higher = more important
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `ai_context` | TextField | Condensed version for AI injection |
| `keywords` | JSONField | List of keywords for matching |
| `priority` | Integer | Higher values prioritized for AI |
| `is_published` | Boolean | Publication status |

### FAQ

Frequently asked questions with view tracking.

```python
class FAQ(models.Model):
    category = models.ForeignKey(KnowledgeCategory, on_delete=models.CASCADE, related_name='faqs')

    # Question
    question = models.CharField(max_length=500)
    question_es = models.CharField(max_length=500)
    question_en = models.CharField(max_length=500)

    # Answer
    answer = models.TextField()
    answer_es = models.TextField()
    answer_en = models.TextField()

    # Metadata
    order = models.IntegerField(default=0)
    view_count = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `view_count` | Integer | Popularity tracking |
| `is_featured` | Boolean | Highlighted FAQs |
| `order` | Integer | Display order within category |

### ArticleVersion

Version history for tracking article changes.

```python
class ArticleVersion(models.Model):
    article = models.ForeignKey(KnowledgeArticle, on_delete=models.CASCADE, related_name='versions')
    version_number = models.IntegerField()
    content_es = models.TextField()
    content_en = models.TextField()
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    change_summary = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ['article', 'version_number']
```

## Workflows

### Creating an Article

```python
from apps.knowledge.models import KnowledgeCategory, KnowledgeArticle

# Get or create category
category = KnowledgeCategory.objects.get(slug='pet-care')

# Create article (auto-creates version 1)
article = KnowledgeArticle.objects.create(
    category=category,
    title='Vaccine Schedule',
    title_es='Calendario de Vacunas',
    title_en='Vaccine Schedule',
    content_es='Las vacunas son esenciales para la salud...',
    content_en='Vaccines are essential for health...',
    ai_context='Core vaccines: rabies, distemper, parvovirus. Schedule varies by age.',
    keywords=['vaccines', 'puppies', 'kittens', 'rabies'],
    is_published=True,
    priority=10,
    created_by=staff_user,
)
```

### Updating Article with Version

```python
from apps.knowledge.models import ArticleVersion

# Get latest version number
latest_version = article.versions.first().version_number if article.versions.exists() else 0

# Create new version
ArticleVersion.objects.create(
    article=article,
    version_number=latest_version + 1,
    content_es=article.content_es,
    content_en=article.content_en,
    changed_by=editor_user,
    change_summary='Updated vaccine schedule for 2025',
)

# Update article content
article.content_es = 'Contenido actualizado...'
article.content_en = 'Updated content...'
article.save()
```

### Incrementing FAQ View Count

```python
from apps.knowledge.models import FAQ

faq = FAQ.objects.get(pk=faq_id)
faq.increment_view_count()
```

## Integration Points

### With AI Assistant

```python
from apps.knowledge.models import KnowledgeArticle

def get_ai_context(keywords, language='es'):
    """Get relevant articles for AI context injection."""
    articles = KnowledgeArticle.objects.filter(
        is_published=True,
        keywords__contains=keywords
    ).order_by('-priority')[:5]

    context_parts = []
    for article in articles:
        if article.ai_context:
            context_parts.append(article.ai_context)
        else:
            context_parts.append(article.get_content(language)[:500])

    return '\n\n'.join(context_parts)
```

### With Homepage

```python
# Featured FAQs for homepage
from apps.knowledge.models import FAQ

featured_faqs = FAQ.objects.filter(
    is_active=True,
    is_featured=True
).order_by('order')[:5]
```

## Query Examples

```python
from apps.knowledge.models import KnowledgeCategory, KnowledgeArticle, FAQ
from django.db.models import Count

# Active root categories
root_categories = KnowledgeCategory.objects.filter(
    parent__isnull=True,
    is_active=True
).prefetch_related('children')

# High-priority articles for AI
ai_articles = KnowledgeArticle.objects.filter(
    is_published=True,
    priority__gte=5
).order_by('-priority')

# Popular FAQs
popular = FAQ.objects.filter(is_active=True).order_by('-view_count')[:10]

# Articles by category with count
by_category = KnowledgeCategory.objects.annotate(
    article_count=Count('articles')
).filter(article_count__gt=0)

# Article version history
versions = ArticleVersion.objects.filter(article=article).order_by('-version_number')

# Search articles by keyword
keyword_matches = KnowledgeArticle.objects.filter(
    keywords__contains=['vaccines'],
    is_published=True
)
```

## Testing

Location: `tests/test_knowledge.py`

```bash
python -m pytest tests/test_knowledge.py -v
```
