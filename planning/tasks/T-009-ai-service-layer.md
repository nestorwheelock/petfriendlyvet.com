# T-009: AI Service Layer (OpenRouter)

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement core AI service layer with OpenRouter integration
**Related Story**: S-002
**Estimate**: 6 hours

### Constraints
**Allowed File Paths**: apps/ai_assistant/, apps/core/
**Forbidden Paths**: None

### Deliverables
- [ ] OpenRouter API client
- [ ] Message formatting for Claude
- [ ] Streaming response support
- [ ] Error handling and retry logic
- [ ] Rate limiting
- [ ] Cost tracking
- [ ] Async/await patterns

### Implementation Details

#### OpenRouter Client
```python
class OpenRouterClient:
    """Client for OpenRouter API with Claude support."""

    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.model = settings.AI_MODEL  # anthropic/claude-3.5-sonnet
        self.base_url = "https://openrouter.ai/api/v1"

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] = None,
        stream: bool = False,
        max_tokens: int = 4096,
    ) -> dict | AsyncGenerator:
        """Send chat completion request."""
        pass

    async def chat_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
        tool_handlers: dict[str, Callable],
    ) -> str:
        """Handle full tool calling loop."""
        pass
```

#### AIService
```python
class AIService:
    """High-level AI service for the application."""

    def __init__(self, user=None, language='es'):
        self.client = OpenRouterClient()
        self.user = user
        self.language = language
        self.conversation = None

    async def get_response(
        self,
        user_message: str,
        context: dict = None,
    ) -> str:
        """Get AI response with full tool handling."""
        pass

    def build_system_prompt(self) -> str:
        """Build system prompt with context and language."""
        pass

    def get_available_tools(self) -> list[dict]:
        """Get tools available based on user permissions."""
        pass
```

#### Configuration
```python
# settings.py
OPENROUTER_API_KEY = env("OPENROUTER_API_KEY")
AI_MODEL = "anthropic/claude-3.5-sonnet"
AI_MAX_TOKENS = 4096
AI_TEMPERATURE = 0.7
AI_RATE_LIMIT_PER_USER = 50  # requests per hour
AI_COST_LIMIT_DAILY = 10.00  # USD
```

#### Error Handling
- Retry with exponential backoff (3 attempts)
- Fallback responses for common queries
- Graceful degradation when AI unavailable
- User-friendly error messages (bilingual)

#### Cost Tracking
```python
class AIUsage(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    session_id = models.CharField(max_length=255)
    input_tokens = models.IntegerField()
    output_tokens = models.IntegerField()
    cost_usd = models.DecimalField(max_digits=10, decimal_places=6)
    model = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
```

### Test Cases
- [ ] Successful chat completion
- [ ] Streaming response works
- [ ] Tool calls executed correctly
- [ ] Rate limiting enforced
- [ ] Retry logic on transient errors
- [ ] Cost tracking accurate
- [ ] User context included in prompts
- [ ] Language switching works
- [ ] Fallback responses work

### Acceptance Criteria

**AC-1: Basic Chat Works**
**Given** a valid OpenRouter API key is configured
**When** I send a message to the AI service
**Then** I receive a coherent response in the configured language

**AC-2: Streaming Responses**
**Given** streaming mode is enabled
**When** I send a message to the AI service
**Then** I receive tokens incrementally as they are generated

**AC-3: Rate Limiting**
**Given** I am a user subject to rate limits
**When** I exceed 50 requests per hour
**Then** I receive a rate limit error with retry-after time

**AC-4: Cost Tracking**
**Given** I send a message to the AI service
**When** the response is complete
**Then** the token count and cost are recorded in the database

**AC-5: Error Recovery**
**Given** the AI service experiences a transient error
**When** the first request fails
**Then** it retries with exponential backoff up to 3 times

### Definition of Done
- [ ] OpenRouter client working
- [ ] Streaming and non-streaming modes
- [ ] Tool calling framework ready
- [ ] Error handling robust
- [ ] Cost tracking in place
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-001: Django Project Setup

### Environment Variables
```
OPENROUTER_API_KEY=
AI_MODEL=anthropic/claude-3.5-sonnet
AI_MAX_TOKENS=4096
AI_RATE_LIMIT_PER_USER=50
AI_COST_LIMIT_DAILY=10.00
```
