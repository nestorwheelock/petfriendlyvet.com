# Roadmap Ideas

Future feature concepts for consideration. These are not committed to any sprint.

---

## Authentication & Security

### IDEA-001: AI Facial Recognition Authentication

**Concept:** Use webcam + AI to authenticate users by comparing live face capture to stored face ID.

**How It Would Work:**
1. Registration: User captures face photos → system creates face embedding (vector)
2. Login: Webcam captures live photo → generates embedding → compares to stored
3. Match threshold met → authenticated

**Benefits:**
- Passwordless - No credentials to leak, phish, or forget
- Hard to share - Can't give someone your face like a password
- Presence verification - Proves the actual person is at the terminal
- Combined with session tokens - Face + token = very strong auth
- Staff accountability - Know exactly who accessed what

**Challenges:**
- Privacy concerns - Storing biometric data requires GDPR/privacy compliance
- Spoofing risk - Photos/videos could trick basic systems (needs liveness detection)
- Accessibility - Users without webcams, lighting conditions, disabilities
- Data breach impact - Can't change your face like a password
- False rejections - Frustrating for legitimate users

**Anti-Spoofing Measures Required:**
- Liveness detection (blink, turn head, random prompts)
- Depth sensing (if hardware supports)
- Texture analysis to detect printed photos/screens
- Motion analysis during capture

**Implementation Options:**
1. **Client-side (privacy-preserving)** - Face embedding computed in browser via TensorFlow.js, only hash/vector sent to server
2. **Server-side** - Full image sent, processed by AI model (more accurate, less private)
3. **Third-party services** - AWS Rekognition, Azure Face API, Google Cloud Vision

**PetFriendlyVet Use Case:**
- Staff-only feature (small, controlled user base)
- Clinic workstations have consistent lighting
- Could combine with magic link: email link + face verify at terminal
- Audit trail: photo captured at each login for security review

**Technical Stack Options:**
- Frontend: TensorFlow.js face-api.js for browser-based detection
- Backend: Python face_recognition library, dlib, or OpenCV
- Storage: Face embeddings (512-dimensional vectors), not raw photos
- Database: Encrypted biometric data with strict access controls

**Privacy Considerations:**
- Explicit user consent required
- Right to delete biometric data
- Data stored encrypted at rest
- No sharing with third parties
- Clear retention policy

**Complexity:** High
**Priority:** Future consideration
**Dependencies:** Webcam hardware, user consent framework, privacy policy updates

---

### IDEA-002: Magic Link Authentication

**Concept:** Passwordless login via email-only. User enters email, receives one-time link.

**Benefits:**
- No password to remember/leak
- Email proves identity
- Links expire quickly (15 min)
- Can combine with face ID for 2FA

**Complexity:** Medium
**Priority:** Near-term consideration

---

### IDEA-003: Hardware Security Key Support (WebAuthn/FIDO2)

**Concept:** Support YubiKey and similar hardware tokens for authentication.

**Benefits:**
- Phishing-resistant
- No passwords
- Industry standard (WebAuthn)

**Complexity:** Medium
**Priority:** Future consideration

---

## Staff Portal Enhancements

### IDEA-004: Voice Commands for Hands-Free Operation

**Concept:** Voice-activated commands for staff during procedures (hands may be occupied).

**Use Cases:**
- "Start timer for medication"
- "Add note: patient showing improvement"
- "Call next appointment"

**Complexity:** High
**Priority:** Future consideration

---

## Customer Portal Enhancements

### IDEA-005: Pet Health Monitoring via Photo AI

**Concept:** Customers upload pet photos, AI analyzes for potential health indicators.

**Examples:**
- Eye discharge detection
- Skin condition analysis
- Weight estimation from photos over time
- Dental health from mouth photos

**Complexity:** Very High
**Priority:** Long-term research

---

*Last updated: 2024-12-26*
