# Multilingual Module

The `apps.multilingual` module provides AI-powered translation capabilities using a generic foreign key system to translate any model field.

## Table of Contents

- [Overview](#overview)
- [Models](#models)
  - [Language](#language)
  - [TranslatedContent](#translatedcontent)
- [Workflows](#workflows)
- [Integration Points](#integration-points)
- [Query Examples](#query-examples)
- [Testing](#testing)

## Overview

The multilingual module provides:

- **Language Configuration** - Core and extended language support
- **Generic Translations** - Translate any model field
- **AI-Generated Translations** - Track AI vs manual translations
- **Human Verification** - Staff verification workflow

## Models

Location: `apps/multilingual/models.py`

### Language

Language configuration for the system.

```python
class Language(models.Model):
    code = models.CharField(max_length=5, unique=True)  # ISO 639-1 (es, en, de)
    name = models.CharField(max_length=50)              # English name
    native_name = models.CharField(max_length=50)       # Native name (Español)
    is_core = models.BooleanField(default=False)        # Pre-translated content
    is_active = models.BooleanField(default=True)
    flag_emoji = models.CharField(max_length=10, blank=True)
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `code` | CharField | ISO 639-1 code (es, en, de) |
| `is_core` | Boolean | Core languages have pre-translated content |
| `flag_emoji` | CharField | Visual flag display |

### TranslatedContent

Stores translations using GenericForeignKey.

```python
class TranslatedContent(models.Model):
    # Generic relation to any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    field_name = models.CharField(max_length=100)
    translation = models.TextField()

    is_ai_generated = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['content_type', 'object_id', 'language', 'field_name']
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `content_object` | GenericFK | Any translatable model |
| `field_name` | CharField | Model field being translated |
| `is_ai_generated` | Boolean | AI vs manual translation |
| `verified_by` | ForeignKey | Human verification |

## Workflows

### Adding Translations

```python
from apps.multilingual.models import Language, TranslatedContent
from apps.services.models import Service
from django.contrib.contenttypes.models import ContentType

# Get service and language
service = Service.objects.get(name='Dental Cleaning')
german = Language.objects.get(code='de')

# Add German translation
TranslatedContent.objects.create(
    content_type=ContentType.objects.get_for_model(Service),
    object_id=service.pk,
    language=german,
    field_name='name',
    translation='Zahnreinigung',
    is_ai_generated=True,  # AI translated
)

TranslatedContent.objects.create(
    content_type=ContentType.objects.get_for_model(Service),
    object_id=service.pk,
    language=german,
    field_name='description',
    translation='Professionelle Zahnreinigung unter Narkose',
    is_ai_generated=True,
)
```

### Retrieving Translations

```python
from apps.multilingual.models import TranslatedContent
from django.contrib.contenttypes.models import ContentType

def get_translation(obj, field_name, language_code):
    """Get translation for a model field."""
    ct = ContentType.objects.get_for_model(obj)
    try:
        return TranslatedContent.objects.get(
            content_type=ct,
            object_id=obj.pk,
            field_name=field_name,
            language__code=language_code
        ).translation
    except TranslatedContent.DoesNotExist:
        return getattr(obj, field_name)  # Fallback to original
```

### Verifying AI Translations

```python
# Staff verifies AI translation
translation = TranslatedContent.objects.get(pk=translation_id)
translation.verified_by = staff_user
translation.save()
```

## Integration Points

### With Services Module

```python
from apps.services.models import Service
from apps.multilingual.models import TranslatedContent

# Get service with translation
service = Service.objects.get(pk=1)
name_de = get_translation(service, 'name', 'de')
```

### With Products (Store)

```python
from apps.store.models import Product

# Translate product catalog
for product in Product.objects.filter(is_active=True):
    translate_field(product, 'name', target_language='de')
    translate_field(product, 'description', target_language='de')
```

## Query Examples

```python
from apps.multilingual.models import Language, TranslatedContent
from django.db.models import Count

# Active languages
active = Language.objects.filter(is_active=True)

# Core languages (have pre-translated content)
core = Language.objects.filter(is_core=True)

# AI translations needing verification
unverified = TranslatedContent.objects.filter(
    is_ai_generated=True,
    verified_by__isnull=True
)

# Translations per language
by_language = TranslatedContent.objects.values(
    'language__code'
).annotate(count=Count('id')).order_by('-count')

# Get all translations for an object
from django.contrib.contenttypes.models import ContentType
ct = ContentType.objects.get_for_model(Service)
translations = TranslatedContent.objects.filter(
    content_type=ct,
    object_id=service.pk
).select_related('language')
```

## Testing

Location: `tests/test_multilingual.py`

```bash
python -m pytest tests/test_multilingual.py -v
```
