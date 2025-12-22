# T-045: Email Integration (Amazon SES)

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement email sending via Amazon SES
**Related Story**: S-006
**Epoch**: 4
**Estimate**: 3 hours

### Constraints
**Allowed File Paths**: apps/communications/
**Forbidden Paths**: None

### Deliverables
- [ ] SES client configuration
- [ ] Email sending service
- [ ] HTML template rendering
- [ ] Bounce/complaint handling
- [ ] Delivery webhooks

### Implementation Details

#### SES Configuration
```python
# settings.py

# Amazon SES Configuration
AWS_SES_REGION_NAME = env('AWS_SES_REGION', default='us-east-1')
AWS_SES_ACCESS_KEY_ID = env('AWS_SES_ACCESS_KEY_ID')
AWS_SES_SECRET_ACCESS_KEY = env('AWS_SES_SECRET_ACCESS_KEY')

# Default sender
DEFAULT_FROM_EMAIL = 'Pet-Friendly <hola@petfriendlyvet.com>'
SERVER_EMAIL = 'sistema@petfriendlyvet.com'

# Email backend
EMAIL_BACKEND = 'django_ses.SESBackend'
```

#### Email Service
```python
import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from premailer import transform


class EmailService:
    """Email sending via Amazon SES."""

    def __init__(self):
        self.client = boto3.client(
            'ses',
            region_name=settings.AWS_SES_REGION_NAME,
            aws_access_key_id=settings.AWS_SES_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SES_SECRET_ACCESS_KEY
        )

    def send(
        self,
        to_email: str,
        subject: str,
        body_html: str = None,
        body_text: str = None,
        from_email: str = None,
        reply_to: str = None,
        attachments: list = None,
        tags: dict = None
    ) -> dict:
        """Send an email."""

        from_email = from_email or settings.DEFAULT_FROM_EMAIL

        # Prepare body
        if body_html and not body_text:
            body_text = strip_tags(body_html)

        # Inline CSS for email clients
        if body_html:
            body_html = transform(body_html)

        message = {
            'Subject': {'Data': subject, 'Charset': 'UTF-8'},
            'Body': {}
        }

        if body_text:
            message['Body']['Text'] = {'Data': body_text, 'Charset': 'UTF-8'}
        if body_html:
            message['Body']['Html'] = {'Data': body_html, 'Charset': 'UTF-8'}

        try:
            response = self.client.send_email(
                Source=from_email,
                Destination={'ToAddresses': [to_email]},
                Message=message,
                ReplyToAddresses=[reply_to] if reply_to else [],
                Tags=[
                    {'Name': k, 'Value': v}
                    for k, v in (tags or {}).items()
                ]
            )

            return {
                'success': True,
                'message_id': response['MessageId']
            }

        except ClientError as e:
            return {
                'success': False,
                'error': str(e)
            }

    def send_template(
        self,
        to_email: str,
        template_name: str,
        context: dict,
        from_email: str = None
    ) -> dict:
        """Send email using Django template."""

        # Render template
        html_content = render_to_string(
            f'emails/{template_name}.html',
            context
        )

        # Get subject from template or context
        subject = context.get('subject', 'Pet-Friendly Veterinaria')

        return self.send(
            to_email=to_email,
            subject=subject,
            body_html=html_content,
            from_email=from_email,
            tags={'template': template_name}
        )

    def send_bulk(
        self,
        recipients: list,
        template_name: str,
        default_context: dict
    ) -> list:
        """Send bulk emails with personalization."""

        results = []

        for recipient in recipients:
            # Merge contexts
            context = {**default_context, **recipient.get('context', {})}

            result = self.send_template(
                to_email=recipient['email'],
                template_name=template_name,
                context=context
            )
            result['email'] = recipient['email']
            results.append(result)

        return results


# Webhook handler for bounces/complaints
class SESWebhookHandler:
    """Handle SES notifications via SNS."""

    def process_notification(self, notification: dict):
        """Process bounce/complaint notification."""

        notif_type = notification.get('notificationType')

        if notif_type == 'Bounce':
            self._handle_bounce(notification['bounce'])
        elif notif_type == 'Complaint':
            self._handle_complaint(notification['complaint'])
        elif notif_type == 'Delivery':
            self._handle_delivery(notification['delivery'])

    def _handle_bounce(self, bounce: dict):
        """Handle bounced email."""
        from apps.communications.models import Message, ContactPreference

        bounce_type = bounce['bounceType']
        recipients = bounce['bouncedRecipients']

        for recipient in recipients:
            email = recipient['emailAddress']

            # Update message status
            Message.objects.filter(
                to_contact=email,
                status='sent'
            ).update(status='failed', error_message=f'Bounce: {bounce_type}')

            # Hard bounce - disable email
            if bounce_type == 'Permanent':
                ContactPreference.objects.filter(email=email).update(
                    email_valid=False
                )

    def _handle_complaint(self, complaint: dict):
        """Handle spam complaint."""
        from apps.communications.models import ContactPreference

        for recipient in complaint['complainedRecipients']:
            email = recipient['emailAddress']

            # Unsubscribe from marketing
            ContactPreference.objects.filter(email=email).update(
                marketing=False,
                promotions=False
            )

    def _handle_delivery(self, delivery: dict):
        """Handle successful delivery."""
        from apps.communications.models import Message

        for recipient in delivery['recipients']:
            Message.objects.filter(
                to_contact=recipient,
                status='sent'
            ).update(
                status='delivered',
                delivered_at=timezone.now()
            )
```

#### SNS Webhook View
```python
import json
import logging
from django.http import HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class SESWebhookView(View):
    """Receive SES notifications via SNS."""

    def post(self, request):
        try:
            body = json.loads(request.body)

            # Handle subscription confirmation
            if body.get('Type') == 'SubscriptionConfirmation':
                # Auto-confirm subscription
                import requests
                requests.get(body['SubscribeURL'])
                return HttpResponse('Confirmed')

            # Handle notification
            if body.get('Type') == 'Notification':
                message = json.loads(body['Message'])
                handler = SESWebhookHandler()
                handler.process_notification(message)

            return HttpResponse('OK')

        except Exception as e:
            logger.error(f"SES webhook error: {e}")
            return HttpResponse('Error', status=400)
```

#### Email Templates Base
```html
<!-- templates/emails/base.html -->
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ subject }}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            text-align: center;
            padding: 20px 0;
            border-bottom: 2px solid #4CAF50;
        }
        .logo {
            max-width: 200px;
        }
        .content {
            padding: 30px 0;
        }
        .footer {
            text-align: center;
            padding: 20px 0;
            font-size: 12px;
            color: #666;
            border-top: 1px solid #eee;
        }
        .button {
            display: inline-block;
            background: #4CAF50;
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 4px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="header">
        <img src="https://petfriendlyvet.com/logo.png" alt="Pet-Friendly" class="logo">
    </div>

    <div class="content">
        {% block content %}{% endblock %}
    </div>

    <div class="footer">
        <p>Pet-Friendly Veterinaria</p>
        <p>Puerto Morelos, Quintana Roo, México</p>
        <p>
            <a href="https://petfriendlyvet.com">Sitio web</a> |
            <a href="tel:+529983162438">+52 998 316 2438</a>
        </p>
        <p style="margin-top: 10px;">
            <a href="{{ unsubscribe_url }}">Cancelar suscripción</a>
        </p>
    </div>
</body>
</html>
```

### Test Cases
- [ ] Email sends successfully
- [ ] Template rendering works
- [ ] HTML is inlined correctly
- [ ] Bounce handling works
- [ ] Complaint handling unsubscribes
- [ ] Delivery updates message status
- [ ] Bulk sending works

### Definition of Done
- [ ] SES integration complete
- [ ] Webhook handlers working
- [ ] Templates rendering
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-044: Communication Channel Models

### Environment Variables
```
AWS_SES_REGION=us-east-1
AWS_SES_ACCESS_KEY_ID=
AWS_SES_SECRET_ACCESS_KEY=
```
