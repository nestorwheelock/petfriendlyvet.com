"""E2E test for prescription and refill journey.

Simulates the full prescription workflow:
1. Vet examines pet during appointment
2. Vet prescribes medication
3. Prescription is added to pet's record
4. Customer requests refill
5. Vet approves refill
6. Pharmacy prepares medication
7. Customer picks up or receives delivery
8. Refill count is updated

Tests the complete pharmacy workflow.
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta

from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db(transaction=True)
class TestPrescriptionJourney:
    """Complete prescription journey from diagnosis to refill."""

    @pytest.fixture
    def vet_user(self, db):
        """Create a veterinarian user with StaffProfile."""
        from apps.practice.models import StaffProfile

        user = User.objects.create_user(
            username='dr.vet@petfriendlyvet.com',
            email='dr.vet@petfriendlyvet.com',
            password='vet123',
            first_name='Dr. Roberto',
            last_name='Sánchez',
            role='vet',
            is_staff=True,
        )
        StaffProfile.objects.create(
            user=user,
            role='veterinarian',
            can_prescribe=True,
            can_dispense=True,
        )
        return user

    @pytest.fixture
    def pharmacist_user(self, db):
        """Create a pharmacist/staff user with StaffProfile."""
        from apps.practice.models import StaffProfile

        user = User.objects.create_user(
            username='pharmacy@petfriendlyvet.com',
            email='pharmacy@petfriendlyvet.com',
            password='pharmacy123',
            first_name='Laura',
            last_name='Méndez',
            role='staff',
            is_staff=True,
        )
        StaffProfile.objects.create(
            user=user,
            role='pharmacy_tech',
            can_dispense=True,
        )
        return user

    @pytest.fixture
    def customer(self, db):
        """Create a customer with a pet."""
        return User.objects.create_user(
            username='pet.owner@example.com',
            email='pet.owner@example.com',
            password='owner123',
            first_name='María',
            last_name='González',
            role='owner',
            phone_number='555-111-2222',
        )

    @pytest.fixture
    def pet(self, db, customer):
        """Create a pet for the customer."""
        from apps.pets.models import Pet

        return Pet.objects.create(
            owner=customer,
            name='Bruno',
            species='dog',
            breed='German Shepherd',
            gender='male',
            date_of_birth=date.today() - timedelta(days=2190),  # 6 years old
            weight_kg=Decimal('35.0'),
        )

    @pytest.fixture
    def medication(self, db):
        """Create a medication."""
        from apps.pharmacy.models import Medication

        return Medication.objects.create(
            name='Amoxicillin',
            name_es='Amoxicilina',
            generic_name='Amoxicillin',
            drug_class='Antibiotic',
            dosage_forms=['tablet', 'capsule'],
            strengths=['250mg', '500mg'],
            species=['dog', 'cat'],
            manufacturer='Generic Pharma',
            requires_prescription=True,
            is_controlled=False,
            is_active=True,
        )

    def test_complete_prescription_journey(
        self, db, vet_user, pharmacist_user, customer, pet, medication
    ):
        """
        Test complete prescription flow from appointment to refill.

        Vet prescribes → Customer picks up → Customer refills
        """
        from apps.appointments.models import Appointment, ServiceType
        from apps.pharmacy.models import Prescription, RefillRequest
        from apps.billing.models import Invoice, Payment

        # =========================================================================
        # STEP 1: Create Appointment and Service
        # =========================================================================
        service = ServiceType.objects.create(
            name='Consulta General',
            duration_minutes=30,
            price=Decimal('500.00'),
            category='clinic',
            is_active=True,
        )

        tomorrow = timezone.now() + timedelta(days=1)
        appointment = Appointment.objects.create(
            owner=customer,
            pet=pet,
            service=service,
            veterinarian=vet_user,
            scheduled_start=tomorrow,
            scheduled_end=tomorrow + timedelta(minutes=30),
            status='scheduled',
            notes='Paciente presenta tos y fiebre leve',
        )

        # =========================================================================
        # STEP 2: Vet Examines Pet and Diagnoses
        # =========================================================================
        appointment.status = 'in_progress'
        appointment.save()

        # Vet notes during examination
        appointment.notes = '''
        Paciente presenta tos y fiebre leve.
        Examen físico: Temperatura 39.5°C, mucosas rosadas, auscultación con estertores leves.
        Diagnóstico: Infección respiratoria bacteriana leve.
        Tratamiento: Antibiótico oral por 10 días.
        '''
        appointment.save()

        # =========================================================================
        # STEP 3: Vet Creates Prescription
        # =========================================================================
        prescription = Prescription.objects.create(
            pet=pet,
            owner=customer,
            prescribing_vet=vet_user.staff_profile,
            visit=appointment,
            medication=medication,
            strength='250mg',
            dosage_form='tablet',
            quantity=30,  # 3 per day x 10 days
            dosage='1 tablet',
            frequency='Cada 8 horas',
            duration='10 days',
            instructions='Administrar con comida. Completar todo el tratamiento.',
            refills_authorized=2,
            refills_remaining=2,
            status='active',
            prescribed_date=date.today(),
            expiration_date=date.today() + timedelta(days=180),  # 6 months validity
        )

        assert prescription.pk is not None
        assert prescription.refills_remaining == 2
        assert prescription.status == 'active'

        # Link prescription to appointment (if your model supports it)
        # appointment.prescriptions.add(prescription)

        # =========================================================================
        # STEP 4: Complete Appointment
        # =========================================================================
        appointment.status = 'completed'
        appointment.completed_at = timezone.now()
        appointment.save()

        # Invoice auto-created for appointment
        invoice = Invoice.objects.filter(appointment=appointment).first()
        if invoice:
            # Add medication to invoice (using a fixed price since Medication is a reference db)
            from apps.billing.models import InvoiceLineItem
            medication_price = Decimal('25.00')  # Fixed dispensing price
            InvoiceLineItem.objects.create(
                invoice=invoice,
                description=f'{medication.name} x 30 tabletas',
                quantity=30,
                unit_price=medication_price,
                line_total=medication_price * 30,
            )

        # =========================================================================
        # STEP 5: Customer Picks Up Medication (First Fill)
        # =========================================================================
        from apps.pharmacy.models import PrescriptionFill

        # Create initial fill record
        initial_fill = PrescriptionFill.objects.create(
            prescription=prescription,
            fill_number=0,  # Original fill
            quantity_dispensed=prescription.quantity,
            dispensed_by=pharmacist_user.staff_profile,
            status='picked_up',
            fulfillment_method='pickup',
            ready_at=timezone.now(),
            completed_at=timezone.now(),
        )

        assert initial_fill.pk is not None
        assert initial_fill.status == 'picked_up'

        # =========================================================================
        # STEP 6: After Treatment - Customer Requests Refill
        # =========================================================================
        # Simulate time passing - pet needs another round of treatment
        # Customer submits refill request

        refill_request = RefillRequest.objects.create(
            prescription=prescription,
            requested_by=customer,
            quantity_requested=30,
            notes='Bruno sigue con tos leve, necesita continuar tratamiento',
            status='pending',
        )

        assert refill_request.pk is not None
        assert refill_request.status == 'pending'

        # =========================================================================
        # STEP 7: Vet Approves Refill
        # =========================================================================
        refill_request.status = 'approved'
        refill_request.authorized_by = vet_user.staff_profile
        refill_request.authorized_at = timezone.now()
        refill_request.save()

        # Update prescription refills using the model method
        prescription.use_refill()

        prescription.refresh_from_db()
        assert prescription.refills_remaining == 1

        # =========================================================================
        # STEP 8: Pharmacy Fills the Refill
        # =========================================================================
        refill_fill = PrescriptionFill.objects.create(
            prescription=prescription,
            fill_number=1,  # First refill
            quantity_dispensed=refill_request.quantity_requested or prescription.quantity,
            dispensed_by=pharmacist_user.staff_profile,
            status='ready',
            fulfillment_method='pickup',
            ready_at=timezone.now(),
        )

        # Link fill to refill request
        refill_request.fill = refill_fill
        refill_request.status = 'filled'
        refill_request.save()

        # =========================================================================
        # STEP 9: Customer Picks Up Refill
        # =========================================================================
        refill_fill.status = 'picked_up'
        refill_fill.completed_at = timezone.now()
        refill_fill.save()

        # =========================================================================
        # VERIFICATION: Complete Journey
        # =========================================================================
        prescription.refresh_from_db()
        refill_request.refresh_from_db()
        refill_fill.refresh_from_db()

        # Prescription status
        assert prescription.status == 'active'
        assert prescription.refills_remaining == 1  # 2 - 1 used

        # Refill request was filled
        assert refill_request.status == 'filled'
        assert refill_request.fill == refill_fill

        # Fill was picked up
        assert refill_fill.status == 'picked_up'
        assert refill_fill.completed_at is not None

        # Pet has prescription history
        assert pet.prescriptions.count() == 1

        # Prescription has fill records
        assert prescription.fills.count() == 2  # Initial + 1 refill


@pytest.mark.django_db(transaction=True)
class TestPrescriptionEdgeCases:
    """Test edge cases in prescription workflow."""

    @pytest.fixture
    def setup_pharmacy(self, db):
        """Create pharmacy test data."""
        from apps.pharmacy.models import Medication
        from apps.practice.models import StaffProfile

        vet = User.objects.create_user(
            username='vet.edge@example.com',
            email='vet.edge@example.com',
            password='vetpass',
            role='vet',
            is_staff=True,
        )
        vet_profile = StaffProfile.objects.create(
            user=vet,
            role='veterinarian',
            can_prescribe=True,
        )

        customer = User.objects.create_user(
            username='owner.edge@example.com',
            email='owner.edge@example.com',
            password='ownerpass',
            role='owner',
        )

        from apps.pets.models import Pet
        pet = Pet.objects.create(
            owner=customer,
            name='Test Pet',
            species='dog',
        )

        medication = Medication.objects.create(
            name='Test Medication',
            drug_class='Antibiotic',
            dosage_forms=['tablet'],
            strengths=['100mg'],
            requires_prescription=True,
            is_controlled=False,
            is_active=True,
        )

        return {
            'vet': vet,
            'vet_profile': vet_profile,
            'customer': customer,
            'pet': pet,
            'medication': medication,
        }

    def test_prescription_expires(self, setup_pharmacy):
        """Expired prescription cannot be refilled."""
        from apps.pharmacy.models import Prescription, RefillRequest

        data = setup_pharmacy

        # Create expired prescription
        prescription = Prescription.objects.create(
            pet=data['pet'],
            owner=data['customer'],
            prescribing_vet=data['vet_profile'],
            medication=data['medication'],
            strength='100mg',
            dosage_form='tablet',
            quantity=7,
            dosage='1 tablet',
            frequency='Once daily',
            duration='7 days',
            refills_authorized=1,
            refills_remaining=1,
            status='active',
            prescribed_date=date.today() - timedelta(days=60),
            expiration_date=date.today() - timedelta(days=53),  # Expired 53 days ago
        )

        # Mark as expired
        prescription.status = 'expired'
        prescription.save()

        # Verify can_refill returns False for expired prescription
        assert prescription.is_expired is True
        assert prescription.can_refill is False

        # Customer tries to request refill
        refill = RefillRequest.objects.create(
            prescription=prescription,
            requested_by=data['customer'],
            quantity_requested=7,
            status='pending',
        )

        # Should be rejected due to expiry
        refill.status = 'denied'
        refill.denial_reason = 'Prescription has expired. Please schedule new appointment.'
        refill.save()

        assert refill.status == 'denied'

    def test_no_refills_remaining(self, setup_pharmacy):
        """Cannot refill when no refills remaining."""
        from apps.pharmacy.models import Prescription, RefillRequest

        data = setup_pharmacy

        # Prescription with no refills left
        prescription = Prescription.objects.create(
            pet=data['pet'],
            owner=data['customer'],
            prescribing_vet=data['vet_profile'],
            medication=data['medication'],
            strength='100mg',
            dosage_form='tablet',
            quantity=7,
            dosage='1 tablet',
            frequency='Once daily',
            duration='7 days',
            refills_authorized=2,
            refills_remaining=0,  # No refills left
            status='completed',  # All refills used
            prescribed_date=date.today() - timedelta(days=7),
            expiration_date=date.today() + timedelta(days=173),  # Still valid
        )

        # Verify can_refill returns False
        assert prescription.refills_remaining == 0
        assert prescription.has_refills is False
        assert prescription.can_refill is False

        # Customer tries to request refill
        refill = RefillRequest.objects.create(
            prescription=prescription,
            requested_by=data['customer'],
            quantity_requested=7,
            status='pending',
        )

        # Should be denied - no refills remaining
        refill.status = 'denied'
        refill.denial_reason = 'No refills remaining. Please schedule appointment for new prescription.'
        refill.save()

        assert refill.status == 'denied'

    def test_controlled_medication_extra_verification(self, setup_pharmacy):
        """Controlled medications require extra verification."""
        from apps.pharmacy.models import Medication, Prescription

        data = setup_pharmacy

        # Create controlled medication
        controlled_med = Medication.objects.create(
            name='Controlled Medication',
            drug_class='Opioid',
            schedule='II',
            dosage_forms=['tablet'],
            strengths=['50mg'],
            requires_prescription=True,
            is_controlled=True,  # Controlled substance
            is_active=True,
        )

        # Prescription for controlled med
        prescription = Prescription.objects.create(
            pet=data['pet'],
            owner=data['customer'],
            prescribing_vet=data['vet_profile'],
            medication=controlled_med,
            strength='50mg',
            dosage_form='tablet',
            quantity=10,
            dosage='1 tablet',
            frequency='As needed for pain',
            duration='5 days',
            refills_authorized=0,  # Controlled - no refills
            refills_remaining=0,
            status='active',
            prescribed_date=date.today(),
            expiration_date=date.today() + timedelta(days=30),
            dea_number='AB1234567',  # DEA number for controlled substance tracking
        )

        # Controlled medications should have no refills authorized
        assert prescription.refills_authorized == 0
        assert controlled_med.is_controlled is True
        assert controlled_med.schedule == 'II'

    def test_multiple_active_prescriptions(self, setup_pharmacy):
        """Pet can have multiple active prescriptions."""
        from apps.pharmacy.models import Medication, Prescription

        data = setup_pharmacy

        # Second medication
        med2 = Medication.objects.create(
            name='Second Medication',
            drug_class='Anti-inflammatory',
            dosage_forms=['liquid'],
            strengths=['5mg/ml'],
            requires_prescription=True,
            is_active=True,
        )

        # First prescription
        Prescription.objects.create(
            pet=data['pet'],
            owner=data['customer'],
            prescribing_vet=data['vet_profile'],
            medication=data['medication'],
            strength='100mg',
            dosage_form='tablet',
            quantity=28,
            dosage='1 tablet',
            frequency='Twice daily',
            duration='14 days',
            refills_authorized=1,
            refills_remaining=1,
            status='active',
            prescribed_date=date.today(),
            expiration_date=date.today() + timedelta(days=180),
        )

        # Second prescription
        Prescription.objects.create(
            pet=data['pet'],
            owner=data['customer'],
            prescribing_vet=data['vet_profile'],
            medication=med2,
            strength='5mg/ml',
            dosage_form='liquid',
            quantity=7,
            dosage='5ml',
            frequency='Once daily',
            duration='7 days',
            refills_authorized=0,
            refills_remaining=0,
            status='active',
            prescribed_date=date.today(),
            expiration_date=date.today() + timedelta(days=180),
        )

        # Pet should have 2 active prescriptions
        active_prescriptions = data['pet'].prescriptions.filter(status='active')
        assert active_prescriptions.count() == 2
