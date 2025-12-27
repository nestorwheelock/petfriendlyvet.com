# T-047: WhatsApp Business API Integration

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md and [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement WhatsApp messaging via Meta Cloud API
**Related Story**: S-006
**Epoch**: 4
**Estimate**: 5 hours

### Constraints
**Allowed File Paths**: apps/communications/
**Forbidden Paths**: None

### Deliverables
- [ ] WhatsApp Cloud API client
- [ ] Template message sending
- [ ] Session message sending
- [ ] Media message handling
- [ ] Webhook for inbound messages
- [ ] Message status tracking

### Implementation Details

#### WhatsApp Configuration
```python
# settings.py

WHATSAPP_PHONE_NUMBER_ID = env('WHATSAPP_PHONE_NUMBER_ID')
WHATSAPP_BUSINESS_ACCOUNT_ID = env('WHATSAPP_BUSINESS_ACCOUNT_ID')
WHATSAPP_ACCESS_TOKEN = env('WHATSAPP_ACCESS_TOKEN')
WHATSAPP_VERIFY_TOKEN = env('WHATSAPP_VERIFY_TOKEN')
WHATSAPP_APP_SECRET = env('WHATSAPP_APP_SECRET')
```

#### WhatsApp Service
```python
import requests
import hmac
import hashlib
from django.conf import settings


class WhatsAppService:
    """WhatsApp messaging via Meta Cloud API."""

    BASE_URL = 'https://graph.facebook.com/v18.0'

    def __init__(self):
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN

    def _headers(self):
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

    def send_template(
        self,
        to_phone: str,
        template_name: str,
        language: str = 'es_MX',
        components: list = None
    ) -> dict:
        """Send a pre-approved template message."""

        # Format phone (remove + for WhatsApp)
        to_phone = to_phone.lstrip('+')

        payload = {
            'messaging_product': 'whatsapp',
            'to': to_phone,
            'type': 'template',
            'template': {
                'name': template_name,
                'language': {'code': language},
            }
        }

        if components:
            payload['template']['components'] = components

        url = f'{self.BASE_URL}/{self.phone_number_id}/messages'

        try:
            response = requests.post(
                url,
                headers=self._headers(),
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            return {
                'success': True,
                'message_id': data['messages'][0]['id'],
                'phone': to_phone
            }

        except requests.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'response': e.response.json() if e.response else None
            }

    def send_text(
        self,
        to_phone: str,
        body: str,
        preview_url: bool = True
    ) -> dict:
        """Send a text message (within 24-hour session window)."""

        to_phone = to_phone.lstrip('+')

        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': to_phone,
            'type': 'text',
            'text': {
                'body': body,
                'preview_url': preview_url
            }
        }

        url = f'{self.BASE_URL}/{self.phone_number_id}/messages'

        try:
            response = requests.post(
                url,
                headers=self._headers(),
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            return {
                'success': True,
                'message_id': data['messages'][0]['id']
            }

        except requests.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }

    def send_media(
        self,
        to_phone: str,
        media_type: str,  # 'image', 'document', 'audio', 'video'
        media_url: str = None,
        media_id: str = None,
        caption: str = None,
        filename: str = None
    ) -> dict:
        """Send a media message."""

        to_phone = to_phone.lstrip('+')

        media_object = {}
        if media_url:
            media_object['link'] = media_url
        elif media_id:
            media_object['id'] = media_id

        if caption:
            media_object['caption'] = caption
        if filename and media_type == 'document':
            media_object['filename'] = filename

        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': to_phone,
            'type': media_type,
            media_type: media_object
        }

        url = f'{self.BASE_URL}/{self.phone_number_id}/messages'

        try:
            response = requests.post(
                url,
                headers=self._headers(),
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            return {
                'success': True,
                'message_id': data['messages'][0]['id']
            }

        except requests.RequestException as e:
            return {'success': False, 'error': str(e)}

    def send_interactive(
        self,
        to_phone: str,
        interactive_type: str,  # 'button', 'list'
        body: str,
        buttons: list = None,
        sections: list = None,
        header: dict = None,
        footer: str = None
    ) -> dict:
        """Send interactive message with buttons or list."""

        to_phone = to_phone.lstrip('+')

        interactive = {
            'type': interactive_type,
            'body': {'text': body}
        }

        if header:
            interactive['header'] = header
        if footer:
            interactive['footer'] = {'text': footer}

        if interactive_type == 'button' and buttons:
            interactive['action'] = {
                'buttons': [
                    {
                        'type': 'reply',
                        'reply': {'id': btn['id'], 'title': btn['title'][:20]}
                    }
                    for btn in buttons[:3]  # Max 3 buttons
                ]
            }
        elif interactive_type == 'list' and sections:
            interactive['action'] = {
                'button': 'Ver opciones',
                'sections': sections
            }

        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': to_phone,
            'type': 'interactive',
            'interactive': interactive
        }

        url = f'{self.BASE_URL}/{self.phone_number_id}/messages'

        try:
            response = requests.post(
                url,
                headers=self._headers(),
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            return {
                'success': True,
                'message_id': data['messages'][0]['id']
            }

        except requests.RequestException as e:
            return {'success': False, 'error': str(e)}

    def mark_as_read(self, message_id: str) -> bool:
        """Mark message as read."""

        payload = {
            'messaging_product': 'whatsapp',
            'status': 'read',
            'message_id': message_id
        }

        url = f'{self.BASE_URL}/{self.phone_number_id}/messages'

        try:
            response = requests.post(
                url,
                headers=self._headers(),
                json=payload
            )
            return response.ok
        except:
            return False

    def upload_media(self, file_path: str, mime_type: str) -> str:
        """Upload media file and return media ID."""

        url = f'{self.BASE_URL}/{self.phone_number_id}/media'

        with open(file_path, 'rb') as f:
            response = requests.post(
                url,
                headers={'Authorization': f'Bearer {self.access_token}'},
                files={'file': (file_path, f, mime_type)},
                data={'messaging_product': 'whatsapp'}
            )

        if response.ok:
            return response.json()['id']
        return None


class WhatsAppWebhookHandler:
    """Handle WhatsApp Cloud API webhooks."""

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature."""

        expected = hmac.new(
            settings.WHATSAPP_APP_SECRET.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(f'sha256={expected}', signature)

    def process_webhook(self, data: dict):
        """Process incoming webhook."""

        entry = data.get('entry', [{}])[0]
        changes = entry.get('changes', [{}])[0]
        value = changes.get('value', {})

        # Process messages
        messages = value.get('messages', [])
        for message in messages:
            self._process_message(message, value.get('contacts', []))

        # Process status updates
        statuses = value.get('statuses', [])
        for status in statuses:
            self._process_status(status)

    def _process_message(self, message: dict, contacts: list):
        """Process inbound message."""
        from apps.communications.models import Conversation, Message, Channel

        from_phone = message['from']
        message_id = message['id']
        message_type = message['type']
        timestamp = message['timestamp']

        # Get contact name
        contact_name = None
        for contact in contacts:
            if contact['wa_id'] == from_phone:
                contact_name = contact.get('profile', {}).get('name')
                break

        # Get content based on type
        body = ''
        attachments = []

        if message_type == 'text':
            body = message['text']['body']
        elif message_type == 'image':
            attachments.append({
                'type': 'image',
                'id': message['image']['id'],
                'caption': message['image'].get('caption', '')
            })
            body = message['image'].get('caption', '[Imagen]')
        elif message_type == 'document':
            attachments.append({
                'type': 'document',
                'id': message['document']['id'],
                'filename': message['document'].get('filename', ''),
                'caption': message['document'].get('caption', '')
            })
            body = f"[Documento: {message['document'].get('filename', '')}]"
        elif message_type == 'audio':
            attachments.append({
                'type': 'audio',
                'id': message['audio']['id']
            })
            body = '[Audio]'
        elif message_type == 'interactive':
            # Button or list reply
            interactive = message['interactive']
            if 'button_reply' in interactive:
                body = interactive['button_reply']['title']
            elif 'list_reply' in interactive:
                body = interactive['list_reply']['title']

        # Find or create conversation
        channel = Channel.objects.get(channel_type='whatsapp')
        from django.contrib.auth import get_user_model
        User = get_user_model()

        user = User.objects.filter(
            Q(profile__whatsapp=from_phone) |
            Q(profile__phone=from_phone)
        ).first()

        conversation = Conversation.objects.filter(
            owner=user,
            status__in=['active', 'pending']
        ).first() if user else None

        if not conversation:
            conversation = Conversation.objects.create(
                owner=user,
                subject=f'WhatsApp: {contact_name or from_phone}',
                status='pending'
            )

        # Create message
        msg = Message.objects.create(
            conversation=conversation,
            channel=channel,
            direction='inbound',
            to_contact=settings.WHATSAPP_PHONE_NUMBER_ID,
            body=body,
            external_id=message_id,
            status='delivered',
            attachments=attachments,
            metadata={'contact_name': contact_name, 'type': message_type}
        )

        # Update conversation
        conversation.last_message_at = timezone.now()
        conversation.last_customer_message_at = timezone.now()
        conversation.unread_count += 1
        conversation.save()

        # Mark as read
        WhatsAppService().mark_as_read(message_id)

    def _process_status(self, status: dict):
        """Process message status update."""
        from apps.communications.models import Message

        message_id = status['id']
        status_type = status['status']

        status_map = {
            'sent': 'sent',
            'delivered': 'delivered',
            'read': 'read',
            'failed': 'failed'
        }

        message = Message.objects.filter(external_id=message_id).first()
        if message:
            message.status = status_map.get(status_type, 'pending')
            if status_type == 'delivered':
                message.delivered_at = timezone.now()
            elif status_type == 'read':
                message.read_at = timezone.now()
            elif status_type == 'failed':
                message.failed_at = timezone.now()
                message.error_message = status.get('errors', [{}])[0].get('title', '')
            message.save()
```

#### Webhook View
```python
import json
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


@method_decorator(csrf_exempt, name='dispatch')
class WhatsAppWebhookView(View):
    """Handle WhatsApp Cloud API webhooks."""

    def get(self, request):
        """Webhook verification."""
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')

        if mode == 'subscribe' and token == settings.WHATSAPP_VERIFY_TOKEN:
            return HttpResponse(challenge)

        return HttpResponse('Forbidden', status=403)

    def post(self, request):
        """Process incoming webhook."""
        # Verify signature
        signature = request.headers.get('X-Hub-Signature-256', '')
        handler = WhatsAppWebhookHandler()

        if not handler.verify_signature(request.body, signature):
            return HttpResponse('Invalid signature', status=403)

        try:
            data = json.loads(request.body)
            handler.process_webhook(data)
            return HttpResponse('OK')
        except Exception as e:
            logger.error(f"WhatsApp webhook error: {e}")
            return HttpResponse('Error', status=500)
```

### Pre-Approved Templates Required
```
Template Name: appointment_reminder
Language: es_MX
Body: "Hola {{1}}, te recordamos tu cita para {{2}} el {{3}} a las {{4}}. Responde SI para confirmar o llámanos al +52 998 316 2438 para reagendar."

Template Name: vaccination_reminder
Language: es_MX
Body: "Hola {{1}}, {{2}} tiene vacunas pendientes. Agenda tu cita en petfriendlyvet.com o responde a este mensaje."

Template Name: order_ready
Language: es_MX
Body: "Hola {{1}}, tu pedido #{{2}} está listo para recoger en Pet-Friendly. Horario: Mar-Dom 9am-8pm."
```

### Test Cases
- [ ] Template message sends
- [ ] Text message sends (session)
- [ ] Media message sends
- [ ] Interactive buttons work
- [ ] Inbound message creates conversation
- [ ] Status updates work
- [ ] Signature verification works

### Definition of Done
- [ ] WhatsApp API integration complete
- [ ] Webhook handlers working
- [ ] Templates configured
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-044: Communication Channel Models

### Environment Variables
```
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_BUSINESS_ACCOUNT_ID=
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_VERIFY_TOKEN=
WHATSAPP_APP_SECRET=
```
