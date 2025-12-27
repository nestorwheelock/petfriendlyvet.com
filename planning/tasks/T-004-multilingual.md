# T-004: Multilingual System

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md and [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement AI-powered multilingual system with 5 core languages
**Related Story**: S-001
**Estimate**: 4 hours

### Constraints
**Allowed File Paths**: apps/multilingual/, templates/, static/
**Forbidden Paths**: apps/store/, apps/pharmacy/

### Deliverables
- [ ] Language model with core 5 languages
- [ ] TranslatableContent model for static content
- [ ] Language switcher component
- [ ] URL prefix routing (/es/, /en/, etc.)
- [ ] Browser language detection
- [ ] User language preference persistence
- [ ] AI translation service for on-demand languages

### Core Languages
1. Spanish (es) - Default
2. English (en)
3. German (de)
4. French (fr)
5. Italian (it)

### Implementation Details

#### Models
```python
class Language(models.Model):
    code = models.CharField(max_length=5, unique=True)
    name = models.CharField(max_length=50)
    native_name = models.CharField(max_length=50)
    is_core = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    flag_emoji = models.CharField(max_length=10)

class TranslatedContent(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    field_name = models.CharField(max_length=100)
    translation = models.TextField()
    is_ai_generated = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### Language Detection Priority
1. URL prefix (/en/services)
2. User preference (if logged in)
3. Session language
4. Cookie language
5. Browser Accept-Language header
6. Default (Spanish)

#### AI Translation Service
```python
async def translate_content(text: str, target_lang: str) -> str:
    """Translate content using AI when not in core languages."""
    # Check cache first
    # Call OpenRouter for translation
    # Cache result
    # Return translated text
```

### Test Cases
- [ ] Language switcher changes URL and content
- [ ] User preference saved and restored
- [ ] Browser detection works for first-time visitors
- [ ] Core language content loads instantly
- [ ] AI translation called for non-core languages
- [ ] Translation cache prevents duplicate API calls
- [ ] RTL languages handled if requested
- [ ] Mixed content (some translated, some default) handled

### Definition of Done
- [ ] All 5 core languages configured
- [ ] Language switcher working on all pages
- [ ] User preferences persisted
- [ ] AI translation working for edge cases
- [ ] Tests written and passing (>95% coverage)
- [ ] Documentation updated

### Dependencies
- T-001: Django Project Setup
- T-002: Base Templates

### Environment Variables
```
DEFAULT_LANGUAGE=es
SUPPORTED_LANGUAGES=es,en,de,fr,it
OPENROUTER_API_KEY=  # For AI translation
```
