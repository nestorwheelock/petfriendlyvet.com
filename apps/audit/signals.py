"""Audit logging signals for model change tracking."""
from threading import local

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

# Thread-local storage for current request/user
_thread_locals = local()


def set_current_user(user, request=None):
    """Set current user for signal handlers (called from middleware)."""
    _thread_locals.user = user
    _thread_locals.request = request


def get_current_user():
    """Get current user from thread-local storage."""
    return getattr(_thread_locals, 'user', None)


def get_current_request():
    """Get current request from thread-local storage."""
    return getattr(_thread_locals, 'request', None)


# Models to audit for changes
AUDITED_MODELS = [
    'inventory.StockMovement',
    'inventory.PurchaseOrder',
    'referrals.Referral',
    'referrals.Specialist',
    'practice.Task',
    'practice.Shift',
    'pharmacy.Prescription',
]


@receiver(post_save)
def audit_model_save(sender, instance, created, **kwargs):
    """Log model create/update."""
    # Avoid circular import
    if sender._meta.app_label == 'audit':
        return

    model_path = f'{sender._meta.app_label}.{sender._meta.object_name}'
    if model_path in AUDITED_MODELS:
        user = get_current_user()
        if user and user.is_staff:
            from apps.audit.services import AuditService
            AuditService.log_model_change(
                user=user,
                action='create' if created else 'update',
                instance=instance,
                request=get_current_request(),
            )


@receiver(post_delete)
def audit_model_delete(sender, instance, **kwargs):
    """Log model delete."""
    # Avoid circular import
    if sender._meta.app_label == 'audit':
        return

    model_path = f'{sender._meta.app_label}.{sender._meta.object_name}'
    if model_path in AUDITED_MODELS:
        user = get_current_user()
        if user and user.is_staff:
            from apps.audit.services import AuditService
            AuditService.log_model_change(
                user=user,
                action='delete',
                instance=instance,
                request=get_current_request(),
            )
