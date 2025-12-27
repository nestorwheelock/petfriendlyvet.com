# T-049: Message Escalation Engine

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md and [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement automatic message escalation across channels
**Related Story**: S-006
**Epoch**: 4
**Estimate**: 3 hours

### Constraints
**Allowed File Paths**: apps/communications/
**Forbidden Paths**: None

### Deliverables
- [ ] Escalation rules engine
- [ ] Channel fallback logic
- [ ] Confirmation tracking
- [ ] Escalation alerts

### Implementation Details

#### Escalation Service
```python
from django.utils import timezone
from datetime import timedelta
from celery import shared_task


class EscalationService:
    """Manage message escalation across channels."""

    def __init__(self):
        self.channel_priority = ['whatsapp', 'sms', 'email', 'voice']

    def send_with_escalation(
        self,
        owner,
        message_type: str,
        context: dict,
        require_confirmation: bool = False
    ):
        """Send message with automatic escalation."""

        preferences = ContactPreference.objects.filter(owner=owner).first()

        if not preferences:
            return {'success': False, 'error': 'No contact preferences'}

        # Get preferred channel and escalation chain
        primary_channel = preferences.preferred_channel
        escalation_chain = self._build_escalation_chain(
            preferences,
            starting_from=primary_channel
        )

        # Get template for message type
        template = MessageTemplate.objects.filter(
            template_type=message_type,
            is_active=True
        ).first()

        if not template:
            return {'success': False, 'error': f'No template for {message_type}'}

        # Create escalation record
        escalation = MessageEscalation.objects.create(
            owner=owner,
            message_type=message_type,
            context=context,
            template=template,
            require_confirmation=require_confirmation,
            escalation_chain=escalation_chain,
            current_step=0
        )

        # Send first attempt
        self._send_step(escalation)

        return {
            'success': True,
            'escalation_id': escalation.id,
            'first_channel': escalation_chain[0] if escalation_chain else None
        }

    def _build_escalation_chain(
        self,
        preferences: ContactPreference,
        starting_from: str
    ) -> list:
        """Build ordered list of channels to try."""

        chain = []

        # Start with preferred channel
        if starting_from and self._has_contact(preferences, starting_from):
            chain.append({
                'channel': starting_from,
                'contact': self._get_contact(preferences, starting_from),
                'wait_minutes': preferences.escalation_after_minutes or 60
            })

        # Add escalation channels
        for channel in preferences.escalation_channels or []:
            if channel != starting_from and self._has_contact(preferences, channel):
                chain.append({
                    'channel': channel,
                    'contact': self._get_contact(preferences, channel),
                    'wait_minutes': 30  # Shorter wait for escalations
                })

        return chain

    def _has_contact(self, preferences: ContactPreference, channel: str) -> bool:
        """Check if owner has contact for channel."""
        contact = self._get_contact(preferences, channel)
        return bool(contact)

    def _get_contact(self, preferences: ContactPreference, channel: str) -> str:
        """Get contact info for channel."""
        if channel == 'email':
            return preferences.email or preferences.owner.email
        elif channel == 'sms':
            return preferences.phone
        elif channel == 'whatsapp':
            return preferences.whatsapp or preferences.phone
        elif channel == 'voice':
            return preferences.phone
        return None

    def _send_step(self, escalation: 'MessageEscalation'):
        """Send current escalation step."""

        if escalation.current_step >= len(escalation.escalation_chain):
            escalation.status = 'exhausted'
            escalation.save()
            return

        step = escalation.escalation_chain[escalation.current_step]
        channel_type = step['channel']
        contact = step['contact']

        # Get channel
        channel = Channel.objects.filter(
            channel_type=channel_type,
            is_active=True
        ).first()

        if not channel:
            # Skip to next channel
            escalation.current_step += 1
            escalation.save()
            self._send_step(escalation)
            return

        # Render message
        from django.template import Template, Context
        template = escalation.template
        body = Template(template.body_text).render(Context(escalation.context))

        # Create message
        message = Message.objects.create(
            channel=channel,
            direction='outbound',
            to_contact=contact,
            body=body,
            template=template,
            status='pending',
            metadata={'escalation_id': escalation.id}
        )

        # Send via appropriate service
        result = self._dispatch_message(message, channel_type, contact, body)

        if result['success']:
            message.external_id = result.get('message_id', '')
            message.status = 'sent'
            message.sent_at = timezone.now()
            message.save()

            escalation.last_attempt_at = timezone.now()
            escalation.save()

            # Schedule escalation check
            if escalation.require_confirmation:
                schedule_escalation_check.apply_async(
                    args=[escalation.id],
                    countdown=step['wait_minutes'] * 60
                )
        else:
            message.status = 'failed'
            message.error_message = result.get('error', '')
            message.save()

            # Immediately try next channel
            escalation.current_step += 1
            escalation.save()
            self._send_step(escalation)

    def _dispatch_message(self, message, channel_type, contact, body):
        """Dispatch message to appropriate service."""

        if channel_type == 'email':
            from apps.communications.services.email import EmailService
            return EmailService().send(to_email=contact, subject='Pet-Friendly', body_text=body)
        elif channel_type == 'sms':
            from apps.communications.services.sms import SMSService
            return SMSService().send(to_phone=contact, body=body)
        elif channel_type == 'whatsapp':
            from apps.communications.services.whatsapp import WhatsAppService
            # Check if within session window (24h)
            # If not, need to use template
            return WhatsAppService().send_text(to_phone=contact, body=body)
        elif channel_type == 'voice':
            # Future: trigger voice call
            return {'success': False, 'error': 'Voice not implemented'}

        return {'success': False, 'error': 'Unknown channel'}

    def confirm_receipt(self, escalation_id: int, method: str = 'reply'):
        """Mark escalation as confirmed."""

        escalation = MessageEscalation.objects.get(id=escalation_id)
        escalation.status = 'confirmed'
        escalation.confirmed_at = timezone.now()
        escalation.confirmation_method = method
        escalation.save()

        return True

    def check_and_escalate(self, escalation_id: int):
        """Check if escalation is needed."""

        escalation = MessageEscalation.objects.get(id=escalation_id)

        if escalation.status in ['confirmed', 'exhausted', 'cancelled']:
            return

        # Check if response received
        if self._has_response(escalation):
            self.confirm_receipt(escalation_id, 'reply')
            return

        # Escalate to next channel
        escalation.current_step += 1
        escalation.save()
        self._send_step(escalation)

    def _has_response(self, escalation) -> bool:
        """Check if owner has responded since message sent."""

        return Message.objects.filter(
            conversation__owner=escalation.owner,
            direction='inbound',
            created_at__gte=escalation.last_attempt_at
        ).exists()


class MessageEscalation(models.Model):
    """Track message escalation."""

    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('sent', 'Enviado'),
        ('confirmed', 'Confirmado'),
        ('exhausted', 'Agotado'),
        ('cancelled', 'Cancelado'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    message_type = models.CharField(max_length=50)
    template = models.ForeignKey(MessageTemplate, on_delete=models.SET_NULL, null=True)
    context = models.JSONField(default=dict)

    require_confirmation = models.BooleanField(default=False)
    escalation_chain = models.JSONField(default=list)
    current_step = models.IntegerField(default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    last_attempt_at = models.DateTimeField(null=True)
    confirmed_at = models.DateTimeField(null=True)
    confirmation_method = models.CharField(max_length=50, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


@shared_task
def schedule_escalation_check(escalation_id: int):
    """Celery task to check escalation status."""
    EscalationService().check_and_escalate(escalation_id)
```

### Test Cases
- [ ] Escalation chain builds correctly
- [ ] First message sends
- [ ] Failed channel triggers escalation
- [ ] Confirmation stops escalation
- [ ] Response detection works
- [ ] Exhausted status when all channels tried
- [ ] Quiet hours respected

### Definition of Done
- [ ] Escalation engine complete
- [ ] Multi-channel fallback works
- [ ] Celery tasks working
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-044: Communication Channel Models
- T-045 to T-047: Channel integrations
