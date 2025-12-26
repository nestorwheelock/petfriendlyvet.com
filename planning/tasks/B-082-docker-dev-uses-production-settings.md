# B-082: Docker Dev Environment Uses Production Settings

**Severity**: Medium
**Affected Component**: Docker/WhiteNoise/Static Files
**Discovered**: 2025-12-26

## Bug Description

The Docker development environment uses production settings (`config.settings.production`), which causes WhiteNoise to cache static files at container startup. This prevents CSS changes from being reflected even when the static directory is properly mounted.

## Steps to Reproduce

1. Start Docker with `docker-compose up -d`
2. Make a CSS change (e.g., `npm run build`)
3. Refresh browser
4. Observe: CSS changes are NOT reflected

## Expected Behavior

CSS changes compiled by `npm run dev` or `npm run build` should be immediately visible in the browser after a page refresh.

## Actual Behavior

CSS changes are not visible because:
1. `docker-compose.yml` sets `DJANGO_SETTINGS_MODULE=config.settings.production`
2. Production settings use `STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'`
3. WhiteNoise caches the static file manifest at container startup
4. Even with `./static:/app/static:ro` mount, WhiteNoise serves from cache

## Root Cause

```yaml
# docker-compose.yml line 9
environment:
  - DJANGO_SETTINGS_MODULE=config.settings.production  # <-- Problem
```

WhiteNoise's `CompressedManifestStaticFilesStorage` is optimized for production and caches file hashes. It doesn't check for file changes after startup.

## Proposed Fix

**Option A: Use development settings in Docker (Recommended)**

Update `docker-compose.override.yml`:
```yaml
services:
  web:
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.development
      - DJANGO_DEBUG=True
    volumes:
      - ./static:/app/static:ro
```

Development settings use `StaticFilesStorage` which doesn't cache.

**Option B: Disable WhiteNoise middleware in development**

Add to `docker-compose.override.yml`:
```yaml
services:
  web:
    environment:
      - WHITENOISE_AUTOREFRESH=true  # (if WhiteNoise supports this)
```

**Option C: Remove WhiteNoise from middleware in dev**

Modify `development.py` to remove WhiteNoise middleware and use Django's built-in static file serving.

## Impact

- CSS/theme development requires Docker rebuild (30+ seconds per change)
- Frontend development velocity significantly reduced
- The `docker-compose.override.yml` created in T-081 is not fully effective

## Related Tasks

- T-081: Docker CSS Dev Workflow - created override file but issue persists
- Superadmin theme not appearing (symptoms of this bug)

## Definition of Done

- [x] Docker dev environment uses development settings
- [x] WhiteNoise does not cache in development mode
- [x] CSS changes visible without Docker restart (verified 2025-12-26)
- [ ] Production deployment still works correctly
- [ ] Tests pass
- [ ] Committed and pushed

## Fix Applied

Updated `docker-compose.override.yml` to set:
```yaml
environment:
  - DJANGO_SETTINGS_MODULE=config.settings.development
```

Docker logs now show: `using settings 'config.settings.development'`
