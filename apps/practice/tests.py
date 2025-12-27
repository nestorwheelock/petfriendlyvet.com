"""Tests for practice app staff CRUD operations."""
from django.test import TestCase, Client
from django.urls import reverse
from apps.accounts.models import User
from apps.practice.models import StaffProfile


class StaffCRUDTests(TestCase):
    """Test staff create, edit, deactivate operations.

    Note: Test settings disable DynamicURLMiddleware so we use direct URLs
    like /operations/practice/... instead of /staff-{token}/operations/practice/...
    """

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        # Create a staff user who can access practice module
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@test.com',
            password='testpass123',
            is_staff=True,
            role='staff'
        )
        # Create a staff profile for the user
        self.staff_profile = StaffProfile.objects.create(
            user=self.staff_user,
            role='manager',
            phone='555-1234'
        )
        # Log in
        self.client.login(username='staffuser', password='testpass123')
        # Base URL for practice staff (test settings disable dynamic URL middleware)
        self.base_url = '/operations/practice/staff'

    def test_staff_list_page_loads(self):
        """Staff list page is accessible."""
        response = self.client.get(f'{self.base_url}/')
        self.assertEqual(response.status_code, 200)

    def test_staff_create_page_loads(self):
        """Staff create page is accessible to staff."""
        response = self.client.get(f'{self.base_url}/add/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')

    def test_staff_create_valid_form(self):
        """Valid form creates User and StaffProfile."""
        data = {
            'email': 'newstaff@test.com',
            'first_name': 'New',
            'last_name': 'Staff',
            'password1': 'securepass123',
            'password2': 'securepass123',
            'role': 'receptionist',
            'phone': '555-9999',
        }
        response = self.client.post(f'{self.base_url}/add/', data=data)
        # Should redirect on success
        self.assertEqual(response.status_code, 302)
        # Verify user was created
        self.assertTrue(User.objects.filter(email='newstaff@test.com').exists())
        # Verify staff profile was created
        new_user = User.objects.get(email='newstaff@test.com')
        self.assertTrue(hasattr(new_user, 'staff_profile'))
        self.assertEqual(new_user.staff_profile.role, 'receptionist')

    def test_staff_create_duplicate_email(self):
        """Duplicate email shows error."""
        data = {
            'email': 'staff@test.com',  # Already exists
            'first_name': 'Duplicate',
            'last_name': 'User',
            'password1': 'securepass123',
            'password2': 'securepass123',
            'role': 'receptionist',
        }
        response = self.client.post(f'{self.base_url}/add/', data=data)
        # Should stay on form with error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'email')  # Error about email

    def test_staff_create_password_mismatch(self):
        """Mismatched passwords show error."""
        data = {
            'email': 'another@test.com',
            'first_name': 'Another',
            'last_name': 'User',
            'password1': 'securepass123',
            'password2': 'differentpass',
            'role': 'receptionist',
        }
        response = self.client.post(f'{self.base_url}/add/', data=data)
        # Should stay on form with error
        self.assertEqual(response.status_code, 200)
        # User should not be created
        self.assertFalse(User.objects.filter(email='another@test.com').exists())

    def test_staff_edit_page_loads(self):
        """Staff edit page loads with existing data."""
        response = self.client.get(f'{self.base_url}/{self.staff_profile.pk}/edit/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')
        self.assertContains(response, '555-1234')  # Existing phone

    def test_staff_edit_valid_form(self):
        """Valid edit updates StaffProfile."""
        data = {
            'role': 'admin',
            'phone': '555-NEW',
            'title': 'Office Manager',
        }
        response = self.client.post(
            f'{self.base_url}/{self.staff_profile.pk}/edit/',
            data=data
        )
        # Should redirect on success
        self.assertEqual(response.status_code, 302)
        # Verify changes were saved
        self.staff_profile.refresh_from_db()
        self.assertEqual(self.staff_profile.role, 'admin')
        self.assertEqual(self.staff_profile.phone, '555-NEW')
        self.assertEqual(self.staff_profile.title, 'Office Manager')

    def test_staff_deactivate_page_loads(self):
        """Staff deactivate confirmation page loads."""
        # Create another staff to deactivate (can't deactivate self)
        other_user = User.objects.create_user(
            username='otherstaff',
            email='other@test.com',
            password='testpass123',
            is_staff=True
        )
        other_profile = StaffProfile.objects.create(
            user=other_user,
            role='receptionist'
        )
        response = self.client.get(f'{self.base_url}/{other_profile.pk}/deactivate/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Deactivate')  # In title/button

    def test_staff_deactivate_sets_inactive(self):
        """Deactivate sets is_active=False on both User and StaffProfile."""
        # Create another staff to deactivate
        other_user = User.objects.create_user(
            username='todeactivate',
            email='deactivate@test.com',
            password='testpass123',
            is_staff=True
        )
        other_profile = StaffProfile.objects.create(
            user=other_user,
            role='receptionist',
            is_active=True
        )
        response = self.client.post(f'{self.base_url}/{other_profile.pk}/deactivate/')
        # Should redirect on success
        self.assertEqual(response.status_code, 302)
        # Verify deactivated
        other_profile.refresh_from_db()
        other_user.refresh_from_db()
        self.assertFalse(other_profile.is_active)
        self.assertFalse(other_user.is_active)

    def test_staff_deactivate_get_does_not_deactivate(self):
        """GET request to deactivate does not deactivate (requires POST)."""
        other_user = User.objects.create_user(
            username='stillactive',
            email='stillactive@test.com',
            password='testpass123',
            is_staff=True
        )
        other_profile = StaffProfile.objects.create(
            user=other_user,
            role='receptionist',
            is_active=True
        )
        # GET request should show confirmation, not deactivate
        response = self.client.get(f'{self.base_url}/{other_profile.pk}/deactivate/')
        self.assertEqual(response.status_code, 200)
        # Should still be active
        other_profile.refresh_from_db()
        self.assertTrue(other_profile.is_active)


class StaffCreateFormTests(TestCase):
    """Test StaffCreateForm validation."""

    def test_form_requires_email(self):
        """Email is required."""
        from apps.practice.forms import StaffCreateForm
        form = StaffCreateForm(data={
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'securepass123',
            'password2': 'securepass123',
            'role': 'receptionist',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_form_requires_matching_passwords(self):
        """Passwords must match."""
        from apps.practice.forms import StaffCreateForm
        form = StaffCreateForm(data={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'securepass123',
            'password2': 'differentpass',
            'role': 'receptionist',
        })
        self.assertFalse(form.is_valid())

    def test_form_valid_with_all_required_fields(self):
        """Form is valid with all required fields."""
        from apps.practice.forms import StaffCreateForm
        form = StaffCreateForm(data={
            'email': 'valid@example.com',
            'first_name': 'Valid',
            'last_name': 'User',
            'password1': 'securepass123',
            'password2': 'securepass123',
            'role': 'receptionist',
        })
        self.assertTrue(form.is_valid())


class StaffEditFormTests(TestCase):
    """Test StaffEditForm validation."""

    def test_form_valid_with_role(self):
        """Form is valid with just role (minimal required field)."""
        from apps.practice.forms import StaffEditForm
        form = StaffEditForm(data={
            'role': 'veterinarian',
        })
        self.assertTrue(form.is_valid())

    def test_form_accepts_optional_fields(self):
        """Form accepts optional fields."""
        from apps.practice.forms import StaffEditForm
        form = StaffEditForm(data={
            'role': 'veterinarian',
            'title': 'Lead Veterinarian',
            'phone': '555-1234',
            'dea_number': 'AB1234567',
        })
        self.assertTrue(form.is_valid())
