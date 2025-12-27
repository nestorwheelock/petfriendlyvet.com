"""Tests for EMR views.

TDD: These tests are written BEFORE views.py implementation.
All tests should FAIL initially, then pass as views are implemented.
"""
import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.models import User
from apps.emr.models import Encounter, PatientProblem, ClinicalEvent
from apps.locations.models import Location
from apps.parties.models import Organization
from apps.practice.models import PatientRecord
from apps.pets.models import Pet


@pytest.fixture
def organization(db):
    """Create test organization."""
    return Organization.objects.create(name="Test Clinic", is_active=True)


@pytest.fixture
def location(db, organization):
    """Create test location."""
    return Location.objects.create(
        organization=organization,
        name="Main Clinic",
        code="MAIN",
        is_active=True,
    )


@pytest.fixture
def staff_user(db):
    """Create staff user with EMR permissions.

    Uses superuser to bypass permission checks in tests.
    In production, users would have permissions via Roles.
    """
    user = User.objects.create_user(
        username="staffuser",
        email="staff@test.com",
        password="testpass123",
        is_staff=True,
        is_superuser=True,  # Grants all module permissions
    )
    return user


@pytest.fixture
def regular_user(db):
    """Create regular (non-staff) user."""
    return User.objects.create_user(
        username="regularuser",
        email="regular@test.com",
        password="testpass123",
        is_staff=False,
    )


@pytest.fixture
def patient(db, organization):
    """Create test patient."""
    # Create a pet owner first
    owner = User.objects.create_user(
        username="petowner",
        email="owner@test.com",
        password="testpass123",
    )
    pet = Pet.objects.create(
        name="Buddy",
        species="dog",
        owner=owner,
    )
    return PatientRecord.objects.create(
        pet=pet,
        patient_number="P-0001",
    )


@pytest.fixture
def encounter(db, patient, location, staff_user):
    """Create test encounter."""
    return Encounter.objects.create(
        patient=patient,
        location=location,
        pipeline_state="checked_in",
        encounter_type="routine",
        chief_complaint="Annual checkup",
        created_by=staff_user,
    )


class TestWhiteboardView:
    """Tests for the whiteboard (encounter board) view."""

    def test_whiteboard_requires_login(self, client):
        """Anonymous users should be redirected to login."""
        url = reverse("emr:whiteboard")
        response = client.get(url)
        assert response.status_code == 302
        assert "/accounts/login/" in response.url or "/login/" in response.url

    def test_whiteboard_requires_staff(self, client, regular_user):
        """Non-staff users should be denied access."""
        client.force_login(regular_user)
        url = reverse("emr:whiteboard")
        response = client.get(url)
        # Should be 403 Forbidden or redirect
        assert response.status_code in (302, 403)

    def test_whiteboard_accessible_to_staff(self, client, staff_user, location):
        """Staff users should access whiteboard."""
        client.force_login(staff_user)
        # Set selected location in session
        session = client.session
        session["emr_selected_location_id"] = location.id
        session.save()

        url = reverse("emr:whiteboard")
        response = client.get(url)
        assert response.status_code == 200

    def test_whiteboard_shows_location_selector_when_none_selected(
        self, client, staff_user, location
    ):
        """Without selected location, show location selector."""
        client.force_login(staff_user)
        url = reverse("emr:whiteboard")
        response = client.get(url)
        assert response.status_code == 200
        # Should contain location selector or prompt
        assert b"select" in response.content.lower() or b"location" in response.content.lower()

    def test_whiteboard_filters_by_selected_location(
        self, client, staff_user, location, encounter
    ):
        """Encounters should be filtered by selected location."""
        client.force_login(staff_user)
        session = client.session
        session["emr_selected_location_id"] = location.id
        session.save()

        url = reverse("emr:whiteboard")
        response = client.get(url)
        assert response.status_code == 200
        # Should show the encounter
        assert encounter.chief_complaint.encode() in response.content


class TestSelectLocationView:
    """Tests for location selection."""

    def test_select_location_requires_post(self, client, staff_user):
        """GET should not be allowed."""
        client.force_login(staff_user)
        url = reverse("emr:select_location")
        response = client.get(url)
        assert response.status_code == 405  # Method Not Allowed

    def test_select_location_sets_session(self, client, staff_user, location):
        """POST should set location in session."""
        client.force_login(staff_user)
        url = reverse("emr:select_location")
        response = client.post(url, {"location_id": location.id})

        # Should redirect to whiteboard
        assert response.status_code == 302

        # Session should have the location
        assert client.session.get("emr_selected_location_id") == location.id

    def test_select_location_validates_location_exists(self, client, staff_user):
        """Invalid location ID should be rejected."""
        client.force_login(staff_user)
        url = reverse("emr:select_location")
        response = client.post(url, {"location_id": 99999})
        # Should return error or redirect with message
        assert response.status_code in (400, 404, 302)


class TestPatientSummaryView:
    """Tests for patient clinical summary."""

    def test_patient_summary_requires_login(self, client, patient):
        """Anonymous users should be redirected."""
        url = reverse("emr:patient_summary", kwargs={"patient_id": patient.id})
        response = client.get(url)
        assert response.status_code == 302

    def test_patient_summary_shows_alerts(self, client, staff_user, patient, location):
        """Should display active alerts (PatientProblem with is_alert=True)."""
        client.force_login(staff_user)
        session = client.session
        session["emr_selected_location_id"] = location.id
        session.save()

        # Create an alert
        PatientProblem.objects.create(
            patient=patient,
            name="Penicillin Allergy",
            problem_type="allergy",
            is_alert=True,
            alert_text="ALLERGIC TO PENICILLIN",
            alert_severity="danger",
            created_by=staff_user,
        )

        url = reverse("emr:patient_summary", kwargs={"patient_id": patient.id})
        response = client.get(url)
        assert response.status_code == 200
        assert b"ALLERGIC TO PENICILLIN" in response.content

    def test_patient_summary_shows_problem_list(self, client, staff_user, patient, location):
        """Should display problem list grouped by status."""
        client.force_login(staff_user)
        session = client.session
        session["emr_selected_location_id"] = location.id
        session.save()

        PatientProblem.objects.create(
            patient=patient,
            name="Diabetes",
            problem_type="chronic",
            status="active",
            created_by=staff_user,
        )

        url = reverse("emr:patient_summary", kwargs={"patient_id": patient.id})
        response = client.get(url)
        assert response.status_code == 200
        assert b"Diabetes" in response.content


class TestTransitionEncounterView:
    """Tests for encounter state transitions."""

    def test_transition_requires_post(self, client, staff_user, encounter):
        """GET should not be allowed."""
        client.force_login(staff_user)
        url = reverse("emr:transition_encounter", kwargs={"encounter_id": encounter.id})
        response = client.get(url)
        assert response.status_code == 405

    def test_transition_updates_state(self, client, staff_user, encounter, location):
        """POST should transition encounter state."""
        client.force_login(staff_user)
        session = client.session
        session["emr_selected_location_id"] = location.id
        session.save()

        url = reverse("emr:transition_encounter", kwargs={"encounter_id": encounter.id})
        response = client.post(url, {"new_state": "roomed"})

        # Refresh from DB
        encounter.refresh_from_db()
        assert encounter.pipeline_state == "roomed"

    def test_transition_creates_clinical_event(self, client, staff_user, encounter, location):
        """State transition should create ClinicalEvent."""
        client.force_login(staff_user)
        session = client.session
        session["emr_selected_location_id"] = location.id
        session.save()

        initial_count = ClinicalEvent.objects.count()

        url = reverse("emr:transition_encounter", kwargs={"encounter_id": encounter.id})
        client.post(url, {"new_state": "roomed"})

        # Should have created a clinical event
        assert ClinicalEvent.objects.count() == initial_count + 1

        event = ClinicalEvent.objects.latest("recorded_at")
        assert event.event_type == "state_change"
        assert event.encounter == encounter

    def test_transition_invalid_state_rejected(self, client, staff_user, encounter, location):
        """Invalid state should be rejected."""
        client.force_login(staff_user)
        session = client.session
        session["emr_selected_location_id"] = location.id
        session.save()

        url = reverse("emr:transition_encounter", kwargs={"encounter_id": encounter.id})
        response = client.post(url, {"new_state": "invalid_state"})

        # Should return error
        assert response.status_code == 400

        # State should not change
        encounter.refresh_from_db()
        assert encounter.pipeline_state == "checked_in"
