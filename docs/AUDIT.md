# Audit Logging Module

The `apps.audit` module provides comprehensive audit logging for staff actions on sensitive data. It tracks page views, model changes, and provides queryable logs for compliance and investigation purposes.

## Table of Contents

- [Overview](#overview)
- [How It Works](#how-it-works)
- [AuditLog Model](#auditlog-model)
- [Automatic Page View Logging](#automatic-page-view-logging)
- [Programmatic Logging](#programmatic-logging)
- [Model Change Tracking](#model-change-tracking)
- [Admin Interface](#admin-interface)
- [Querying Audit Logs](#querying-audit-logs)
- [Adding New Audited Paths](#adding-new-audited-paths)
- [Adding New Audited Models](#adding-new-audited-models)
- [Data Retention](#data-retention)

## Overview

The audit module automatically logs:

- **Page views** - When staff access sensitive pages (inventory, practice, referrals, pharmacy, CRM, billing)
- **Model changes** - When audited models are created, updated, or deleted
- **Request context** - IP address, user agent, URL path, HTTP method

Each log entry includes:
- Who (user)
- What (action, resource type, resource ID)
- When (timestamp)
- Where (IP address, user agent)
- Sensitivity level (normal, high, critical)

## How It Works

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   HTTP Request  │────▶│ AuditMiddleware │────▶│    AuditLog     │
│  (staff user)   │     │  (page views)   │     │    (database)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                         ▲
┌─────────────────┐     ┌─────────────────┐              │
│  Model Save/    │────▶│  Django Signals │──────────────┘
│  Delete         │     │  (post_save,    │
└─────────────────┘     │   post_delete)  │
                        └─────────────────┘
```

## AuditLog Model

Location: `apps/audit/models.py`

```python
class AuditLog(models.Model):
    # Who
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    # What
    action = models.CharField(max_length=20)  # view, create, update, delete, export
    resource_type = models.CharField(max_length=100)  # e.g., 'inventory.dashboard'
    resource_id = models.CharField(max_length=50)  # e.g., '123' or ''
    resource_repr = models.CharField(max_length=200)  # Human-readable description

    # Context
    url_path = models.CharField(max_length=500)
    method = models.CharField(max_length=10)  # GET, POST, etc.
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.CharField(max_length=500)

    # Metadata
    sensitivity = models.CharField(max_length=20)  # normal, high, critical
    extra_data = models.JSONField(default=dict)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
```

### Action Types

| Action | Description |
|--------|-------------|
| `view` | Resource was viewed |
| `create` | Resource was created |
| `update` | Resource was modified |
| `delete` | Resource was deleted |
| `export` | Data was exported |
| `login` | User logged in |
| `logout` | User logged out |

### Sensitivity Levels

| Level | Description | Examples |
|-------|-------------|----------|
| `normal` | Standard business data | Inventory dashboard, stock levels |
| `high` | Sensitive data | Prescriptions, referrals, settings, invoices |
| `critical` | Highly sensitive | Controlled substances, security settings |

## Automatic Page View Logging

The `AuditMiddleware` automatically logs page views for staff users accessing these paths:

| Path Prefix | Resource Types |
|-------------|----------------|
| `/inventory/` | `inventory.dashboard`, `inventory.stock`, `inventory.batch`, etc. |
| `/practice/` | `practice.dashboard`, `practice.staff`, `practice.settings`, etc. |
| `/referrals/` | `referrals.dashboard`, `referrals.specialist`, `referrals.referral`, etc. |
| `/pharmacy/` | `pharmacy.dashboard`, `pharmacy.prescription`, etc. |
| `/crm/` | `crm.dashboard`, `crm.customer`, etc. |
| `/billing/` | `billing.dashboard`, `billing.invoice`, etc. |

### High-Sensitivity Paths

These paths are automatically marked with `sensitivity='high'`:

- `/referrals/outbound/*` - Patient referral data
- `/pharmacy/prescriptions/*` - Prescription information
- `/practice/settings/*` - Clinic settings
- `/billing/*` - Financial data
- `/crm/customers/*` - Customer personal data

## Programmatic Logging

Use `AuditService` for custom audit logging:

Location: `apps/audit/services.py`

### Basic Usage

```python
from apps.audit.services import AuditService

# Log a custom action
AuditService.log_action(
    user=request.user,
    action='export',
    resource_type='reports.inventory',
    resource_id='',
    request=request,
    sensitivity='normal',
    format='csv',  # Extra data stored in extra_data field
    rows=1000,
)
```

### Log Model Changes

```python
from apps.audit.services import AuditService

# Log a model change
AuditService.log_model_change(
    user=request.user,
    action='update',
    instance=prescription,
    request=request,
)
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user` | User | Yes | The user performing the action |
| `action` | str | Yes | Action type (view, create, update, delete, export) |
| `resource_type` | str | Yes | Dot-notation type (e.g., 'inventory.stock') |
| `resource_id` | str | No | ID of the specific resource |
| `resource_repr` | str | No | Human-readable description |
| `request` | HttpRequest | No | Request object for context extraction |
| `sensitivity` | str | No | Sensitivity level (default: 'normal') |
| `**extra` | kwargs | No | Additional data stored in extra_data JSON field |

## Model Change Tracking

Django signals automatically track changes to specified models.

Location: `apps/audit/signals.py`

### Currently Audited Models

```python
AUDITED_MODELS = [
    'inventory.StockMovement',
    'inventory.PurchaseOrder',
    'referrals.Referral',
    'referrals.Specialist',
    'practice.Task',
    'practice.Shift',
    'pharmacy.Prescription',
]
```

When these models are created, updated, or deleted by a staff user, an audit log entry is automatically created.

## Admin Interface

Access the audit logs at: `/admin/audit/auditlog/`

Features:
- **List view**: Shows timestamp, user, action, resource type, resource ID, sensitivity, IP
- **Filters**: By action, sensitivity, resource type, date
- **Search**: By user email, resource type, resource ID, URL path, IP address
- **Date hierarchy**: Navigate by date
- **Read-only**: Logs cannot be created, edited, or deleted via admin

## Querying Audit Logs

### Django ORM Examples

```python
from apps.audit.models import AuditLog
from django.utils import timezone
from datetime import timedelta

# Get all logs for a specific user
user_logs = AuditLog.objects.filter(user=user)

# Get high-sensitivity actions in the last 24 hours
recent_sensitive = AuditLog.objects.filter(
    sensitivity='high',
    created_at__gte=timezone.now() - timedelta(days=1)
)

# Get all prescription views
prescription_views = AuditLog.objects.filter(
    resource_type='pharmacy.prescription',
    action='view'
)

# Get actions for a specific resource
resource_history = AuditLog.objects.filter(
    resource_type='referrals.referral',
    resource_id='123'
).order_by('-created_at')

# Get all actions from a specific IP
ip_actions = AuditLog.objects.filter(ip_address='192.168.1.100')

# Count actions by type for a date range
from django.db.models import Count

action_counts = AuditLog.objects.filter(
    created_at__date=timezone.now().date()
).values('action').annotate(count=Count('id'))
```

### Compliance Report Examples

```python
# Staff activity report for a date range
def staff_activity_report(start_date, end_date):
    return AuditLog.objects.filter(
        created_at__range=(start_date, end_date)
    ).values('user__email', 'action').annotate(
        count=Count('id')
    ).order_by('user__email', 'action')

# High-sensitivity access report
def sensitive_access_report(start_date, end_date):
    return AuditLog.objects.filter(
        created_at__range=(start_date, end_date),
        sensitivity__in=['high', 'critical']
    ).select_related('user').order_by('-created_at')

# Unusual activity detection (actions outside business hours)
def after_hours_activity(start_date, end_date):
    return AuditLog.objects.filter(
        created_at__range=(start_date, end_date),
        created_at__hour__lt=8  # Before 8 AM
    ) | AuditLog.objects.filter(
        created_at__range=(start_date, end_date),
        created_at__hour__gte=18  # After 6 PM
    )
```

## Adding New Audited Paths

To add a new path prefix to automatic logging:

1. Edit `apps/audit/middleware.py`
2. Add the path to `AUDITED_PREFIXES`:

```python
AUDITED_PREFIXES = [
    '/inventory/',
    '/practice/',
    '/referrals/',
    '/pharmacy/',
    '/crm/',
    '/billing/',
    '/new-app/',  # Add new path here
]
```

3. Add resource type mappings in `_get_resource_type()`:

```python
if path.startswith('/new-app/'):
    if path == '/new-app/' or path == '/new-app':
        return 'newapp.dashboard'
    elif '/items/' in path:
        return 'newapp.item'
    # ... more mappings
```

4. If needed, add high-sensitivity patterns in `HIGH_SENSITIVITY_PATTERNS`:

```python
HIGH_SENSITIVITY_PATTERNS = [
    # ... existing patterns
    r'^/new-app/sensitive/',
]
```

## Adding New Audited Models

To track create/update/delete on a new model:

1. Edit `apps/audit/signals.py`
2. Add the model path to `AUDITED_MODELS`:

```python
AUDITED_MODELS = [
    # ... existing models
    'newapp.SensitiveModel',  # Format: 'app_label.ModelName'
]
```

The model will now be automatically tracked when staff users make changes.

## Data Retention

**Current Policy**: Audit logs are kept forever (no automatic deletion).

Rationale:
- Compliance requirements may need historical data
- Storage costs are minimal for text-based logs
- Audit trails should be complete for investigations

### Future Considerations

If retention limits are needed, consider:

1. **Archive to cold storage** before deletion
2. **Aggregate old data** into summary reports
3. **Configure retention period** in settings:

```python
# config/settings/base.py (future implementation)
AUDIT_RETENTION_DAYS = 365 * 7  # 7 years
```

## Testing

### Unit Tests

Location: `tests/test_audit.py`

```bash
# Run audit unit tests
python -m pytest tests/test_audit.py -v
```

### Browser Tests

Location: `tests/e2e/browser/test_audit.py`

```bash
# Run audit browser tests
python -m pytest tests/e2e/browser/test_audit.py -v

# Run with visible browser
python -m pytest tests/e2e/browser/test_audit.py -v --headed --slowmo=500
```

### Test Coverage

- 19 unit tests covering model, service, and middleware
- 11 browser tests verifying end-to-end audit logging
- Tests verify: log creation, sensitivity levels, IP capture, resource ID extraction
