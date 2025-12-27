# T-075: Loyalty App Customer-Facing URLs

> **REQUIRED READING:** Before implementation, review [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)

**Story Type**: Task
**Priority**: High (Customer Engagement)
**Estimate**: 5 hours
**Status**: Pending
**Discovered By**: QA Browser Tests (2025-12-25)

## Objective

Create customer-facing views and URLs for the Loyalty app so customers can view their points balance, redeem rewards, and participate in the referral program.

## Background

Browser E2E tests revealed that the Loyalty app only has Django admin interfaces. Customers cannot:
- View their points balance or tier status
- Browse and redeem rewards
- See their transaction history
- Learn about tier benefits
- Access their referral link or track referrals

## Required URLs

| URL | View | Description |
|-----|------|-------------|
| `/loyalty/` | `dashboard` | Points balance, current tier, recent activity |
| `/loyalty/rewards/` | `rewards_catalog` | Available rewards to redeem |
| `/loyalty/history/` | `transaction_history` | Points earned/spent history |
| `/loyalty/tiers/` | `tier_benefits` | All tiers and their benefits |
| `/loyalty/referrals/` | `referral_program` | Referral link, stats, pending referrals |

## Deliverables

### Files to Create
- [ ] `apps/loyalty/urls.py` - URL patterns
- [ ] `apps/loyalty/views.py` - View functions/classes
- [ ] `templates/loyalty/dashboard.html` - Main dashboard
- [ ] `templates/loyalty/rewards.html` - Reward catalog
- [ ] `templates/loyalty/history.html` - Transaction history
- [ ] `templates/loyalty/tiers.html` - Tier information
- [ ] `templates/loyalty/referrals.html` - Referral program

### Files to Modify
- [ ] `config/urls.py` - Include loyalty URLs

## Definition of Done

- [ ] All 5 URLs accessible to authenticated users
- [ ] Dashboard shows user's LoyaltyAccount details
- [ ] Rewards catalog shows available LoyaltyRewards
- [ ] Redemption creates RewardRedemption record
- [ ] History shows PointTransaction records
- [ ] Referral page shows unique referral link
- [ ] Tests written with >95% coverage
- [ ] Browser tests updated to validate customer URLs
- [ ] Mobile-responsive templates

## Technical Notes

- Use existing models: `LoyaltyProgram`, `LoyaltyTier`, `LoyaltyAccount`, `PointTransaction`, `LoyaltyReward`, `RewardRedemption`, `Referral`
- Dashboard requires @login_required decorator
- Referral link should be unique per user
- Consider AJAX for reward redemption
- Points balance should update in real-time

## Related

- QA Discovery: `planning/issues/MISSING_CUSTOMER_URLS.md`
- Existing models: `apps/loyalty/models.py`
- Existing admin: `apps/loyalty/admin.py`
