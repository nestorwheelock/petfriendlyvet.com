# T-013: Chat History Persistence

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement conversation and message persistence
**Related Story**: S-002
**Estimate**: 3 hours

### Constraints
**Allowed File Paths**: apps/ai_assistant/
**Forbidden Paths**: None

### Deliverables
- [ ] Conversation model
- [ ] Message model
- [ ] Session-to-user linking
- [ ] Conversation continuation
- [ ] History retrieval API
- [ ] Archival and cleanup
- [ ] Export functionality

### Implementation Details

#### Models
```python
class Conversation(models.Model):
    """Chat conversation container."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    session_id = models.CharField(max_length=255, db_index=True)
    language = models.CharField(max_length=5, default='es')

    # Metadata
    title = models.CharField(max_length=255, blank=True)
    summary = models.TextField(blank=True)
    topic = models.CharField(max_length=100, blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    is_resolved = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']


class Message(models.Model):
    """Individual chat message."""

    ROLES = [
        ('system', 'System'),
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('tool', 'Tool Result'),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    role = models.CharField(max_length=20, choices=ROLES)
    content = models.TextField()

    # Tool calls
    tool_calls = models.JSONField(null=True, blank=True)
    tool_call_id = models.CharField(max_length=100, blank=True)

    # Metadata
    tokens_used = models.IntegerField(default=0)
    model = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
```

#### Session Linking
When anonymous user logs in, link their session conversations:
```python
def link_session_to_user(session_id: str, user: User):
    """Link anonymous conversations to logged-in user."""
    Conversation.objects.filter(
        session_id=session_id,
        user__isnull=True
    ).update(user=user)
```

#### Conversation Context
Build context from history for AI:
```python
def get_conversation_context(
    conversation: Conversation,
    max_messages: int = 20
) -> list[dict]:
    """Get message history for AI context."""
    messages = conversation.messages.all()[:max_messages]
    return [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]
```

#### Auto-Summarization
After N messages, generate summary:
```python
async def summarize_conversation(conversation: Conversation) -> str:
    """Generate AI summary of conversation."""
    # Called every 10 messages to prevent context overflow
    pass
```

#### Cleanup Jobs
```python
# Celery task
@shared_task
def cleanup_old_conversations():
    """Archive conversations older than 90 days."""
    threshold = timezone.now() - timedelta(days=90)
    Conversation.objects.filter(
        updated_at__lt=threshold
    ).update(is_active=False)
```

### API Endpoints
- `GET /api/conversations/` - List user's conversations
- `GET /api/conversations/{id}/` - Get conversation with messages
- `POST /api/conversations/{id}/continue/` - Continue conversation
- `DELETE /api/conversations/{id}/` - Archive conversation

### Test Cases
- [ ] Messages saved correctly
- [ ] Conversation context builds properly
- [ ] Session linking works
- [ ] History retrieval paginates
- [ ] Summarization triggers
- [ ] Cleanup job runs
- [ ] Export generates valid data

### Definition of Done
- [ ] Full persistence working
- [ ] Session linking functional
- [ ] Context building optimized
- [ ] Cleanup scheduled
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-009: AI Service Layer
