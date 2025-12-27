# T-003: Authentication System

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md and [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement multi-method authentication (Google OAuth, email, phone)
**Related Story**: S-001
**Estimate**: 4 hours

### Constraints
**Allowed File Paths**: apps/accounts/, apps/core/, templates/accounts/
**Forbidden Paths**: apps/store/, apps/pharmacy/

### Deliverables
- [ ] User model extended with phone number field
- [ ] Google OAuth integration (django-allauth)
- [ ] Email magic link authentication
- [ ] Phone/SMS verification (Twilio)
- [ ] Login/logout views and templates
- [ ] Password reset flow
- [ ] Session management across devices

### Implementation Details

#### User Model Extension
```python
class User(AbstractUser):
    phone_number = models.CharField(max_length=20, blank=True)
    phone_verified = models.BooleanField(default=False)
    preferred_language = models.CharField(max_length=5, default='es')
    auth_method = models.CharField(max_length=20)  # google, email, phone
```

#### OAuth Configuration
- Google OAuth via django-allauth
- Callback URL: /accounts/google/login/callback/
- Scopes: email, profile

#### Phone Authentication
- Twilio Verify API for SMS codes
- 6-digit verification code
- 10-minute expiry
- Rate limit: 3 attempts per hour

### Test Cases
- [ ] Google OAuth login flow
- [ ] Email magic link generation and verification
- [ ] Phone number verification with valid code
- [ ] Phone number verification with invalid code
- [ ] Session persistence across browser close
- [ ] Logout clears all sessions
- [ ] Rate limiting prevents abuse
- [ ] User profile shows auth method used

### Acceptance Criteria

**AC-1: Google OAuth Login**
**Given** I am on the login page
**When** I click "Sign in with Google" and authorize
**Then** I am logged in and redirected to the dashboard

**AC-2: Email Magic Link**
**Given** I enter my email on the login page
**When** I click the magic link sent to my email
**Then** I am logged in without entering a password

**AC-3: Phone/SMS Verification**
**Given** I enter my phone number for verification
**When** I enter the 6-digit code from SMS
**Then** my phone is verified and I am logged in

**AC-4: Session Persistence**
**Given** I am logged in and close the browser
**When** I reopen the browser and visit the site
**Then** I remain logged in until session expires

**AC-5: Multi-Device Sessions**
**Given** I am logged in on my phone
**When** I log in on my laptop
**Then** both sessions remain active independently

### Definition of Done
- [ ] All three auth methods working
- [ ] Users can switch between auth methods
- [ ] Sessions properly managed
- [ ] Tests written and passing (>95% coverage)
- [ ] Documentation updated

### Dependencies
- T-001: Django Project Setup
- T-002: Base Templates

### Environment Variables
```
GOOGLE_OAUTH_CLIENT_ID=
GOOGLE_OAUTH_CLIENT_SECRET=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_VERIFY_SERVICE_SID=
```
