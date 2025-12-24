"""Loyalty and rewards models."""
from django.conf import settings
from django.db import models


class LoyaltyProgram(models.Model):
    """Loyalty program configuration."""

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    points_per_currency = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1.0,
        help_text="Points earned per currency unit spent"
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class LoyaltyTier(models.Model):
    """Loyalty program tier levels."""

    program = models.ForeignKey(
        LoyaltyProgram,
        on_delete=models.CASCADE,
        related_name='tiers'
    )

    name = models.CharField(max_length=50)
    min_points = models.IntegerField(default=0)
    max_points = models.IntegerField(null=True, blank=True)

    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    points_multiplier = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=1.0
    )

    benefits = models.JSONField(default=list, blank=True)
    color = models.CharField(max_length=20, blank=True)
    icon = models.CharField(max_length=50, blank=True)

    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'min_points']

    def __str__(self):
        return f"{self.program.name} - {self.name}"


class LoyaltyAccount(models.Model):
    """Customer loyalty account."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='loyalty_account'
    )
    program = models.ForeignKey(
        LoyaltyProgram,
        on_delete=models.PROTECT,
        related_name='accounts'
    )
    tier = models.ForeignKey(
        LoyaltyTier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accounts'
    )

    points_balance = models.IntegerField(default=0)
    lifetime_points = models.IntegerField(default=0)
    points_redeemed = models.IntegerField(default=0)

    is_active = models.BooleanField(default=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-lifetime_points']

    def __str__(self):
        return f"{self.user.email} - {self.points_balance} points"

    def update_tier(self):
        """Update tier based on lifetime points."""
        applicable_tiers = self.program.tiers.filter(
            min_points__lte=self.lifetime_points
        ).order_by('-min_points')
        if applicable_tiers.exists():
            self.tier = applicable_tiers.first()
            self.save()


class PointTransaction(models.Model):
    """Record of point transactions."""

    TRANSACTION_TYPES = [
        ('earn', 'Earned'),
        ('redeem', 'Redeemed'),
        ('bonus', 'Bonus'),
        ('adjustment', 'Adjustment'),
        ('expire', 'Expired'),
        ('referral', 'Referral Bonus'),
    ]

    account = models.ForeignKey(
        LoyaltyAccount,
        on_delete=models.CASCADE,
        related_name='transactions'
    )

    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    points = models.IntegerField()
    balance_after = models.IntegerField()

    description = models.CharField(max_length=200)
    reference_type = models.CharField(max_length=50, blank=True)
    reference_id = models.IntegerField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        sign = '+' if self.points > 0 else ''
        return f"{self.account.user.email}: {sign}{self.points} ({self.transaction_type})"


class LoyaltyReward(models.Model):
    """Available rewards for redemption."""

    REWARD_TYPES = [
        ('discount', 'Discount'),
        ('free_service', 'Free Service'),
        ('free_product', 'Free Product'),
        ('voucher', 'Voucher'),
        ('special', 'Special Reward'),
    ]

    program = models.ForeignKey(
        LoyaltyProgram,
        on_delete=models.CASCADE,
        related_name='rewards'
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    reward_type = models.CharField(max_length=20, choices=REWARD_TYPES)

    points_cost = models.IntegerField()
    value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    min_tier = models.ForeignKey(
        LoyaltyTier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Minimum tier required to redeem"
    )

    quantity_available = models.IntegerField(null=True, blank=True)
    quantity_redeemed = models.IntegerField(default=0)

    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['points_cost']

    def __str__(self):
        return f"{self.name} ({self.points_cost} points)"


class RewardRedemption(models.Model):
    """Record of reward redemptions."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('fulfilled', 'Fulfilled'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]

    account = models.ForeignKey(
        LoyaltyAccount,
        on_delete=models.CASCADE,
        related_name='redemptions'
    )
    reward = models.ForeignKey(
        LoyaltyReward,
        on_delete=models.PROTECT,
        related_name='redemptions'
    )

    points_spent = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    code = models.CharField(max_length=50, unique=True, blank=True)
    notes = models.TextField(blank=True)

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_redemptions'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    fulfilled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.account.user.email} - {self.reward.name}"

    def save(self, *args, **kwargs):
        if not self.code:
            import uuid
            self.code = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)


class ReferralProgram(models.Model):
    """Referral bonus configuration."""

    program = models.OneToOneField(
        LoyaltyProgram,
        on_delete=models.CASCADE,
        related_name='referral_program'
    )

    referrer_bonus = models.IntegerField(
        default=100,
        help_text="Points for referrer when referred user makes first purchase"
    )
    referred_bonus = models.IntegerField(
        default=50,
        help_text="Points for referred user on first purchase"
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        pass

    def __str__(self):
        return f"Referral Program for {self.program.name}"


class Referral(models.Model):
    """Track referrals between users."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
    ]

    referrer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='loyalty_referrals_made'
    )
    referred = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='loyalty_referrals_received',
        null=True,
        blank=True
    )
    referred_email = models.EmailField()

    code = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    referrer_points_awarded = models.IntegerField(default=0)
    referred_points_awarded = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.referrer.email} -> {self.referred_email}"

    def save(self, *args, **kwargs):
        if not self.code:
            import uuid
            self.code = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)
