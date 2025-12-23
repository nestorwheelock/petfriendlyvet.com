"""
Tests for Appointment Reminder System (S-004)

Tests cover:
- Reminder identification (upcoming appointments)
- Email reminder sending
- Reminder task scheduling
"""
import pytest
from datetime import date, time, timedelta, datetime
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core import mail

User = get_user_model()


# =============================================================================
# Reminder Service Tests
# =============================================================================

@pytest.mark.django_db
class TestReminderService:
    """Tests for the appointment reminder service."""

    @pytest.fixture
    def owner(self):
        return User.objects.create_user(
            username='petowner',
            email='owner@test.com',
            password='pass123',
            role='owner'
        )

    @pytest.fixture
    def vet(self):
        return User.objects.create_user(
            username='drpablo',
            email='pablo@test.com',
            password='pass123',
            role='vet'
        )

    @pytest.fixture
    def pet(self, owner):
        from apps.pets.models import Pet
        return Pet.objects.create(
            owner=owner,
            name='Luna',
            species='dog'
        )

    @pytest.fixture
    def service(self):
        from apps.appointments.models import ServiceType
        return ServiceType.objects.create(
            name='General Consultation',
            duration_minutes=30,
            price=Decimal('450.00')
        )

    def test_reminder_service_exists(self):
        """ReminderService should exist."""
        from apps.appointments.reminders import ReminderService
        assert ReminderService is not None

    def test_get_appointments_needing_reminder(
        self, owner, pet, vet, service
    ):
        """Should find appointments that need reminders."""
        from apps.appointments.models import Appointment
        from apps.appointments.reminders import ReminderService

        # Appointment tomorrow - needs reminder
        tomorrow = timezone.now() + timedelta(days=1)
        appt_needs_reminder = Appointment.objects.create(
            owner=owner,
            pet=pet,
            service=service,
            veterinarian=vet,
            scheduled_start=tomorrow,
            scheduled_end=tomorrow + timedelta(minutes=30),
            status='scheduled'
        )

        # Appointment in 5 days - doesn't need reminder yet
        future = timezone.now() + timedelta(days=5)
        Appointment.objects.create(
            owner=owner,
            pet=pet,
            service=service,
            veterinarian=vet,
            scheduled_start=future,
            scheduled_end=future + timedelta(minutes=30),
            status='scheduled'
        )

        appointments = ReminderService.get_appointments_needing_reminder(
            hours_before=48
        )

        assert len(appointments) == 1
        assert appointments[0].id == appt_needs_reminder.id

    def test_already_reminded_excluded(
        self, owner, pet, vet, service
    ):
        """Appointments with reminder_sent should be excluded."""
        from apps.appointments.models import Appointment
        from apps.appointments.reminders import ReminderService

        tomorrow = timezone.now() + timedelta(days=1)
        Appointment.objects.create(
            owner=owner,
            pet=pet,
            service=service,
            veterinarian=vet,
            scheduled_start=tomorrow,
            scheduled_end=tomorrow + timedelta(minutes=30),
            status='scheduled',
            reminder_sent=True
        )

        appointments = ReminderService.get_appointments_needing_reminder(
            hours_before=48
        )

        assert len(appointments) == 0

    def test_cancelled_excluded(
        self, owner, pet, vet, service
    ):
        """Cancelled appointments should be excluded."""
        from apps.appointments.models import Appointment
        from apps.appointments.reminders import ReminderService

        tomorrow = timezone.now() + timedelta(days=1)
        Appointment.objects.create(
            owner=owner,
            pet=pet,
            service=service,
            veterinarian=vet,
            scheduled_start=tomorrow,
            scheduled_end=tomorrow + timedelta(minutes=30),
            status='cancelled'
        )

        appointments = ReminderService.get_appointments_needing_reminder(
            hours_before=48
        )

        assert len(appointments) == 0


# =============================================================================
# Email Reminder Tests
# =============================================================================

@pytest.mark.django_db
class TestEmailReminders:
    """Tests for email reminder sending."""

    @pytest.fixture
    def owner(self):
        return User.objects.create_user(
            username='petowner',
            email='owner@test.com',
            password='pass123',
            role='owner'
        )

    @pytest.fixture
    def vet(self):
        return User.objects.create_user(
            username='drpablo',
            email='pablo@test.com',
            password='pass123',
            role='vet',
            first_name='Pablo',
            last_name='Rojo'
        )

    @pytest.fixture
    def pet(self, owner):
        from apps.pets.models import Pet
        return Pet.objects.create(
            owner=owner,
            name='Luna',
            species='dog'
        )

    @pytest.fixture
    def service(self):
        from apps.appointments.models import ServiceType
        return ServiceType.objects.create(
            name='General Consultation',
            duration_minutes=30,
            price=Decimal('450.00')
        )

    @pytest.fixture
    def appointment(self, owner, pet, vet, service):
        from apps.appointments.models import Appointment
        tomorrow = timezone.now() + timedelta(days=1)
        return Appointment.objects.create(
            owner=owner,
            pet=pet,
            service=service,
            veterinarian=vet,
            scheduled_start=tomorrow,
            scheduled_end=tomorrow + timedelta(minutes=30),
            status='scheduled'
        )

    def test_send_reminder_email(self, appointment):
        """Should send reminder email to owner."""
        from apps.appointments.reminders import ReminderService

        ReminderService.send_reminder_email(appointment)

        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        assert 'owner@test.com' in email.to
        assert 'reminder' in email.subject.lower() or 'appointment' in email.subject.lower()

    def test_reminder_email_contains_details(self, appointment):
        """Reminder email should contain appointment details."""
        from apps.appointments.reminders import ReminderService

        ReminderService.send_reminder_email(appointment)

        email = mail.outbox[0]
        body = email.body.lower()
        assert 'luna' in body  # Pet name
        assert 'consultation' in body  # Service name

    def test_send_reminder_marks_as_sent(self, appointment):
        """Sending reminder should mark appointment as reminded."""
        from apps.appointments.reminders import ReminderService

        ReminderService.send_reminder_email(appointment)

        appointment.refresh_from_db()
        assert appointment.reminder_sent is True

    def test_reminder_without_pet(self, owner, vet, service):
        """Reminder should work for appointments without pet."""
        from apps.appointments.models import Appointment, ServiceType
        from apps.appointments.reminders import ReminderService

        no_pet_service = ServiceType.objects.create(
            name='Phone Consultation',
            duration_minutes=15,
            price=Decimal('200.00'),
            requires_pet=False
        )

        tomorrow = timezone.now() + timedelta(days=1)
        appt = Appointment.objects.create(
            owner=owner,
            pet=None,
            service=no_pet_service,
            veterinarian=vet,
            scheduled_start=tomorrow,
            scheduled_end=tomorrow + timedelta(minutes=15),
            status='scheduled'
        )

        ReminderService.send_reminder_email(appt)

        assert len(mail.outbox) == 1


# =============================================================================
# Celery Task Tests
# =============================================================================

@pytest.mark.django_db
class TestReminderTask:
    """Tests for the Celery reminder task."""

    @pytest.fixture
    def owner(self):
        return User.objects.create_user(
            username='petowner',
            email='owner@test.com',
            password='pass123'
        )

    @pytest.fixture
    def vet(self):
        return User.objects.create_user(
            username='drpablo',
            email='pablo@test.com',
            password='pass123',
            role='vet'
        )

    @pytest.fixture
    def pet(self, owner):
        from apps.pets.models import Pet
        return Pet.objects.create(
            owner=owner,
            name='Luna',
            species='dog'
        )

    @pytest.fixture
    def service(self):
        from apps.appointments.models import ServiceType
        return ServiceType.objects.create(
            name='Consultation',
            duration_minutes=30,
            price=Decimal('450.00')
        )

    def test_reminder_task_exists(self):
        """send_appointment_reminders task should exist."""
        from apps.appointments.tasks import send_appointment_reminders
        assert send_appointment_reminders is not None

    def test_reminder_task_sends_reminders(
        self, owner, pet, vet, service
    ):
        """Task should send reminders for upcoming appointments."""
        from apps.appointments.models import Appointment
        from apps.appointments.tasks import send_appointment_reminders

        tomorrow = timezone.now() + timedelta(days=1)
        Appointment.objects.create(
            owner=owner,
            pet=pet,
            service=service,
            veterinarian=vet,
            scheduled_start=tomorrow,
            scheduled_end=tomorrow + timedelta(minutes=30),
            status='scheduled'
        )

        result = send_appointment_reminders()

        assert result['sent'] == 1
        assert len(mail.outbox) == 1

    def test_reminder_task_returns_count(
        self, owner, pet, vet, service
    ):
        """Task should return count of reminders sent."""
        from apps.appointments.models import Appointment
        from apps.appointments.tasks import send_appointment_reminders

        # Use 12 hours ahead to be safely within 24-hour window
        upcoming = timezone.now() + timedelta(hours=12)
        for i in range(3):
            user = User.objects.create_user(
                username=f'owner{i}',
                email=f'owner{i}@test.com',
                password='pass'
            )
            Appointment.objects.create(
                owner=user,
                pet=None,
                service=service,
                veterinarian=vet,
                scheduled_start=upcoming + timedelta(hours=i),
                scheduled_end=upcoming + timedelta(hours=i, minutes=30),
                status='scheduled'
            )

        result = send_appointment_reminders()

        assert result['sent'] == 3

    def test_reminder_task_handles_errors(
        self, owner, pet, vet, service
    ):
        """Task should continue even if one email fails."""
        from apps.appointments.models import Appointment
        from apps.appointments.tasks import send_appointment_reminders

        # Use 12 hours ahead to be safely within 24-hour window
        upcoming = timezone.now() + timedelta(hours=12)

        # Owner with no email
        owner_no_email = User.objects.create_user(
            username='noemail',
            email='',
            password='pass'
        )
        Appointment.objects.create(
            owner=owner_no_email,
            pet=None,
            service=service,
            veterinarian=vet,
            scheduled_start=upcoming,
            scheduled_end=upcoming + timedelta(minutes=30),
            status='scheduled'
        )

        # Normal owner
        Appointment.objects.create(
            owner=owner,
            pet=pet,
            service=service,
            veterinarian=vet,
            scheduled_start=upcoming + timedelta(hours=1),
            scheduled_end=upcoming + timedelta(hours=1, minutes=30),
            status='scheduled'
        )

        result = send_appointment_reminders()

        # Should still send to valid email
        assert result['sent'] >= 1
