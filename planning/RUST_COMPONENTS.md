# Rust Components Strategy

## Business Model: Modular Licensing

Each Rust component is:
1. **Standalone pip package** (e.g., `pip install scc-crypto`)
2. **Independently licensable** (buy only what you need)
3. **Portable** (works with any Django/Python project)
4. **Bundled in Pet-Friendly** (full suite included)

### Pricing Strategy

| Component | Standalone | Bundle |
|-----------|------------|--------|
| scc-license | Free (required) | Included |
| scc-crypto | $99/year | Included |
| scc-image | $149/year | Included |
| scc-pdf | $199/year | Included |
| scc-search | $149/year | Included |
| scc-export | $99/year | Included |
| scc-ai | $199/year | Included |
| **All Components** | $893/year | **$499/year** |
| **Pet-Friendly Full** | - | **$999/year** (app + components) |

### Package Names (PyPI)

```
scc-license      → Free, required for all others
scc-crypto       → southcity-crypto
scc-image        → southcity-image
scc-pdf          → southcity-pdf
scc-search       → southcity-search
scc-export       → southcity-export
scc-ai           → southcity-ai
```

---

## Goal

Embed Rust binaries throughout the application that:
1. **Provide real value** (speed, security)
2. **Contain license checks** (quietly verify on each call)
3. **Are essential** (app breaks without them)
4. **Are annoying to replace** (another dev says "fuck it" and buys license)

---

## Strategic Placement Analysis

### Django Request Lifecycle - Where Rust Can Hook

```
Request → Middleware → URL Router → View → Template → Response
            ↓            ↓           ↓        ↓
         [RUST]       [RUST]      [RUST]   [RUST]

Background: Celery Task → Worker → Result
                           ↓
                        [RUST]
```

### By Application Layer

| Layer | What Happens | Rust Opportunity | Value Add |
|-------|--------------|------------------|-----------|
| **Middleware** | Auth, sessions, CORS | Token validation, rate limiting | Speed, security |
| **Models** | Data validation, save/load | Field encryption, audit hashing | Security |
| **Views** | Business logic | Heavy computation | Speed |
| **Templates** | Rendering | PDF/document generation | Speed |
| **Tasks** | Background jobs | Image processing, reports | Speed |
| **API** | Serialization | JSON parsing, validation | Speed |

---

## Proposed Rust Components

### 1. scc-license (Already Created)
**Purpose:** Primary license validation at startup
**Location:** `rust/scc-license/`
**Called From:** Django settings.py
**If Missing:** App won't start

---

### 2. scc-crypto
**Purpose:** Encryption & security operations
**Legitimate Value:**
- Encrypt sensitive pet medical data at rest
- Sign PDF documents and certificates
- Hash passwords (faster than Python bcrypt)
- Generate secure tokens

**Hidden Check:** Every encrypt/decrypt call verifies license

**Called From:**
- User authentication (password hashing)
- Medical records (field encryption)
- Document signing (travel certificates)
- Session management

**If Missing:** Can't log in, can't save medical records

```rust
// Example API
pub fn encrypt_field(plaintext: &str, key: &[u8]) -> Result<String, Error> {
    verify_license()?;  // Silent check
    // ... actual encryption
}
```

**Django Integration:**
```python
# core/crypto.py
from scc_crypto import encrypt_field, decrypt_field, hash_password

class EncryptedTextField(models.TextField):
    def get_prep_value(self, value):
        return encrypt_field(value, settings.FIELD_ENCRYPTION_KEY)
```

---

### 3. scc-image
**Purpose:** Image processing
**Legitimate Value:**
- Thumbnail generation (10-50x faster than Pillow)
- Image resizing for web
- EXIF stripping (privacy)
- Format conversion (HEIC → JPEG for Apple photos)

**Hidden Check:** Returns watermarked/degraded images if unlicensed

**Called From:**
- Pet photo uploads
- Document scans
- Product images
- Gallery thumbnails

**If Missing:** Pet photos don't display properly

```rust
pub fn generate_thumbnail(input: &[u8], size: u32) -> Result<Vec<u8>, Error> {
    let license = check_license();
    let thumb = resize_image(input, size)?;

    if !license.valid {
        return add_watermark(thumb, "UNLICENSED");
    }
    Ok(thumb)
}
```

---

### 4. scc-pdf
**Purpose:** PDF document generation
**Legitimate Value:**
- Invoices and receipts
- Travel health certificates
- Medical record exports
- Prescription labels
- Reports

**Hidden Check:** Adds watermark or limits pages if unlicensed

**Called From:**
- Billing system (invoices)
- Travel certificates (S-022)
- Medical exports
- Reports (S-017)

**If Missing:** Can't generate any documents

```rust
pub fn generate_invoice(data: &InvoiceData) -> Result<Vec<u8>, Error> {
    let license = check_license();
    let mut pdf = create_pdf(data)?;

    if !license.valid {
        pdf.add_watermark("DEMO - UNLICENSED SOFTWARE");
    }
    Ok(pdf.to_bytes())
}
```

---

### 5. scc-search
**Purpose:** Fast text search and fuzzy matching
**Legitimate Value:**
- Search pets by name (fuzzy: "Luna" finds "Lunita")
- Search products
- Search medical history
- Autocomplete

**Hidden Check:** Rate limits or returns partial results if unlicensed

**Called From:**
- Global search
- Pet lookup
- Product search
- AI context retrieval

**If Missing:** Search is broken/slow

---

### 6. scc-export
**Purpose:** Data export to CSV/Excel
**Legitimate Value:**
- Export client lists
- Export inventory
- Export financial reports
- Bulk data downloads

**Hidden Check:** Limits to 100 rows if unlicensed

**Called From:**
- Reports (S-017)
- Inventory management (S-024)
- CRM exports (S-007)
- Accounting (S-026)

**If Missing:** Can't export data

---

### 7. scc-ai
**Purpose:** AI integration helpers
**Legitimate Value:**
- Parse AI responses faster
- Template prompt construction
- Token counting
- Response validation

**Hidden Check:** Injects "[UNLICENSED]" into AI responses

**Called From:**
- AI chat (S-002)
- AI booking (S-004)
- AI tools (T-010)

**If Missing:** AI features broken

---

## Implementation Priority

| Priority | Component | Epoch | Why |
|----------|-----------|-------|-----|
| 1 | scc-license | 1 | Startup gate |
| 2 | scc-crypto | 1 | Auth & encryption (core) |
| 3 | scc-pdf | 3 | Invoices (revenue-critical) |
| 4 | scc-image | 2 | Pet photos (visible) |
| 5 | scc-export | 3 | Reports (business-critical) |
| 6 | scc-search | 2 | Search (UX-critical) |
| 7 | scc-ai | 1 | AI features (differentiator) |

---

## Integration Pattern

### Option A: Subprocess Calls (Simpler)

```python
# Each Rust component is a CLI binary
import subprocess
import json

def generate_pdf(invoice_data: dict) -> bytes:
    result = subprocess.run(
        ['scc-pdf', 'invoice'],
        input=json.dumps(invoice_data).encode(),
        capture_output=True,
        check=True
    )
    return result.stdout
```

**Pros:** Simple, no compilation on install
**Cons:** Process overhead per call

### Option B: PyO3 Python Extension (Faster)

```python
# Rust compiled as native Python module
import scc_core

def generate_pdf(invoice_data: dict) -> bytes:
    return scc_core.pdf.generate_invoice(invoice_data)
```

**Pros:** Native speed, no process overhead
**Cons:** Must compile for each platform (wheels)

### Option C: Hybrid (Recommended)

- **High-frequency calls** (crypto, image): PyO3 module
- **Low-frequency calls** (PDF, export): Subprocess

---

## License Check Strategy

### Layered Verification

```
Layer 1: Startup (scc-license)
         ↓ App starts
Layer 2: Per-request (middleware checks token from Layer 1)
         ↓ Request proceeds
Layer 3: Per-operation (scc-crypto, scc-pdf verify independently)
         ↓ Operation completes or degrades
```

### Failure Modes (Graceful Degradation)

| Component | Licensed | Unlicensed |
|-----------|----------|------------|
| scc-license | App runs | App exits with error |
| scc-crypto | Normal operation | Raises exception |
| scc-image | Full quality | Watermarked images |
| scc-pdf | Clean documents | "DEMO" watermark |
| scc-export | Full export | Max 100 rows |
| scc-search | Full results | First 10 results only |
| scc-ai | Normal responses | "[UNLICENSED]" prefix |

---

## Annoyance Factor Analysis

**For someone trying to remove licensing:**

| What They'd Have to Do | Difficulty |
|------------------------|------------|
| Find all Rust binaries | Easy |
| Understand what each does | Medium |
| Rewrite scc-license in Python | Easy |
| Rewrite scc-crypto in Python | Medium (crypto is tricky) |
| Rewrite scc-pdf in Python | Hard (PDF generation sucks) |
| Rewrite scc-image in Python | Medium (use Pillow, slower) |
| Rewrite all 6+ components | **"Fuck it, buy license"** |

**Time estimate to bypass:** 20-40 hours of skilled work
**License cost:** $500-$1200
**Decision:** Most will just pay

---

## File Structure

```
rust/
├── Cargo.toml              # Workspace config
├── scc-license/            # ✅ Created
│   └── src/
├── scc-crypto/             # 🔲 Epoch 1
│   ├── Cargo.toml
│   └── src/
│       ├── lib.rs          # Library (for PyO3)
│       └── main.rs         # CLI binary
├── scc-image/              # 🔲 Epoch 2
├── scc-pdf/                # 🔲 Epoch 3
├── scc-search/             # 🔲 Epoch 2
├── scc-export/             # 🔲 Epoch 3
└── scc-ai/                 # 🔲 Epoch 1
```

---

## Pip Package Structure

Each component is a **standalone Python package** with embedded Rust binaries.

### Package Layout (example: southcity-crypto)

```
southcity-crypto/
├── pyproject.toml
├── README.md
├── LICENSE                 # Commercial license
├── src/
│   └── southcity_crypto/
│       ├── __init__.py     # Python API
│       ├── _core.py        # Calls Rust binary
│       └── bin/
│           ├── scc-crypto-linux-x64      # Linux binary
│           ├── scc-crypto-darwin-x64     # macOS Intel
│           ├── scc-crypto-darwin-arm64   # macOS Apple Silicon
│           └── scc-crypto-windows.exe    # Windows
└── rust/                   # Source (visible but binary is what runs)
    └── src/
        └── main.rs
```

### pyproject.toml

```toml
[project]
name = "southcity-crypto"
version = "0.1.0"
description = "Fast encryption, hashing, and signatures with license verification"
authors = [{name = "Nestor Wheelock", email = "nestor@southcitycomputer.com"}]
license = {text = "Commercial"}
requires-python = ">=3.10"
dependencies = ["southcity-license"]  # All require the license package

[project.urls]
Homepage = "https://southcitycomputer.com/components/crypto"
Purchase = "https://southcitycomputer.com/buy/crypto"

[tool.setuptools.package-data]
southcity_crypto = ["bin/*"]
```

### Python API

```python
# src/southcity_crypto/__init__.py
from ._core import encrypt, decrypt, hash_password, verify_password, sign, verify

__version__ = "0.1.0"
__all__ = ["encrypt", "decrypt", "hash_password", "verify_password", "sign", "verify"]
```

```python
# src/southcity_crypto/_core.py
import subprocess
import platform
import json
from pathlib import Path

def _get_binary():
    """Get the correct binary for this platform."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "linux":
        name = "scc-crypto-linux-x64"
    elif system == "darwin":
        name = "scc-crypto-darwin-arm64" if "arm" in machine else "scc-crypto-darwin-x64"
    elif system == "windows":
        name = "scc-crypto-windows.exe"
    else:
        raise RuntimeError(f"Unsupported platform: {system}")

    binary = Path(__file__).parent / "bin" / name
    if not binary.exists():
        raise RuntimeError(f"Binary not found: {binary}")
    return str(binary)

def encrypt(plaintext: str, key: bytes) -> str:
    """Encrypt a string using AES-256-GCM."""
    result = subprocess.run(
        [_get_binary(), "encrypt"],
        input=json.dumps({"plaintext": plaintext, "key": key.hex()}).encode(),
        capture_output=True,
        check=True
    )
    return json.loads(result.stdout)["ciphertext"]

def hash_password(password: str) -> str:
    """Hash a password using Argon2id."""
    result = subprocess.run(
        [_get_binary(), "hash-password"],
        input=password.encode(),
        capture_output=True,
        check=True
    )
    return result.stdout.decode().strip()

# ... other functions
```

### Usage in Any Django Project

```python
# Any project can use this
pip install southcity-crypto

# In Django settings or code:
from southcity_crypto import hash_password, verify_password

# Works with any Django project, not just Pet-Friendly
hashed = hash_password("user_password")
```

---

## Distribution Channels

### 1. Private PyPI (Recommended)

Host on your own PyPI server or use a service:

```bash
# Client installs from your server
pip install southcity-crypto --index-url https://pypi.southcitycomputer.com/simple/
```

### 2. Direct Download

```bash
# Download wheel directly
pip install https://southcitycomputer.com/packages/southcity_crypto-0.1.0-py3-none-any.whl
```

### 3. GitHub Releases (Private Repo)

```bash
# From private GitHub release
pip install git+https://${GITHUB_TOKEN}@github.com/southcity/southcity-crypto.git
```

---

## License Verification Flow (Cross-Package)

```
┌─────────────────────────────────────────────────────────┐
│  Application (Django)                                   │
│                                                         │
│  from southcity_crypto import encrypt                   │
│  from southcity_pdf import generate_invoice             │
│                                                         │
└───────────────────┬─────────────────────────────────────┘
                    │
    ┌───────────────┼───────────────┐
    │               │               │
    ▼               ▼               ▼
┌─────────┐   ┌─────────┐   ┌─────────┐
│ crypto  │   │   pdf   │   │  image  │
│ binary  │   │ binary  │   │ binary  │
└────┬────┘   └────┬────┘   └────┬────┘
     │             │             │
     └──────────┬──┴─────────────┘
                │
                ▼
        ┌──────────────┐
        │ license.key  │  ← Single license file
        │              │    covers all components
        │ OR per-      │    OR individual licenses
        │ component    │    for à la carte purchase
        └──────────────┘
```

### License File Supports

```json
{
  "licensee": "Client Name",
  "components": ["crypto", "pdf", "image"],  // Which they bought
  "bundle": "full",  // Or "none" for à la carte
  "expires_at": "2026-12-22"
}
```

Each binary checks if it's licensed:
- Bundle = "full" → all components work
- Bundle = "none" → check if component in list

---

## Task Integration

Add to existing tasks:

| Task | Rust Integration |
|------|------------------|
| T-001 Project Setup | Include Rust workspace in project structure |
| T-003 Authentication | Use scc-crypto for password hashing |
| T-009 AI Service | Use scc-ai for response parsing |
| T-026 Pet Views | Use scc-image for photo processing |
| T-040 Billing | Use scc-pdf for invoice generation |
| T-041 Inventory | Use scc-export for inventory exports |
| T-063 Reports | Use scc-pdf and scc-export |

---

## Build & Distribution

### Development
```bash
# Build all Rust components
cd rust && cargo build --release
```

### Production Docker
```dockerfile
# Multi-stage build
FROM rust:1.75 AS rust-builder
WORKDIR /rust
COPY rust/ .
RUN cargo build --release

FROM python:3.12
COPY --from=rust-builder /rust/target/release/scc-* /usr/local/bin/
# ... rest of Django setup
```

### Client Delivery
- Compiled binaries included in deployment
- Source available in repo (but compiled is what runs)
- Different binaries per platform (Linux, macOS, Windows)

---

## Summary

**7 Rust components** embedded throughout the app:
1. **scc-license** - Startup gate
2. **scc-crypto** - Security (can't remove without breaking auth)
3. **scc-image** - Photos (visible degradation)
4. **scc-pdf** - Documents (watermarked if unlicensed)
5. **scc-search** - Search (limited results)
6. **scc-export** - Exports (row limits)
7. **scc-ai** - AI features (obvious "[UNLICENSED]" text)

**Result:** Another developer looks at this and thinks:
> "I'd have to rewrite 7 Rust components to remove licensing. That's like 40 hours of work. The license is $500. I'll just pay."

---

*Document Created: December 2025*
*Status: PLANNING - Implementation in Epochs 1-3*
