"""Tests for S-010 Pharmacy Management.

Tests validate pharmacy functionality:
- Medication database
- Prescription management
- Refill requests
- Drug interactions
- Controlled substance logging
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def staff_user(db):
    """Create a staff user."""
    user = User.objects.create_user(
        username='staff_pharm',
        email='staff@petfriendly.com',
        password='testpass123',
        is_staff=True
    )
    return user


@pytest.fixture
def vet_user(db):
    """Create a veterinarian user."""
    user = User.objects.create_user(
        username='vet_pablo',
        email='vet@petfriendly.com',
        password='testpass123',
        is_staff=True
    )
    return user


@pytest.fixture
def owner_user(db):
    """Create a pet owner user."""
    return User.objects.create_user(
        username='owner_pharm',
        email='owner@test.com',
        password='testpass123'
    )


@pytest.fixture
def staff_profile(staff_user):
    """Create a staff profile."""
    from apps.practice.models import StaffProfile
    return StaffProfile.objects.create(
        user=staff_user,
        role='pharmacy_tech',
        title='Pharmacy Technician'
    )


@pytest.fixture
def vet_profile(vet_user):
    """Create a veterinarian staff profile."""
    from apps.practice.models import StaffProfile
    return StaffProfile.objects.create(
        user=vet_user,
        role='veterinarian',
        title='Veterinarian',
        can_prescribe=True
    )


@pytest.fixture
def pet(owner_user):
    """Create a test pet."""
    from apps.pets.models import Pet
    return Pet.objects.create(
        name='Luna',
        species='cat',
        owner=owner_user
    )


@pytest.fixture
def medication(db):
    """Create a test medication."""
    from apps.pharmacy.models import Medication
    return Medication.objects.create(
        name='Methimazole',
        generic_name='Methimazole',
        drug_class='Antithyroid',
        species=['cat'],
        dosage_forms=['tablet'],
        strengths=['5mg', '10mg'],
        requires_prescription=True
    )


@pytest.fixture
def controlled_medication(db):
    """Create a controlled substance medication."""
    from apps.pharmacy.models import Medication
    return Medication.objects.create(
        name='Tramadol',
        generic_name='Tramadol HCL',
        drug_class='Opioid Analgesic',
        schedule='IV',
        is_controlled=True,
        species=['dog', 'cat'],
        dosage_forms=['tablet'],
        strengths=['50mg', '100mg'],
        requires_prescription=True
    )


@pytest.fixture
def prescription(pet, owner_user, vet_profile, medication):
    """Create a test prescription."""
    from apps.pharmacy.models import Prescription
    return Prescription.objects.create(
        pet=pet,
        owner=owner_user,
        prescribing_vet=vet_profile,
        medication=medication,
        strength='5mg',
        dosage_form='tablet',
        quantity=60,
        dosage='1 tablet',
        frequency='twice daily',
        duration='30 days',
        instructions='Give with food',
        refills_authorized=3,
        refills_remaining=3,
        prescribed_date=date.today(),
        expiration_date=date.today() + timedelta(days=180)
    )


# =============================================================================
# StaffProfile Model Tests
# =============================================================================

@pytest.mark.django_db
class TestStaffProfileModel:
    """Tests for the StaffProfile model."""

    def test_create_staff_profile(self, staff_user):
        """Can create a staff profile."""
        from apps.practice.models import StaffProfile

        profile = StaffProfile.objects.create(
            user=staff_user,
            role='pharmacy_tech',
            title='Pharmacy Technician'
        )

        assert profile.pk is not None
        assert profile.user == staff_user
        assert profile.role == 'pharmacy_tech'

    def test_staff_profile_str(self, staff_profile):
        """Staff profile string representation."""
        assert 'staff_pharm' in str(staff_profile)

    def test_veterinarian_can_prescribe(self, vet_profile):
        """Veterinarians can prescribe."""
        assert vet_profile.can_prescribe is True

    def test_staff_cannot_prescribe_by_default(self, staff_profile):
        """Regular staff cannot prescribe by default."""
        assert staff_profile.can_prescribe is False


# =============================================================================
# Medication Model Tests
# =============================================================================

@pytest.mark.django_db
class TestMedicationModel:
    """Tests for the Medication model."""

    def test_create_medication(self):
        """Can create a medication."""
        from apps.pharmacy.models import Medication

        med = Medication.objects.create(
            name='Amoxicillin',
            generic_name='Amoxicillin',
            drug_class='Antibiotic',
            species=['dog', 'cat'],
            dosage_forms=['capsule', 'liquid'],
            strengths=['250mg', '500mg'],
            requires_prescription=True
        )

        assert med.pk is not None
        assert med.name == 'Amoxicillin'
        assert 'dog' in med.species

    def test_medication_str(self, medication):
        """Medication string representation."""
        assert 'Methimazole' in str(medication)

    def test_controlled_medication(self, controlled_medication):
        """Controlled medication has schedule."""
        assert controlled_medication.is_controlled is True
        assert controlled_medication.schedule == 'IV'

    def test_medication_default_values(self):
        """Medication has correct defaults."""
        from apps.pharmacy.models import Medication

        med = Medication.objects.create(
            name='Test Med',
            drug_class='Test Class'
        )

        assert med.is_controlled is False
        assert med.requires_prescription is True
        assert med.is_active is True
        assert med.species == []


# =============================================================================
# Prescription Model Tests
# =============================================================================

@pytest.mark.django_db
class TestPrescriptionModel:
    """Tests for the Prescription model."""

    def test_create_prescription(self, pet, owner_user, vet_profile, medication):
        """Can create a prescription."""
        from apps.pharmacy.models import Prescription

        rx = Prescription.objects.create(
            pet=pet,
            owner=owner_user,
            prescribing_vet=vet_profile,
            medication=medication,
            strength='5mg',
            dosage_form='tablet',
            quantity=30,
            dosage='1 tablet',
            frequency='once daily',
            duration='30 days',
            refills_authorized=2,
            refills_remaining=2,
            prescribed_date=date.today(),
            expiration_date=date.today() + timedelta(days=180)
        )

        assert rx.pk is not None
        assert rx.pet == pet
        assert rx.medication == medication
        assert rx.status == 'active'

    def test_prescription_str(self, prescription):
        """Prescription string representation."""
        assert 'Methimazole' in str(prescription)
        assert 'Luna' in str(prescription)

    def test_prescription_is_active(self, prescription):
        """Prescription is active."""
        assert prescription.status == 'active'
        assert prescription.is_active is True

    def test_prescription_is_expired(self, prescription):
        """Prescription expiration check."""
        prescription.expiration_date = date.today() - timedelta(days=1)
        prescription.save()

        assert prescription.is_expired is True

    def test_prescription_has_refills(self, prescription):
        """Prescription has refills available."""
        assert prescription.refills_remaining == 3
        assert prescription.has_refills is True

    def test_prescription_no_refills(self, prescription):
        """Prescription with no refills remaining."""
        prescription.refills_remaining = 0
        prescription.save()

        assert prescription.has_refills is False

    def test_prescription_can_refill(self, prescription):
        """Check if prescription can be refilled."""
        assert prescription.can_refill is True

    def test_prescription_cannot_refill_expired(self, prescription):
        """Cannot refill expired prescription."""
        prescription.expiration_date = date.today() - timedelta(days=1)
        prescription.save()

        assert prescription.can_refill is False

    def test_prescription_cannot_refill_no_refills(self, prescription):
        """Cannot refill without refills remaining."""
        prescription.refills_remaining = 0
        prescription.save()

        assert prescription.can_refill is False


# =============================================================================
# Prescription Fill Tests
# =============================================================================

@pytest.mark.django_db
class TestPrescriptionFillModel:
    """Tests for the PrescriptionFill model."""

    def test_create_prescription_fill(self, prescription, staff_profile):
        """Can create a prescription fill."""
        from apps.pharmacy.models import PrescriptionFill

        fill = PrescriptionFill.objects.create(
            prescription=prescription,
            fill_number=0,  # Original fill
            quantity_dispensed=60,
            dispensed_by=staff_profile,
            fulfillment_method='pickup'
        )

        assert fill.pk is not None
        assert fill.fill_number == 0
        assert fill.status == 'pending'

    def test_fill_ready_for_pickup(self, prescription, staff_profile):
        """Fill can be marked ready."""
        from apps.pharmacy.models import PrescriptionFill

        fill = PrescriptionFill.objects.create(
            prescription=prescription,
            fill_number=0,
            quantity_dispensed=60,
            dispensed_by=staff_profile,
            fulfillment_method='pickup',
            status='ready',
            ready_at=timezone.now()
        )

        assert fill.status == 'ready'
        assert fill.ready_at is not None


# =============================================================================
# Refill Request Tests
# =============================================================================

@pytest.mark.django_db
class TestRefillRequestModel:
    """Tests for the RefillRequest model."""

    def test_create_refill_request(self, prescription, owner_user):
        """Can create a refill request."""
        from apps.pharmacy.models import RefillRequest

        request = RefillRequest.objects.create(
            prescription=prescription,
            requested_by=owner_user,
            notes='Running low on medication'
        )

        assert request.pk is not None
        assert request.status == 'pending'
        assert request.prescription == prescription

    def test_refill_request_approval(self, prescription, owner_user, vet_profile):
        """Refill request can be approved."""
        from apps.pharmacy.models import RefillRequest

        request = RefillRequest.objects.create(
            prescription=prescription,
            requested_by=owner_user
        )

        request.status = 'approved'
        request.authorized_by = vet_profile
        request.authorized_at = timezone.now()
        request.save()

        assert request.status == 'approved'
        assert request.authorized_by == vet_profile

    def test_refill_request_denial(self, prescription, owner_user, vet_profile):
        """Refill request can be denied."""
        from apps.pharmacy.models import RefillRequest

        request = RefillRequest.objects.create(
            prescription=prescription,
            requested_by=owner_user
        )

        request.status = 'denied'
        request.authorized_by = vet_profile
        request.denial_reason = 'Prescription expired'
        request.save()

        assert request.status == 'denied'
        assert 'expired' in request.denial_reason


# =============================================================================
# Controlled Substance Log Tests
# =============================================================================

@pytest.mark.django_db
class TestControlledSubstanceLog:
    """Tests for the ControlledSubstanceLog model."""

    def test_create_controlled_log(self, controlled_medication, staff_profile, vet_profile):
        """Can create controlled substance log entry."""
        from apps.pharmacy.models import ControlledSubstanceLog

        log = ControlledSubstanceLog.objects.create(
            medication=controlled_medication,
            transaction_type='received',
            quantity=Decimal('100'),
            unit='tablets',
            balance_before=Decimal('0'),
            balance_after=Decimal('100'),
            performed_by=staff_profile,
            witnessed_by=vet_profile,
            notes='Initial stock'
        )

        assert log.pk is not None
        assert log.balance_after == Decimal('100')

    def test_dispensing_log(self, controlled_medication, staff_profile, vet_profile, prescription):
        """Log dispensing of controlled substance."""
        from apps.pharmacy.models import ControlledSubstanceLog, PrescriptionFill

        # Create fill first
        fill = PrescriptionFill.objects.create(
            prescription=prescription,
            fill_number=0,
            quantity_dispensed=30,
            dispensed_by=staff_profile,
            fulfillment_method='pickup'
        )

        log = ControlledSubstanceLog.objects.create(
            medication=controlled_medication,
            transaction_type='dispensed',
            quantity=Decimal('30'),
            unit='tablets',
            balance_before=Decimal('100'),
            balance_after=Decimal('70'),
            prescription_fill=fill,
            performed_by=staff_profile,
            witnessed_by=vet_profile
        )

        assert log.transaction_type == 'dispensed'
        assert log.prescription_fill == fill


# =============================================================================
# Drug Interaction Tests
# =============================================================================

@pytest.mark.django_db
class TestDrugInteraction:
    """Tests for drug interaction checking."""

    def test_create_drug_interaction(self, medication, controlled_medication):
        """Can create drug interaction record."""
        from apps.pharmacy.models import DrugInteraction

        interaction = DrugInteraction.objects.create(
            medication_1=medication,
            medication_2=controlled_medication,
            severity='moderate',
            description='May increase sedation effects',
            management='Monitor closely'
        )

        assert interaction.pk is not None
        assert interaction.severity == 'moderate'

    def test_check_interactions(self, medication):
        """Check for drug interactions."""
        from apps.pharmacy.models import Medication, DrugInteraction

        other_med = Medication.objects.create(
            name='Fluoxetine',
            drug_class='SSRI',
            species=['dog', 'cat']
        )

        DrugInteraction.objects.create(
            medication_1=medication,
            medication_2=other_med,
            severity='major',
            description='Risk of serotonin syndrome'
        )

        # Check interactions for medication
        interactions = DrugInteraction.objects.filter(
            medication_1=medication
        ) | DrugInteraction.objects.filter(
            medication_2=medication
        )

        assert interactions.count() == 1
        assert interactions.first().severity == 'major'


# =============================================================================
# AI Tools Tests
# =============================================================================

@pytest.mark.django_db
class TestPharmacyAITools:
    """Tests for pharmacy AI tools."""

    def test_get_pet_prescriptions(self, prescription, owner_user):
        """Get prescriptions for a pet."""
        from apps.ai_assistant.tools import get_pet_prescriptions

        result = get_pet_prescriptions(
            pet_id=prescription.pet.id,
            user_id=owner_user.id
        )

        assert 'prescriptions' in result
        assert len(result['prescriptions']) == 1
        assert result['prescriptions'][0]['medication_name'] == 'Methimazole'

    def test_get_pet_prescriptions_includes_expired(self, prescription, owner_user):
        """Get prescriptions including expired ones."""
        from apps.ai_assistant.tools import get_pet_prescriptions

        # Make prescription expired
        prescription.expiration_date = date.today() - timedelta(days=1)
        prescription.status = 'expired'
        prescription.save()

        result = get_pet_prescriptions(
            pet_id=prescription.pet.id,
            user_id=owner_user.id,
            include_expired=True
        )

        assert len(result['prescriptions']) == 1

    def test_check_refill_eligibility(self, prescription, owner_user):
        """Check refill eligibility."""
        from apps.ai_assistant.tools import check_refill_eligibility

        result = check_refill_eligibility(
            prescription_id=prescription.id,
            user_id=owner_user.id
        )

        assert result['can_refill'] is True
        assert result['refills_remaining'] == 3

    def test_check_refill_eligibility_no_refills(self, prescription, owner_user):
        """Check refill eligibility when no refills."""
        from apps.ai_assistant.tools import check_refill_eligibility

        prescription.refills_remaining = 0
        prescription.save()

        result = check_refill_eligibility(
            prescription_id=prescription.id,
            user_id=owner_user.id
        )

        assert result['can_refill'] is False
        assert 'No refills remaining' in result['reason']

    def test_request_refill(self, prescription, owner_user):
        """Request a prescription refill."""
        from apps.ai_assistant.tools import request_refill

        result = request_refill(
            prescription_id=prescription.id,
            user_id=owner_user.id,
            notes='Running low'
        )

        assert result['success'] is True
        assert 'request_id' in result

    def test_request_refill_controlled_substance(self, owner_user, vet_profile, pet, controlled_medication):
        """Cannot request refill for controlled substance online."""
        from apps.pharmacy.models import Prescription
        from apps.ai_assistant.tools import request_refill

        rx = Prescription.objects.create(
            pet=pet,
            owner=owner_user,
            prescribing_vet=vet_profile,
            medication=controlled_medication,
            strength='50mg',
            dosage_form='tablet',
            quantity=30,
            dosage='1 tablet',
            frequency='as needed',
            duration='30 days',
            refills_authorized=1,
            refills_remaining=1,
            prescribed_date=date.today(),
            expiration_date=date.today() + timedelta(days=30)
        )

        result = request_refill(
            prescription_id=rx.id,
            user_id=owner_user.id
        )

        assert result['success'] is False
        assert 'controlled' in result['error'].lower()

    def test_get_medication_info(self, medication):
        """Get medication information."""
        from apps.ai_assistant.tools import get_medication_info

        result = get_medication_info(medication_name='Methimazole')

        assert 'medication' in result
        assert result['medication']['name'] == 'Methimazole'
        assert 'cat' in result['medication']['species']

    def test_get_refill_status(self, prescription, owner_user):
        """Get status of a refill request."""
        from apps.pharmacy.models import RefillRequest
        from apps.ai_assistant.tools import get_refill_status

        refill = RefillRequest.objects.create(
            prescription=prescription,
            requested_by=owner_user
        )

        result = get_refill_status(
            refill_request_id=refill.id,
            user_id=owner_user.id
        )

        assert result['status'] == 'pending'
        assert 'medication_name' in result


# =============================================================================
# Staff Tools Tests
# =============================================================================

@pytest.mark.django_db
class TestPharmacyStaffTools:
    """Tests for pharmacy staff AI tools."""

    def test_get_pharmacy_queue(self, prescription, staff_profile, owner_user):
        """Get pharmacy queue (staff only)."""
        from apps.pharmacy.models import RefillRequest
        from apps.ai_assistant.tools import get_pharmacy_queue

        RefillRequest.objects.create(
            prescription=prescription,
            requested_by=owner_user
        )

        result = get_pharmacy_queue(user_id=staff_profile.user.id)

        assert 'queue' in result
        assert len(result['queue']) >= 1

    def test_create_prescription_vet_only(self, vet_profile, pet, medication):
        """Create prescription (vet only)."""
        from apps.ai_assistant.tools import create_prescription

        result = create_prescription(
            user_id=vet_profile.user.id,
            pet_id=pet.id,
            medication_id=medication.id,
            strength='5mg',
            quantity=60,
            dosage='1 tablet',
            frequency='twice daily',
            duration='30 days',
            refills=3
        )

        assert result['success'] is True
        assert 'prescription_id' in result

    def test_create_prescription_non_vet_denied(self, staff_profile, pet, medication):
        """Non-vet cannot create prescription."""
        from apps.ai_assistant.tools import create_prescription

        result = create_prescription(
            user_id=staff_profile.user.id,
            pet_id=pet.id,
            medication_id=medication.id,
            strength='5mg',
            quantity=60,
            dosage='1 tablet',
            frequency='twice daily'
        )

        assert 'error' in result
        assert 'authorized' in result['error'].lower() or 'prescribe' in result['error'].lower()


# =============================================================================
# View Tests
# =============================================================================

@pytest.mark.django_db
class TestPrescriptionViews:
    """Tests for prescription views."""

    def test_prescription_list_requires_login(self, client):
        """Prescription list requires authentication."""
        from django.urls import reverse

        response = client.get(reverse('pharmacy:prescription_list'))
        assert response.status_code == 302
        assert 'login' in response.url

    def test_prescription_list_shows_user_prescriptions(self, client, prescription, owner_user):
        """Prescription list shows only user's prescriptions."""
        from django.urls import reverse

        client.force_login(owner_user)
        response = client.get(reverse('pharmacy:prescription_list'))

        assert response.status_code == 200
        assert prescription.medication.name in response.content.decode()

    def test_prescription_detail_requires_login(self, client, prescription):
        """Prescription detail requires authentication."""
        from django.urls import reverse

        response = client.get(
            reverse('pharmacy:prescription_detail', kwargs={'pk': prescription.pk})
        )
        assert response.status_code == 302
        assert 'login' in response.url

    def test_prescription_detail_shows_prescription(self, client, prescription, owner_user):
        """Prescription detail shows prescription info."""
        from django.urls import reverse

        client.force_login(owner_user)
        response = client.get(
            reverse('pharmacy:prescription_detail', kwargs={'pk': prescription.pk})
        )

        assert response.status_code == 200
        assert prescription.medication.name in response.content.decode()
        assert prescription.dosage in response.content.decode()

    def test_prescription_detail_denies_other_user(self, client, prescription, staff_user):
        """Cannot view another user's prescription."""
        from django.urls import reverse

        client.force_login(staff_user)
        response = client.get(
            reverse('pharmacy:prescription_detail', kwargs={'pk': prescription.pk})
        )

        assert response.status_code == 404


@pytest.mark.django_db
class TestRefillRequestViews:
    """Tests for refill request views."""

    def test_refill_request_create_requires_login(self, client, prescription):
        """Refill request requires authentication."""
        from django.urls import reverse

        response = client.post(
            reverse('pharmacy:request_refill', kwargs={'prescription_id': prescription.pk})
        )
        assert response.status_code == 302
        assert 'login' in response.url

    def test_refill_request_creates_request(self, client, prescription, owner_user):
        """Can create refill request."""
        from django.urls import reverse
        from apps.pharmacy.models import RefillRequest

        client.force_login(owner_user)
        response = client.post(
            reverse('pharmacy:request_refill', kwargs={'prescription_id': prescription.pk}),
            {'notes': 'Running low on medication'}
        )

        # Should redirect to prescription detail or refills list
        assert response.status_code in [302, 200]
        assert RefillRequest.objects.filter(
            prescription=prescription,
            requested_by=owner_user
        ).exists()

    def test_refill_list_shows_user_refills(self, client, prescription, owner_user):
        """Refill list shows user's refill requests."""
        from django.urls import reverse
        from apps.pharmacy.models import RefillRequest

        RefillRequest.objects.create(
            prescription=prescription,
            requested_by=owner_user,
            notes='Test refill'
        )

        client.force_login(owner_user)
        response = client.get(reverse('pharmacy:refill_list'))

        assert response.status_code == 200
        assert prescription.medication.name in response.content.decode()

    def test_refill_detail_shows_status(self, client, prescription, owner_user):
        """Refill detail shows status."""
        from django.urls import reverse
        from apps.pharmacy.models import RefillRequest

        refill = RefillRequest.objects.create(
            prescription=prescription,
            requested_by=owner_user
        )

        client.force_login(owner_user)
        response = client.get(
            reverse('pharmacy:refill_detail', kwargs={'pk': refill.pk})
        )

        assert response.status_code == 200
        assert 'pending' in response.content.decode().lower() or 'Pending' in response.content.decode()
