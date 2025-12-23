# S-028: Production Error Monitoring and Graceful Degradation

**Story Type**: User Story
**Priority**: High
**Estimate**: 3-4 days
**Status**: PENDING

## User Story

**As a** developer and site owner
**I want to** automatically detect, log, and gracefully handle production errors
**So that** users see friendly error pages for known issues, and new bugs are automatically filed as GitHub issues

## Problem Statement

1. Users see ugly Django error pages (like CSRF 403) when bugs occur
2. Bugs are only discovered when manually reported or when developer notices
3. No automated system to detect error patterns and create bug reports
4. Developer (Claude) needs reminders to file bugs - should be automatic

## Proposed Solution

### Component 1: Error Tracking Middleware
- Capture all 4xx/5xx errors
- Log to database with: URL, error type, user (if any), timestamp, request data
- Rate-limit duplicate errors (don't spam)

### Component 2: Known Issues Registry
- Database model: `KnownIssue(bug_id, error_pattern, affected_urls, status, friendly_message)`
- When error matches known issue, show friendly "We're aware" page instead of ugly error
- Link to GitHub issue for transparency

### Component 3: Automated Bug Detection
- Celery task runs every hour (configurable)
- Groups errors by pattern (URL + error type)
- If new pattern with 3+ occurrences → auto-create GitHub issue
- Uses `gh` CLI to create issues with B-XXX format

### Component 4: Custom Error Pages
- Friendly 403, 404, 500 pages
- If known issue: "We're aware of this problem and working on it"
- If unknown: "Something went wrong, we've been notified"
- Always provide navigation back to safety

### Component 5: Admin Dashboard
- View error frequency over time
- See most common errors
- Mark errors as "known" (links to bug)
- Manual trigger for bug creation

## Acceptance Criteria

- [ ] All 4xx/5xx errors are logged to database
- [ ] Known issues show friendly message instead of Django error page
- [ ] New error patterns automatically create GitHub issues after threshold
- [ ] GitHub issues follow B-XXX naming convention
- [ ] Admin can view error dashboard and manage known issues
- [ ] Works in both dev and production environments
- [ ] Rate limiting prevents duplicate bug creation

## Technical Considerations

### Environment Variables
```
ERROR_MONITORING_ENABLED=true
ERROR_AUTO_BUG_THRESHOLD=3
ERROR_SCAN_INTERVAL_MINUTES=60
GITHUB_REPO=owner/petfriendlyvet.com
GITHUB_TOKEN=ghp_xxx
```

### Models
```python
class ErrorLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    error_type = models.CharField(max_length=50)  # csrf, 404, 500, etc.
    status_code = models.IntegerField()
    url = models.URLField()
    user = models.ForeignKey(User, null=True)
    request_data = models.JSONField()
    fingerprint = models.CharField(max_length=64)  # hash for grouping

class KnownIssue(models.Model):
    bug_id = models.CharField(max_length=10)  # B-001
    github_issue_url = models.URLField()
    error_fingerprint = models.CharField(max_length=64)
    friendly_message = models.TextField()
    status = models.CharField(choices=['open', 'fixed', 'wontfix'])
    created_at = models.DateTimeField(auto_now_add=True)
```

### Middleware Flow
```
Request → Django → Error occurs
                      ↓
              ErrorMiddleware catches
                      ↓
              Log to ErrorLog table
                      ↓
              Check KnownIssue registry
                      ↓
         ┌─────────────┴─────────────┐
    Known Issue               Unknown Issue
         ↓                           ↓
  Show friendly page         Show generic error
  with bug link              "We've been notified"
```

## Definition of Done

- [ ] ErrorLog model created with migrations
- [ ] KnownIssue model created with migrations
- [ ] Error capture middleware implemented
- [ ] Custom error templates (403, 404, 500)
- [ ] Known issue matching logic works
- [ ] Celery task for auto-bug-creation
- [ ] GitHub issue creation via `gh` CLI
- [ ] Admin views for error dashboard
- [ ] Tests written (>95% coverage)
- [ ] Documentation updated
- [ ] Works in dev and production

## Out of Scope (Future)

- Email/Slack notifications for critical errors
- Integration with external services (Sentry, DataDog)
- User-facing bug report submission
- Error analytics and trending

## Dependencies

- GitHub CLI (`gh`) installed and authenticated
- Celery for background tasks (already configured)
- Redis for rate limiting (already configured)

## Related

- B-001: CSRF Trusted Origins (triggered this story)
- S-027: Security Hardening
