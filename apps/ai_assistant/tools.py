"""Tool calling framework for AI assistant."""
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """Result from executing a tool."""

    success: bool
    data: Any
    error: str | None = None
    ui_component: str | None = None

    def to_message(self) -> str:
        """Format result for AI context."""
        if self.success:
            return json.dumps(self.data)
        return f"Error: {self.error}"


@dataclass
class Tool:
    """Definition of an AI tool."""

    name: str
    description: str
    parameters: dict
    handler: Callable
    permission_level: str = 'public'  # public, customer, staff, admin
    module: str = 'core'

    def to_openai_format(self) -> dict:
        """Convert to OpenAI function calling format."""
        return {
            'type': 'function',
            'function': {
                'name': self.name,
                'description': self.description,
                'parameters': self.parameters
            }
        }


class ToolRegistry:
    """Central registry for all AI tools."""

    _tools: dict[str, Tool] = {}

    @classmethod
    def register(cls, tool: Tool) -> None:
        """Register a tool."""
        cls._tools[tool.name] = tool

    @classmethod
    def get_tools(cls) -> list[Tool]:
        """Get all registered tools."""
        return list(cls._tools.values())

    @classmethod
    def get_tools_for_user(cls, user=None) -> list[Tool]:
        """Get tools available for user's permission level.

        Args:
            user: Django user object or None for anonymous

        Returns:
            List of Tool objects the user can access
        """
        if user is None or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
            # Anonymous users get public tools only
            return [t for t in cls._tools.values() if t.permission_level == 'public']

        user_role = getattr(user, 'role', 'customer')

        # Define permission hierarchy
        role_levels = {
            'public': 0,
            'customer': 1,
            'staff': 2,
            'admin': 3,
        }

        user_level = role_levels.get(user_role, 1)

        # Return tools at or below user's permission level
        return [
            t for t in cls._tools.values()
            if role_levels.get(t.permission_level, 0) <= user_level
        ]

    @classmethod
    def execute(cls, tool_name: str, params: dict, context: dict) -> ToolResult:
        """Execute a tool with given parameters.

        Args:
            tool_name: Name of the tool to execute
            params: Parameters to pass to the tool
            context: Execution context (user, language, etc.)

        Returns:
            ToolResult with success/failure and data
        """
        tool = cls._tools.get(tool_name)

        if tool is None:
            return ToolResult(
                success=False,
                data=None,
                error=f"Tool '{tool_name}' not found"
            )

        try:
            result = tool.handler(**params)
            return ToolResult(success=True, data=result)
        except Exception as e:
            logger.exception("Tool execution error for '%s'", tool_name)
            return ToolResult(
                success=False,
                data=None,
                error="Tool execution failed. Please try again."
            )

    @classmethod
    def clear(cls) -> None:
        """Clear all registered tools (for testing)."""
        cls._tools.clear()


def tool(
    name: str,
    description: str,
    parameters: dict = None,
    permission: str = 'public',
    module: str = 'core'
):
    """Decorator to register a function as a tool.

    Args:
        name: Tool name for AI to call
        description: Description for AI context
        parameters: JSON Schema for parameters
        permission: Required permission level
        module: Django app providing this tool

    Usage:
        @tool(
            name='get_clinic_hours',
            description='Get clinic operating hours',
            permission='public'
        )
        def get_clinic_hours(day: str = None) -> dict:
            return {'hours': '9am-8pm'}
    """
    if parameters is None:
        parameters = {'type': 'object', 'properties': {}}

    def decorator(func: Callable) -> Callable:
        t = Tool(
            name=name,
            description=description,
            parameters=parameters,
            handler=func,
            permission_level=permission,
            module=module
        )
        ToolRegistry.register(t)
        return func

    return decorator


async def handle_tool_calls(
    tool_calls: list[dict],
    context: dict
) -> list[dict]:
    """Execute multiple tool calls and return results.

    Args:
        tool_calls: List of tool call dicts from AI
        context: Execution context

    Returns:
        List of result dicts for AI context
    """
    results = []
    for call in tool_calls:
        func_data = call.get('function', {})
        tool_name = func_data.get('name', '')
        arguments = func_data.get('arguments', '{}')

        try:
            params = json.loads(arguments)
        except json.JSONDecodeError:
            params = {}

        result = ToolRegistry.execute(tool_name, params, context)
        results.append({
            'tool_call_id': call.get('id', ''),
            'role': 'tool',
            'content': result.to_message()
        })

    return results


# =============================================================================
# Built-in Tools for Pet-Friendly Vet
# =============================================================================

@tool(
    name='get_clinic_hours',
    description='Get the clinic operating hours for a specific day or all days',
    parameters={
        'type': 'object',
        'properties': {
            'day': {
                'type': 'string',
                'description': 'Day of the week (monday, tuesday, etc.) or "all"',
                'enum': ['monday', 'tuesday', 'wednesday', 'thursday',
                         'friday', 'saturday', 'sunday', 'all']
            }
        },
        'required': []
    },
    permission='public',
    module='core'
)
def get_clinic_hours(day: str = 'all') -> dict:
    """Return clinic hours."""
    hours = {
        'monday': 'Closed',
        'tuesday': '9:00 AM - 8:00 PM',
        'wednesday': '9:00 AM - 8:00 PM',
        'thursday': '9:00 AM - 8:00 PM',
        'friday': '9:00 AM - 8:00 PM',
        'saturday': '9:00 AM - 8:00 PM',
        'sunday': '9:00 AM - 8:00 PM',
    }

    if day == 'all':
        return {'hours': hours}

    day_lower = day.lower()
    if day_lower in hours:
        return {'day': day, 'hours': hours[day_lower]}

    return {'error': f'Unknown day: {day}'}


@tool(
    name='get_services',
    description='Get list of clinic services by category',
    parameters={
        'type': 'object',
        'properties': {
            'category': {
                'type': 'string',
                'description': 'Service category',
                'enum': ['clinic', 'pharmacy', 'store', 'all']
            }
        },
        'required': []
    },
    permission='public',
    module='core'
)
def get_services(category: str = 'all') -> dict:
    """Return list of services."""
    services = {
        'clinic': [
            'General Consultation',
            'Vaccination',
            'Surgery',
            'Dental Care',
            'Laboratory',
            'Emergency Care',
        ],
        'pharmacy': [
            'Prescription Medications',
            'Flea & Tick Prevention',
            'Supplements',
            'Specialty Diets',
        ],
        'store': [
            'Pet Food',
            'Accessories',
            'Toys',
            'Grooming Supplies',
        ],
    }

    if category == 'all':
        return {'services': services}

    cat_lower = category.lower()
    if cat_lower in services:
        return {'category': category, 'services': services[cat_lower]}

    return {'error': f'Unknown category: {category}'}


@tool(
    name='get_contact_info',
    description='Get clinic contact information',
    parameters={'type': 'object', 'properties': {}},
    permission='public',
    module='core'
)
def get_contact_info() -> dict:
    """Return clinic contact info."""
    return {
        'name': 'Pet-Friendly Veterinary Clinic',
        'phone': '+52 998 316 2438',
        'whatsapp': 'https://wa.me/529983162438',
        'address': 'Puerto Morelos, Quintana Roo, Mexico',
        'email': 'contact@petfriendlyvet.com'
    }
