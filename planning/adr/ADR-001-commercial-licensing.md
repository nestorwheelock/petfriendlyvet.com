# ADR-001: Commercial Licensing Architecture

**Status:** Accepted
**Date:** December 22, 2025
**Decision Makers:** Nestor Wheelock (South City Computer)

---

## Context

South City Computer (SCC) is building reusable software components that will be used across multiple client projects and potentially sold as standalone products. We need a licensing model that:

1. Protects our commercial interests
2. Allows legitimate source code inspection
3. Prevents unauthorized commercial use
4. Works across Python (Django) and Rust components
5. Is enforceable without relying solely on legal action

### Business Requirements

- **Revenue Protection:** Clients must pay for commercial use
- **Transparency:** Clients can see what they're running
- **Flexibility:** Different tiers for different needs (single clinic, multi-location, enterprise)
- **Portability:** License works across all SCC products
- **Enforcement:** Technical barriers, not just legal ones

### Technical Requirements

- License validation at application startup
- Feature gating based on license type
- Domain/deployment restrictions
- Expiration handling
- Resistance to casual bypassing

---

## Decision

We will implement a **Source-Available Commercial License** with **embedded Rust-based license validation**.

### License Model: Source-Available Commercial

```
                    ┌─────────────────────┐
                    │   Source Code       │
                    │   (Visible)         │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
       ┌──────────┐     ┌──────────┐     ┌──────────┐
       │  Study   │     │  Modify  │     │Commercial│
       │  Audit   │     │ (Limited)│     │   Use    │
       │  Learn   │     │          │     │          │
       └──────────┘     └──────────┘     └──────────┘
            ✓               ✓                ✗
         Allowed         Allowed          Requires
                      (for own use)       License
```

**Key Characteristics:**
- Source code is visible (not obfuscated)
- Clients can audit, study, and understand what they're running
- Modifications allowed for personal/internal use
- Commercial deployment requires valid license
- Redistribution and resale prohibited

### License Types

| Type | Use Case | Price Range | Features |
|------|----------|-------------|----------|
| Trial | Evaluation | Free | 30 days, localhost only, limited features |
| Single | One clinic | $199-499/year | Single domain, full features |
| Multi | Multiple locations | $499-999/year | Multiple domains, priority support |
| Enterprise | Large organizations | $2,000+/year | Unlimited, SLA, custom features |
| Developer | Our team | Free | All features, dev mode |

### Technical Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Client Application                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────┐     ┌───────────────┐     ┌───────────────┐ │
│  │    Django     │     │   scc-image   │     │   scc-pdf     │ │
│  │  Application  │     │               │     │               │ │
│  └───────┬───────┘     └───────┬───────┘     └───────┬───────┘ │
│          │                     │                     │         │
│          └─────────────────────┼─────────────────────┘         │
│                                │                               │
│                    ┌───────────▼───────────┐                   │
│                    │    scc-license        │                   │
│                    │   (Rust Binary)       │                   │
│                    │                       │                   │
│                    │  • Validates license  │                   │
│                    │  • Returns features   │                   │
│                    │  • Checks expiry      │                   │
│                    │  • Verifies domain    │                   │
│                    └───────────┬───────────┘                   │
│                                │                               │
│                    ┌───────────▼───────────┐                   │
│                    │    license.key        │                   │
│                    │   (JSON + Signature)  │                   │
│                    └───────────────────────┘                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### License File Structure

```json
{
  "version": 1,
  "payload": "base64_encoded_json",
  "signature": "sha256_hmac_signature"
}
```

**Decoded Payload:**
```json
{
  "licensee": "Dr. Pablo - Pet Friendly Clinic",
  "email": "pablorojomendoza@gmail.com",
  "license_type": "single",
  "issued_at": "2025-01-01T00:00:00Z",
  "expires_at": "2026-01-01T00:00:00Z",
  "domains": ["petfriendlyvet.com", "localhost"],
  "features": ["appointments", "ecommerce", "ai_assistant"],
  "max_users": 5
}
```

### Validation Flow

```
Application Startup
       │
       ▼
┌──────────────────┐
│ Load license.key │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐     ┌──────────────────┐
│ Call scc-license │────▶│ Verify signature │
│     binary       │     └────────┬─────────┘
└──────────────────┘              │
                                  ▼
                         ┌──────────────────┐
                         │ Check expiration │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Verify domain    │
                         └────────┬─────────┘
                                  │
              ┌───────────────────┴───────────────────┐
              │                                       │
              ▼                                       ▼
       ┌─────────────┐                        ┌─────────────┐
       │   VALID     │                        │  INVALID    │
       │             │                        │             │
       │ Return JSON │                        │ Exit code 1 │
       │ with info   │                        │ Error msg   │
       └─────────────┘                        └─────────────┘
              │                                       │
              ▼                                       ▼
       App continues                           App refuses
       with features                           to start
```

### Why Rust for License Validation

| Approach | Pros | Cons |
|----------|------|------|
| **Pure Python** | Easy to write | Easy to patch/bypass |
| **Obfuscated Python** | Some protection | Can be reverse-engineered |
| **Binary (Rust)** | Hard to modify | Requires build toolchain |
| **External Service** | Very secure | Requires internet, latency |

**Our Choice: Rust Binary**
- Compiled code is harder to casually patch
- No external dependencies at runtime
- Fast validation (<100ms)
- Cross-platform binaries
- Same codebase for all SCC products

### Feature Gating

```python
# In Django code
from apps.core.license import get_license_info

license_info = get_license_info()

if 'ai_assistant' in license_info.features:
    # Enable AI chat functionality
    pass

if license_info.license_type in ['multi', 'enterprise']:
    # Enable multi-location features
    pass
```

### Environment Variables

```bash
# License file location
SCC_LICENSE_FILE=license.key

# Optional: Path to validator binary
SCC_LICENSE_BINARY=rust/target/release/scc-license
```

---

## Alternatives Considered

### 1. SaaS-Only Model

**Rejected because:**
- Some clients want to self-host
- Higher support burden
- Single point of failure

### 2. Pure Open Source (GPL/MIT)

**Rejected because:**
- No revenue protection
- Competitors can fork and sell
- Doesn't support commercial business model

### 3. Proprietary Closed Source

**Rejected because:**
- Clients can't audit what they run
- Security concerns for sensitive data
- Less trust from clients

### 4. License Server (Phone Home)

**Rejected because:**
- Requires internet connection
- Privacy concerns
- Single point of failure
- Higher latency

### 5. Hardware Dongles

**Rejected because:**
- Expensive to distribute
- Poor UX
- Doesn't scale for web deployment

---

## Consequences

### Positive

- **Revenue Protection:** Technical barrier to unauthorized use
- **Client Trust:** Source is visible and auditable
- **Flexibility:** Easy to issue licenses for different tiers
- **Speed:** Validation happens locally, no network required
- **Consistency:** Same mechanism across all SCC products

### Negative

- **Build Complexity:** Requires Rust toolchain in CI/CD
- **Platform Binaries:** Need to build for Linux, macOS, Windows
- **Key Management:** Must protect the signing secret
- **Not Bulletproof:** Determined attackers could still bypass

### Mitigations

- **Automated builds:** GitHub Actions for cross-platform binaries
- **PyPI packages:** Include pre-built binaries in pip packages
- **Secret management:** Use environment variables, not hardcoded
- **Legal backup:** License agreement provides legal recourse

---

## Implementation Plan

### Phase 1: Foundation (T-001)
- [x] Create scc-license Rust crate
- [x] Implement validator binary
- [x] Implement generator binary
- [ ] Django integration (startup validation)
- [ ] Tests for license validation

### Phase 2: Distribution
- [ ] GitHub Actions for multi-platform builds
- [ ] PyPI package with bundled binaries
- [ ] Installation documentation

### Phase 3: Additional Components
- [ ] scc-crypto (encryption, hashing)
- [ ] scc-image (image processing)
- [ ] scc-pdf (document generation)
- [ ] Each component calls scc-license

### Phase 4: Management
- [ ] Admin interface for license generation
- [ ] Customer portal for license management
- [ ] Automated renewal reminders

---

## Security Considerations

### Signature Algorithm
- Using SHA-256 HMAC for signing
- Salt embedded in binary (not in source)
- Future: Consider Ed25519 for asymmetric signing

### Secret Protection
```
                  ┌─────────────────┐
                  │  SECRET SALT    │
                  │  (in binary)    │
                  └────────┬────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
       ┌─────────────┐           ┌─────────────┐
       │  scc-license│           │scc-license- │
       │  (validates)│           │  generate   │
       └─────────────┘           │ (creates)   │
                                 └─────────────┘
```

**Note:** `scc-license-generate` is for internal use only and should NOT be distributed to clients.

### Attack Vectors and Mitigations

| Attack | Difficulty | Mitigation |
|--------|------------|------------|
| Patch binary | Medium | Strip symbols, use LTO |
| Extract salt | Hard | Embedded in optimized code |
| Forge license | Very Hard | HMAC signature required |
| Bypass in Python | Easy | Don't ship modified source |
| Replace binary | Medium | Verify binary hash at build |

---

## Related Documents

- [LICENSING.md](../LICENSING.md) - Full licensing documentation
- [RUST_COMPONENTS.md](../RUST_COMPONENTS.md) - All SCC Rust components
- [T-001-project-setup.md](../tasks/T-001-project-setup.md) - Implementation task

---

## Revision History

| Date | Author | Changes |
|------|--------|---------|
| 2025-12-22 | Nestor Wheelock | Initial version |
