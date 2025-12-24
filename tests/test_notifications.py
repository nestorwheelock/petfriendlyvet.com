"""
Tests for Notifications System (S-012)

Tests cover:
- Notification model and preferences
- Vaccination reminders
- Notification delivery (email)
- User notification views
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core import mail

User = get_user_model()


# =============================================================================
# Notification Model Tests
# =============================================================================

@pytest.mark.django_db
class TestNotificationModel:
    """Tests for the Notification model."""

    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_create_notification(self, user):
        """Can create a notification."""
        from apps.notifications.models import Notification

        notification = Notification.objects.create(
            user=user,
            notification_type='appointment_reminder',
            title='Upcoming Appointment',
            message='Your appointment is tomorrow at 10:00 AM'
        )

        assert notification.pk is not None
        assert notification.user == user
        assert notification.is_read is False
        assert notification.created_at is not None

    def test_notification_str(self, user):
        """Notification string representation."""
        from apps.notifications.models import Notification

        notification = Notification.objects.create(
            user=user,
            notification_type='vaccination_reminder',
            title='Vaccination Due',
            message='Rabies vaccination is due'
        )

        assert 'Vaccination Due' in str(notification)

    def test_mark_as_read(self, user):
        """Can mark notification as read."""
        from apps.notifications.models import Notification

        notification = Notification.objects.create(
            user=user,
            notification_type='general',
            title='Test',
            message='Test message'
        )

        assert notification.is_read is False
        notification.mark_as_read()
        assert notification.is_read is True
        assert notification.read_at is not None

    def test_unread_notifications_manager(self, user):
        """Can filter unread notifications."""
        from apps.notifications.models import Notification

        # Create read and unread notifications
        Notification.objects.create(
            user=user,
            notification_type='general',
            title='Unread 1',
            message='Message'
        )
        Notification.objects.create(
            user=user,
            notification_type='general',
            title='Unread 2',
            message='Message'
        )
        read_notif = Notification.objects.create(
            user=user,
            notification_type='general',
            title='Read',
            message='Message'
        )
        read_notif.mark_as_read()

        unread = Notification.objects.filter(user=user, is_read=False)
        assert unread.count() == 2


# =============================================================================
# Notification Preferences Tests
# =============================================================================

@pytest.mark.django_db
class TestNotificationPreferences:
    """Tests for notification preferences."""

    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_create_preferences(self, user):
        """Can create notification preferences."""
        from apps.notifications.models import NotificationPreference

        prefs = NotificationPreference.objects.create(
            user=user,
            email_appointments=True,
            email_vaccinations=True,
            email_promotions=False
        )

        assert prefs.pk is not None
        assert prefs.email_appointments is True
        assert prefs.email_promotions is False

    def test_default_preferences(self, user):
        """Preferences have sensible defaults."""
        from apps.notifications.models import NotificationPreference

        prefs = NotificationPreference.objects.create(user=user)

        # Important notifications should default to True
        assert prefs.email_appointments is True
        assert prefs.email_vaccinations is True

    def test_get_or_create_for_user(self, user):
        """Get or create preferences for user."""
        from apps.notifications.models import NotificationPreference

        # First call creates
        prefs1, created1 = NotificationPreference.objects.get_or_create(user=user)
        assert created1 is True

        # Second call retrieves
        prefs2, created2 = NotificationPreference.objects.get_or_create(user=user)
        assert created2 is False
        assert prefs1.pk == prefs2.pk


# =============================================================================
# Vaccination Reminder Tests
# =============================================================================

@pytest.mark.django_db
class TestVaccinationReminders:
    """Tests for vaccination reminder service."""

    @pytest.fixture
    def owner(self):
        return User.objects.create_user(
            username='petowner',
            email='owner@example.com',
            password='testpass123',
            role='owner'
        )

    @pytest.fixture
    def pet(self, owner):
        from apps.pets.models import Pet
        return Pet.objects.create(
            owner=owner,
            name='Luna',
            species='dog',
            date_of_birth=date(2020, 5, 15)
        )

    def test_get_vaccinations_due_soon(self, owner, pet):
        """Find vaccinations due within specified days."""
        from apps.pets.models import Vaccination
        from apps.notifications.services import VaccinationReminderService

        # Vaccination due in 7 days
        Vaccination.objects.create(
            pet=pet,
            vaccine_name='Rabies',
            date_administered=date.today() - timedelta(days=358),
            next_due_date=date.today() + timedelta(days=7)
        )

        # Vaccination due in 60 days (outside window)
        Vaccination.objects.create(
            pet=pet,
            vaccine_name='Distemper',
            date_administered=date.today() - timedelta(days=300),
            next_due_date=date.today() + timedelta(days=60)
        )

        due_soon = VaccinationReminderService.get_vaccinations_due_soon(days_ahead=30)
        assert len(due_soon) == 1
        assert due_soon[0].vaccine_name == 'Rabies'

    def test_get_overdue_vaccinations(self, owner, pet):
        """Find overdue vaccinations."""
        from apps.pets.models import Vaccination
        from apps.notifications.services import VaccinationReminderService

        # Overdue vaccination
        Vaccination.objects.create(
            pet=pet,
            vaccine_name='Rabies',
            date_administered=date.today() - timedelta(days=400),
            next_due_date=date.today() - timedelta(days=35)
        )

        overdue = VaccinationReminderService.get_overdue_vaccinations()
        assert len(overdue) == 1
        assert overdue[0].vaccine_name == 'Rabies'

    def test_send_vaccination_reminder_email(self, owner, pet):
        """Send vaccination reminder email."""
        from apps.pets.models import Vaccination
        from apps.notifications.services import VaccinationReminderService

        vaccination = Vaccination.objects.create(
            pet=pet,
            vaccine_name='Rabies',
            date_administered=date.today() - timedelta(days=358),
            next_due_date=date.today() + timedelta(days=7)
        )

        result = VaccinationReminderService.send_reminder_email(vaccination)

        assert result is True
        assert len(mail.outbox) == 1
        assert 'Rabies' in mail.outbox[0].subject
        assert 'Luna' in mail.outbox[0].body

    def test_skip_reminder_if_no_email(self, pet):
        """Skip reminder if owner has no email."""
        from apps.pets.models import Vaccination
        from apps.notifications.services import VaccinationReminderService

        # Owner without email
        pet.owner.email = ''
        pet.owner.save()

        vaccination = Vaccination.objects.create(
            pet=pet,
            vaccine_name='Rabies',
            date_administered=date.today() - timedelta(days=358),
            next_due_date=date.today() + timedelta(days=7)
        )

        result = VaccinationReminderService.send_reminder_email(vaccination)
        assert result is False
        assert len(mail.outbox) == 0


# =============================================================================
# Notification Service Tests
# =============================================================================

@pytest.mark.django_db
class TestNotificationService:
    """Tests for general notification service."""

    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_create_notification(self, user):
        """Create in-app notification."""
        from apps.notifications.services import NotificationService
        from apps.notifications.models import Notification

        notification = NotificationService.create_notification(
            user=user,
            notification_type='general',
            title='Welcome!',
            message='Welcome to Pet Friendly Vet'
        )

        assert notification.pk is not None
        assert Notification.objects.filter(user=user).count() == 1

    def test_create_and_send_email(self, user):
        """Create notification and send email."""
        from apps.notifications.services import NotificationService

        notification = NotificationService.create_notification(
            user=user,
            notification_type='appointment_reminder',
            title='Appointment Tomorrow',
            message='Your appointment is tomorrow at 10:00 AM',
            send_email=True
        )

        assert notification.pk is not None
        assert len(mail.outbox) == 1
        assert 'Appointment Tomorrow' in mail.outbox[0].subject

    def test_respect_email_preferences(self, user):
        """Respect user email preferences."""
        from apps.notifications.services import NotificationService
        from apps.notifications.models import NotificationPreference

        # Disable email for appointments
        NotificationPreference.objects.create(
            user=user,
            email_appointments=False
        )

        NotificationService.create_notification(
            user=user,
            notification_type='appointment_reminder',
            title='Appointment Tomorrow',
            message='Your appointment is tomorrow',
            send_email=True
        )

        # Email should not be sent due to preference
        assert len(mail.outbox) == 0

    def test_get_user_notifications(self, user):
        """Get notifications for a user."""
        from apps.notifications.services import NotificationService
        from apps.notifications.models import Notification

        Notification.objects.create(
            user=user,
            notification_type='general',
            title='Notification 1',
            message='Message 1'
        )
        Notification.objects.create(
            user=user,
            notification_type='general',
            title='Notification 2',
            message='Message 2'
        )

        notifications = NotificationService.get_user_notifications(user)
        assert len(notifications) == 2

    def test_get_user_notifications_unread_only(self, user):
        """Get only unread notifications for a user."""
        from apps.notifications.services import NotificationService
        from apps.notifications.models import Notification

        # Create read notification
        read_notif = Notification.objects.create(
            user=user,
            notification_type='general',
            title='Read Notification',
            message='Already read'
        )
        read_notif.mark_as_read()

        # Create unread notification
        Notification.objects.create(
            user=user,
            notification_type='general',
            title='Unread Notification',
            message='Not yet read'
        )

        # Should return only unread
        notifications = NotificationService.get_user_notifications(user, unread_only=True)
        assert len(notifications) == 1
        assert notifications[0].title == 'Unread Notification'

    def test_send_email_exception_handling(self, user, mocker):
        """Email send failure is handled gracefully."""
        from apps.notifications.services import NotificationService

        # Mock send_mail to raise exception
        mocker.patch('apps.notifications.services.send_mail', side_effect=Exception("SMTP error"))

        # Create notification and try to send email
        notification = NotificationService.create_notification(
            user=user,
            notification_type='general',
            title='Test Notification',
            message='This should fail to send',
            send_email=True
        )

        # Notification should be created but email not sent
        assert notification is not None
        assert notification.email_sent is False

    def test_mark_all_as_read(self, user):
        """Mark all user notifications as read."""
        from apps.notifications.services import NotificationService
        from apps.notifications.models import Notification

        Notification.objects.create(
            user=user,
            notification_type='general',
            title='Notification 1',
            message='Message 1'
        )
        Notification.objects.create(
            user=user,
            notification_type='general',
            title='Notification 2',
            message='Message 2'
        )

        count = NotificationService.mark_all_as_read(user)
        assert count == 2
        assert Notification.objects.filter(user=user, is_read=False).count() == 0


# =============================================================================
# Notification Views Tests
# =============================================================================

@pytest.mark.django_db
class TestNotificationViews:
    """Tests for notification views."""

    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_notification_list_requires_login(self, client):
        """Notification list requires authentication."""
        url = reverse('notifications:list')
        response = client.get(url)
        assert response.status_code == 302

    def test_notification_list_shows_notifications(self, client, user):
        """Shows user's notifications."""
        from apps.notifications.models import Notification

        Notification.objects.create(
            user=user,
            notification_type='general',
            title='Test Notification',
            message='Test message'
        )

        client.force_login(user)
        url = reverse('notifications:list')
        response = client.get(url)

        assert response.status_code == 200
        assert b'Test Notification' in response.content

    def test_mark_notification_read(self, client, user):
        """Can mark single notification as read."""
        from apps.notifications.models import Notification

        notification = Notification.objects.create(
            user=user,
            notification_type='general',
            title='Test',
            message='Test'
        )

        client.force_login(user)
        url = reverse('notifications:mark_read', kwargs={'pk': notification.pk})
        response = client.post(url)

        notification.refresh_from_db()
        assert notification.is_read is True

    def test_mark_all_read(self, client, user):
        """Can mark all notifications as read."""
        from apps.notifications.models import Notification

        Notification.objects.create(
            user=user,
            notification_type='general',
            title='Test 1',
            message='Test'
        )
        Notification.objects.create(
            user=user,
            notification_type='general',
            title='Test 2',
            message='Test'
        )

        client.force_login(user)
        url = reverse('notifications:mark_all_read')
        response = client.post(url)

        assert Notification.objects.filter(user=user, is_read=False).count() == 0

    def test_unread_count_api(self, client, user):
        """API returns unread notification count."""
        from apps.notifications.models import Notification

        Notification.objects.create(
            user=user,
            notification_type='general',
            title='Test 1',
            message='Test'
        )
        Notification.objects.create(
            user=user,
            notification_type='general',
            title='Test 2',
            message='Test'
        )

        client.force_login(user)
        url = reverse('notifications:unread_count')
        response = client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data['count'] == 2

    def test_cannot_mark_other_user_notification(self, client, user):
        """Cannot mark another user's notification as read."""
        from apps.notifications.models import Notification

        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass'
        )
        notification = Notification.objects.create(
            user=other_user,
            notification_type='general',
            title='Other user notification',
            message='Test'
        )

        client.force_login(user)
        url = reverse('notifications:mark_read', kwargs={'pk': notification.pk})
        response = client.post(url)

        assert response.status_code == 404

    def test_mark_notification_read_ajax(self, client, user):
        """Mark notification read via AJAX returns JSON."""
        from apps.notifications.models import Notification

        notification = Notification.objects.create(
            user=user,
            notification_type='general',
            title='Test',
            message='Test notification'
        )

        client.force_login(user)
        url = reverse('notifications:mark_read', kwargs={'pk': notification.pk})
        response = client.post(
            url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        assert response.status_code == 200
        assert response.json()['success'] is True
        notification.refresh_from_db()
        assert notification.is_read is True

    def test_mark_all_read_ajax(self, client, user):
        """Mark all notifications read via AJAX returns JSON."""
        from apps.notifications.models import Notification

        Notification.objects.create(
            user=user,
            notification_type='general',
            title='Test 1',
            message='Test'
        )
        Notification.objects.create(
            user=user,
            notification_type='general',
            title='Test 2',
            message='Test'
        )

        client.force_login(user)
        url = reverse('notifications:mark_all_read')
        response = client.post(
            url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['count'] == 2
        assert Notification.objects.filter(user=user, is_read=False).count() == 0


# =============================================================================
# Celery Task Tests
# =============================================================================

@pytest.mark.django_db
class TestNotificationTasks:
    """Tests for notification Celery tasks."""

    @pytest.fixture
    def owner(self):
        return User.objects.create_user(
            username='petowner',
            email='owner@example.com',
            password='testpass123',
            role='owner'
        )

    @pytest.fixture
    def pet(self, owner):
        from apps.pets.models import Pet
        return Pet.objects.create(
            owner=owner,
            name='Luna',
            species='dog',
            date_of_birth=date(2020, 5, 15)
        )

    def test_send_vaccination_reminders_task(self, owner, pet):
        """Celery task sends vaccination reminders."""
        from apps.pets.models import Vaccination
        from apps.notifications.tasks import send_vaccination_reminders

        # Vaccination due in 7 days
        Vaccination.objects.create(
            pet=pet,
            vaccine_name='Rabies',
            date_administered=date.today() - timedelta(days=358),
            next_due_date=date.today() + timedelta(days=7),
            reminder_sent=False
        )

        result = send_vaccination_reminders(days_ahead=30)

        assert result['sent'] >= 1
        assert len(mail.outbox) >= 1

    def test_skip_already_reminded_vaccinations(self, owner, pet):
        """Skip vaccinations that already had reminders sent."""
        from apps.pets.models import Vaccination
        from apps.notifications.tasks import send_vaccination_reminders

        Vaccination.objects.create(
            pet=pet,
            vaccine_name='Rabies',
            date_administered=date.today() - timedelta(days=358),
            next_due_date=date.today() + timedelta(days=7),
            reminder_sent=True  # Already reminded
        )

        result = send_vaccination_reminders(days_ahead=30)

        assert result['sent'] == 0
        assert len(mail.outbox) == 0

    def test_send_overdue_vaccination_alerts(self, owner, pet):
        """Test sending overdue vaccination alerts."""
        from apps.pets.models import Vaccination
        from apps.notifications.tasks import send_overdue_vaccination_alerts

        Vaccination.objects.create(
            pet=pet,
            vaccine_name='Rabies',
            date_administered=date.today() - timedelta(days=400),
            next_due_date=date.today() - timedelta(days=35),  # Overdue
            reminder_sent=False
        )

        result = send_overdue_vaccination_alerts()

        assert 'sent' in result
        assert 'errors' in result
        assert 'total_checked' in result

    def test_send_overdue_alerts_no_overdue(self, owner, pet):
        """No alerts when no vaccinations are overdue."""
        from apps.pets.models import Vaccination
        from apps.notifications.tasks import send_overdue_vaccination_alerts

        Vaccination.objects.create(
            pet=pet,
            vaccine_name='Rabies',
            date_administered=date.today() - timedelta(days=30),
            next_due_date=date.today() + timedelta(days=335),  # Not overdue
            reminder_sent=False
        )

        result = send_overdue_vaccination_alerts()

        assert result['total_checked'] == 0
        assert result['sent'] == 0

    def test_vaccination_reminder_error_handling(self, owner, pet, mocker):
        """Test error handling in vaccination reminder task."""
        from apps.pets.models import Vaccination
        from apps.notifications.tasks import send_vaccination_reminders
        from apps.notifications import services

        Vaccination.objects.create(
            pet=pet,
            vaccine_name='Rabies',
            date_administered=date.today() - timedelta(days=358),
            next_due_date=date.today() + timedelta(days=7),
            reminder_sent=False
        )

        mocker.patch.object(
            services.VaccinationReminderService,
            'send_reminder_email',
            side_effect=Exception("Email service down")
        )

        result = send_vaccination_reminders(days_ahead=30)

        assert result['errors'] >= 1

    def test_overdue_alert_error_handling(self, owner, pet, mocker):
        """Test error handling in overdue alert task."""
        from apps.pets.models import Vaccination
        from apps.notifications.tasks import send_overdue_vaccination_alerts
        from apps.notifications import services

        Vaccination.objects.create(
            pet=pet,
            vaccine_name='Rabies',
            date_administered=date.today() - timedelta(days=400),
            next_due_date=date.today() - timedelta(days=35),
            reminder_sent=False
        )

        mocker.patch.object(
            services.VaccinationReminderService,
            'send_reminder_email',
            side_effect=Exception("Email service down")
        )

        result = send_overdue_vaccination_alerts()

        assert result['errors'] >= 1
