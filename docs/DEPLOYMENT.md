# Deployment Guide

## Server Requirements

### System Packages

The following packages must be installed on the production server:

```bash
# Docker (required for containerized deployment)
sudo apt-get install docker.io docker-compose-plugin

# ImageMagick (for image format conversion)
sudo apt-get install imagemagick

# Nginx (reverse proxy)
sudo apt-get install nginx
```

### Python Dependencies

Listed in `requirements/production.txt`. Key packages:
- Django 5.2.x
- Pillow (image processing for Django ImageField)
- WhiteNoise (static file serving)
- Gunicorn (WSGI server)

### Image Processing

For image format conversion (JPG to PNG, resizing):
- **Runtime**: Pillow is included in Python dependencies
- **Server tools**: ImageMagick for command-line conversion

Example ImageMagick usage:
```bash
# Convert JPG to PNG
convert input.jpg output.png

# Resize to favicon size (64x64)
convert input.jpg -resize 64x64 favicon.png
```

## Development Workflow

### CSS/Tailwind Development

The project uses Tailwind CSS with DaisyUI for styling. CSS is compiled from `static/css/input.css` to `static/css/output.css`.

**Development (instant CSS changes):**
```bash
# Start Tailwind in watch mode (recompiles on file changes)
npm run dev

# Start Docker services (override auto-applied for live mounting)
docker-compose up -d

# CSS changes are instant - just refresh browser
```

**How it works:** The `docker-compose.override.yml` file is automatically loaded by docker-compose and mounts the local `static/` directory into the container. This means CSS changes compiled by `npm run dev` are immediately visible without rebuilding Docker.

**Production build (baked into image):**
```bash
# Compile and minify CSS
npm run build

# Build WITHOUT the override (uses explicit -f flag)
docker-compose -f docker-compose.yml build

# Deploy WITHOUT the override
docker-compose -f docker-compose.yml up -d
```

### Docker Compose Override Behavior

The `docker-compose.override.yml` file provides development-friendly settings:
- Mounts `./static:/app/static:ro` for instant CSS changes
- Sets `DJANGO_DEBUG=True` for development

**Important:** This override is auto-loaded when you run `docker-compose up` without specifying a file. For production deployments, always use the explicit `-f docker-compose.yml` flag to bypass the override.

## Docker Deployment

### Build and Run

```bash
# Build the image
docker compose -f docker-compose.prod.yml build

# Run the container
docker compose -f docker-compose.prod.yml up -d
```

### Environment Variables

Required environment variables (set in `.env.prod`):
- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `SCRIPT_NAME` (for subdirectory deployment, e.g., `/dev`)
- `DATABASE_URL`

### Static Files

Static files are served by WhiteNoise from within the Docker container.

The `static/` folder is:
- **Not tracked by git** (in `.gitignore`)
- **Included in Docker build** (not in `.dockerignore`)
- **Collected at build time** via `collectstatic`

To update static files:
1. Update files in local `static/` folder
2. Rebuild Docker image
3. Restart container

### Subdirectory Deployment

To deploy under a URL prefix (e.g., `petfriendlyvet.com/dev`):

1. Set `SCRIPT_NAME=/dev` in environment
2. Configure nginx with `^~` location priority:

```nginx
location ^~ /dev/ {
    proxy_pass http://127.0.0.1:7777;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### SSL/TLS Configuration

When behind an SSL-terminating proxy (nginx), add to Django settings:

```python
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
```

## Security Features (v2.0.0)

### Dynamic URL System

Admin and staff URLs are obfuscated with session-based tokens:

| URL Pattern | Access |
|-------------|--------|
| `/admin/` | Returns 404 (blocked) |
| `/panel-{admin_token}/` | Django admin (superusers only) |
| `/accounting/`, `/inventory/`, etc. | Returns 404 (blocked) |
| `/staff-{staff_token}/section/module/` | Staff portal access |

**How it works:**
1. User logs in
2. Session generates unique tokens (admin_token for superusers, staff_token for staff)
3. User accesses protected areas via token URLs
4. Middleware validates token matches session
5. Tokens invalidate on logout/session expiry

**Staff URL Sections:**
- `/staff-{token}/operations/` - Practice, Inventory, Referrals, Delivery
- `/staff-{token}/customers/` - CRM, Marketing
- `/staff-{token}/finance/` - Accounting, Reports
- `/staff-{token}/admin-tools/` - Audit, AI Chat

### WAF (Web Application Firewall)

The WAF module provides request-level security:

| Feature | Production Setting |
|---------|-------------------|
| Rate limiting | 100 req/min per IP |
| Ban threshold | 5 strikes |
| Ban duration | 1 hour |
| Pattern detection | SQL injection, XSS, path traversal |
| Data leak detection | Credit cards, SSNs, API keys |

**fail2ban Integration:**

For VPS deployments, configure fail2ban:

```bash
# Copy filter and jail configs
sudo cp apps/waf/conf/fail2ban-filter.conf /etc/fail2ban/filter.d/django-waf.conf
sudo cp apps/waf/conf/fail2ban-jail.conf /etc/fail2ban/jail.d/django.conf

# Restart fail2ban
sudo systemctl restart fail2ban
```

### Module Activation System

Enable/disable entire app modules from superadmin:

1. Access `/panel-{admin_token}/` → Django admin
2. Or use superadmin interface at `/superadmin/modules/`
3. Toggle modules on/off
4. Disabled modules return 404 and hide from navigation

### Feature Flags

Granular control over individual features:

```python
# In views
from apps.core.feature_flags import is_enabled, require_feature

if is_enabled('sms_notifications'):
    send_sms()

@require_feature('advanced_reporting')
def advanced_report_view(request):
    ...
```

```html
<!-- In templates -->
{% load feature_flags %}
{% if_feature "dark_mode" %}
  <button>Toggle Dark Mode</button>
{% endif_feature %}
```

## Troubleshooting

### Static Files 404

1. Ensure static files are in Docker build context
2. Rebuild image after adding new files
3. WhiteNoise caches file list at startup - restart container after adding files

### HTMX Indicator Blocking Clicks

Add to CSS:
```css
.htmx-indicator {
  opacity: 0;
  pointer-events: none;
}
.htmx-request .htmx-indicator {
  opacity: 1;
  pointer-events: auto;
}
```
