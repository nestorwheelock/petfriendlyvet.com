"""Mixins for superadmin access control."""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class SuperuserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin requiring user to be a superuser."""

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("Superuser access required.")
        return super().handle_no_permission()
