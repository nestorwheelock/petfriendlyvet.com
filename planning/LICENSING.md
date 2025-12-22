# Commercial Licensing System

## Overview

Pet-Friendly Veterinary software uses a commercial source-available license with Rust-based license validation.

**Public Repository**: Code is visible on GitHub for transparency
**Commercial Use**: Requires a paid license from South City Computer
**Enforcement**: Rust binary validates license at Django bootstrap

---

## License Types

| Type | Max Users | Features | Use Case |
|------|-----------|----------|----------|
| **Trial** | 1 | Basic only | 30-day evaluation |
| **Single** | 5 | Full features | Single clinic location |
| **Multi** | 20 | Full + multi-location | Multiple clinic locations |
| **Enterprise** | Unlimited | All features | Large organizations |
| **Developer** | 2 | All + dev_mode | Development/testing |

---

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────┐
│  Django Application                                 │
│                                                     │
│  AppConfig.ready() or settings.py                   │
│    │                                                │
│    └──► license.validate()                          │
│           │                                         │
│           └──► subprocess: scc-license license.key  │
│                    │                                │
│                    ▼                                │
│           ┌────────────────────────┐                │
│           │  Rust Binary           │                │
│           │  (compiled, stripped)  │                │
│           │                        │                │
│           │  - Read license.key    │                │
│           │  - Verify signature    │                │
│           │  - Check expiry        │                │
│           │  - Check domain        │                │
│           │  - Return JSON or exit │                │
│           └────────────────────────┘                │
│                    │                                │
│                    ▼                                │
│           Valid: Continue startup                   │
│           Invalid: Raise LicenseError, exit         │
└─────────────────────────────────────────────────────┘
```

### License File Format

```json
{
  "version": 1,
  "payload": "base64_encoded_license_info",
  "signature": "sha256_signature_hex"
}
```

### Decoded Payload

```json
{
  "licensee": "Dr. Pablo Rojo Mendoza",
  "email": "pablo@petfriendlyvet.com",
  "license_type": "single",
  "issued_at": "2025-12-22T00:00:00Z",
  "expires_at": "2026-12-22T00:00:00Z",
  "domains": ["petfriendlyvet.com", "localhost"],
  "features": ["basic", "appointments", "ecommerce"],
  "max_users": 5
}
```

---

## Rust Components

### Location

```
rust/
└── scc-license/
    ├── Cargo.toml
    ├── src/
    │   ├── main.rs           # License validator (scc-license)
    │   └── bin/
    │       └── generate.rs   # License generator (scc-license-generate)
    └── target/
        └── release/
            ├── scc-license           # Validator binary
            └── scc-license-generate  # Generator binary
```

### Build

```bash
cd rust/scc-license
cargo build --release

# Binaries in target/release/
```

### Usage

**Validate a license:**
```bash
./scc-license license.key
./scc-license license.key petfriendlyvet.com  # With domain check
```

**Generate a license:**
```bash
./scc-license-generate \
  --licensee "Dr. Pablo" \
  --email "pablo@clinic.com" \
  --type single \
  --domains "petfriendlyvet.com,localhost" \
  --days 365 \
  --output license.key
```

---

## Django Integration

### Python Wrapper

```python
# core/license.py
import json
import subprocess
import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured

class LicenseError(ImproperlyConfigured):
    """Raised when license validation fails."""
    pass

class LicenseInfo:
    def __init__(self, data: dict):
        self.licensee = data['licensee']
        self.email = data['email']
        self.license_type = data['license_type']
        self.expires_at = data['expires_at']
        self.domains = data['domains']
        self.features = data['features']
        self.max_users = data.get('max_users')

    def has_feature(self, feature: str) -> bool:
        return 'all' in self.features or feature in self.features

def validate_license(license_path: str = None, domain: str = None) -> LicenseInfo:
    """
    Validate license using Rust binary.
    Called during Django startup.
    """
    if license_path is None:
        license_path = os.environ.get('SCC_LICENSE_FILE', 'license.key')

    # Find the Rust binary
    binary = _find_license_binary()

    # Build command
    cmd = [binary, license_path]
    if domain:
        cmd.append(domain)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5
        )
    except FileNotFoundError:
        raise LicenseError(
            "License validator binary not found. "
            "Run: cd rust/scc-license && cargo build --release"
        )
    except subprocess.TimeoutExpired:
        raise LicenseError("License validation timed out")

    if result.returncode != 0:
        raise LicenseError(result.stderr.strip())

    try:
        data = json.loads(result.stdout)
        return LicenseInfo(data)
    except json.JSONDecodeError:
        raise LicenseError("Invalid license validator response")

def _find_license_binary() -> str:
    """Find the scc-license binary."""
    # Check common locations
    locations = [
        Path(__file__).parent.parent / 'rust' / 'scc-license' / 'target' / 'release' / 'scc-license',
        Path('/usr/local/bin/scc-license'),
        Path.home() / '.local' / 'bin' / 'scc-license',
    ]

    for loc in locations:
        if loc.exists():
            return str(loc)

    # Try PATH
    return 'scc-license'
```

### Settings Integration

```python
# config/settings/base.py
from core.license import validate_license, LicenseError

# Validate license at startup
try:
    LICENSE = validate_license(
        domain=os.environ.get('ALLOWED_HOST', 'localhost')
    )
    print(f"✓ License valid for: {LICENSE.licensee}")
    print(f"  Type: {LICENSE.license_type}")
    print(f"  Expires: {LICENSE.expires_at}")
except LicenseError as e:
    print("=" * 60)
    print("LICENSE ERROR")
    print("=" * 60)
    print(str(e))
    print()
    print("This software requires a valid commercial license.")
    print("Contact: nestor@southcitycomputer.com")
    print("=" * 60)
    raise
```

### Feature Gating

```python
# In views or middleware
from django.conf import settings

def some_view(request):
    if not settings.LICENSE.has_feature('ecommerce'):
        raise PermissionDenied("E-commerce feature not licensed")
    # ... rest of view
```

---

## Security Considerations

### Why Rust?

1. **Compiled binary** - Can't just edit Python to skip validation
2. **Stripped symbols** - Harder to reverse engineer
3. **No runtime dependencies** - No Python interpreter needed
4. **Fast startup** - Minimal impact on Django boot time

### What It Protects Against

- ✅ Casual copying without license
- ✅ Running on unlicensed domains
- ✅ Using expired licenses
- ✅ Feature access without proper tier

### What It Doesn't Protect Against

- ❌ Determined reverse engineering (nothing does)
- ❌ Patching the binary
- ❌ Running with LICENSE checks removed from Django code

### Philosophy

The goal is **honest licensing**, not perfect DRM. We:
- Make it clear a license is required
- Make it easy to comply
- Make it inconvenient (not impossible) to circumvent
- Trust that clients who want support will pay

---

## Generating Client Licenses

### Quick Generate

```bash
cd rust/scc-license

# Build if needed
cargo build --release

# Generate license
./target/release/scc-license-generate \
  --licensee "Pet-Friendly Veterinaria" \
  --email "vetpetfriendly@gmail.com" \
  --type single \
  --domains "petfriendlyvet.com,www.petfriendlyvet.com,localhost" \
  --days 365 \
  --output ~/licenses/petfriendly-2025.key
```

### License Delivery

1. Generate license key file
2. Send to client via secure channel (email, portal)
3. Client places `license.key` in project root (or sets `SCC_LICENSE_FILE` env var)
4. Django validates on startup

---

## Pricing Tiers (Suggested)

| Tier | Annual | Includes |
|------|--------|----------|
| **Single** | $500 | 1 location, 5 users, email support |
| **Multi** | $1,200 | Up to 5 locations, 20 users, priority support |
| **Enterprise** | Custom | Unlimited, SLA, customization |

---

## Files

| File | Purpose |
|------|---------|
| `LICENSE` | Public license text in repo root |
| `license.key` | Client's license file (gitignored) |
| `rust/scc-license/` | Rust license validator source |
| `core/license.py` | Django integration (to be created in Epoch 1) |

---

*Last Updated: December 2025*
