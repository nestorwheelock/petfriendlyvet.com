# T-069: Add Content Security Policy Headers

> **Parent Story:** [S-027 Security Hardening](../stories/S-027-security-hardening.md)

**Task Type:** Security Configuration
**Priority:** MEDIUM
**Estimate:** 1 hour
**Status:** PENDING

---

## Objective

Implement Content Security Policy (CSP) headers to mitigate Cross-Site Scripting (XSS) attacks by controlling which resources the browser is allowed to load.

---

## Background

Content Security Policy is a security layer that helps detect and mitigate XSS and data injection attacks. By specifying allowed sources for scripts, styles, images, and other resources, CSP prevents malicious code from executing even if an attacker manages to inject it into the page.

---

## Current State

The application currently has no CSP headers configured. While Django's template auto-escaping provides XSS protection, CSP adds defense-in-depth.

---

## Implementation

### Step 1: Add Dependency

```bash
# requirements/production.txt
django-csp>=3.8
```

### Step 2: Configure CSP Settings

```python
# config/settings/production.py

# Content Security Policy Configuration
# Start in report-only mode, then enforce after testing

MIDDLEWARE = [
    # ... existing middleware
    'csp.middleware.CSPMiddleware',
]

# CSP Directives
CSP_DEFAULT_SRC = ("'self'",)

# Scripts: self + HTMX + Alpine.js CDNs
CSP_SCRIPT_SRC = (
    "'self'",
    "unpkg.com",
    "cdn.jsdelivr.net",
    # Add nonce for inline scripts
)

# Styles: self + inline (for Tailwind) + Google Fonts
CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",  # Required for Tailwind utility classes
    "fonts.googleapis.com",
)

# Fonts: Google Fonts
CSP_FONT_SRC = (
    "'self'",
    "fonts.gstatic.com",
)

# Images: self + data URIs + any HTTPS
CSP_IMG_SRC = (
    "'self'",
    "data:",
    "https:",
)

# Connect (AJAX/fetch): self only
CSP_CONNECT_SRC = (
    "'self'",
)

# Frames: none (prevent clickjacking)
CSP_FRAME_SRC = ("'none'",)

# Object/embed: none
CSP_OBJECT_SRC = ("'none'",)

# Base URI: self only
CSP_BASE_URI = ("'self'",)

# Form actions: self only
CSP_FORM_ACTION = ("'self'",)

# Frame ancestors: none (alternative to X-Frame-Options)
CSP_FRAME_ANCESTORS = ("'none'",)

# Report violations to endpoint
CSP_REPORT_URI = "/csp-report/"

# Start in report-only mode for testing
CSP_REPORT_ONLY = True  # Change to False after testing
```

### Step 3: Create CSP Report Handler

```python
# apps/core/views.py

import json
import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger('csp')


@csrf_exempt
@require_POST
def csp_report(request):
    """
    Receive and log CSP violation reports.

    These reports help identify:
    1. Legitimate resources that need to be whitelisted
    2. Actual XSS attempts being blocked
    """
    try:
        report = json.loads(request.body)
        csp_report = report.get('csp-report', {})

        logger.warning(
            "CSP Violation",
            extra={
                'blocked_uri': csp_report.get('blocked-uri'),
                'violated_directive': csp_report.get('violated-directive'),
                'document_uri': csp_report.get('document-uri'),
                'source_file': csp_report.get('source-file'),
                'line_number': csp_report.get('line-number'),
                'column_number': csp_report.get('column-number'),
            }
        )
    except json.JSONDecodeError:
        pass

    return HttpResponse(status=204)
```

### Step 4: Add URL Route

```python
# config/urls.py

from apps.core.views import csp_report

urlpatterns = [
    # ... existing urls
    path('csp-report/', csp_report, name='csp_report'),
]
```

### Step 5: Development Settings

```python
# config/settings/development.py

# Disable CSP in development for easier debugging
# Or use report-only mode
CSP_REPORT_ONLY = True

# Alternative: disable entirely in dev
# MIDDLEWARE = [m for m in MIDDLEWARE if m != 'csp.middleware.CSPMiddleware']
```

---

## CSP Testing Process

### Phase 1: Report-Only Mode (1 week)
1. Deploy with `CSP_REPORT_ONLY = True`
2. Monitor CSP reports in logs
3. Add legitimate sources to whitelist
4. Fix any violations in our own code

### Phase 2: Enforcement
1. Set `CSP_REPORT_ONLY = False`
2. Monitor for user-reported issues
3. Keep report endpoint active for ongoing monitoring

---

## Files to Modify

| File | Action |
|------|--------|
| `requirements/production.txt` | Add django-csp |
| `config/settings/production.py` | Add CSP configuration |
| `config/settings/development.py` | Development CSP settings |
| `apps/core/views.py` | Add CSP report handler |
| `config/urls.py` | Add report endpoint |

---

## Tests Required

```python
# tests/test_csp.py

import pytest
from django.test import Client, override_settings


class TestCSPHeaders:
    """Test Content Security Policy configuration."""

    @override_settings(CSP_REPORT_ONLY=False)
    def test_csp_header_present(self, client):
        """CSP header should be present in responses."""
        response = client.get('/')

        # Check for CSP header (either enforcing or report-only)
        assert (
            'Content-Security-Policy' in response.headers or
            'Content-Security-Policy-Report-Only' in response.headers
        )

    @override_settings(CSP_REPORT_ONLY=False)
    def test_csp_blocks_inline_scripts(self, client):
        """CSP should restrict script sources."""
        response = client.get('/')
        csp = response.headers.get('Content-Security-Policy', '')

        # Should have script-src directive
        assert 'script-src' in csp or 'default-src' in csp

    def test_csp_report_endpoint(self, client):
        """CSP report endpoint should accept reports."""
        report = {
            'csp-report': {
                'blocked-uri': 'https://evil.com/script.js',
                'violated-directive': 'script-src',
                'document-uri': 'https://petfriendlyvet.com/',
            }
        }

        response = client.post(
            '/csp-report/',
            data=report,
            content_type='application/json'
        )

        assert response.status_code == 204

    def test_csp_allows_required_sources(self, client):
        """CSP should allow HTMX, Alpine, and Google Fonts."""
        response = client.get('/')
        csp = response.headers.get(
            'Content-Security-Policy',
            response.headers.get('Content-Security-Policy-Report-Only', '')
        )

        # Should allow our CDNs
        assert 'unpkg.com' in csp or "'self'" in csp
        assert 'cdn.jsdelivr.net' in csp or "'self'" in csp
        assert 'fonts.googleapis.com' in csp or "'self'" in csp
```

---

## Acceptance Criteria

- [ ] django-csp installed and configured
- [ ] CSP middleware added to production
- [ ] Script sources restricted to trusted CDNs
- [ ] Style sources allow necessary CDNs
- [ ] Report endpoint receives and logs violations
- [ ] Report-only mode tested before enforcement
- [ ] No legitimate functionality broken

---

## Definition of Done

- [ ] CSP package added to requirements
- [ ] CSP settings configured for production
- [ ] Report handler created and URL added
- [ ] CSP tests pass
- [ ] Deployed in report-only mode
- [ ] No false positives after 24 hours of testing
- [ ] Documentation updated

---

## Security Benefit

CSP provides defense-in-depth against XSS:

| Attack | Without CSP | With CSP |
|--------|-------------|----------|
| Inline script injection | Template escaping stops most | Blocked by script-src |
| External script loading | Could execute | Blocked unless whitelisted |
| Data exfiltration | Possible | Blocked by connect-src |
| Clickjacking | Depends on X-Frame-Options | Blocked by frame-ancestors |

---

## Common CSP Issues

**Problem:** Inline styles not working
**Solution:** `'unsafe-inline'` in style-src (required for Tailwind)

**Problem:** HTMX not loading
**Solution:** Add `unpkg.com` to script-src

**Problem:** Google Fonts broken
**Solution:** Add `fonts.googleapis.com` to style-src, `fonts.gstatic.com` to font-src

**Problem:** Images from third parties blocked
**Solution:** Add `https:` to img-src for all HTTPS images

---

*Created: December 23, 2025*
