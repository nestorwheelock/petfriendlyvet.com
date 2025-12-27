# T-081: Improve Docker CSS Development Workflow

> **REQUIRED READING:** Before implementation, review [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)

**Related Story**: Infrastructure Improvement
**Estimate**: 1 hour
**Status**: In Progress
**Dependencies**: None

## Problem Statement

Currently, CSS/theme changes require a full Docker image rebuild to be reflected in the dev environment. This creates friction during frontend development:

1. Edit CSS locally (`npm run build`)
2. Must run `docker-compose build web` (~30 seconds)
3. Must run `docker-compose up -d` to deploy new image
4. Only then are changes visible

This slows down CSS/theme iteration significantly.

## Objective

Create a development-friendly Docker configuration that allows instant CSS changes without rebuilding the Docker image.

## Deliverables

1. **`docker-compose.override.yml`** - Dev override that mounts static files
2. **Updated `docs/DEPLOYMENT.md`** - Document both workflows
3. **Updated deploy scripts** (if applicable) - Ensure production still bakes CSS

## Implementation

### docker-compose.override.yml

This file is automatically loaded by docker-compose and overrides settings for development:

```yaml
# Development overrides - mounts static files for instant CSS changes
# This file is auto-loaded by docker-compose alongside docker-compose.yml
version: '3.8'

services:
  web:
    volumes:
      - ./static:/app/static:ro
    environment:
      - DJANGO_DEBUG=True
```

### Workflow Documentation

**For CSS Development:**
```bash
npm run dev              # Watch and compile CSS changes
docker-compose up -d     # Start services (override auto-applied)
# CSS changes are instant - just refresh browser
```

**For Production Deploy:**
```bash
npm run build                              # Compile CSS
docker-compose -f docker-compose.yml build # Build WITHOUT override
docker-compose -f docker-compose.yml up -d # Deploy WITHOUT override
```

## Definition of Done

- [x] Task document created
- [x] docker-compose.override.yml created
- [x] DEPLOYMENT.md updated with both workflows
- [x] Verified CSS changes work without rebuild
- [ ] Committed and pushed

## Notes

- The override file is NOT used when explicitly specifying `-f docker-compose.yml`
- Production deployments should always use explicit `-f` flag to avoid override
- The override should be committed to git so all developers get the same experience
