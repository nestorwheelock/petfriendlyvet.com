"""Tests for HR module - Practice integration and task time tracking."""
from datetime import date, time, timedelta
from decimal import Decimal

from django.test import TestCase, Client
from django.utils import timezone
from django.contrib.auth.models import Group, Permission as DjangoPermission
from django.contrib.contenttypes.models import ContentType

from apps.accounts.models import User, Role, UserRole
from apps.hr.models import Department, Position, Employee, TimeEntry, Shift
from apps.practice.models import StaffProfile, Task


def grant_hr_permission(user):
    """Grant hr.view permission to a user via the RBAC system."""
    group, _ = Group.objects.get_or_create(name='HR Test Staff')

    role, created = Role.objects.get_or_create(
        slug='hr-test-staff',
        defaults={
            'name': 'HR Test Staff',
            'hierarchy_level': 30,
            'group': group
        }
    )
    if not created:
        role.group = group
        role.save()

    content_type = ContentType.objects.get_for_model(User)
    hr_view_perm, _ = DjangoPermission.objects.get_or_create(
        codename='hr.view',
        defaults={'name': 'Can view HR', 'content_type': content_type}
    )
    hr_manage_perm, _ = DjangoPermission.objects.get_or_create(
        codename='hr.manage',
        defaults={'name': 'Can manage HR', 'content_type': content_type}
    )
    group.permissions.add(hr_view_perm, hr_manage_perm)

    UserRole.objects.get_or_create(user=user, role=role, defaults={'is_primary': True})


class StaffProfileEmployeeLinkTests(TestCase):
    """Test linking StaffProfile to HR Employee."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='staffuser',
            email='staff@test.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )

    def test_staffprofile_has_employee_field(self):
        """StaffProfile should have an optional employee ForeignKey."""
        staff = StaffProfile.objects.create(
            user=self.user,
            role='veterinarian'
        )
        # Should have employee field (nullable)
        self.assertTrue(hasattr(staff, 'employee'))
        self.assertIsNone(staff.employee)

    def test_staffprofile_can_link_to_employee(self):
        """StaffProfile can be linked to an Employee record."""
        employee = Employee.objects.create(
            user=self.user,
            employee_id='EMP001',
            hire_date=date.today()
        )
        staff = StaffProfile.objects.create(
            user=self.user,
            role='veterinarian',
            employee=employee
        )
        self.assertEqual(staff.employee, employee)
        self.assertEqual(staff.employee.employee_id, 'EMP001')

    def test_employee_can_access_staffprofile(self):
        """Employee record can reverse-access StaffProfile."""
        employee = Employee.objects.create(
            user=self.user,
            employee_id='EMP001',
            hire_date=date.today()
        )
        staff = StaffProfile.objects.create(
            user=self.user,
            role='veterinarian',
            employee=employee
        )
        # Reverse relation from Employee to StaffProfile
        self.assertEqual(employee.staff_profiles.first(), staff)


class TimeEntryTaskLinkTests(TestCase):
    """Test linking TimeEntry to Practice Task."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='empuser',
            email='emp@test.com',
            password='testpass123',
            first_name='Jane',
            last_name='Smith'
        )
        self.employee = Employee.objects.create(
            user=self.user,
            employee_id='EMP002',
            hire_date=date.today()
        )
        # Create a staff profile for task assignment
        self.staff = StaffProfile.objects.create(
            user=self.user,
            role='veterinarian'
        )

    def test_timeentry_has_task_field(self):
        """TimeEntry should have an optional task ForeignKey."""
        now = timezone.now()
        entry = TimeEntry.objects.create(
            employee=self.employee,
            date=now.date(),
            clock_in=now
        )
        self.assertTrue(hasattr(entry, 'task'))
        self.assertIsNone(entry.task)

    def test_timeentry_can_link_to_task(self):
        """TimeEntry can be linked to a Task."""
        task = Task.objects.create(
            title='Test Task',
            assigned_to=self.staff,
            priority='medium',
            status='pending'
        )
        now = timezone.now()
        entry = TimeEntry.objects.create(
            employee=self.employee,
            date=now.date(),
            clock_in=now,
            task=task
        )
        self.assertEqual(entry.task, task)
        self.assertEqual(entry.task.title, 'Test Task')

    def test_task_can_access_time_entries(self):
        """Task can reverse-access its TimeEntries."""
        task = Task.objects.create(
            title='Test Task',
            assigned_to=self.staff,
            priority='medium',
            status='pending'
        )
        now = timezone.now()
        entry1 = TimeEntry.objects.create(
            employee=self.employee,
            date=now.date(),
            clock_in=now,
            clock_out=now + timedelta(hours=2),
            task=task
        )
        entry2 = TimeEntry.objects.create(
            employee=self.employee,
            date=(now + timedelta(days=1)).date(),
            clock_in=now + timedelta(days=1),
            clock_out=now + timedelta(days=1, hours=3),
            task=task
        )
        # Reverse relation from Task to TimeEntries
        self.assertEqual(task.time_entries.count(), 2)
        self.assertIn(entry1, task.time_entries.all())
        self.assertIn(entry2, task.time_entries.all())

    def test_task_total_hours(self):
        """Task can calculate total hours from TimeEntries."""
        task = Task.objects.create(
            title='Test Task',
            assigned_to=self.staff,
            priority='medium',
            status='pending'
        )
        now = timezone.now()
        TimeEntry.objects.create(
            employee=self.employee,
            date=now.date(),
            clock_in=now,
            clock_out=now + timedelta(hours=2),
            task=task
        )
        TimeEntry.objects.create(
            employee=self.employee,
            date=(now + timedelta(days=1)).date(),
            clock_in=now + timedelta(days=1),
            clock_out=now + timedelta(days=1, hours=3),
            task=task
        )
        # Total should be 5 hours
        total = sum(e.hours_worked for e in task.time_entries.filter(clock_out__isnull=False))
        self.assertEqual(total, Decimal('5.00'))


class TaskClockInOutViewTests(TestCase):
    """Test clock in/out from task detail page."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='empuser2',
            email='emp2@test.com',
            password='testpass123',
            first_name='Jane',
            last_name='Smith'
        )
        self.employee = Employee.objects.create(
            user=self.user,
            employee_id='EMP003',
            hire_date=date.today()
        )
        self.staff = StaffProfile.objects.create(
            user=self.user,
            role='veterinarian'
        )
        self.task = Task.objects.create(
            title='Test Task',
            assigned_to=self.staff,
            priority='medium',
            status='pending'
        )
        grant_hr_permission(self.user)
        self.client.login(username='empuser2', password='testpass123')

    def test_clock_in_for_task(self):
        """User can clock in for a specific task."""
        response = self.client.post(
            f'/operations/hr/time/clock-in/',
            {'task_id': self.task.pk}
        )
        self.assertEqual(response.status_code, 302)
        # Should create a time entry linked to the task
        entry = TimeEntry.objects.filter(employee=self.employee, task=self.task).first()
        self.assertIsNotNone(entry)
        self.assertEqual(entry.task, self.task)
        self.assertIsNone(entry.clock_out)

    def test_clock_out_for_task(self):
        """User can clock out from a task."""
        # First clock in
        now = timezone.now()
        entry = TimeEntry.objects.create(
            employee=self.employee,
            date=now.date(),
            clock_in=now,
            task=self.task
        )
        response = self.client.post('/operations/hr/time/clock-out/')
        self.assertEqual(response.status_code, 302)
        entry.refresh_from_db()
        self.assertIsNotNone(entry.clock_out)


class TimesheetTaskFilterTests(TestCase):
    """Test filtering timesheet by task."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='empuser3',
            email='emp3@test.com',
            password='testpass123',
            first_name='Jane',
            last_name='Smith'
        )
        self.employee = Employee.objects.create(
            user=self.user,
            employee_id='EMP004',
            hire_date=date.today()
        )
        self.staff = StaffProfile.objects.create(
            user=self.user,
            role='veterinarian'
        )
        grant_hr_permission(self.user)
        self.client.login(username='empuser3', password='testpass123')

    def test_timesheet_shows_task_column(self):
        """Timesheet view should show task column."""
        response = self.client.get('/operations/hr/time/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Task')

    def test_timesheet_filter_by_task(self):
        """Timesheet can be filtered by task."""
        task1 = Task.objects.create(
            title='Task 1',
            assigned_to=self.staff,
            priority='medium',
            status='pending'
        )
        task2 = Task.objects.create(
            title='Task 2',
            assigned_to=self.staff,
            priority='high',
            status='pending'
        )
        now = timezone.now()
        TimeEntry.objects.create(
            employee=self.employee,
            date=now.date(),
            clock_in=now,
            clock_out=now + timedelta(hours=2),
            task=task1
        )
        TimeEntry.objects.create(
            employee=self.employee,
            date=now.date(),
            clock_in=now + timedelta(hours=3),
            clock_out=now + timedelta(hours=5),
            task=task2
        )
        # Filter by task1
        response = self.client.get(f'/operations/hr/time/?task={task1.pk}')
        self.assertEqual(response.status_code, 200)
        # Should show task1 entry but not task2
        entries = response.context.get('entries', [])
        self.assertEqual(len([e for e in entries if e.task == task1]), 1)
