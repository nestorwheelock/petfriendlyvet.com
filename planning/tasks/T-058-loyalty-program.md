# T-058: Loyalty & Rewards Program

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md and [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Full Stack Developer
**Objective**: Implement points-based loyalty program
**Related Story**: S-016
**Epoch**: 5
**Estimate**: 5 hours

### Constraints
**Allowed File Paths**: apps/loyalty/
**Forbidden Paths**: None

### Deliverables
- [ ] LoyaltyTier model
- [ ] LoyaltyMembership model
- [ ] PointsTransaction model
- [ ] Points earning rules
- [ ] Points redemption
- [ ] Tier progression

### Wireframe Reference
See: `planning/wireframes/20-loyalty-program.txt`

### Implementation Details

#### Models
```python
from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()


class LoyaltyTier(models.Model):
    """Loyalty program tiers."""

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    # Requirements
    min_points = models.IntegerField()
    min_lifetime_spending = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )

    # Benefits
    points_multiplier = models.DecimalField(
        max_digits=3, decimal_places=2, default=1.00
    )  # 1.5x, 2x, etc.
    discount_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )
    free_services = models.JSONField(default=list)
    # ['nail_trim', 'bath_discount', ...]

    # Visual
    color = models.CharField(max_length=20, default='#gray')
    icon = models.CharField(max_length=50, blank=True)
    badge_image = models.ImageField(upload_to='loyalty/', null=True, blank=True)

    # Ordering
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']


class LoyaltyMembership(models.Model):
    """User's loyalty membership."""

    owner = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name='loyalty'
    )

    tier = models.ForeignKey(
        LoyaltyTier, on_delete=models.SET_NULL,
        null=True, related_name='members'
    )

    # Points
    current_points = models.IntegerField(default=0)
    lifetime_points = models.IntegerField(default=0)
    points_expiring_soon = models.IntegerField(default=0)
    next_expiry_date = models.DateField(null=True)

    # Progress to next tier
    next_tier = models.ForeignKey(
        LoyaltyTier, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+'
    )
    points_to_next_tier = models.IntegerField(null=True)

    # Referrals
    referral_code = models.CharField(max_length=20, unique=True)
    referrals_count = models.IntegerField(default=0)
    referral_points_earned = models.IntegerField(default=0)

    enrolled_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = self._generate_referral_code()
        super().save(*args, **kwargs)

    def _generate_referral_code(self):
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


class PointsTransaction(models.Model):
    """Points earned or redeemed."""

    TRANSACTION_TYPES = [
        ('earn', 'Ganados'),
        ('redeem', 'Canjeados'),
        ('expire', 'Expirados'),
        ('adjust', 'Ajuste'),
        ('bonus', 'Bono'),
        ('referral', 'Referido'),
    ]

    membership = models.ForeignKey(
        LoyaltyMembership, on_delete=models.CASCADE,
        related_name='transactions'
    )

    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    points = models.IntegerField()  # Positive for earn, negative for redeem/expire
    balance_after = models.IntegerField()

    # Source
    description = models.CharField(max_length=500)
    order = models.ForeignKey(
        'store.Order', on_delete=models.SET_NULL,
        null=True, blank=True
    )
    invoice = models.ForeignKey(
        'billing.Invoice', on_delete=models.SET_NULL,
        null=True, blank=True
    )
    reward = models.ForeignKey(
        'Reward', on_delete=models.SET_NULL,
        null=True, blank=True
    )

    # Expiry
    expires_at = models.DateField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class EarningRule(models.Model):
    """Rules for earning points."""

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    RULE_TYPES = [
        ('purchase', 'Por compra'),
        ('service', 'Por servicio'),
        ('referral', 'Por referido'),
        ('review', 'Por reseña'),
        ('birthday', 'Cumpleaños'),
        ('milestone', 'Meta alcanzada'),
    ]
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES)

    # Points calculation
    points_per_peso = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )  # e.g., 1 point per $10
    fixed_points = models.IntegerField(default=0)

    # Conditions
    min_purchase = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    applies_to_services = models.ManyToManyField(
        'appointments.ServiceType', blank=True
    )
    applies_to_categories = models.ManyToManyField(
        'store.Category', blank=True
    )

    # Multiplier bonus
    multiplier = models.DecimalField(
        max_digits=3, decimal_places=2, default=1.00
    )
    multiplier_start = models.DateTimeField(null=True, blank=True)
    multiplier_end = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']


class Reward(models.Model):
    """Rewards available for redemption."""

    name = models.CharField(max_length=200)
    description = models.TextField()

    REWARD_TYPES = [
        ('discount', 'Descuento'),
        ('free_service', 'Servicio gratis'),
        ('free_product', 'Producto gratis'),
        ('upgrade', 'Mejora'),
        ('experience', 'Experiencia'),
    ]
    reward_type = models.CharField(max_length=20, choices=REWARD_TYPES)

    # Cost
    points_cost = models.IntegerField()

    # Value
    discount_percent = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    free_service = models.ForeignKey(
        'appointments.ServiceType', on_delete=models.SET_NULL,
        null=True, blank=True
    )
    free_product = models.ForeignKey(
        'store.Product', on_delete=models.SET_NULL,
        null=True, blank=True
    )

    # Availability
    min_tier = models.ForeignKey(
        LoyaltyTier, on_delete=models.SET_NULL,
        null=True, blank=True
    )
    quantity_available = models.IntegerField(null=True)  # null = unlimited
    quantity_redeemed = models.IntegerField(default=0)
    max_per_member = models.IntegerField(default=1)

    valid_from = models.DateTimeField(null=True)
    valid_until = models.DateTimeField(null=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['points_cost']


class RewardRedemption(models.Model):
    """Record of reward redemptions."""

    membership = models.ForeignKey(
        LoyaltyMembership, on_delete=models.CASCADE,
        related_name='redemptions'
    )
    reward = models.ForeignKey(Reward, on_delete=models.PROTECT)
    transaction = models.OneToOneField(
        PointsTransaction, on_delete=models.SET_NULL,
        null=True
    )

    # Coupon code generated
    coupon_code = models.CharField(max_length=50, unique=True)
    coupon = models.ForeignKey(
        'billing.CouponCode', on_delete=models.SET_NULL,
        null=True, blank=True
    )

    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True)
    used_on_order = models.ForeignKey(
        'store.Order', on_delete=models.SET_NULL,
        null=True, blank=True
    )

    expires_at = models.DateTimeField()
    redeemed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-redeemed_at']
```

#### Loyalty Service
```python
class LoyaltyService:
    """Loyalty program operations."""

    def earn_points(
        self,
        membership: LoyaltyMembership,
        amount: Decimal,
        source: str,
        order=None,
        invoice=None
    ) -> int:
        """Award points for a purchase."""

        # Get applicable earning rules
        rules = EarningRule.objects.filter(
            is_active=True,
            rule_type='purchase'
        )

        total_points = 0

        for rule in rules:
            if rule.min_purchase and amount < rule.min_purchase:
                continue

            points = int(amount * rule.points_per_peso)
            points += rule.fixed_points

            # Apply multiplier
            multiplier = rule.multiplier
            if membership.tier:
                multiplier *= membership.tier.points_multiplier

            points = int(points * multiplier)
            total_points += points

        if total_points > 0:
            # Create transaction
            PointsTransaction.objects.create(
                membership=membership,
                transaction_type='earn',
                points=total_points,
                balance_after=membership.current_points + total_points,
                description=source,
                order=order,
                invoice=invoice,
                expires_at=timezone.now().date() + timedelta(days=365)
            )

            membership.current_points += total_points
            membership.lifetime_points += total_points
            membership.save()

            # Check tier upgrade
            self.check_tier_upgrade(membership)

        return total_points

    def redeem_points(
        self,
        membership: LoyaltyMembership,
        reward: Reward
    ) -> RewardRedemption:
        """Redeem points for reward."""

        if membership.current_points < reward.points_cost:
            raise ValueError("Puntos insuficientes")

        if reward.min_tier and membership.tier:
            if membership.tier.order < reward.min_tier.order:
                raise ValueError("Nivel insuficiente")

        # Create coupon code for the reward
        coupon_code = self._generate_coupon_code()

        # Create the actual coupon
        from apps.billing.models import CouponCode

        coupon = None
        if reward.discount_percent or reward.discount_amount:
            coupon = CouponCode.objects.create(
                code=coupon_code,
                description=f"Reward: {reward.name}",
                discount_type='percent' if reward.discount_percent else 'fixed',
                discount_value=reward.discount_percent or reward.discount_amount,
                max_uses=1,
                valid_from=timezone.now(),
                valid_until=timezone.now() + timedelta(days=30)
            )

        # Create transaction
        transaction = PointsTransaction.objects.create(
            membership=membership,
            transaction_type='redeem',
            points=-reward.points_cost,
            balance_after=membership.current_points - reward.points_cost,
            description=f"Canje: {reward.name}"
        )

        membership.current_points -= reward.points_cost
        membership.save()

        # Create redemption record
        redemption = RewardRedemption.objects.create(
            membership=membership,
            reward=reward,
            transaction=transaction,
            coupon_code=coupon_code,
            coupon=coupon,
            expires_at=timezone.now() + timedelta(days=30)
        )

        reward.quantity_redeemed += 1
        reward.save()

        return redemption

    def check_tier_upgrade(self, membership: LoyaltyMembership):
        """Check and apply tier upgrades."""
        tiers = LoyaltyTier.objects.filter(
            min_points__lte=membership.lifetime_points
        ).order_by('-min_points')

        if tiers.exists():
            new_tier = tiers.first()
            if membership.tier != new_tier:
                old_tier = membership.tier
                membership.tier = new_tier
                membership.save()

                # Notify user of upgrade
                self._send_tier_upgrade_notification(membership, old_tier, new_tier)

    def _generate_coupon_code(self):
        import random
        import string
        return 'RW-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
```

### Test Cases
- [ ] Points earning calculates correctly
- [ ] Tier multiplier applies
- [ ] Redemption deducts points
- [ ] Coupon generated for rewards
- [ ] Tier upgrade triggers
- [ ] Expiry tracking works
- [ ] Referral points credited

### Definition of Done
- [ ] Complete loyalty system
- [ ] Admin for managing rewards
- [ ] Customer portal integration
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-040: Billing/Invoicing
- T-038: Checkout & Stripe
