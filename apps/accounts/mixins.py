"""Permission mixins for class-based views."""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class ModulePermissionMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to check module-level permissions for class-based views.

    Usage:
        class StaffListView(ModulePermissionMixin, ListView):
            required_module = 'practice'
            required_action = 'view'
            model = StaffProfile

    Attributes:
        required_module: The module name (e.g., 'practice', 'accounting')
        required_action: The action name (e.g., 'view', 'manage')
    """

    required_module = None
    required_action = 'view'

    def test_func(self):
        """Check if user has the required module permission."""
        if not self.required_module:
            return True
        return self.request.user.has_module_permission(
            self.required_module,
            self.required_action
        )


class HierarchyPermissionMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to check if user can manage the target user (hierarchy check).

    Usage:
        class StaffEditView(HierarchyPermissionMixin, UpdateView):
            model = StaffProfile

            def get_target_user(self):
                return self.get_object().user

    Override get_target_user() to return the user being managed.
    """

    def get_target_user(self):
        """Override to return the user being managed.

        Returns:
            User: The user that this action targets.
        """
        raise NotImplementedError(
            "Subclasses must implement get_target_user()"
        )

    def test_func(self):
        """Check if requesting user can manage the target user."""
        target = self.get_target_user()
        if target is None:
            return True
        return self.request.user.can_manage_user(target)


class CombinedPermissionMixin(ModulePermissionMixin, HierarchyPermissionMixin):
    """Mixin that combines module permission and hierarchy checks.

    Usage:
        class StaffEditView(CombinedPermissionMixin, UpdateView):
            required_module = 'practice'
            required_action = 'edit'
            model = StaffProfile

            def get_target_user(self):
                return self.get_object().user
    """

    def test_func(self):
        """Check both module permission and hierarchy."""
        # First check module permission
        if self.required_module:
            if not self.request.user.has_module_permission(
                self.required_module,
                self.required_action
            ):
                return False

        # Then check hierarchy if target user exists
        try:
            target = self.get_target_user()
            if target is not None:
                return self.request.user.can_manage_user(target)
        except NotImplementedError:
            # No target user specified, just check module permission
            pass

        return True
