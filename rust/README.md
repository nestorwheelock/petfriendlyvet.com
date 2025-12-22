# Pet-Friendly Rust Components

Performance-critical and license-enforcing components written in Rust.

## Components

| Component | Status | Purpose |
|-----------|--------|---------|
| pfv-license | ✅ Created | License validation at startup |
| pfv-crypto | 🔲 Planned | Encryption, hashing, signatures |
| pfv-image | 🔲 Planned | Image processing, thumbnails |
| pfv-pdf | 🔲 Planned | PDF generation (invoices, certs) |
| pfv-search | 🔲 Planned | Fast text search, fuzzy matching |
| pfv-export | 🔲 Planned | CSV/Excel export |
| pfv-ai | 🔲 Planned | AI response parsing |

## Build

```bash
# Build all components
cargo build --release

# Binaries output to target/release/
```

## Architecture

See [planning/RUST_COMPONENTS.md](../planning/RUST_COMPONENTS.md) for full strategy.

Each component:
1. Provides legitimate performance/security value
2. Contains embedded license verification
3. Is essential for app functionality
