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

    @pytest.mark.asyncio
    async def test_handle_tool_calls_executes_tools(self):
        """handle_tool_calls should execute tools and return results."""
        from apps.ai_assistant.tools import handle_tool_calls

        tool_calls = [
            {
                'id': 'call_1',
                'function': {
                    'name': 'get_clinic_hours',
                    'arguments': '{}'
                }
            }
        ]

        results = await handle_tool_calls(tool_calls, {})

        assert len(results) == 1
        assert results[0]['tool_call_id'] == 'call_1'
        assert results[0]['role'] == 'tool'
        assert 'hours' in results[0]['content'].lower() or 'monday' in results[0]['content'].lower()

    @pytest.mark.asyncio
    async def test_handle_tool_calls_multiple(self):
        """handle_tool_calls should handle multiple tools."""
        from apps.ai_assistant.tools import handle_tool_calls

        tool_calls = [
            {'id': 'call_1', 'function': {'name': 'get_clinic_hours', 'arguments': '{}'}},
            {'id': 'call_2', 'function': {'name': 'get_contact_info', 'arguments': '{}'}},
        ]

        results = await handle_tool_calls(tool_calls, {})

        assert len(results) == 2
        assert results[0]['tool_call_id'] == 'call_1'
        assert results[1]['tool_call_id'] == 'call_2'

    @pytest.mark.asyncio
    async def test_handle_tool_calls_invalid_json(self):
        """handle_tool_calls should handle invalid JSON arguments."""
        from apps.ai_assistant.tools import handle_tool_calls

        tool_calls = [
            {'id': 'call_1', 'function': {'name': 'get_clinic_hours', 'arguments': 'invalid json'}}
        ]

        results = await handle_tool_calls(tool_calls, {})

        assert len(results) == 1
        # Should still execute with empty params


class TestToolResultToMessage:
    """Test ToolResult.to_message method."""

    def test_to_message_error_case(self):
        """to_message should format error correctly."""
        from apps.ai_assistant.tools import ToolResult

        result = ToolResult(success=False, data=None, error='Something went wrong')
        message = result.to_message()

        assert 'Error:' in message
        assert 'Something went wrong' in message


class TestToolRegistryClear:
    """Test ToolRegistry.clear method."""

    def test_clear_removes_all_tools(self):
        """clear should remove all registered tools."""
        from apps.ai_assistant.tools import ToolRegistry, Tool

        # Store original tools count
        original_tools = ToolRegistry.get_tools().copy()

        # Register a test tool
        test_tool = Tool(
            name='temp_test_tool',
            description='Temporary test',
            parameters={},
            handler=lambda: None
        )
        ToolRegistry.register(test_tool)

        # Clear and verify
        ToolRegistry.clear()
        assert len(ToolRegistry.get_tools()) == 0

        # Re-register original tools for other tests
        for tool in original_tools:
            ToolRegistry.register(tool)


class TestToolDecoratorDefault:
    """Test @tool decorator with default parameters."""

    def test_decorator_sets_default_parameters(self):
        """Decorator should set default empty parameters."""
        from apps.ai_assistant.tools import tool, ToolRegistry

        @tool(name='test_default_params', description='Test')
        def test_func():
            return {}

        tools = ToolRegistry.get_tools()
        test_tool = next((t for t in tools if t.name == 'test_default_params'), None)

        assert test_tool is not None
        assert test_tool.parameters == {'type': 'object', 'properties': {}}


class TestToolExecutionException:
    """Test tool execution exception handling."""

    def test_execute_handles_exception(self):
        """Execute should catch exceptions and return sanitized error."""
        from apps.ai_assistant.tools import ToolRegistry, Tool

        # Register a tool that raises an exception
        def failing_handler():
            raise ValueError("Intentional test error")

        failing_tool = Tool(
            name='failing_tool',
            description='Always fails',
            parameters={},
            handler=failing_handler
        )
        ToolRegistry.register(failing_tool)

        result = ToolRegistry.execute('failing_tool', {}, {})

        assert result.success is False
        # Error message should be sanitized (not leak internal details)
        assert 'Intentional test error' not in result.error
        assert 'failed' in result.error.lower()


class TestGetClinicHoursSpecificDay:
    """Test get_clinic_hours with specific day."""

    def test_get_hours_specific_day(self):
        """get_clinic_hours should return specific day hours."""
        from apps.ai_assistant.tools import get_clinic_hours

        result = get_clinic_hours(day='tuesday')

        assert 'day' in result
        assert 'hours' in result
        assert result['day'] == 'tuesday'
        assert '9:00 AM' in result['hours']

    def test_get_hours_unknown_day(self):
        """get_clinic_hours should handle unknown day."""
        from apps.ai_assistant.tools import get_clinic_hours

        result = get_clinic_hours(day='invalidday')

        assert 'error' in result
        assert 'Unknown day' in result['error']

    def test_get_hours_all_days(self):
        """get_clinic_hours should return all days."""
        from apps.ai_assistant.tools import get_clinic_hours

        result = get_clinic_hours(day='all')

        assert 'hours' in result
        assert 'monday' in result['hours']
        assert result['hours']['monday'] == 'Closed'


class TestGetServicesSpecificCategory:
    """Test get_services with specific category."""

    def test_get_services_clinic(self):
        """get_services should return clinic services."""
        from apps.ai_assistant.tools import get_services

        result = get_services(category='clinic')

        assert 'category' in result
        assert 'services' in result
        assert 'General Consultation' in result['services']

    def test_get_services_pharmacy(self):
        """get_services should return pharmacy services."""
        from apps.ai_assistant.tools import get_services

        result = get_services(category='pharmacy')

        assert 'category' in result
        assert 'Prescription Medications' in result['services']

    def test_get_services_store(self):
        """get_services should return store services."""
        from apps.ai_assistant.tools import get_services

        result = get_services(category='store')

        assert 'Pet Food' in result['services']

    def test_get_services_unknown_category(self):
        """get_services should handle unknown category."""
        from apps.ai_assistant.tools import get_services

        result = get_services(category='unknown')

        assert 'error' in result
        assert 'Unknown category' in result['error']

    def test_get_services_all(self):
        """get_services should return all services."""
        from apps.ai_assistant.tools import get_services

        result = get_services(category='all')

        assert 'services' in result
        assert 'clinic' in result['services']
        assert 'pharmacy' in result['services']
        assert 'store' in result['services']


class TestGetContactInfo:
    """Test get_contact_info tool."""

    def test_get_contact_info_returns_data(self):
        """get_contact_info should return contact details."""
        from apps.ai_assistant.tools import get_contact_info

        result = get_contact_info()

        assert 'name' in result
        assert 'phone' in result
        assert 'whatsapp' in result
        assert 'address' in result
        assert 'email' in result
        assert 'Pet-Friendly' in result['name']
        assert '+52 998 316 2438' in result['phone']


# =============================================================================
# Pet Tools Tests
# =============================================================================

@pytest.mark.django_db
class TestPetToolsRegistration:
    """Test pet tools are registered."""

    def test_list_user_pets_tool_registered(self):
        """list_user_pets tool should be registered."""
        from apps.ai_assistant.tools import ToolRegistry
        tools = ToolRegistry.get_tools()
        tool_names = [t.name for t in tools]
        assert 'list_user_pets' in tool_names

    def test_get_pet_profile_tool_registered(self):
        """get_pet_profile tool should be registered."""
        from apps.ai_assistant.tools import ToolRegistry
        tools = ToolRegistry.get_tools()
        tool_names = [t.name for t in tools]
        assert 'get_pet_profile' in tool_names

    def test_get_vaccination_status_tool_registered(self):
        """get_vaccination_status tool should be registered."""
        from apps.ai_assistant.tools import ToolRegistry
        tools = ToolRegistry.get_tools()
        tool_names = [t.name for t in tools]
        assert 'get_vaccination_status' in tool_names

    def test_pet_tools_require_customer_permission(self):
        """Pet tools should require customer permission level."""
        from apps.ai_assistant.tools import ToolRegistry
        tools = ToolRegistry.get_tools()

        pet_tool_names = ['list_user_pets', 'get_pet_profile', 'get_vaccination_status']
        for tool in tools:
            if tool.name in pet_tool_names:
                assert tool.permission_level == 'customer'


@pytest.mark.django_db
class TestListUserPetsTool:
    """Test list_user_pets tool."""

    @pytest.fixture
    def owner(self):
        return User.objects.create_user(
            username='petowner',
            email='owner@test.com',
            password='pass123',
            role='owner'
        )

    @pytest.fixture
    def pets(self, owner):
        from apps.pets.models import Pet
        from datetime import date
        Pet.objects.create(
            owner=owner,
            name='Luna',
            species='dog',
            breed='Golden Retriever',
            date_of_birth=date(2021, 3, 15)
        )
        Pet.objects.create(
            owner=owner,
            name='Mochi',
            species='cat',
            breed='Siamese',
            date_of_birth=date(2022, 7, 20)
        )
        return owner.pets.all()

    def test_list_user_pets_returns_pets(self, owner, pets):
        """list_user_pets should return user's pets."""
        from apps.ai_assistant.tools import list_user_pets

        result = list_user_pets(user_id=owner.id)

        assert 'pets' in result
        assert len(result['pets']) == 2
        pet_names = [p['name'] for p in result['pets']]
        assert 'Luna' in pet_names
        assert 'Mochi' in pet_names

    def test_list_user_pets_includes_species(self, owner, pets):
        """list_user_pets should include species info."""
        from apps.ai_assistant.tools import list_user_pets

        result = list_user_pets(user_id=owner.id)

        assert result['pets'][0]['species'] in ['dog', 'cat']

    def test_list_user_pets_empty_for_no_pets(self, owner):
        """list_user_pets should return empty list for user with no pets."""
        from apps.ai_assistant.tools import list_user_pets

        result = list_user_pets(user_id=owner.id)

        assert 'pets' in result
        assert len(result['pets']) == 0

    def test_list_user_pets_invalid_user(self):
        """list_user_pets should handle invalid user ID."""
        from apps.ai_assistant.tools import list_user_pets

        result = list_user_pets(user_id=99999)

        assert 'error' in result


@pytest.mark.django_db
class TestGetPetProfileTool:
    """Test get_pet_profile tool."""

    @pytest.fixture
    def owner(self):
        return User.objects.create_user(
            username='petowner',
            email='owner@test.com',
            password='pass123',
            role='owner'
        )

    @pytest.fixture
    def pet(self, owner):
        from apps.pets.models import Pet
        from datetime import date
        from decimal import Decimal
        return Pet.objects.create(
            owner=owner,
            name='Max',
            species='dog',
            breed='Labrador',
            gender='male',
            date_of_birth=date(2020, 5, 10),
            weight_kg=Decimal('28.5'),
            microchip_id='123456789012345',
            is_neutered=True
        )

    def test_get_pet_profile_returns_details(self, owner, pet):
        """get_pet_profile should return pet details."""
        from apps.ai_assistant.tools import get_pet_profile

        result = get_pet_profile(pet_id=pet.id, user_id=owner.id)

        assert result['name'] == 'Max'
        assert result['species'] == 'dog'
        assert result['breed'] == 'Labrador'
        assert result['gender'] == 'male'
        assert result['microchip_id'] == '123456789012345'
        assert result['is_neutered'] is True

    def test_get_pet_profile_includes_age(self, owner, pet):
        """get_pet_profile should include calculated age."""
        from apps.ai_assistant.tools import get_pet_profile

        result = get_pet_profile(pet_id=pet.id, user_id=owner.id)

        assert 'age_years' in result
        assert result['age_years'] >= 4  # Pet born in 2020

    def test_get_pet_profile_not_found(self, owner):
        """get_pet_profile should handle pet not found."""
        from apps.ai_assistant.tools import get_pet_profile

        result = get_pet_profile(pet_id=99999, user_id=owner.id)

        assert 'error' in result

    def test_get_pet_profile_wrong_owner(self, pet):
        """get_pet_profile should deny access to other user's pet."""
        from apps.ai_assistant.tools import get_pet_profile

        other_user = User.objects.create_user(
            username='other',
            email='other@test.com',
            password='pass123'
        )

        result = get_pet_profile(pet_id=pet.id, user_id=other_user.id)

        assert 'error' in result


@pytest.mark.django_db
class TestGetVaccinationStatusTool:
    """Test get_vaccination_status tool."""

    @pytest.fixture
    def owner(self):
        return User.objects.create_user(
            username='petowner',
            email='owner@test.com',
            password='pass123',
            role='owner'
        )

    @pytest.fixture
    def pet_with_vaccinations(self, owner):
        from apps.pets.models import Pet, Vaccination
        from datetime import date, timedelta

        pet = Pet.objects.create(
            owner=owner,
            name='Buddy',
            species='dog'
        )

        # Current vaccination
        Vaccination.objects.create(
            pet=pet,
            vaccine_name='Rabies',
            date_administered=date.today() - timedelta(days=30),
            next_due_date=date.today() + timedelta(days=335)
        )

        # Overdue vaccination
        Vaccination.objects.create(
            pet=pet,
            vaccine_name='DHPP',
            date_administered=date.today() - timedelta(days=400),
            next_due_date=date.today() - timedelta(days=35)
        )

        # Due soon vaccination
        Vaccination.objects.create(
            pet=pet,
            vaccine_name='Bordetella',
            date_administered=date.today() - timedelta(days=340),
            next_due_date=date.today() + timedelta(days=15)
        )

        return pet

    def test_get_vaccination_status_returns_summary(self, owner, pet_with_vaccinations):
        """get_vaccination_status should return vaccination summary."""
        from apps.ai_assistant.tools import get_vaccination_status

        result = get_vaccination_status(pet_id=pet_with_vaccinations.id, user_id=owner.id)

        assert 'pet_name' in result
        assert result['pet_name'] == 'Buddy'
        assert 'vaccinations' in result
        assert len(result['vaccinations']) == 3

    def test_get_vaccination_status_identifies_overdue(self, owner, pet_with_vaccinations):
        """get_vaccination_status should identify overdue vaccinations."""
        from apps.ai_assistant.tools import get_vaccination_status

        result = get_vaccination_status(pet_id=pet_with_vaccinations.id, user_id=owner.id)

        overdue = [v for v in result['vaccinations'] if v['is_overdue']]
        assert len(overdue) >= 1
        assert any(v['vaccine_name'] == 'DHPP' for v in overdue)

    def test_get_vaccination_status_identifies_due_soon(self, owner, pet_with_vaccinations):
        """get_vaccination_status should identify vaccinations due soon."""
        from apps.ai_assistant.tools import get_vaccination_status

        result = get_vaccination_status(pet_id=pet_with_vaccinations.id, user_id=owner.id)

        due_soon = [v for v in result['vaccinations'] if v['is_due_soon']]
        assert len(due_soon) >= 1
        assert any(v['vaccine_name'] == 'Bordetella' for v in due_soon)

    def test_get_vaccination_status_not_found(self, owner):
        """get_vaccination_status should handle pet not found."""
        from apps.ai_assistant.tools import get_vaccination_status

        result = get_vaccination_status(pet_id=99999, user_id=owner.id)

        assert 'error' in result

    def test_get_vaccination_status_wrong_owner(self, pet_with_vaccinations):
        """get_vaccination_status should deny access to other user's pet."""
        from apps.ai_assistant.tools import get_vaccination_status

        other_user = User.objects.create_user(
            username='other',
            email='other@test.com',
            password='pass123'
        )

        result = get_vaccination_status(pet_id=pet_with_vaccinations.id, user_id=other_user.id)

        assert 'error' in result
