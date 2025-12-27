"""Views for superadmin control panel."""

from collections import defaultdict

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView

from apps.audit.models import AuditLog
from apps.core.models import ModuleConfig, FeatureFlag
from apps.practice.models import ClinicSettings

from .forms import UserForm, UserCreateForm, ClinicSettingsForm
from .mixins import SuperuserRequiredMixin

User = get_user_model()


class SuperadminDashboardView(SuperuserRequiredMixin, TemplateView):
    """Main superadmin dashboard with system overview."""

    template_name = 'superadmin/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # User statistics
        context['total_users'] = User.objects.count()
        context['staff_users'] = User.objects.filter(is_staff=True).count()
        context['superusers'] = User.objects.filter(is_superuser=True).count()
        context['active_users'] = User.objects.filter(is_active=True).count()

        # User breakdown by role
        context['users_by_role'] = User.objects.values('role').annotate(
            count=Count('id')
        ).order_by('-count')

        # Recent audit logs
        context['recent_audit_logs'] = AuditLog.objects.select_related('user').order_by(
            '-created_at'
        )[:10]

        # Recent user registrations
        context['recent_users'] = User.objects.order_by('-date_joined')[:5]

        # System health checks
        context['system_health'] = self._get_system_health()

        return context

    def _get_system_health(self):
        """Get system health status."""
        from django.db import connection

        health = {
            'database': {'status': 'ok', 'message': 'Connected'},
            'cache': {'status': 'ok', 'message': 'Working'},
        }

        # Check database
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
        except Exception as e:
            health['database'] = {'status': 'error', 'message': str(e)}

        # Check cache
        try:
            from django.core.cache import cache
            cache.set('health_check', 'ok', 10)
            if cache.get('health_check') != 'ok':
                health['cache'] = {'status': 'warning', 'message': 'Not responding'}
        except Exception as e:
            health['cache'] = {'status': 'error', 'message': str(e)}

        return health


class UserListView(SuperuserRequiredMixin, ListView):
    """List all users with filtering options."""

    model = User
    template_name = 'superadmin/user_list.html'
    context_object_name = 'users'
    paginate_by = 25

    def get_queryset(self):
        queryset = User.objects.all().order_by('-date_joined')

        # Filter by role
        role = self.request.GET.get('role')
        if role:
            queryset = queryset.filter(role=role)

        # Filter by staff status
        is_staff = self.request.GET.get('is_staff')
        if is_staff == '1':
            queryset = queryset.filter(is_staff=True)
        elif is_staff == '0':
            queryset = queryset.filter(is_staff=False)

        # Filter by active status
        is_active = self.request.GET.get('is_active')
        if is_active == '1':
            queryset = queryset.filter(is_active=True)
        elif is_active == '0':
            queryset = queryset.filter(is_active=False)

        # Search by email or name
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['role_choices'] = User.ROLE_CHOICES
        context['current_filters'] = {
            'role': self.request.GET.get('role', ''),
            'is_staff': self.request.GET.get('is_staff', ''),
            'is_active': self.request.GET.get('is_active', ''),
            'search': self.request.GET.get('search', ''),
        }
        return context


class UserCreateView(SuperuserRequiredMixin, CreateView):
    """Create a new user."""

    model = User
    form_class = UserCreateForm
    template_name = 'superadmin/user_form.html'
    success_url = reverse_lazy('superadmin:user_list')

    def form_valid(self, form):
        messages.success(self.request, _('User created successfully.'))
        return super().form_valid(form)


class UserUpdateView(SuperuserRequiredMixin, UpdateView):
    """Edit an existing user."""

    model = User
    form_class = UserForm
    template_name = 'superadmin/user_form.html'
    success_url = reverse_lazy('superadmin:user_list')

    def form_valid(self, form):
        messages.success(self.request, _('User updated successfully.'))
        return super().form_valid(form)


class UserDeactivateView(SuperuserRequiredMixin, DeleteView):
    """Deactivate a user (soft delete)."""

    model = User
    template_name = 'superadmin/user_confirm_deactivate.html'
    success_url = reverse_lazy('superadmin:user_list')

    def form_valid(self, form):
        self.object = self.get_object()
        self.object.is_active = False
        self.object.save(update_fields=['is_active'])
        messages.success(self.request, _('User deactivated successfully.'))
        return HttpResponseRedirect(self.get_success_url())


class RoleListView(SuperuserRequiredMixin, ListView):
    """Display role list with hierarchy and user counts."""

    template_name = 'superadmin/role_list.html'
    context_object_name = 'roles'

    def get_queryset(self):
        from apps.accounts.models import Role
        return Role.objects.annotate(
            user_count=Count('user_roles')
        ).order_by('-hierarchy_level')


class RoleCreateView(SuperuserRequiredMixin, CreateView):
    """Create a new role."""

    template_name = 'superadmin/role_form.html'

    def get_form_class(self):
        from .forms import RoleForm
        return RoleForm

    def get_success_url(self):
        return reverse_lazy('superadmin:role_list')

    def form_valid(self, form):
        messages.success(self.request, _('Role created successfully.'))
        return super().form_valid(form)


class RoleUpdateView(SuperuserRequiredMixin, UpdateView):
    """Update an existing role."""

    template_name = 'superadmin/role_form.html'
    context_object_name = 'role'

    def get_queryset(self):
        from apps.accounts.models import Role
        return Role.objects.all()

    def get_form_class(self):
        from .forms import RoleForm
        return RoleForm

    def get_success_url(self):
        return reverse_lazy('superadmin:role_list')

    def form_valid(self, form):
        messages.success(self.request, _('Role updated successfully.'))
        return super().form_valid(form)


class RolePermissionsView(SuperuserRequiredMixin, TemplateView):
    """Manage permissions for a role using a permission matrix."""

    template_name = 'superadmin/role_permissions.html'

    # Define all modules and actions for the permission matrix
    MODULES = [
        ('practice', 'Practice Management'),
        ('accounting', 'Accounting'),
        ('inventory', 'Inventory'),
        ('pharmacy', 'Pharmacy'),
        ('appointments', 'Appointments'),
        ('delivery', 'Delivery'),
        ('crm', 'CRM'),
        ('reports', 'Reports'),
        ('billing', 'Billing'),
        ('superadmin', 'System Admin'),
        ('audit', 'Audit'),
        ('email_marketing', 'Email Marketing'),
        ('core', 'Core'),
    ]

    ACTIONS = [
        ('view', 'View'),
        ('create', 'Create'),
        ('edit', 'Edit'),
        ('delete', 'Delete'),
        ('approve', 'Approve'),
        ('manage', 'Manage'),
    ]

    def get_role(self):
        from apps.accounts.models import Role
        return get_object_or_404(Role, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        role = self.get_role()

        # Get current permissions for this role
        current_perms = set(
            role.group.permissions.values_list('codename', flat=True)
        )

        # Build permission matrix data
        matrix = []
        for module_code, module_name in self.MODULES:
            row = {
                'module_code': module_code,
                'module_name': module_name,
                'actions': []
            }
            for action_code, action_name in self.ACTIONS:
                codename = f'{module_code}.{action_code}'
                row['actions'].append({
                    'action_code': action_code,
                    'action_name': action_name,
                    'codename': codename,
                    'has_permission': codename in current_perms,
                })
            matrix.append(row)

        context['role'] = role
        context['matrix'] = matrix
        context['actions'] = self.ACTIONS
        return context

    def post(self, request, *args, **kwargs):
        from django.contrib.auth.models import Permission

        role = self.get_role()

        # Get selected permissions from form
        selected_perms = request.POST.getlist('permissions')

        # Get all module permissions (those with . in codename)
        all_module_perms = Permission.objects.filter(codename__contains='.')

        # Clear current module permissions and add selected ones
        role.group.permissions.remove(*all_module_perms)

        if selected_perms:
            perms_to_add = Permission.objects.filter(codename__in=selected_perms)
            role.group.permissions.add(*perms_to_add)

        messages.success(request, _('Permissions updated successfully.'))
        return HttpResponseRedirect(reverse_lazy('superadmin:role_list'))


class SettingsView(SuperuserRequiredMixin, UpdateView):
    """Edit clinic settings."""

    model = ClinicSettings
    form_class = ClinicSettingsForm
    template_name = 'superadmin/settings.html'
    success_url = reverse_lazy('superadmin:settings')

    def get_object(self, queryset=None):
        from datetime import time
        # Get or create the singleton clinic settings with sensible defaults
        obj, created = ClinicSettings.objects.get_or_create(
            pk=1,
            defaults={
                'name': 'My Clinic',
                'address': '',
                'phone': '',
                'email': 'clinic@example.com',
                'opening_time': time(8, 0),
                'closing_time': time(18, 0),
                'days_open': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
            }
        )
        return obj

    def form_valid(self, form):
        messages.success(self.request, _('Settings saved successfully.'))
        return super().form_valid(form)


class AuditDashboardView(SuperuserRequiredMixin, ListView):
    """View and filter audit logs."""

    model = AuditLog
    template_name = 'superadmin/audit_dashboard.html'
    context_object_name = 'audit_logs'
    paginate_by = 50

    def get_queryset(self):
        queryset = AuditLog.objects.select_related('user').order_by('-created_at')

        # Filter by user
        user_id = self.request.GET.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        # Filter by action
        action = self.request.GET.get('action')
        if action:
            queryset = queryset.filter(action=action)

        # Filter by date range
        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)

        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = User.objects.filter(is_staff=True).order_by('email')
        context['actions'] = AuditLog.objects.values_list('action', flat=True).distinct()
        context['current_filters'] = {
            'user': self.request.GET.get('user', ''),
            'action': self.request.GET.get('action', ''),
            'date_from': self.request.GET.get('date_from', ''),
            'date_to': self.request.GET.get('date_to', ''),
        }
        return context


class MonitoringView(SuperuserRequiredMixin, TemplateView):
    """System monitoring and stats."""

    template_name = 'superadmin/monitoring.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Database stats
        context['db_stats'] = self._get_db_stats()

        # Model counts
        context['model_counts'] = self._get_model_counts()

        # Recent activity
        context['activity_stats'] = self._get_activity_stats()

        return context

    def _get_db_stats(self):
        """Get database statistics."""
        from django.db import connection

        stats = {}
        try:
            with connection.cursor() as cursor:
                # Get database size (PostgreSQL)
                cursor.execute("""
                    SELECT pg_size_pretty(pg_database_size(current_database()))
                """)
                stats['size'] = cursor.fetchone()[0]
        except Exception:
            stats['size'] = 'N/A'

        return stats

    def _get_model_counts(self):
        """Get counts for key models."""
        from apps.pets.models import Pet
        from apps.appointments.models import Appointment
        from apps.store.models import Order
        from apps.billing.models import Invoice

        return {
            'users': User.objects.count(),
            'pets': Pet.objects.count(),
            'appointments': Appointment.objects.count(),
            'orders': Order.objects.count(),
            'invoices': Invoice.objects.count(),
            'audit_logs': AuditLog.objects.count(),
        }

    def _get_activity_stats(self):
        """Get activity statistics."""
        today = timezone.now().date()
        last_7_days = today - timezone.timedelta(days=7)
        last_30_days = today - timezone.timedelta(days=30)

        return {
            'logins_today': AuditLog.objects.filter(
                action='login',
                created_at__date=today
            ).count(),
            'logins_7_days': AuditLog.objects.filter(
                action='login',
                created_at__date__gte=last_7_days
            ).count(),
            'actions_30_days': AuditLog.objects.filter(
                created_at__date__gte=last_30_days
            ).count(),
        }


class ModuleListView(SuperuserRequiredMixin, ListView):
    """List all modules grouped by section with toggle controls."""

    model = ModuleConfig
    template_name = 'superadmin/module_list.html'
    context_object_name = 'modules'

    def get_queryset(self):
        return ModuleConfig.objects.all().order_by('section', 'display_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Group modules by section
        modules_by_section = defaultdict(list)
        for module in context['modules']:
            modules_by_section[module.section].append(module)

        # Convert to ordered dict with section display names
        section_names = dict(ModuleConfig.SECTION_CHOICES)
        context['modules_by_section'] = {
            section: {
                'name': section_names.get(section, section.title()),
                'modules': modules,
            }
            for section, modules in modules_by_section.items()
        }
        context['sections'] = list(modules_by_section.keys())

        return context


class ModuleToggleView(SuperuserRequiredMixin, View):
    """Toggle module enabled/disabled status (HTMX endpoint)."""

    def post(self, request, pk):
        module = get_object_or_404(ModuleConfig, pk=pk)

        # Toggle the status
        if module.is_enabled:
            module.disable(user=request.user)
            action = 'module_disabled'
            message = f"Module '{module.display_name}' disabled."
        else:
            module.enable()
            action = 'module_enabled'
            message = f"Module '{module.display_name}' enabled."

        # Create audit log
        AuditLog.objects.create(
            user=request.user,
            action=action,
            resource_type='ModuleConfig',
            resource_id=str(module.pk),
            resource_repr=module.display_name,
            extra_data={
                'module_id': module.pk,
                'module_name': module.app_name,
                'display_name': module.display_name,
                'new_status': module.is_enabled,
            },
            ip_address=self._get_client_ip(request),
        )

        # Return partial for HTMX or redirect
        if request.headers.get('HX-Request'):
            return self._render_module_row(request, module, message)

        messages.success(request, message)
        return HttpResponseRedirect(reverse_lazy('superadmin:module_list'))

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    def _render_module_row(self, request, module, message):
        from django.template.loader import render_to_string
        html = render_to_string(
            'superadmin/partials/module_row.html',
            {'module': module, 'message': message},
            request=request,
        )
        return HttpResponse(html)


class ModuleFeaturesView(SuperuserRequiredMixin, TemplateView):
    """List features for a specific module."""

    template_name = 'superadmin/module_features.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        module = get_object_or_404(ModuleConfig, pk=self.kwargs['pk'])
        context['module'] = module
        context['features'] = FeatureFlag.objects.filter(module=module).order_by('key')
        return context


class FeatureToggleView(SuperuserRequiredMixin, View):
    """Toggle feature flag enabled/disabled status (HTMX endpoint)."""

    def post(self, request, pk):
        feature = get_object_or_404(FeatureFlag, pk=pk)

        # Toggle the status
        feature.is_enabled = not feature.is_enabled
        feature.save(update_fields=['is_enabled', 'updated_at'])

        action = 'feature_enabled' if feature.is_enabled else 'feature_disabled'
        message = f"Feature '{feature.key}' {'enabled' if feature.is_enabled else 'disabled'}."

        # Create audit log
        AuditLog.objects.create(
            user=request.user,
            action=action,
            resource_type='FeatureFlag',
            resource_id=str(feature.pk),
            resource_repr=feature.key,
            extra_data={
                'feature_id': feature.pk,
                'feature_key': feature.key,
                'module_id': feature.module_id,
                'new_status': feature.is_enabled,
            },
            ip_address=self._get_client_ip(request),
        )

        # Return partial for HTMX or redirect
        if request.headers.get('HX-Request'):
            return self._render_feature_row(request, feature, message)

        messages.success(request, message)
        if feature.module:
            return HttpResponseRedirect(
                reverse_lazy('superadmin:module_features', kwargs={'pk': feature.module.pk})
            )
        return HttpResponseRedirect(reverse_lazy('superadmin:module_list'))

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    def _render_feature_row(self, request, feature, message):
        from django.template.loader import render_to_string
        html = render_to_string(
            'superadmin/partials/feature_row.html',
            {'feature': feature, 'message': message},
            request=request,
        )
        return HttpResponse(html)
