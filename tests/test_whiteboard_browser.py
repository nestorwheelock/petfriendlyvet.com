"""Browser tests for EMR Whiteboard using Playwright.

Tests the whiteboard kanban board functionality:
- Login as staff
- Navigate to whiteboard
- Select location
- Interact with encounter cards
- Test drag and drop / state transitions
"""
import re
from playwright.sync_api import sync_playwright, expect


BASE_URL = "http://localhost:7777"
STAFF_USERNAME = "seed_vet@example.com"  # Login uses email, not username
STAFF_PASSWORD = "devpass123"


def test_whiteboard_full_workflow():
    """Test the complete whiteboard workflow."""
    errors = []

    with sync_playwright() as p:
        # Launch browser (headless for CI, headed for debugging)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            ignore_https_errors=True,
        )
        page = context.new_page()

        # Capture console errors
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

        # Capture failed requests
        failed_requests = []
        def handle_response(response):
            if response.status >= 400:
                failed_requests.append(f"{response.status} {response.url}")
        page.on("response", handle_response)

        # Capture page errors
        page_errors = []
        page.on("pageerror", lambda err: page_errors.append(str(err)))

        try:
            print("\n=== WHITEBOARD BROWSER TEST ===\n")

            # 1. Login
            print("1. Logging in as staff...")
            page.goto(f"{BASE_URL}/accounts/login/")
            page.wait_for_load_state("networkidle")

            # Fill login form
            page.fill('input[name="username"]', STAFF_USERNAME)
            page.fill('input[name="password"]', STAFF_PASSWORD)
            page.click('button[type="submit"]')
            page.wait_for_load_state("networkidle")

            # Check if login succeeded
            if "login" in page.url.lower():
                errors.append("LOGIN FAILED: Still on login page")
                print(f"   ERROR: Login failed, current URL: {page.url}")
            else:
                print(f"   OK: Logged in, redirected to: {page.url}")

            # 2. Navigate to staff portal
            print("\n2. Navigating to staff portal...")

            # Find the staff portal link - look for any staff-* URL pattern
            page.goto(f"{BASE_URL}/")
            page.wait_for_load_state("networkidle")

            # Look for staff dashboard link in profile dropdown or navigation
            staff_link = page.locator('a[href*="staff-"]').first
            if staff_link.count() > 0:
                staff_url = staff_link.get_attribute("href")
                print(f"   Found staff link: {staff_url}")
                page.goto(staff_url if staff_url.startswith("http") else f"{BASE_URL}{staff_url}")
            else:
                # Try to find staff token from the page
                print("   Looking for staff portal access...")
                # Check if we're already in staff portal
                if "staff-" in page.url:
                    print(f"   Already in staff portal: {page.url}")
                else:
                    errors.append("NAVIGATION: Could not find staff portal link")

            page.wait_for_load_state("networkidle")
            print(f"   Current URL: {page.url}")

            # 3. Navigate to clinical whiteboard
            print("\n3. Navigating to whiteboard...")

            # Extract staff token from URL
            staff_token_match = re.search(r'staff-([a-zA-Z0-9]+)', page.url)
            if staff_token_match:
                staff_token = staff_token_match.group(1)
                whiteboard_url = f"{BASE_URL}/staff-{staff_token}/operations/clinical/"
                print(f"   Navigating to: {whiteboard_url}")
                page.goto(whiteboard_url)
                page.wait_for_load_state("networkidle")
            else:
                errors.append("NAVIGATION: Could not extract staff token")
                print("   ERROR: Could not find staff token in URL")

            print(f"   Current URL: {page.url}")

            # Take screenshot
            page.screenshot(path="/tmp/whiteboard_01_initial.png")
            print("   Screenshot saved: /tmp/whiteboard_01_initial.png")

            # 4. Check if location selector is shown
            print("\n4. Checking for location selector...")

            location_selector = page.locator('select[name="location_id"], form[action*="select-location"]')
            if location_selector.count() > 0:
                print("   Location selector found - selecting location...")

                # Try to select the first location
                select = page.locator('select[name="location_id"]')
                if select.count() > 0:
                    # Get available options
                    options = select.locator('option').all()
                    print(f"   Found {len(options)} location options")
                    for opt in options:
                        print(f"      - {opt.get_attribute('value')}: {opt.text_content()}")

                    # Select the first non-empty option
                    for opt in options:
                        val = opt.get_attribute('value')
                        if val and val != '':
                            select.select_option(val)
                            print(f"   Selected location: {val}")
                            break

                    # Submit the form - specifically the location form button
                    submit_btn = page.locator('button.btn-primary:has-text("Select Location")')
                    if submit_btn.count() > 0:
                        submit_btn.click()
                        page.wait_for_load_state("networkidle")
            else:
                print("   No location selector - whiteboard should be showing")

            page.screenshot(path="/tmp/whiteboard_02_after_location.png")
            print("   Screenshot saved: /tmp/whiteboard_02_after_location.png")

            # 5. Check whiteboard columns
            print("\n5. Checking whiteboard columns...")

            # Look for kanban columns
            columns = page.locator('[data-state], .kanban-column, [class*="column"]')
            print(f"   Found {columns.count()} potential columns")

            # Look for encounter cards
            cards = page.locator('[id^="encounter-"], .encounter-card, [class*="encounter"]')
            print(f"   Found {cards.count()} encounter cards")

            if cards.count() == 0:
                print("   NOTE: No encounters found. May need to create appointments first.")

            # 6. Test state transition buttons
            print("\n6. Testing state transition buttons...")

            # Look for HTMX transition buttons
            transition_buttons = page.locator('button[hx-post*="transition"]')
            print(f"   Found {transition_buttons.count()} transition buttons")

            if transition_buttons.count() > 0:
                # Click the first transition button
                first_btn = transition_buttons.first
                btn_text = first_btn.text_content().strip()
                print(f"   Clicking button: '{btn_text}'")

                # Wait for HTMX to be ready
                page.wait_for_function("typeof htmx !== 'undefined'", timeout=5000)

                first_btn.click()
                page.wait_for_timeout(1000)  # Wait for HTMX response
                page.wait_for_load_state("networkidle")

                page.screenshot(path="/tmp/whiteboard_03_after_transition.png")
                print("   Screenshot saved: /tmp/whiteboard_03_after_transition.png")

            # 7. Test dropdown state selector
            print("\n7. Testing dropdown state selector...")

            state_selectors = page.locator('select[onchange*="transition"]')
            print(f"   Found {state_selectors.count()} state selector dropdowns")

            if state_selectors.count() > 0:
                first_select = state_selectors.first
                # Get current options
                options = first_select.locator('option').all()
                print(f"   Dropdown has {len(options)} options")

                # Try selecting an option
                for opt in options[1:]:  # Skip first "Move to..." option
                    val = opt.get_attribute('value')
                    if val:
                        print(f"   Selecting state: {val}")
                        first_select.select_option(val)
                        page.wait_for_timeout(1000)
                        break

                page.screenshot(path="/tmp/whiteboard_04_after_dropdown.png")
                print("   Screenshot saved: /tmp/whiteboard_04_after_dropdown.png")

            # 8. Check for any visible errors on page
            print("\n8. Checking for visible errors on page...")

            error_elements = page.locator('.error, .alert-danger, .text-red-500, [class*="error"]')
            if error_elements.count() > 0:
                for i in range(min(error_elements.count(), 5)):
                    err_text = error_elements.nth(i).text_content().strip()
                    if err_text:
                        errors.append(f"PAGE ERROR: {err_text[:100]}")
                        print(f"   Found error: {err_text[:100]}")
            else:
                print("   No visible errors found")

            # 9. Report failed requests
            print("\n9. Failed HTTP requests:")
            if failed_requests:
                for req in failed_requests[:15]:
                    print(f"   {req}")
                    errors.append(f"HTTP: {req[:100]}")
            else:
                print("   No failed requests")

            # 10. Report console errors
            print("\n10. Console errors captured:")
            if console_errors:
                for err in console_errors[:10]:
                    print(f"   CONSOLE: {err.text[:200]}")
            else:
                print("   No console errors")

            # 11. Report page errors
            print("\n11. Page errors captured:")
            if page_errors:
                for err in page_errors[:10]:
                    print(f"   PAGE ERROR: {err[:200]}")
                    errors.append(f"PAGE: {err[:100]}")
            else:
                print("   No page errors")

            # Final screenshot
            page.screenshot(path="/tmp/whiteboard_05_final.png")
            print("\n   Final screenshot: /tmp/whiteboard_05_final.png")

        except Exception as e:
            errors.append(f"EXCEPTION: {str(e)}")
            print(f"\n   EXCEPTION: {e}")
            page.screenshot(path="/tmp/whiteboard_error.png")
            print("   Error screenshot: /tmp/whiteboard_error.png")

        finally:
            browser.close()

        # Summary
        print("\n" + "=" * 50)
        print("SUMMARY")
        print("=" * 50)

        if errors:
            print(f"\nFOUND {len(errors)} ERRORS:")
            for i, err in enumerate(errors, 1):
                print(f"  {i}. {err}")
        else:
            print("\nNo errors found!")

        print("\nScreenshots saved to /tmp/whiteboard_*.png")

        return errors


if __name__ == "__main__":
    errors = test_whiteboard_full_workflow()
    exit(1 if errors else 0)
