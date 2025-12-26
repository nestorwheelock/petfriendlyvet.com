"""Core views for Pet-Friendly Vet."""
import logging
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import TemplateView

from .models import ContactSubmission

logger = logging.getLogger(__name__)


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin that requires user to be staff."""

    def test_func(self):
        return self.request.user.is_staff


class StaffHubView(StaffRequiredMixin, TemplateView):
    """Staff hub dashboard - central access point for all staff modules."""

    template_name = 'staff/hub.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get summary stats
        stats = self._get_summary_stats()
        context['stats'] = stats

        # Get recent activity
        context['recent_activity'] = self._get_recent_activity()

        return context

    def _get_summary_stats(self):
        """Get summary statistics across all modules."""
        from apps.appointments.models import Appointment
        from apps.store.models import Order
        from apps.pets.models import Pet

        today = timezone.now().date()
        stats = {}

        try:
            stats['appointments_today'] = Appointment.objects.filter(
                scheduled_start__date=today
            ).count()
        except Exception:
            stats['appointments_today'] = 0

        try:
            stats['pending_orders'] = Order.objects.filter(
                status__in=['pending', 'processing']
            ).count()
        except Exception:
            stats['pending_orders'] = 0

        try:
            stats['total_pets'] = Pet.objects.count()
        except Exception:
            stats['total_pets'] = 0

        return stats

    def _get_recent_activity(self):
        """Get recent activity across the system."""
        from apps.audit.models import AuditLog

        try:
            return AuditLog.objects.select_related('user').order_by(
                '-created_at'
            )[:10]
        except Exception:
            return []


class PortalDashboardView(LoginRequiredMixin, TemplateView):
    """Customer portal dashboard - personalized customer homepage."""

    template_name = 'portal/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get user's pets
        context['pets'] = self._get_user_pets(user)

        # Get upcoming appointments
        context['upcoming_appointments'] = self._get_upcoming_appointments(user)

        # Get recent orders
        context['recent_orders'] = self._get_recent_orders(user)

        # Get loyalty account
        context['loyalty_account'] = self._get_loyalty_account(user)

        return context

    def _get_user_pets(self, user):
        """Get user's pets."""
        from apps.pets.models import Pet

        try:
            return Pet.objects.filter(owner=user)
        except Exception:
            return Pet.objects.none()

    def _get_upcoming_appointments(self, user):
        """Get user's upcoming appointments."""
        from apps.appointments.models import Appointment

        try:
            now = timezone.now()
            return Appointment.objects.filter(
                owner=user,
                scheduled_start__gte=now
            ).order_by('scheduled_start')[:5]
        except Exception:
            return []

    def _get_recent_orders(self, user):
        """Get user's recent orders."""
        from apps.store.models import Order

        try:
            return Order.objects.filter(user=user).order_by('-created_at')[:5]
        except Exception:
            return []

    def _get_loyalty_account(self, user):
        """Get user's loyalty account if exists."""
        from apps.loyalty.models import LoyaltyAccount

        try:
            return LoyaltyAccount.objects.filter(user=user).first()
        except Exception:
            return None


class HomeView(TemplateView):
    """Homepage view."""

    template_name = 'core/home.html'


class AboutView(TemplateView):
    """About page view."""

    template_name = 'core/about.html'


class ServicesView(TemplateView):
    """Services page view."""

    template_name = 'core/services.html'


class ContactView(View):
    """Contact page view with form handling."""

    template_name = 'core/contact.html'

    def get(self, request):
        """Display the contact form."""
        return render(request, self.template_name)

    def get_client_ip(self, request):
        """Extract client IP from request, handling proxy headers."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    def post(self, request):
        """Handle contact form submission."""
        # Check honeypot field (spam prevention)
        # If 'website' field is filled, it's likely a bot
        honeypot = request.POST.get('website', '').strip()
        if honeypot:
            # Silently redirect (don't reveal spam detection)
            logger.warning("Honeypot triggered from IP: %s", self.get_client_ip(request))
            messages.success(
                request,
                _('Gracias por tu mensaje. Te contactaremos pronto.')
            )
            return redirect('core:contact')

        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        subject = request.POST.get('subject', '').strip()
        message_text = request.POST.get('message', '').strip()

        if not all([name, email, subject, message_text]):
            messages.error(request, _('Por favor completa todos los campos requeridos.'))
            return render(request, self.template_name)

        # Save to database
        submission = ContactSubmission.objects.create(
            name=name,
            email=email,
            phone=phone,
            subject=subject,
            message=message_text,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        )

        logger.info("Contact form submission #%s from %s (%s)",
                    submission.id, email, subject)

        # Send email notification to clinic
        try:
            send_mail(
                subject=f'[Pet-Friendly] Nuevo mensaje de contacto: {subject}',
                message=f"""
Nuevo mensaje de contacto recibido:

Nombre: {name}
Email: {email}
Teléfono: {phone or 'No proporcionado'}
Asunto: {subject}

Mensaje:
{message_text}

---
Enviado desde el formulario de contacto de Pet-Friendly Veterinary Clinic
IP: {submission.ip_address}
""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.DEFAULT_FROM_EMAIL],
                fail_silently=True,
            )
        except Exception as e:
            logger.exception("Failed to send contact notification email")

        messages.success(
            request,
            _('Gracias por tu mensaje. Te contactaremos pronto.')
        )
        return redirect('core:contact')


def health_check(request):
    """Health check endpoint for load balancers."""
    return render(request, 'core/health.html', {'status': 'ok'})


def csrf_failure(request, reason=''):
    """Custom CSRF failure view with friendly error page."""
    return render(request, '403_csrf.html', {'reason': reason}, status=403)
