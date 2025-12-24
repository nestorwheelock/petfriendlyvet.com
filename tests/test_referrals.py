"""Tests for S-025 Referral Network & Visiting Specialists.

Tests validate referral network functionality:
- Specialist directory management
- Visiting specialist schedules
- Outbound referrals to specialists
- Inbound referrals from other vets
- Referral documents and notes
- Visiting appointments
- AI tools for referral management
"""
import pytest
from decimal import Decimal
from datetime import date, time, timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def owner_user(db):
    """Create a pet owner user."""
    return User.objects.create_user(
        username='owner_referral',
        email='owner@example.com',
        password='testpass123'
    )


@pytest.fixture
def staff_user(db):
    """Create a staff user."""
    return User.objects.create_user(
        username='staff_referral',
        email='staff@petfriendly.com',
        password='testpass123',
        is_staff=True
    )


@pytest.fixture
def vet_user(db):
    """Create a veterinarian user for referrals."""
    return User.objects.create_user(
        username='vet_referral',
        email='vet@otherclinic.com',
        password='testpass123'
    )


@pytest.fixture
def pet(db, owner_user):
    """Create a pet for referral tests."""
    from apps.pets.models import Pet
    return Pet.objects.create(
        owner=owner_user,
        name='Max',
        species='dog',
        breed='Golden Retriever',
        gender='male',
        date_of_birth=date.today() - timedelta(days=365 * 8)
    )


@pytest.fixture
def specialist(db):
    """Create a specialist veterinarian."""
    from apps.referrals.models import Specialist
    return Specialist.objects.create(
        name='Dr. Ana Martínez',
        specialty='oncology',
        credentials='DACVIM (Oncology)',
        is_facility=False,
        clinic_name='Centro Oncológico Veterinario Cancún',
        email='ana.martinez@oncoved.mx',
        phone='998-884-5678',
        address='Av. Bonampak 123, Zona Hotelera',
        city='Cancún',
        species_treated=['dog', 'cat'],
        services=['consultation', 'chemotherapy', 'surgery'],
        is_active=True
    )


@pytest.fixture
def visiting_specialist(db):
    """Create a visiting specialist who comes to Pet-Friendly."""
    from apps.referrals.models import Specialist
    return Specialist.objects.create(
        name='Dr. María López',
        specialty='cardiology',
        credentials='Diplomate ACVIM (Cardiology)',
        is_facility=False,
        email='maria.lopez@cardiovet.mx',
        phone='984-873-2345',
        address='Playa del Carmen',
        city='Playa del Carmen',
        is_visiting=True,
        visiting_services=['cardiac_consultation', 'echocardiogram', 'ecg'],
        equipment_provided=['portable_ultrasound', 'ecg_machine'],
        revenue_share_percent=Decimal('30.00'),
        species_treated=['dog', 'cat'],
        is_active=True
    )


@pytest.fixture
def emergency_hospital(db):
    """Create an emergency hospital facility."""
    from apps.referrals.models import Specialist
    return Specialist.objects.create(
        name='Hospital Veterinario 24 Horas Cancún',
        specialty='emergency',
        is_facility=True,
        phone='998-999-0000',
        address='Av. Kukulcán Km 10',
        city='Cancún',
        is_24_hours=True,
        species_treated=['dog', 'cat', 'exotic'],
        services=['emergency', 'critical_care', 'surgery'],
        is_active=True
    )


@pytest.fixture
def imaging_center(db):
    """Create an imaging center facility."""
    from apps.referrals.models import Specialist
    return Specialist.objects.create(
        name='Centro de Diagnóstico por Imagen',
        specialty='imaging',
        is_facility=True,
        phone='998-888-1234',
        address='Av. Nichupté 456',
        city='Cancún',
        species_treated=['dog', 'cat'],
        services=['xray', 'ultrasound', 'ct_scan', 'mri'],
        is_active=True
    )


@pytest.fixture
def visiting_schedule(db, visiting_specialist):
    """Create a visiting schedule."""
    from apps.referrals.models import VisitingSchedule
    visit_date = timezone.now().date() + timedelta(days=7)
    return VisitingSchedule.objects.create(
        specialist=visiting_specialist,
        date=visit_date,
        start_time=time(9, 0),
        end_time=time(15, 0),
        max_appointments=6,
        services_available=['cardiac_consultation', 'echocardiogram'],
        equipment_bringing=['portable_ultrasound'],
        status='scheduled'
    )


@pytest.fixture
def outbound_referral(db, pet, owner_user, specialist, staff_user):
    """Create an outbound referral to a specialist."""
    from apps.referrals.models import Referral
    return Referral.objects.create(
        direction='outbound',
        pet=pet,
        owner=owner_user,
        specialist=specialist,
        reason='Suspicious mass evaluation - possible mast cell tumor recurrence',
        clinical_summary='8-year-old MN Golden Retriever with firm subcutaneous mass on left flank',
        urgency='urgent',
        requested_services=['consultation', 'staging'],
        status='sent',
        referred_by=staff_user,
        sent_at=timezone.now()
    )


@pytest.fixture
def inbound_referral(db, pet, owner_user, staff_user):
    """Create an inbound referral from another vet."""
    from apps.referrals.models import Referral
    return Referral.objects.create(
        direction='inbound',
        pet=pet,
        owner=owner_user,
        referring_vet_name='Dr. Carlos Vega',
        referring_clinic='Veterinaria Costa del Sol',
        referring_contact='carlos.vega@costavet.mx',
        reason='Cytology services requested',
        clinical_summary='Fine needle aspirate of splenic mass',
        urgency='routine',
        requested_services=['cytology'],
        status='received',
        referred_by=staff_user
    )


@pytest.fixture
def professional_account(db, vet_user):
    """Create a professional account for B2B referrals."""
    from apps.billing.models import ProfessionalAccount
    return ProfessionalAccount.objects.create(
        owner=vet_user,
        business_name='Veterinaria Costa del Sol',
        rfc='VCS201234567',
        contact_name='Dr. Carlos Vega',
        phone='998-765-4321',
        email='carlos.vega@costavet.mx',
        payment_terms='net30',
        credit_limit=Decimal('15000.00'),
        is_approved=True
    )


@pytest.fixture
def invoice(db, owner_user, pet):
    """Create an invoice for billing integration."""
    from apps.billing.models import Invoice
    return Invoice.objects.create(
        owner=owner_user,
        pet=pet,
        subtotal=Decimal('2500.00'),
        tax_amount=Decimal('400.00'),
        total=Decimal('2900.00'),
        due_date=date.today() + timedelta(days=30)
    )


# =============================================================================
# Specialist Model Tests
# =============================================================================

@pytest.mark.django_db
class TestSpecialistModel:
    """Tests for the Specialist model."""

    def test_create_specialist_individual(self, db):
        """Can create an individual specialist."""
        from apps.referrals.models import Specialist

        specialist = Specialist.objects.create(
            name='Dr. Roberto Sánchez',
            specialty='surgery',
            credentials='Diplomate ACVS',
            is_facility=False,
            clinic_name='Hospital Quirúrgico Veterinario',
            email='roberto.sanchez@hvq.mx',
            phone='998-555-1234',
            address='Calle Principal 789',
            city='Cancún',
            species_treated=['dog', 'cat'],
            services=['orthopedic_surgery', 'soft_tissue_surgery']
        )

        assert specialist.id is not None
        assert specialist.name == 'Dr. Roberto Sánchez'
        assert specialist.specialty == 'surgery'
        assert specialist.is_facility is False
        assert specialist.is_visiting is False
        assert specialist.is_active is True

    def test_create_specialist_facility(self, emergency_hospital):
        """Can create a facility specialist (hospital/lab)."""
        assert emergency_hospital.is_facility is True
        assert emergency_hospital.specialty == 'emergency'
        assert emergency_hospital.is_24_hours is True

    def test_create_visiting_specialist(self, visiting_specialist):
        """Can create a visiting specialist."""
        assert visiting_specialist.is_visiting is True
        assert 'cardiac_consultation' in visiting_specialist.visiting_services
        assert 'portable_ultrasound' in visiting_specialist.equipment_provided
        assert visiting_specialist.revenue_share_percent == Decimal('30.00')

    def test_specialist_string_representation(self, specialist):
        """Specialist string representation is correct."""
        assert str(specialist) == 'Dr. Ana Martínez'

    def test_specialist_specialty_choices(self, db):
        """Specialist supports all specialty types."""
        from apps.referrals.models import Specialist

        specialties = [
            'oncology', 'cardiology', 'orthopedics', 'ophthalmology',
            'dermatology', 'neurology', 'surgery', 'internal_medicine',
            'emergency', 'imaging', 'laboratory', 'rehabilitation',
            'behavior', 'exotics', 'dentistry', 'other'
        ]

        for specialty in specialties:
            specialist = Specialist.objects.create(
                name=f'Dr. Test {specialty}',
                specialty=specialty,
                phone='555-1234',
                address='Test Address',
                city='Test City'
            )
            assert specialist.specialty == specialty

    def test_specialist_default_values(self, db):
        """Specialist has correct default values."""
        from apps.referrals.models import Specialist

        specialist = Specialist.objects.create(
            name='Dr. Test Default',
            specialty='cardiology',
            phone='555-0000',
            address='Test',
            city='Test'
        )

        assert specialist.is_facility is False
        assert specialist.is_visiting is False
        assert specialist.is_24_hours is False
        assert specialist.is_active is True
        assert specialist.relationship_status == 'active'
        assert specialist.total_referrals_sent == 0
        assert specialist.total_referrals_received == 0
        assert specialist.hours == {}
        assert specialist.services == []
        assert specialist.species_treated == []

    def test_specialist_location_fields(self, db):
        """Can set location with GPS coordinates."""
        from apps.referrals.models import Specialist

        specialist = Specialist.objects.create(
            name='Dr. GPS Test',
            specialty='imaging',
            phone='555-1111',
            address='Av. Kukulcán',
            city='Cancún',
            latitude=Decimal('21.16056'),
            longitude=Decimal('-86.85167'),
            distance_km=25.5
        )

        assert specialist.latitude == Decimal('21.16056')
        assert specialist.longitude == Decimal('-86.85167')
        assert specialist.distance_km == 25.5

    def test_specialist_referral_stats(self, specialist):
        """Specialist tracks referral statistics."""
        specialist.total_referrals_sent = 10
        specialist.total_referrals_received = 5
        specialist.average_rating = Decimal('4.75')
        specialist.save()

        specialist.refresh_from_db()
        assert specialist.total_referrals_sent == 10
        assert specialist.total_referrals_received == 5
        assert specialist.average_rating == Decimal('4.75')


# =============================================================================
# VisitingSchedule Model Tests
# =============================================================================

@pytest.mark.django_db
class TestVisitingScheduleModel:
    """Tests for the VisitingSchedule model."""

    def test_create_visiting_schedule(self, visiting_specialist):
        """Can create a visiting schedule."""
        from apps.referrals.models import VisitingSchedule

        visit_date = timezone.now().date() + timedelta(days=14)
        schedule = VisitingSchedule.objects.create(
            specialist=visiting_specialist,
            date=visit_date,
            start_time=time(9, 0),
            end_time=time(17, 0),
            max_appointments=8,
            services_available=['echocardiogram', 'cardiac_consultation'],
            status='scheduled'
        )

        assert schedule.id is not None
        assert schedule.specialist == visiting_specialist
        assert schedule.date == visit_date
        assert schedule.start_time == time(9, 0)
        assert schedule.end_time == time(17, 0)
        assert schedule.max_appointments == 8
        assert schedule.appointments_booked == 0
        assert schedule.status == 'scheduled'

    def test_visiting_schedule_recurring(self, visiting_specialist):
        """Can create recurring visiting schedule."""
        from apps.referrals.models import VisitingSchedule

        schedule = VisitingSchedule.objects.create(
            specialist=visiting_specialist,
            date=timezone.now().date() + timedelta(days=7),
            start_time=time(10, 0),
            end_time=time(14, 0),
            is_recurring=True,
            recurrence_pattern='monthly_first_sunday'
        )

        assert schedule.is_recurring is True
        assert schedule.recurrence_pattern == 'monthly_first_sunday'

    def test_visiting_schedule_status_choices(self, visiting_specialist):
        """Visiting schedule supports all status types."""
        from apps.referrals.models import VisitingSchedule

        statuses = ['scheduled', 'confirmed', 'cancelled', 'completed']

        for status in statuses:
            schedule = VisitingSchedule.objects.create(
                specialist=visiting_specialist,
                date=timezone.now().date() + timedelta(days=30),
                start_time=time(9, 0),
                end_time=time(15, 0),
                status=status
            )
            assert schedule.status == status

    def test_visiting_schedule_cancellation(self, visiting_schedule):
        """Can cancel a visiting schedule with reason."""
        visiting_schedule.status = 'cancelled'
        visiting_schedule.cancellation_reason = 'Specialist unavailable due to illness'
        visiting_schedule.save()

        visiting_schedule.refresh_from_db()
        assert visiting_schedule.status == 'cancelled'
        assert 'illness' in visiting_schedule.cancellation_reason

    def test_visiting_schedule_equipment(self, visiting_schedule):
        """Visiting schedule tracks equipment being brought."""
        visiting_schedule.equipment_bringing = ['portable_ultrasound', 'ecg_machine', 'bp_monitor']
        visiting_schedule.save()

        visiting_schedule.refresh_from_db()
        assert len(visiting_schedule.equipment_bringing) == 3
        assert 'ecg_machine' in visiting_schedule.equipment_bringing

    def test_visiting_schedule_appointment_tracking(self, visiting_schedule):
        """Can track appointment bookings."""
        visiting_schedule.appointments_booked = 3
        visiting_schedule.save()

        visiting_schedule.refresh_from_db()
        assert visiting_schedule.appointments_booked == 3
        assert visiting_schedule.max_appointments == 6

    def test_visiting_schedule_string_representation(self, visiting_schedule):
        """Schedule has useful string representation."""
        expected = f"{visiting_schedule.specialist.name} - {visiting_schedule.date}"
        assert str(visiting_schedule) == expected


# =============================================================================
# Referral Model Tests
# =============================================================================

@pytest.mark.django_db
class TestReferralModel:
    """Tests for the Referral model."""

    def test_create_outbound_referral(self, pet, owner_user, specialist, staff_user):
        """Can create an outbound referral to specialist."""
        from apps.referrals.models import Referral

        referral = Referral.objects.create(
            direction='outbound',
            pet=pet,
            owner=owner_user,
            specialist=specialist,
            reason='Suspected cardiac disease - murmur detected',
            clinical_summary='5-year-old FS Cavalier with Grade IV/VI heart murmur',
            urgency='routine',
            requested_services=['cardiac_consultation', 'echocardiogram'],
            status='draft',
            referred_by=staff_user
        )

        assert referral.id is not None
        assert referral.referral_number is not None
        assert referral.direction == 'outbound'
        assert referral.pet == pet
        assert referral.specialist == specialist
        assert referral.status == 'draft'

    def test_create_inbound_referral(self, pet, owner_user, staff_user):
        """Can create an inbound referral from another vet."""
        from apps.referrals.models import Referral

        referral = Referral.objects.create(
            direction='inbound',
            pet=pet,
            owner=owner_user,
            referring_vet_name='Dr. Juan López',
            referring_clinic='Clínica Veterinaria Norte',
            referring_contact='juan.lopez@cvn.mx',
            reason='Lab work - CBC and chemistry panel',
            urgency='routine',
            requested_services=['blood_work'],
            status='received',
            referred_by=staff_user
        )

        assert referral.direction == 'inbound'
        assert referral.referring_vet_name == 'Dr. Juan López'
        assert referral.specialist is None

    def test_referral_auto_generates_number(self, pet, owner_user, specialist, staff_user):
        """Referral automatically generates referral number."""
        from apps.referrals.models import Referral

        referral = Referral.objects.create(
            direction='outbound',
            pet=pet,
            owner=owner_user,
            specialist=specialist,
            reason='Test referral',
            referred_by=staff_user
        )

        assert referral.referral_number is not None
        assert len(referral.referral_number) > 0

    def test_referral_status_choices(self, pet, owner_user, specialist, staff_user):
        """Referral supports all status types."""
        from apps.referrals.models import Referral

        statuses = [
            'draft', 'sent', 'received', 'scheduled', 'seen',
            'report_pending', 'completed', 'cancelled', 'declined'
        ]

        for status in statuses:
            referral = Referral.objects.create(
                direction='outbound',
                pet=pet,
                owner=owner_user,
                specialist=specialist,
                reason=f'Test referral for {status}',
                status=status,
                referred_by=staff_user
            )
            assert referral.status == status

    def test_referral_urgency_levels(self, pet, owner_user, specialist, staff_user):
        """Referral supports urgency levels."""
        from apps.referrals.models import Referral

        urgencies = ['routine', 'urgent', 'emergency']

        for urgency in urgencies:
            referral = Referral.objects.create(
                direction='outbound',
                pet=pet,
                owner=owner_user,
                specialist=specialist,
                reason=f'Test {urgency} referral',
                urgency=urgency,
                referred_by=staff_user
            )
            assert referral.urgency == urgency

    def test_referral_specialist_findings(self, outbound_referral):
        """Can record specialist findings and recommendations."""
        outbound_referral.specialist_findings = 'Mass confirmed on ultrasound'
        outbound_referral.specialist_diagnosis = 'Mast cell tumor Grade II'
        outbound_referral.specialist_recommendations = 'Recommend wide surgical excision'
        outbound_referral.follow_up_needed = True
        outbound_referral.follow_up_instructions = 'Recheck in 2 weeks post-surgery'
        outbound_referral.status = 'completed'
        outbound_referral.completed_at = timezone.now()
        outbound_referral.save()

        outbound_referral.refresh_from_db()
        assert 'Mast cell tumor' in outbound_referral.specialist_diagnosis
        assert outbound_referral.follow_up_needed is True

    def test_referral_outcome_tracking(self, outbound_referral):
        """Can track referral outcomes."""
        from apps.referrals.models import Referral

        outcomes = [
            'successful', 'ongoing', 'referred_again', 'no_treatment',
            'client_declined', 'euthanasia', 'unknown'
        ]

        for outcome in outcomes:
            outbound_referral.outcome = outcome
            outbound_referral.save()
            outbound_referral.refresh_from_db()
            assert outbound_referral.outcome == outcome

    def test_referral_satisfaction_ratings(self, outbound_referral):
        """Can record satisfaction and quality ratings."""
        outbound_referral.client_satisfaction = 5
        outbound_referral.quality_rating = 4
        outbound_referral.save()

        outbound_referral.refresh_from_db()
        assert outbound_referral.client_satisfaction == 5
        assert outbound_referral.quality_rating == 4

    def test_referral_billing_integration(self, outbound_referral, invoice):
        """Can link referral to invoice."""
        outbound_referral.invoice = invoice
        outbound_referral.save()

        outbound_referral.refresh_from_db()
        assert outbound_referral.invoice == invoice

    def test_referral_with_professional_account(self, inbound_referral, professional_account):
        """Inbound referral can link to professional B2B account."""
        inbound_referral.referring_professional_account = professional_account
        inbound_referral.save()

        inbound_referral.refresh_from_db()
        assert inbound_referral.referring_professional_account == professional_account
        assert inbound_referral.referring_professional_account.business_name == 'Veterinaria Costa del Sol'

    def test_referral_string_representation(self, outbound_referral):
        """Referral has useful string representation."""
        expected = f"REF-{outbound_referral.referral_number}: {outbound_referral.pet.name} to {outbound_referral.specialist.name}"
        assert str(outbound_referral) == expected

    def test_referral_date_tracking(self, outbound_referral):
        """Can track important dates in referral workflow."""
        now = timezone.now()
        outbound_referral.sent_at = now
        outbound_referral.appointment_date = now + timedelta(days=7)
        outbound_referral.seen_at = now + timedelta(days=7, hours=2)
        outbound_referral.completed_at = now + timedelta(days=14)
        outbound_referral.save()

        outbound_referral.refresh_from_db()
        assert outbound_referral.sent_at is not None
        assert outbound_referral.appointment_date is not None
        assert outbound_referral.seen_at is not None
        assert outbound_referral.completed_at is not None


# =============================================================================
# ReferralDocument Model Tests
# =============================================================================

@pytest.mark.django_db
class TestReferralDocumentModel:
    """Tests for the ReferralDocument model."""

    def test_create_referral_document(self, outbound_referral, staff_user):
        """Can attach document to referral."""
        from apps.referrals.models import ReferralDocument
        from django.core.files.uploadedfile import SimpleUploadedFile

        doc = ReferralDocument.objects.create(
            referral=outbound_referral,
            document_type='referral_letter',
            title='Referral Letter for Max',
            file=SimpleUploadedFile('referral.pdf', b'PDF content'),
            description='Initial referral letter with clinical summary',
            is_outgoing=True,
            uploaded_by=staff_user
        )

        assert doc.id is not None
        assert doc.referral == outbound_referral
        assert doc.document_type == 'referral_letter'
        assert doc.is_outgoing is True

    def test_referral_document_types(self, outbound_referral, staff_user):
        """Document supports all document types."""
        from apps.referrals.models import ReferralDocument
        from django.core.files.uploadedfile import SimpleUploadedFile

        doc_types = [
            'referral_letter', 'medical_history', 'lab_results',
            'imaging', 'specialist_report', 'prescription', 'other'
        ]

        for doc_type in doc_types:
            doc = ReferralDocument.objects.create(
                referral=outbound_referral,
                document_type=doc_type,
                title=f'Test {doc_type}',
                file=SimpleUploadedFile(f'{doc_type}.pdf', b'content'),
                uploaded_by=staff_user
            )
            assert doc.document_type == doc_type

    def test_referral_incoming_document(self, outbound_referral, staff_user):
        """Can add incoming document from specialist."""
        from apps.referrals.models import ReferralDocument
        from django.core.files.uploadedfile import SimpleUploadedFile

        doc = ReferralDocument.objects.create(
            referral=outbound_referral,
            document_type='specialist_report',
            title='Oncology Report',
            file=SimpleUploadedFile('onco_report.pdf', b'PDF content'),
            is_outgoing=False,
            uploaded_by=staff_user
        )

        assert doc.is_outgoing is False

    def test_referral_multiple_documents(self, outbound_referral, staff_user):
        """Can attach multiple documents to referral."""
        from apps.referrals.models import ReferralDocument
        from django.core.files.uploadedfile import SimpleUploadedFile

        docs = [
            ('referral_letter', 'Referral Letter'),
            ('lab_results', 'CBC Results'),
            ('imaging', 'X-ray Images'),
        ]

        for doc_type, title in docs:
            ReferralDocument.objects.create(
                referral=outbound_referral,
                document_type=doc_type,
                title=title,
                file=SimpleUploadedFile(f'{doc_type}.pdf', b'content'),
                uploaded_by=staff_user
            )

        assert outbound_referral.documents.count() == 3


# =============================================================================
# ReferralNote Model Tests
# =============================================================================

@pytest.mark.django_db
class TestReferralNoteModel:
    """Tests for the ReferralNote model."""

    def test_create_referral_note(self, outbound_referral, staff_user):
        """Can add notes to referral."""
        from apps.referrals.models import ReferralNote

        note = ReferralNote.objects.create(
            referral=outbound_referral,
            note='Called specialist office to confirm receipt of referral',
            is_internal=True,
            author=staff_user
        )

        assert note.id is not None
        assert note.referral == outbound_referral
        assert note.is_internal is True

    def test_referral_internal_vs_shared_notes(self, outbound_referral, staff_user):
        """Can distinguish internal vs shared notes."""
        from apps.referrals.models import ReferralNote

        internal_note = ReferralNote.objects.create(
            referral=outbound_referral,
            note='Owner seemed worried about cost',
            is_internal=True,
            author=staff_user
        )

        shared_note = ReferralNote.objects.create(
            referral=outbound_referral,
            note='Patient stable, ready for transport',
            is_internal=False,
            author=staff_user
        )

        assert internal_note.is_internal is True
        assert shared_note.is_internal is False

    def test_referral_multiple_notes(self, outbound_referral, staff_user):
        """Can add multiple notes to track conversation."""
        from apps.referrals.models import ReferralNote

        notes = [
            'Referral sent to specialist',
            'Specialist confirmed receipt',
            'Appointment scheduled for Monday',
            'Owner notified of appointment'
        ]

        for note_text in notes:
            ReferralNote.objects.create(
                referral=outbound_referral,
                note=note_text,
                author=staff_user
            )

        assert outbound_referral.notes_list.count() == 4


# =============================================================================
# VisitingAppointment Model Tests
# =============================================================================

@pytest.mark.django_db
class TestVisitingAppointmentModel:
    """Tests for the VisitingAppointment model."""

    def test_create_visiting_appointment(self, visiting_schedule, visiting_specialist, pet, owner_user):
        """Can book appointment with visiting specialist."""
        from apps.referrals.models import VisitingAppointment

        appointment = VisitingAppointment.objects.create(
            schedule=visiting_schedule,
            specialist=visiting_specialist,
            pet=pet,
            owner=owner_user,
            appointment_time=time(10, 0),
            duration_minutes=45,
            service='cardiac_consultation',
            reason='Heart murmur evaluation'
        )

        assert appointment.id is not None
        assert appointment.schedule == visiting_schedule
        assert appointment.specialist == visiting_specialist
        assert appointment.pet == pet
        assert appointment.status == 'scheduled'

    def test_visiting_appointment_status_workflow(self, visiting_schedule, visiting_specialist, pet, owner_user):
        """Appointment goes through proper status workflow."""
        from apps.referrals.models import VisitingAppointment

        appointment = VisitingAppointment.objects.create(
            schedule=visiting_schedule,
            specialist=visiting_specialist,
            pet=pet,
            owner=owner_user,
            appointment_time=time(11, 0),
            service='echocardiogram',
            reason='Follow-up echo'
        )

        statuses = ['scheduled', 'confirmed', 'checked_in', 'in_progress', 'completed']

        for status in statuses:
            appointment.status = status
            appointment.save()
            appointment.refresh_from_db()
            assert appointment.status == status

    def test_visiting_appointment_results(self, visiting_schedule, visiting_specialist, pet, owner_user):
        """Can record appointment results."""
        from apps.referrals.models import VisitingAppointment

        appointment = VisitingAppointment.objects.create(
            schedule=visiting_schedule,
            specialist=visiting_specialist,
            pet=pet,
            owner=owner_user,
            appointment_time=time(9, 0),
            service='echocardiogram',
            reason='Cardiac screening'
        )

        appointment.findings = 'Mild mitral regurgitation identified'
        appointment.diagnosis = 'Early stage MMVD (Stage B1)'
        appointment.recommendations = 'No treatment needed yet. Recheck in 6 months.'
        appointment.follow_up_needed = True
        appointment.follow_up_notes = 'Schedule follow-up echo in 6 months'
        appointment.status = 'completed'
        appointment.save()

        appointment.refresh_from_db()
        assert 'mitral regurgitation' in appointment.findings
        assert 'MMVD' in appointment.diagnosis
        assert appointment.follow_up_needed is True

    def test_visiting_appointment_billing(self, visiting_schedule, visiting_specialist, pet, owner_user, invoice):
        """Can link appointment to billing."""
        from apps.referrals.models import VisitingAppointment

        appointment = VisitingAppointment.objects.create(
            schedule=visiting_schedule,
            specialist=visiting_specialist,
            pet=pet,
            owner=owner_user,
            appointment_time=time(13, 0),
            service='cardiac_consultation',
            reason='Initial consultation',
            fee=Decimal('2500.00'),
            pet_friendly_share=Decimal('750.00'),  # 30% share
            invoice=invoice
        )

        assert appointment.fee == Decimal('2500.00')
        assert appointment.pet_friendly_share == Decimal('750.00')
        assert appointment.invoice == invoice

    def test_visiting_appointment_from_referral(self, visiting_schedule, visiting_specialist, pet, owner_user, outbound_referral):
        """Visiting appointment can be linked to referral."""
        from apps.referrals.models import VisitingAppointment

        appointment = VisitingAppointment.objects.create(
            schedule=visiting_schedule,
            specialist=visiting_specialist,
            pet=pet,
            owner=owner_user,
            appointment_time=time(14, 0),
            service='oncology_consultation',
            reason='Follow-up to referral',
            referral=outbound_referral
        )

        assert appointment.referral == outbound_referral

    def test_visiting_appointment_no_show(self, visiting_schedule, visiting_specialist, pet, owner_user):
        """Can mark appointment as no-show."""
        from apps.referrals.models import VisitingAppointment

        appointment = VisitingAppointment.objects.create(
            schedule=visiting_schedule,
            specialist=visiting_specialist,
            pet=pet,
            owner=owner_user,
            appointment_time=time(15, 0),
            service='consultation',
            reason='Test'
        )

        appointment.status = 'no_show'
        appointment.notes = 'Owner did not show up. Called but no answer.'
        appointment.save()

        assert appointment.status == 'no_show'

    def test_visiting_appointment_string_representation(self, visiting_schedule, visiting_specialist, pet, owner_user):
        """Appointment has useful string representation."""
        from apps.referrals.models import VisitingAppointment

        appointment = VisitingAppointment.objects.create(
            schedule=visiting_schedule,
            specialist=visiting_specialist,
            pet=pet,
            owner=owner_user,
            appointment_time=time(10, 0),
            service='echocardiogram',
            reason='Echo check'
        )

        expected = f"{pet.name} with {visiting_specialist.name} at {appointment.appointment_time}"
        assert str(appointment) == expected


# =============================================================================
# AI Tools Tests
# =============================================================================

@pytest.mark.django_db
class TestFindSpecialistTool:
    """Tests for the find_specialist AI tool."""

    def test_find_specialist_by_specialty(self, specialist, emergency_hospital, imaging_center):
        """Can find specialists by specialty type."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('find_specialist')
        assert tool is not None

        result = tool.handler(specialty='oncology')
        assert result['success'] is True
        assert len(result['specialists']) >= 1
        assert any(s['name'] == 'Dr. Ana Martínez' for s in result['specialists'])

    def test_find_specialist_by_species(self, specialist, visiting_specialist):
        """Can filter specialists by species treated."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('find_specialist')
        result = tool.handler(specialty='cardiology', species='dog')

        assert result['success'] is True
        for spec in result['specialists']:
            assert 'dog' in spec['species_treated']

    def test_find_emergency_specialists(self, emergency_hospital):
        """Can find 24-hour emergency facilities."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('find_specialist')
        result = tool.handler(specialty='emergency', urgent=True)

        assert result['success'] is True
        assert any(s['is_24_hours'] for s in result['specialists'])

    def test_find_visiting_specialists(self, visiting_specialist, visiting_schedule):
        """Can find specialists who visit Pet-Friendly."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('find_specialist')
        result = tool.handler(specialty='cardiology')

        assert result['success'] is True
        visiting = [s for s in result['specialists'] if s.get('is_visiting')]
        assert len(visiting) >= 1


@pytest.mark.django_db
class TestGetVisitingScheduleTool:
    """Tests for the get_visiting_schedule AI tool."""

    def test_get_upcoming_schedules(self, visiting_specialist, visiting_schedule):
        """Can get upcoming visiting schedules."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('get_visiting_schedule')
        assert tool is not None

        result = tool.handler()
        assert result['success'] is True
        assert len(result['schedules']) >= 1

    def test_get_schedules_by_specialty(self, visiting_specialist, visiting_schedule):
        """Can filter schedules by specialty."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('get_visiting_schedule')
        result = tool.handler(specialty='cardiology')

        assert result['success'] is True
        for schedule in result['schedules']:
            assert schedule['specialty'] == 'cardiology'

    def test_get_schedules_by_date_range(self, visiting_specialist, visiting_schedule):
        """Can filter schedules by date range."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('get_visiting_schedule')
        date_from = timezone.now().date().isoformat()
        date_to = (timezone.now().date() + timedelta(days=30)).isoformat()

        result = tool.handler(date_from=date_from, date_to=date_to)
        assert result['success'] is True


@pytest.mark.django_db
class TestCreateReferralTool:
    """Tests for the create_referral AI tool."""

    def test_create_referral_via_tool(self, pet, specialist, staff_user):
        """Can create referral via AI tool."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('create_referral')
        assert tool is not None

        result = tool.handler(
            pet_id=pet.id,
            specialist_id=specialist.id,
            reason='Suspicious mass evaluation',
            urgency='urgent',
            services_requested=['consultation', 'staging'],
            user=staff_user
        )

        assert result['success'] is True
        assert 'referral_number' in result
        assert result['status'] == 'draft'

    def test_create_referral_with_clinical_summary(self, pet, specialist, staff_user):
        """Can create referral with clinical summary."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('create_referral')
        result = tool.handler(
            pet_id=pet.id,
            specialist_id=specialist.id,
            reason='Cancer screening',
            clinical_summary='8yo Golden with history of MCT removed 2 years ago',
            user=staff_user
        )

        assert result['success'] is True


@pytest.mark.django_db
class TestBookVisitingSpecialistTool:
    """Tests for the book_visiting_specialist AI tool."""

    def test_book_visiting_appointment(self, pet, visiting_schedule, owner_user):
        """Can book appointment with visiting specialist."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('book_visiting_specialist')
        assert tool is not None

        result = tool.handler(
            pet_id=pet.id,
            schedule_id=visiting_schedule.id,
            service='echocardiogram',
            reason='Heart murmur evaluation',
            preferred_time='10:00',
            user=owner_user
        )

        assert result['success'] is True
        assert 'appointment_id' in result
        assert result['appointment_time'] is not None

    def test_book_when_schedule_full(self, pet, visiting_schedule, owner_user):
        """Cannot book when schedule is at capacity."""
        from apps.ai_assistant.tools import ToolRegistry

        visiting_schedule.appointments_booked = visiting_schedule.max_appointments
        visiting_schedule.save()

        tool = ToolRegistry.get_tool('book_visiting_specialist')
        result = tool.handler(
            pet_id=pet.id,
            schedule_id=visiting_schedule.id,
            service='consultation',
            user=owner_user
        )

        assert result['success'] is False
        assert 'full' in result['message'].lower() or 'capacity' in result['message'].lower()


@pytest.mark.django_db
class TestUpdateReferralStatusTool:
    """Tests for the update_referral_status AI tool."""

    def test_update_referral_status(self, outbound_referral, staff_user):
        """Can update referral status."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('update_referral_status')
        assert tool is not None

        result = tool.handler(
            referral_id=outbound_referral.id,
            status='received',
            notes='Specialist confirmed receipt of referral',
            user=staff_user
        )

        assert result['success'] is True
        outbound_referral.refresh_from_db()
        assert outbound_referral.status == 'received'

    def test_update_status_to_completed(self, outbound_referral, staff_user):
        """Can mark referral as completed."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('update_referral_status')
        result = tool.handler(
            referral_id=outbound_referral.id,
            status='completed',
            notes='Treatment successful. Owner satisfied.',
            user=staff_user
        )

        assert result['success'] is True
        outbound_referral.refresh_from_db()
        assert outbound_referral.status == 'completed'
        assert outbound_referral.completed_at is not None


@pytest.mark.django_db
class TestRecordSpecialistReportTool:
    """Tests for the record_specialist_report AI tool."""

    def test_record_specialist_report(self, outbound_referral, staff_user):
        """Can record specialist findings and recommendations."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('record_specialist_report')
        assert tool is not None

        result = tool.handler(
            referral_id=outbound_referral.id,
            findings='Mass confirmed as mast cell tumor on cytology',
            diagnosis='Mast cell tumor, Grade II',
            recommendations='Recommend wide surgical excision followed by adjuvant chemotherapy',
            user=staff_user
        )

        assert result['success'] is True
        outbound_referral.refresh_from_db()
        assert 'mast cell tumor' in outbound_referral.specialist_findings
        assert 'Grade II' in outbound_referral.specialist_diagnosis


@pytest.mark.django_db
class TestGetReferralStatusTool:
    """Tests for the get_referral_status AI tool."""

    def test_get_referral_status(self, outbound_referral):
        """Can check referral status."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('get_referral_status')
        assert tool is not None

        result = tool.handler(referral_id=outbound_referral.id)

        assert result['success'] is True
        assert result['referral_number'] == outbound_referral.referral_number
        assert result['status'] == outbound_referral.status
        assert result['pet_name'] == outbound_referral.pet.name


# =============================================================================
# Integration Tests
# =============================================================================

@pytest.mark.django_db
class TestReferralWorkflow:
    """Integration tests for complete referral workflows."""

    def test_outbound_referral_complete_workflow(self, pet, owner_user, specialist, staff_user):
        """Test complete outbound referral workflow from creation to completion."""
        from apps.referrals.models import Referral, ReferralDocument, ReferralNote

        # 1. Create referral
        referral = Referral.objects.create(
            direction='outbound',
            pet=pet,
            owner=owner_user,
            specialist=specialist,
            reason='Oncology consultation',
            clinical_summary='Suspicious mass on left flank',
            urgency='urgent',
            status='draft',
            referred_by=staff_user
        )

        assert referral.status == 'draft'

        # 2. Add documents
        from django.core.files.uploadedfile import SimpleUploadedFile
        ReferralDocument.objects.create(
            referral=referral,
            document_type='referral_letter',
            title='Referral Letter',
            file=SimpleUploadedFile('letter.pdf', b'content'),
            uploaded_by=staff_user
        )

        # 3. Send referral
        referral.status = 'sent'
        referral.sent_at = timezone.now()
        referral.save()

        # 4. Add note about sending
        ReferralNote.objects.create(
            referral=referral,
            note='Referral sent via email',
            author=staff_user
        )

        # 5. Specialist receives
        referral.status = 'received'
        referral.save()

        # 6. Appointment scheduled
        referral.status = 'scheduled'
        referral.appointment_date = timezone.now() + timedelta(days=5)
        referral.save()

        # 7. Patient seen
        referral.status = 'seen'
        referral.seen_at = timezone.now()
        referral.save()

        # 8. Report received
        referral.specialist_findings = 'Mass confirmed'
        referral.specialist_diagnosis = 'MCT Grade II'
        referral.specialist_recommendations = 'Surgery recommended'
        referral.status = 'completed'
        referral.completed_at = timezone.now()
        referral.outcome = 'successful'
        referral.client_satisfaction = 5
        referral.quality_rating = 5
        referral.save()

        # Verify final state
        referral.refresh_from_db()
        assert referral.status == 'completed'
        assert referral.outcome == 'successful'
        assert referral.documents.count() == 1
        assert referral.notes_list.count() == 1
        # Verify through Pet relationship (specialist_referrals, not referrals)
        assert pet.specialist_referrals.filter(pk=referral.pk).exists()

    def test_visiting_specialist_appointment_workflow(self, visiting_specialist, pet, owner_user, staff_user):
        """Test complete visiting specialist appointment workflow."""
        from apps.referrals.models import VisitingSchedule, VisitingAppointment

        # 1. Create visiting schedule
        visit_date = timezone.now().date() + timedelta(days=7)
        schedule = VisitingSchedule.objects.create(
            specialist=visiting_specialist,
            date=visit_date,
            start_time=time(9, 0),
            end_time=time(15, 0),
            max_appointments=6,
            services_available=['echocardiogram', 'cardiac_consultation'],
            status='scheduled'
        )

        # 2. Confirm schedule
        schedule.status = 'confirmed'
        schedule.save()

        # 3. Book appointment
        appointment = VisitingAppointment.objects.create(
            schedule=schedule,
            specialist=visiting_specialist,
            pet=pet,
            owner=owner_user,
            appointment_time=time(10, 0),
            duration_minutes=45,
            service='echocardiogram',
            reason='Heart murmur evaluation',
            fee=Decimal('2500.00'),
            pet_friendly_share=Decimal('750.00')
        )

        schedule.appointments_booked = 1
        schedule.save()

        # 4. Confirm appointment
        appointment.status = 'confirmed'
        appointment.save()

        # 5. Check in
        appointment.status = 'checked_in'
        appointment.save()

        # 6. In progress
        appointment.status = 'in_progress'
        appointment.save()

        # 7. Complete with results
        appointment.status = 'completed'
        appointment.findings = 'Mild MR, LA mildly enlarged'
        appointment.diagnosis = 'Early MMVD Stage B1'
        appointment.recommendations = 'Monitor, recheck in 6 months'
        appointment.follow_up_needed = True
        appointment.follow_up_notes = '6-month recheck echo'
        appointment.save()

        # Verify
        appointment.refresh_from_db()
        assert appointment.status == 'completed'
        assert appointment.follow_up_needed is True
        assert schedule.appointments_booked == 1

    def test_inbound_referral_with_b2b_workflow(self, pet, owner_user, vet_user, professional_account, staff_user):
        """Test inbound referral with B2B professional account."""
        from apps.referrals.models import Referral, ReferralNote

        # 1. Create inbound referral linked to B2B account
        referral = Referral.objects.create(
            direction='inbound',
            pet=pet,
            owner=owner_user,
            referring_vet_name='Dr. Carlos Vega',
            referring_clinic='Veterinaria Costa del Sol',
            referring_contact='carlos.vega@costavet.mx',
            referring_professional_account=professional_account,
            reason='Cytology - splenic mass FNA',
            clinical_summary='5yo FS DSH with incidental splenic mass on ultrasound',
            urgency='routine',
            requested_services=['cytology'],
            status='received',
            referred_by=staff_user
        )

        # 2. Process sample
        ReferralNote.objects.create(
            referral=referral,
            note='Sample received, processing',
            author=staff_user
        )

        referral.status = 'seen'
        referral.seen_at = timezone.now()
        referral.save()

        # 3. Complete with results
        referral.specialist_findings = 'Extramedullary hematopoiesis consistent with nodular hyperplasia'
        referral.specialist_diagnosis = 'Benign nodular hyperplasia'
        referral.specialist_recommendations = 'No treatment needed. Monitor for growth.'
        referral.status = 'completed'
        referral.completed_at = timezone.now()
        referral.outcome = 'successful'
        referral.save()

        # 4. Add thank you note
        ReferralNote.objects.create(
            referral=referral,
            note='Results sent to referring vet. Thank you email sent.',
            is_internal=False,
            author=staff_user
        )

        # Verify
        referral.refresh_from_db()
        assert referral.status == 'completed'
        assert referral.referring_professional_account == professional_account
        assert referral.notes_list.count() == 2


# =============================================================================
# Ordering and Query Tests
# =============================================================================

@pytest.mark.django_db
class TestReferralQueries:
    """Tests for referral queries and ordering."""

    def test_specialists_ordered_by_name(self, specialist, visiting_specialist, emergency_hospital):
        """Specialists are ordered by name."""
        from apps.referrals.models import Specialist

        specialists = list(Specialist.objects.all())
        names = [s.name for s in specialists]
        assert names == sorted(names)

    def test_referrals_ordered_by_date_descending(self, pet, owner_user, specialist, staff_user):
        """Referrals are ordered newest first."""
        from apps.referrals.models import Referral
        import time as time_module

        # Create multiple referrals
        for i in range(3):
            Referral.objects.create(
                direction='outbound',
                pet=pet,
                owner=owner_user,
                specialist=specialist,
                reason=f'Test referral {i}',
                referred_by=staff_user
            )
            time_module.sleep(0.01)  # Ensure different timestamps

        referrals = list(Referral.objects.all())
        dates = [r.created_at for r in referrals]
        assert dates == sorted(dates, reverse=True)

    def test_visiting_schedules_ordered_by_date(self, visiting_specialist):
        """Visiting schedules ordered by date then time."""
        from apps.referrals.models import VisitingSchedule

        base_date = timezone.now().date()

        VisitingSchedule.objects.create(
            specialist=visiting_specialist,
            date=base_date + timedelta(days=14),
            start_time=time(9, 0),
            end_time=time(15, 0)
        )

        VisitingSchedule.objects.create(
            specialist=visiting_specialist,
            date=base_date + timedelta(days=7),
            start_time=time(10, 0),
            end_time=time(14, 0)
        )

        schedules = list(VisitingSchedule.objects.all())
        dates = [s.date for s in schedules]
        assert dates == sorted(dates)
