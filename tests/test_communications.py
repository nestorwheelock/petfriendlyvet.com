"""Tests for omnichannel communications app (TDD first)."""
import pytest
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from apps.accounts.models import User

pytestmark = pytest.mark.django_db


class TestCommunicationChannelModel:
    """Tests for CommunicationChannel model."""

    def test_create_email_channel(self, user):
        """Test creating an email channel."""
        from apps.communications.models import CommunicationChannel

        channel = CommunicationChannel.objects.create(
            user=user,
            channel_type='email',
            identifier='user@example.com',
            is_verified=True,
            is_primary=True,
        )

        assert channel.user == user
        assert channel.channel_type == 'email'
        assert channel.identifier == 'user@example.com'
        assert channel.is_verified is True
        assert channel.is_primary is True

    def test_create_sms_channel(self, user):
        """Test creating an SMS channel."""
        from apps.communications.models import CommunicationChannel

        channel = CommunicationChannel.objects.create(
            user=user,
            channel_type='sms',
            identifier='+529981234567',
        )

        assert channel.channel_type == 'sms'
        assert channel.identifier == '+529981234567'

    def test_create_whatsapp_channel(self, user):
        """Test creating a WhatsApp channel."""
        from apps.communications.models import CommunicationChannel

        channel = CommunicationChannel.objects.create(
            user=user,
            channel_type='whatsapp',
            identifier='+529981234567',
            preferences={'marketing': False, 'reminders': True},
        )

        assert channel.channel_type == 'whatsapp'
        assert channel.preferences['reminders'] is True

    def test_channel_str_representation(self, user):
        """Test string representation of channel."""
        from apps.communications.models import CommunicationChannel

        channel = CommunicationChannel.objects.create(
            user=user,
            channel_type='email',
            identifier='test@example.com',
        )

        assert 'email' in str(channel).lower()
        assert 'test@example.com' in str(channel)

    def test_channel_types(self):
        """Test all channel types are valid."""
        from apps.communications.models import CommunicationChannel

        channel_types = ['email', 'sms', 'whatsapp', 'voice']
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        for channel_type in channel_types:
            channel = CommunicationChannel.objects.create(
                user=user,
                channel_type=channel_type,
                identifier=f'{channel_type}@test.com',
            )
            assert channel.channel_type == channel_type


class TestMessageTemplateModel:
    """Tests for MessageTemplate model."""

    def test_create_appointment_reminder_template(self):
        """Test creating an appointment reminder template."""
        from apps.communications.models import MessageTemplate

        template = MessageTemplate.objects.create(
            name='Appointment Reminder 24h',
            template_type='appointment_reminder',
            subject_es='Recordatorio de cita',
            subject_en='Appointment Reminder',
            body_es='Hola {{owner_name}}, te recordamos tu cita mañana a las {{time}}.',
            body_en='Hello {{owner_name}}, reminder about your appointment tomorrow at {{time}}.',
            channels=['email', 'sms', 'whatsapp'],
        )

        assert template.name == 'Appointment Reminder 24h'
        assert template.template_type == 'appointment_reminder'
        assert 'email' in template.channels
        assert template.is_active is True

    def test_template_str_representation(self):
        """Test string representation of template."""
        from apps.communications.models import MessageTemplate

        template = MessageTemplate.objects.create(
            name='Order Confirmation',
            template_type='order_update',
            body_es='Tu pedido ha sido confirmado.',
            body_en='Your order has been confirmed.',
        )

        assert str(template) == 'Order Confirmation'

    def test_template_types(self):
        """Test various template types."""
        from apps.communications.models import MessageTemplate

        types = ['appointment_reminder', 'order_update', 'vaccination_due', 'prescription_refill']
        for template_type in types:
            template = MessageTemplate.objects.create(
                name=f'Test {template_type}',
                template_type=template_type,
                body_es='Test body',
                body_en='Test body',
            )
            assert template.template_type == template_type


class TestMessageModel:
    """Tests for Message model."""

    def test_create_outbound_message(self, user):
        """Test creating an outbound message."""
        from apps.communications.models import Message

        message = Message.objects.create(
            user=user,
            channel='email',
            direction='outbound',
            recipient='user@example.com',
            subject='Test Subject',
            body='Test message body',
        )

        assert message.user == user
        assert message.direction == 'outbound'
        assert message.status == 'pending'

    def test_create_inbound_message(self, user):
        """Test creating an inbound message."""
        from apps.communications.models import Message

        message = Message.objects.create(
            user=user,
            channel='whatsapp',
            direction='inbound',
            recipient='+529981234567',
            body='Customer response',
        )

        assert message.direction == 'inbound'

    def test_message_status_choices(self, user):
        """Test message status transitions."""
        from apps.communications.models import Message

        statuses = ['pending', 'sent', 'delivered', 'read', 'failed']
        for status in statuses:
            message = Message.objects.create(
                user=user,
                channel='sms',
                direction='outbound',
                recipient='+529981234567',
                body='Test',
                status=status,
            )
            assert message.status == status

    def test_message_timestamps(self, user):
        """Test message timestamps."""
        from apps.communications.models import Message

        now = timezone.now()
        message = Message.objects.create(
            user=user,
            channel='email',
            direction='outbound',
            recipient='test@example.com',
            body='Test',
            sent_at=now,
            delivered_at=now + timedelta(seconds=5),
        )

        assert message.sent_at == now
        assert message.delivered_at is not None

    def test_message_ordering(self, user):
        """Test messages are ordered by created_at descending."""
        from apps.communications.models import Message

        m1 = Message.objects.create(
            user=user,
            channel='email',
            direction='outbound',
            recipient='test@example.com',
            body='First',
        )
        m2 = Message.objects.create(
            user=user,
            channel='email',
            direction='outbound',
            recipient='test@example.com',
            body='Second',
        )

        messages = list(Message.objects.all())
        assert messages[0] == m2  # Most recent first


class TestReminderScheduleModel:
    """Tests for ReminderSchedule model."""

    def test_create_appointment_reminder(self, user):
        """Test creating an appointment reminder."""
        from apps.communications.models import ReminderSchedule
        from apps.appointments.models import Appointment, ServiceType

        # Create service type
        service = ServiceType.objects.create(
            name='Checkup',
            duration_minutes=30,
            price=100,
            is_active=True
        )

        # Create appointment with correct fields
        scheduled_start = timezone.now() + timedelta(days=1)
        appointment = Appointment.objects.create(
            owner=user,
            service=service,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_start + timedelta(minutes=30),
            status='scheduled',
        )

        content_type = ContentType.objects.get_for_model(Appointment)

        reminder = ReminderSchedule.objects.create(
            reminder_type='appointment',
            content_type=content_type,
            object_id=appointment.id,
            scheduled_for=timezone.now() + timedelta(hours=24),
        )

        assert reminder.reminder_type == 'appointment'
        assert reminder.sent is False
        assert reminder.confirmed is False

    def test_reminder_types(self, user):
        """Test all reminder types."""
        from apps.communications.models import ReminderSchedule

        types = ['appointment', 'vaccination', 'prescription', 'followup']
        content_type = ContentType.objects.get_for_model(User)

        for reminder_type in types:
            reminder = ReminderSchedule.objects.create(
                reminder_type=reminder_type,
                content_type=content_type,
                object_id=user.id,
                scheduled_for=timezone.now() + timedelta(hours=24),
            )
            assert reminder.reminder_type == reminder_type


class TestEscalationRuleModel:
    """Tests for EscalationRule model."""

    def test_create_escalation_rule(self):
        """Test creating an escalation rule."""
        from apps.communications.models import EscalationRule

        rule = EscalationRule.objects.create(
            reminder_type='appointment',
            step=1,
            channel='email',
            wait_hours=2,
        )

        assert rule.reminder_type == 'appointment'
        assert rule.step == 1
        assert rule.channel == 'email'
        assert rule.wait_hours == 2
        assert rule.is_active is True

    def test_escalation_rule_ordering(self):
        """Test escalation rules are ordered by type and step."""
        from apps.communications.models import EscalationRule

        r1 = EscalationRule.objects.create(
            reminder_type='appointment',
            step=2,
            channel='sms',
            wait_hours=2,
        )
        r2 = EscalationRule.objects.create(
            reminder_type='appointment',
            step=1,
            channel='email',
            wait_hours=0,
        )

        rules = list(EscalationRule.objects.filter(reminder_type='appointment'))
        assert rules[0] == r2  # Step 1 first
        assert rules[1] == r1  # Step 2 second


class TestCommunicationAITools:
    """Tests for communication AI tools."""

    def test_send_message_tool_exists(self):
        """Test send_message tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('send_message')
        assert tool is not None

    def test_send_email_message(self, user):
        """Test sending an email message."""
        from apps.ai_assistant.tools import send_message
        from apps.communications.models import CommunicationChannel

        CommunicationChannel.objects.create(
            user=user,
            channel_type='email',
            identifier='user@example.com',
            is_verified=True,
            is_primary=True,
        )

        result = send_message(
            user_id=user.id,
            message='Test message content',
            channel='email',
        )

        assert result['success'] is True
        assert 'message_id' in result

    def test_send_sms_message(self, user):
        """Test sending an SMS message."""
        from apps.ai_assistant.tools import send_message
        from apps.communications.models import CommunicationChannel

        CommunicationChannel.objects.create(
            user=user,
            channel_type='sms',
            identifier='+529981234567',
            is_verified=True,
        )

        result = send_message(
            user_id=user.id,
            message='Test SMS',
            channel='sms',
        )

        assert result['success'] is True

    def test_get_unread_messages_tool_exists(self):
        """Test get_unread_messages tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('get_unread_messages')
        assert tool is not None

    def test_get_unread_messages(self, user):
        """Test getting unread messages."""
        from apps.ai_assistant.tools import get_unread_messages
        from apps.communications.models import Message

        Message.objects.create(
            user=user,
            channel='whatsapp',
            direction='inbound',
            recipient='+529981234567',
            body='Customer question',
            status='delivered',
        )

        result = get_unread_messages()

        assert result['count'] >= 1

    def test_schedule_reminder_tool_exists(self):
        """Test schedule_reminder tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('schedule_reminder')
        assert tool is not None

    def test_schedule_reminder(self, user):
        """Test scheduling a reminder."""
        from apps.ai_assistant.tools import schedule_reminder

        scheduled_for = (timezone.now() + timedelta(hours=24)).isoformat()

        result = schedule_reminder(
            user_id=user.id,
            reminder_type='appointment',
            scheduled_for=scheduled_for,
            message='Don\'t forget your appointment tomorrow!',
        )

        assert result['success'] is True
        assert 'reminder_id' in result

    def test_check_message_status_tool_exists(self):
        """Test check_message_status tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('check_message_status')
        assert tool is not None

    def test_check_message_status(self, user):
        """Test checking message delivery status."""
        from apps.ai_assistant.tools import check_message_status
        from apps.communications.models import Message

        message = Message.objects.create(
            user=user,
            channel='email',
            direction='outbound',
            recipient='test@example.com',
            body='Test',
            status='sent',
            external_id='ext123',
        )

        result = check_message_status(message_id=message.id)

        assert result['success'] is True
        assert result['status'] == 'sent'

    def test_get_conversation_history_tool_exists(self):
        """Test get_conversation_history tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('get_conversation_history')
        assert tool is not None

    def test_get_conversation_history(self, user):
        """Test getting conversation history."""
        from apps.ai_assistant.tools import get_conversation_history
        from apps.communications.models import Message

        Message.objects.create(
            user=user,
            channel='whatsapp',
            direction='outbound',
            recipient='+529981234567',
            body='Hello',
        )
        Message.objects.create(
            user=user,
            channel='whatsapp',
            direction='inbound',
            recipient='+529981234567',
            body='Hi there',
        )

        result = get_conversation_history(user_id=user.id)

        assert result['count'] >= 2
        assert len(result['messages']) >= 2


class TestCommunicationIntegration:
    """Integration tests for communication workflows."""

    def test_multi_channel_message_flow(self, user):
        """Test sending messages across multiple channels."""
        from apps.communications.models import CommunicationChannel, Message
        from apps.ai_assistant.tools import send_message

        # Setup channels
        CommunicationChannel.objects.create(
            user=user,
            channel_type='email',
            identifier='user@example.com',
            is_verified=True,
            is_primary=True,
        )
        CommunicationChannel.objects.create(
            user=user,
            channel_type='sms',
            identifier='+529981234567',
            is_verified=True,
        )

        # Send via email
        email_result = send_message(
            user_id=user.id,
            message='Email notification',
            channel='email',
        )
        assert email_result['success'] is True

        # Send via SMS
        sms_result = send_message(
            user_id=user.id,
            message='SMS notification',
            channel='sms',
        )
        assert sms_result['success'] is True

        # Verify messages created
        messages = Message.objects.filter(user=user)
        assert messages.count() >= 2

    def test_reminder_with_escalation_setup(self, user):
        """Test setting up reminder with escalation rules."""
        from apps.communications.models import EscalationRule, ReminderSchedule
        from django.contrib.contenttypes.models import ContentType

        # Create escalation rules
        EscalationRule.objects.create(
            reminder_type='appointment',
            step=1,
            channel='email',
            wait_hours=0,
        )
        EscalationRule.objects.create(
            reminder_type='appointment',
            step=2,
            channel='sms',
            wait_hours=2,
        )
        EscalationRule.objects.create(
            reminder_type='appointment',
            step=3,
            channel='whatsapp',
            wait_hours=2,
        )

        content_type = ContentType.objects.get_for_model(User)

        # Create reminder
        reminder = ReminderSchedule.objects.create(
            reminder_type='appointment',
            content_type=content_type,
            object_id=user.id,
            scheduled_for=timezone.now() + timedelta(hours=24),
        )

        # Get applicable rules
        rules = EscalationRule.objects.filter(
            reminder_type='appointment',
            is_active=True
        ).order_by('step')

        assert rules.count() == 3
        assert rules[0].channel == 'email'
        assert rules[1].channel == 'sms'
        assert rules[2].channel == 'whatsapp'


# Fixtures
@pytest.fixture
def user():
    """Create a test user."""
    return User.objects.create_user(
        username='commuser',
        email='comm@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User',
    )
