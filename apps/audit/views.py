"""Views for audit log functionality."""
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.views.generic import TemplateView, ListView, DetailView

from apps.accounts.mixins import ModulePermissionMixin
from .models import AuditLog

User = get_user_model()


class AuditPermissionMixin(ModulePermissionMixin):
    """Mixin requiring audit module permission."""
    required_module = 'audit'
    required_action = 'view'


class AuditDashboardView(AuditPermissionMixin, TemplateView):
    """Audit dashboard with overview statistics."""

    template_name = 'audit/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Total logs
        context['total_logs'] = AuditLog.objects.count()

        # Recent logs
        context['recent_logs'] = AuditLog.objects.select_related(
            'user'
        ).order_by('-created_at')[:20]

        # Logs by action type
        context['action_stats'] = AuditLog.objects.values('action').annotate(
            count=Count('id')
        ).order_by('-count')

        # Logs by sensitivity
        context['sensitivity_stats'] = AuditLog.objects.values('sensitivity').annotate(
            count=Count('id')
        ).order_by('-count')

        # High sensitivity count
        context['high_sensitivity_count'] = AuditLog.objects.filter(
            sensitivity__in=['high', 'critical']
        ).count()

        return context


class AuditLogListView(AuditPermissionMixin, ListView):
    """List of audit log entries."""

    model = AuditLog
    template_name = 'audit/log_list.html'
    context_object_name = 'logs'
    paginate_by = 50

    def get_queryset(self):
        queryset = AuditLog.objects.select_related('user')

        # Filter by user
        user_id = self.request.GET.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        # Filter by action
        action = self.request.GET.get('action')
        if action:
            queryset = queryset.filter(action=action)

        # Filter by resource type
        resource_type = self.request.GET.get('resource_type')
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)

        # Filter by sensitivity
        sensitivity = self.request.GET.get('sensitivity')
        if sensitivity:
            queryset = queryset.filter(sensitivity=sensitivity)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Available filters
        context['users'] = User.objects.filter(is_staff=True).order_by('email')
        context['actions'] = AuditLog.ACTION_CHOICES
        context['sensitivities'] = AuditLog.SENSITIVITY_CHOICES

        # Resource types in use
        context['resource_types'] = AuditLog.objects.values_list(
            'resource_type', flat=True
        ).distinct().order_by('resource_type')

        return context


class AuditLogDetailView(AuditPermissionMixin, DetailView):
    """Audit log entry detail."""

    model = AuditLog
    template_name = 'audit/log_detail.html'
    context_object_name = 'log'


class UserActivityReportView(AuditPermissionMixin, TemplateView):
    """User activity report showing activity summary by user."""

    template_name = 'audit/user_activity.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Activity stats by user
        context['user_stats'] = AuditLog.objects.values(
            'user__id', 'user__email', 'user__first_name', 'user__last_name'
        ).annotate(
            total_actions=Count('id')
        ).order_by('-total_actions')[:20]

        # Activity by action type per user
        context['action_breakdown'] = AuditLog.objects.values(
            'user__email', 'action'
        ).annotate(
            count=Count('id')
        ).order_by('user__email', '-count')

        return context
