"""Tests for ExamRoom model."""
import pytest
from django.db import IntegrityError

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
def second_location(organization):
    """Create a second test location."""
    return Location.objects.create(
        organization=organization,
        name='North Branch',
        code='NORTH',
    )


class TestExamRoomModel:
    """Tests for ExamRoom model."""

    def test_create_exam_room(self, location):
        """Can create an exam room for a location."""
        room = ExamRoom.objects.create(
            location=location,
            name='Room 1',
            room_type='exam',
        )
        assert room.pk is not None
        assert room.name == 'Room 1'
        assert room.location == location
        assert room.room_type == 'exam'
        assert room.is_active is True
        assert room.display_order == 0

    def test_exam_room_str(self, location):
        """ExamRoom __str__ returns name."""
        room = ExamRoom.objects.create(
            location=location,
            name='Surgery Suite',
            room_type='surgery',
        )
        assert str(room) == 'Surgery Suite'

    def test_exam_room_types(self, location):
        """Can create rooms of different types."""
        types = ['exam', 'surgery', 'imaging', 'treatment', 'isolation']
        for i, room_type in enumerate(types):
            room = ExamRoom.objects.create(
                location=location,
                name=f'Room {i}',
                room_type=room_type,
            )
            assert room.room_type == room_type

    def test_exam_room_unique_name_per_location(self, location):
        """Room names must be unique within a location."""
        ExamRoom.objects.create(
            location=location,
            name='Room 1',
        )
        with pytest.raises(IntegrityError):
            ExamRoom.objects.create(
                location=location,
                name='Room 1',
            )

    def test_same_room_name_different_locations(self, location, second_location):
        """Same room name can exist at different locations."""
        room1 = ExamRoom.objects.create(
            location=location,
            name='Room 1',
        )
        room2 = ExamRoom.objects.create(
            location=second_location,
            name='Room 1',
        )
        assert room1.pk != room2.pk

    def test_exam_room_ordering(self, location):
        """Rooms are ordered by display_order then name."""
        room_c = ExamRoom.objects.create(location=location, name='C Room', display_order=2)
        room_a = ExamRoom.objects.create(location=location, name='A Room', display_order=1)
        room_b = ExamRoom.objects.create(location=location, name='B Room', display_order=1)

        rooms = list(ExamRoom.objects.filter(location=location))
        # Order: display_order asc, then name asc
        # room_a (1), room_b (1), room_c (2) - but room_a < room_b by name
        assert rooms[0] == room_a
        assert rooms[1] == room_b
        assert rooms[2] == room_c

    def test_soft_deactivate_room(self, location):
        """Rooms can be soft-deactivated by setting is_active=False."""
        room = ExamRoom.objects.create(
            location=location,
            name='Room 1',
        )
        assert room.is_active is True

        room.is_active = False
        room.save()
        room.refresh_from_db()

        assert room.is_active is False
        # Room still exists
        assert ExamRoom.objects.filter(pk=room.pk).exists()

    def test_active_rooms_filter(self, location):
        """Can filter to only active rooms."""
        room1 = ExamRoom.objects.create(location=location, name='Room 1', is_active=True)
        room2 = ExamRoom.objects.create(location=location, name='Room 2', is_active=False)
        room3 = ExamRoom.objects.create(location=location, name='Room 3', is_active=True)

        active_rooms = ExamRoom.objects.filter(location=location, is_active=True)
        assert list(active_rooms) == [room1, room3]

    def test_location_exam_rooms_related_name(self, location):
        """Location has exam_rooms related manager."""
        ExamRoom.objects.create(location=location, name='Room 1')
        ExamRoom.objects.create(location=location, name='Room 2')

        assert location.exam_rooms.count() == 2

    def test_delete_location_cascades_rooms(self, organization):
        """Deleting a location cascades to delete its rooms."""
        loc = Location.objects.create(
            organization=organization,
            name='Temp Clinic',
            code='TEMP',
        )
        room = ExamRoom.objects.create(location=loc, name='Room 1')
        room_pk = room.pk

        loc.delete()

        assert not ExamRoom.objects.filter(pk=room_pk).exists()
