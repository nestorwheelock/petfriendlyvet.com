# S-028: Production Error Monitoring and Graceful Degradation

> **REQUIRED READING:** Before implementation, review [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)

**Story Type**: User Story
**Priority**: High
**Estimate**: 3-4 days
**Status**: COMPLETED

## User Story

**As a** developer and site owner
**I want to** automatically detect, log, and gracefully handle production errors
**So that** users see friendly error pages for known issues, and new bugs are automatically filed as GitHub issues

## Problem Statement

1. Users see ugly Django error pages (like CSRF 403) when bugs occur
2. Bugs are only discovered when manually reported or when developer notices
3. No automated system to detect error patterns and create bug reports
4. Developer (Claude) needs reminders to file bugs - should be automatic

## Proposed Solution: Modular Django App

### Architecture: `apps.error_tracking`

A **reusable Django app** that can be installed in any Django project, following the pattern of other modular components.

```
apps/error_tracking/
├── __init__.py
├── admin.py              # Admin views for error dashboard
├── apps.py               # Django app config
├── middleware.py         # ErrorCaptureMiddleware
├── models.py             # ErrorLog, KnownBug models
├── services.py           # ErrorCaptureService, BugCreationService
├── tasks.py              # Celery tasks for async operations
├── urls.py               # Admin-only URLs for dashboard
├── utils.py              # Fingerprinting, GitHub CLI helpers
├── templates/
│   └── error_tracking/
│       ├── admin/
│       │   └── dashboard.html
│       └── known_bug.html
└── migrations/
```

### Component 1: Error Tracking Models

```python
# models.py
class ErrorLog(TimeStampedModel):
    """Captures all 4xx/5xx errors for analysis."""
    fingerprint = models.CharField(max_length=64, db_index=True)
    error_type = models.CharField(max_length=50)  # csrf, 404, 500, etc.
    status_code = models.IntegerField()
    url_pattern = models.CharField(max_length=500)  # Normalized URL
    full_url = models.URLField()
    method = models.CharField(max_length=10)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.CharField(max_length=500, blank=True)
    request_data = models.JSONField(default=dict)
    exception_type = models.CharField(max_length=200, blank=True)
    exception_message = models.TextField(blank=True)
    traceback = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['fingerprint', 'created']),
            models.Index(fields=['status_code', 'created']),
        ]


class KnownBug(TimeStampedModel, SoftDeleteModel):
    """Links error fingerprints to tracked bugs."""
    bug_id = models.CharField(max_length=10, unique=True)  # B-001
    fingerprint = models.CharField(max_length=64, unique=True, db_index=True)
    github_issue_number = models.IntegerField(null=True, blank=True)
    github_issue_url = models.URLField(blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    occurrence_count = models.IntegerField(default=1)
    last_occurrence = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Known Bug"
        verbose_name_plural = "Known Bugs"
```

### Component 2: Error Capture Middleware

```python
# middleware.py
class ErrorCaptureMiddleware:
    """Captures all errors and routes to error tracking service."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.service = ErrorCaptureService()

    def __call__(self, request):
        response = self.get_response(request)

        # Capture 4xx and 5xx errors
        if response.status_code >= 400:
            self.service.capture_error(request, response)

        return response

    def process_exception(self, request, exception):
        """Capture unhandled exceptions with full traceback."""
        self.service.capture_exception(request, exception)
        return None  # Let Django's normal exception handling continue
```

### Component 3: Error Capture Service

```python
# services.py
class ErrorCaptureService:
    """Handles error capture, fingerprinting, and bug creation."""

    def generate_fingerprint(self, error_type: str, url: str, status_code: int) -> str:
        """Create unique fingerprint from error type + normalized URL pattern."""
        normalized_url = self.normalize_url(url)
        data = f"{error_type}:{status_code}:{normalized_url}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def normalize_url(self, url: str) -> str:
        """Replace dynamic segments with placeholders."""
        # /api/pets/123/ -> /api/pets/{id}/
        # /users/john/ -> /users/{slug}/
        patterns = [
            (r'/\d+/', '/{id}/'),
            (r'/[a-f0-9-]{36}/', '/{uuid}/'),
        ]
        for pattern, replacement in patterns:
            url = re.sub(pattern, replacement, url)
        return url

    def capture_error(self, request, response):
        """Log error and trigger bug creation if new."""
        fingerprint = self.generate_fingerprint(...)

        # Check if this is a known bug
        known_bug = KnownBug.objects.filter(fingerprint=fingerprint).first()

        if known_bug:
            # Increment count for existing bug
            known_bug.occurrence_count = F('occurrence_count') + 1
            known_bug.save(update_fields=['occurrence_count', 'last_occurrence'])
        else:
            # Queue bug creation (async via Celery)
            create_bug_task.delay(fingerprint, error_data)

        # Always log the error
        ErrorLog.objects.create(...)


class BugCreationService:
    """Creates bug files and GitHub issues."""

    def get_next_bug_id(self) -> str:
        """Get next sequential B-XXX ID."""
        last_bug = KnownBug.objects.order_by('-bug_id').first()
        if last_bug:
            num = int(last_bug.bug_id.split('-')[1]) + 1
        else:
            num = 1
        return f"B-{num:03d}"

    def create_bug_file(self, bug_id: str, data: dict) -> Path:
        """Create planning/tasks/B-XXX-description.md file."""
        template = self.get_bug_template()
        content = template.format(**data)

        filename = f"{bug_id}-{slugify(data['title'])}.md"
        filepath = Path(settings.BASE_DIR) / 'planning' / 'tasks' / filename
        filepath.write_text(content)
        return filepath

    def create_github_issue(self, bug_id: str, data: dict) -> tuple[int, str]:
        """Create GitHub issue using gh CLI."""
        title = f"{bug_id}: {data['title']}"
        body = self.format_issue_body(data)

        result = subprocess.run([
            'gh', 'issue', 'create',
            '--title', title,
            '--body', body,
            '--label', 'bug',
            '--label', data['severity'],
        ], capture_output=True, text=True)

        # Parse issue number and URL from output
        # Returns: (issue_number, issue_url)
        return self.parse_gh_output(result.stdout)
```

### Component 4: Celery Tasks

```python
# tasks.py
@shared_task(bind=True, max_retries=3)
def create_bug_task(self, fingerprint: str, error_data: dict):
    """Async task to create bug file and GitHub issue."""
    service = BugCreationService()

    try:
        bug_id = service.get_next_bug_id()

        # Create local bug file
        filepath = service.create_bug_file(bug_id, error_data)

        # Create GitHub issue
        issue_number, issue_url = service.create_github_issue(bug_id, error_data)

        # Save KnownBug record
        KnownBug.objects.create(
            bug_id=bug_id,
            fingerprint=fingerprint,
            github_issue_number=issue_number,
            github_issue_url=issue_url,
            title=error_data['title'],
            description=error_data['description'],
            severity=error_data['severity'],
        )

        logger.info(f"Created bug {bug_id} with GitHub issue #{issue_number}")

    except Exception as e:
        logger.error(f"Bug creation failed: {e}")
        self.retry(exc=e, countdown=60)
```

### Component 5: Admin Dashboard

```python
# admin.py
@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = ['created', 'status_code', 'error_type', 'url_pattern', 'fingerprint']
    list_filter = ['status_code', 'error_type', 'created']
    search_fields = ['url_pattern', 'exception_message']
    readonly_fields = ['fingerprint', 'request_data', 'traceback']

    def changelist_view(self, request, extra_context=None):
        # Add dashboard stats to context
        extra_context = extra_context or {}
        extra_context['error_stats'] = self.get_error_stats()
        return super().changelist_view(request, extra_context)


@admin.register(KnownBug)
class KnownBugAdmin(admin.ModelAdmin):
    list_display = ['bug_id', 'title', 'severity', 'status', 'occurrence_count', 'last_occurrence']
    list_filter = ['severity', 'status']
    search_fields = ['bug_id', 'title', 'description']
    actions = ['mark_resolved', 'create_github_issue']
```

### Configuration

```python
# settings.py
INSTALLED_APPS = [
    ...
    'apps.error_tracking',
]

MIDDLEWARE = [
    ...
    'apps.error_tracking.middleware.ErrorCaptureMiddleware',  # After SecurityMiddleware
]

# Error tracking configuration
ERROR_TRACKING = {
    'ENABLED': True,
    'AUTO_CREATE_BUGS': True,  # Auto-create B-XXX files and GitHub issues
    'BUG_THRESHOLD': 1,  # Create bug after N occurrences (1 for dev testing)
    'GITHUB_REPO': 'owner/repo',  # For gh CLI
    'PLANNING_DIR': 'planning/tasks',  # Where to create B-XXX.md files
    'EXCLUDE_PATHS': ['/health/', '/static/', '/media/'],
    'EXCLUDE_STATUS_CODES': [],  # e.g., [404] to ignore 404s
}
```

## Task Breakdown

| Task | Description | Estimate |
|------|-------------|----------|
| T-072 | Create error_tracking app with models | 2h |
| T-073 | Implement ErrorCaptureMiddleware | 2h |
| T-074 | Implement fingerprinting and ErrorCaptureService | 2h |
| T-075 | Implement BugCreationService (file + GitHub) | 3h |
| T-076 | Create Celery tasks for async bug creation | 2h |
| T-077 | Build admin dashboard with stats | 2h |
| T-078 | Integration tests and edge cases | 3h |
| T-079 | Documentation and deployment | 2h |

## Acceptance Criteria

- [ ] All 4xx/5xx errors are logged to ErrorLog table
- [ ] Errors with same fingerprint increment occurrence_count
- [ ] First occurrence of new error creates B-XXX.md file
- [ ] First occurrence of new error creates GitHub issue with bug label
- [ ] Admin can view error dashboard with stats
- [ ] Admin can manually create bug from error log
- [ ] Configuration via Django settings
- [ ] Works in both dev and production environments
- [ ] >95% test coverage

## Definition of Done

- [ ] `apps/error_tracking/` app created with all components
- [ ] ErrorLog and KnownBug models with migrations
- [ ] ErrorCaptureMiddleware capturing all errors
- [ ] BugCreationService creating files and GitHub issues
- [ ] Celery tasks for async processing
- [ ] Admin dashboard with error stats
- [ ] Tests written (>95% coverage)
- [ ] Documentation in README
- [ ] App registered in INSTALLED_APPS
- [ ] Middleware added to MIDDLEWARE

## Dependencies

- Celery (already configured)
- Redis (already configured)
- GitHub CLI (`gh`) authenticated
- `planning/tasks/` directory exists

## Related

- B-001: CSRF Trusted Origins (triggered this story)
- S-027: Security Hardening
