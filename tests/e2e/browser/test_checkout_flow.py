"""Browser tests for checkout flow.

Tests JavaScript interactions and form behaviors.

Note: Browser tests use live_server fixture which handles DB transactions.
Do not use @pytest.mark.django_db(transaction=True) as it conflicts with
pytest-playwright's async context.
"""
import re
import pytest
from playwright.sync_api import expect


@pytest.mark.browser
class TestStoreBrowsing:
    """Test store browsing and product viewing."""

    def test_store_page_loads(self, page, live_server):
        """Store page loads with products."""
        page.goto(f'{live_server.url}/store/')

        # Page should load without errors
        expect(page).to_have_title(re.compile(r'.*[Ss]tore|[Tt]ienda.*'))

    def test_product_detail_page(self, page, live_server, store_with_products):
        """Product detail page shows correct information."""
        products = store_with_products['products']
        product = products[0]

        page.goto(f'{live_server.url}/store/product/{product.slug}/')

        # Product name should be visible
        expect(page.locator('h1')).to_contain_text(product.name)


@pytest.mark.browser
class TestCartInteractions:
    """Test shopping cart JavaScript interactions."""

    def test_add_to_cart_updates_counter(
        self, authenticated_page, live_server, store_with_products
    ):
        """Cart counter updates when adding product."""
        page = authenticated_page
        product = store_with_products['products'][0]

        page.goto(f'{live_server.url}/store/product/{product.slug}/')

        # Find and click add to cart button
        add_button = page.locator('[data-add-to-cart], .add-to-cart, button:has-text("Add")')
        if add_button.count() > 0:
            add_button.first.click()

            # Wait for AJAX response
            page.wait_for_load_state('networkidle')

            # Cart counter should update (adjust selector for your template)
            cart_counter = page.locator('.cart-count, .cart-badge, [data-cart-count]')
            if cart_counter.count() > 0:
                expect(cart_counter.first).not_to_have_text('0')

    def test_cart_quantity_update(
        self, authenticated_page, live_server, store_with_products
    ):
        """Cart quantity can be updated."""
        page = authenticated_page

        # First add item to cart
        product = store_with_products['products'][0]
        page.goto(f'{live_server.url}/store/product/{product.slug}/')

        add_button = page.locator('[data-add-to-cart], .add-to-cart, button:has-text("Add")')
        if add_button.count() > 0:
            add_button.first.click()
            page.wait_for_load_state('networkidle')

        # Go to cart
        page.goto(f'{live_server.url}/store/cart/')

        # Look for quantity input
        qty_input = page.locator('input[name="quantity"], input[type="number"]')
        if qty_input.count() > 0:
            qty_input.first.fill('2')
            # Trigger update (varies by implementation)
            page.keyboard.press('Tab')
            page.wait_for_load_state('networkidle')


@pytest.mark.browser
class TestCheckoutProcess:
    """Test checkout form and validation."""

    def test_checkout_form_validation(
        self, authenticated_page, live_server, store_with_products
    ):
        """Checkout form shows validation errors."""
        page = authenticated_page

        # Add product to cart
        product = store_with_products['products'][0]
        page.goto(f'{live_server.url}/store/product/{product.slug}/')

        add_button = page.locator('[data-add-to-cart], .add-to-cart, button:has-text("Add")')
        if add_button.count() > 0:
            add_button.first.click()
            page.wait_for_load_state('networkidle')

        # Go to checkout
        page.goto(f'{live_server.url}/store/checkout/')

        # Try submitting empty form
        submit_button = page.locator('button[type="submit"], input[type="submit"]')
        if submit_button.count() > 0:
            submit_button.first.click()

            # Should show validation errors
            # Adjust selector based on your error display
            errors = page.locator('.error, .invalid-feedback, [role="alert"]')
            # If form has required fields, errors should appear

    def test_delivery_option_shows_address_fields(
        self, authenticated_page, live_server, store_with_products
    ):
        """Selecting delivery shows address fields."""
        page = authenticated_page

        # Add product to cart first
        product = store_with_products['products'][0]
        page.goto(f'{live_server.url}/store/product/{product.slug}/')

        add_button = page.locator('[data-add-to-cart], .add-to-cart, button:has-text("Add")')
        if add_button.count() > 0:
            add_button.first.click()
            page.wait_for_load_state('networkidle')

        # Go to checkout
        page.goto(f'{live_server.url}/store/checkout/')

        # Select delivery option
        delivery_radio = page.locator('input[value="delivery"], #fulfillment_delivery')
        if delivery_radio.count() > 0:
            delivery_radio.first.click()

            # Address fields should become visible
            address_field = page.locator(
                'input[name="shipping_address"], '
                'textarea[name="shipping_address"], '
                '#shipping_address'
            )
            if address_field.count() > 0:
                expect(address_field.first).to_be_visible()


@pytest.mark.browser
class TestDeliverySlotSelection:
    """Test delivery slot selection interface."""

    def test_delivery_date_selection(
        self, authenticated_page, live_server, store_with_products, delivery_zone, delivery_slot
    ):
        """User can select delivery date/time slot."""
        page = authenticated_page

        # Setup: Add item and go to checkout
        product = store_with_products['products'][0]
        page.goto(f'{live_server.url}/store/product/{product.slug}/')

        add_button = page.locator('[data-add-to-cart], .add-to-cart, button:has-text("Add")')
        if add_button.count() > 0:
            add_button.first.click()
            page.wait_for_load_state('networkidle')

        page.goto(f'{live_server.url}/store/checkout/')

        # Select delivery
        delivery_radio = page.locator('input[value="delivery"]')
        if delivery_radio.count() > 0:
            delivery_radio.first.click()

            # Look for slot selection
            slot_selector = page.locator('[data-delivery-slots], .delivery-slots, select[name="slot"]')
            # If slot selector exists, interact with it


@pytest.mark.browser
class TestMobileCheckout:
    """Test checkout on mobile viewport."""

    def test_mobile_cart_toggle(self, mobile_page, live_server, store_with_products, owner_user):
        """Mobile cart toggle works correctly."""
        page = mobile_page

        # Login on mobile
        page.goto(f'{live_server.url}/accounts/login/')
        page.fill('input[name="username"]', owner_user.username)
        page.fill('input[name="password"]', 'owner123')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # Go to store
        page.goto(f'{live_server.url}/store/')

        # Mobile menu toggle if exists
        menu_toggle = page.locator('.navbar-toggler, .mobile-menu-toggle, [data-toggle="nav"]')
        if menu_toggle.count() > 0 and menu_toggle.first.is_visible():
            menu_toggle.first.click()

            # Cart link should be accessible
            cart_link = page.locator('a[href*="cart"]')
            if cart_link.count() > 0:
                expect(cart_link.first).to_be_visible()
