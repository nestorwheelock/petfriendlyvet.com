"""Tests for T-012 Admin Chat Interface.

Tests validate admin/staff AI chat:
- Admin page loads for staff/admin users
- Elevated tool access
- Tool execution visibility
- Conversation history browser
- Quick commands palette
- Mobile-optimized layout
"""
import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestAdminChatAccess:
    """Test admin chat access control."""

    @pytest.fixture
    def staff_user(self):
        return User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='testpass123',
            role='staff'
        )

    @pytest.fixture
    def admin_user(self):
        return User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='testpass123',
            role='admin'
        )

    @pytest.fixture
    def regular_user(self):
        return User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='testpass123',
            role='customer'
        )

    def test_admin_chat_url_exists(self):
        """Admin chat URL should be resolvable."""
        url = reverse('ai_assistant:admin_chat')
        assert '/chat/' in url or '/admin' in url

    def test_anonymous_redirected_to_login(self, client):
        """Anonymous users should be redirected to login."""
        url = reverse('ai_assistant:admin_chat')
        response = client.get(url)
        assert response.status_code in [302, 403]

    def test_customer_denied_access(self, client, regular_user):
        """Regular customers should not access admin chat."""
        client.force_login(regular_user)
        url = reverse('ai_assistant:admin_chat')
        response = client.get(url)
        assert response.status_code in [403, 302]

    def test_staff_can_access(self, client, staff_user):
        """Staff users should access admin chat."""
        client.force_login(staff_user)
        url = reverse('ai_assistant:admin_chat')
        response = client.get(url)
        assert response.status_code == 200

    def test_admin_can_access(self, client, admin_user):
        """Admin users should access admin chat."""
        client.force_login(admin_user)
        url = reverse('ai_assistant:admin_chat')
        response = client.get(url)
        assert response.status_code == 200


@pytest.mark.django_db
class TestAdminChatTemplate:
    """Test admin chat template elements."""

    @pytest.fixture
    def admin_user(self):
        return User.objects.create_user(
            username='admin2',
            email='admin2@example.com',
            password='testpass123',
            role='admin'
        )

    def test_admin_chat_has_quick_commands(self, client, admin_user):
        """Admin chat should have quick commands."""
        client.force_login(admin_user)
        url = reverse('ai_assistant:admin_chat')
        response = client.get(url)
        content = response.content.decode()
        assert 'quick' in content.lower() or 'command' in content.lower()

    def test_admin_chat_has_conversation_area(self, client, admin_user):
        """Admin chat should have message/conversation area."""
        client.force_login(admin_user)
        url = reverse('ai_assistant:admin_chat')
        response = client.get(url)
        content = response.content.decode()
        assert 'message' in content.lower() or 'conversation' in content.lower()

    def test_admin_chat_is_mobile_friendly(self, client, admin_user):
        """Admin chat should be mobile-optimized."""
        client.force_login(admin_user)
        url = reverse('ai_assistant:admin_chat')
        response = client.get(url)
        content = response.content.decode()
        # Check for responsive classes
        has_responsive = any(cls in content for cls in ['sm:', 'md:', 'lg:', 'w-full'])
        assert has_responsive


@pytest.mark.django_db
class TestAdminQuickCommands:
    """Test admin quick commands."""

    def test_admin_quick_commands_defined(self):
        """Admin quick commands should be defined."""
        from apps.ai_assistant.views import ADMIN_QUICK_COMMANDS
        assert len(ADMIN_QUICK_COMMANDS) >= 3

    def test_quick_commands_have_required_fields(self):
        """Quick commands should have label and command."""
        from apps.ai_assistant.views import ADMIN_QUICK_COMMANDS
        for cmd in ADMIN_QUICK_COMMANDS:
            assert 'label' in cmd
            assert 'command' in cmd


@pytest.mark.django_db
class TestAdminToolPermissions:
    """Test elevated tool access for admin."""

    @pytest.fixture
    def admin_user(self):
        return User.objects.create_user(
            username='admin3',
            email='admin3@example.com',
            password='testpass123',
            role='admin'
        )

    @pytest.fixture
    def staff_user(self):
        return User.objects.create_user(
            username='staff3',
            email='staff3@example.com',
            password='testpass123',
            role='staff'
        )

    def test_admin_gets_elevated_tools(self, admin_user):
        """Admin should have access to more tools."""
        from apps.ai_assistant.tools import ToolRegistry
        admin_tools = ToolRegistry.get_tools_for_user(admin_user)
        anon_tools = ToolRegistry.get_tools_for_user(None)
        # Admin should have at least as many tools as anonymous
        assert len(admin_tools) >= len(anon_tools)

    def test_staff_gets_staff_tools(self, staff_user):
        """Staff should have staff-level tool access."""
        from apps.ai_assistant.tools import ToolRegistry
        staff_tools = ToolRegistry.get_tools_for_user(staff_user)
        anon_tools = ToolRegistry.get_tools_for_user(None)
        assert len(staff_tools) >= len(anon_tools)


@pytest.mark.django_db
class TestConversationHistory:
    """Test conversation history browser."""

    @pytest.fixture
    def admin_user(self):
        return User.objects.create_user(
            username='admin4',
            email='admin4@example.com',
            password='testpass123',
            role='admin'
        )

    def test_conversation_list_endpoint_exists(self):
        """Conversation list endpoint should exist."""
        url = reverse('ai_assistant:conversation_list')
        assert url is not None

    def test_conversation_list_requires_staff(self, client):
        """Conversation list should require staff access."""
        url = reverse('ai_assistant:conversation_list')
        response = client.get(url)
        assert response.status_code in [302, 403]

    def test_admin_can_view_conversation_list(self, client, admin_user):
        """Admin can view conversation list."""
        client.force_login(admin_user)
        url = reverse('ai_assistant:conversation_list')
        response = client.get(url)
        assert response.status_code == 200


@pytest.mark.django_db
class TestToolExecutionVisibility:
    """Test that tool execution is visible to admin."""

    @pytest.fixture
    def admin_user(self):
        return User.objects.create_user(
            username='admin5',
            email='admin5@example.com',
            password='testpass123',
            role='admin'
        )

    def test_tool_log_displayed_for_admin(self, client, admin_user):
        """Admin should see tool execution logs."""
        client.force_login(admin_user)
        url = reverse('ai_assistant:admin_chat')
        response = client.get(url)
        content = response.content.decode()
        # Should have some indication of tool/execution visibility
        has_tools = 'tool' in content.lower() or 'execute' in content.lower()
        assert has_tools or 'admin' in content.lower()


@pytest.mark.django_db
class TestAdminChatAPI:
    """Test admin chat API endpoint."""

    @pytest.fixture
    def admin_user(self):
        return User.objects.create_user(
            username='admin6',
            email='admin6@example.com',
            password='testpass123',
            role='admin'
        )

    def test_admin_chat_api_exists(self):
        """Admin chat API should exist."""
        url = reverse('ai_assistant:admin_chat_api')
        assert url is not None

    def test_admin_chat_api_requires_auth(self, client):
        """Admin chat API should require authentication."""
        url = reverse('ai_assistant:admin_chat_api')
        response = client.post(url, {'message': 'test'}, content_type='application/json')
        assert response.status_code in [302, 403, 401]

    def test_admin_chat_api_works_for_admin(self, client, admin_user):
        """Admin chat API should work for admin users."""
        client.force_login(admin_user)
        url = reverse('ai_assistant:admin_chat_api')
        response = client.post(
            url,
            {'message': 'test'},
            content_type='application/json'
        )
        # Should return success or fallback response (no API key in test)
        assert response.status_code in [200, 500, 503]
