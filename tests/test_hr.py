"""Tests for HR module (T-097).

TDD tests for:
- Department model and CRUD
- Position model and CRUD
- Employee model and CRUD
- Time tracking
"""
from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class DepartmentModelTests(TestCase):
    """Test Department model."""

    def test_department_creation(self):
        """Department can be created with name and code."""
        from apps.hr.models import Department
        dept = Department.objects.create(name='Veterinary', code='vet')
        self.assertEqual(dept.name, 'Veterinary')
        self.assertEqual(dept.code, 'vet')
        self.assertTrue(dept.is_active)

    def test_department_str(self):
        """Department string representation."""
        from apps.hr.models import Department
        dept = Department.objects.create(name='Clinical Services', code='clinical')
        self.assertEqual(str(dept), 'Clinical Services')

    def test_department_hierarchy(self):
        """Department can have parent for hierarchy."""
        from apps.hr.models import Department
        parent = Department.objects.create(name='Clinical', code='clinical')
        child = Department.objects.create(name='Surgery', code='surgery', parent=parent)
        self.assertEqual(child.parent, parent)
        self.assertIn(child, parent.children.all())

    def test_department_unique_code(self):
        """Department code must be unique."""
        from apps.hr.models import Department
        from django.db import IntegrityError
        Department.objects.create(name='Dept 1', code='dept1')
        with self.assertRaises(IntegrityError):
            Department.objects.create(name='Dept 2', code='dept1')


class PositionModelTests(TestCase):
    """Test Position model."""

    def test_position_creation(self):
        """Position can be created with title and code."""
        from apps.hr.models import Position
        pos = Position.objects.create(title='Veterinarian', code='vet')
        self.assertEqual(pos.title, 'Veterinarian')
        self.assertEqual(pos.code, 'vet')
        self.assertTrue(pos.is_active)

    def test_position_str(self):
        """Position string representation."""
        from apps.hr.models import Position
        pos = Position.objects.create(title='Senior Veterinarian', code='sr-vet')
        self.assertEqual(str(pos), 'Senior Veterinarian')

    def test_position_with_department(self):
        """Position can be linked to department."""
        from apps.hr.models import Department, Position
        dept = Department.objects.create(name='Clinical', code='clinical')
        pos = Position.objects.create(title='Surgeon', code='surgeon', department=dept)
        self.assertEqual(pos.department, dept)

    def test_position_salary_range(self):
        """Position can have salary range."""
        from apps.hr.models import Position
        pos = Position.objects.create(
            title='Manager',
            code='mgr',
            min_salary=Decimal('50000.00'),
            max_salary=Decimal('80000.00')
        )
        self.assertEqual(pos.min_salary, Decimal('50000.00'))
        self.assertEqual(pos.max_salary, Decimal('80000.00'))


class EmployeeModelTests(TestCase):
    """Test Employee model."""

    def test_employee_creation(self):
        """Employee can be created linked to user."""
        from apps.hr.models import Employee
        user = User.objects.create_user('emp1', 'emp1@test.com', 'pass')
        emp = Employee.objects.create(
            user=user,
            employee_id='EMP001',
            hire_date=date.today()
        )
        self.assertEqual(emp.employee_id, 'EMP001')
        self.assertEqual(emp.user, user)

    def test_employee_str(self):
        """Employee string representation shows name and ID."""
        from apps.hr.models import Employee
        user = User.objects.create_user('emp2', 'emp2@test.com', 'pass')
        user.first_name = 'John'
        user.last_name = 'Doe'
        user.save()
        emp = Employee.objects.create(user=user, employee_id='EMP002', hire_date=date.today())
        self.assertIn('EMP002', str(emp))

    def test_employee_with_department_and_position(self):
        """Employee can have department and position."""
        from apps.hr.models import Department, Position, Employee
        dept = Department.objects.create(name='Clinical', code='clinical')
        pos = Position.objects.create(title='Vet', code='vet', department=dept)
        user = User.objects.create_user('emp3', 'emp3@test.com', 'pass')
        emp = Employee.objects.create(
            user=user,
            employee_id='EMP003',
            hire_date=date.today(),
            department=dept,
            position=pos
        )
        self.assertEqual(emp.department, dept)
        self.assertEqual(emp.position, pos)

    def test_employee_manager_relationship(self):
        """Employee can have a manager (another employee)."""
        from apps.hr.models import Employee
        user1 = User.objects.create_user('mgr', 'mgr@test.com', 'pass')
        user2 = User.objects.create_user('emp', 'emp@test.com', 'pass')
        manager = Employee.objects.create(user=user1, employee_id='MGR001', hire_date=date.today())
        employee = Employee.objects.create(
            user=user2,
            employee_id='EMP004',
            hire_date=date.today(),
            manager=manager
        )
        self.assertEqual(employee.manager, manager)
        self.assertIn(employee, manager.direct_reports.all())

    def test_employee_unique_id(self):
        """Employee ID must be unique."""
        from apps.hr.models import Employee
        from django.db import IntegrityError
        user1 = User.objects.create_user('u1', 'u1@test.com', 'pass')
        user2 = User.objects.create_user('u2', 'u2@test.com', 'pass')
        Employee.objects.create(user=user1, employee_id='EMP999', hire_date=date.today())
        with self.assertRaises(IntegrityError):
            Employee.objects.create(user=user2, employee_id='EMP999', hire_date=date.today())


class DepartmentCRUDTests(TestCase):
    """Test Department CRUD views."""

    def setUp(self):
        """Set up test user with HR permissions."""
        self.user = User.objects.create_superuser('hradmin', 'hr@test.com', 'pass')
        self.client = Client()
        self.client.login(username='hradmin', password='pass')

    def test_department_list_view(self):
        """Department list view loads."""
        response = self.client.get(reverse('hr:department_list'))
        self.assertEqual(response.status_code, 200)

    def test_department_create_view_get(self):
        """Department create form loads."""
        response = self.client.get(reverse('hr:department_create'))
        self.assertEqual(response.status_code, 200)

    def test_department_create_view_post(self):
        """Department can be created via form."""
        from apps.hr.models import Department
        response = self.client.post(reverse('hr:department_create'), {
            'name': 'New Department',
            'code': 'new-dept',
            'description': 'Test department',
            'is_active': True,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Department.objects.filter(code='new-dept').exists())

    def test_department_update_view(self):
        """Department can be updated."""
        from apps.hr.models import Department
        dept = Department.objects.create(name='Old Name', code='old')
        response = self.client.post(reverse('hr:department_update', kwargs={'pk': dept.pk}), {
            'name': 'New Name',
            'code': 'old',
            'is_active': True,
        })
        self.assertEqual(response.status_code, 302)
        dept.refresh_from_db()
        self.assertEqual(dept.name, 'New Name')

    def test_department_delete_view(self):
        """Department can be deleted."""
        from apps.hr.models import Department
        dept = Department.objects.create(name='To Delete', code='del')
        response = self.client.post(reverse('hr:department_delete', kwargs={'pk': dept.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Department.objects.filter(pk=dept.pk).exists())


class PositionCRUDTests(TestCase):
    """Test Position CRUD views."""

    def setUp(self):
        """Set up test user with HR permissions."""
        self.user = User.objects.create_superuser('hradmin', 'hr@test.com', 'pass')
        self.client = Client()
        self.client.login(username='hradmin', password='pass')

    def test_position_list_view(self):
        """Position list view loads."""
        response = self.client.get(reverse('hr:position_list'))
        self.assertEqual(response.status_code, 200)

    def test_position_create_view_post(self):
        """Position can be created via form."""
        from apps.hr.models import Position
        response = self.client.post(reverse('hr:position_create'), {
            'title': 'New Position',
            'code': 'new-pos',
            'is_active': True,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Position.objects.filter(code='new-pos').exists())


class EmployeeCRUDTests(TestCase):
    """Test Employee CRUD views."""

    def setUp(self):
        """Set up test user with HR permissions."""
        self.admin = User.objects.create_superuser('hradmin', 'hr@test.com', 'pass')
        self.client = Client()
        self.client.login(username='hradmin', password='pass')

    def test_employee_list_view(self):
        """Employee list view loads."""
        response = self.client.get(reverse('hr:employee_list'))
        self.assertEqual(response.status_code, 200)

    def test_employee_create_view_get(self):
        """Employee create form loads."""
        response = self.client.get(reverse('hr:employee_create'))
        self.assertEqual(response.status_code, 200)

    def test_employee_detail_view(self):
        """Employee detail view shows employee info."""
        from apps.hr.models import Employee
        user = User.objects.create_user('testuser', 'test@test.com', 'pass')
        emp = Employee.objects.create(user=user, employee_id='TEST001', hire_date=date.today())
        response = self.client.get(reverse('hr:employee_detail', kwargs={'pk': emp.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TEST001')


class TimeEntryModelTests(TestCase):
    """Test TimeEntry model."""

    def setUp(self):
        """Create employee for time entries."""
        from apps.hr.models import Employee
        self.user = User.objects.create_user('timeuser', 'time@test.com', 'pass')
        self.employee = Employee.objects.create(
            user=self.user,
            employee_id='TIME001',
            hire_date=date.today()
        )

    def test_time_entry_creation(self):
        """Time entry can be created."""
        from apps.hr.models import TimeEntry
        from django.utils import timezone
        entry = TimeEntry.objects.create(
            employee=self.employee,
            date=date.today(),
            clock_in=timezone.now()
        )
        self.assertEqual(entry.employee, self.employee)
        self.assertIsNone(entry.clock_out)
        self.assertFalse(entry.is_approved)

    def test_time_entry_clock_out(self):
        """Time entry can be clocked out."""
        from apps.hr.models import TimeEntry
        from django.utils import timezone
        entry = TimeEntry.objects.create(
            employee=self.employee,
            date=date.today(),
            clock_in=timezone.now()
        )
        entry.clock_out = timezone.now()
        entry.save()
        self.assertIsNotNone(entry.clock_out)

    def test_time_entry_hours_worked(self):
        """Time entry calculates hours worked."""
        from apps.hr.models import TimeEntry
        from django.utils import timezone
        import datetime

        clock_in = timezone.now()
        clock_out = clock_in + datetime.timedelta(hours=8)

        entry = TimeEntry.objects.create(
            employee=self.employee,
            date=date.today(),
            clock_in=clock_in,
            clock_out=clock_out,
            break_minutes=30
        )
        # 8 hours minus 30 min break = 7.5 hours
        self.assertAlmostEqual(entry.hours_worked, 7.5, places=1)


class TimeTrackingViewTests(TestCase):
    """Test time tracking views."""

    def setUp(self):
        """Set up employee user."""
        from apps.hr.models import Employee
        self.user = User.objects.create_user('timeuser', 'time@test.com', 'pass')
        self.employee = Employee.objects.create(
            user=self.user,
            employee_id='TIME002',
            hire_date=date.today()
        )
        self.client = Client()
        self.client.login(username='timeuser', password='pass')

    def test_timesheet_view(self):
        """Timesheet view loads for employee."""
        response = self.client.get(reverse('hr:timesheet'))
        self.assertEqual(response.status_code, 200)

    def test_clock_in(self):
        """Employee can clock in."""
        from apps.hr.models import TimeEntry
        response = self.client.post(reverse('hr:clock_in'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            TimeEntry.objects.filter(
                employee=self.employee,
                clock_out__isnull=True
            ).exists()
        )

    def test_clock_out(self):
        """Employee can clock out."""
        from apps.hr.models import TimeEntry
        from django.utils import timezone
        # First clock in
        entry = TimeEntry.objects.create(
            employee=self.employee,
            date=date.today(),
            clock_in=timezone.now()
        )
        # Then clock out
        response = self.client.post(reverse('hr:clock_out'))
        self.assertEqual(response.status_code, 302)
        entry.refresh_from_db()
        self.assertIsNotNone(entry.clock_out)

    def test_cannot_clock_in_twice(self):
        """Cannot clock in when already clocked in."""
        from apps.hr.models import TimeEntry
        from django.utils import timezone
        # Already clocked in
        TimeEntry.objects.create(
            employee=self.employee,
            date=date.today(),
            clock_in=timezone.now()
        )
        # Try to clock in again
        response = self.client.post(reverse('hr:clock_in'))
        # Should redirect with error message
        self.assertEqual(response.status_code, 302)
        # Should still only have 1 entry
        self.assertEqual(
            TimeEntry.objects.filter(employee=self.employee, date=date.today()).count(),
            1
        )
