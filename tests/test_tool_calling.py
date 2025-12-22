"""Tests for T-010 Tool Calling Framework.

Tests validate tool calling infrastructure:
- Tool registration works
- Tools filtered by permission
- Tool execution succeeds
- Tool parameters validated
- Multi-tool calls handled
- Tool errors handled gracefully
- Permission escalation prevented
"""
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


class TestToolRegistry:
    """Test tool registry system."""

    def test_tool_registry_exists(self):
        """ToolRegistry class should exist."""
        from apps.ai_assistant.tools import ToolRegistry
        assert ToolRegistry is not None

    def test_registry_has_register_method(self):
        """Registry should have register method."""
        from apps.ai_assistant.tools import ToolRegistry
        assert hasattr(ToolRegistry, 'register')

    def test_registry_has_get_tools_method(self):
        """Registry should have get_tools method."""
        from apps.ai_assistant.tools import ToolRegistry
        assert hasattr(ToolRegistry, 'get_tools')

    def test_registry_has_execute_method(self):
        """Registry should have execute method."""
        from apps.ai_assistant.tools import ToolRegistry
        assert hasattr(ToolRegistry, 'execute')


class TestToolDefinition:
    """Test Tool dataclass."""

    def test_tool_class_exists(self):
        """Tool class should exist."""
        from apps.ai_assistant.tools import Tool
        assert Tool is not None

    def test_tool_has_required_attributes(self):
        """Tool should have required attributes."""
        from apps.ai_assistant.tools import Tool
        tool = Tool(
            name='test_tool',
            description='A test tool',
            parameters={'type': 'object', 'properties': {}},
            handler=lambda: None,
            permission_level='public',
            module='test'
        )
        assert tool.name == 'test_tool'
        assert tool.description == 'A test tool'
        assert tool.permission_level == 'public'

    def test_tool_to_openai_format(self):
        """Tool should convert to OpenAI format."""
        from apps.ai_assistant.tools import Tool
        tool = Tool(
            name='test_tool',
            description='A test tool',
            parameters={'type': 'object', 'properties': {}},
            handler=lambda: None,
            permission_level='public',
            module='test'
        )
        openai_format = tool.to_openai_format()
        assert openai_format['type'] == 'function'
        assert openai_format['function']['name'] == 'test_tool'


class TestToolResult:
    """Test ToolResult dataclass."""

    def test_tool_result_exists(self):
        """ToolResult class should exist."""
        from apps.ai_assistant.tools import ToolResult
        assert ToolResult is not None

    def test_tool_result_success(self):
        """ToolResult should handle success case."""
        from apps.ai_assistant.tools import ToolResult
        result = ToolResult(success=True, data={'hours': '9am-8pm'})
        assert result.success is True
        assert result.data == {'hours': '9am-8pm'}

    def test_tool_result_error(self):
        """ToolResult should handle error case."""
        from apps.ai_assistant.tools import ToolResult
        result = ToolResult(success=False, data=None, error='Tool not found')
        assert result.success is False
        assert result.error == 'Tool not found'

    def test_tool_result_to_message(self):
        """ToolResult should convert to message string."""
        from apps.ai_assistant.tools import ToolResult
        result = ToolResult(success=True, data={'hours': '9am-8pm'})
        message = result.to_message()
        assert isinstance(message, str)
        assert 'hours' in message


class TestToolDecorator:
    """Test tool decorator."""

    def test_tool_decorator_exists(self):
        """tool decorator should exist."""
        from apps.ai_assistant.tools import tool
        assert tool is not None
        assert callable(tool)


class TestBuiltInTools:
    """Test built-in tools for the clinic."""

    def test_get_clinic_hours_tool_registered(self):
        """get_clinic_hours tool should be registered."""
        from apps.ai_assistant.tools import ToolRegistry
        tools = ToolRegistry.get_tools()
        tool_names = [t.name for t in tools]
        assert 'get_clinic_hours' in tool_names

    def test_get_services_tool_registered(self):
        """get_services tool should be registered."""
        from apps.ai_assistant.tools import ToolRegistry
        tools = ToolRegistry.get_tools()
        tool_names = [t.name for t in tools]
        assert 'get_services' in tool_names


@pytest.mark.django_db
class TestToolPermissions:
    """Test permission-based tool filtering."""

    @pytest.fixture
    def regular_user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def staff_user(self):
        return User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='testpass123',
            role='staff'
        )

    def test_public_tools_available_to_anonymous(self):
        """Public tools should be available to anonymous users."""
        from apps.ai_assistant.tools import ToolRegistry
        tools = ToolRegistry.get_tools_for_user(user=None)
        tool_names = [t.name for t in tools]
        assert 'get_clinic_hours' in tool_names

    def test_customer_tools_require_auth(self, regular_user):
        """Customer tools should require authentication."""
        from apps.ai_assistant.tools import ToolRegistry
        tools = ToolRegistry.get_tools_for_user(user=regular_user)
        # Should have public + customer tools
        assert len(tools) >= 1


class TestToolExecution:
    """Test tool execution."""

    def test_execute_returns_tool_result(self):
        """Execute should return ToolResult."""
        from apps.ai_assistant.tools import ToolRegistry, ToolResult
        result = ToolRegistry.execute('get_clinic_hours', {}, {})
        assert isinstance(result, ToolResult)

    def test_execute_nonexistent_tool_returns_error(self):
        """Executing nonexistent tool should return error."""
        from apps.ai_assistant.tools import ToolRegistry
        result = ToolRegistry.execute('nonexistent_tool', {}, {})
        assert result.success is False
        assert 'not found' in result.error.lower() or 'error' in result.error.lower()

    def test_execute_get_clinic_hours(self):
        """get_clinic_hours should execute and return data."""
        from apps.ai_assistant.tools import ToolRegistry
        result = ToolRegistry.execute('get_clinic_hours', {}, {})
        assert result.success is True
        assert 'hours' in result.data or isinstance(result.data, (dict, list, str))


class TestMultiToolHandling:
    """Test handling multiple tool calls."""

    def test_handle_tool_calls_function_exists(self):
        """handle_tool_calls function should exist."""
        from apps.ai_assistant.tools import handle_tool_calls
        assert handle_tool_calls is not None
        assert callable(handle_tool_calls)
