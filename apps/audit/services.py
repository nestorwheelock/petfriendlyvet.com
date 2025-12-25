"""Audit logging service."""
from .models import AuditLog


class AuditService:
    """Service for creating audit log entries."""

    @classmethod
    def get_client_ip(cls, request):
        """Extract client IP from request."""
        if not request:
            return None
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    @classmethod
    def log_action(
        cls,
        user,
        action,
        resource_type,
        resource_id='',
        resource_repr='',
        request=None,
        sensitivity='normal',
        **extra
    ):
        """Log an action to the audit trail."""
        return AuditLog.objects.create(
            user=user,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else '',
            resource_repr=resource_repr[:200] if resource_repr else '',
            url_path=request.path if request else '',
            method=request.method if request else '',
            ip_address=cls.get_client_ip(request),
            user_agent=(request.META.get('HTTP_USER_AGENT', '')[:500]
                        if request else ''),
            sensitivity=sensitivity,
            extra_data=extra if extra else {},
        )

    @classmethod
    def log_model_change(cls, user, action, instance, request=None, sensitivity='normal'):
        """Log a model create/update/delete."""
        return cls.log_action(
            user=user,
            action=action,
            resource_type=f'{instance._meta.app_label}.{instance._meta.model_name}',
            resource_id=instance.pk,
            resource_repr=str(instance)[:200],
            request=request,
            sensitivity=sensitivity,
        )
