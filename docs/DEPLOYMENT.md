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
