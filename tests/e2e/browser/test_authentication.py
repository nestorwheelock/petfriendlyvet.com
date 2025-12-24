"""Browser tests for user authentication and self-service.

Tests registration, login, password reset, profile management.
"""
import re
import pytest
from playwright.sync_api import expect

from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.browser
class TestUserRegistration:
    """Test user registration flow."""

    def test_registration_page_loads(self, page, live_server):
        """Registration page loads with form."""
        page.goto(f'{live_server.url}/accounts/register/')

        expect(page).to_have_title(re.compile(r'.*(Crear|Cuenta|Register).*', re.IGNORECASE))
        expect(page.locator('form#registration-form')).to_be_visible()

    def test_registration_form_has_required_fields(self, page, live_server):
        """Registration form has all required fields."""
        page.goto(f'{live_server.url}/accounts/register/')

        expect(page.locator('input[name="email"]')).to_be_visible()
        expect(page.locator('input[name="password1"]')).to_be_visible()
        expect(page.locator('input[name="password2"]')).to_be_visible()

    def test_successful_registration(self, page, live_server, db):
        """User can register and is logged in automatically."""
        page.goto(f'{live_server.url}/accounts/register/')

        # Fill registration form
        page.fill('input[name="email"]', 'newuser@example.com')
        page.fill('input[name="first_name"]', 'Test')
        page.fill('input[name="last_name"]', 'User')
        page.fill('input[name="password1"]', 'SecurePass123!')
        page.fill('input[name="password2"]', 'SecurePass123!')

        # Submit form
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # Should be redirected to profile (logged in)
        expect(page).to_have_url(re.compile(r'.*/accounts/profile.*'))

        # User should exist in database
        assert User.objects.filter(email='newuser@example.com').exists()

    def test_registration_password_mismatch(self, page, live_server, db):
        """Registration shows error when passwords don't match."""
        page.goto(f'{live_server.url}/accounts/register/')

        page.fill('input[name="email"]', 'newuser@example.com')
        page.fill('input[name="password1"]', 'SecurePass123!')
        page.fill('input[name="password2"]', 'DifferentPass456!')

        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # Should show error
        error = page.locator('[role="alert"], .text-red-600, .text-red-700')
        expect(error.first).to_be_visible()

    def test_registration_duplicate_email(self, page, live_server, owner_user):
        """Registration shows error for duplicate email."""
        page.goto(f'{live_server.url}/accounts/register/')

        page.fill('input[name="email"]', owner_user.email)
        page.fill('input[name="password1"]', 'SecurePass123!')
        page.fill('input[name="password2"]', 'SecurePass123!')

        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # Should show email already registered error
        error = page.locator('.text-red-600, [role="alert"]')
        expect(error.first).to_be_visible()

    def test_registration_link_from_login(self, page, live_server):
        """Login page has link to registration."""
        page.goto(f'{live_server.url}/accounts/login/')

        register_link = page.locator('a[href*="register"]')
        expect(register_link).to_be_visible()

        register_link.click()
        page.wait_for_load_state('networkidle')

        expect(page).to_have_url(re.compile(r'.*/accounts/register.*'))


@pytest.mark.browser
class TestUserLogin:
    """Test user login flow."""

    def test_login_page_loads(self, page, live_server):
        """Login page loads with form."""
        page.goto(f'{live_server.url}/accounts/login/')

        expect(page).to_have_title(re.compile(r'.*(Ingresar|Login).*', re.IGNORECASE))
        # Look for the visible form with login inputs
        expect(page.locator('input[name="username"]')).to_be_visible()

    def test_successful_login(self, page, live_server, owner_user):
        """User can login with valid credentials."""
        page.goto(f'{live_server.url}/accounts/login/')

        page.fill('input[name="username"]', owner_user.username)
        page.fill('input[name="password"]', 'owner123')

        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # Should be redirected (not on login page anymore)
        expect(page).not_to_have_url(re.compile(r'.*/accounts/login.*'))

    def test_failed_login_invalid_password(self, page, live_server, owner_user):
        """Login fails with wrong password."""
        page.goto(f'{live_server.url}/accounts/login/')

        page.fill('input[name="username"]', owner_user.username)
        page.fill('input[name="password"]', 'wrongpassword')

        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # Should show error
        error = page.locator('[role="alert"], .bg-red-50, .text-red-700')
        expect(error.first).to_be_visible()

    def test_failed_login_nonexistent_user(self, page, live_server, db):
        """Login fails for nonexistent user."""
        page.goto(f'{live_server.url}/accounts/login/')

        page.fill('input[name="username"]', 'nonexistent@example.com')
        page.fill('input[name="password"]', 'anypassword')

        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # Should stay on login page with error
        expect(page).to_have_url(re.compile(r'.*/accounts/login.*'))

    def test_password_reset_link_visible(self, page, live_server):
        """Login page has password reset link."""
        page.goto(f'{live_server.url}/accounts/login/')

        reset_link = page.locator('a[href*="password-reset"]')
        expect(reset_link).to_be_visible()


@pytest.mark.browser
class TestUserLogout:
    """Test user logout flow."""

    def test_logout_clears_session(self, authenticated_page, live_server):
        """Logout clears user session."""
        page = authenticated_page

        # Navigate to profile to confirm logged in
        page.goto(f'{live_server.url}/accounts/profile/')
        expect(page).to_have_url(re.compile(r'.*/accounts/profile.*'))

        # Logout via POST (Django's LogoutView requires POST by default)
        # Use a form submission or click the logout button/link if available
        page.evaluate('''() => {
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/accounts/logout/';
            const csrf = document.querySelector('[name=csrfmiddlewaretoken]');
            if (csrf) {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'csrfmiddlewaretoken';
                input.value = csrf.value;
                form.appendChild(input);
            }
            document.body.appendChild(form);
            form.submit();
        }''')
        page.wait_for_load_state('networkidle')

        # Try to access profile again - should redirect to login
        page.goto(f'{live_server.url}/accounts/profile/')
        page.wait_for_load_state('networkidle')

        expect(page).to_have_url(re.compile(r'.*/accounts/login.*'))


@pytest.mark.browser
class TestPasswordReset:
    """Test password reset flow."""

    def test_password_reset_page_loads(self, page, live_server):
        """Password reset page loads."""
        page.goto(f'{live_server.url}/accounts/password-reset/')

        expect(page.locator('form#password-reset-form')).to_be_visible()
        expect(page.locator('input[name="email"]')).to_be_visible()

    def test_password_reset_request_submission(self, page, live_server, owner_user):
        """Password reset request can be submitted."""
        page.goto(f'{live_server.url}/accounts/password-reset/')

        page.fill('input[name="email"]', owner_user.email)
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # Should redirect to sent confirmation page
        expect(page).to_have_url(re.compile(r'.*/password-reset/sent.*'))

    def test_password_reset_nonexistent_email(self, page, live_server, db):
        """Password reset for nonexistent email still shows success (security)."""
        page.goto(f'{live_server.url}/accounts/password-reset/')

        page.fill('input[name="email"]', 'nonexistent@example.com')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # Should still redirect to sent page (don't reveal if email exists)
        expect(page).to_have_url(re.compile(r'.*/password-reset/sent.*'))

    def test_password_reset_invalid_token(self, page, live_server, db):
        """Invalid reset token shows error page."""
        page.goto(f'{live_server.url}/accounts/password-reset/invaliduid/invalidtoken/')
        page.wait_for_load_state('networkidle')

        # Should redirect to invalid link page
        expect(page).to_have_url(re.compile(r'.*/password-reset/invalid.*'))


@pytest.mark.browser
class TestProfileView:
    """Test profile viewing."""

    def test_profile_requires_login(self, page, live_server, db):
        """Profile page requires authentication."""
        page.goto(f'{live_server.url}/accounts/profile/')
        page.wait_for_load_state('networkidle')

        # Should redirect to login
        expect(page).to_have_url(re.compile(r'.*/accounts/login.*'))

    def test_profile_shows_user_info(self, authenticated_page, live_server, owner_user):
        """Profile page shows user information."""
        page = authenticated_page

        page.goto(f'{live_server.url}/accounts/profile/')

        # Should show user's name or email
        content = page.content()
        assert owner_user.email in content or owner_user.first_name in content

    def test_profile_has_edit_link(self, authenticated_page, live_server):
        """Profile page has edit profile link."""
        page = authenticated_page

        page.goto(f'{live_server.url}/accounts/profile/')

        edit_link = page.locator('a[href*="profile/edit"]')
        expect(edit_link).to_be_visible()

    def test_profile_has_change_password_link(self, authenticated_page, live_server):
        """Profile page has change password link."""
        page = authenticated_page

        page.goto(f'{live_server.url}/accounts/profile/')

        password_link = page.locator('a[href*="change-password"]')
        expect(password_link).to_be_visible()


@pytest.mark.browser
class TestProfileEdit:
    """Test profile editing."""

    def test_profile_edit_page_loads(self, authenticated_page, live_server):
        """Profile edit page loads with form."""
        page = authenticated_page

        page.goto(f'{live_server.url}/accounts/profile/edit/')

        expect(page.locator('form#profile-edit-form')).to_be_visible()

    def test_profile_edit_prefills_data(self, authenticated_page, live_server, owner_user):
        """Profile edit form prefills with current data."""
        page = authenticated_page

        page.goto(f'{live_server.url}/accounts/profile/edit/')

        first_name_input = page.locator('input[name="first_name"]')
        if owner_user.first_name:
            expect(first_name_input).to_have_value(owner_user.first_name)

    def test_profile_edit_saves_changes(self, authenticated_page, live_server, owner_user):
        """Profile edit saves changes successfully."""
        page = authenticated_page

        page.goto(f'{live_server.url}/accounts/profile/edit/')

        # Update first name
        page.fill('input[name="first_name"]', 'UpdatedName')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # Should redirect to profile
        expect(page).to_have_url(re.compile(r'.*/accounts/profile.*'))

        # Verify change was saved
        owner_user.refresh_from_db()
        assert owner_user.first_name == 'UpdatedName'


@pytest.mark.browser
class TestChangePassword:
    """Test password change flow."""

    def test_change_password_page_loads(self, authenticated_page, live_server):
        """Change password page loads with form."""
        page = authenticated_page

        page.goto(f'{live_server.url}/accounts/profile/change-password/')

        expect(page.locator('form#change-password-form')).to_be_visible()
        expect(page.locator('input[name="old_password"]')).to_be_visible()
        expect(page.locator('input[name="new_password1"]')).to_be_visible()
        expect(page.locator('input[name="new_password2"]')).to_be_visible()

    def test_change_password_success(self, authenticated_page, live_server, owner_user):
        """User can change password successfully."""
        page = authenticated_page

        page.goto(f'{live_server.url}/accounts/profile/change-password/')

        page.fill('input[name="old_password"]', 'owner123')
        page.fill('input[name="new_password1"]', 'NewSecurePass456!')
        page.fill('input[name="new_password2"]', 'NewSecurePass456!')

        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # Should redirect to profile
        expect(page).to_have_url(re.compile(r'.*/accounts/profile.*'))

        # Verify password was changed
        owner_user.refresh_from_db()
        assert owner_user.check_password('NewSecurePass456!')

    def test_change_password_wrong_old_password(self, authenticated_page, live_server):
        """Change password fails with wrong old password."""
        page = authenticated_page

        page.goto(f'{live_server.url}/accounts/profile/change-password/')

        page.fill('input[name="old_password"]', 'wrongoldpassword')
        page.fill('input[name="new_password1"]', 'NewSecurePass456!')
        page.fill('input[name="new_password2"]', 'NewSecurePass456!')

        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # Should show error
        error = page.locator('[role="alert"], .text-red-600')
        expect(error.first).to_be_visible()


@pytest.mark.browser
class TestDeleteAccount:
    """Test account deletion (deactivation)."""

    def test_delete_account_page_loads(self, authenticated_page, live_server):
        """Delete account confirmation page loads."""
        page = authenticated_page

        page.goto(f'{live_server.url}/accounts/profile/delete/')

        expect(page.locator('form#delete-account-form')).to_be_visible()

    def test_delete_account_deactivates_user(self, page, live_server, db):
        """Deleting account deactivates user (soft delete)."""
        # Create a user specifically for this test
        user = User.objects.create_user(
            username='deletetest@example.com',
            email='deletetest@example.com',
            password='testpass123'
        )

        # Login
        page.goto(f'{live_server.url}/accounts/login/')
        page.fill('input[name="username"]', user.username)
        page.fill('input[name="password"]', 'testpass123')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # Go to delete page
        page.goto(f'{live_server.url}/accounts/profile/delete/')

        # Confirm deletion
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # Should redirect to login
        expect(page).to_have_url(re.compile(r'.*/accounts/login.*'))

        # User should be deactivated but not deleted
        user.refresh_from_db()
        assert user.is_active is False
        assert User.objects.filter(pk=user.pk).exists()

    def test_delete_account_cancel(self, authenticated_page, live_server):
        """Cancel button returns to profile."""
        page = authenticated_page

        page.goto(f'{live_server.url}/accounts/profile/delete/')

        # Click cancel - look for any link that's not the submit button
        cancel_link = page.locator('a:has-text("Cancelar"), a:has-text("Volver"), a.btn-secondary').first
        cancel_link.click()
        page.wait_for_load_state('networkidle')

        # Should be on profile page
        expect(page).to_have_url(re.compile(r'.*/accounts/profile.*'))


@pytest.mark.browser
class TestMobileAuthentication:
    """Test authentication on mobile viewport."""

    def test_mobile_login_form(self, mobile_page, live_server):
        """Login form works on mobile viewport."""
        page = mobile_page
        page.set_viewport_size({'width': 375, 'height': 667})

        page.goto(f'{live_server.url}/accounts/login/')

        # Form should be visible and usable
        expect(page.locator('input[name="username"]')).to_be_visible()
        expect(page.locator('input[name="password"]')).to_be_visible()
        expect(page.locator('button[type="submit"]').first).to_be_visible()

    def test_mobile_registration_form(self, mobile_page, live_server):
        """Registration form works on mobile viewport."""
        page = mobile_page
        page.set_viewport_size({'width': 375, 'height': 667})

        page.goto(f'{live_server.url}/accounts/register/')

        # Form should be visible
        expect(page.locator('input[name="email"]')).to_be_visible()
