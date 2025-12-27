"""Integration tests for RBAC (Role-Based Access Control) system.

T-095: Comprehensive testing of the permission system including:
- End-to-end permission workflows
- Hierarchy enforcement
- Privilege escalation prevention
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission as DjangoPermission
from django.contrib.contenttypes.models import ContentType

from apps.accounts.models import Role, UserRole, Permission

User = get_user_model()


class FullPermissionWorkflowTests(TestCase):
    """Test complete permission workflow: create role, assign to user, verify access."""

    def test_full_permission_workflow(self):
        """Create role, assign to user, verify access."""
        # Step 1: Create a role with permissions
        group = Group.objects.create(name='Custom Workflow Role')
        role = Role.objects.create(
            name='Custom Workflow Role',
            slug='custom-workflow-role',
            hierarchy_level=35,
            group=group
        )

        # Step 2: Add practice.view permission to the role's group
        content_type = ContentType.objects.get_for_model(User)
        practice_view_perm, _ = DjangoPermission.objects.get_or_create(
            codename='practice.view',
            defaults={'name': 'Can view practice', 'content_type': content_type}
        )
        group.permissions.add(practice_view_perm)

        # Step 3: Create a user and assign the role
        user = User.objects.create_user(
            username='workflowuser',
            email='workflow@test.com',
            password='testpass123'
        )
        UserRole.objects.create(user=user, role=role, is_primary=True)

        # Step 4: Verify user has the permission
        self.assertTrue(user.has_module_permission('practice', 'view'))

        # Step 5: Verify user can access a protected view
        client = Client()
        client.login(username='workflowuser', password='testpass123')
        response = client.get(reverse('practice:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_user_without_permission_denied(self):
        """User without permission is denied access."""
        # Create user without any roles/permissions
        user = User.objects.create_user(
            username='denieduser',
            email='denied@test.com',
            password='testpass123'
        )

        # Verify user doesn't have permission
        self.assertFalse(user.has_module_permission('practice', 'view'))

        # Verify user is denied access
        client = Client()
        client.login(username='denieduser', password='testpass123')
        response = client.get(reverse('practice:dashboard'))
        self.assertIn(response.status_code, [403, 302])  # Forbidden or redirect


class HierarchyEnforcementTests(TestCase):
    """Test hierarchy-based access control."""

    def setUp(self):
        """Create users at different hierarchy levels."""
        # Create roles at different levels
        self.staff_group = Group.objects.create(name='Hierarchy Staff')
        self.manager_group = Group.objects.create(name='Hierarchy Manager')
        self.admin_group = Group.objects.create(name='Hierarchy Admin')

        self.staff_role = Role.objects.create(
            name='Hierarchy Staff',
            slug='hierarchy-staff',
            hierarchy_level=20,
            group=self.staff_group
        )
        self.manager_role = Role.objects.create(
            name='Hierarchy Manager',
            slug='hierarchy-manager',
            hierarchy_level=60,
            group=self.manager_group
        )
        self.admin_role = Role.objects.create(
            name='Hierarchy Admin',
            slug='hierarchy-admin',
            hierarchy_level=80,
            group=self.admin_group
        )

        # Create users
        self.staff_user = User.objects.create_user(
            username='hierstaff', email='hierstaff@test.com', password='pass'
        )
        self.manager_user = User.objects.create_user(
            username='hiermanager', email='hiermanager@test.com', password='pass'
        )
        self.admin_user = User.objects.create_user(
            username='hieradmin', email='hieradmin@test.com', password='pass'
        )

        # Assign roles
        UserRole.objects.create(user=self.staff_user, role=self.staff_role, is_primary=True)
        UserRole.objects.create(user=self.manager_user, role=self.manager_role, is_primary=True)
        UserRole.objects.create(user=self.admin_user, role=self.admin_role, is_primary=True)

    def test_manager_can_manage_staff(self):
        """Manager (level 60) can manage staff (level 20)."""
        self.assertTrue(self.manager_user.can_manage_user(self.staff_user))

    def test_staff_cannot_manage_manager(self):
        """Staff (level 20) cannot manage manager (level 60)."""
        self.assertFalse(self.staff_user.can_manage_user(self.manager_user))

    def test_manager_cannot_manage_admin(self):
        """Manager (level 60) cannot manage admin (level 80)."""
        self.assertFalse(self.manager_user.can_manage_user(self.admin_user))

    def test_admin_can_manage_everyone_below(self):
        """Admin (level 80) can manage both manager and staff."""
        self.assertTrue(self.admin_user.can_manage_user(self.manager_user))
        self.assertTrue(self.admin_user.can_manage_user(self.staff_user))

    def test_same_level_cannot_manage_each_other(self):
        """Users at same hierarchy level cannot manage each other."""
        # Create another manager
        manager2 = User.objects.create_user(
            username='hiermanager2', email='hiermanager2@test.com', password='pass'
        )
        UserRole.objects.create(user=manager2, role=self.manager_role, is_primary=True)

        self.assertFalse(self.manager_user.can_manage_user(manager2))
        self.assertFalse(manager2.can_manage_user(self.manager_user))

    def test_superuser_has_highest_level(self):
        """Superuser has hierarchy level 100."""
        superuser = User.objects.create_superuser(
            username='superuser', email='super@test.com', password='pass'
        )
        self.assertEqual(superuser.hierarchy_level, 100)
        self.assertTrue(superuser.can_manage_user(self.admin_user))

    def test_user_without_roles_has_level_zero(self):
        """User without any roles has hierarchy level 0."""
        no_role_user = User.objects.create_user(
            username='norole', email='norole@test.com', password='pass'
        )
        self.assertEqual(no_role_user.hierarchy_level, 0)


class PrivilegeEscalationPreventionTests(TestCase):
    """Test that users cannot escalate their privileges."""

    def setUp(self):
        """Create roles at different levels."""
        self.staff_group = Group.objects.create(name='Escalation Staff')
        self.manager_group = Group.objects.create(name='Escalation Manager')
        self.admin_group = Group.objects.create(name='Escalation Admin')

        self.staff_role = Role.objects.create(
            name='Escalation Staff',
            slug='escalation-staff',
            hierarchy_level=20,
            group=self.staff_group
        )
        self.manager_role = Role.objects.create(
            name='Escalation Manager',
            slug='escalation-manager',
            hierarchy_level=60,
            group=self.manager_group
        )
        self.admin_role = Role.objects.create(
            name='Escalation Admin',
            slug='escalation-admin',
            hierarchy_level=80,
            group=self.admin_group
        )

        # Create manager user
        self.manager_user = User.objects.create_user(
            username='escmanager', email='escmanager@test.com', password='pass'
        )
        UserRole.objects.create(user=self.manager_user, role=self.manager_role, is_primary=True)

    def test_manager_cannot_escalate_privileges(self):
        """Manager cannot assign admin role (higher than their level)."""
        manageable_roles = list(self.manager_user.get_manageable_roles())
        role_slugs = [r.slug for r in manageable_roles]

        # Manager can only see roles below their level (60)
        self.assertIn('escalation-staff', role_slugs)  # Staff (20) is below
        self.assertNotIn('escalation-manager', role_slugs)  # Manager (60) is at same level
        self.assertNotIn('escalation-admin', role_slugs)  # Admin (80) is above

    def test_staff_cannot_see_any_manageable_roles(self):
        """Staff (level 20) cannot see most manageable roles."""
        staff_user = User.objects.create_user(
            username='escstaff', email='escstaff@test.com', password='pass'
        )
        UserRole.objects.create(user=staff_user, role=self.staff_role, is_primary=True)

        manageable_roles = list(staff_user.get_manageable_roles())
        # Staff at level 20 can only see roles below 20 (very limited)
        for role in manageable_roles:
            self.assertLess(role.hierarchy_level, 20)


class MultipleRolesTests(TestCase):
    """Test users with multiple roles."""

    def test_user_with_multiple_roles_gets_highest_level(self):
        """User with multiple roles gets highest hierarchy level."""
        group1 = Group.objects.create(name='Multi Role 1')
        group2 = Group.objects.create(name='Multi Role 2')

        role1 = Role.objects.create(
            name='Multi Role 1',
            slug='multi-role-1',
            hierarchy_level=20,
            group=group1
        )
        role2 = Role.objects.create(
            name='Multi Role 2',
            slug='multi-role-2',
            hierarchy_level=60,
            group=group2
        )

        user = User.objects.create_user(
            username='multirole', email='multi@test.com', password='pass'
        )
        UserRole.objects.create(user=user, role=role1, is_primary=True)
        UserRole.objects.create(user=user, role=role2, is_primary=False)

        # User should have highest level (60)
        self.assertEqual(user.hierarchy_level, 60)

    def test_user_with_multiple_roles_gets_combined_permissions(self):
        """User with multiple roles gets permissions from all roles."""
        content_type = ContentType.objects.get_for_model(User)

        # Create two groups with different permissions
        group1 = Group.objects.create(name='Perm Group 1')
        group2 = Group.objects.create(name='Perm Group 2')

        perm1, _ = DjangoPermission.objects.get_or_create(
            codename='practice.view',
            defaults={'name': 'Can view practice', 'content_type': content_type}
        )
        perm2, _ = DjangoPermission.objects.get_or_create(
            codename='accounting.view',
            defaults={'name': 'Can view accounting', 'content_type': content_type}
        )

        group1.permissions.add(perm1)
        group2.permissions.add(perm2)

        role1 = Role.objects.create(
            name='Perm Role 1',
            slug='perm-role-1',
            hierarchy_level=30,
            group=group1
        )
        role2 = Role.objects.create(
            name='Perm Role 2',
            slug='perm-role-2',
            hierarchy_level=40,
            group=group2
        )

        user = User.objects.create_user(
            username='comboperm', email='combo@test.com', password='pass'
        )
        UserRole.objects.create(user=user, role=role1, is_primary=True)
        UserRole.objects.create(user=user, role=role2, is_primary=False)

        # User should have both permissions
        self.assertTrue(user.has_module_permission('practice', 'view'))
        self.assertTrue(user.has_module_permission('accounting', 'view'))


class ModulePermissionCreationTests(TestCase):
    """T-096a: Test that module permissions are created by migration."""

    def test_module_permissions_exist(self):
        """All module permissions are created."""
        perm = DjangoPermission.objects.filter(codename='practice.view')
        self.assertTrue(perm.exists(), "practice.view permission should exist")

    def test_all_modules_have_permissions(self):
        """Each module has view/create/edit/delete/manage permissions."""
        modules = [
            'practice', 'accounting', 'inventory', 'pharmacy',
            'appointments', 'delivery', 'crm', 'reports',
            'billing', 'superadmin', 'audit', 'email_marketing', 'core'
        ]
        actions = ['view', 'create', 'edit', 'delete', 'manage']

        for module in modules:
            for action in actions:
                codename = f'{module}.{action}'
                self.assertTrue(
                    DjangoPermission.objects.filter(codename=codename).exists(),
                    f"Missing permission: {codename}"
                )

    def test_permissions_have_correct_content_type(self):
        """Module permissions use User content type."""
        perm = DjangoPermission.objects.filter(codename='practice.view').first()
        if perm:
            content_type = ContentType.objects.get_for_model(User)
            self.assertEqual(perm.content_type, content_type)


class DefaultRolePermissionTests(TestCase):
    """T-096a: Test that default roles have appropriate permissions assigned."""

    def test_administrator_has_manage_permissions(self):
        """Administrator role has manage permission for most modules."""
        admin = Role.objects.get(slug='administrator')
        self.assertTrue(
            admin.group.permissions.filter(codename='practice.manage').exists(),
            "Administrator should have practice.manage"
        )
        self.assertTrue(
            admin.group.permissions.filter(codename='accounting.manage').exists(),
            "Administrator should have accounting.manage"
        )
        self.assertTrue(
            admin.group.permissions.filter(codename='inventory.manage').exists(),
            "Administrator should have inventory.manage"
        )

    def test_receptionist_has_limited_permissions(self):
        """Receptionist has view access but not accounting."""
        receptionist = Role.objects.get(slug='receptionist')
        self.assertTrue(
            receptionist.group.permissions.filter(codename='appointments.view').exists(),
            "Receptionist should have appointments.view"
        )
        self.assertTrue(
            receptionist.group.permissions.filter(codename='practice.view').exists(),
            "Receptionist should have practice.view"
        )
        self.assertFalse(
            receptionist.group.permissions.filter(codename='accounting.view').exists(),
            "Receptionist should NOT have accounting.view"
        )

    def test_finance_manager_has_accounting_not_practice_manage(self):
        """Finance Manager has accounting but not practice manage."""
        fm = Role.objects.get(slug='finance-manager')
        self.assertTrue(
            fm.group.permissions.filter(codename='accounting.manage').exists(),
            "Finance Manager should have accounting.manage"
        )
        self.assertTrue(
            fm.group.permissions.filter(codename='billing.manage').exists(),
            "Finance Manager should have billing.manage"
        )
        self.assertFalse(
            fm.group.permissions.filter(codename='practice.manage').exists(),
            "Finance Manager should NOT have practice.manage"
        )

    def test_practice_manager_has_practice_not_accounting(self):
        """Practice Manager has practice manage but not accounting manage."""
        pm = Role.objects.get(slug='practice-manager')
        self.assertTrue(
            pm.group.permissions.filter(codename='practice.manage').exists(),
            "Practice Manager should have practice.manage"
        )
        self.assertFalse(
            pm.group.permissions.filter(codename='accounting.manage').exists(),
            "Practice Manager should NOT have accounting.manage"
        )

    def test_veterinarian_has_pharmacy_manage(self):
        """Veterinarian has pharmacy manage permission."""
        vet = Role.objects.get(slug='veterinarian')
        self.assertTrue(
            vet.group.permissions.filter(codename='pharmacy.manage').exists(),
            "Veterinarian should have pharmacy.manage"
        )

    def test_pet_owner_has_minimal_permissions(self):
        """Pet Owner has only appointments and billing view."""
        pet_owner = Role.objects.get(slug='pet-owner')
        self.assertTrue(
            pet_owner.group.permissions.filter(codename='appointments.view').exists(),
            "Pet Owner should have appointments.view"
        )
        self.assertTrue(
            pet_owner.group.permissions.filter(codename='billing.view').exists(),
            "Pet Owner should have billing.view"
        )
        self.assertFalse(
            pet_owner.group.permissions.filter(codename='practice.view').exists(),
            "Pet Owner should NOT have practice.view"
        )


class PermissionMatrixUITests(TestCase):
    """T-096b: Test permission matrix UI for role management."""

    def setUp(self):
        """Create superuser and test role for permission matrix tests."""
        self.superuser = User.objects.create_superuser(
            username='matrixadmin',
            email='matrixadmin@test.com',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='matrixadmin', password='testpass123')

        # Get an existing role to test with
        self.test_role = Role.objects.get(slug='receptionist')

    def test_permission_matrix_loads(self):
        """Permission matrix page loads for superuser."""
        response = self.client.get(
            reverse('superadmin:role_permissions', kwargs={'pk': self.test_role.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'practice')
        self.assertContains(response, 'accounting')

    def test_permission_matrix_shows_role_name(self):
        """Permission matrix shows the role being edited."""
        response = self.client.get(
            reverse('superadmin:role_permissions', kwargs={'pk': self.test_role.pk})
        )
        self.assertContains(response, self.test_role.name)

    def test_permission_matrix_shows_current_state(self):
        """Matrix shows which permissions role currently has."""
        # Receptionist should have practice.view
        response = self.client.get(
            reverse('superadmin:role_permissions', kwargs={'pk': self.test_role.pk})
        )
        # Should contain checked checkbox for practice.view
        self.assertContains(response, 'practice.view')

    def test_permission_matrix_saves_new_permissions(self):
        """Saving permission matrix updates role's group permissions."""
        # Initially receptionist doesn't have accounting.view
        self.assertFalse(
            self.test_role.group.permissions.filter(codename='accounting.view').exists()
        )

        # POST to add accounting.view
        current_perms = list(
            self.test_role.group.permissions.values_list('codename', flat=True)
        )
        current_perms.append('accounting.view')

        response = self.client.post(
            reverse('superadmin:role_permissions', kwargs={'pk': self.test_role.pk}),
            {'permissions': current_perms}
        )
        self.assertEqual(response.status_code, 302)  # Redirect on success

        # Refresh and verify
        self.test_role.refresh_from_db()
        self.assertTrue(
            self.test_role.group.permissions.filter(codename='accounting.view').exists()
        )

    def test_permission_matrix_removes_permissions(self):
        """Saving without a permission removes it from role."""
        # Get current permissions, remove practice.view
        current_perms = list(
            self.test_role.group.permissions.values_list('codename', flat=True)
        )
        current_perms = [p for p in current_perms if p != 'practice.view']

        response = self.client.post(
            reverse('superadmin:role_permissions', kwargs={'pk': self.test_role.pk}),
            {'permissions': current_perms}
        )
        self.assertEqual(response.status_code, 302)

        # Refresh and verify practice.view is removed
        self.test_role.refresh_from_db()
        self.assertFalse(
            self.test_role.group.permissions.filter(codename='practice.view').exists()
        )

    def test_permission_matrix_requires_superuser(self):
        """Non-superuser cannot access permission matrix."""
        # Create non-superuser
        regular_user = User.objects.create_user(
            username='regularuser',
            email='regular@test.com',
            password='testpass123'
        )
        client = Client()
        client.login(username='regularuser', password='testpass123')

        response = client.get(
            reverse('superadmin:role_permissions', kwargs={'pk': self.test_role.pk})
        )
        self.assertIn(response.status_code, [403, 302])


class DefaultRolesIntegrationTests(TestCase):
    """Test default roles from migration work correctly."""

    def test_default_roles_have_correct_hierarchy(self):
        """Default roles have correct hierarchy ordering."""
        pet_owner = Role.objects.get(slug='pet-owner')
        receptionist = Role.objects.get(slug='receptionist')
        vet_tech = Role.objects.get(slug='vet-tech')
        veterinarian = Role.objects.get(slug='veterinarian')
        practice_manager = Role.objects.get(slug='practice-manager')
        administrator = Role.objects.get(slug='administrator')

        # Verify hierarchy ordering
        self.assertLess(pet_owner.hierarchy_level, receptionist.hierarchy_level)
        self.assertLess(receptionist.hierarchy_level, vet_tech.hierarchy_level)
        self.assertLess(vet_tech.hierarchy_level, veterinarian.hierarchy_level)
        self.assertLess(veterinarian.hierarchy_level, practice_manager.hierarchy_level)
        self.assertLess(practice_manager.hierarchy_level, administrator.hierarchy_level)

    def test_default_roles_have_linked_groups(self):
        """Each default role has a linked Django Group."""
        default_slugs = [
            'pet-owner', 'receptionist', 'vet-tech', 'veterinarian',
            'practice-manager', 'finance-manager', 'administrator'
        ]

        for slug in default_slugs:
            role = Role.objects.get(slug=slug)
            self.assertIsNotNone(role.group, f"Role {slug} should have a linked group")
            self.assertEqual(role.group.name, role.name)
