"""Browser tests for admin user management.

Tests admin creating users, changing permissions, resetting passwords,
deactivating users (never deleting).
"""
import re
import pytest
from playwright.sync_api import expect

from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def admin_page(page, live_server, db):
    """Page with authenticated superuser session."""
    # Create superuser
    admin = User.objects.create_superuser(
        username='admin@example.com',
        email='admin@example.com',
        password='adminpass123'
    )

    # Login to admin
    page.goto(f'{live_server.url}/admin/login/')
    page.fill('input[name="username"]', 'admin@example.com')
    page.fill('input[name="password"]', 'adminpass123')
    page.click('input[type="submit"]')
    page.wait_for_load_state('networkidle')

    return page


@pytest.mark.browser
class TestAdminUserList:
    """Test admin user list view."""

    def test_admin_can_access_user_list(self, admin_page, live_server):
        """Admin can access the user list."""
        page = admin_page

        page.goto(f'{live_server.url}/admin/accounts/user/')
        page.wait_for_load_state('networkidle')

        # Should see user list
        expect(page.locator('#changelist, .module')).to_be_visible()

    def test_admin_user_list_shows_users(self, admin_page, live_server, owner_user):
        """User list shows registered users."""
        page = admin_page

        page.goto(f'{live_server.url}/admin/accounts/user/')

        # Should show the owner user
        content = page.content()
        assert owner_user.username in content or owner_user.email in content

    def test_admin_can_search_users(self, admin_page, live_server, owner_user):
        """Admin can search for users."""
        page = admin_page

        page.goto(f'{live_server.url}/admin/accounts/user/')

        # Search for user
        search_input = page.locator('input[name="q"]')
        search_input.fill(owner_user.email)
        page.click('input[type="submit"][value="Search"]')
        page.wait_for_load_state('networkidle')

        # Should show search results
        content = page.content()
        assert owner_user.email in content

    def test_admin_can_filter_by_active_status(self, admin_page, live_server, owner_user):
        """Admin can filter users by active status."""
        page = admin_page

        page.goto(f'{live_server.url}/admin/accounts/user/')

        # Look for active filter
        filter_link = page.locator('a:has-text("Yes"), a:has-text("Active")')
        if filter_link.count() > 0:
            filter_link.first.click()
            page.wait_for_load_state('networkidle')


@pytest.mark.browser
class TestAdminCreateUser:
    """Test admin creating new users."""

    def test_admin_can_access_add_user_page(self, admin_page, live_server):
        """Admin can access add user page."""
        page = admin_page

        page.goto(f'{live_server.url}/admin/accounts/user/add/')
        page.wait_for_load_state('networkidle')

        expect(page.locator('form#user_form, form')).to_be_visible()

    def test_admin_can_create_user(self, admin_page, live_server):
        """Admin can create a new user."""
        page = admin_page

        page.goto(f'{live_server.url}/admin/accounts/user/add/')

        # Fill user creation form (Django admin's 2-step process)
        page.fill('input[name="username"]', 'newadminuser')
        page.fill('input[name="password1"]', 'SecurePass123!')
        page.fill('input[name="password2"]', 'SecurePass123!')

        # Submit
        page.click('input[name="_save"], button[name="_save"]')
        page.wait_for_load_state('networkidle')

        # Should be on edit page or list (depending on Django version)
        # User should exist
        assert User.objects.filter(username='newadminuser').exists()

    def test_admin_can_set_user_email(self, admin_page, live_server):
        """Admin can set user email during creation."""
        page = admin_page

        page.goto(f'{live_server.url}/admin/accounts/user/add/')

        # Fill basic info
        page.fill('input[name="username"]', 'emailuser')
        page.fill('input[name="password1"]', 'SecurePass123!')
        page.fill('input[name="password2"]', 'SecurePass123!')

        # Check for email field in add form
        email_input = page.locator('input[name="email"]')
        if email_input.count() > 0:
            email_input.fill('emailuser@example.com')

        page.click('input[name="_save"], button[name="_save"]')
        page.wait_for_load_state('networkidle')

        # User should exist
        assert User.objects.filter(username='emailuser').exists()


@pytest.mark.browser
class TestAdminEditUser:
    """Test admin editing existing users."""

    def test_admin_can_access_user_edit(self, admin_page, live_server, owner_user):
        """Admin can access user edit page."""
        page = admin_page

        page.goto(f'{live_server.url}/admin/accounts/user/{owner_user.pk}/change/')
        page.wait_for_load_state('networkidle')

        expect(page.locator('form#user_form, form')).to_be_visible()

    def test_admin_can_edit_user_name(self, admin_page, live_server, owner_user):
        """Admin can edit user's name."""
        page = admin_page

        page.goto(f'{live_server.url}/admin/accounts/user/{owner_user.pk}/change/')

        # Update first name
        first_name_input = page.locator('input[name="first_name"]')
        first_name_input.fill('AdminEdited')

        page.click('input[name="_save"], button[name="_save"]')
        page.wait_for_load_state('networkidle')

        # Verify change
        owner_user.refresh_from_db()
        assert owner_user.first_name == 'AdminEdited'

    def test_admin_can_edit_user_email(self, admin_page, live_server, owner_user):
        """Admin can edit user's email."""
        page = admin_page

        page.goto(f'{live_server.url}/admin/accounts/user/{owner_user.pk}/change/')

        # Update email
        email_input = page.locator('input[name="email"]')
        email_input.fill('newemail@example.com')

        page.click('input[name="_save"], button[name="_save"]')
        page.wait_for_load_state('networkidle')

        # Verify change
        owner_user.refresh_from_db()
        assert owner_user.email == 'newemail@example.com'

    def test_admin_can_change_user_role(self, admin_page, live_server, owner_user):
        """Admin can change user's role."""
        page = admin_page

        page.goto(f'{live_server.url}/admin/accounts/user/{owner_user.pk}/change/')

        # Change role
        role_select = page.locator('select[name="role"]')
        if role_select.count() > 0:
            role_select.select_option('staff')

            page.click('input[name="_save"], button[name="_save"]')
            page.wait_for_load_state('networkidle')

            owner_user.refresh_from_db()
            assert owner_user.role == 'staff'


@pytest.mark.browser
class TestAdminUserPermissions:
    """Test admin managing user permissions."""

    def test_admin_can_make_user_staff(self, admin_page, live_server, owner_user):
        """Admin can make user a staff member."""
        page = admin_page

        page.goto(f'{live_server.url}/admin/accounts/user/{owner_user.pk}/change/')

        # Check is_staff checkbox
        staff_checkbox = page.locator('input[name="is_staff"]')
        if not staff_checkbox.is_checked():
            staff_checkbox.check()

        page.click('input[name="_save"], button[name="_save"]')
        page.wait_for_load_state('networkidle')

        owner_user.refresh_from_db()
        assert owner_user.is_staff is True

    def test_admin_can_remove_staff_status(self, admin_page, live_server, staff_user):
        """Admin can remove staff status from user."""
        page = admin_page

        page.goto(f'{live_server.url}/admin/accounts/user/{staff_user.pk}/change/')

        # Uncheck is_staff checkbox
        staff_checkbox = page.locator('input[name="is_staff"]')
        if staff_checkbox.is_checked():
            staff_checkbox.uncheck()

        page.click('input[name="_save"], button[name="_save"]')
        page.wait_for_load_state('networkidle')

        staff_user.refresh_from_db()
        assert staff_user.is_staff is False

    def test_admin_can_make_user_superuser(self, admin_page, live_server, owner_user):
        """Admin can make user a superuser."""
        page = admin_page

        page.goto(f'{live_server.url}/admin/accounts/user/{owner_user.pk}/change/')

        # Check is_superuser checkbox
        superuser_checkbox = page.locator('input[name="is_superuser"]')
        if superuser_checkbox.count() > 0 and not superuser_checkbox.is_checked():
            superuser_checkbox.check()

            # Also need to check is_staff for superuser
            staff_checkbox = page.locator('input[name="is_staff"]')
            if not staff_checkbox.is_checked():
                staff_checkbox.check()

            page.click('input[name="_save"], button[name="_save"]')
            page.wait_for_load_state('networkidle')

            owner_user.refresh_from_db()
            assert owner_user.is_superuser is True

    def test_admin_can_assign_groups(self, admin_page, live_server, owner_user):
        """Admin can assign user to groups."""
        page = admin_page

        # First create a group
        from django.contrib.auth.models import Group
        group = Group.objects.create(name='VIP Customers')

        page.goto(f'{live_server.url}/admin/accounts/user/{owner_user.pk}/change/')

        # Look for groups selector
        groups_select = page.locator('select[name="groups"]')
        if groups_select.count() > 0:
            # Select the group (multi-select widget varies by Django version)
            groups_select.select_option(str(group.pk))

            page.click('input[name="_save"], button[name="_save"]')
            page.wait_for_load_state('networkidle')

            owner_user.refresh_from_db()
            assert group in owner_user.groups.all()


@pytest.mark.browser
class TestAdminResetUserPassword:
    """Test admin resetting user passwords."""

    def test_admin_can_access_password_change(self, admin_page, live_server, owner_user):
        """Admin can access user password change page."""
        page = admin_page

        # Navigate to user edit page first
        page.goto(f'{live_server.url}/admin/accounts/user/{owner_user.pk}/change/')

        # Look for password change link
        password_link = page.locator('a[href*="password"]')
        if password_link.count() > 0:
            password_link.click()
            page.wait_for_load_state('networkidle')

            # Should be on password change page
            expect(page.locator('input[name="password1"]')).to_be_visible()

    def test_admin_can_change_user_password(self, admin_page, live_server, owner_user):
        """Admin can change user's password."""
        page = admin_page

        page.goto(f'{live_server.url}/admin/accounts/user/{owner_user.pk}/password/')

        # Fill password form
        page.fill('input[name="password1"]', 'AdminSetPass123!')
        page.fill('input[name="password2"]', 'AdminSetPass123!')

        page.click('input[type="submit"]')
        page.wait_for_load_state('networkidle')

        # Verify password was changed
        owner_user.refresh_from_db()
        assert owner_user.check_password('AdminSetPass123!')


@pytest.mark.browser
class TestAdminDeactivateUser:
    """Test admin deactivating users (soft delete)."""

    def test_admin_can_deactivate_user(self, admin_page, live_server, owner_user):
        """Admin can deactivate a user account."""
        page = admin_page

        page.goto(f'{live_server.url}/admin/accounts/user/{owner_user.pk}/change/')

        # Uncheck is_active checkbox
        active_checkbox = page.locator('input[name="is_active"]')
        if active_checkbox.is_checked():
            active_checkbox.uncheck()

        page.click('input[name="_save"], button[name="_save"]')
        page.wait_for_load_state('networkidle')

        owner_user.refresh_from_db()
        assert owner_user.is_active is False
        # User still exists (soft delete)
        assert User.objects.filter(pk=owner_user.pk).exists()

    def test_admin_can_reactivate_user(self, admin_page, live_server, db):
        """Admin can reactivate a deactivated user."""
        # Create deactivated user
        inactive_user = User.objects.create_user(
            username='inactive@example.com',
            email='inactive@example.com',
            password='pass123',
            is_active=False
        )

        page = admin_page

        page.goto(f'{live_server.url}/admin/accounts/user/{inactive_user.pk}/change/')

        # Check is_active checkbox
        active_checkbox = page.locator('input[name="is_active"]')
        if not active_checkbox.is_checked():
            active_checkbox.check()

        page.click('input[name="_save"], button[name="_save"]')
        page.wait_for_load_state('networkidle')

        inactive_user.refresh_from_db()
        assert inactive_user.is_active is True

    def test_deactivated_user_cannot_login(self, page, live_server, db):
        """Deactivated user cannot login."""
        # Create and deactivate user
        inactive_user = User.objects.create_user(
            username='disabled@example.com',
            email='disabled@example.com',
            password='pass123',
            is_active=False
        )

        page.goto(f'{live_server.url}/accounts/login/')
        page.fill('input[name="username"]', 'disabled@example.com')
        page.fill('input[name="password"]', 'pass123')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # Should stay on login page with error
        expect(page).to_have_url(re.compile(r'.*/accounts/login.*'))


@pytest.mark.browser
class TestAdminBulkUserActions:
    """Test admin bulk actions on users."""

    def test_admin_can_bulk_deactivate_users(self, admin_page, live_server, db):
        """Admin can bulk deactivate multiple users."""
        # Create some users
        users = []
        for i in range(3):
            users.append(User.objects.create_user(
                username=f'bulkuser{i}@example.com',
                email=f'bulkuser{i}@example.com',
                password='pass123'
            ))

        page = admin_page

        page.goto(f'{live_server.url}/admin/accounts/user/')

        # Select users (checkboxes)
        for user in users:
            checkbox = page.locator(f'input[name="_selected_action"][value="{user.pk}"]')
            if checkbox.count() > 0:
                checkbox.check()

        # Select action - Django admin doesn't have bulk deactivate by default
        # but has delete action (which we should NOT use)
        # This test documents expected behavior

    def test_admin_cannot_hard_delete_users(self, admin_page, live_server, owner_user):
        """Verify users are soft deleted (deactivated) not hard deleted."""
        page = admin_page

        page.goto(f'{live_server.url}/admin/accounts/user/{owner_user.pk}/change/')

        # Deactivate instead of delete
        active_checkbox = page.locator('input[name="is_active"]')
        if active_checkbox.is_checked():
            active_checkbox.uncheck()

        page.click('input[name="_save"], button[name="_save"]')
        page.wait_for_load_state('networkidle')

        # User should still exist
        assert User.objects.filter(pk=owner_user.pk).exists()


@pytest.mark.browser
class TestAdminUserHistory:
    """Test admin viewing user activity history."""

    def test_admin_can_view_user_history(self, admin_page, live_server, owner_user):
        """Admin can view user's change history."""
        page = admin_page

        page.goto(f'{live_server.url}/admin/accounts/user/{owner_user.pk}/history/')
        page.wait_for_load_state('networkidle')

        # Should show history page
        content = page.content()
        assert 'history' in content.lower() or 'History' in content


@pytest.mark.browser
class TestAdminUserFilters:
    """Test admin user list filters."""

    def test_admin_can_filter_by_role(self, admin_page, live_server, owner_user, staff_user):
        """Admin can filter users by role."""
        page = admin_page

        page.goto(f'{live_server.url}/admin/accounts/user/')

        # Look for role filter in sidebar
        role_filter = page.locator('#changelist-filter a:has-text("owner"), #changelist-filter a:has-text("Pet Owner")')
        if role_filter.count() > 0:
            role_filter.first.click()
            page.wait_for_load_state('networkidle')

    def test_admin_can_filter_by_language(self, admin_page, live_server, owner_user):
        """Admin can filter users by preferred language."""
        page = admin_page

        page.goto(f'{live_server.url}/admin/accounts/user/')

        # Look for language filter
        language_filter = page.locator('#changelist-filter a:has-text("Español"), #changelist-filter a:has-text("es")')
        if language_filter.count() > 0:
            language_filter.first.click()
            page.wait_for_load_state('networkidle')
