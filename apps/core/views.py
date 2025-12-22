"""Core views for Pet-Friendly Vet."""
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import TemplateView


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

    def post(self, request):
        """Handle contact form submission."""
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        if not all([name, email, subject, message]):
            messages.error(request, _('Por favor completa todos los campos requeridos.'))
            return render(request, self.template_name)

        messages.success(
            request,
            _('Gracias por tu mensaje. Te contactaremos pronto.')
        )
        return redirect('core:contact')


def health_check(request):
    """Health check endpoint for load balancers."""
    return render(request, 'core/health.html', {'status': 'ok'})
