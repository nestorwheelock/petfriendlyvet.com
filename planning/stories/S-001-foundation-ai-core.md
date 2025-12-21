# S-001: Foundation + AI Core

**Story Type:** Epic
**Priority:** Critical
**Epoch:** 1
**Status:** PENDING

## Overview

Establish the foundational Django architecture with modular packages, authentication, bilingual support, and the core AI service layer that powers all conversational interactions.

## User Stories

### As a visitor
- **I want to** access the website in Spanish or English
- **So that** I can understand all content in my preferred language

### As a pet owner
- **I want to** sign in with my Google account or email/phone
- **So that** I can access personalized features without remembering another password

### As Dr. Pablo (admin)
- **I want to** manage content through a mobile-friendly admin interface
- **So that** I can update the website from my phone between appointments

## Acceptance Criteria

### Authentication
- [ ] Users can sign in with Google OAuth
- [ ] Users can sign in with email (magic link or password)
- [ ] Users can sign in with phone number (SMS verification)
- [ ] Session management works across devices
- [ ] Admin users have elevated permissions

### Bilingual System
- [ ] Language switcher visible on all pages (ES/EN toggle)
- [ ] URL structure supports language prefix (/es/, /en/)
- [ ] All static content available in both languages
- [ ] User language preference persisted
- [ ] Browser language detected for first-time visitors

### Django Architecture
- [ ] Project follows modular package structure
- [ ] Settings split (base, development, production)
- [ ] PostgreSQL database configured
- [ ] Static files and media handling configured
- [ ] Environment variables for secrets (.env)

### AI Service Layer
- [ ] OpenRouter integration configured
- [ ] Tool calling infrastructure in place
- [ ] Knowledge base models created
- [ ] Basic AI response generation working
- [ ] Error handling and fallbacks implemented

### Basic Pages
- [ ] Homepage with hero, services overview, location
- [ ] About page with Dr. Pablo bio
- [ ] Services page with offerings
- [ ] Contact page with map, hours, phone/WhatsApp
- [ ] All pages responsive (mobile-first)

## Technical Requirements

### Packages to Initialize

| Package | Purpose |
|---------|---------|
| django-bilingual | Language management, content translation |
| django-ai-assistant | AI service layer, tool calling |

### Models

```python
# django-bilingual
class Language(models.Model):
    code = models.CharField(max_length=5)  # 'es', 'en'
    name = models.CharField(max_length=50)
    is_default = models.BooleanField(default=False)

class TranslatableContent(models.Model):
    key = models.CharField(max_length=255, unique=True)
    content_es = models.TextField()
    content_en = models.TextField()

# django-ai-assistant
class KnowledgeBase(models.Model):
    topic = models.CharField(max_length=255)
    content_es = models.TextField()
    content_en = models.TextField()
    category = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

class Conversation(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    session_id = models.CharField(max_length=255)
    language = models.CharField(max_length=5, default='es')
    created_at = models.DateTimeField(auto_now_add=True)

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    role = models.CharField(max_length=20)  # 'user', 'assistant', 'system'
    content = models.TextField()
    tool_calls = models.JSONField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### AI Tools (Epoch 1)

```python
EPOCH_1_TOOLS = [
    {
        "name": "get_clinic_info",
        "description": "Get clinic information like hours, location, services, or about Dr. Pablo",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "enum": ["hours", "location", "services", "about", "contact", "emergency"]
                }
            },
            "required": ["topic"]
        }
    },
    {
        "name": "search_knowledge_base",
        "description": "Search the knowledge base for pet care information",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "category": {"type": "string", "enum": ["general", "dogs", "cats", "birds", "other"]}
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_service_details",
        "description": "Get detailed information about a specific veterinary service",
        "parameters": {
            "type": "object",
            "properties": {
                "service_name": {"type": "string"}
            },
            "required": ["service_name"]
        }
    }
]
```

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Authentication working (Google + email + phone)
- [ ] Bilingual content switching functional
- [ ] AI chat responding to basic queries
- [ ] Knowledge base seeded with initial content
- [ ] All pages responsive on mobile
- [ ] Tests written and passing (>95% coverage)
- [ ] Documentation updated

## Dependencies

- OpenRouter API key
- Google OAuth credentials
- Twilio credentials (for phone auth)
- PostgreSQL database

## Notes

- This epoch establishes the foundation for all future epochs
- AI chat is informational only in Epoch 1 (no transactions)
- Custom admin interface is mobile-first, not Django admin
