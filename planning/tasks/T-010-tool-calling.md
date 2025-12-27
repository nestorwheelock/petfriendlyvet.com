# T-010: Tool Calling Framework

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md and [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement tool calling infrastructure for AI assistant
**Related Story**: S-002
**Estimate**: 6 hours

### Constraints
**Allowed File Paths**: apps/ai_assistant/
**Forbidden Paths**: None

### Deliverables
- [ ] Tool registry system
- [ ] Permission-based tool access
- [ ] Tool execution handler
- [ ] Tool result formatting
- [ ] Multi-tool call handling
- [ ] Tool validation and error handling
- [ ] Logging and auditing

### Implementation Details

#### Tool Registry
```python
class ToolRegistry:
    """Central registry for all AI tools."""

    _tools: dict[str, Tool] = {}

    @classmethod
    def register(cls, tool: Tool):
        """Register a tool."""
        cls._tools[tool.name] = tool

    @classmethod
    def get_tools_for_user(cls, user) -> list[dict]:
        """Get tools available for user's permission level."""
        pass

    @classmethod
    def execute(cls, tool_name: str, params: dict, context: dict) -> ToolResult:
        """Execute a tool with given parameters."""
        pass
```

#### Tool Definition
```python
@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    handler: Callable
    permission_level: str  # public, customer, staff, admin
    module: str  # Which django app provides this tool

    def to_openai_format(self) -> dict:
        """Convert to OpenAI function calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }
```

#### Tool Result
```python
@dataclass
class ToolResult:
    success: bool
    data: Any
    error: str | None = None
    ui_component: str | None = None  # Optional HTMX component to render

    def to_message(self) -> str:
        """Format result for AI context."""
        if self.success:
            return json.dumps(self.data)
        return f"Error: {self.error}"
```

#### Tool Decorators
```python
@tool(
    name="get_clinic_hours",
    description="Get clinic operating hours",
    permission="public",
    module="pages"
)
def get_clinic_hours(day: str = None) -> dict:
    """Return clinic hours for a day or all days."""
    pass
```

#### Multi-Tool Handler
```python
async def handle_tool_calls(
    tool_calls: list[dict],
    context: dict
) -> list[dict]:
    """Execute multiple tool calls and return results."""
    results = []
    for call in tool_calls:
        result = await ToolRegistry.execute(
            call["function"]["name"],
            json.loads(call["function"]["arguments"]),
            context
        )
        results.append({
            "tool_call_id": call["id"],
            "role": "tool",
            "content": result.to_message()
        })
    return results
```

#### Permission Levels
| Level | Access |
|-------|--------|
| public | Basic info, services, hours |
| customer | Pet records, appointments, orders |
| staff | All customer + clinical tools |
| admin | Everything including system tools |

### Test Cases
- [ ] Tool registration works
- [ ] Tools filtered by permission
- [ ] Tool execution succeeds
- [ ] Tool parameters validated
- [ ] Multi-tool calls handled
- [ ] Tool errors handled gracefully
- [ ] Audit log created
- [ ] Permission escalation prevented

### Definition of Done
- [ ] Registry system working
- [ ] All Epoch 1 tools registered
- [ ] Permission filtering works
- [ ] Error handling robust
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-009: AI Service Layer
