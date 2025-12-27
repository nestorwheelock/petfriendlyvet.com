"""Tests for practice app CRUD operations."""
from datetime import date, time, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from apps.accounts.models import User
from apps.practice.models import StaffProfile, Shift, Task, TimeEntry


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

    def test_form_allows_existing_user_without_profile(self):
        """Form should allow creating StaffProfile for existing user without one."""
        from apps.practice.forms import StaffCreateForm
        # Create existing user WITHOUT StaffProfile
        existing_user = User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='oldpassword',
            first_name='Existing',
            last_name='User',
        )
        # Try to create staff with same email - should succeed
        form = StaffCreateForm(data={
            'email': 'existing@example.com',
            'first_name': 'Existing',
            'last_name': 'User',
            'password1': '',  # No password needed for existing user
            'password2': '',
            'role': 'receptionist',
        })
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

    def test_form_rejects_user_with_existing_profile(self):
        """Form should reject if user already has StaffProfile."""
        from apps.practice.forms import StaffCreateForm
        from apps.practice.models import StaffProfile
        # Create user WITH StaffProfile
        user_with_profile = User.objects.create_user(
            username='hasprofile',
            email='hasprofile@example.com',
            password='testpass',
            first_name='Has',
            last_name='Profile',
        )
        StaffProfile.objects.create(user=user_with_profile, role='receptionist')
        # Try to create staff with same email - should fail
        form = StaffCreateForm(data={
            'email': 'hasprofile@example.com',
            'first_name': 'Has',
            'last_name': 'Profile',
            'password1': '',
            'password2': '',
            'role': 'vet_tech',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_form_save_creates_profile_for_existing_user(self):
        """save() should create StaffProfile for existing user."""
        from apps.practice.forms import StaffCreateForm
        from apps.practice.models import StaffProfile
        # Create existing user WITHOUT StaffProfile
        existing_user = User.objects.create_user(
            username='existinguser2',
            email='existing2@example.com',
            password='oldpassword',
            first_name='Existing',
            last_name='User',
        )
        self.assertFalse(hasattr(existing_user, 'staff_profile'))
        # Create staff profile for them
        form = StaffCreateForm(data={
            'email': 'existing2@example.com',
            'first_name': 'Existing',
            'last_name': 'User',
            'password1': '',
            'password2': '',
            'role': 'receptionist',
        })
        self.assertTrue(form.is_valid())
        profile = form.save()
        # Verify profile was created and linked to existing user
        self.assertEqual(profile.user.pk, existing_user.pk)
        self.assertEqual(profile.role, 'receptionist')
        # Verify user is now staff
        existing_user.refresh_from_db()
        self.assertTrue(existing_user.is_staff)


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


# =============================================================================
# T-086: Shift Management CRUD Tests
# =============================================================================

class ShiftCRUDTests(TestCase):
    """Test shift CRUD operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@test.com',
            password='testpass123',
            is_staff=True,
            role='staff'
        )
        self.staff_profile = StaffProfile.objects.create(
            user=self.staff_user,
            role='manager',
        )
        self.client.login(username='staffuser', password='testpass123')
        self.base_url = '/operations/practice/shifts'
        # Create a test shift
        self.shift = Shift.objects.create(
            staff=self.staff_profile,
            date=date.today(),
            start_time=time(9, 0),
            end_time=time(17, 0),
        )

    def test_shift_list_page_loads(self):
        """Shift list page is accessible."""
        response = self.client.get(f'{self.base_url}/')
        self.assertEqual(response.status_code, 200)

    def test_shift_create_page_loads(self):
        """Shift create page is accessible."""
        response = self.client.get(f'{self.base_url}/add/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')

    def test_shift_create_valid_form(self):
        """Valid form creates Shift."""
        tomorrow = date.today() + timedelta(days=1)
        data = {
            'staff': self.staff_profile.pk,
            'date': tomorrow.isoformat(),
            'start_time': '08:00',
            'end_time': '16:00',
            'notes': 'Morning shift',
        }
        response = self.client.post(f'{self.base_url}/add/', data=data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Shift.objects.filter(date=tomorrow).exists())

    def test_shift_create_end_before_start(self):
        """End time before start time shows error."""
        tomorrow = date.today() + timedelta(days=1)
        data = {
            'staff': self.staff_profile.pk,
            'date': tomorrow.isoformat(),
            'start_time': '17:00',
            'end_time': '09:00',  # Before start
        }
        response = self.client.post(f'{self.base_url}/add/', data=data)
        self.assertEqual(response.status_code, 200)  # Stays on form

    def test_shift_detail_page_loads(self):
        """Shift detail page loads."""
        response = self.client.get(f'{self.base_url}/{self.shift.pk}/')
        self.assertEqual(response.status_code, 200)

    def test_shift_edit_page_loads(self):
        """Shift edit page loads with existing data."""
        response = self.client.get(f'{self.base_url}/{self.shift.pk}/edit/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')

    def test_shift_edit_valid_form(self):
        """Valid edit updates Shift."""
        data = {
            'staff': self.staff_profile.pk,
            'date': self.shift.date.isoformat(),
            'start_time': '10:00',
            'end_time': '18:00',
            'notes': 'Updated shift',
        }
        response = self.client.post(
            f'{self.base_url}/{self.shift.pk}/edit/',
            data=data
        )
        self.assertEqual(response.status_code, 302)
        self.shift.refresh_from_db()
        self.assertEqual(self.shift.start_time, time(10, 0))
        self.assertEqual(self.shift.notes, 'Updated shift')

    def test_shift_delete_confirmation(self):
        """Shift delete confirmation page loads."""
        response = self.client.get(f'{self.base_url}/{self.shift.pk}/delete/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Delete')

    def test_shift_delete_removes_shift(self):
        """POST to delete removes shift."""
        shift_pk = self.shift.pk
        response = self.client.post(f'{self.base_url}/{shift_pk}/delete/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Shift.objects.filter(pk=shift_pk).exists())


class ShiftFormTests(TestCase):
    """Test ShiftForm validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            is_staff=True
        )
        self.staff_profile = StaffProfile.objects.create(
            user=self.user,
            role='receptionist'
        )

    def test_form_valid_with_required_fields(self):
        """Form is valid with required fields."""
        from apps.practice.forms import ShiftForm
        form = ShiftForm(data={
            'staff': self.staff_profile.pk,
            'date': date.today().isoformat(),
            'start_time': '09:00',
            'end_time': '17:00',
        })
        self.assertTrue(form.is_valid())

    def test_form_end_before_start_invalid(self):
        """End time before start time is invalid."""
        from apps.practice.forms import ShiftForm
        form = ShiftForm(data={
            'staff': self.staff_profile.pk,
            'date': date.today().isoformat(),
            'start_time': '17:00',
            'end_time': '09:00',
        })
        self.assertFalse(form.is_valid())


# =============================================================================
# T-087: Task Management CRUD Tests
# =============================================================================

class TaskCRUDTests(TestCase):
    """Test task CRUD operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@test.com',
            password='testpass123',
            is_staff=True,
            role='staff'
        )
        self.staff_profile = StaffProfile.objects.create(
            user=self.staff_user,
            role='manager',
        )
        self.client.login(username='staffuser', password='testpass123')
        self.base_url = '/operations/practice/tasks'
        # Create a test task
        self.task = Task.objects.create(
            title='Test Task',
            description='Test description',
            priority='medium',
            status='pending',
            created_by=self.staff_user,
        )

    def test_task_list_page_loads(self):
        """Task list page is accessible."""
        response = self.client.get(f'{self.base_url}/')
        self.assertEqual(response.status_code, 200)

    def test_task_create_page_loads(self):
        """Task create page is accessible."""
        response = self.client.get(f'{self.base_url}/add/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')

    def test_task_create_valid_form(self):
        """Valid form creates Task."""
        data = {
            'title': 'New Task',
            'description': 'Task description',
            'priority': 'high',
            'status': 'pending',
        }
        response = self.client.post(f'{self.base_url}/add/', data=data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Task.objects.filter(title='New Task').exists())

    def test_task_create_sets_created_by(self):
        """created_by is set to current user."""
        data = {
            'title': 'Auto Created By',
            'priority': 'low',
            'status': 'pending',
        }
        self.client.post(f'{self.base_url}/add/', data=data)
        task = Task.objects.get(title='Auto Created By')
        self.assertEqual(task.created_by, self.staff_user)

    def test_task_detail_page_loads(self):
        """Task detail page loads."""
        response = self.client.get(f'{self.base_url}/{self.task.pk}/')
        self.assertEqual(response.status_code, 200)

    def test_task_edit_page_loads(self):
        """Task edit page loads."""
        response = self.client.get(f'{self.base_url}/{self.task.pk}/edit/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')

    def test_task_edit_valid_form(self):
        """Valid edit updates Task."""
        data = {
            'title': 'Updated Task',
            'priority': 'high',
            'status': 'in_progress',
        }
        response = self.client.post(
            f'{self.base_url}/{self.task.pk}/edit/',
            data=data
        )
        self.assertEqual(response.status_code, 302)
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, 'Updated Task')
        self.assertEqual(self.task.status, 'in_progress')

    def test_task_delete_confirmation(self):
        """Task delete confirmation page loads."""
        response = self.client.get(f'{self.base_url}/{self.task.pk}/delete/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Delete')

    def test_task_delete_removes_task(self):
        """POST to delete removes task."""
        task_pk = self.task.pk
        response = self.client.post(f'{self.base_url}/{task_pk}/delete/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Task.objects.filter(pk=task_pk).exists())


class TaskFormTests(TestCase):
    """Test TaskForm validation."""

    def test_form_valid_with_required_fields(self):
        """Form is valid with required fields."""
        from apps.practice.forms import TaskForm
        form = TaskForm(data={
            'title': 'Test Task',
            'priority': 'medium',
            'status': 'pending',
        })
        self.assertTrue(form.is_valid())

    def test_form_requires_title(self):
        """Title is required."""
        from apps.practice.forms import TaskForm
        form = TaskForm(data={
            'priority': 'medium',
            'status': 'pending',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)


# =============================================================================
# T-088: Time Entry Clock In/Out Tests
# =============================================================================

class TimeEntryCRUDTests(TestCase):
    """Test time entry operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@test.com',
            password='testpass123',
            is_staff=True,
            role='staff'
        )
        self.staff_profile = StaffProfile.objects.create(
            user=self.staff_user,
            role='receptionist',
        )
        self.client.login(username='staffuser', password='testpass123')
        self.base_url = '/operations/practice/time'

    def test_clock_in_creates_entry(self):
        """Clock in creates a new TimeEntry."""
        response = self.client.post(f'{self.base_url}/clock-in/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            TimeEntry.objects.filter(
                staff=self.staff_profile,
                clock_out__isnull=True
            ).exists()
        )

    def test_clock_in_when_already_clocked_in(self):
        """Cannot clock in twice."""
        # First clock in
        TimeEntry.objects.create(
            staff=self.staff_profile,
            clock_in=timezone.now()
        )
        # Try to clock in again
        response = self.client.post(f'{self.base_url}/clock-in/')
        self.assertEqual(response.status_code, 302)
        # Should still only have one open entry
        open_entries = TimeEntry.objects.filter(
            staff=self.staff_profile,
            clock_out__isnull=True
        )
        self.assertEqual(open_entries.count(), 1)

    def test_clock_out_closes_entry(self):
        """Clock out sets clock_out on current entry."""
        entry = TimeEntry.objects.create(
            staff=self.staff_profile,
            clock_in=timezone.now() - timedelta(hours=4)
        )
        response = self.client.post(f'{self.base_url}/clock-out/')
        self.assertEqual(response.status_code, 302)
        entry.refresh_from_db()
        self.assertIsNotNone(entry.clock_out)

    def test_clock_out_when_not_clocked_in(self):
        """Cannot clock out without being clocked in."""
        response = self.client.post(f'{self.base_url}/clock-out/')
        self.assertEqual(response.status_code, 302)
        # Should show error message (redirects back)

    def test_time_entry_edit_page_loads(self):
        """Time entry edit page loads."""
        entry = TimeEntry.objects.create(
            staff=self.staff_profile,
            clock_in=timezone.now() - timedelta(hours=4),
            clock_out=timezone.now()
        )
        response = self.client.get(f'{self.base_url}/{entry.pk}/edit/')
        self.assertEqual(response.status_code, 200)

    def test_time_entry_approve(self):
        """Manager can approve time entry."""
        entry = TimeEntry.objects.create(
            staff=self.staff_profile,
            clock_in=timezone.now() - timedelta(hours=4),
            clock_out=timezone.now(),
            is_approved=False
        )
        response = self.client.post(f'{self.base_url}/{entry.pk}/approve/')
        self.assertEqual(response.status_code, 302)
        entry.refresh_from_db()
        self.assertTrue(entry.is_approved)

    def test_clock_in_without_staff_profile_shows_error(self):
        """User without StaffProfile gets error message."""
        # Create a staff user WITHOUT a StaffProfile
        user_no_profile = User.objects.create_user(
            username='noprofile',
            email='noprofile@test.com',
            password='testpass123',
            is_staff=True,
            role='staff'
        )
        self.client.logout()
        self.client.login(username='noprofile', password='testpass123')

        response = self.client.post(f'{self.base_url}/clock-in/', follow=True)
        self.assertEqual(response.status_code, 200)
        # Should show error message
        self.assertContains(response, 'do not have a staff profile')
