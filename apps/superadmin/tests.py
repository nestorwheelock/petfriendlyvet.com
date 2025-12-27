"""Tests for superadmin role management UI."""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()


class RoleListViewTests(TestCase):
    """Test role list view."""

    def setUp(self):
        """Create superuser for testing."""
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass'
        )
        self.client.login(username='admin', password='adminpass')

    def test_role_list_displays_default_roles(self):
        """Role list should display default roles from migration."""
        response = self.client.get(reverse('superadmin:role_list'))
        self.assertEqual(response.status_code, 200)
        # Check for default roles in response
        self.assertContains(response, 'Pet Owner')
        self.assertContains(response, 'Receptionist')
        self.assertContains(response, 'Veterinarian')
        self.assertContains(response, 'Administrator')

    def test_role_list_shows_hierarchy_levels(self):
        """Role list should show hierarchy levels."""
        response = self.client.get(reverse('superadmin:role_list'))
        self.assertEqual(response.status_code, 200)
        # Context should have roles
        self.assertIn('roles', response.context)

    def test_role_list_requires_superuser(self):
        """Role list should only be accessible to superusers."""
        self.client.logout()
        regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='pass'
        )
        self.client.login(username='regular', password='pass')

        response = self.client.get(reverse('superadmin:role_list'))
        # Should redirect or return 403
        self.assertIn(response.status_code, [302, 403])


class RoleCreateViewTests(TestCase):
    """Test role creation."""

    def setUp(self):
        """Create superuser for testing."""
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass'
        )
        self.client.login(username='admin', password='adminpass')

    def test_role_create_form_accessible(self):
        """Role create form should be accessible."""
        response = self.client.get(reverse('superadmin:role_create'))
        self.assertEqual(response.status_code, 200)

    def test_role_create_creates_role_and_group(self):
        """Creating a role should also create linked Django Group."""
        from apps.accounts.models import Role

        initial_count = Role.objects.count()

        response = self.client.post(reverse('superadmin:role_create'), {
            'name': 'Test Manager',
            'slug': 'test-manager',
            'hierarchy_level': 55,
            'description': 'Test manager role',
        })

        # Should redirect on success
        self.assertEqual(response.status_code, 302)

        # Role should be created
        self.assertEqual(Role.objects.count(), initial_count + 1)

        # Group should be created
        role = Role.objects.get(slug='test-manager')
        self.assertIsNotNone(role.group)
        self.assertEqual(role.group.name, 'Test Manager')


class RoleUpdateViewTests(TestCase):
    """Test role updates."""

    def setUp(self):
        """Create superuser and test role."""
        from apps.accounts.models import Role

        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass'
        )
        self.client.login(username='admin', password='adminpass')

        # Get a default role to edit
        self.role = Role.objects.get(slug='receptionist')

    def test_role_update_form_accessible(self):
        """Role update form should be accessible."""
        response = self.client.get(
            reverse('superadmin:role_update', kwargs={'pk': self.role.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_role_update_changes_role(self):
        """Updating role should change its properties."""
        response = self.client.post(
            reverse('superadmin:role_update', kwargs={'pk': self.role.pk}),
            {
                'name': self.role.name,
                'slug': self.role.slug,
                'hierarchy_level': 25,  # Changed from 20
                'description': 'Updated description',
            }
        )

        self.assertEqual(response.status_code, 302)

        self.role.refresh_from_db()
        self.assertEqual(self.role.hierarchy_level, 25)
        self.assertEqual(self.role.description, 'Updated description')


class UserRoleAssignmentTests(TestCase):
    """Test assigning roles to users."""

    def setUp(self):
        """Create superuser and test data."""
        from apps.accounts.models import Role

        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass'
        )
        self.client.login(username='admin', password='adminpass')

        # Create a test user
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass'
        )

        self.role = Role.objects.get(slug='receptionist')

    def test_user_edit_shows_role_options(self):
        """User edit form should show role assignment options."""
        response = self.client.get(
            reverse('superadmin:user_update', kwargs={'pk': self.test_user.pk})
        )
        self.assertEqual(response.status_code, 200)
        # Form should have role field
        self.assertContains(response, 'role')
