# T-014: Knowledge Base Models

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement knowledge base models for AI context
**Related Story**: S-011
**Estimate**: 3 hours

### Constraints
**Allowed File Paths**: apps/ai_assistant/, apps/knowledge/
**Forbidden Paths**: None

### Deliverables
- [ ] KnowledgeCategory model
- [ ] KnowledgeArticle model
- [ ] FAQ model
- [ ] Content versioning
- [ ] Search functionality
- [ ] Category hierarchy
- [ ] Bilingual content fields

### Implementation Details

#### Models
```python
class KnowledgeCategory(models.Model):
    """Category for organizing knowledge base content."""

    name = models.CharField(max_length=100)
    name_es = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    icon = models.CharField(max_length=50, blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Knowledge Categories"
        ordering = ['order', 'name']


class KnowledgeArticle(models.Model):
    """Knowledge base article for AI context."""

    category = models.ForeignKey(
        KnowledgeCategory,
        on_delete=models.CASCADE,
        related_name='articles'
    )

    # Titles
    title = models.CharField(max_length=255)
    title_es = models.CharField(max_length=255)
    title_en = models.CharField(max_length=255)

    # Content
    content = models.TextField()
    content_es = models.TextField()
    content_en = models.TextField()

    # AI-specific fields
    ai_context = models.TextField(
        blank=True,
        help_text="Condensed version for AI context injection"
    )
    keywords = models.JSONField(default=list)

    # Metadata
    slug = models.SlugField(unique=True)
    is_published = models.BooleanField(default=False)
    priority = models.IntegerField(default=0)  # Higher = more important

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )


class FAQ(models.Model):
    """Frequently asked questions."""

    category = models.ForeignKey(
        KnowledgeCategory,
        on_delete=models.CASCADE,
        related_name='faqs'
    )

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

    class Meta:
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
        ordering = ['order']


class ArticleVersion(models.Model):
    """Version history for articles."""

    article = models.ForeignKey(
        KnowledgeArticle,
        on_delete=models.CASCADE,
        related_name='versions'
    )
    version_number = models.IntegerField()
    content_es = models.TextField()
    content_en = models.TextField()
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    change_summary = models.CharField(max_length=255, blank=True)
```

#### Category Hierarchy
```
Pet Care
├── Dogs
│   ├── Nutrition
│   ├── Health
│   └── Training
├── Cats
│   ├── Nutrition
│   ├── Health
│   └── Behavior
├── Birds
└── Exotic Pets

Clinic Info
├── Services
├── Hours & Location
├── Staff
└── Policies

Emergency
├── First Aid
├── Poison Control
└── When to Come In
```

#### Search Functionality
```python
def search_knowledge_base(query: str, language: str = 'es') -> list:
    """Full-text search across knowledge base."""
    from django.contrib.postgres.search import SearchVector, SearchQuery

    vector = SearchVector(
        f'title_{language}',
        f'content_{language}',
        'keywords'
    )
    search_query = SearchQuery(query, config='spanish' if language == 'es' else 'english')

    return KnowledgeArticle.objects.annotate(
        search=vector
    ).filter(
        search=search_query,
        is_published=True
    ).order_by('-priority')
```

### Test Cases
- [ ] Categories nest correctly
- [ ] Articles save with versions
- [ ] Search finds relevant content
- [ ] Bilingual content works
- [ ] FAQs display correctly
- [ ] Version history tracks changes

### Definition of Done
- [ ] All models migrated
- [ ] Search functional
- [ ] Version history working
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-001: Django Project Setup
- T-004: Multilingual System
