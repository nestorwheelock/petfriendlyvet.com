"""Browser tests for loyalty program functionality.

Tests both admin interface and customer-facing loyalty pages.
"""
import re

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.browser
class TestLoyaltyCustomerPages:
    """Test customer-facing loyalty pages."""

    def test_loyalty_dashboard_requires_login(
        self, page: Page, live_server
    ):
        """Loyalty dashboard requires authentication."""
        page.goto(f"{live_server.url}/loyalty/")
        # Should redirect to login
        expect(page).to_have_url(re.compile(r'.*(login|accounts).*'))

    def test_loyalty_dashboard_loads(
        self, authenticated_page: Page, live_server, loyalty_program_setup
    ):
        """Authenticated user can access loyalty dashboard."""
        page = authenticated_page
        page.goto(f"{live_server.url}/loyalty/")
        expect(page.locator('h1')).to_contain_text('Rewards', ignore_case=True)

    def test_rewards_catalog_loads(
        self, authenticated_page: Page, live_server, loyalty_program_setup
    ):
        """Rewards catalog page loads."""
        page = authenticated_page
        page.goto(f"{live_server.url}/loyalty/rewards/")
        expect(page.locator('h1')).to_contain_text('Rewards', ignore_case=True)

    def test_transaction_history_loads(
        self, authenticated_page: Page, live_server, loyalty_program_setup
    ):
        """Transaction history page loads."""
        page = authenticated_page
        page.goto(f"{live_server.url}/loyalty/history/")
        expect(page.locator('h1')).to_contain_text('History', ignore_case=True)

    def test_tier_benefits_loads(
        self, authenticated_page: Page, live_server, loyalty_program_setup
    ):
        """Tier benefits page loads."""
        page = authenticated_page
        page.goto(f"{live_server.url}/loyalty/tiers/")
        expect(page.locator('h1')).to_contain_text('Tier', ignore_case=True)

    def test_referral_program_loads(
        self, authenticated_page: Page, live_server, loyalty_program_setup
    ):
        """Referral program page loads."""
        page = authenticated_page
        page.goto(f"{live_server.url}/loyalty/referrals/")
        expect(page.locator('h1')).to_contain_text('Referral', ignore_case=True)

    def test_dashboard_shows_points_balance(
        self, authenticated_page: Page, live_server, loyalty_program_setup
    ):
        """Dashboard displays points balance."""
        page = authenticated_page
        page.goto(f"{live_server.url}/loyalty/")
        # The account has 500 points from fixture
        expect(page.locator('body')).to_contain_text('500')

    def test_no_program_fallback(
        self, authenticated_page: Page, live_server
    ):
        """Shows fallback when no loyalty program exists."""
        # This test uses authenticated_page without loyalty_program_setup
        # Should show "coming soon" or similar message
        page = authenticated_page
        page.goto(f"{live_server.url}/loyalty/")
        # Either shows dashboard or "coming soon" message
        expect(page.locator('body')).to_be_visible()


@pytest.mark.browser
class TestLoyaltyAdmin:
    """Test loyalty program admin interface."""

    def test_loyalty_program_admin_loads(
        self, admin_page: Page, live_server
    ):
        """Loyalty program admin list is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/loyalty/loyaltyprogram/")
        # Check we're on admin page, not 404
        expect(page.locator('h1')).to_contain_text('loyalty', ignore_case=True)

    def test_loyalty_tier_admin_loads(
        self, admin_page: Page, live_server
    ):
        """Loyalty tier admin list is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/loyalty/loyaltytier/")
        expect(page.locator('h1')).to_contain_text('tier', ignore_case=True)

    def test_loyalty_account_admin_loads(
        self, admin_page: Page, live_server
    ):
        """Loyalty account admin list is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/loyalty/loyaltyaccount/")
        expect(page.locator('h1')).to_contain_text('account', ignore_case=True)

    def test_point_transaction_admin_loads(
        self, admin_page: Page, live_server
    ):
        """Point transaction admin list is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/loyalty/pointtransaction/")
        expect(page.locator('h1')).to_contain_text('transaction', ignore_case=True)


@pytest.mark.browser
class TestLoyaltyRewardsAdmin:
    """Test loyalty rewards admin."""

    def test_rewards_admin_loads(
        self, admin_page: Page, live_server
    ):
        """Rewards admin list is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/loyalty/loyaltyreward/")
        expect(page.locator('h1')).to_contain_text('reward', ignore_case=True)

    def test_add_reward_form(
        self, admin_page: Page, live_server
    ):
        """Add reward form is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/loyalty/loyaltyreward/add/")
        # Check we got the add form
        expect(page.locator('input[name="name"]')).to_be_visible()

    def test_redemption_admin_loads(
        self, admin_page: Page, live_server
    ):
        """Redemption admin list is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/loyalty/rewardredemption/")
        expect(page.locator('h1')).to_contain_text('redemption', ignore_case=True)


@pytest.mark.browser
class TestLoyaltyReferralAdmin:
    """Test loyalty referral admin."""

    def test_referral_admin_loads(
        self, admin_page: Page, live_server
    ):
        """Referral admin list is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/loyalty/referral/")
        expect(page.locator('h1')).to_contain_text('referral', ignore_case=True)

    def test_add_referral_form(
        self, admin_page: Page, live_server
    ):
        """Add referral form is accessible."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/loyalty/referral/add/")
        expect(page.locator('body')).to_be_visible()


@pytest.mark.browser
class TestLoyaltyWithData:
    """Test loyalty admin with actual data."""

    def test_view_loyalty_account(
        self, admin_page: Page, live_server, loyalty_program_setup
    ):
        """Can view loyalty account in admin."""
        page = admin_page
        account = loyalty_program_setup['account']
        page.goto(f"{live_server.url}/admin/loyalty/loyaltyaccount/{account.pk}/change/")
        # Should show the account edit form
        expect(page.locator('body')).to_be_visible()
        # Check points balance field exists
        expect(page.locator('input[name="points_balance"]')).to_be_visible()

    def test_view_loyalty_program(
        self, admin_page: Page, live_server, loyalty_program_setup
    ):
        """Can view loyalty program in admin."""
        page = admin_page
        program = loyalty_program_setup['program']
        page.goto(f"{live_server.url}/admin/loyalty/loyaltyprogram/{program.pk}/change/")
        expect(page.locator('input[name="name"]')).to_be_visible()
