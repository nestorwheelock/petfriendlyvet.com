# Security Implementation Guide

## Overview

This document provides security implementation guidance for the Pet-Friendly Veterinary Clinic web application. It covers security controls, configuration requirements, and best practices for maintaining a secure deployment.

---

## Security Architecture

### Defense in Depth

The application implements multiple layers of security:

```
┌─────────────────────────────────────────────────────────┐
│                    CDN/WAF Layer                        │
│              (Cloudflare - DDoS protection)             │
├─────────────────────────────────────────────────────────┤
│                    Web Server                           │
│           (Nginx - TLS, rate limiting, CSP)             │
├─────────────────────────────────────────────────────────┤
│                  Application Layer                      │
│    (Django - CSRF, XSS, SQL injection protection)       │
├─────────────────────────────────────────────────────────┤
│                   Database Layer                        │
│          (PostgreSQL - encrypted, isolated)             │
└─────────────────────────────────────────────────────────┘
```

---

## Security Controls

### Authentication & Authorization

| Control | Implementation | Location |
|---------|----------------|----------|
| Session Management | Django sessions | `config/settings/base.py` |
| Password Hashing | PBKDF2 (Django default) | Django auth |
| Role-Based Access | Custom User model roles | `apps/accounts/models.py` |
| OAuth Integration | Google OAuth 2.0 | `apps/accounts/` |

**Configuration:**

```python
# Session security
SESSION_COOKIE_SECURE = True  # HTTPS only
SESSION_COOKIE_HTTPONLY = True  # No JavaScript access
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# CSRF protection
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
```

### Input Validation

| Attack | Protection | Notes |
|--------|------------|-------|
| SQL Injection | Django ORM | All queries parameterized |
| XSS | Template auto-escaping | `{% autoescape on %}` default |
| CSRF | Token validation | `{% csrf_token %}` required |
| File Upload | Type/size validation | `apps/accounts/validators.py` |

### Stored Procedures - When NOT to Use Them

**Question**: Should we use stored procedures for forms like the contact form to add extra SQL injection protection?

**Answer**: No, stored procedures are **not recommended** for this Django application.

#### Why Stored Procedures Are Not Needed

1. **Django ORM Already Prevents SQL Injection**
   - All Django ORM queries use parameterized statements
   - User input is never interpolated directly into SQL
   - The ORM handles escaping automatically

2. **Example - Django's Built-in Protection**
   ```python
   # SAFE - Django automatically parameterizes this
   ContactSubmission.objects.create(
       name=user_input_name,
       email=user_input_email,
       message=user_input_message
   )

   # Results in: INSERT INTO ... VALUES ($1, $2, $3)
   # NOT: INSERT INTO ... VALUES ('user_input')
   ```

3. **When Stored Procedures Make Sense**
   - Legacy databases with existing stored procedure architecture
   - Complex multi-table transactions requiring database-level atomicity
   - Performance-critical batch operations with large datasets
   - When database logic must be shared across multiple applications
   - Regulatory requirements mandating database-level access control

4. **Why Stored Procedures Are Overkill Here**
   - Django ORM provides equivalent SQL injection protection
   - Adds database vendor lock-in (PostgreSQL-specific)
   - Makes code harder to test and maintain
   - Splits business logic between application and database
   - Complicates migrations and deployments
   - No additional security benefit over parameterized queries

#### Best Practice for Django Applications

**Use the ORM correctly:**
```python
# CORRECT - Always use ORM methods
Model.objects.filter(field=user_input)
Model.objects.create(**validated_data)

# DANGEROUS - Never do this
Model.objects.raw(f"SELECT * FROM table WHERE field = '{user_input}'")
cursor.execute(f"DELETE FROM table WHERE id = {user_input}")
```

**If you must use raw SQL:**
```python
# SAFE - Use parameterized queries
Model.objects.raw("SELECT * FROM table WHERE field = %s", [user_input])
cursor.execute("DELETE FROM table WHERE id = %s", [user_input])
```

---

### Rate Limiting

API endpoints are protected by rate limiting:

| Endpoint | Anonymous | Authenticated |
|----------|-----------|---------------|
| `/chat/` | 10/min per IP | 50/hour per user |
| `/api/*` | 30/min per IP | 100/hour per user |
| `/contact/` | 5/min per IP | 10/min per user |

**Implementation:** `apps/ai_assistant/decorators.py`

### Content Security Policy

CSP headers restrict resource loading:

```python
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "unpkg.com", "cdn.jsdelivr.net")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "fonts.googleapis.com")
CSP_FONT_SRC = ("'self'", "fonts.gstatic.com")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FRAME_ANCESTORS = ("'none'",)
```

---

## Secrets Management

### Environment Variables

All secrets stored in environment variables:

```bash
# Required secrets
SECRET_KEY=<django-secret-key>
DATABASE_URL=postgres://user:pass@host/db
OPENROUTER_API_KEY=<api-key>

# Optional
GOOGLE_OAUTH_CLIENT_ID=<client-id>
GOOGLE_OAUTH_CLIENT_SECRET=<secret>
```

### Never Commit

These should never be in version control:
- `.env` files
- API keys
- Database credentials
- SSL certificates
- Private keys

---

## Production Checklist

### Django Settings

```python
# Production requirements
DEBUG = False
ALLOWED_HOSTS = ['petfriendlyvet.com', 'www.petfriendlyvet.com']
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

### Nginx Configuration

```nginx
# SSL configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_prefer_server_ciphers on;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;

# Security headers
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;

# Rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req zone=api burst=20 nodelay;
```

---

## Monitoring & Logging

### Security Events to Log

- Authentication failures
- Authorization denials
- Rate limit violations
- Input validation failures
- Error responses (500s)
- Admin actions

### Log Format

```python
LOGGING = {
    'handlers': {
        'security': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/petfriendlyvet/security.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
        },
    },
    'loggers': {
        'security': {
            'handlers': ['security'],
            'level': 'WARNING',
        },
    },
}
```

---

## Incident Response

### If a Security Issue is Found

1. **Contain** - Disable affected functionality
2. **Assess** - Determine scope and impact
3. **Remediate** - Fix the vulnerability
4. **Notify** - Inform affected users if data breach
5. **Review** - Update security controls

### Contact

Security issues should be reported to:
- Email: security@petfriendlyvet.com
- Response time: 24-48 hours

---

## Compliance

### Data Protection

- Personal data encrypted at rest
- HTTPS for all data in transit
- Minimal data collection
- Clear privacy policy
- User data export capability

### OWASP Top 10 Coverage

| Risk | Status | Implementation |
|------|--------|----------------|
| A01: Broken Access Control | ✅ | Role-based access |
| A02: Cryptographic Failures | ✅ | TLS, hashed passwords |
| A03: Injection | ✅ | ORM, parameterized queries |
| A04: Insecure Design | ✅ | Security by design |
| A05: Security Misconfiguration | ✅ | Hardened settings |
| A06: Vulnerable Components | ⚠️ | Regular updates needed |
| A07: Auth Failures | ✅ | Session management |
| A08: Data Integrity Failures | ✅ | Input validation |
| A09: Logging Failures | ✅ | Security logging |
| A10: SSRF | ✅ | No user-controlled URLs |

---

## Security Testing

### Running Security Tests

```bash
# Run security test suite
pytest tests/test_security.py -v

# Run with coverage
pytest tests/test_security.py --cov=apps --cov-report=term-missing
```

### Manual Testing

- [ ] Test authentication flows
- [ ] Verify authorization controls
- [ ] Check rate limiting
- [ ] Validate input handling
- [ ] Review error messages
- [ ] Check security headers

---

## Updates & Maintenance

### Regular Tasks

- **Weekly**: Review security logs
- **Monthly**: Update dependencies
- **Quarterly**: Security audit
- **Annually**: Penetration test

### Dependency Updates

```bash
# Check for vulnerable packages
pip-audit

# Update packages
pip install --upgrade -r requirements/production.txt
```

---

*Last Updated: December 23, 2025*
