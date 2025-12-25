"""E2E test for loyalty program journey.

Simulates the complete loyalty program workflow using actual models.
Tests the customer loyalty system.
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta

from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db(transaction=True)
class TestLoyaltyProgramJourney:
    """Complete loyalty program journey."""

    @pytest.fixture
    def loyalty_program(self, db):
        """Create the main loyalty program."""
        from apps.loyalty.models import LoyaltyProgram

        return LoyaltyProgram.objects.create(
            name='PetFriendly Rewards',
            description='Gana puntos con cada compra',
            points_per_currency=Decimal('1.0'),
            is_active=True,
        )

    @pytest.fixture
    def loyalty_tiers(self, db, loyalty_program):
        """Create loyalty tiers."""
        from apps.loyalty.models import LoyaltyTier

        tiers = [
            LoyaltyTier.objects.create(
                program=loyalty_program,
                name='Bronce',
                min_points=0,
                discount_percent=Decimal('5.0'),
                points_multiplier=Decimal('1.0'),
                display_order=1,
            ),
            LoyaltyTier.objects.create(
                program=loyalty_program,
                name='Plata',
                min_points=1000,
                discount_percent=Decimal('10.0'),
                points_multiplier=Decimal('1.25'),
                display_order=2,
            ),
            LoyaltyTier.objects.create(
                program=loyalty_program,
                name='Oro',
                min_points=5000,
                discount_percent=Decimal('15.0'),
                points_multiplier=Decimal('1.5'),
                display_order=3,
            ),
        ]
        return tiers

    @pytest.fixture
    def rewards(self, db, loyalty_program):
        """Create available rewards."""
        from apps.loyalty.models import LoyaltyReward

        return [
            LoyaltyReward.objects.create(
                program=loyalty_program,
                name='Descuento $50',
                description='$50 de descuento en tu próxima compra',
                points_cost=500,
                reward_type='discount',
                value=Decimal('50.00'),
                is_active=True,
            ),
            LoyaltyReward.objects.create(
                program=loyalty_program,
                name='Consulta Gratis',
                description='Una consulta general sin costo',
                points_cost=1500,
                reward_type='free_service',
                value=Decimal('500.00'),
                is_active=True,
            ),
        ]

    @pytest.fixture
    def customer(self, db):
        """Create a customer."""
        return User.objects.create_user(
            username='loyal.customer@example.com',
            email='loyal.customer@example.com',
            password='loyal123',
            first_name='Leal',
            last_name='Cliente',
            role='owner',
        )

    def test_complete_loyalty_journey(
        self, db, loyalty_program, loyalty_tiers, rewards, customer
    ):
        """Test loyalty program from enrollment to rewards."""
        from apps.loyalty.models import (
            LoyaltyAccount, PointTransaction, RewardRedemption, Referral
        )
        from apps.notifications.models import Notification

        # =========================================================================
        # STEP 1: Customer Enrolls in Loyalty Program
        # =========================================================================
        loyalty_account = LoyaltyAccount.objects.create(
            user=customer,
            program=loyalty_program,
            tier=loyalty_tiers[0],  # Start at Bronce
            points_balance=0,
            lifetime_points=0,
        )

        assert loyalty_account.pk is not None
        assert loyalty_account.tier.name == 'Bronce'

        # Welcome notification
        Notification.objects.create(
            user=customer,
            notification_type='loyalty_welcome',
            title='¡Bienvenido a PetFriendly Rewards!',
            message='Ahora ganas puntos con cada compra.',
            email_sent=True,
            email_sent_at=timezone.now(),
        )

        # =========================================================================
        # STEP 2: Customer Earns Points from Purchase
        # =========================================================================
        points_earned = 500

        PointTransaction.objects.create(
            account=loyalty_account,
            transaction_type='earn',
            points=points_earned,
            balance_after=points_earned,
            description='Puntos por compra',
            reference_type='order',
            reference_id=1,
        )

        loyalty_account.points_balance = points_earned
        loyalty_account.lifetime_points = points_earned
        loyalty_account.save()

        assert loyalty_account.points_balance == 500

        # =========================================================================
        # STEP 3: More Purchases - Tier Upgrade
        # =========================================================================
        more_points = 600

        PointTransaction.objects.create(
            account=loyalty_account,
            transaction_type='earn',
            points=more_points,
            balance_after=points_earned + more_points,
            description='Puntos por segunda compra',
            reference_type='order',
            reference_id=2,
        )

        loyalty_account.points_balance += more_points
        loyalty_account.lifetime_points += more_points
        loyalty_account.save()

        # Update tier (now at 1100 points, qualifies for Plata)
        loyalty_account.update_tier()
        loyalty_account.refresh_from_db()
        assert loyalty_account.tier.name == 'Plata'

        # Tier upgrade notification
        Notification.objects.create(
            user=customer,
            notification_type='tier_upgrade',
            title='¡Subiste a Nivel Plata!',
            message='Nuevos beneficios desbloqueados.',
            email_sent=True,
            email_sent_at=timezone.now(),
        )

        # =========================================================================
        # STEP 4: Redeem Reward
        # =========================================================================
        reward = rewards[0]  # $50 discount (500 points)

        redemption = RewardRedemption.objects.create(
            account=loyalty_account,
            reward=reward,
            points_spent=reward.points_cost,
            status='approved',
        )

        # Deduct points
        PointTransaction.objects.create(
            account=loyalty_account,
            transaction_type='redeem',
            points=-reward.points_cost,
            balance_after=loyalty_account.points_balance - reward.points_cost,
            description=f'Canje: {reward.name}',
            reference_type='redemption',
            reference_id=redemption.pk,
        )

        loyalty_account.points_balance -= reward.points_cost
        loyalty_account.points_redeemed += reward.points_cost
        loyalty_account.save()

        assert redemption.pk is not None
        loyalty_account.refresh_from_db()
        assert loyalty_account.points_balance == 600  # 1100 - 500

        # =========================================================================
        # STEP 5: Refer a Friend
        # =========================================================================
        referred_friend = User.objects.create_user(
            username='referred@example.com',
            email='referred@example.com',
            password='friend123',
            role='owner',
        )

        referral = Referral.objects.create(
            referrer=customer,
            referred=referred_friend,
            referred_email='referred@example.com',
            status='pending',
        )

        # Friend completes first purchase
        referral.status = 'completed'
        referral.completed_at = timezone.now()
        referral.referrer_points_awarded = 200
        referral.referred_points_awarded = 100
        referral.save()

        # Award referral bonus
        PointTransaction.objects.create(
            account=loyalty_account,
            transaction_type='referral',
            points=200,
            balance_after=loyalty_account.points_balance + 200,
            description=f'Bono por referido: {referred_friend.email}',
            reference_type='referral',
            reference_id=referral.pk,
        )

        loyalty_account.points_balance += 200
        loyalty_account.lifetime_points += 200
        loyalty_account.save()

        # =========================================================================
        # VERIFICATION
        # =========================================================================
        loyalty_account.refresh_from_db()
        referral.refresh_from_db()

        # Customer enrolled and has points
        assert loyalty_account.points_balance == 800  # 600 + 200
        assert loyalty_account.lifetime_points == 1300  # 500 + 600 + 200

        # Tier upgraded
        assert loyalty_account.tier.name == 'Plata'

        # Reward redeemed
        assert RewardRedemption.objects.filter(
            account=loyalty_account,
            status='approved'
        ).exists()

        # Referral completed
        assert referral.status == 'completed'


@pytest.mark.django_db(transaction=True)
class TestLoyaltyPointTransactions:
    """Test point transaction management."""

    def test_transaction_types(self, db):
        """Different transaction types work correctly."""
        from apps.loyalty.models import (
            LoyaltyProgram, LoyaltyTier, LoyaltyAccount, PointTransaction
        )

        program = LoyaltyProgram.objects.create(
            name='Test Rewards',
            points_per_currency=Decimal('1.0'),
            is_active=True,
        )

        tier = LoyaltyTier.objects.create(
            program=program,
            name='Basic',
            min_points=0,
            points_multiplier=Decimal('1.0'),
            display_order=1,
        )

        customer = User.objects.create_user(
            username='txn.test@example.com',
            email='txn.test@example.com',
            password='test123',
            role='owner',
        )

        account = LoyaltyAccount.objects.create(
            user=customer,
            program=program,
            tier=tier,
            points_balance=1000,
            lifetime_points=1000,
        )

        # Create various transaction types
        transactions = [
            ('earn', 100, 1100),
            ('bonus', 50, 1150),
            ('redeem', -200, 950),
            ('adjustment', -50, 900),
        ]

        for txn_type, points, balance_after in transactions:
            PointTransaction.objects.create(
                account=account,
                transaction_type=txn_type,
                points=points,
                balance_after=balance_after,
                description=f'Test {txn_type} transaction',
            )

        # All transactions recorded
        assert PointTransaction.objects.filter(account=account).count() == 4


@pytest.mark.django_db(transaction=True)
class TestLoyaltyRewards:
    """Test loyalty reward redemption."""

    def test_reward_redemption_statuses(self, db):
        """Rewards go through different statuses."""
        from apps.loyalty.models import (
            LoyaltyProgram, LoyaltyTier, LoyaltyAccount,
            LoyaltyReward, RewardRedemption
        )

        program = LoyaltyProgram.objects.create(
            name='Reward Test',
            points_per_currency=Decimal('1.0'),
            is_active=True,
        )

        tier = LoyaltyTier.objects.create(
            program=program,
            name='Basic',
            min_points=0,
            display_order=1,
        )

        customer = User.objects.create_user(
            username='reward.test@example.com',
            email='reward.test@example.com',
            password='test123',
            role='owner',
        )

        account = LoyaltyAccount.objects.create(
            user=customer,
            program=program,
            tier=tier,
            points_balance=2000,
        )

        reward = LoyaltyReward.objects.create(
            program=program,
            name='Test Reward',
            points_cost=500,
            reward_type='discount',
            value=Decimal('100.00'),
            is_active=True,
        )

        # Create redemption
        redemption = RewardRedemption.objects.create(
            account=account,
            reward=reward,
            points_spent=500,
            status='pending',
        )

        assert redemption.code is not None  # Auto-generated

        # Approve
        redemption.status = 'approved'
        redemption.save()

        # Fulfill
        redemption.status = 'fulfilled'
        redemption.fulfilled_at = timezone.now()
        redemption.save()

        redemption.refresh_from_db()
        assert redemption.status == 'fulfilled'
        assert redemption.fulfilled_at is not None
