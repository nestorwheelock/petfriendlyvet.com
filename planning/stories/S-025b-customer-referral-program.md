# S-025b: Customer Referral Program

> **REQUIRED READING:** Before implementation, review [CODING_STANDARDS.md](../CODING_STANDARDS.md)

**Story Type:** User Story
**Priority:** Medium
**Status:** PLANNING
**Module:** loyalty / referrals

## Overview

The `referrals` module should handle TWO distinct concepts:

### 1. Professional Referrals (S-025 - Existing)
- Vet-to-vet specialist referrals (oncology, cardiology, etc.)
- Visiting specialists who come to Pet-Friendly
- Inbound/outbound patient referrals with tracking
- **Keep existing implementation in `apps.referrals`**

### 2. Customer Referral Program (S-025b - NEW)
- Customer-to-customer referrals for new business
- Referrer portal with coupon/card generation
- QR codes and unique referral codes
- Commission tracking (pay out or credit)
- Rewards, discounts, gifts for referrers
- **New implementation in `apps.loyalty.referrals` or expand `apps.loyalty`**

---

## User Stories

**As a** loyal customer
**I want to** refer my friends to Pet-Friendly
**So that** I earn rewards when they become customers

**As a** referrer
**I want to** generate unique referral codes and QR cards
**So that** I can share them with potential customers

**As a** clinic owner
**I want to** track referral sources and pay commissions
**So that** I can reward people who bring new business

**As a** new customer
**I want to** use a referral code for a discount
**So that** I save money on my first visit

---

## Acceptance Criteria

### Referrer Portal
- [ ] Referrers can log in to a self-service portal
- [ ] Generate unique referral codes (alphanumeric)
- [ ] Generate QR codes that link to signup with referral code
- [ ] Generate printable referral cards (PDF with QR code)
- [ ] View referral statistics (sent, converted, pending)
- [ ] View earned rewards/commissions
- [ ] Request payout or apply credit to account

### Referral Codes
- [ ] Unique code per referrer (e.g., `JUAN2025`)
- [ ] Optional campaign codes (e.g., `SUMMER25`)
- [ ] Expiration dates (optional)
- [ ] Usage limits (optional)
- [ ] Track: code → referrer → new customer

### Rewards System
- [ ] Configurable reward types:
  - Cash commission (pay out)
  - Account credit
  - Discount on next service
  - Free service/product
  - Points (if loyalty program exists)
- [ ] Tiered rewards (1st referral = X, 5th = Y, 10th = Z)
- [ ] Two-sided rewards (referrer + new customer both get something)

### Tracking & Analytics
- [ ] Referral funnel: Code shared → Used → Converted
- [ ] Conversion rate by referrer
- [ ] Revenue generated per referrer
- [ ] Top referrers leaderboard
- [ ] Campaign performance

### Integration
- [ ] Link to billing for commission payouts
- [ ] Link to loyalty points (if applicable)
- [ ] Link to customer accounts

---

## Technical Design

### Models

```python
# apps/loyalty/models.py (or apps/referrals/customer_referrals.py)

class Referrer(models.Model):
    """Person who refers new customers (can be customer, partner, influencer)."""
    REFERRER_TYPES = [
        ('customer', 'Customer'),
        ('partner', 'Business Partner'),
        ('influencer', 'Influencer'),
        ('employee', 'Employee'),
        ('professional', 'Professional (Vet, Trainer, etc.)'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    referrer_type = models.CharField(max_length=20, choices=REFERRER_TYPES, default='customer')

    # For non-user referrers
    name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)

    # Unique referral code
    referral_code = models.CharField(max_length=20, unique=True)

    # Commission settings
    commission_type = models.CharField(max_length=20)  # 'percent', 'fixed', 'credit'
    commission_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Stats (denormalized for performance)
    total_referrals = models.IntegerField(default=0)
    successful_referrals = models.IntegerField(default=0)
    total_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pending_payout = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ReferralCode(models.Model):
    """Individual referral/campaign codes."""
    referrer = models.ForeignKey(Referrer, on_delete=models.CASCADE, related_name='codes')

    code = models.CharField(max_length=30, unique=True)
    campaign = models.CharField(max_length=100, blank=True)  # e.g., "Summer 2025"

    # Rewards
    referrer_reward_type = models.CharField(max_length=20)  # 'cash', 'credit', 'discount', 'points'
    referrer_reward_value = models.DecimalField(max_digits=10, decimal_places=2)
    new_customer_reward_type = models.CharField(max_length=20)
    new_customer_reward_value = models.DecimalField(max_digits=10, decimal_places=2)

    # Limits
    expires_at = models.DateTimeField(null=True, blank=True)
    max_uses = models.IntegerField(null=True, blank=True)
    times_used = models.IntegerField(default=0)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class CustomerReferral(models.Model):
    """A referral from one customer to another."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),      # Code used, awaiting first purchase
        ('converted', 'Converted'),  # New customer made qualifying purchase
        ('paid', 'Paid Out'),        # Commission paid to referrer
        ('expired', 'Expired'),      # Never converted
        ('cancelled', 'Cancelled'),
    ]

    referrer = models.ForeignKey(Referrer, on_delete=models.CASCADE, related_name='referrals')
    code_used = models.ForeignKey(ReferralCode, on_delete=models.SET_NULL, null=True)

    # New customer
    new_customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referred_by')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Tracking
    code_used_at = models.DateTimeField(auto_now_add=True)
    converted_at = models.DateTimeField(null=True, blank=True)
    first_purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    # Rewards
    referrer_reward_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    referrer_reward_paid_at = models.DateTimeField(null=True, blank=True)
    new_customer_discount_applied = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ReferralPayout(models.Model):
    """Commission payouts to referrers."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]

    PAYOUT_METHODS = [
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('account_credit', 'Account Credit'),
        ('check', 'Check'),
    ]

    referrer = models.ForeignKey(Referrer, on_delete=models.CASCADE, related_name='payouts')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=PAYOUT_METHODS)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Linked referrals being paid out
    referrals = models.ManyToManyField(CustomerReferral, related_name='payouts')

    requested_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)
```

### Referrer Portal Views

```
/referral-portal/                    # Login/dashboard
/referral-portal/codes/              # My referral codes
/referral-portal/codes/generate/     # Generate new code
/referral-portal/card/<code>/        # Generate printable card with QR
/referral-portal/stats/              # My statistics
/referral-portal/payouts/            # My earnings & payouts
/referral-portal/payouts/request/    # Request payout
```

### QR Code Generation

```python
import qrcode
from io import BytesIO

def generate_referral_qr(referral_code, base_url):
    """Generate QR code for referral link."""
    referral_url = f"{base_url}/register/?ref={referral_code}"

    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(referral_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()
```

---

## Professional Referral Tracking (Enhancement to S-025)

For vet-to-vet professional referrals, add balance tracking:

```python
class ProfessionalReferralBalance(models.Model):
    """Track referral balance between clinics/vets."""
    # "You gave me 3, I gave you 2, I owe you 1"

    our_clinic = models.ForeignKey('practice.Practice', on_delete=models.CASCADE)
    partner = models.ForeignKey(Specialist, on_delete=models.CASCADE)

    # Counts
    referrals_sent = models.IntegerField(default=0)      # We sent to them
    referrals_received = models.IntegerField(default=0)  # They sent to us

    @property
    def balance(self):
        """Positive = they owe us, Negative = we owe them."""
        return self.referrals_received - self.referrals_sent

    @property
    def balance_description(self):
        b = self.balance
        if b > 0:
            return f"They owe us {b} referral(s)"
        elif b < 0:
            return f"We owe them {abs(b)} referral(s)"
        return "Even"

    last_updated = models.DateTimeField(auto_now=True)
```

---

## Definition of Done

- [ ] Referrer model with unique codes
- [ ] Customer referral tracking (pending → converted → paid)
- [ ] Referrer portal with login
- [ ] QR code generation for referral codes
- [ ] Printable referral card (PDF)
- [ ] Payout request and approval workflow
- [ ] Integration with billing for commissions
- [ ] Professional referral balance tracking
- [ ] Admin dashboard for referral program management
- [ ] Tests written and passing (>95% coverage)

---

## Notes

- Keep professional vet referrals (S-025) separate from customer referrals
- Customer referrals belong in `apps.loyalty` or new `apps.loyalty.referrals`
- Professional referral balance tracking enhances existing `apps.referrals`
- Consider gamification (leaderboards, badges) for top referrers
