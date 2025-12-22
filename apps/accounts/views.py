"""Account views."""
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class LoginView(auth_views.LoginView):
    """Custom login view."""

    template_name = 'accounts/login.html'


class LogoutView(auth_views.LogoutView):
    """Custom logout view."""

    pass


class ProfileView(LoginRequiredMixin, TemplateView):
    """User profile view - requires authentication."""

    template_name = 'accounts/profile.html'
