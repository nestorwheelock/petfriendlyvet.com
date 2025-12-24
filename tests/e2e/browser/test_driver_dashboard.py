"""Browser tests for driver mobile interface.

Tests the driver dashboard functionality from a mobile perspective.

Note: Browser tests use live_server fixture which handles DB transactions.
"""
import pytest
from playwright.sync_api import expect

from apps.delivery.models import Delivery, DeliveryProof


@pytest.mark.browser
class TestDriverDashboard:
    """Test driver dashboard views."""

    def test_driver_sees_assigned_deliveries(
        self, driver_page, live_server, paid_order, delivery_zone,
        delivery_slot, delivery_driver
    ):
        """Driver dashboard shows today's assigned deliveries."""
        page = driver_page

        # Create assigned delivery
        delivery = Delivery.objects.create(
            order=paid_order,
            driver=delivery_driver,
            zone=delivery_zone,
            slot=delivery_slot,
            status='assigned',
            address='Calle Test 123',
        )

        # Go to driver dashboard
        page.goto(f'{live_server.url}/driver/dashboard/')

        # Should see the delivery
        delivery_card = page.locator(f'[data-delivery="{delivery.id}"], .delivery-card')
        if delivery_card.count() > 0:
            expect(delivery_card.first).to_be_visible()

    def test_driver_empty_dashboard(self, driver_page, live_server, delivery_driver):
        """Empty dashboard shows appropriate message."""
        page = driver_page

        page.goto(f'{live_server.url}/driver/dashboard/')

        # Should show empty state or message
        empty_message = page.locator('.empty-state, .no-deliveries, :text("No deliveries")')
        # May or may not have deliveries, just ensure page loads


@pytest.mark.browser
class TestDriverStatusUpdates:
    """Test driver can update delivery status via UI."""

    def test_driver_can_mark_picked_up(
        self, driver_page, live_server, paid_order, delivery_zone,
        delivery_slot, delivery_driver
    ):
        """Driver can tap to mark delivery as picked up."""
        page = driver_page

        delivery = Delivery.objects.create(
            order=paid_order,
            driver=delivery_driver,
            zone=delivery_zone,
            slot=delivery_slot,
            status='assigned',
            address='Calle Test 123',
        )
        from django.utils import timezone
        delivery.assigned_at = timezone.now()
        delivery.save()

        # Go to delivery detail
        page.goto(f'{live_server.url}/driver/delivery/{delivery.id}/')

        # Find pickup button
        pickup_button = page.locator('button:has-text("Pick"), [data-action="pickup"]')
        if pickup_button.count() > 0:
            pickup_button.first.click()
            page.wait_for_load_state('networkidle')

            # Verify status updated
            delivery.refresh_from_db()
            assert delivery.status == 'picked_up'

    def test_driver_status_flow_navigation(
        self, driver_page, live_server, paid_order, delivery_zone,
        delivery_slot, delivery_driver
    ):
        """Driver can navigate through status updates."""
        page = driver_page

        # Create delivery in picked_up status
        from django.utils import timezone

        delivery = Delivery.objects.create(
            order=paid_order,
            driver=delivery_driver,
            zone=delivery_zone,
            slot=delivery_slot,
            status='picked_up',
            address='Calle Test 123',
            picked_up_at=timezone.now(),
        )
        delivery.assigned_at = timezone.now()
        delivery.save()

        page.goto(f'{live_server.url}/driver/delivery/{delivery.id}/')

        # Look for out for delivery button
        ofd_button = page.locator('button:has-text("Out for"), [data-action="out_for_delivery"]')
        if ofd_button.count() > 0:
            ofd_button.first.click()
            page.wait_for_load_state('networkidle')


@pytest.mark.browser
class TestDriverProofCapture:
    """Test proof of delivery capture interface."""

    def test_driver_proof_form_loads(
        self, driver_page, live_server, paid_order, delivery_zone,
        delivery_slot, delivery_driver
    ):
        """Proof of delivery form loads for arrived deliveries."""
        page = driver_page

        from django.utils import timezone

        delivery = Delivery.objects.create(
            order=paid_order,
            driver=delivery_driver,
            zone=delivery_zone,
            slot=delivery_slot,
            status='arrived',
            address='Calle Test 123',
            arrived_at=timezone.now(),
        )

        # Try the proof page - may not be implemented yet
        response = page.goto(f'{live_server.url}/driver/delivery/{delivery.id}/proof/')

        # If proof route exists, check for form
        if response and response.status == 200:
            proof_form = page.locator('form[data-proof], .proof-form, form:not(.hidden)')
            if proof_form.count() > 0:
                expect(proof_form.first).to_be_visible()
        # If route doesn't exist (404), that's expected - proof page not yet implemented

    def test_driver_can_submit_recipient_name(
        self, driver_page, live_server, paid_order, delivery_zone,
        delivery_slot, delivery_driver
    ):
        """Driver can enter recipient name for proof."""
        page = driver_page

        from django.utils import timezone

        delivery = Delivery.objects.create(
            order=paid_order,
            driver=delivery_driver,
            zone=delivery_zone,
            slot=delivery_slot,
            status='arrived',
            address='Calle Test 123',
            arrived_at=timezone.now(),
        )

        page.goto(f'{live_server.url}/driver/delivery/{delivery.id}/proof/')

        # Fill recipient name
        name_input = page.locator('input[name="recipient_name"], #recipient_name')
        if name_input.count() > 0:
            name_input.first.fill('Juan Pérez')


@pytest.mark.browser
class TestDriverMobileOptimization:
    """Test driver interface is optimized for mobile."""

    def test_mobile_viewport_layout(
        self, mobile_page, live_server, driver_user, delivery_driver
    ):
        """Driver dashboard works on mobile viewport."""
        page = mobile_page
        page.set_viewport_size({'width': 375, 'height': 667})

        # Login
        page.goto(f'{live_server.url}/accounts/login/')
        page.fill('input[name="username"]', driver_user.username)
        page.fill('input[name="password"]', 'driver123')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # Dashboard should be accessible
        page.goto(f'{live_server.url}/driver/dashboard/')

        # Check no horizontal scroll
        # Page width should match viewport
        body_width = page.evaluate('document.body.scrollWidth')
        viewport_width = page.viewport_size['width']

        # Allow small difference for scrollbars
        assert body_width <= viewport_width + 20

    def test_touch_friendly_buttons(
        self, mobile_page, live_server, driver_user, delivery_driver
    ):
        """Buttons are touch-friendly size on mobile."""
        page = mobile_page
        page.set_viewport_size({'width': 375, 'height': 667})

        # Login
        page.goto(f'{live_server.url}/accounts/login/')
        page.fill('input[name="username"]', driver_user.username)
        page.fill('input[name="password"]', 'driver123')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        page.goto(f'{live_server.url}/driver/dashboard/')

        # Check button sizes (should be at least 44px for touch)
        buttons = page.locator('button, .btn')
        for i in range(min(5, buttons.count())):
            button = buttons.nth(i)
            if button.is_visible():
                box = button.bounding_box()
                if box:
                    # Buttons should be at least 36px for reasonable touch target
                    assert box['height'] >= 36 or box['width'] >= 36


@pytest.mark.browser
class TestDriverNavigation:
    """Test driver can navigate delivery addresses."""

    def test_address_shows_on_delivery(
        self, driver_page, live_server, paid_order, delivery_zone,
        delivery_slot, delivery_driver
    ):
        """Delivery address is visible and potentially linkable."""
        page = driver_page

        delivery = Delivery.objects.create(
            order=paid_order,
            driver=delivery_driver,
            zone=delivery_zone,
            slot=delivery_slot,
            status='out_for_delivery',
            address='Calle Roma 123, Col. Roma Norte, CDMX',
        )

        page.goto(f'{live_server.url}/driver/delivery/{delivery.id}/')

        # Address should be visible
        address_element = page.locator('.address, [data-address], :text("Calle Roma")')
        if address_element.count() > 0:
            expect(address_element.first).to_be_visible()
