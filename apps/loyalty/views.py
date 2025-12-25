"""Loyalty app views for customer-facing pages."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import (
    LoyaltyAccount,
    LoyaltyProgram,
    LoyaltyReward,
    LoyaltyTier,
    PointTransaction,
    Referral,
    ReferralProgram,
    RewardRedemption,
)


def get_or_create_loyalty_account(user):
    """Get or create a loyalty account for the user."""
    try:
        return user.loyalty_account
    except LoyaltyAccount.DoesNotExist:
        program = LoyaltyProgram.objects.filter(is_active=True).first()
        if program:
            account = LoyaltyAccount.objects.create(
                user=user,
                program=program,
            )
            account.update_tier()
            return account
        return None


@login_required
def dashboard(request):
    """Loyalty dashboard - points balance, tier, recent activity."""
    account = get_or_create_loyalty_account(request.user)

    if not account:
        return render(request, 'loyalty/no_program.html')

    recent_transactions = account.transactions.all()[:5]
    pending_redemptions = account.redemptions.filter(
        status__in=['pending', 'approved']
    )

    # Calculate progress to next tier
    next_tier = None
    progress_percent = 100
    points_to_next = 0

    if account.tier:
        next_tiers = account.program.tiers.filter(
            min_points__gt=account.tier.min_points
        ).order_by('min_points')
        if next_tiers.exists():
            next_tier = next_tiers.first()
            points_to_next = next_tier.min_points - account.lifetime_points
            if points_to_next > 0:
                tier_range = next_tier.min_points - account.tier.min_points
                progress = account.lifetime_points - account.tier.min_points
                progress_percent = min(100, int((progress / tier_range) * 100))

    context = {
        'account': account,
        'recent_transactions': recent_transactions,
        'pending_redemptions': pending_redemptions,
        'next_tier': next_tier,
        'points_to_next': points_to_next,
        'progress_percent': progress_percent,
    }
    return render(request, 'loyalty/dashboard.html', context)


@login_required
def rewards_catalog(request):
    """Available rewards for redemption."""
    account = get_or_create_loyalty_account(request.user)

    if not account:
        return render(request, 'loyalty/no_program.html')

    now = timezone.now()

    # Get available rewards
    rewards = LoyaltyReward.objects.filter(
        program=account.program,
        is_active=True,
    ).filter(
        models.Q(valid_from__isnull=True) | models.Q(valid_from__lte=now)
    ).filter(
        models.Q(valid_until__isnull=True) | models.Q(valid_until__gte=now)
    )

    # Separate featured and regular rewards
    featured_rewards = rewards.filter(is_featured=True)
    regular_rewards = rewards.filter(is_featured=False)

    context = {
        'account': account,
        'featured_rewards': featured_rewards,
        'regular_rewards': regular_rewards,
    }
    return render(request, 'loyalty/rewards.html', context)


@login_required
def redeem_reward(request, pk):
    """Redeem a reward."""
    account = get_or_create_loyalty_account(request.user)

    if not account:
        messages.error(request, 'No loyalty account found.')
        return redirect('loyalty:dashboard')

    reward = get_object_or_404(LoyaltyReward, pk=pk, is_active=True)

    # Check if user has enough points
    if account.points_balance < reward.points_cost:
        messages.error(
            request,
            f'Not enough points. You need {reward.points_cost} points '
            f'but only have {account.points_balance}.'
        )
        return redirect('loyalty:rewards')

    # Check tier requirement
    if reward.min_tier:
        user_tier_order = account.tier.display_order if account.tier else -1
        if user_tier_order < reward.min_tier.display_order:
            messages.error(
                request,
                f'This reward requires {reward.min_tier.name} tier or higher.'
            )
            return redirect('loyalty:rewards')

    # Check quantity
    if reward.quantity_available is not None:
        remaining = reward.quantity_available - reward.quantity_redeemed
        if remaining <= 0:
            messages.error(request, 'This reward is no longer available.')
            return redirect('loyalty:rewards')

    if request.method == 'POST':
        # Create redemption
        redemption = RewardRedemption.objects.create(
            account=account,
            reward=reward,
            points_spent=reward.points_cost,
            status='pending',
        )

        # Deduct points
        account.points_balance -= reward.points_cost
        account.points_redeemed += reward.points_cost
        account.save()

        # Create transaction record
        PointTransaction.objects.create(
            account=account,
            transaction_type='redeem',
            points=-reward.points_cost,
            balance_after=account.points_balance,
            description=f'Redeemed: {reward.name}',
            reference_type='redemption',
            reference_id=redemption.pk,
        )

        # Update reward quantity
        reward.quantity_redeemed += 1
        reward.save()

        messages.success(
            request,
            f'Successfully redeemed {reward.name}! '
            f'Your code is: {redemption.code}'
        )
        return redirect('loyalty:dashboard')

    context = {
        'account': account,
        'reward': reward,
    }
    return render(request, 'loyalty/redeem_confirm.html', context)


@login_required
def transaction_history(request):
    """Points transaction history."""
    account = get_or_create_loyalty_account(request.user)

    if not account:
        return render(request, 'loyalty/no_program.html')

    transactions = account.transactions.all()

    # Calculate totals
    earned = transactions.filter(
        transaction_type__in=['earn', 'bonus', 'referral']
    ).aggregate(total=Sum('points'))['total'] or 0

    redeemed = abs(transactions.filter(
        transaction_type='redeem'
    ).aggregate(total=Sum('points'))['total'] or 0)

    context = {
        'account': account,
        'transactions': transactions,
        'total_earned': earned,
        'total_redeemed': redeemed,
    }
    return render(request, 'loyalty/history.html', context)


@login_required
def tier_benefits(request):
    """All tiers and their benefits."""
    account = get_or_create_loyalty_account(request.user)

    if not account:
        return render(request, 'loyalty/no_program.html')

    tiers = account.program.tiers.all().order_by('display_order', 'min_points')

    context = {
        'account': account,
        'tiers': tiers,
        'current_tier': account.tier,
    }
    return render(request, 'loyalty/tiers.html', context)


@login_required
def referral_program(request):
    """Referral link, stats, pending referrals."""
    account = get_or_create_loyalty_account(request.user)

    if not account:
        return render(request, 'loyalty/no_program.html')

    try:
        referral_config = account.program.referral_program
    except ReferralProgram.DoesNotExist:
        referral_config = None

    # Get or create referral code for user
    user_referral = Referral.objects.filter(
        referrer=request.user
    ).first()

    if not user_referral and referral_config and referral_config.is_active:
        # Create a referral entry with user's own code
        import uuid
        referral_code = str(uuid.uuid4())[:8].upper()
    else:
        referral_code = user_referral.code if user_referral else None

    # Get referral stats
    referrals_made = Referral.objects.filter(referrer=request.user)
    completed_referrals = referrals_made.filter(status='completed')
    pending_referrals = referrals_made.filter(status='pending')

    total_points_earned = completed_referrals.aggregate(
        total=Sum('referrer_points_awarded')
    )['total'] or 0

    context = {
        'account': account,
        'referral_config': referral_config,
        'referral_code': referral_code,
        'referrals_made': referrals_made,
        'completed_count': completed_referrals.count(),
        'pending_count': pending_referrals.count(),
        'total_points_earned': total_points_earned,
    }
    return render(request, 'loyalty/referrals.html', context)
