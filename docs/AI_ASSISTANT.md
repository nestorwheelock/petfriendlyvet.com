# AI Assistant Module

The `apps.ai_assistant` module provides AI-powered chat functionality with conversation management and usage tracking for cost monitoring.

## Table of Contents

- [Overview](#overview)
- [Models](#models)
  - [AIUsage](#aiusage)
  - [Conversation](#conversation)
  - [Message](#message)
- [Workflows](#workflows)
- [Integration Points](#integration-points)
- [Query Examples](#query-examples)
- [Testing](#testing)

## Overview

The AI assistant module provides:

- **Chat Conversations** - Multi-turn chat sessions
- **Message History** - Full conversation records
- **Usage Tracking** - Token counts and API costs
- **Tool Integration** - Tool calling support

## Models

Location: `apps/ai_assistant/models.py`

### AIUsage

Track AI API usage for cost monitoring.

```python
class AIUsage(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    session_id = models.CharField(max_length=255, db_index=True)
    input_tokens = models.IntegerField()
    output_tokens = models.IntegerField()
    cost_usd = models.DecimalField(max_digits=10, decimal_places=6)
    model = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `input_tokens` | Integer | Tokens in prompt |
| `output_tokens` | Integer | Tokens in response |
| `cost_usd` | Decimal | API cost in USD |
| `model` | CharField | Model used (gpt-4, claude-3, etc.) |

### Conversation

Chat conversation session.

```python
class Conversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    session_id = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=200, blank=True)
    language = models.CharField(max_length=5, default='es')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | CharField | Unique session identifier |
| `language` | CharField | Conversation language |
| `is_active` | Boolean | Active vs archived |

### Message

Individual message in a conversation.

```python
ROLE_CHOICES = [
    ('user', 'User'),
    ('assistant', 'Assistant'),
    ('system', 'System'),
    ('tool', 'Tool'),
]

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    tool_calls = models.JSONField(null=True, blank=True)
    tool_call_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `role` | CharField | user, assistant, system, tool |
| `tool_calls` | JSONField | Function calls made |
| `tool_call_id` | CharField | Response to specific tool call |

## Workflows

### Creating a Conversation

```python
from apps.ai_assistant.models import Conversation, Message
import uuid

# Create new conversation
conversation = Conversation.objects.create(
    user=user,
    session_id=str(uuid.uuid4()),
    language='es',
)

# Add system message
Message.objects.create(
    conversation=conversation,
    role='system',
    content='You are a helpful veterinary assistant.',
)

# Add user message
Message.objects.create(
    conversation=conversation,
    role='user',
    content='What vaccines does my puppy need?',
)

# Add assistant response
Message.objects.create(
    conversation=conversation,
    role='assistant',
    content='For puppies, the core vaccines include...',
)
```

### Tracking Usage

```python
from apps.ai_assistant.models import AIUsage
from decimal import Decimal

# After AI API call
AIUsage.objects.create(
    user=user,
    session_id=conversation.session_id,
    input_tokens=150,
    output_tokens=300,
    cost_usd=Decimal('0.001350'),  # ($0.003/1K input + $0.006/1K output)
    model='gpt-4-turbo',
)
```

### Tool Calling

```python
from apps.ai_assistant.models import Message

# Assistant makes tool call
Message.objects.create(
    conversation=conversation,
    role='assistant',
    content='',
    tool_calls=[{
        'id': 'call_abc123',
        'type': 'function',
        'function': {
            'name': 'get_pet_vaccinations',
            'arguments': '{"pet_id": 42}'
        }
    }],
)

# Tool response
Message.objects.create(
    conversation=conversation,
    role='tool',
    content='[{"vaccine": "Rabies", "due_date": "2025-02-01"}]',
    tool_call_id='call_abc123',
)
```

## Integration Points

### With Notifications

```python
# Notify user of AI response if they leave the page
from apps.notifications.services import NotificationService

def on_ai_response(conversation, message):
    if not is_user_online(conversation.user):
        NotificationService.create_notification(
            user=conversation.user,
            notification_type='general',
            title='New AI Response',
            message=message.content[:100] + '...',
        )
```

### With Pets Module

```python
# AI can query pet data
from apps.pets.models import Pet, Vaccination

def get_pet_vaccinations(pet_id, user):
    pet = Pet.objects.get(pk=pet_id, owner=user)
    return list(pet.vaccinations.values('vaccine_name', 'next_due_date'))
```

## Query Examples

```python
from apps.ai_assistant.models import AIUsage, Conversation, Message
from django.db.models import Sum, Avg
from datetime import timedelta
from django.utils import timezone

# Total API costs this month
monthly_cost = AIUsage.objects.filter(
    created_at__month=timezone.now().month
).aggregate(total=Sum('cost_usd'))

# Average tokens per conversation
avg_tokens = AIUsage.objects.filter(
    user=user
).aggregate(
    avg_input=Avg('input_tokens'),
    avg_output=Avg('output_tokens')
)

# User's conversations
conversations = Conversation.objects.filter(
    user=user,
    is_active=True
).prefetch_related('messages').order_by('-updated_at')

# Messages in conversation
messages = Message.objects.filter(
    conversation=conversation
).order_by('created_at')

# Recent active conversations
recent = Conversation.objects.filter(
    updated_at__gte=timezone.now() - timedelta(days=7)
).count()
```

## Testing

Location: `tests/test_ai_assistant.py`

```bash
python -m pytest tests/test_ai_assistant.py -v
```
