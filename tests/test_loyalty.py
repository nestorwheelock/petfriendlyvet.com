"""Tests for Loyalty and Rewards app (TDD first)."""
import pytest

from apps.accounts.models import User

pytestmark = pytest.mark.django_db


class TestLoyaltyProgramModel:
    """Tests for LoyaltyProgram model."""

    def test_create_program(self):
        """Test creating a loyalty program."""
        from apps.loyalty.models import LoyaltyProgram

        program = LoyaltyProgram.objects.create(
            name='Pet Rewards',
            description='Earn points on every visit',
            points_per_currency=1.0,
        )

        assert program.name == 'Pet Rewards'
        assert program.is_active is True


class TestLoyaltyTierModel:
    """Tests for LoyaltyTier model."""

    def test_create_tier(self):
        """Test creating loyalty tiers."""
        from apps.loyalty.models import LoyaltyProgram, LoyaltyTier

        program = LoyaltyProgram.objects.create(name='Pet Rewards')

        bronze = LoyaltyTier.objects.create(
            program=program,
            name='Bronze',
            min_points=0,
            max_points=999,
            discount_percent=0,
        )
        silver = LoyaltyTier.objects.create(
            program=program,
            name='Silver',
            min_points=1000,
            max_points=4999,
            discount_percent=5,
        )
        gold = LoyaltyTier.objects.create(
            program=program,
            name='Gold',
            min_points=5000,
            discount_percent=10,
            points_multiplier=1.5,
        )

        assert program.tiers.count() == 3
        assert gold.discount_percent == 10


class TestLoyaltyAccountModel:
    """Tests for LoyaltyAccount model."""

    def test_create_account(self, user):
        """Test creating a loyalty account."""
        from apps.loyalty.models import LoyaltyProgram, LoyaltyAccount

        program = LoyaltyProgram.objects.create(name='Pet Rewards')
        account = LoyaltyAccount.objects.create(
            user=user,
            program=program,
        )

        assert account.points_balance == 0
        assert account.lifetime_points == 0
        assert account.is_active is True

    def test_update_tier(self, user):
        """Test tier auto-update based on points."""
        from apps.loyalty.models import LoyaltyProgram, LoyaltyTier, LoyaltyAccount

        program = LoyaltyProgram.objects.create(name='Pet Rewards')
        bronze = LoyaltyTier.objects.create(
            program=program, name='Bronze', min_points=0, display_order=0
        )
        silver = LoyaltyTier.objects.create(
            program=program, name='Silver', min_points=1000, display_order=1
        )

        account = LoyaltyAccount.objects.create(
            user=user, program=program, lifetime_points=1500
        )
        account.update_tier()

        assert account.tier == silver


class TestPointTransactionModel:
    """Tests for PointTransaction model."""

    def test_earn_points(self, user):
        """Test earning points."""
        from apps.loyalty.models import (
            LoyaltyProgram, LoyaltyAccount, PointTransaction
        )

        program = LoyaltyProgram.objects.create(name='Pet Rewards')
        account = LoyaltyAccount.objects.create(user=user, program=program)

        transaction = PointTransaction.objects.create(
            account=account,
            transaction_type='earn',
            points=100,
            balance_after=100,
            description='Purchase: Consultation',
        )

        assert transaction.points == 100
        assert 'earn' in str(transaction)

    def test_redeem_points(self, user):
        """Test redeeming points."""
        from apps.loyalty.models import (
            LoyaltyProgram, LoyaltyAccount, PointTransaction
        )

        program = LoyaltyProgram.objects.create(name='Pet Rewards')
        account = LoyaltyAccount.objects.create(
            user=user, program=program, points_balance=500
        )

        transaction = PointTransaction.objects.create(
            account=account,
            transaction_type='redeem',
            points=-100,
            balance_after=400,
            description='Redeemed: Free nail trim',
        )

        assert transaction.points == -100


class TestLoyaltyRewardModel:
    """Tests for LoyaltyReward model."""

    def test_create_reward(self):
        """Test creating a reward."""
        from apps.loyalty.models import LoyaltyProgram, LoyaltyReward

        program = LoyaltyProgram.objects.create(name='Pet Rewards')
        reward = LoyaltyReward.objects.create(
            program=program,
            name='Free Nail Trim',
            reward_type='free_service',
            points_cost=200,
            is_active=True,
        )

        assert reward.points_cost == 200
        assert '200 points' in str(reward)


class TestRewardRedemptionModel:
    """Tests for RewardRedemption model."""

    def test_redeem_reward(self, user):
        """Test redeeming a reward."""
        from apps.loyalty.models import (
            LoyaltyProgram, LoyaltyAccount, LoyaltyReward, RewardRedemption
        )

        program = LoyaltyProgram.objects.create(name='Pet Rewards')
        account = LoyaltyAccount.objects.create(
            user=user, program=program, points_balance=500
        )
        reward = LoyaltyReward.objects.create(
            program=program,
            name='Free Consultation',
            reward_type='free_service',
            points_cost=300,
        )

        redemption = RewardRedemption.objects.create(
            account=account,
            reward=reward,
            points_spent=300,
            status='pending',
        )

        assert redemption.code != ''
        assert len(redemption.code) == 8


class TestReferralModel:
    """Tests for Referral model."""

    def test_create_referral(self, user):
        """Test creating a referral."""
        from apps.loyalty.models import Referral

        referral = Referral.objects.create(
            referrer=user,
            referred_email='newuser@example.com',
        )

        assert referral.code != ''
        assert referral.status == 'pending'


class TestLoyaltyAITools:
    """Tests for Loyalty AI tools."""

    def test_get_loyalty_status_tool_exists(self):
        """Test get_loyalty_status tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('get_loyalty_status')
        assert tool is not None

    def test_get_loyalty_status(self, user):
        """Test getting loyalty status."""
        from apps.ai_assistant.tools import get_loyalty_status
        from apps.loyalty.models import LoyaltyProgram, LoyaltyAccount

        program = LoyaltyProgram.objects.create(name='Pet Rewards')
        LoyaltyAccount.objects.create(
            user=user, program=program, points_balance=500
        )

        result = get_loyalty_status(user_id=user.id)

        assert result['success'] is True
        assert result['points_balance'] == 500

    def test_earn_points_tool_exists(self):
        """Test earn_points tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('earn_points')
        assert tool is not None

    def test_earn_points(self, user):
        """Test earning points."""
        from apps.ai_assistant.tools import earn_points
        from apps.loyalty.models import LoyaltyProgram, LoyaltyAccount

        program = LoyaltyProgram.objects.create(name='Pet Rewards')
        LoyaltyAccount.objects.create(
            user=user, program=program, points_balance=100
        )

        result = earn_points(
            user_id=user.id,
            points=50,
            description='Bonus points'
        )

        assert result['success'] is True
        assert result['new_balance'] == 150

    def test_redeem_reward_tool_exists(self):
        """Test redeem_reward tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('redeem_reward')
        assert tool is not None

    def test_redeem_reward(self, user):
        """Test redeeming a reward."""
        from apps.ai_assistant.tools import redeem_reward
        from apps.loyalty.models import (
            LoyaltyProgram, LoyaltyAccount, LoyaltyReward
        )

        program = LoyaltyProgram.objects.create(name='Pet Rewards')
        LoyaltyAccount.objects.create(
            user=user, program=program, points_balance=500
        )
        reward = LoyaltyReward.objects.create(
            program=program,
            name='Free Bath',
            reward_type='free_service',
            points_cost=200,
        )

        result = redeem_reward(user_id=user.id, reward_id=reward.id)

        assert result['success'] is True
        assert 'redemption_code' in result

    def test_get_available_rewards_tool_exists(self):
        """Test get_available_rewards tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('get_available_rewards')
        assert tool is not None

    def test_get_available_rewards(self, user):
        """Test getting available rewards."""
        from apps.ai_assistant.tools import get_available_rewards
        from apps.loyalty.models import (
            LoyaltyProgram, LoyaltyAccount, LoyaltyReward
        )

        program = LoyaltyProgram.objects.create(name='Pet Rewards')
        LoyaltyAccount.objects.create(
            user=user, program=program, points_balance=500
        )
        LoyaltyReward.objects.create(
            program=program,
            name='Free Bath',
            reward_type='free_service',
            points_cost=200,
            is_active=True,
        )

        result = get_available_rewards(user_id=user.id)

        assert result['success'] is True
        assert len(result['rewards']) >= 1

    def test_create_referral_tool_exists(self):
        """Test create_referral tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('create_referral')
        assert tool is not None

    def test_create_referral(self, user):
        """Test creating a referral."""
        from apps.ai_assistant.tools import create_referral

        result = create_referral(
            referrer_id=user.id,
            referred_email='friend@example.com'
        )

        assert result['success'] is True
        assert 'referral_code' in result


# Fixtures
@pytest.fixture
def user():
    """Create a test user."""
    return User.objects.create_user(
        username='loyaltyuser',
        email='loyalty@example.com',
        password='testpass123',
        first_name='Loyalty',
        last_name='User',
    )
