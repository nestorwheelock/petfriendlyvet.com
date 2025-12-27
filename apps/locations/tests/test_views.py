"""Tests for locations views - exam room management."""
import pytest
from django.urls import reverse

from apps.locations.models import ExamRoom, Location
from apps.parties.models import Organization


@pytest.fixture
def organization(db):
    """Create a test organization."""
    return Organization.objects.create(
        name='Test Vet Clinic',
        org_type='veterinary_clinic',
    )


@pytest.fixture
def location(organization):
    """Create a test location."""
    return Location.objects.create(
        organization=organization,
        name='Main Clinic',
        code='MAIN',
    )


@pytest.fixture
def exam_room(location):
    """Create a test exam room."""
    return ExamRoom.objects.create(
        location=location,
        name='Room 1',
        room_type='exam',
    )


@pytest.fixture
def staff_user(db, django_user_model):
    """Create a staff user with locations permissions."""
    return django_user_model.objects.create_user(
        username='staff',
        email='staff@test.com',
        password='testpass123',
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def regular_user(db, django_user_model):
    """Create a regular user without staff permissions."""
    return django_user_model.objects.create_user(
        username='regular',
        email='regular@test.com',
        password='testpass123',
    )


class TestLocationListView:
    """Tests for location list view."""

    def test_location_list_requires_login(self, client, location):
        """Location list requires authentication."""
        url = reverse('locations:location_list')
        response = client.get(url)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_location_list_requires_staff(self, client, regular_user, location):
        """Location list requires staff permissions."""
        client.force_login(regular_user)
        url = reverse('locations:location_list')
        response = client.get(url)
        assert response.status_code == 403

    def test_location_list_accessible_to_staff(self, client, staff_user, location):
        """Staff can access location list."""
        client.force_login(staff_user)
        url = reverse('locations:location_list')
        response = client.get(url)
        assert response.status_code == 200
        assert 'Main Clinic' in response.content.decode()


class TestExamRoomListView:
    """Tests for exam room list view."""

    def test_room_list_requires_login(self, client, location):
        """Room list requires authentication."""
        url = reverse('locations:room_list', kwargs={'location_id': location.id})
        response = client.get(url)
        assert response.status_code == 302

    def test_room_list_shows_rooms_for_location(self, client, staff_user, location, exam_room):
        """Room list shows rooms for the specified location."""
        client.force_login(staff_user)
        url = reverse('locations:room_list', kwargs={'location_id': location.id})
        response = client.get(url)
        assert response.status_code == 200
        assert 'Room 1' in response.content.decode()

    def test_room_list_shows_empty_state(self, client, staff_user, location):
        """Room list shows empty state when no rooms."""
        client.force_login(staff_user)
        url = reverse('locations:room_list', kwargs={'location_id': location.id})
        response = client.get(url)
        assert response.status_code == 200


class TestExamRoomCreateView:
    """Tests for exam room create view."""

    def test_room_create_requires_login(self, client, location):
        """Room create requires authentication."""
        url = reverse('locations:room_create', kwargs={'location_id': location.id})
        response = client.get(url)
        assert response.status_code == 302

    def test_room_create_get_shows_form(self, client, staff_user, location):
        """GET request shows room creation form."""
        client.force_login(staff_user)
        url = reverse('locations:room_create', kwargs={'location_id': location.id})
        response = client.get(url)
        assert response.status_code == 200
        assert 'form' in response.context

    def test_room_create_post_creates_room(self, client, staff_user, location):
        """POST request creates a new room."""
        client.force_login(staff_user)
        url = reverse('locations:room_create', kwargs={'location_id': location.id})
        response = client.post(url, {
            'name': 'New Room',
            'room_type': 'exam',
            'display_order': 0,
            'is_active': True,
        })
        assert response.status_code == 302
        assert ExamRoom.objects.filter(location=location, name='New Room').exists()

    def test_room_create_validates_unique_name(self, client, staff_user, location, exam_room):
        """Room create validates unique name per location."""
        client.force_login(staff_user)
        url = reverse('locations:room_create', kwargs={'location_id': location.id})
        response = client.post(url, {
            'name': 'Room 1',  # Already exists
            'room_type': 'exam',
            'display_order': 0,
            'is_active': True,
        })
        assert response.status_code == 200  # Form re-rendered with errors
        assert ExamRoom.objects.filter(location=location).count() == 1


class TestExamRoomEditView:
    """Tests for exam room edit view."""

    def test_room_edit_requires_login(self, client, location, exam_room):
        """Room edit requires authentication."""
        url = reverse('locations:room_edit', kwargs={
            'location_id': location.id,
            'room_id': exam_room.id,
        })
        response = client.get(url)
        assert response.status_code == 302

    def test_room_edit_get_shows_form(self, client, staff_user, location, exam_room):
        """GET request shows room edit form."""
        client.force_login(staff_user)
        url = reverse('locations:room_edit', kwargs={
            'location_id': location.id,
            'room_id': exam_room.id,
        })
        response = client.get(url)
        assert response.status_code == 200
        assert response.context['form'].instance == exam_room

    def test_room_edit_post_updates_room(self, client, staff_user, location, exam_room):
        """POST request updates the room."""
        client.force_login(staff_user)
        url = reverse('locations:room_edit', kwargs={
            'location_id': location.id,
            'room_id': exam_room.id,
        })
        response = client.post(url, {
            'name': 'Updated Room',
            'room_type': 'surgery',
            'display_order': 1,
            'is_active': True,
        })
        assert response.status_code == 302
        exam_room.refresh_from_db()
        assert exam_room.name == 'Updated Room'
        assert exam_room.room_type == 'surgery'


class TestExamRoomDeactivateView:
    """Tests for exam room deactivate view."""

    def test_room_deactivate_requires_login(self, client, location, exam_room):
        """Room deactivate requires authentication."""
        url = reverse('locations:room_deactivate', kwargs={
            'location_id': location.id,
            'room_id': exam_room.id,
        })
        response = client.post(url)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_room_deactivate_requires_post(self, client, staff_user, location, exam_room):
        """Room deactivate requires POST method."""
        client.force_login(staff_user)
        url = reverse('locations:room_deactivate', kwargs={
            'location_id': location.id,
            'room_id': exam_room.id,
        })
        response = client.get(url)
        assert response.status_code == 405  # Method not allowed

    def test_room_deactivate_sets_inactive(self, client, staff_user, location, exam_room):
        """POST request sets room to inactive."""
        client.force_login(staff_user)
        url = reverse('locations:room_deactivate', kwargs={
            'location_id': location.id,
            'room_id': exam_room.id,
        })
        response = client.post(url)
        assert response.status_code == 302
        exam_room.refresh_from_db()
        assert exam_room.is_active is False

    def test_room_deactivate_does_not_delete(self, client, staff_user, location, exam_room):
        """Room deactivate soft-deletes, doesn't hard delete."""
        client.force_login(staff_user)
        room_id = exam_room.id
        url = reverse('locations:room_deactivate', kwargs={
            'location_id': location.id,
            'room_id': exam_room.id,
        })
        client.post(url)
        # Room still exists
        assert ExamRoom.objects.filter(id=room_id).exists()


class TestExamRoomReactivateView:
    """Tests for exam room reactivate view."""

    def test_room_reactivate_sets_active(self, client, staff_user, location, exam_room):
        """POST request sets room to active."""
        exam_room.is_active = False
        exam_room.save()

        client.force_login(staff_user)
        url = reverse('locations:room_reactivate', kwargs={
            'location_id': location.id,
            'room_id': exam_room.id,
        })
        response = client.post(url)
        assert response.status_code == 302
        exam_room.refresh_from_db()
        assert exam_room.is_active is True
