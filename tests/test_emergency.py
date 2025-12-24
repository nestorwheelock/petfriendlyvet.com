"""Tests for emergency services app (TDD first)."""
import pytest
from datetime import date, time, timedelta
from decimal import Decimal
from django.utils import timezone

from apps.accounts.models import User

pytestmark = pytest.mark.django_db


class TestEmergencySymptomModel:
    """Tests for EmergencySymptom model."""

    def test_create_emergency_symptom(self):
        """Test creating an emergency symptom."""
        from apps.emergency.models import EmergencySymptom

        symptom = EmergencySymptom.objects.create(
            keyword='not breathing',
            keywords_es=['no respira', 'sin respirar', 'dejo de respirar'],
            keywords_en=['not breathing', 'cant breathe', 'stopped breathing'],
            species=['dog', 'cat', 'all'],
            severity='critical',
            description='Pet is having difficulty breathing or has stopped breathing',
            follow_up_questions=[
                'Is your pet conscious?',
                'What color are the gums?',
            ],
            first_aid_instructions='Keep pet calm, check airway is clear',
            warning_signs='Blue gums, gasping, collapse',
        )

        assert symptom.keyword == 'not breathing'
        assert 'no respira' in symptom.keywords_es
        assert symptom.severity == 'critical'
        assert symptom.is_active is True

    def test_symptom_str_representation(self):
        """Test string representation of symptom."""
        from apps.emergency.models import EmergencySymptom

        symptom = EmergencySymptom.objects.create(
            keyword='poisoning',
            severity='critical',
            description='Suspected poisoning',
        )

        assert str(symptom) == 'poisoning (critical)'

    def test_default_json_fields(self):
        """Test default values for JSON fields."""
        from apps.emergency.models import EmergencySymptom

        symptom = EmergencySymptom.objects.create(
            keyword='vomiting',
            severity='moderate',
            description='Pet is vomiting',
        )

        assert symptom.keywords_es == []
        assert symptom.keywords_en == []
        assert symptom.species == []
        assert symptom.follow_up_questions == []


class TestEmergencyContactModel:
    """Tests for EmergencyContact model."""

    def test_create_emergency_contact(self, user):
        """Test creating an emergency contact record."""
        from apps.emergency.models import EmergencyContact
        from apps.pets.models import Pet

        pet = Pet.objects.create(
            name='Max',
            species='dog',
            breed='Labrador',
            owner=user,
            date_of_birth=date(2020, 5, 15),
        )

        contact = EmergencyContact.objects.create(
            owner=user,
            pet=pet,
            phone='+529981234567',
            channel='whatsapp',
            reported_symptoms='Dog is not breathing well, collapsed',
            pet_species='dog',
            pet_age='4 years',
            severity='critical',
            triage_notes='Owner reports sudden collapse',
            ai_assessment={'symptoms': ['collapse', 'breathing'], 'urgency': 'critical'},
        )

        assert contact.owner == user
        assert contact.pet == pet
        assert contact.severity == 'critical'
        assert contact.status == 'initiated'

    def test_emergency_contact_status_choices(self):
        """Test all status choices are valid."""
        from apps.emergency.models import EmergencyContact

        statuses = ['initiated', 'triaging', 'escalated', 'resolved', 'referred', 'no_response']
        for status in statuses:
            contact = EmergencyContact.objects.create(
                phone='+529981234567',
                channel='phone',
                reported_symptoms='Test symptoms',
                pet_species='dog',
                status=status,
            )
            assert contact.status == status

    def test_emergency_contact_severity_choices(self):
        """Test all severity choices are valid."""
        from apps.emergency.models import EmergencyContact

        severities = ['critical', 'urgent', 'moderate', 'low']
        for severity in severities:
            contact = EmergencyContact.objects.create(
                phone='+529981234567',
                channel='web',
                reported_symptoms='Test symptoms',
                pet_species='cat',
                severity=severity,
            )
            assert contact.severity == severity

    def test_emergency_contact_timestamps(self):
        """Test timestamp handling."""
        from apps.emergency.models import EmergencyContact

        before = timezone.now()
        contact = EmergencyContact.objects.create(
            phone='+529981234567',
            channel='sms',
            reported_symptoms='Test',
            pet_species='dog',
        )
        after = timezone.now()

        assert before <= contact.created_at <= after
        assert contact.escalated_at is None
        assert contact.resolved_at is None

    def test_emergency_contact_ordering(self):
        """Test contacts are ordered by created_at descending."""
        from apps.emergency.models import EmergencyContact

        c1 = EmergencyContact.objects.create(
            phone='+529981234567',
            channel='web',
            reported_symptoms='First',
            pet_species='dog',
        )
        c2 = EmergencyContact.objects.create(
            phone='+529987654321',
            channel='web',
            reported_symptoms='Second',
            pet_species='cat',
        )

        contacts = list(EmergencyContact.objects.all())
        assert contacts[0] == c2  # Most recent first
        assert contacts[1] == c1


class TestOnCallScheduleModel:
    """Tests for OnCallSchedule model."""

    def test_create_oncall_schedule(self, staff_user):
        """Test creating an on-call schedule."""
        from apps.emergency.models import OnCallSchedule
        from apps.practice.models import StaffProfile

        staff_profile = StaffProfile.objects.create(
            user=staff_user,
            role='veterinarian',
        )

        schedule = OnCallSchedule.objects.create(
            staff=staff_profile,
            date=date.today(),
            start_time=time(18, 0),
            end_time=time(8, 0),
            contact_phone='+529981234567',
            backup_phone='+529987654321',
        )

        assert schedule.staff == staff_profile
        assert schedule.date == date.today()
        assert schedule.is_active is True
        assert schedule.swap_requested is False

    def test_oncall_schedule_ordering(self, staff_user):
        """Test schedules are ordered by date and start_time."""
        from apps.emergency.models import OnCallSchedule
        from apps.practice.models import StaffProfile

        staff_profile = StaffProfile.objects.create(
            user=staff_user,
            role='veterinarian',
        )

        today = date.today()
        s1 = OnCallSchedule.objects.create(
            staff=staff_profile,
            date=today + timedelta(days=1),
            start_time=time(8, 0),
            end_time=time(18, 0),
            contact_phone='+529981234567',
        )
        s2 = OnCallSchedule.objects.create(
            staff=staff_profile,
            date=today,
            start_time=time(18, 0),
            end_time=time(8, 0),
            contact_phone='+529981234567',
        )

        schedules = list(OnCallSchedule.objects.all())
        assert schedules[0] == s2  # Today first
        assert schedules[1] == s1  # Tomorrow second

    def test_oncall_str_representation(self, staff_user):
        """Test string representation of on-call schedule."""
        from apps.emergency.models import OnCallSchedule
        from apps.practice.models import StaffProfile

        staff_profile = StaffProfile.objects.create(
            user=staff_user,
            role='veterinarian',
        )

        schedule = OnCallSchedule.objects.create(
            staff=staff_profile,
            date=date(2025, 12, 25),
            start_time=time(18, 0),
            end_time=time(8, 0),
            contact_phone='+529981234567',
        )

        assert '2025-12-25' in str(schedule)


class TestEmergencyReferralModel:
    """Tests for EmergencyReferral model (24-hour hospitals)."""

    def test_create_emergency_referral(self):
        """Test creating an emergency referral hospital."""
        from apps.emergency.models import EmergencyReferral

        hospital = EmergencyReferral.objects.create(
            name='Hospital Veterinario Cancún',
            address='Av. Tulum 123, Cancún, QR',
            phone='+529988845678',
            whatsapp='+529988845678',
            latitude=Decimal('21.1619'),
            longitude=Decimal('-86.8515'),
            distance_km=35.5,
            is_24_hours=True,
            hours={'mon': '24h', 'tue': '24h'},
            services=['surgery', 'xray', 'blood_work', 'icu', 'oxygen'],
            species_treated=['dog', 'cat', 'bird'],
        )

        assert hospital.name == 'Hospital Veterinario Cancún'
        assert hospital.is_24_hours is True
        assert 'surgery' in hospital.services
        assert hospital.is_active is True

    def test_referral_str_representation(self):
        """Test string representation."""
        from apps.emergency.models import EmergencyReferral

        hospital = EmergencyReferral.objects.create(
            name='Pet Emergency Center',
            address='Test Address',
            phone='+529981234567',
            latitude=Decimal('21.0000'),
            longitude=Decimal('-86.0000'),
        )

        assert str(hospital) == 'Pet Emergency Center'

    def test_referral_defaults(self):
        """Test default values for JSON fields."""
        from apps.emergency.models import EmergencyReferral

        hospital = EmergencyReferral.objects.create(
            name='Test Hospital',
            address='Test Address',
            phone='+529981234567',
            latitude=Decimal('21.0000'),
            longitude=Decimal('-86.0000'),
        )

        assert hospital.hours == {}
        assert hospital.services == []
        assert hospital.species_treated == []
        assert hospital.is_24_hours is False


class TestEmergencyFirstAidModel:
    """Tests for EmergencyFirstAid model."""

    def test_create_first_aid_instructions(self):
        """Test creating first aid instructions."""
        from apps.emergency.models import EmergencyFirstAid

        first_aid = EmergencyFirstAid.objects.create(
            title='Choking',
            title_es='Asfixia',
            condition='choking',
            species=['dog', 'cat'],
            description='How to help a choking pet',
            description_es='Cómo ayudar a una mascota que se asfixia',
            steps=[
                {'step': 1, 'instruction': 'Stay calm', 'instruction_es': 'Mantén la calma'},
                {'step': 2, 'instruction': 'Check mouth', 'instruction_es': 'Revisa la boca'},
            ],
            warnings=['Do not put fingers in mouth if pet is conscious'],
            do_not=['Do not perform CPR unless necessary'],
        )

        assert first_aid.title == 'Choking'
        assert len(first_aid.steps) == 2
        assert first_aid.is_active is True

    def test_first_aid_str_representation(self):
        """Test string representation."""
        from apps.emergency.models import EmergencyFirstAid

        first_aid = EmergencyFirstAid.objects.create(
            title='Poisoning',
            title_es='Envenenamiento',
            condition='poisoning',
            description='Treatment for poisoning',
            description_es='Tratamiento para envenenamiento',
        )

        assert str(first_aid) == 'Poisoning'

    def test_first_aid_with_related_symptoms(self):
        """Test first aid with related symptoms."""
        from apps.emergency.models import EmergencyFirstAid, EmergencySymptom

        symptom = EmergencySymptom.objects.create(
            keyword='vomiting',
            severity='moderate',
            description='Vomiting',
        )

        first_aid = EmergencyFirstAid.objects.create(
            title='Vomiting Care',
            title_es='Cuidado de Vómitos',
            condition='vomiting',
            description='How to handle vomiting',
            description_es='Cómo manejar el vómito',
        )
        first_aid.related_symptoms.add(symptom)

        assert symptom in first_aid.related_symptoms.all()


class TestEmergencyAITools:
    """Tests for emergency AI tools."""

    def test_triage_emergency_tool_exists(self):
        """Test triage_emergency tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('triage_emergency')
        assert tool is not None

    def test_triage_critical_emergency(self):
        """Test triaging a critical emergency."""
        from apps.ai_assistant.tools import triage_emergency
        from apps.emergency.models import EmergencySymptom

        # Create critical symptom in database
        EmergencySymptom.objects.create(
            keyword='not breathing',
            keywords_es=['no respira'],
            keywords_en=['not breathing'],
            species=['all'],
            severity='critical',
            description='Breathing emergency',
            first_aid_instructions='Keep calm, check airway',
        )

        result = triage_emergency(
            symptoms='my dog is not breathing',
            species='dog',
        )

        assert result['severity'] in ['critical', 'urgent']
        assert result['requires_immediate_attention'] is True

    def test_triage_moderate_emergency(self):
        """Test triaging a moderate emergency."""
        from apps.ai_assistant.tools import triage_emergency
        from apps.emergency.models import EmergencySymptom

        EmergencySymptom.objects.create(
            keyword='vomiting',
            keywords_en=['vomited', 'throwing up', 'vomit'],
            severity='moderate',
            description='Vomiting',
        )

        result = triage_emergency(
            symptoms='my cat has vomited twice',
            species='cat',
        )

        assert result['severity'] in ['moderate', 'urgent']
        assert 'recommendations' in result

    def test_get_oncall_status_tool_exists(self):
        """Test get_oncall_status tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('get_oncall_status')
        assert tool is not None

    def test_get_oncall_status_returns_current_oncall(self, staff_user):
        """Test getting current on-call vet."""
        from apps.ai_assistant.tools import get_oncall_status
        from apps.emergency.models import OnCallSchedule
        from apps.practice.models import StaffProfile

        staff_profile = StaffProfile.objects.create(
            user=staff_user,
            role='veterinarian',
        )

        now = timezone.now()
        OnCallSchedule.objects.create(
            staff=staff_profile,
            date=now.date(),
            start_time=time(0, 0),
            end_time=time(23, 59),
            contact_phone='+529981234567',
            is_active=True,
        )

        result = get_oncall_status()

        assert result['is_on_call'] is True
        assert result['staff_name'] == staff_user.get_full_name() or staff_user.email
        assert result['contact_phone'] == '+529981234567'

    def test_get_oncall_status_no_oncall(self):
        """Test when no one is on call."""
        from apps.ai_assistant.tools import get_oncall_status

        result = get_oncall_status()

        assert result['is_on_call'] is False
        assert 'message' in result

    def test_get_emergency_referrals_tool_exists(self):
        """Test get_emergency_referrals tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('get_emergency_referrals')
        assert tool is not None

    def test_get_emergency_referrals(self):
        """Test getting emergency referral hospitals."""
        from apps.ai_assistant.tools import get_emergency_referrals
        from apps.emergency.models import EmergencyReferral

        EmergencyReferral.objects.create(
            name='24 Hour Pet Hospital',
            address='Main Street',
            phone='+529981234567',
            latitude=Decimal('21.0000'),
            longitude=Decimal('-86.0000'),
            is_24_hours=True,
            species_treated=['dog', 'cat'],
        )

        result = get_emergency_referrals(is_24_hours=True)

        assert result['count'] >= 1
        assert any(h['name'] == '24 Hour Pet Hospital' for h in result['hospitals'])

    def test_get_emergency_referrals_by_species(self):
        """Test filtering referrals by species."""
        from apps.ai_assistant.tools import get_emergency_referrals
        from apps.emergency.models import EmergencyReferral

        EmergencyReferral.objects.create(
            name='Exotic Animal Hospital',
            address='Test Address',
            phone='+529981234567',
            latitude=Decimal('21.0000'),
            longitude=Decimal('-86.0000'),
            species_treated=['bird', 'reptile'],
        )

        result = get_emergency_referrals(species='bird')

        assert any(h['name'] == 'Exotic Animal Hospital' for h in result['hospitals'])

    def test_get_first_aid_instructions_tool_exists(self):
        """Test get_first_aid_instructions tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('get_first_aid_instructions')
        assert tool is not None

    def test_get_first_aid_instructions(self):
        """Test getting first aid instructions."""
        from apps.ai_assistant.tools import get_first_aid_instructions
        from apps.emergency.models import EmergencyFirstAid

        EmergencyFirstAid.objects.create(
            title='Bleeding',
            title_es='Sangrado',
            condition='bleeding',
            species=['all'],
            description='Control bleeding',
            description_es='Controlar sangrado',
            steps=[
                {'step': 1, 'instruction': 'Apply pressure'},
            ],
        )

        result = get_first_aid_instructions(condition='bleeding')

        assert result['title'] == 'Bleeding'
        assert len(result['steps']) >= 1

    def test_escalate_to_oncall_tool_exists(self):
        """Test escalate_to_oncall tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('escalate_to_oncall')
        assert tool is not None

    def test_escalate_to_oncall(self, staff_user):
        """Test escalating emergency to on-call vet."""
        from apps.ai_assistant.tools import escalate_to_oncall
        from apps.emergency.models import EmergencyContact, OnCallSchedule
        from apps.practice.models import StaffProfile

        staff_profile = StaffProfile.objects.create(
            user=staff_user,
            role='veterinarian',
        )

        now = timezone.now()
        OnCallSchedule.objects.create(
            staff=staff_profile,
            date=now.date(),
            start_time=time(0, 0),
            end_time=time(23, 59),
            contact_phone='+529981234567',
            is_active=True,
        )

        contact = EmergencyContact.objects.create(
            phone='+529987654321',
            channel='web',
            reported_symptoms='Critical symptoms',
            pet_species='dog',
            severity='critical',
        )

        result = escalate_to_oncall(
            emergency_contact_id=contact.id,
            urgency='critical',
            callback_number='+529987654321',
        )

        assert result['escalated'] is True
        assert result['on_call_vet'] == staff_user.get_full_name() or staff_user.email

        # Verify contact was updated
        contact.refresh_from_db()
        assert contact.status == 'escalated'
        assert contact.escalated_at is not None

    def test_create_emergency_contact_tool_exists(self):
        """Test create_emergency_contact tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('create_emergency_contact')
        assert tool is not None

    def test_create_emergency_contact(self, user):
        """Test creating an emergency contact via AI tool."""
        from apps.ai_assistant.tools import create_emergency_contact

        result = create_emergency_contact(
            phone='+529981234567',
            channel='whatsapp',
            symptoms='Dog is having trouble breathing',
            pet_species='dog',
            owner_id=user.id,
        )

        assert result['success'] is True
        assert 'emergency_contact_id' in result

    def test_log_emergency_resolution_tool_exists(self):
        """Test log_emergency_resolution tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('log_emergency_resolution')
        assert tool is not None

    def test_log_emergency_resolution(self):
        """Test logging emergency resolution."""
        from apps.ai_assistant.tools import log_emergency_resolution
        from apps.emergency.models import EmergencyContact

        contact = EmergencyContact.objects.create(
            phone='+529981234567',
            channel='web',
            reported_symptoms='Test symptoms',
            pet_species='dog',
            severity='moderate',
        )

        result = log_emergency_resolution(
            emergency_contact_id=contact.id,
            outcome='seen_at_clinic',
            notes='Pet treated successfully',
        )

        assert result['success'] is True

        contact.refresh_from_db()
        assert contact.status == 'resolved'
        assert contact.outcome == 'seen_at_clinic'
        assert contact.resolved_at is not None


class TestEmergencyIntegration:
    """Integration tests for emergency workflow."""

    def test_full_emergency_triage_workflow(self, user, staff_user):
        """Test complete emergency triage workflow."""
        from apps.ai_assistant.tools import (
            create_emergency_contact,
            triage_emergency,
            escalate_to_oncall,
            log_emergency_resolution,
        )
        from apps.emergency.models import EmergencyContact, EmergencySymptom, OnCallSchedule
        from apps.practice.models import StaffProfile

        # Setup symptom database
        EmergencySymptom.objects.create(
            keyword='collapsed',
            severity='critical',
            description='Pet has collapsed',
            first_aid_instructions='Keep pet calm',
        )

        # Setup on-call staff
        staff_profile = StaffProfile.objects.create(
            user=staff_user,
            role='veterinarian',
        )
        now = timezone.now()
        OnCallSchedule.objects.create(
            staff=staff_profile,
            date=now.date(),
            start_time=time(0, 0),
            end_time=time(23, 59),
            contact_phone='+529981234567',
            is_active=True,
        )

        # Step 1: Create emergency contact
        contact_result = create_emergency_contact(
            phone='+529987654321',
            channel='whatsapp',
            symptoms='My dog collapsed and is not moving',
            pet_species='dog',
            owner_id=user.id,
        )
        assert contact_result['success'] is True
        contact_id = contact_result['emergency_contact_id']

        # Step 2: Triage
        triage_result = triage_emergency(
            symptoms='collapsed not moving',
            species='dog',
        )
        assert triage_result['severity'] in ['critical', 'urgent']

        # Step 3: Escalate to on-call
        escalate_result = escalate_to_oncall(
            emergency_contact_id=contact_id,
            urgency='critical',
            callback_number='+529987654321',
        )
        assert escalate_result['escalated'] is True

        # Step 4: Resolve
        resolve_result = log_emergency_resolution(
            emergency_contact_id=contact_id,
            outcome='seen_at_clinic',
            notes='Pet stabilized and treated',
        )
        assert resolve_result['success'] is True

        # Verify final state
        contact = EmergencyContact.objects.get(id=contact_id)
        assert contact.status == 'resolved'
        assert contact.outcome == 'seen_at_clinic'

    def test_emergency_referral_workflow(self):
        """Test emergency referral to 24-hour hospital."""
        from apps.ai_assistant.tools import (
            create_emergency_contact,
            get_emergency_referrals,
            log_emergency_resolution,
        )
        from apps.emergency.models import EmergencyReferral

        # Setup referral hospital
        EmergencyReferral.objects.create(
            name='24 Hour Emergency Hospital',
            address='Emergency Street 123',
            phone='+529988887777',
            latitude=Decimal('21.0000'),
            longitude=Decimal('-86.0000'),
            is_24_hours=True,
            species_treated=['dog', 'cat'],
        )

        # Create emergency
        contact_result = create_emergency_contact(
            phone='+529987654321',
            channel='web',
            symptoms='Dog was hit by a car',
            pet_species='dog',
        )
        contact_id = contact_result['emergency_contact_id']

        # Get referral options
        referrals = get_emergency_referrals(is_24_hours=True, species='dog')
        assert referrals['count'] >= 1

        # Log referral
        resolve_result = log_emergency_resolution(
            emergency_contact_id=contact_id,
            outcome='referred',
            notes='Referred to 24 Hour Emergency Hospital',
        )
        assert resolve_result['success'] is True


# Fixtures
@pytest.fixture
def user():
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User',
    )


@pytest.fixture
def staff_user():
    """Create a staff user."""
    return User.objects.create_user(
        username='drpablo',
        email='drpablo@petfriendly.com',
        password='staffpass123',
        first_name='Pablo',
        last_name='Rojo',
        is_staff=True,
    )
