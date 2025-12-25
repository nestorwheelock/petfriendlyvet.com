# Error Tracking Module

The `apps.error_tracking` module captures and manages application errors, providing error logging with fingerprinting and bug tracking with GitHub integration.

## Table of Contents

- [Overview](#overview)
- [Models](#models)
  - [ErrorLog](#errorlog)
  - [KnownBug](#knownbug)
- [Workflows](#workflows)
- [Integration Points](#integration-points)
- [Query Examples](#query-examples)
- [Testing](#testing)

## Overview

The error tracking module provides:

- **Error Logging** - Capture 4xx/5xx errors with fingerprinting
- **Bug Tracking** - Link errors to known bugs
- **GitHub Integration** - Track bugs with GitHub issues
- **Occurrence Tracking** - Count and monitor error frequency

## Models

Location: `apps/error_tracking/models.py`

### ErrorLog

Captures all 4xx/5xx errors for analysis.

```python
class ErrorLog(TimeStampedModel):
    fingerprint = models.CharField(max_length=64, db_index=True)  # Unique error signature
    error_type = models.CharField(max_length=50)
    status_code = models.IntegerField()
    url_pattern = models.CharField(max_length=500)
    full_url = models.URLField(max_length=2000)
    method = models.CharField(max_length=10)  # GET, POST, etc.

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.CharField(max_length=500, blank=True)

    request_data = models.JSONField(default=dict)  # Request payload
    exception_type = models.CharField(max_length=200, blank=True)
    exception_message = models.TextField(blank=True)
    traceback = models.TextField(blank=True)
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `fingerprint` | CharField | Unique error signature for grouping |
| `status_code` | Integer | HTTP status code (404, 500, etc.) |
| `exception_type` | CharField | Python exception class name |
| `traceback` | TextField | Full stack trace |

### KnownBug

Links error fingerprints to tracked bugs.

```python
SEVERITY_CHOICES = [
    ('critical', 'Critical'),
    ('high', 'High'),
    ('medium', 'Medium'),
    ('low', 'Low'),
]

STATUS_CHOICES = [
    ('open', 'Open'),
    ('in_progress', 'In Progress'),
    ('resolved', 'Resolved'),
    ('wontfix', "Won't Fix"),
]

class KnownBug(TimeStampedModel, SoftDeleteModel):
    bug_id = models.CharField(max_length=10, unique=True)  # B-001
    fingerprint = models.CharField(max_length=64, unique=True)

    # GitHub integration
    github_issue_number = models.IntegerField(null=True)
    github_issue_url = models.URLField(blank=True)

    title = models.CharField(max_length=200)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')

    occurrence_count = models.IntegerField(default=1)
    last_occurrence = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True)
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `bug_id` | CharField | Bug identifier (B-001 format) |
| `fingerprint` | CharField | Links to ErrorLog entries |
| `github_issue_number` | Integer | GitHub issue number |
| `occurrence_count` | Integer | Times this bug occurred |

## Workflows

### Logging an Error

```python
from apps.error_tracking.models import ErrorLog
import hashlib

def log_error(request, exception, status_code):
    # Generate fingerprint from exception details
    fingerprint_data = f"{exception.__class__.__name__}:{request.path}"
    fingerprint = hashlib.sha256(fingerprint_data.encode()).hexdigest()[:64]

    ErrorLog.objects.create(
        fingerprint=fingerprint,
        error_type=exception.__class__.__name__,
        status_code=status_code,
        url_pattern=request.path,
        full_url=request.build_absolute_uri(),
        method=request.method,
        user=request.user if request.user.is_authenticated else None,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        exception_type=exception.__class__.__name__,
        exception_message=str(exception),
        traceback=traceback.format_exc(),
    )
```

### Creating a Known Bug

```python
from apps.error_tracking.models import ErrorLog, KnownBug

# Find recurring error
fingerprint = '...'
errors = ErrorLog.objects.filter(fingerprint=fingerprint)

if errors.count() >= 3:  # Create bug if recurring
    bug = KnownBug.objects.create(
        bug_id='B-001',
        fingerprint=fingerprint,
        title='NullPointerException in checkout',
        description='User encounters error when cart is empty',
        severity='high',
        status='open',
        occurrence_count=errors.count(),
    )

    # Optionally create GitHub issue
    issue = create_github_issue(bug.title, bug.description)
    bug.github_issue_number = issue.number
    bug.github_issue_url = issue.html_url
    bug.save()
```

## Integration Points

### With Middleware

```python
# Error logging middleware
class ErrorLoggingMiddleware:
    def process_exception(self, request, exception):
        log_error(request, exception, 500)
        return None  # Let Django handle response
```

### With GitHub

```python
from apps.error_tracking.models import KnownBug

# When bug is resolved, update status
bug = KnownBug.objects.get(github_issue_number=123)
bug.status = 'resolved'
bug.resolved_at = timezone.now()
bug.save()
```

## Query Examples

```python
from apps.error_tracking.models import ErrorLog, KnownBug
from django.db.models import Count
from datetime import timedelta
from django.utils import timezone

# Most frequent errors today
frequent = ErrorLog.objects.filter(
    created_at__date=timezone.now().date()
).values('fingerprint', 'error_type').annotate(
    count=Count('id')
).order_by('-count')[:10]

# Untracked recurring errors
untracked = ErrorLog.objects.values('fingerprint').annotate(
    count=Count('id')
).filter(count__gte=5).exclude(
    fingerprint__in=KnownBug.objects.values('fingerprint')
)

# Open critical bugs
critical = KnownBug.objects.filter(
    severity='critical',
    status='open'
)

# 500 errors in last hour
recent_500 = ErrorLog.objects.filter(
    status_code=500,
    created_at__gte=timezone.now() - timedelta(hours=1)
)
```

## Testing

Location: `tests/test_error_tracking.py`

```bash
python -m pytest tests/test_error_tracking.py -v
```
