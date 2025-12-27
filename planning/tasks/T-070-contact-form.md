# T-070: Fix Contact Form

> **REQUIRED READING:** Before implementation, review [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)

> **Parent Story:** [S-027 Security Hardening](../stories/S-027-security-hardening.md)

**Task Type:** Functional Fix + Security Enhancement
**Priority:** MEDIUM
**Estimate:** 2 hours
**Status:** PENDING

---

## Objective

Make the contact form actually send email notifications when submitted, add a confirmation email to users, implement spam prevention with honeypot fields, and log all submissions for audit trail.

---

## Background

The current contact form collects user information but doesn't:
- Send email notifications to the clinic
- Send confirmation emails to users
- Store submissions for record-keeping
- Prevent spam submissions

This is both a functional issue and a security/auditing gap.

---

## Implementation

### Step 1: Create Contact Submission Model

```python
# apps/core/models.py

from django.db import models
from django.utils import timezone


class ContactSubmission(models.Model):
    """
    Store all contact form submissions for audit trail.
    """
    STATUS_CHOICES = [
        ('new', 'New'),
        ('read', 'Read'),
        ('replied', 'Replied'),
        ('spam', 'Spam'),
        ('archived', 'Archived'),
    ]

    # Submission details
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    subject = models.CharField(max_length=300)
    message = models.TextField()

    # Metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    language = models.CharField(max_length=10, default='es')

    # Spam detection
    honeypot_filled = models.BooleanField(default=False)
    is_spam = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    replied_at = models.DateTimeField(null=True, blank=True)

    # Response tracking
    notification_sent = models.BooleanField(default=False)
    confirmation_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Submission'
        verbose_name_plural = 'Contact Submissions'

    def __str__(self):
        return f"{self.name} - {self.subject[:50]}"

    def mark_read(self):
        if not self.read_at:
            self.read_at = timezone.now()
            self.status = 'read'
            self.save(update_fields=['read_at', 'status'])

    def mark_replied(self):
        self.replied_at = timezone.now()
        self.status = 'replied'
        self.save(update_fields=['replied_at', 'status'])
```

### Step 2: Create Contact Form with Honeypot

```python
# apps/core/forms.py

from django import forms
from django.core.exceptions import ValidationError
from .models import ContactSubmission


class ContactForm(forms.ModelForm):
    """
    Contact form with honeypot spam prevention.
    """
    # Honeypot field - should remain empty
    # Named innocuously to trick bots
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'hidden-field',  # Hidden via CSS
            'tabindex': '-1',
            'autocomplete': 'off',
        })
    )

    class Meta:
        model = ContactSubmission
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your name',
                'required': True,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your@email.com',
                'required': True,
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+52 998 XXX XXXX',
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'How can we help?',
                'required': True,
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Your message...',
                'rows': 5,
                'required': True,
            }),
        }

    def clean_website(self):
        """Honeypot validation - should be empty."""
        website = self.cleaned_data.get('website', '')
        if website:
            # Bot filled the honeypot
            raise ValidationError('Invalid submission detected.')
        return website

    def clean_message(self):
        """Basic message validation."""
        message = self.cleaned_data.get('message', '')
        if len(message) < 10:
            raise ValidationError('Please provide more details in your message.')
        if len(message) > 5000:
            raise ValidationError('Message is too long. Please keep it under 5000 characters.')
        return message
```

### Step 3: Create Email Templates

```html
<!-- templates/emails/contact_notification.html -->
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>New Contact Form Submission</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2c5282;">New Contact Form Submission</h2>

        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>Name:</strong></td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{{ submission.name }}</td>
            </tr>
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>Email:</strong></td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">
                    <a href="mailto:{{ submission.email }}">{{ submission.email }}</a>
                </td>
            </tr>
            {% if submission.phone %}
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>Phone:</strong></td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">
                    <a href="tel:{{ submission.phone }}">{{ submission.phone }}</a>
                </td>
            </tr>
            {% endif %}
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>Subject:</strong></td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{{ submission.subject }}</td>
            </tr>
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>Received:</strong></td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{{ submission.created_at|date:"F j, Y g:i A" }}</td>
            </tr>
        </table>

        <h3 style="margin-top: 20px;">Message:</h3>
        <div style="background: #f7fafc; padding: 15px; border-radius: 5px;">
            {{ submission.message|linebreaks }}
        </div>

        <p style="margin-top: 20px; color: #718096; font-size: 14px;">
            Reply directly to this email to respond to the customer.
        </p>
    </div>
</body>
</html>
```

```html
<!-- templates/emails/contact_confirmation.html -->
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{% if lang == 'es' %}Recibimos tu mensaje{% else %}We received your message{% endif %}</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <img src="{{ site_url }}/static/images/logo.png" alt="Pet-Friendly Veterinary" style="max-width: 200px;">

        {% if lang == 'es' %}
        <h2 style="color: #2c5282;">¡Gracias por contactarnos!</h2>
        <p>Hola {{ submission.name }},</p>
        <p>Hemos recibido tu mensaje y te responderemos lo antes posible, generalmente dentro de 24 horas.</p>

        <h3>Tu mensaje:</h3>
        <div style="background: #f7fafc; padding: 15px; border-radius: 5px;">
            <strong>Asunto:</strong> {{ submission.subject }}<br><br>
            {{ submission.message|linebreaks }}
        </div>

        <p style="margin-top: 20px;">
            Si tienes una emergencia, por favor llámanos directamente:<br>
            <strong>📞 +52 998 316 2438</strong>
        </p>

        <p>Saludos,<br>
        <strong>Dr. Pablo Rojo Mendoza</strong><br>
        Pet-Friendly Veterinary Clinic</p>

        {% else %}
        <h2 style="color: #2c5282;">Thank you for contacting us!</h2>
        <p>Hello {{ submission.name }},</p>
        <p>We have received your message and will get back to you as soon as possible, typically within 24 hours.</p>

        <h3>Your message:</h3>
        <div style="background: #f7fafc; padding: 15px; border-radius: 5px;">
            <strong>Subject:</strong> {{ submission.subject }}<br><br>
            {{ submission.message|linebreaks }}
        </div>

        <p style="margin-top: 20px;">
            If you have an emergency, please call us directly:<br>
            <strong>📞 +52 998 316 2438</strong>
        </p>

        <p>Best regards,<br>
        <strong>Dr. Pablo Rojo Mendoza</strong><br>
        Pet-Friendly Veterinary Clinic</p>
        {% endif %}
    </div>
</body>
</html>
```

### Step 4: Create Contact View

```python
# apps/core/views.py

import logging
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

from .forms import ContactForm
from .models import ContactSubmission

logger = logging.getLogger(__name__)


@require_POST
@csrf_protect
def contact_submit(request):
    """
    Handle contact form submission.

    - Validates form data
    - Detects spam via honeypot
    - Stores submission for audit trail
    - Sends notification email to clinic
    - Sends confirmation email to user
    """
    form = ContactForm(request.POST)

    if form.is_valid():
        # Check honeypot
        honeypot_filled = bool(request.POST.get('website', ''))

        # Create submission record
        submission = form.save(commit=False)
        submission.ip_address = get_client_ip(request)
        submission.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        submission.language = request.LANGUAGE_CODE or 'es'
        submission.honeypot_filled = honeypot_filled
        submission.is_spam = honeypot_filled
        submission.save()

        if honeypot_filled:
            # Log spam but don't send emails
            logger.warning(
                "Spam contact submission detected",
                extra={
                    'ip': submission.ip_address,
                    'email': submission.email,
                }
            )
            # Return success to not tip off bots
            return JsonResponse({'status': 'success'})

        # Send notification to clinic
        try:
            send_notification_email(submission)
            submission.notification_sent = True
        except Exception as e:
            logger.exception("Failed to send contact notification")

        # Send confirmation to user
        try:
            send_confirmation_email(submission)
            submission.confirmation_sent = True
        except Exception as e:
            logger.exception("Failed to send contact confirmation")

        submission.save(update_fields=['notification_sent', 'confirmation_sent'])

        logger.info(
            "Contact form submission processed",
            extra={
                'submission_id': submission.id,
                'email': submission.email,
            }
        )

        return JsonResponse({
            'status': 'success',
            'message': 'Thank you! We will respond soon.' if submission.language == 'en'
                      else '¡Gracias! Te responderemos pronto.'
        })

    else:
        # Form validation failed
        return JsonResponse({
            'status': 'error',
            'errors': form.errors,
        }, status=400)


def send_notification_email(submission):
    """Send notification email to clinic."""
    html_content = render_to_string('emails/contact_notification.html', {
        'submission': submission,
    })
    text_content = strip_tags(html_content)

    msg = EmailMultiAlternatives(
        subject=f"[Contact Form] {submission.subject}",
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.CONTACT_EMAIL],
        reply_to=[submission.email],
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def send_confirmation_email(submission):
    """Send confirmation email to user."""
    html_content = render_to_string('emails/contact_confirmation.html', {
        'submission': submission,
        'lang': submission.language,
        'site_url': settings.SITE_URL,
    })
    text_content = strip_tags(html_content)

    subject = (
        "Recibimos tu mensaje - Pet-Friendly Veterinary"
        if submission.language == 'es'
        else "We received your message - Pet-Friendly Veterinary"
    )

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[submission.email],
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def get_client_ip(request):
    """Extract client IP from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')
```

### Step 5: Add Settings

```python
# config/settings/base.py

# Contact form settings
CONTACT_EMAIL = env('CONTACT_EMAIL', default='pablorojomendoza@gmail.com')
SITE_URL = env('SITE_URL', default='https://petfriendlyvet.com')
```

### Step 6: Add URL

```python
# apps/core/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('contact/submit/', views.contact_submit, name='contact_submit'),
]
```

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `apps/core/models.py` | Add ContactSubmission model |
| `apps/core/forms.py` | Create ContactForm |
| `apps/core/views.py` | Add contact_submit view |
| `apps/core/urls.py` | Add URL route |
| `templates/emails/contact_notification.html` | Create |
| `templates/emails/contact_confirmation.html` | Create |
| `config/settings/base.py` | Add contact settings |

---

## Tests Required

```python
# tests/test_contact_form.py

import pytest
from django.core import mail
from apps.core.models import ContactSubmission


@pytest.mark.django_db
class TestContactForm:
    """Test contact form functionality."""

    def test_valid_submission_creates_record(self, client):
        """Valid submission should create database record."""
        response = client.post('/contact/submit/', {
            'name': 'Test User',
            'email': 'test@example.com',
            'subject': 'Test inquiry',
            'message': 'This is a test message for the contact form.',
        })

        assert response.status_code == 200
        assert ContactSubmission.objects.count() == 1

        submission = ContactSubmission.objects.first()
        assert submission.name == 'Test User'
        assert submission.email == 'test@example.com'

    def test_submission_sends_notification(self, client, settings):
        """Submission should send notification email."""
        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

        client.post('/contact/submit/', {
            'name': 'Test User',
            'email': 'test@example.com',
            'subject': 'Test inquiry',
            'message': 'This is a test message for the contact form.',
        })

        assert len(mail.outbox) == 2  # Notification + confirmation

    def test_honeypot_blocks_spam(self, client):
        """Honeypot field should block spam."""
        response = client.post('/contact/submit/', {
            'name': 'Spam Bot',
            'email': 'spam@example.com',
            'subject': 'Buy our stuff',
            'message': 'Click here for free money.',
            'website': 'http://spam.com',  # Honeypot filled
        })

        assert response.status_code == 200  # Don't tip off bots

        submission = ContactSubmission.objects.first()
        assert submission.is_spam is True
        assert submission.notification_sent is False

    def test_missing_required_fields(self, client):
        """Missing required fields should return error."""
        response = client.post('/contact/submit/', {
            'name': '',
            'email': 'test@example.com',
            'subject': 'Test',
            'message': 'Test message here.',
        })

        assert response.status_code == 400
        data = response.json()
        assert 'errors' in data

    def test_invalid_email(self, client):
        """Invalid email should return error."""
        response = client.post('/contact/submit/', {
            'name': 'Test User',
            'email': 'not-an-email',
            'subject': 'Test',
            'message': 'Test message here.',
        })

        assert response.status_code == 400
```

---

## Acceptance Criteria

- [ ] Contact submissions stored in database
- [ ] Notification email sent to clinic
- [ ] Confirmation email sent to user
- [ ] Honeypot prevents spam submissions
- [ ] All submissions logged for audit
- [ ] CSRF protection enabled
- [ ] Tests cover all scenarios

---

## Definition of Done

- [ ] ContactSubmission model created with migration
- [ ] ContactForm with honeypot validation
- [ ] Email templates created (notification + confirmation)
- [ ] View handles submissions with proper error handling
- [ ] All tests pass
- [ ] Manual testing confirms emails sent
- [ ] Admin can view submissions in Django admin

---

*Created: December 23, 2025*
