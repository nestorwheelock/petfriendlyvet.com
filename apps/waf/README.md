# WAF (Web Application Firewall) Module

A standalone Django security module providing multi-layer protection against common web attacks and data leaks.

## Features

- **Rate Limiting** - Token bucket algorithm to prevent DDoS and brute force attacks
- **Attack Pattern Detection** - SQL injection, XSS, and path traversal detection
- **Data Leak Prevention** - Blocks responses containing SSNs, credit cards, API keys
- **IP Banning** - Automatic and manual IP blocking with expiration
- **Geo-blocking** - Country-based access control (optional)
- **fail2ban Integration** - Security event logging compatible with fail2ban

## Quick Start

### Installation

1. Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    'apps.waf',
]
```

2. Add middleware (should be early in the stack):

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'apps.waf.middleware.WAFMiddleware',  # Add here
    # ...
]
```

3. Run migrations:

```bash
python manage.py migrate waf
```

### Configuration

All settings have sensible defaults. Override in `settings.py`:

```python
# Enable/disable WAF entirely
WAF_ENABLED = True

# Rate limiting
WAF_RATE_LIMIT_REQUESTS = 200  # Max requests per window
WAF_RATE_LIMIT_WINDOW = 60     # Window in seconds

# Auto-ban settings
WAF_MAX_STRIKES = 5            # Strikes before auto-ban
WAF_BAN_DURATION = 900         # Ban duration in seconds (15 min)

# Detection features
WAF_PATTERN_DETECTION = True   # SQL injection, XSS, path traversal
WAF_DATA_LEAK_DETECTION = True # SSN, credit card, API key detection

# Excluded paths (no WAF processing)
WAF_EXCLUDED_PATHS = [
    '/static/',
    '/media/',
    '/__reload__/',
    '/favicon.ico',
]

# Security logging path
WAF_LOG_PATH = '/var/log/django/security.log'
```

## Components

### Rate Limiter (`rate_limiter.py`)

Uses token bucket algorithm with Django cache backend:

```python
from apps.waf.rate_limiter import TokenBucketRateLimiter

limiter = TokenBucketRateLimiter(max_requests=100, window_seconds=60)
allowed, remaining = limiter.is_allowed('192.168.1.1')

if not allowed:
    return HttpResponse("Too many requests", status=429)
```

### Pattern Detector (`pattern_detector.py`)

Detects attack patterns in requests:

```python
from apps.waf.pattern_detector import scan_request, scan_response

# Scan incoming request
result = scan_request(request)
if result.detected:
    # result.pattern_type: 'sqli', 'xss', 'path_traversal'
    # result.matched_pattern: the pattern that triggered detection
    return HttpResponseForbidden()

# Scan outgoing response for data leaks
result = scan_response(response.content)
if result.detected:
    # result.pattern_type: 'ssn_leak', 'cc_leak', 'api_key_leak', 'email_exposure'
    return HttpResponse("Error", status=500)
```

#### Attack Patterns Detected

**SQL Injection:**
- UNION SELECT attacks
- Boolean-based attacks (`' OR '1'='1`)
- Comment injection (`--`, `#`, `/* */`)
- Function calls (SLEEP, BENCHMARK, LOAD_FILE)
- Information schema access

**XSS (Cross-Site Scripting):**
- Script tags
- Event handlers (onclick, onerror, onload)
- JavaScript/VBScript protocol handlers
- Expression evaluation (eval, expression())
- DOM manipulation (document.cookie, window.location)

**Path Traversal:**
- Directory traversal (`../`, `..\`)
- URL-encoded variants (`%2e%2e%2f`)
- Null byte injection (`%00`)
- System file access (`/etc/passwd`, `c:\boot.ini`)

#### Data Leak Detection

**Social Security Numbers:**
- Format: `XXX-XX-XXXX`
- Validates against invalid SSN ranges
- Filters obvious fakes (all zeros, sequential)

**Credit Cards:**
- Visa, Mastercard, Amex, Discover
- Validates with Luhn algorithm
- Supports formatted and unformatted

**API Keys/Secrets:**
- AWS access keys (AKIA...)
- Generic API key patterns
- Bearer tokens

**Email Exposure:**
- Detects mass email dumps (5+ unique emails)

### Security Logger (`security_logger.py`)

Logs security events in fail2ban-compatible format:

```python
from apps.waf.security_logger import (
    log_failed_login,
    log_invalid_token,
    log_rate_limit,
    log_pattern_detected,
    log_ip_banned,
)

# Log a failed login
log_failed_login('192.168.1.1', '/login/', username='admin')

# Output: 2025-12-26 10:15:23 [SECURITY] FAILED_LOGIN ip=192.168.1.1 path=/login/ username=admin
```

### Models (`models.py`)

**WAFConfig** - Singleton configuration model:
```python
from apps.waf.models import WAFConfig

config = WAFConfig.get_config()
config.rate_limit_requests = 100
config.save()
```

**BannedIP** - IP ban management:
```python
from apps.waf.models import BannedIP

# Check if IP is banned
ban = BannedIP.objects.filter(ip_address='192.168.1.1').first()
if ban and ban.is_active:
    # IP is banned

# Unban an IP
BannedIP.objects.filter(ip_address='192.168.1.1').delete()
```

**SecurityEvent** - Security event log (read-only):
```python
from apps.waf.models import SecurityEvent

recent_events = SecurityEvent.objects.filter(
    event_type='sqli'
).order_by('-created_at')[:100]
```

**AllowedCountry** - Geo-blocking whitelist:
```python
from apps.waf.models import AllowedCountry

AllowedCountry.objects.create(
    country_code='US',
    country_name='United States'
)
```

## fail2ban Integration

### Filter Configuration

Copy `conf/fail2ban-filter.conf` to `/etc/fail2ban/filter.d/django-waf.conf`:

```ini
[Definition]
failregex = \[SECURITY\]\s+(FAILED_LOGIN|INVALID_TOKEN|RATE_LIMIT|PATTERN_DETECTED|BANNED_ACCESS|GEO_BLOCKED|DATA_LEAK_BLOCKED)\s+ip=<HOST>
ignoreregex =
datepattern = ^%%Y-%%m-%%d %%H:%%M:%%S
```

### Jail Configuration

Copy `conf/fail2ban-jail.conf` to `/etc/fail2ban/jail.d/django-waf.conf`:

```ini
[django-waf]
enabled = true
port = http,https
filter = django-waf
logpath = /var/log/django/security.log
maxretry = 5
findtime = 300
bantime = 3600
```

### Testing fail2ban

```bash
# Test filter regex against log
fail2ban-regex /var/log/django/security.log /etc/fail2ban/filter.d/django-waf.conf

# Check jail status
fail2ban-client status django-waf

# Manually ban/unban for testing
fail2ban-client set django-waf banip 192.168.1.100
fail2ban-client set django-waf unbanip 192.168.1.100
```

## Middleware Flow

```
Request
   ↓
WAFMiddleware.__call__()
   ↓
[Skip if disabled or excluded path]
   ↓
Check IP ban (cache + database)
   ↓ Banned → 403 Forbidden
   ↓
Rate limiting check
   ↓ Exceeded → 429 + record strike
   ↓
Pattern detection (path, query, body)
   ↓ Detected → 403 + record strike
   ↓
Pass to next middleware/view
   ↓
Response received
   ↓
Data leak detection (response body)
   ↓ Detected → 500 + log event
   ↓
Add rate limit headers
   ↓
Return response
```

## Strike System

Each security violation records a "strike" against the IP:

1. First strike: Logged only
2. Subsequent strikes: Logged
3. At `WAF_MAX_STRIKES`: Auto-ban for `WAF_BAN_DURATION`

Strike counts are stored in cache with automatic expiration.

## Django Admin

The module provides Django admin interfaces for:

- **WAF Configuration** - Edit settings
- **Banned IPs** - View, add, remove bans
- **Allowed Countries** - Manage geo-blocking whitelist
- **Security Events** - Read-only log viewer with export

## Testing

Run WAF tests:

```bash
pytest tests/test_waf.py -v
```

Test coverage includes:
- Rate limiter (token bucket algorithm)
- Pattern detection (all attack types)
- Data leak detection (SSN, CC, API keys)
- Security logging
- Middleware flow
- Database models

## Performance Considerations

- **Cache dependency**: Rate limiting uses Django cache; configure Redis or Memcached in production
- **Regex compilation**: Attack patterns are pre-compiled for performance
- **Response scanning**: Only scans text content types under 1MB
- **Database queries**: Ban checks use cache-first strategy

## Security Best Practices

1. **Place WAF middleware early** in the stack (after SecurityMiddleware)
2. **Use Redis/Memcached** for cache in production
3. **Configure fail2ban** for additional OS-level protection
4. **Monitor security logs** regularly
5. **Adjust rate limits** based on your traffic patterns
6. **Review and unban** legitimate IPs that get caught

## Troubleshooting

### "An error occurred processing your request"

This message appears when data leak detection blocks a response. Check:
- Is the response accidentally containing test SSNs or credit card numbers?
- Disable with `WAF_DATA_LEAK_DETECTION = False` for debugging

### Rate limiting too aggressive

Increase limits:
```python
WAF_RATE_LIMIT_REQUESTS = 500
WAF_RATE_LIMIT_WINDOW = 60
```

### False positives in pattern detection

Check the matched pattern in security logs. If legitimate, consider:
- Adding path to `WAF_EXCLUDED_PATHS`
- Submitting a bug report for pattern refinement

### fail2ban not banning IPs

1. Verify log path matches configuration
2. Test filter regex with `fail2ban-regex`
3. Check fail2ban service status: `systemctl status fail2ban`
4. Review fail2ban logs: `/var/log/fail2ban.log`
