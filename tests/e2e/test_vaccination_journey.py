"""E2E test for vaccination reminder journey.

Simulates the complete vaccination workflow:
1. Pet has vaccination record
2. Vaccination is due soon (within 30 days)
3. System identifies upcoming vaccinations
4. Reminder notification is sent
5. Owner books appointment
6. Vet administers vaccine
7. Vaccination record updated with next due date
8. Follow-up reminder scheduled

Tests the vaccination reminder automation.
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta

from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db(transaction=True)
class TestVaccinationReminderJourney:
    """Complete vaccination reminder journey."""

    @pytest.fixture
    def vet_user(self, db):
        """Create a veterinarian user."""
        from apps.practice.models import StaffProfile

        user = User.objects.create_user(
            username='dr.vaccines@petfriendlyvet.com',
            email='dr.vaccines@petfriendlyvet.com',
            password='vet123',
            first_name='Dr. Maria',
            last_name='Vacunas',
            role='vet',
            is_staff=True,
        )
        StaffProfile.objects.create(
            user=user,
            role='veterinarian',
            can_prescribe=True,
        )
        return user

    @pytest.fixture
    def customer(self, db):
        """Create a pet owner."""
        return User.objects.create_user(
            username='pet.owner@example.com',
            email='pet.owner@example.com',
            password='owner123',
            first_name='Juan',
            last_name='Propietario',
            role='owner',
            phone_number='555-123-4567',
        )

    @pytest.fixture
    def pet(self, db, customer):
        """Create a pet."""
        from apps.pets.models import Pet

        return Pet.objects.create(
            owner=customer,
            name='Max',
            species='dog',
            breed='Golden Retriever',
            gender='male',
            date_of_birth=date.today() - timedelta(days=365),  # 1 year old
            weight_kg=Decimal('25.0'),
        )

    @pytest.fixture
    def vaccination_service(self, db):
        """Create a vaccination service."""
        from apps.appointments.models import ServiceType

        return ServiceType.objects.create(
            name='Vacunación',
            description='Aplicación de vacuna',
            duration_minutes=15,
            price=Decimal('350.00'),
            category='vaccination',
            is_active=True,
        )

    def test_complete_vaccination_reminder_journey(
        self, db, vet_user, customer, pet, vaccination_service
    ):
        """
        Test complete vaccination journey from reminder to administration.

        Pet has due vaccination → Reminder sent → Appointment booked → Vaccine given
        """
        from apps.pets.models import Vaccination
        from apps.appointments.models import Appointment
        from apps.notifications.models import Notification
        from apps.billing.models import Invoice, Payment

        # =========================================================================
        # STEP 1: Pet Has Previous Vaccination Due for Renewal
        # =========================================================================
        # Create vaccination record from last year, due in 2 weeks
        previous_vaccination = Vaccination.objects.create(
            pet=pet,
            vaccine_name='Rabia (Rabies)',
            date_administered=date.today() - timedelta(days=350),
            next_due_date=date.today() + timedelta(days=15),  # Due in 15 days
            administered_by=vet_user,
            batch_number='RAB-2024-001',
            notes='Primera vacuna de rabia aplicada',
        )

        assert previous_vaccination.pk is not None
        assert previous_vaccination.is_due_soon is True
        assert previous_vaccination.is_overdue is False

        # =========================================================================
        # STEP 2: System Identifies Upcoming Vaccinations
        # =========================================================================
        # Query for pets with vaccinations due soon
        upcoming_vaccinations = Vaccination.objects.filter(
            next_due_date__gt=date.today(),
            next_due_date__lte=date.today() + timedelta(days=30),
            reminder_sent=False,
        )

        assert upcoming_vaccinations.count() >= 1
        assert previous_vaccination in upcoming_vaccinations

        # =========================================================================
        # STEP 3: Reminder Notification is Sent
        # =========================================================================
        reminder = Notification.objects.create(
            user=customer,
            notification_type='vaccination_reminder',
            title='Recordatorio de Vacuna - Max',
            message=f'La vacuna de Rabia de Max vence el {previous_vaccination.next_due_date}. '
                    f'Por favor agende una cita para renovarla.',
            related_pet_id=pet.pk,
            email_sent=True,
            email_sent_at=timezone.now(),
        )

        # Mark reminder as sent on vaccination record
        previous_vaccination.reminder_sent = True
        previous_vaccination.reminder_sent_at = timezone.now()
        previous_vaccination.save()

        assert reminder.pk is not None
        previous_vaccination.refresh_from_db()
        assert previous_vaccination.reminder_sent is True

        # =========================================================================
        # STEP 4: Owner Books Appointment
        # =========================================================================
        appointment_date = timezone.now() + timedelta(days=10)
        appointment = Appointment.objects.create(
            owner=customer,
            pet=pet,
            service=vaccination_service,
            veterinarian=vet_user,
            scheduled_start=appointment_date,
            scheduled_end=appointment_date + timedelta(minutes=15),
            status='scheduled',
            notes='Renovación de vacuna de rabia',
        )

        assert appointment.pk is not None
        assert appointment.status == 'scheduled'

        # Confirm appointment
        appointment.status = 'confirmed'
        appointment.confirmed_at = timezone.now()
        appointment.save()

        # =========================================================================
        # STEP 5: Customer Checks In
        # =========================================================================
        appointment.status = 'in_progress'
        appointment.save()

        assert appointment.status == 'in_progress'

        # =========================================================================
        # STEP 6: Vet Administers Vaccine
        # =========================================================================
        # Create new vaccination record
        new_vaccination = Vaccination.objects.create(
            pet=pet,
            vaccine_name='Rabia (Rabies)',
            date_administered=date.today(),
            next_due_date=date.today() + timedelta(days=365),  # Due in 1 year
            administered_by=vet_user,
            batch_number='RAB-2024-002',
            notes='Refuerzo anual de rabia aplicado',
        )

        assert new_vaccination.pk is not None
        assert new_vaccination.next_due_date == date.today() + timedelta(days=365)

        # Complete the appointment
        appointment.status = 'completed'
        appointment.completed_at = timezone.now()
        appointment.save()

        # =========================================================================
        # STEP 7: Invoice is Created and Paid
        # =========================================================================
        invoice = Invoice.objects.filter(appointment=appointment).first()
        assert invoice is not None

        # Pay the invoice
        Payment.objects.create(
            invoice=invoice,
            amount=invoice.total,
            payment_method='card',
            recorded_by=vet_user,
        )

        invoice.refresh_from_db()
        assert invoice.status == 'paid'

        # =========================================================================
        # STEP 8: Verify Vaccination History
        # =========================================================================
        # Pet should now have 2 rabies vaccinations
        rabies_vaccinations = pet.vaccinations.filter(vaccine_name__icontains='Rabia')
        assert rabies_vaccinations.count() == 2

        # Latest should be the new one
        latest_vaccination = pet.vaccinations.first()
        assert latest_vaccination == new_vaccination
        assert latest_vaccination.next_due_date == date.today() + timedelta(days=365)

        # =========================================================================
        # VERIFICATION: Complete Journey
        # =========================================================================
        # Notification was sent
        assert Notification.objects.filter(
            user=customer,
            notification_type='vaccination_reminder'
        ).exists()

        # Appointment was completed
        appointment.refresh_from_db()
        assert appointment.status == 'completed'

        # Invoice was paid
        assert invoice.status == 'paid'

        # New vaccination scheduled for next year
        assert new_vaccination.is_due_soon is False
        assert new_vaccination.reminder_sent is False  # Not yet


@pytest.mark.django_db(transaction=True)
class TestVaccinationOverdueScenarios:
    """Test vaccination overdue and multi-vaccine scenarios."""

    @pytest.fixture
    def setup_vaccination_data(self, db):
        """Create test data for vaccination tests."""
        from apps.pets.models import Pet
        from apps.practice.models import StaffProfile

        owner = User.objects.create_user(
            username='multi.pet@example.com',
            email='multi.pet@example.com',
            password='owner123',
            role='owner',
        )

        vet = User.objects.create_user(
            username='vet.vacc@example.com',
            email='vet.vacc@example.com',
            password='vet123',
            role='vet',
            is_staff=True,
        )
        StaffProfile.objects.create(user=vet, role='veterinarian')

        pet = Pet.objects.create(
            owner=owner,
            name='Rocky',
            species='dog',
            breed='Labrador',
            gender='male',
        )

        return {'owner': owner, 'vet': vet, 'pet': pet}

    def test_overdue_vaccination_alert(self, setup_vaccination_data):
        """Overdue vaccinations should be flagged."""
        from apps.pets.models import Vaccination
        from apps.notifications.models import Notification

        data = setup_vaccination_data

        # Create overdue vaccination
        overdue_vaccination = Vaccination.objects.create(
            pet=data['pet'],
            vaccine_name='Parvovirus',
            date_administered=date.today() - timedelta(days=400),
            next_due_date=date.today() - timedelta(days=35),  # Overdue by 35 days
            administered_by=data['vet'],
            batch_number='PARVO-2023-001',
        )

        assert overdue_vaccination.is_overdue is True
        assert overdue_vaccination.is_due_soon is False

        # System sends overdue notification
        overdue_notification = Notification.objects.create(
            user=data['owner'],
            notification_type='vaccination_overdue',
            title='URGENTE: Vacuna Vencida - Rocky',
            message=f'La vacuna de Parvovirus de Rocky venció hace 35 días. '
                    f'Es importante vacunar a su mascota lo antes posible.',
            related_pet_id=data['pet'].pk,
            email_sent=True,
            email_sent_at=timezone.now(),
        )

        assert overdue_notification.pk is not None

    def test_multiple_vaccines_due(self, setup_vaccination_data):
        """Pet can have multiple vaccines due at same time."""
        from apps.pets.models import Vaccination

        data = setup_vaccination_data

        # Create multiple vaccinations due soon
        vaccines = [
            ('Rabia', 10),
            ('Parvovirus', 15),
            ('Moquillo', 20),
        ]

        for vaccine_name, days_until_due in vaccines:
            Vaccination.objects.create(
                pet=data['pet'],
                vaccine_name=vaccine_name,
                date_administered=date.today() - timedelta(days=350),
                next_due_date=date.today() + timedelta(days=days_until_due),
                administered_by=data['vet'],
            )

        # Query for all due soon
        due_soon = Vaccination.objects.filter(
            pet=data['pet'],
            next_due_date__gt=date.today(),
            next_due_date__lte=date.today() + timedelta(days=30),
        )

        assert due_soon.count() == 3

    def test_puppy_vaccination_schedule(self, setup_vaccination_data):
        """Puppies have multiple vaccinations in first months."""
        from apps.pets.models import Pet, Vaccination

        data = setup_vaccination_data

        # Create a puppy
        puppy = Pet.objects.create(
            owner=data['owner'],
            name='Cachorro',
            species='dog',
            breed='Mixed',
            gender='male',
            date_of_birth=date.today() - timedelta(days=60),  # 2 months old
        )

        # First round of vaccinations
        first_round = [
            ('Parvovirus - 1ra dosis', date.today() - timedelta(days=30)),
            ('Moquillo - 1ra dosis', date.today() - timedelta(days=30)),
        ]

        for vaccine_name, admin_date in first_round:
            Vaccination.objects.create(
                pet=puppy,
                vaccine_name=vaccine_name,
                date_administered=admin_date,
                next_due_date=admin_date + timedelta(days=21),  # 2nd dose in 3 weeks
                administered_by=data['vet'],
            )

        # Verify schedule
        vaccinations = puppy.vaccinations.all()
        assert vaccinations.count() == 2

        # Check which are due soon
        due_for_second_dose = vaccinations.filter(
            next_due_date__lte=date.today() + timedelta(days=7)
        )
        assert due_for_second_dose.count() == 2  # Both need 2nd dose soon


@pytest.mark.django_db(transaction=True)
class TestVaccinationWeightTracking:
    """Test weight recording during vaccination visits."""

    def test_weight_recorded_during_vaccination(self, db):
        """Weight is recorded during vaccination visit."""
        from apps.pets.models import Pet, Vaccination, WeightRecord
        from apps.practice.models import StaffProfile

        owner = User.objects.create_user(
            username='weight.test@example.com',
            email='weight.test@example.com',
            password='test123',
            role='owner',
        )

        vet = User.objects.create_user(
            username='vet.weight@example.com',
            email='vet.weight@example.com',
            password='vet123',
            role='vet',
            is_staff=True,
        )
        StaffProfile.objects.create(user=vet, role='veterinarian')

        pet = Pet.objects.create(
            owner=owner,
            name='Gordo',
            species='dog',
            weight_kg=Decimal('20.0'),
        )

        original_weight = pet.weight_kg

        # Record weight during vaccination visit
        WeightRecord.objects.create(
            pet=pet,
            weight_kg=Decimal('22.5'),
            recorded_by=vet,
            notes='Peso durante vacunación',
        )

        # Create vaccination record
        Vaccination.objects.create(
            pet=pet,
            vaccine_name='Vacuna Anual',
            date_administered=date.today(),
            next_due_date=date.today() + timedelta(days=365),
            administered_by=vet,
        )

        # Weight should be updated on pet
        pet.refresh_from_db()
        assert pet.weight_kg == Decimal('22.5')
        assert pet.weight_kg != original_weight

        # Weight history should have entry
        assert pet.weight_records.count() >= 1
