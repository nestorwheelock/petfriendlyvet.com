# S-011: Knowledge Base Administration

**Story Type:** User Story
**Priority:** High
**Epoch:** 1 (Foundation)
**Status:** PENDING
**Module:** django-ai-assistant

## User Story

**As a** clinic owner
**I want to** manage the AI's knowledge base content
**So that** the AI provides accurate, personalized responses about my clinic

**As a** veterinarian
**I want to** add pet care advice and medical information
**So that** pet owners receive expert guidance from the AI

**As an** administrator
**I want to** control what the AI can and cannot say
**So that** responses align with clinic policies and legal requirements

## Acceptance Criteria

### Knowledge Base Content Management
- [ ] Create, edit, delete knowledge base entries
- [ ] Organize content by category (services, policies, pet care, FAQs)
- [ ] Support rich text formatting (markdown)
- [ ] Version history for all content changes
- [ ] Preview how AI will use the content
- [ ] Bulk import/export capabilities

### Content Categories
- [ ] Clinic Information (hours, location, contact, staff)
- [ ] Services (descriptions, pricing, duration)
- [ ] Policies (cancellation, payment, emergencies)
- [ ] Pet Care Advice (by species, condition, topic)
- [ ] FAQs (common questions and answers)
- [ ] Products (descriptions, usage, recommendations)
- [ ] Medical Conditions (symptoms, treatments, prevention)

### Multilingual Content
- [ ] Enter content in primary language (Spanish)
- [ ] AI auto-translates to other languages on save
- [ ] Review and edit translations
- [ ] Mark content as translation-reviewed
- [ ] Language-specific content overrides

### AI Behavior Configuration
- [ ] Set AI personality and tone
- [ ] Define response templates for common scenarios
- [ ] Configure escalation triggers (when to involve human)
- [ ] Set topic restrictions (what AI should not discuss)
- [ ] Define disclaimer text for medical advice
- [ ] Configure confidence thresholds

### Content Approval Workflow
- [ ] Draft → Review → Approved → Published
- [ ] Role-based editing permissions
- [ ] Require approval for sensitive content
- [ ] Scheduled publishing
- [ ] Expiration dates for time-sensitive content

### Analytics & Improvement
- [ ] Track which content is used most
- [ ] Identify questions AI couldn't answer
- [ ] Suggest content gaps
- [ ] User feedback on AI responses
- [ ] A/B testing for response variations

## Technical Requirements

### Models

```python
class KnowledgeCategory(models.Model):
    """Categories for organizing knowledge base content"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True
    )
    icon = models.CharField(max_length=50, blank=True)  # Icon class
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Knowledge Categories'


class KnowledgeEntry(models.Model):
    """Individual knowledge base entry"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('review', 'In Review'),
        ('approved', 'Approved'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    # Identity
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(KnowledgeCategory, on_delete=models.CASCADE)

    # Content (primary language - Spanish)
    content = models.TextField()  # Markdown supported
    summary = models.TextField(blank=True)  # Short version for quick answers
    keywords = models.JSONField(default=list)  # For matching queries

    # Translations (auto-generated, editable)
    translations = models.JSONField(default=dict)
    # {"en": {"title": "...", "content": "...", "reviewed": true}, ...}

    # Metadata
    content_type = models.CharField(max_length=50)
    # faq, service, policy, pet_care, medical, product, general

    # Targeting
    species = models.JSONField(default=list)  # ["dog", "cat", "all"]
    applies_to = models.JSONField(default=list)  # ["customers", "staff", "all"]

    # Status & Workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    published_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    # Authorship
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='created_entries'
    )
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_entries'
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    # Analytics
    usage_count = models.IntegerField(default=0)
    last_used_at = models.DateTimeField(null=True, blank=True)
    helpfulness_score = models.FloatField(default=0.0)  # From user feedback

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']


class KnowledgeVersion(models.Model):
    """Version history for knowledge entries"""
    entry = models.ForeignKey(KnowledgeEntry, on_delete=models.CASCADE)
    version_number = models.IntegerField()
    title = models.CharField(max_length=200)
    content = models.TextField()
    translations = models.JSONField(default=dict)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    change_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-version_number']
        unique_together = ['entry', 'version_number']


class AIConfiguration(models.Model):
    """AI behavior and personality settings"""
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=False)  # Only one active at a time

    # Personality
    personality_prompt = models.TextField()  # System prompt for AI
    tone = models.CharField(max_length=50)  # friendly, professional, casual
    language_style = models.JSONField(default=dict)
    # {"formality": "informal", "emoji_usage": "minimal", ...}

    # Behavior
    confidence_threshold = models.FloatField(default=0.7)
    # Below this, escalate to human
    max_response_length = models.IntegerField(default=500)
    include_disclaimers = models.BooleanField(default=True)
    medical_disclaimer = models.TextField(blank=True)

    # Restrictions
    restricted_topics = models.JSONField(default=list)
    # ["competitor recommendations", "specific drug dosages", ...]
    escalation_triggers = models.JSONField(default=list)
    # ["angry customer", "legal threat", "emergency", ...]

    # Templates
    greeting_templates = models.JSONField(default=list)
    fallback_responses = models.JSONField(default=list)
    handoff_message = models.TextField(blank=True)

    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class UnansweredQuery(models.Model):
    """Queries the AI couldn't answer - for content gap analysis"""
    query = models.TextField()
    language = models.CharField(max_length=10)
    session_id = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    # AI's attempt
    attempted_response = models.TextField(blank=True)
    confidence_score = models.FloatField()

    # Resolution
    is_resolved = models.BooleanField(default=False)
    resolution_entry = models.ForeignKey(
        KnowledgeEntry, on_delete=models.SET_NULL, null=True, blank=True
    )
    resolution_notes = models.TextField(blank=True)

    # Frequency
    occurrence_count = models.IntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-occurrence_count', '-created_at']


class ContentFeedback(models.Model):
    """User feedback on AI responses"""
    RATING_CHOICES = [
        ('helpful', 'Helpful'),
        ('not_helpful', 'Not Helpful'),
        ('incorrect', 'Incorrect'),
        ('incomplete', 'Incomplete'),
    ]

    knowledge_entry = models.ForeignKey(
        KnowledgeEntry, on_delete=models.CASCADE, null=True, blank=True
    )
    query = models.TextField()
    response = models.TextField()
    rating = models.CharField(max_length=20, choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    # Staff review
    reviewed = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_feedback'
    )
    action_taken = models.TextField(blank=True)
```

### AI Tools (Admin)

```python
KNOWLEDGE_ADMIN_TOOLS = [
    {
        "name": "search_knowledge_base",
        "description": "Search the knowledge base for content",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "category": {"type": "string"},
                "content_type": {"type": "string"},
                "status": {"type": "string"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "create_knowledge_entry",
        "description": "Create a new knowledge base entry",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "category": {"type": "string"},
                "content": {"type": "string"},
                "content_type": {"type": "string"},
                "keywords": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["title", "category", "content"]
        }
    },
    {
        "name": "update_knowledge_entry",
        "description": "Update an existing knowledge base entry",
        "parameters": {
            "type": "object",
            "properties": {
                "entry_id": {"type": "integer"},
                "title": {"type": "string"},
                "content": {"type": "string"},
                "status": {"type": "string"}
            },
            "required": ["entry_id"]
        }
    },
    {
        "name": "get_unanswered_queries",
        "description": "Get queries the AI couldn't answer",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 10},
                "min_occurrences": {"type": "integer", "default": 1}
            }
        }
    },
    {
        "name": "get_content_analytics",
        "description": "Get analytics on knowledge base usage",
        "parameters": {
            "type": "object",
            "properties": {
                "date_range": {"type": "string"},
                "category": {"type": "string"}
            }
        }
    },
    {
        "name": "preview_ai_response",
        "description": "Preview how AI would respond to a query",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "language": {"type": "string", "default": "es"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "translate_entry",
        "description": "Trigger translation of a knowledge entry",
        "parameters": {
            "type": "object",
            "properties": {
                "entry_id": {"type": "integer"},
                "target_languages": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["entry_id"]
        }
    }
]
```

## Example AI Conversations

### Adding Content (Admin)
```
Dr. Pablo: Add information about our new laser therapy service

AI: I'll help you create a knowledge base entry for laser therapy.

    Please provide the following information:

    1. Service Description:
       What is laser therapy and what conditions does it treat?

    2. Pricing:
       Cost per session or package pricing?

    3. Duration:
       How long is each session?

    4. Species:
       Available for dogs, cats, or both?

    5. Any contraindications or special notes?

Dr. Pablo: It's cold laser therapy for pain and inflammation.
           $500 per session, 15-20 minutes. Both dogs and cats.
           Not for pregnant animals or those with cancer.

AI: I've created the knowledge base entry:

    Title: Terapia Láser Fría
    Category: Services
    Status: Draft

    Preview:
    "La terapia láser fría es un tratamiento no invasivo
    para el dolor y la inflamación. Cada sesión dura
    15-20 minutos y cuesta $500 MXN. Disponible para
    perros y gatos. No recomendado para animales
    embarazadas o con cáncer."

    I've also auto-generated translations for:
    ✓ English ✓ German ✓ French ✓ Italian

    Would you like to:
    1. Edit the content
    2. Review translations
    3. Publish immediately
    4. Save as draft
```

### Content Gap Analysis
```
Dr. Pablo: What questions are customers asking that we can't answer?

AI: Here are the top unanswered queries from the last 30 days:

    | Query | Occurrences | Category Gap |
    |-------|-------------|--------------|
    | "Do you board pets overnight?" | 12 | Services |
    | "What vaccines does my puppy need?" | 8 | Pet Care |
    | "Do you accept pet insurance?" | 7 | Policies |
    | "How much is spaying a cat?" | 6 | Pricing |
    | "Can I bring my bird?" | 4 | Services |

    Recommendation:
    Creating entries for the top 3 would address 57%
    of unanswered queries.

    Would you like me to draft content for any of these?
```

### Configuring AI Behavior
```
Dr. Pablo: I don't want the AI to recommend specific dosages

AI: I'll add that to the AI restrictions. Currently the AI is
    configured to:

    Restricted Topics:
    ✓ Competitor recommendations
    ✓ Specific drug dosages (NEW)
    ✓ Definitive diagnoses
    ✓ Legal/liability advice

    When asked about dosages, the AI will respond:
    "For specific medication dosages, please consult directly
    with Dr. Pablo during your appointment. Dosing depends on
    your pet's weight, condition, and other medications."

    Is this the response you'd like, or would you prefer
    different wording?
```

## Admin Interface

### Knowledge Base Dashboard
- Content by category (tree view)
- Quick stats (total entries, published, drafts)
- Recent changes timeline
- Content gap alerts
- Translation status

### Entry Editor
- Rich markdown editor
- Side-by-side translation view
- Preview panel (how AI uses it)
- Version history
- Publishing controls

### Analytics View
- Most used content
- Helpfulness ratings
- Unanswered query trends
- Search query analysis
- Response time metrics

## Definition of Done

- [ ] Knowledge entry CRUD with categories
- [ ] Version history for all changes
- [ ] Auto-translation on save
- [ ] Translation review workflow
- [ ] AI configuration panel
- [ ] Unanswered query tracking
- [ ] Content feedback collection
- [ ] Usage analytics dashboard
- [ ] Bulk import/export (CSV, JSON)
- [ ] Preview AI responses
- [ ] Tests written and passing (>95% coverage)

## Dependencies

- S-001: Foundation (auth, multilingual)
- S-002: AI Chat Interface (integration)

## Notes

- Consider using vector embeddings for semantic search
- May want to integrate with external knowledge sources
- Content moderation for user-submitted questions
- Regular content review reminders

## Development Process

**Before implementing this story**, review and follow the **23-Step TDD Cycle** in:
- `CLAUDE.md` - Global development workflow
- `planning/TASK_BREAKDOWN.md` - Specific tasks for this story

Tests must be written before implementation. >95% coverage required.
