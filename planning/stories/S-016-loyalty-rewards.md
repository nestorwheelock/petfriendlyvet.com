# S-016: Loyalty & Rewards Program

> **REQUIRED READING:** Before implementation, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md)

**Story Type:** User Story
**Priority:** Low
**Epoch:** 5 (with CRM)
**Status:** PENDING
**Module:** django-crm-lite

## User Story

**As a** pet owner
**I want to** earn rewards for my loyalty to the clinic
**So that** I feel valued and save money on pet care

**As a** clinic owner
**I want to** reward loyal clients
**So that** I increase retention and encourage repeat visits

**As a** pet owner
**I want to** refer friends and earn bonuses
**So that** I can help others find great care and benefit myself

## Acceptance Criteria

### Points System
- [ ] Earn points on purchases and services
- [ ] Clear point-to-currency conversion
- [ ] Points visible in account dashboard
- [ ] Points expiration policy
- [ ] Bonus point promotions
- [ ] AI notifies of points balance

### Reward Tiers
- [ ] Multiple membership levels (Bronze, Silver, Gold, Platinum)
- [ ] Tier benefits clearly displayed
- [ ] Auto-upgrade based on spending
- [ ] Tier status notifications
- [ ] Exclusive tier perks

### Redemption
- [ ] Redeem points for discounts
- [ ] Redeem for free services
- [ ] Redeem for products
- [ ] Easy redemption via AI chat
- [ ] Redemption history

### Referral Program
- [ ] Unique referral codes/links
- [ ] Reward for referrer
- [ ] Welcome bonus for referred
- [ ] Track referral status
- [ ] Referral leaderboard (optional)

### Special Rewards
- [ ] Birthday rewards (pet birthdays)
- [ ] Anniversary rewards (client since)
- [ ] Multi-pet discounts
- [ ] Prepaid package discounts
- [ ] Seasonal promotions

## Technical Requirements

### Models

```python
class LoyaltyProgram(models.Model):
    """Loyalty program configuration"""
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    # Points configuration
    points_per_peso = models.DecimalField(max_digits=5, decimal_places=2, default=1)
    peso_per_point = models.DecimalField(max_digits=5, decimal_places=2, default=0.10)
    # 1 peso spent = 1 point, 1 point = $0.10 discount

    # Expiration
    points_expire = models.BooleanField(default=True)
    expiration_months = models.IntegerField(default=12)

    # Minimum redemption
    min_points_to_redeem = models.IntegerField(default=100)
    max_discount_percentage = models.IntegerField(default=20)
    # Can't discount more than 20% of purchase with points

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LoyaltyTier(models.Model):
    """Membership tiers"""
    program = models.ForeignKey(LoyaltyProgram, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    name_es = models.CharField(max_length=50)

    # Requirements
    min_spend = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # Lifetime spend to reach this tier
    min_visits = models.IntegerField(default=0)

    # Benefits
    points_multiplier = models.DecimalField(max_digits=3, decimal_places=1, default=1.0)
    # 1.0 = normal, 1.5 = 50% bonus points
    discount_percentage = models.IntegerField(default=0)
    # Automatic discount on all purchases

    # Perks
    perks = models.JSONField(default=list)
    # ["priority_booking", "free_nail_trim", "birthday_gift", ...]

    # Display
    color = models.CharField(max_length=7, default='#CD7F32')  # Bronze
    icon = models.CharField(max_length=50, blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']


class MemberProfile(models.Model):
    """Client loyalty membership"""
    owner = models.OneToOneField(User, on_delete=models.CASCADE)
    program = models.ForeignKey(LoyaltyProgram, on_delete=models.CASCADE)
    tier = models.ForeignKey(LoyaltyTier, on_delete=models.SET_NULL, null=True)

    # Points
    points_balance = models.IntegerField(default=0)
    points_earned_lifetime = models.IntegerField(default=0)
    points_redeemed_lifetime = models.IntegerField(default=0)

    # Spending
    total_spend = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_visits = models.IntegerField(default=0)

    # Referral
    referral_code = models.CharField(max_length=20, unique=True)
    referred_by = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True
    )
    referral_count = models.IntegerField(default=0)
    referral_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Status
    is_active = models.BooleanField(default=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    tier_updated_at = models.DateTimeField(null=True)


class PointsTransaction(models.Model):
    """Points earning and redemption history"""
    TRANSACTION_TYPES = [
        ('earned', 'Points Earned'),
        ('redeemed', 'Points Redeemed'),
        ('bonus', 'Bonus Points'),
        ('expired', 'Points Expired'),
        ('adjustment', 'Manual Adjustment'),
        ('referral', 'Referral Bonus'),
    ]

    member = models.ForeignKey(MemberProfile, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    points = models.IntegerField()  # Positive = earned, Negative = spent
    balance_after = models.IntegerField()

    # Reference
    description = models.CharField(max_length=200)
    order = models.ForeignKey(
        'store.Order', on_delete=models.SET_NULL, null=True, blank=True
    )
    appointment = models.ForeignKey(
        'appointments.Appointment', on_delete=models.SET_NULL, null=True, blank=True
    )

    # For expiration tracking
    expires_at = models.DateTimeField(null=True, blank=True)
    expired = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ['-created_at']


class Reward(models.Model):
    """Redeemable rewards"""
    REWARD_TYPES = [
        ('discount', 'Discount'),
        ('service', 'Free Service'),
        ('product', 'Free Product'),
        ('upgrade', 'Service Upgrade'),
    ]

    name = models.CharField(max_length=100)
    name_es = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    reward_type = models.CharField(max_length=20, choices=REWARD_TYPES)

    # Cost
    points_required = models.IntegerField()

    # Value
    discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    discount_percentage = models.IntegerField(null=True, blank=True)
    free_service = models.ForeignKey(
        'appointments.ServiceType', on_delete=models.SET_NULL, null=True, blank=True
    )
    free_product = models.ForeignKey(
        'store.Product', on_delete=models.SET_NULL, null=True, blank=True
    )

    # Restrictions
    min_tier = models.ForeignKey(
        LoyaltyTier, on_delete=models.SET_NULL, null=True, blank=True
    )
    min_purchase = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    valid_days = models.IntegerField(default=30)  # Days until expiration

    # Availability
    is_active = models.BooleanField(default=True)
    limited_quantity = models.IntegerField(null=True, blank=True)
    quantity_remaining = models.IntegerField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    # Display
    image = models.ImageField(upload_to='rewards/', null=True, blank=True)
    featured = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'points_required']


class RedeemedReward(models.Model):
    """Redeemed reward tracking"""
    member = models.ForeignKey(MemberProfile, on_delete=models.CASCADE)
    reward = models.ForeignKey(Reward, on_delete=models.CASCADE)
    points_spent = models.IntegerField()

    # Redemption code
    code = models.CharField(max_length=20, unique=True)

    # Status
    status = models.CharField(max_length=20, default='active')
    # active, used, expired, cancelled
    used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()

    # Usage reference
    order = models.ForeignKey(
        'store.Order', on_delete=models.SET_NULL, null=True, blank=True
    )
    appointment = models.ForeignKey(
        'appointments.Appointment', on_delete=models.SET_NULL, null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)


class Referral(models.Model):
    """Referral tracking"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('registered', 'Registered'),
        ('qualified', 'Qualified'),
        ('rewarded', 'Rewarded'),
    ]

    referrer = models.ForeignKey(
        MemberProfile, on_delete=models.CASCADE, related_name='referrals_made'
    )
    referred_email = models.EmailField(blank=True)
    referred_phone = models.CharField(max_length=20, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    referred_member = models.ForeignKey(
        MemberProfile, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='referred_by_referral'
    )

    # Rewards
    referrer_points = models.IntegerField(default=0)
    referred_points = models.IntegerField(default=0)
    qualification_purchase = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    # Tracking
    referral_link_clicks = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    registered_at = models.DateTimeField(null=True, blank=True)
    qualified_at = models.DateTimeField(null=True, blank=True)
    rewarded_at = models.DateTimeField(null=True, blank=True)


class BirthdayReward(models.Model):
    """Pet birthday rewards"""
    pet = models.ForeignKey('vet_clinic.Pet', on_delete=models.CASCADE)
    member = models.ForeignKey(MemberProfile, on_delete=models.CASCADE)
    year = models.IntegerField()

    reward = models.ForeignKey(
        RedeemedReward, on_delete=models.SET_NULL, null=True, blank=True
    )
    points_bonus = models.IntegerField(default=0)

    notified_at = models.DateTimeField(null=True, blank=True)
    claimed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['pet', 'year']


class SpecialPromotion(models.Model):
    """Limited-time promotions"""
    name = models.CharField(max_length=100)
    description = models.TextField()

    # Bonus points
    points_multiplier = models.DecimalField(max_digits=3, decimal_places=1, default=1.0)
    bonus_points = models.IntegerField(default=0)

    # Conditions
    min_purchase = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    service_types = models.JSONField(default=list)  # Empty = all
    product_categories = models.JSONField(default=list)

    # Validity
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    # Targeting
    tiers = models.ManyToManyField(LoyaltyTier, blank=True)  # Empty = all
    new_members_only = models.BooleanField(default=False)

    # Tracking
    times_used = models.IntegerField(default=0)
    max_uses = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
```

### AI Tools

```python
LOYALTY_TOOLS = [
    {
        "name": "get_loyalty_status",
        "description": "Get member's loyalty program status",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"}
            }
        }
    },
    {
        "name": "get_points_balance",
        "description": "Get member's points balance and history",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
                "include_history": {"type": "boolean", "default": False}
            }
        }
    },
    {
        "name": "get_available_rewards",
        "description": "Get rewards available for redemption",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
                "points_max": {"type": "integer"}
            }
        }
    },
    {
        "name": "redeem_reward",
        "description": "Redeem points for a reward",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
                "reward_id": {"type": "integer"}
            },
            "required": ["user_id", "reward_id"]
        }
    },
    {
        "name": "apply_reward_code",
        "description": "Apply a redeemed reward to purchase",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "order_id": {"type": "integer"}
            },
            "required": ["code"]
        }
    },
    {
        "name": "get_referral_link",
        "description": "Get member's referral link/code",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"}
            }
        }
    },
    {
        "name": "check_tier_progress",
        "description": "Check progress to next tier",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"}
            }
        }
    },
    {
        "name": "get_active_promotions",
        "description": "Get currently active promotions",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
]
```

## Example AI Conversations

### Points Balance Check
```
Owner: How many points do I have?

AI: Here's your Pet-Friendly Rewards status, Maria:

    🏆 Silver Member

    💰 Points Balance: 1,250 points
    (Worth $125 MXN in discounts)

    📊 This Month:
    • Earned: 350 points
    • Redeemed: 0 points

    🎁 You can redeem for:
    • Free nail trim (500 pts)
    • $100 discount (1,000 pts)
    • Free bath & brush (1,500 pts - 250 more needed)

    🎯 Progress to Gold:
    ████████░░ 80%
    $2,000 more spend to reach Gold tier

    Would you like to redeem points or see all rewards?
```

### Referral Program
```
Owner: How does the referral program work?

AI: Great question! Here's how you can earn rewards
    by referring friends:

    🎁 Referral Rewards

    You Get: 500 points ($50 value)
    They Get: 300 welcome points + 10% off first visit

    How It Works:
    1. Share your unique link or code: MARIA2025
    2. Friend registers and books first appointment
    3. After their first visit, you both get rewarded!

    Your Referral Stats:
    • Friends referred: 3
    • Points earned: 1,500
    • Pending referrals: 1 (waiting for first visit)

    Share your link:
    petfriendlyvet.com/ref/MARIA2025

    [Copy Link] [Share on WhatsApp] [Share on Facebook]
```

### Birthday Reward
```
AI (WhatsApp):
    🎂 Happy Birthday, Luna! 🐕

    Luna turns 3 today! We hope she has a wonderful day.

    As a Silver member, here's Luna's birthday gift:

    🎁 FREE Nail Trim
    (Normally $150 MXN)

    Valid for the next 30 days.
    Use code: LUNA-BDAY-2025

    We'd love to see her! Book a grooming appointment
    and show off that birthday glow.

    [Book Grooming] [Save for Later]

    With love from the Pet-Friendly family! 💚
```

## Tier Structure

| Tier | Spend Required | Points Multiplier | Perks |
|------|---------------|-------------------|-------|
| Bronze | $0 | 1x | Basic rewards |
| Silver | $5,000 | 1.25x | Priority booking, birthday treats |
| Gold | $15,000 | 1.5x | Free annual checkup, 5% all purchases |
| Platinum | $30,000 | 2x | VIP everything, free grooming monthly |

## Definition of Done

- [ ] Loyalty program configuration
- [ ] Member enrollment
- [ ] Points earning on purchases
- [ ] Tier auto-upgrade
- [ ] Reward catalog
- [ ] Points redemption
- [ ] Referral tracking
- [ ] Birthday rewards
- [ ] Promotional campaigns
- [ ] Points expiration
- [ ] Member dashboard
- [ ] Tests written and passing (>95% coverage)

## Dependencies

- S-005: E-Commerce (points on purchases)
- S-007: CRM (owner profiles)
- S-012: Notifications (reward notifications)

## Notes

- Consider gamification elements (badges, achievements)
- Points should never expire for inactive members
- Consider family accounts (shared points across pets)
- Integration with payment processor for automatic points
- Consider prepaid packages (buy 5 checkups, get 1 free)

## Development Process

**Before implementing this story**, review and follow the **23-Step TDD Cycle** in:
- `CLAUDE.md` - Global development workflow
- `planning/TASK_BREAKDOWN.md` - Specific tasks for this story

Tests must be written before implementation. >95% coverage required.
