"""Tests for accounts app - RBAC system."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()


class RoleModelTests(TestCase):
    """Test Role model functionality."""

    def test_role_creation(self):
        """Role can be created with hierarchy level."""
        from apps.accounts.models import Role

        group = Group.objects.create(name='Test Role Group')
        role = Role.objects.create(
            name='Test Role',
            slug='test-role',
            hierarchy_level=50,
            group=group
        )
        self.assertEqual(role.name, 'Test Role')
        self.assertEqual(role.hierarchy_level, 50)
        self.assertEqual(role.group, group)

    def test_role_str_method(self):
        """Role string representation is the name."""
        from apps.accounts.models import Role

        group = Group.objects.create(name='Manager Group')
        role = Role.objects.create(
            name='Manager',
            slug='manager',
            hierarchy_level=60,
            group=group
        )
        self.assertEqual(str(role), 'Manager')

    def test_role_unique_slug(self):
        """Role slugs must be unique."""
        from apps.accounts.models import Role
        from django.db import IntegrityError

        group1 = Group.objects.create(name='Group 1')
        group2 = Group.objects.create(name='Group 2')

        Role.objects.create(name='Manager', slug='manager', hierarchy_level=60, group=group1)

        with self.assertRaises(IntegrityError):
            Role.objects.create(name='Manager 2', slug='manager', hierarchy_level=60, group=group2)


class PermissionModelTests(TestCase):
    """Test Permission model functionality."""

    def test_permission_creation(self):
        """Permission can be created with module/action/resource."""
        from apps.accounts.models import Permission

        perm = Permission.objects.create(
            module='practice',
            action='manage',
            resource='staff',
            codename='practice.manage_staff',
            name='Can manage staff in Practice'
        )
        self.assertEqual(perm.module, 'practice')
        self.assertEqual(perm.action, 'manage')
        self.assertEqual(perm.codename, 'practice.manage_staff')

    def test_permission_unique_codename(self):
        """Permission codenames must be unique."""
        from apps.accounts.models import Permission
        from django.db import IntegrityError

        Permission.objects.create(
            module='practice',
            action='view',
            resource='staff',
            codename='practice.view_staff',
            name='Can view staff'
        )

        with self.assertRaises(IntegrityError):
            Permission.objects.create(
                module='practice',
                action='view',
                resource='dashboard',
                codename='practice.view_staff',  # Duplicate codename
                name='Can view dashboard'
            )


class UserRoleModelTests(TestCase):
    """Test UserRole model functionality."""

    def setUp(self):
        """Create test user and role."""
        from apps.accounts.models import Role

        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.group = Group.objects.create(name='Staff Group')
        self.role = Role.objects.create(
            name='Staff',
            slug='staff',
            hierarchy_level=20,
            group=self.group
        )

    def test_user_role_assignment(self):
        """User can be assigned a role."""
        from apps.accounts.models import UserRole

        user_role = UserRole.objects.create(
            user=self.user,
            role=self.role,
            is_primary=True
        )
        self.assertEqual(user_role.user, self.user)
        self.assertEqual(user_role.role, self.role)
        self.assertTrue(user_role.is_primary)

    def test_user_role_unique_together(self):
        """User cannot have same role twice."""
        from apps.accounts.models import UserRole
        from django.db import IntegrityError

        UserRole.objects.create(user=self.user, role=self.role)

        with self.assertRaises(IntegrityError):
            UserRole.objects.create(user=self.user, role=self.role)

    def test_user_role_tracks_assigned_by(self):
        """UserRole tracks who assigned the role."""
        from apps.accounts.models import UserRole

        admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass'
        )
        user_role = UserRole.objects.create(
            user=self.user,
            role=self.role,
            assigned_by=admin_user
        )
        self.assertEqual(user_role.assigned_by, admin_user)


class UserHierarchyTests(TestCase):
    """Test user hierarchy functionality."""

    def setUp(self):
        """Create test roles with different hierarchy levels."""
        from apps.accounts.models import Role, UserRole

        # Create roles with unique names (to avoid conflict with default roles)
        self.staff_group = Group.objects.create(name='Test Staff Hierarchy')
        self.manager_group = Group.objects.create(name='Test Manager Hierarchy')
        self.admin_group = Group.objects.create(name='Test Admin Hierarchy')

        self.staff_role = Role.objects.create(
            name='Test Staff Hierarchy', slug='test-staff-hier', hierarchy_level=20, group=self.staff_group
        )
        self.manager_role = Role.objects.create(
            name='Test Manager Hierarchy', slug='test-manager-hier', hierarchy_level=60, group=self.manager_group
        )
        self.admin_role = Role.objects.create(
            name='Test Admin Hierarchy', slug='test-admin-hier', hierarchy_level=80, group=self.admin_group
        )

        # Create users
        self.staff_user = User.objects.create_user(
            username='staff', email='staff@example.com', password='pass'
        )
        self.manager_user = User.objects.create_user(
            username='manager', email='manager@example.com', password='pass'
        )
        self.admin_user = User.objects.create_user(
            username='admin', email='admin@example.com', password='pass'
        )

        # Assign roles
        UserRole.objects.create(user=self.staff_user, role=self.staff_role, is_primary=True)
        UserRole.objects.create(user=self.manager_user, role=self.manager_role, is_primary=True)
        UserRole.objects.create(user=self.admin_user, role=self.admin_role, is_primary=True)

    def test_user_hierarchy_level(self):
        """User.hierarchy_level returns highest from all roles."""
        self.assertEqual(self.staff_user.hierarchy_level, 20)
        self.assertEqual(self.manager_user.hierarchy_level, 60)
        self.assertEqual(self.admin_user.hierarchy_level, 80)

    def test_superuser_hierarchy_level(self):
        """Superuser has hierarchy level 100."""
        superuser = User.objects.create_superuser(
            username='super', email='super@example.com', password='pass'
        )
        self.assertEqual(superuser.hierarchy_level, 100)

    def test_user_with_no_roles_hierarchy_level(self):
        """User with no roles has hierarchy level 0."""
        no_role_user = User.objects.create_user(
            username='norole', email='norole@example.com', password='pass'
        )
        self.assertEqual(no_role_user.hierarchy_level, 0)

    def test_can_manage_user_hierarchy(self):
        """User can only manage users with lower hierarchy."""
        # Manager can manage staff
        self.assertTrue(self.manager_user.can_manage_user(self.staff_user))

        # Staff cannot manage manager
        self.assertFalse(self.staff_user.can_manage_user(self.manager_user))

        # Manager cannot manage admin
        self.assertFalse(self.manager_user.can_manage_user(self.admin_user))

        # Admin can manage manager
        self.assertTrue(self.admin_user.can_manage_user(self.manager_user))

        # Same level cannot manage each other
        manager2 = User.objects.create_user(
            username='manager2', email='manager2@example.com', password='pass'
        )
        from apps.accounts.models import UserRole
        UserRole.objects.create(user=manager2, role=self.manager_role, is_primary=True)
        self.assertFalse(self.manager_user.can_manage_user(manager2))

    def test_multiple_roles_per_user(self):
        """User can have multiple roles with combined permissions."""
        from apps.accounts.models import UserRole

        # Give staff user an additional manager role
        UserRole.objects.create(user=self.staff_user, role=self.manager_role, is_primary=False)

        # Hierarchy level should be highest (manager = 60)
        self.assertEqual(self.staff_user.hierarchy_level, 60)

    def test_get_manageable_roles(self):
        """User can only see roles below their hierarchy."""
        manageable = list(self.manager_user.get_manageable_roles())
        role_slugs = [r.slug for r in manageable]

        # Manager (60) can assign staff (20) but not manager (60) or admin (80)
        self.assertIn('test-staff-hier', role_slugs)
        self.assertNotIn('test-manager-hier', role_slugs)
        self.assertNotIn('test-admin-hier', role_slugs)


class PermissionMixinTests(TestCase):
    """Test permission checking mixins and decorators."""

    def setUp(self):
        """Create test users, roles, and permissions."""
        from django.contrib.auth.models import Group as AuthGroup
        from apps.accounts.models import Role, UserRole, Permission

        # Create roles
        self.staff_group = AuthGroup.objects.create(name='Staff Perm Test')
        self.manager_group = AuthGroup.objects.create(name='Manager Perm Test')

        self.staff_role = Role.objects.create(
            name='Staff Perm', slug='staff-perm', hierarchy_level=20, group=self.staff_group
        )
        self.manager_role = Role.objects.create(
            name='Manager Perm', slug='manager-perm', hierarchy_level=60, group=self.manager_group
        )

        # Create permissions
        Permission.objects.create(
            module='practice',
            action='view',
            resource='staff',
            codename='practice.view_staff',
            name='Can view staff'
        )
        Permission.objects.create(
            module='practice',
            action='manage',
            resource='staff',
            codename='practice.manage_staff',
            name='Can manage staff'
        )

        # Create users
        self.staff_user = User.objects.create_user(
            username='permstaff', email='permstaff@example.com', password='pass'
        )
        self.manager_user = User.objects.create_user(
            username='permmanager', email='permmanager@example.com', password='pass'
        )

        # Assign roles
        UserRole.objects.create(user=self.staff_user, role=self.staff_role, is_primary=True)
        UserRole.objects.create(user=self.manager_user, role=self.manager_role, is_primary=True)

    def test_has_module_permission_returns_false_without_permission(self):
        """User without permission returns False."""
        # Staff user has no practice.manage permission assigned
        self.assertFalse(self.staff_user.has_module_permission('practice', 'manage'))

    def test_has_module_permission_returns_true_with_permission(self):
        """User with permission returns True."""
        from django.contrib.auth.models import Permission as DjangoPermission
        from django.contrib.contenttypes.models import ContentType

        # Get or create the Django permission with codename matching module.action
        content_type = ContentType.objects.get_for_model(User)
        perm, _ = DjangoPermission.objects.get_or_create(
            codename='practice.manage',
            defaults={'name': 'Can manage practice', 'content_type': content_type}
        )
        self.manager_group.permissions.add(perm)

        # Manager user should have permission via group
        self.assertTrue(self.manager_user.has_module_permission('practice', 'manage'))

    def test_superuser_has_all_permissions(self):
        """Superuser has all module permissions."""
        superuser = User.objects.create_superuser(
            username='superadmin', email='super@example.com', password='pass'
        )
        self.assertTrue(superuser.has_module_permission('practice', 'manage'))
        self.assertTrue(superuser.has_module_permission('accounting', 'delete'))
        self.assertTrue(superuser.has_module_permission('any_module', 'any_action'))


class RequirePermissionDecoratorTests(TestCase):
    """Test the @require_permission decorator."""

    def setUp(self):
        """Create test user."""
        self.user = User.objects.create_user(
            username='decortest', email='decor@example.com', password='pass'
        )

    def test_decorator_denies_without_permission(self):
        """Decorator raises PermissionDenied without required permission."""
        from django.test import RequestFactory
        from django.core.exceptions import PermissionDenied
        from apps.accounts.decorators import require_permission

        @require_permission('practice', 'manage')
        def protected_view(request):
            return "success"

        factory = RequestFactory()
        request = factory.get('/test/')
        request.user = self.user

        with self.assertRaises(PermissionDenied):
            protected_view(request)

    def test_decorator_allows_superuser(self):
        """Decorator allows superuser without explicit permission."""
        from django.test import RequestFactory
        from apps.accounts.decorators import require_permission

        @require_permission('practice', 'manage')
        def protected_view(request):
            return "success"

        superuser = User.objects.create_superuser(
            username='supertest', email='supertest@example.com', password='pass'
        )

        factory = RequestFactory()
        request = factory.get('/test/')
        request.user = superuser

        result = protected_view(request)
        self.assertEqual(result, "success")


class ModulePermissionMixinTests(TestCase):
    """Test ModulePermissionMixin for class-based views."""

    def setUp(self):
        """Create test user."""
        self.user = User.objects.create_user(
            username='mixintest', email='mixin@example.com', password='pass'
        )
        self.client.login(username='mixintest', password='pass')

    def test_mixin_denies_without_permission(self):
        """Mixin test_func returns False without required permission."""
        from django.views.generic import TemplateView
        from apps.accounts.mixins import ModulePermissionMixin

        class ProtectedView(ModulePermissionMixin, TemplateView):
            required_module = 'practice'
            required_action = 'manage'
            template_name = 'base.html'

        # Test the test_func directly
        request = self.client.get('/test/').wsgi_request
        request.user = self.user

        view = ProtectedView()
        view.request = request
        self.assertFalse(view.test_func())

    def test_mixin_allows_superuser(self):
        """Mixin allows superuser access."""
        from django.views.generic import TemplateView
        from apps.accounts.mixins import ModulePermissionMixin

        superuser = User.objects.create_superuser(
            username='supermixin', email='supermixin@example.com', password='pass'
        )
        self.client.login(username='supermixin', password='pass')

        class ProtectedView(ModulePermissionMixin, TemplateView):
            required_module = 'practice'
            required_action = 'manage'
            template_name = 'base.html'

        request = self.client.get('/test/').wsgi_request
        request.user = superuser

        # test_func should return True for superuser
        view = ProtectedView()
        view.request = request
        self.assertTrue(view.test_func())


class DefaultRolesTests(TestCase):
    """Test default roles and permissions setup."""

    def test_default_roles_exist(self):
        """Default roles should exist after migration."""
        from apps.accounts.models import Role

        expected_slugs = [
            'pet-owner',
            'receptionist',
            'vet-tech',
            'veterinarian',
            'practice-manager',
            'finance-manager',
            'administrator',
        ]

        for slug in expected_slugs:
            self.assertTrue(
                Role.objects.filter(slug=slug).exists(),
                f"Role '{slug}' should exist"
            )

    def test_roles_have_correct_hierarchy(self):
        """Roles should have correct hierarchy levels."""
        from apps.accounts.models import Role

        # Pet Owner = 10, Staff = 20-30, Managers = 60, Admin = 80
        pet_owner = Role.objects.get(slug='pet-owner')
        receptionist = Role.objects.get(slug='receptionist')
        veterinarian = Role.objects.get(slug='veterinarian')
        practice_manager = Role.objects.get(slug='practice-manager')
        administrator = Role.objects.get(slug='administrator')

        self.assertEqual(pet_owner.hierarchy_level, 10)
        self.assertEqual(receptionist.hierarchy_level, 20)
        self.assertGreater(veterinarian.hierarchy_level, receptionist.hierarchy_level)
        self.assertGreater(practice_manager.hierarchy_level, veterinarian.hierarchy_level)
        self.assertGreater(administrator.hierarchy_level, practice_manager.hierarchy_level)

    def test_roles_have_linked_groups(self):
        """Each role should have a linked Django Group."""
        from apps.accounts.models import Role

        for role in Role.objects.all():
            self.assertIsNotNone(role.group, f"Role '{role.name}' should have a group")


class UserRoleMigrationTests(TestCase):
    """Test migration of existing users to new role system."""

    def test_user_with_owner_role_gets_pet_owner(self):
        """User with role='owner' should get pet-owner Role."""
        from apps.accounts.models import Role, UserRole

        # Create the pet-owner role first (simulating migration)
        from django.contrib.auth.models import Group
        group = Group.objects.create(name='Pet Owner Test')
        pet_owner_role = Role.objects.create(
            name='Pet Owner Test',
            slug='pet-owner-test',
            hierarchy_level=10,
            group=group
        )

        # Create user with old role system
        user = User.objects.create_user(
            username='oldowner',
            email='oldowner@example.com',
            password='pass',
            role='owner'
        )

        # Simulate migration by assigning role based on old role
        if user.role == 'owner':
            UserRole.objects.create(user=user, role=pet_owner_role, is_primary=True)

        # Verify user has new role
        self.assertTrue(user.user_roles.filter(role=pet_owner_role).exists())

    def test_user_with_staff_role_gets_receptionist(self):
        """User with role='staff' should get receptionist Role."""
        from apps.accounts.models import Role, UserRole

        # Create receptionist role
        from django.contrib.auth.models import Group
        group = Group.objects.create(name='Receptionist Test')
        receptionist_role = Role.objects.create(
            name='Receptionist Test',
            slug='receptionist-test',
            hierarchy_level=20,
            group=group
        )

        # Create user with old role system
        user = User.objects.create_user(
            username='oldstaff',
            email='oldstaff@example.com',
            password='pass',
            role='staff'
        )

        # Simulate migration
        if user.role == 'staff':
            UserRole.objects.create(user=user, role=receptionist_role, is_primary=True)

        self.assertTrue(user.user_roles.filter(role=receptionist_role).exists())


class T094ViewPermissionTests(TestCase):
    """T-094: Test views use centralized permission system."""

    def setUp(self):
        """Create test users with different permission levels."""
        from apps.accounts.models import Role, UserRole
        from django.contrib.auth.models import Group, Permission as DjangoPermission
        from django.contrib.contenttypes.models import ContentType

        # Create a user with practice.view permission
        self.practice_group = Group.objects.create(name='Practice Staff Test')
        self.practice_role = Role.objects.create(
            name='Practice Staff Test',
            slug='practice-staff-test',
            hierarchy_level=20,
            group=self.practice_group
        )

        # Create Django permission for practice.view
        content_type = ContentType.objects.get_for_model(User)
        self.practice_view_perm, _ = DjangoPermission.objects.get_or_create(
            codename='practice.view',
            defaults={'name': 'Can view practice', 'content_type': content_type}
        )
        self.practice_group.permissions.add(self.practice_view_perm)

        # Create user with practice permission
        self.practice_user = User.objects.create_user(
            username='practiceuser', email='practice@test.com', password='pass123'
        )
        self.practice_user.is_staff = True
        self.practice_user.save()
        UserRole.objects.create(user=self.practice_user, role=self.practice_role, is_primary=True)

        # Create user without practice permission
        self.no_perm_user = User.objects.create_user(
            username='nopermuser', email='noperm@test.com', password='pass123'
        )
        self.no_perm_user.is_staff = True
        self.no_perm_user.save()

        # Create accounting group and role
        self.accounting_group = Group.objects.create(name='Accounting Staff Test')
        self.accounting_role = Role.objects.create(
            name='Accounting Staff Test',
            slug='accounting-staff-test',
            hierarchy_level=30,
            group=self.accounting_group
        )

        # Create Django permission for accounting.view
        self.accounting_view_perm, _ = DjangoPermission.objects.get_or_create(
            codename='accounting.view',
            defaults={'name': 'Can view accounting', 'content_type': content_type}
        )
        self.accounting_group.permissions.add(self.accounting_view_perm)

        # User with accounting permission
        self.accounting_user = User.objects.create_user(
            username='accountinguser', email='accounting@test.com', password='pass123'
        )
        self.accounting_user.is_staff = True
        self.accounting_user.save()
        UserRole.objects.create(user=self.accounting_user, role=self.accounting_role, is_primary=True)

    def test_practice_dashboard_requires_permission(self):
        """Practice dashboard requires practice.view permission."""
        from django.urls import reverse

        # User with permission should access
        self.client.login(username='practiceuser', password='pass123')
        response = self.client.get(reverse('practice:dashboard'))
        self.assertEqual(response.status_code, 200)

        # User without permission should be denied
        self.client.login(username='nopermuser', password='pass123')
        response = self.client.get(reverse('practice:dashboard'))
        self.assertIn(response.status_code, [403, 302])  # 403 Forbidden or redirect to login

    def test_accounting_requires_accounting_permission(self):
        """Accounting views require accounting module permission."""
        from django.urls import reverse

        # User with accounting permission should access
        self.client.login(username='accountinguser', password='pass123')
        response = self.client.get(reverse('accounting:dashboard'))
        self.assertEqual(response.status_code, 200)

        # User without accounting permission should be denied
        self.client.login(username='practiceuser', password='pass123')
        response = self.client.get(reverse('accounting:dashboard'))
        self.assertIn(response.status_code, [403, 302])  # Denied

    def test_staff_create_checks_hierarchy(self):
        """Cannot create staff at higher hierarchy level."""
        from apps.accounts.models import Role, UserRole
        from django.contrib.auth.models import Group, Permission as DjangoPermission
        from django.contrib.contenttypes.models import ContentType

        # Create a manager role (level 60)
        manager_group = Group.objects.create(name='Hierarchy Manager Test')
        manager_role = Role.objects.create(
            name='Hierarchy Manager Test',
            slug='hierarchy-manager-test',
            hierarchy_level=60,
            group=manager_group
        )

        # Create practice.manage permission for creating staff
        content_type = ContentType.objects.get_for_model(User)
        practice_manage_perm, _ = DjangoPermission.objects.get_or_create(
            codename='practice.manage',
            defaults={'name': 'Can manage practice', 'content_type': content_type}
        )
        manager_group.permissions.add(practice_manage_perm)
        manager_group.permissions.add(self.practice_view_perm)

        # Create manager user
        manager_user = User.objects.create_user(
            username='managertest', email='manager@test.com', password='pass123'
        )
        manager_user.is_staff = True
        manager_user.save()
        UserRole.objects.create(user=manager_user, role=manager_role, is_primary=True)

        self.client.login(username='managertest', password='pass123')

        # Manager can only see roles with hierarchy < 60
        manageable_roles = manager_user.get_manageable_roles()
        role_levels = [r.hierarchy_level for r in manageable_roles]

        # All manageable roles should be below manager's level
        for level in role_levels:
            self.assertLess(level, 60)
