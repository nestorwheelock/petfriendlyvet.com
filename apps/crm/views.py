"""Views for CRM functionality."""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin requiring user to be staff."""

    def test_func(self):
        return self.request.user.is_staff


class CRMDashboardView(StaffRequiredMixin, TemplateView):
    """CRM dashboard for customer management."""

    template_name = 'crm/dashboard.html'
