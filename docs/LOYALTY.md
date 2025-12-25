# Loyalty Module

The `apps.loyalty` module manages customer loyalty programs with points, tiers, rewards, and referrals.

## Table of Contents

- [Overview](#overview)
- [Models](#models)
  - [LoyaltyProgram](#loyaltyprogram)
  - [LoyaltyTier](#loyaltytier)
  - [LoyaltyAccount](#loyaltyaccount)
  - [PointTransaction](#pointtransaction)
  - [LoyaltyReward](#loyaltyreward)
  - [RewardRedemption](#rewardredemption)
  - [ReferralProgram](#referralprogram)
  - [Referral](#referral)
- [Workflows](#workflows)
- [Integration Points](#integration-points)
- [Query Examples](#query-examples)
- [Testing](#testing)

## Overview

The loyalty module provides:

- **Points System** - Earn points on purchases, bonus points for actions
- **Tier Levels** - Bronze, Silver, Gold with escalating benefits
- **Rewards Catalog** - Redeem points for discounts, services, products
- **Referral Program** - Earn points for referring new customers
- **Transaction History** - Complete audit trail of points earned/redeemed

## Models

Location: `apps/loyalty/models.py`

### LoyaltyProgram

Loyalty program configuration.

```python
class LoyaltyProgram(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    points_per_currency = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1.0,
        help_text="Points earned per currency unit spent"
    )
    is_active = models.BooleanField(default=True)
```

### LoyaltyTier

Loyalty program tier levels.

```python
class LoyaltyTier(models.Model):
    program = models.ForeignKey(LoyaltyProgram, on_delete=models.CASCADE, related_name='tiers')
    name = models.CharField(max_length=50)
    min_points = models.IntegerField(default=0)
    max_points = models.IntegerField(null=True)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    points_multiplier = models.DecimalField(max_digits=3, decimal_places=1, default=1.0)
    benefits = models.JSONField(default=list)
    color = models.CharField(max_length=20, blank=True)
    icon = models.CharField(max_length=50, blank=True)
    display_order = models.IntegerField(default=0)
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `min_points` | Integer | Lifetime points to reach tier |
| `discount_percent` | Decimal | Automatic discount for tier members |
| `points_multiplier` | Decimal | Multiplier for earning points |
| `benefits` | JSONField | List of tier perks |

### LoyaltyAccount

Customer loyalty account.

```python
class LoyaltyAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='loyalty_account')
    program = models.ForeignKey(LoyaltyProgram, on_delete=models.PROTECT, related_name='accounts')
    tier = models.ForeignKey(LoyaltyTier, null=True, on_delete=models.SET_NULL)
    points_balance = models.IntegerField(default=0)
    lifetime_points = models.IntegerField(default=0)
    points_redeemed = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    def update_tier(self):
        """Update tier based on lifetime points."""
        applicable_tiers = self.program.tiers.filter(
            min_points__lte=self.lifetime_points
        ).order_by('-min_points')
        if applicable_tiers.exists():
            self.tier = applicable_tiers.first()
            self.save()
```

### PointTransaction

Record of point transactions.

```python
TRANSACTION_TYPES = [
    ('earn', 'Earned'),
    ('redeem', 'Redeemed'),
    ('bonus', 'Bonus'),
    ('adjustment', 'Adjustment'),
    ('expire', 'Expired'),
    ('referral', 'Referral Bonus'),
]

class PointTransaction(models.Model):
    account = models.ForeignKey(LoyaltyAccount, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    points = models.IntegerField()
    balance_after = models.IntegerField()
    description = models.CharField(max_length=200)
    reference_type = models.CharField(max_length=50, blank=True)
    reference_id = models.IntegerField(null=True)
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
```

### LoyaltyReward

Available rewards for redemption.

```python
REWARD_TYPES = [
    ('discount', 'Discount'),
    ('free_service', 'Free Service'),
    ('free_product', 'Free Product'),
    ('voucher', 'Voucher'),
    ('special', 'Special Reward'),
]

class LoyaltyReward(models.Model):
    program = models.ForeignKey(LoyaltyProgram, on_delete=models.CASCADE, related_name='rewards')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    reward_type = models.CharField(max_length=20, choices=REWARD_TYPES)
    points_cost = models.IntegerField()
    value = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    min_tier = models.ForeignKey(LoyaltyTier, null=True, on_delete=models.SET_NULL)
    quantity_available = models.IntegerField(null=True)
    quantity_redeemed = models.IntegerField(default=0)
    valid_from = models.DateTimeField(null=True)
    valid_until = models.DateTimeField(null=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
```

### RewardRedemption

Record of reward redemptions.

```python
STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('fulfilled', 'Fulfilled'),
    ('cancelled', 'Cancelled'),
    ('expired', 'Expired'),
]

class RewardRedemption(models.Model):
    account = models.ForeignKey(LoyaltyAccount, on_delete=models.CASCADE, related_name='redemptions')
    reward = models.ForeignKey(LoyaltyReward, on_delete=models.PROTECT, related_name='redemptions')
    points_spent = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    code = models.CharField(max_length=50, unique=True)  # Auto-generated
    notes = models.TextField(blank=True)
    approved_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    fulfilled_at = models.DateTimeField(null=True)
```

### ReferralProgram

Referral bonus configuration.

```python
class ReferralProgram(models.Model):
    program = models.OneToOneField(LoyaltyProgram, on_delete=models.CASCADE)
    referrer_bonus = models.IntegerField(default=100)  # Points for referrer
    referred_bonus = models.IntegerField(default=50)   # Points for new customer
    is_active = models.BooleanField(default=True)
```

### Referral

Track referrals between users.

```python
STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('completed', 'Completed'),
    ('expired', 'Expired'),
]

class Referral(models.Model):
    referrer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loyalty_referrals_made')
    referred = models.ForeignKey(User, null=True, on_delete=models.CASCADE, related_name='loyalty_referrals_received')
    referred_email = models.EmailField()
    code = models.CharField(max_length=20, unique=True)  # Auto-generated
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    referrer_points_awarded = models.IntegerField(default=0)
    referred_points_awarded = models.IntegerField(default=0)
    completed_at = models.DateTimeField(null=True)
```

## Workflows

### Enrolling a Customer

```python
from apps.loyalty.models import LoyaltyProgram, LoyaltyAccount, LoyaltyTier

program = LoyaltyProgram.objects.get(is_active=True)
base_tier = LoyaltyTier.objects.filter(program=program).order_by('min_points').first()

account = LoyaltyAccount.objects.create(
    user=customer,
    program=program,
    tier=base_tier,
)
```

### Earning Points on Purchase

```python
from apps.loyalty.models import LoyaltyAccount, PointTransaction
from decimal import Decimal

def award_purchase_points(user, purchase_amount, reference_type, reference_id):
    account = LoyaltyAccount.objects.get(user=user, is_active=True)
    program = account.program

    # Calculate points (with tier multiplier)
    base_points = int(purchase_amount * program.points_per_currency)
    multiplier = account.tier.points_multiplier if account.tier else 1
    points = int(base_points * multiplier)

    # Update account
    account.points_balance += points
    account.lifetime_points += points
    account.save()

    # Record transaction
    PointTransaction.objects.create(
        account=account,
        transaction_type='earn',
        points=points,
        balance_after=account.points_balance,
        description=f'Purchase - {purchase_amount} MXN',
        reference_type=reference_type,
        reference_id=reference_id,
    )

    # Check for tier upgrade
    account.update_tier()

    return points
```

### Redeeming a Reward

```python
from apps.loyalty.models import LoyaltyReward, RewardRedemption, PointTransaction

def redeem_reward(account, reward):
    # Validate
    if account.points_balance < reward.points_cost:
        raise ValueError('Insufficient points')
    if reward.min_tier and account.tier:
        if account.tier.min_points < reward.min_tier.min_points:
            raise ValueError('Tier requirement not met')

    # Deduct points
    account.points_balance -= reward.points_cost
    account.points_redeemed += reward.points_cost
    account.save()

    # Record transaction
    PointTransaction.objects.create(
        account=account,
        transaction_type='redeem',
        points=-reward.points_cost,
        balance_after=account.points_balance,
        description=f'Redeemed: {reward.name}',
    )

    # Create redemption record
    redemption = RewardRedemption.objects.create(
        account=account,
        reward=reward,
        points_spent=reward.points_cost,
        status='pending',
    )

    # Update reward quantity
    reward.quantity_redeemed += 1
    reward.save()

    return redemption
```

### Processing a Referral

```python
from apps.loyalty.models import Referral, ReferralProgram, PointTransaction
from django.utils import timezone

def complete_referral(referral, referred_user):
    referral_program = ReferralProgram.objects.get(is_active=True)

    # Award referrer
    referrer_account = LoyaltyAccount.objects.get(user=referral.referrer)
    referrer_account.points_balance += referral_program.referrer_bonus
    referrer_account.lifetime_points += referral_program.referrer_bonus
    referrer_account.save()

    PointTransaction.objects.create(
        account=referrer_account,
        transaction_type='referral',
        points=referral_program.referrer_bonus,
        balance_after=referrer_account.points_balance,
        description=f'Referral bonus for {referred_user.email}',
    )

    # Award referred
    referred_account = LoyaltyAccount.objects.get(user=referred_user)
    referred_account.points_balance += referral_program.referred_bonus
    referred_account.lifetime_points += referral_program.referred_bonus
    referred_account.save()

    PointTransaction.objects.create(
        account=referred_account,
        transaction_type='referral',
        points=referral_program.referred_bonus,
        balance_after=referred_account.points_balance,
        description='Welcome bonus from referral',
    )

    # Update referral
    referral.referred = referred_user
    referral.status = 'completed'
    referral.referrer_points_awarded = referral_program.referrer_bonus
    referral.referred_points_awarded = referral_program.referred_bonus
    referral.completed_at = timezone.now()
    referral.save()
```

## Integration Points

### With Billing/Invoices

```python
# Award points when invoice is paid
def on_invoice_paid(invoice):
    if invoice.customer.loyalty_account:
        award_purchase_points(
            user=invoice.customer,
            purchase_amount=invoice.total,
            reference_type='billing.invoice',
            reference_id=invoice.pk,
        )
```

### With Store Orders

```python
# Award points on order completion
def on_order_completed(order):
    if hasattr(order.customer, 'loyalty_account'):
        award_purchase_points(
            user=order.customer,
            purchase_amount=order.total,
            reference_type='store.order',
            reference_id=order.pk,
        )
```

## Query Examples

```python
from apps.loyalty.models import (
    LoyaltyAccount, PointTransaction, LoyaltyReward, RewardRedemption, Referral
)
from django.db.models import Sum, Count

# Top point earners
top_accounts = LoyaltyAccount.objects.filter(
    is_active=True
).order_by('-lifetime_points')[:10]

# Points by tier
by_tier = LoyaltyAccount.objects.values('tier__name').annotate(
    count=Count('id'),
    total_points=Sum('points_balance')
)

# Recent transactions
recent = PointTransaction.objects.filter(
    created_at__gte=timezone.now() - timedelta(days=30)
).select_related('account__user')

# Popular rewards
popular = LoyaltyReward.objects.filter(
    is_active=True
).order_by('-quantity_redeemed')

# Pending redemptions
pending = RewardRedemption.objects.filter(
    status='pending'
).select_related('account__user', 'reward')

# Referral leaderboard
top_referrers = Referral.objects.filter(
    status='completed'
).values('referrer__email').annotate(
    count=Count('id'),
    points=Sum('referrer_points_awarded')
).order_by('-count')[:10]

# Points about to expire (if implementing expiration)
expiring = PointTransaction.objects.filter(
    transaction_type='earn',
    created_at__lte=timezone.now() - timedelta(days=365)
)
```

## Testing

Location: `tests/test_loyalty.py`

```bash
python -m pytest tests/test_loyalty.py -v
```
