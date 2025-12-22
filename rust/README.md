# South City Computer (SCC) Rust Components

Reusable, performance-critical components with embedded license verification.

**These components are designed to be used across multiple South City Computer projects** - not just Pet-Friendly. They will be distributed as standalone pip packages.

## Components

| Component | Status | Purpose | Reusable For |
|-----------|--------|---------|--------------|
| scc-license | ✅ Created | License validation at startup | All SCC projects |
| scc-crypto | 🔲 Planned | Encryption, hashing, signatures | Any app with auth/security |
| scc-image | 🔲 Planned | Image processing, thumbnails | Any app with uploads |
| scc-pdf | 🔲 Planned | PDF generation (invoices, certs) | Any app with documents |
| scc-search | 🔲 Planned | Fast text search, fuzzy matching | Any app with search |
| scc-export | 🔲 Planned | CSV/Excel export | Any app with reports |
| scc-ai | 🔲 Planned | AI response parsing | Any AI-powered app |

## Distribution

Each component will be:
- **Standalone pip package** (e.g., `pip install southcity-crypto`)
- **Independently licensable** (buy only what you need)
- **Cross-platform** (Linux, macOS Intel/ARM, Windows binaries)

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
3. Works with any Django/Python project
4. Can be bundled or sold à la carte
