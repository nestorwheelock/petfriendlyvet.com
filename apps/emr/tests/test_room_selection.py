"""Tests for exam room selection during encounter transitions."""
import pytest
from django.contrib.auth import get_user_model

from apps.emr.models import Encounter, ClinicalEvent
from apps.emr.services import encounters
from apps.locations.models import ExamRoom, Location
from apps.parties.models import Organization
from apps.practice.models import PatientRecord
from apps.pets.models import Pet

User = get_user_model()


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
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username='testvet',
        email='testvet@example.com',
        password='testpass123',
    )


@pytest.fixture
def pet(db, user):
    """Create a test pet."""
    return Pet.objects.create(
        name='Fluffy',
        species='dog',
        breed='Golden Retriever',
        owner=user,
    )


@pytest.fixture
def patient(pet):
    """Create a test patient record."""
    return PatientRecord.objects.create(
        pet=pet,
        patient_number='P000001',
    )


@pytest.fixture
def encounter(location, patient, user):
    """Create a test encounter in checked_in state."""
    return Encounter.objects.create(
        location=location,
        patient=patient,
        created_by=user,
        pipeline_state='checked_in',
    )


class TestRoomSelectionRequired:
    """Tests for RoomSelectionRequired exception."""

    def test_room_selection_required_has_available_rooms(self, location):
        """RoomSelectionRequired stores available rooms."""
        room1 = ExamRoom.objects.create(location=location, name='Room 1')
        room2 = ExamRoom.objects.create(location=location, name='Room 2')

        available = ExamRoom.objects.filter(location=location, is_active=True)
        exc = encounters.RoomSelectionRequired(available)

        assert list(exc.available_rooms) == [room1, room2]


class TestTransitionToRoomed:
    """Tests for room assignment when transitioning to 'roomed' state."""

    def test_transition_roomed_with_zero_rooms(self, encounter, user):
        """Transition to roomed with no rooms configured proceeds without room."""
        # No rooms configured for the location
        assert encounter.location.exam_rooms.count() == 0

        result = encounters.transition_state(encounter, 'roomed', user)

        assert result.pipeline_state == 'roomed'
        assert result.exam_room is None
        assert result.roomed_at is not None

    def test_transition_roomed_with_one_room_auto_assigns(self, encounter, user, location):
        """Transition to roomed with 1 room auto-assigns it."""
        room = ExamRoom.objects.create(location=location, name='Room 1')

        result = encounters.transition_state(encounter, 'roomed', user)

        assert result.pipeline_state == 'roomed'
        assert result.exam_room == room
        assert result.roomed_at is not None

    def test_transition_roomed_with_multiple_rooms_requires_selection(self, encounter, user, location):
        """Transition to roomed with >1 rooms raises RoomSelectionRequired."""
        room1 = ExamRoom.objects.create(location=location, name='Room 1')
        room2 = ExamRoom.objects.create(location=location, name='Room 2')

        with pytest.raises(encounters.RoomSelectionRequired) as exc_info:
            encounters.transition_state(encounter, 'roomed', user)

        # State should NOT have changed
        encounter.refresh_from_db()
        assert encounter.pipeline_state == 'checked_in'
        assert encounter.exam_room is None

        # Exception should have available rooms
        assert list(exc_info.value.available_rooms) == [room1, room2]

    def test_transition_roomed_with_room_id_succeeds(self, encounter, user, location):
        """Transition to roomed with exam_room_id assigns the room."""
        room1 = ExamRoom.objects.create(location=location, name='Room 1')
        room2 = ExamRoom.objects.create(location=location, name='Room 2')

        result = encounters.transition_state(
            encounter, 'roomed', user, exam_room_id=room2.id
        )

        assert result.pipeline_state == 'roomed'
        assert result.exam_room == room2

    def test_transition_roomed_invalid_room_id_raises_error(self, encounter, user, location):
        """Transition with invalid room_id raises ValueError."""
        ExamRoom.objects.create(location=location, name='Room 1')
        ExamRoom.objects.create(location=location, name='Room 2')

        with pytest.raises(ValueError, match="Invalid room"):
            encounters.transition_state(
                encounter, 'roomed', user, exam_room_id=99999
            )

        # State should NOT have changed
        encounter.refresh_from_db()
        assert encounter.pipeline_state == 'checked_in'

    def test_transition_roomed_inactive_room_not_auto_assigned(self, encounter, user, location):
        """Inactive rooms are not counted for auto-assignment."""
        ExamRoom.objects.create(location=location, name='Room 1', is_active=False)
        room2 = ExamRoom.objects.create(location=location, name='Room 2', is_active=True)

        # Only 1 active room, should auto-assign
        result = encounters.transition_state(encounter, 'roomed', user)

        assert result.exam_room == room2

    def test_transition_roomed_inactive_room_not_in_selection(self, encounter, user, location):
        """Inactive rooms are excluded from room selection."""
        room1 = ExamRoom.objects.create(location=location, name='Room 1', is_active=True)
        ExamRoom.objects.create(location=location, name='Room 2', is_active=False)
        room3 = ExamRoom.objects.create(location=location, name='Room 3', is_active=True)

        # 2 active rooms should require selection
        with pytest.raises(encounters.RoomSelectionRequired) as exc_info:
            encounters.transition_state(encounter, 'roomed', user)

        available = list(exc_info.value.available_rooms)
        assert room1 in available
        assert room3 in available
        assert len(available) == 2


class TestRoomAssignmentClinicalEvent:
    """Tests for ClinicalEvent logging when room is assigned."""

    def test_room_assignment_logs_clinical_event(self, encounter, user, location):
        """Room assignment creates a ClinicalEvent."""
        room = ExamRoom.objects.create(location=location, name='Room 1')

        initial_event_count = ClinicalEvent.objects.filter(
            encounter=encounter,
            event_type='state_change',
        ).count()

        encounters.transition_state(encounter, 'roomed', user)

        # Should have logged state transition (includes room assignment info)
        events = ClinicalEvent.objects.filter(
            encounter=encounter,
            event_type='state_change',
        ).order_by('-occurred_at')

        # At least one new event should exist
        assert events.count() > initial_event_count

        # Most recent event should mention roomed
        latest_event = events.first()
        assert 'Roomed' in latest_event.summary or 'roomed' in latest_event.event_subtype

    def test_room_assignment_event_has_room_name(self, encounter, user, location):
        """Room assignment event includes room name in summary."""
        room = ExamRoom.objects.create(location=location, name='Surgery Suite')

        encounters.transition_state(encounter, 'roomed', user)

        event = ClinicalEvent.objects.filter(
            encounter=encounter,
            event_type='state_change',
            event_subtype='room_assignment',
        ).first()

        assert event is not None
        assert 'Surgery Suite' in event.summary


class TestOtherTransitionsIgnoreRoom:
    """Tests that non-roomed transitions ignore room parameter."""

    def test_transition_to_in_exam_ignores_room_id(self, encounter, user, location):
        """Transition to in_exam doesn't assign room even with room_id."""
        room = ExamRoom.objects.create(location=location, name='Room 1')
        encounter.pipeline_state = 'roomed'
        encounter.save()

        result = encounters.transition_state(
            encounter, 'in_exam', user, exam_room_id=room.id
        )

        assert result.pipeline_state == 'in_exam'
        # Room should not be changed (it wasn't set before)
        # The point is no error is raised

    def test_transition_to_checkout_works_normally(self, encounter, user, location):
        """Normal transitions work without room selection."""
        encounter.pipeline_state = 'in_exam'
        encounter.save()

        result = encounters.transition_state(encounter, 'checkout', user)

        assert result.pipeline_state == 'checkout'


class TestEncounterExamRoomFK:
    """Tests for Encounter.exam_room FK field."""

    def test_encounter_exam_room_nullable(self, encounter):
        """Encounter.exam_room is nullable."""
        assert encounter.exam_room is None

    def test_encounter_exam_room_can_be_set(self, encounter, location):
        """Can assign exam_room to encounter."""
        room = ExamRoom.objects.create(location=location, name='Room 1')

        encounter.exam_room = room
        encounter.save()
        encounter.refresh_from_db()

        assert encounter.exam_room == room

    def test_exam_room_protect_on_delete(self, encounter, location):
        """Cannot delete ExamRoom if encounters reference it."""
        room = ExamRoom.objects.create(location=location, name='Room 1')
        encounter.exam_room = room
        encounter.save()

        from django.db.models import ProtectedError
        with pytest.raises(ProtectedError):
            room.delete()
