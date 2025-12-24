# B-007: CSP Blocking Alpine.js Expression Evaluation

**Severity**: Critical
**Affected Component**: Frontend / Alpine.js / Security Settings
**Discovered**: December 24, 2025
**Status**: RESOLVED

## Bug Description

Content Security Policy (CSP) was blocking Alpine.js from evaluating expressions, causing all interactive components (chat widget, language selector, mobile menu) to become non-functional. Buttons would not respond to clicks, dropdowns would not toggle.

## Steps to Reproduce

1. Load any page with Alpine.js components (e.g., homepage)
2. Click on chat widget button, language selector, or mobile menu
3. Observe that buttons do not respond
4. Open browser console (F12)
5. See error: `Uncaught EvalError: call to Function() blocked by CSP`

## Expected Behavior

Alpine.js components should respond to user interactions (clicks, toggles, etc.)

## Actual Behavior

All Alpine.js interactive elements were frozen/stuck. The chat widget remained stuck open, the language selector dropdown would not close, and no click handlers worked.

## Root Cause

Alpine.js internally uses `new Function()` to evaluate expressions like `@click="chatOpen = false"`. This is blocked by Content Security Policy unless the `'unsafe-eval'` directive is included in `script-src`.

The django-csp middleware was configured without `'unsafe-eval'`, causing the browser to block Alpine.js's expression evaluation.

## Environment

- Browser: All browsers (CSP is enforced universally)
- Django: 5.0
- Alpine.js: 3.14.3
- django-csp: 4.0+

## Fix Applied

Added `'unsafe-eval'` to the `script-src` directive in CSP settings.

### Files Modified

**config/settings/base.py** (lines 264-270):
```python
"script-src": [
    "'self'",
    "'unsafe-inline'",  # Required for HTMX and Alpine.js event handlers
    "'unsafe-eval'",    # Required for Alpine.js expression evaluation
    "unpkg.com",
    "cdn.jsdelivr.net",
],
```

**config/settings/production.py** (lines 68-74):
```python
"script-src": [
    "'self'",
    "'unsafe-inline'",
    "'unsafe-eval'",  # Required for Alpine.js expression evaluation
    "unpkg.com",
    "cdn.jsdelivr.net",
],
```

## Security Considerations

Adding `'unsafe-eval'` does reduce CSP protection against certain XSS attacks that rely on `eval()`. However, this is a necessary trade-off for using Alpine.js, which requires this capability for its core functionality.

**Mitigations in place:**
- All other CSP directives remain strict
- Django's built-in XSS protections (auto-escaping) are active
- Input validation on all user-submitted data
- CSRF protection enabled

**Alternative approaches considered:**
- Using Alpine.js CSP-compatible build (`alpinejs/csp`) - requires refactoring all inline expressions
- Switching to a different framework - significant rework required

The current approach (allowing `'unsafe-eval'`) is the standard solution used by most Alpine.js deployments.

## Verification

After applying the fix and restarting the Docker container:
1. Refresh the page
2. Click the chat widget button - should toggle open/close
3. Click the language selector - dropdown should open/close
4. Click mobile menu (on small screens) - should toggle
5. Browser console should show no CSP errors

## Lessons Learned

1. When using Alpine.js with CSP, `'unsafe-eval'` is required in `script-src`
2. CSP errors appear in browser console, not server logs
3. CSP blocks happen silently from user perspective - components just "don't work"
4. Always test interactive components after CSP configuration changes

## Related Issues

- B-004: Initial deployment debugging session
- B-005: Django template comments vs HTML comments

## Resolution

**Fixed**: December 24, 2025
**Verified**: December 24, 2025 - User confirmed fix works
