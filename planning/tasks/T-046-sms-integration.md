# T-046: SMS Integration (Twilio)

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement SMS sending via Twilio
**Related Story**: S-006
**Epoch**: 4
**Estimate**: 3 hours

### Constraints
**Allowed File Paths**: apps/communications/
**Forbidden Paths**: None

### Deliverables
- [ ] Twilio client configuration
- [ ] SMS sending service
- [ ] Inbound SMS handling
- [ ] Delivery status webhooks
- [ ] Phone number validation

### Implementation Details

#### Twilio Configuration
```python
# settings.py

TWILIO_ACCOUNT_SID = env('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = env('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = env('TWILIO_PHONE_NUMBER', default='+529983162438')
TWILIO_MESSAGING_SERVICE_SID = env('TWILIO_MESSAGING_SERVICE_SID', default=None)
```

#### SMS Service
```python
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from django.conf import settings
import phonenumbers


class SMSService:
    """SMS sending via Twilio."""

    def __init__(self):
        self.client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
        self.from_number = settings.TWILIO_PHONE_NUMBER
        self.messaging_service = settings.TWILIO_MESSAGING_SERVICE_SID

    def send(
        self,
        to_phone: str,
        body: str,
        media_urls: list = None
    ) -> dict:
        """Send an SMS."""

        # Validate and format phone number
        formatted = self._format_phone(to_phone)
        if not formatted:
            return {'success': False, 'error': 'Número de teléfono inválido'}

        try:
            message_params = {
                'to': formatted,
                'body': body[:1600],  # SMS limit
            }

            # Use messaging service if available (better deliverability)
            if self.messaging_service:
                message_params['messaging_service_sid'] = self.messaging_service
            else:
                message_params['from_'] = self.from_number

            # Add media for MMS
            if media_urls:
                message_params['media_url'] = media_urls[:10]

            message = self.client.messages.create(**message_params)

            return {
                'success': True,
                'message_sid': message.sid,
                'status': message.status,
                'segments': self._count_segments(body)
            }

        except TwilioRestException as e:
            return {
                'success': False,
                'error': str(e),
                'code': e.code
            }

    def send_template(
        self,
        to_phone: str,
        template: 'MessageTemplate',
        context: dict
    ) -> dict:
        """Send SMS using template."""

        from django.template import Template, Context

        # Render template
        t = Template(template.body_text)
        body = t.render(Context(context))

        return self.send(to_phone, body)

    def _format_phone(self, phone: str) -> str:
        """Format phone to E.164 format for Mexico."""

        try:
            # Default to Mexico if no country code
            if not phone.startswith('+'):
                phone = '+52' + phone.lstrip('0')

            parsed = phonenumbers.parse(phone, 'MX')

            if not phonenumbers.is_valid_number(parsed):
                return None

            return phonenumbers.format_number(
                parsed,
                phonenumbers.PhoneNumberFormat.E164
            )

        except phonenumbers.NumberParseException:
            return None

    def _count_segments(self, body: str) -> int:
        """Count SMS segments."""

        # GSM-7 allows 160 chars, Unicode allows 70
        has_unicode = any(ord(c) > 127 for c in body)

        if has_unicode:
            segment_size = 67 if len(body) > 70 else 70
        else:
            segment_size = 153 if len(body) > 160 else 160

        return (len(body) + segment_size - 1) // segment_size

    def lookup(self, phone: str) -> dict:
        """Lookup phone number info."""

        formatted = self._format_phone(phone)
        if not formatted:
            return {'valid': False}

        try:
            lookup = self.client.lookups.v2.phone_numbers(formatted).fetch(
                fields='line_type_intelligence'
            )

            return {
                'valid': True,
                'phone': lookup.phone_number,
                'country_code': lookup.country_code,
                'carrier': lookup.line_type_intelligence.get('carrier_name'),
                'type': lookup.line_type_intelligence.get('type'),
                'mobile': lookup.line_type_intelligence.get('type') == 'mobile'
            }

        except TwilioRestException:
            return {'valid': False}


class SMSWebhookHandler:
    """Handle Twilio SMS webhooks."""

    def process_status(self, data: dict):
        """Process delivery status update."""
        from apps.communications.models import Message

        message_sid = data.get('MessageSid')
        status = data.get('MessageStatus')

        status_map = {
            'queued': 'queued',
            'sent': 'sent',
            'delivered': 'delivered',
            'undelivered': 'failed',
            'failed': 'failed',
        }

        mapped_status = status_map.get(status, 'pending')

        message = Message.objects.filter(external_id=message_sid).first()
        if message:
            message.status = mapped_status
            if mapped_status == 'delivered':
                message.delivered_at = timezone.now()
            elif mapped_status == 'failed':
                message.failed_at = timezone.now()
                message.error_message = data.get('ErrorMessage', '')
            message.save()

    def process_inbound(self, data: dict) -> dict:
        """Process inbound SMS."""
        from apps.communications.models import Conversation, Message, Channel

        from_phone = data.get('From')
        body = data.get('Body')
        media_urls = []

        # Get media if MMS
        num_media = int(data.get('NumMedia', 0))
        for i in range(num_media):
            media_urls.append(data.get(f'MediaUrl{i}'))

        # Find or create conversation
        channel = Channel.objects.get(channel_type='sms')

        # Try to find existing conversation
        conversation = Conversation.objects.filter(
            owner__profile__phone=from_phone,
            status__in=['active', 'pending']
        ).first()

        if not conversation:
            # Create new conversation
            from django.contrib.auth import get_user_model
            User = get_user_model()

            user = User.objects.filter(profile__phone=from_phone).first()
            if not user:
                # Anonymous message
                user = None

            conversation = Conversation.objects.create(
                owner=user,
                subject=f'SMS desde {from_phone}',
                status='pending'
            )

        # Create message
        message = Message.objects.create(
            conversation=conversation,
            channel=channel,
            direction='inbound',
            to_contact=settings.TWILIO_PHONE_NUMBER,
            body=body,
            external_id=data.get('MessageSid'),
            status='delivered',
            attachments=[{'url': url} for url in media_urls]
        )

        conversation.last_message_at = timezone.now()
        conversation.last_customer_message_at = timezone.now()
        conversation.unread_count += 1
        conversation.save()

        return {
            'conversation_id': conversation.id,
            'message_id': message.id
        }
```

#### Webhook Views
```python
from django.http import HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from twilio.twiml.messaging_response import MessagingResponse


@method_decorator(csrf_exempt, name='dispatch')
class SMSStatusView(View):
    """Receive SMS status webhooks."""

    def post(self, request):
        handler = SMSWebhookHandler()
        handler.process_status(request.POST.dict())
        return HttpResponse('OK')


@method_decorator(csrf_exempt, name='dispatch')
class SMSInboundView(View):
    """Receive inbound SMS."""

    def post(self, request):
        handler = SMSWebhookHandler()
        result = handler.process_inbound(request.POST.dict())

        # Auto-reply
        response = MessagingResponse()
        response.message(
            "Gracias por tu mensaje. Te responderemos pronto. "
            "Para emergencias llama al +52 998 316 2438"
        )

        return HttpResponse(str(response), content_type='text/xml')
```

### Test Cases
- [ ] SMS sends successfully
- [ ] Phone formatting works for Mexico
- [ ] Invalid phones rejected
- [ ] Segment counting accurate
- [ ] Status webhook updates message
- [ ] Inbound SMS creates message
- [ ] Auto-reply works

### Definition of Done
- [ ] Twilio integration complete
- [ ] Webhook handlers working
- [ ] Phone validation working
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-044: Communication Channel Models

### Environment Variables
```
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=+529983162438
TWILIO_MESSAGING_SERVICE_SID=
```
