# T-003: Authentication System

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
