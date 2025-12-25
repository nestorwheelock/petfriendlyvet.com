"""E2E test for complete customer journey.

Simulates the full workflow:
1. New customer registers
2. Customer adds a pet
3. Customer schedules an appointment
4. Vet confirms the appointment
5. Reminder is sent
6. Customer checks in
7. Pet is examined (appointment completed)
8. Bill is automatically created
9. Bill is paid

This is the "happy path" test that exercises the core business flow.
"""
import pytest
from decimal import Decimal
from datetime import date, time, timedelta

from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db(transaction=True)
class TestFullCustomerJourney:
    """Complete customer journey from registration to payment."""

    @pytest.fixture
    def vet_user(self, db):
        """Create a veterinarian user."""
        return User.objects.create_user(
            username='dr.martinez@petfriendlyvet.com',
            email='dr.martinez@petfriendlyvet.com',
            password='vet123secure',
            first_name='Dr. Ana',
            last_name='Martínez',
            role='vet',
            is_staff=True,
        )

    @pytest.fixture
    def staff_user(self, db):
        """Create a staff user for payment processing."""
        return User.objects.create_user(
            username='staff@petfriendlyvet.com',
            email='staff@petfriendlyvet.com',
            password='staff123',
            first_name='María',
            last_name='García',
            role='staff',
            is_staff=True,
        )

    @pytest.fixture
    def service_type(self, db):
        """Create a consultation service."""
        from apps.appointments.models import ServiceType

        return ServiceType.objects.create(
            name='Consulta General',
            description='Consulta veterinaria estándar',
            duration_minutes=30,
            price=Decimal('500.00'),
            category='clinic',
            is_active=True,
        )

    def test_complete_customer_journey(self, db, vet_user, staff_user, service_type):
        """
        Test the complete customer journey from registration to payment.

        This is the "golden path" test that verifies the core business flow works.
        """
        from apps.pets.models import Pet
        from apps.appointments.models import Appointment
        from apps.billing.models import Invoice, Payment
        from apps.notifications.models import Notification

        # =========================================================================
        # STEP 1: New Customer Registers
        # =========================================================================
        customer = User.objects.create_user(
            username='carlos.perez@gmail.com',
            email='carlos.perez@gmail.com',
            password='securepass123',
            first_name='Carlos',
            last_name='Pérez',
            role='owner',
            phone_number='555-123-4567',
        )

        assert customer.pk is not None
        assert customer.role == 'owner'
        assert customer.is_active is True

        # =========================================================================
        # STEP 2: Customer Adds a Pet
        # =========================================================================
        pet = Pet.objects.create(
            owner=customer,
            name='Rocky',
            species='dog',
            breed='Labrador Retriever',
            gender='male',
            date_of_birth=date.today() - timedelta(days=730),  # 2 years old
            weight_kg=Decimal('28.5'),
            is_neutered=True,
        )

        assert pet.pk is not None
        assert pet.owner == customer
        assert pet.name == 'Rocky'

        # Verify pet appears in customer's pets
        assert customer.pets.count() == 1
        assert customer.pets.first() == pet

        # =========================================================================
        # STEP 3: Customer Schedules an Appointment
        # =========================================================================
        # Schedule for tomorrow at 10:00 AM
        tomorrow = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)

        appointment = Appointment.objects.create(
            owner=customer,
            pet=pet,
            service=service_type,
            veterinarian=vet_user,
            scheduled_start=tomorrow,
            scheduled_end=tomorrow + timedelta(minutes=service_type.duration_minutes),
            status='scheduled',
            notes='Primera visita - chequeo general',
        )

        assert appointment.pk is not None
        assert appointment.status == 'scheduled'
        assert appointment.pet == pet
        assert appointment.veterinarian == vet_user

        # =========================================================================
        # STEP 4: Vet Confirms the Appointment
        # =========================================================================
        appointment.status = 'confirmed'
        appointment.confirmed_at = timezone.now()
        appointment.save()

        appointment.refresh_from_db()
        assert appointment.status == 'confirmed'
        assert appointment.confirmed_at is not None

        # =========================================================================
        # STEP 5: Reminder is Sent
        # =========================================================================
        # Simulate reminder being sent (would normally be done by a scheduled task)
        appointment.reminder_sent = True
        appointment.reminder_sent_at = timezone.now()
        appointment.save()

        # Log the notification
        Notification.objects.create(
            user=customer,
            notification_type='appointment_reminder',
            title='Recordatorio de cita - Rocky',
            message='Su cita para Rocky está programada para mañana a las 10:00 AM',
            related_appointment_id=appointment.pk,
            related_pet_id=pet.pk,
            email_sent=True,
            email_sent_at=timezone.now(),
        )

        appointment.refresh_from_db()
        assert appointment.reminder_sent is True
        assert appointment.reminder_sent_at is not None

        # Verify notification was logged
        reminder_log = Notification.objects.filter(
            user=customer,
            notification_type='appointment_reminder'
        ).first()
        assert reminder_log is not None
        assert reminder_log.email_sent is True

        # =========================================================================
        # STEP 6: Customer Checks In (Appointment Starts)
        # =========================================================================
        appointment.status = 'in_progress'
        appointment.save()

        appointment.refresh_from_db()
        assert appointment.status == 'in_progress'

        # At this point, no invoice should exist yet
        invoice_before_completion = Invoice.objects.filter(appointment=appointment).first()
        assert invoice_before_completion is None, "Invoice should not be created until appointment is completed"

        # =========================================================================
        # STEP 7: Pet is Examined (Appointment Completed)
        # =========================================================================
        appointment.status = 'completed'
        appointment.completed_at = timezone.now()
        appointment.notes = 'Primera visita - chequeo general. Rocky está en excelente salud. Peso: 28.5kg.'
        appointment.save()

        appointment.refresh_from_db()
        assert appointment.status == 'completed'
        assert appointment.completed_at is not None

        # =========================================================================
        # STEP 8: Bill is Automatically Created
        # =========================================================================
        # The signal should have created an invoice
        invoice = Invoice.objects.filter(appointment=appointment).first()
        assert invoice is not None, "Invoice should be auto-created when appointment is completed"

        # Verify invoice details
        assert invoice.owner == customer
        assert invoice.pet == pet
        assert invoice.appointment == appointment

        # Verify pricing
        expected_subtotal = service_type.price  # 500.00
        expected_tax = expected_subtotal * Decimal('0.16')  # 80.00
        expected_total = expected_subtotal + expected_tax  # 580.00

        assert invoice.subtotal == expected_subtotal
        assert invoice.tax_amount == expected_tax
        assert invoice.total == expected_total

        # Verify invoice has line item for the service
        assert invoice.items.count() >= 1
        service_line = invoice.items.first()
        assert service_line.description == service_type.name
        assert service_line.unit_price == service_type.price

        # Invoice should be in 'sent' or 'draft' status
        assert invoice.status in ['draft', 'sent']

        # =========================================================================
        # STEP 9: Bill is Paid
        # =========================================================================
        payment = Payment.objects.create(
            invoice=invoice,
            amount=invoice.total,
            payment_method='card',
            recorded_by=staff_user,
            notes='Pago con tarjeta de crédito',
        )

        assert payment.pk is not None
        assert payment.amount == invoice.total

        # Verify invoice is now paid
        invoice.refresh_from_db()
        assert invoice.status == 'paid'
        assert invoice.amount_paid == invoice.total
        assert invoice.paid_at is not None

        # Verify balance is zero
        assert invoice.get_balance_due() == Decimal('0.00')

        # =========================================================================
        # VERIFICATION: Complete Journey Summary
        # =========================================================================
        # Customer has:
        assert customer.pets.count() == 1
        assert customer.appointments.count() == 1

        # Pet has:
        assert pet.appointments.count() == 1
        appointment_for_pet = pet.appointments.first()
        assert appointment_for_pet.status == 'completed'

        # Invoice chain is complete:
        assert Invoice.objects.filter(owner=customer).count() == 1
        assert Payment.objects.filter(invoice__owner=customer).count() == 1

        # All financial records match:
        customer_invoice = Invoice.objects.get(owner=customer)
        assert customer_invoice.status == 'paid'
        assert customer_invoice.total == Decimal('580.00')
        assert customer_invoice.amount_paid == Decimal('580.00')


@pytest.mark.django_db(transaction=True)
class TestCustomerJourneyVariations:
    """Test variations of the customer journey."""

    @pytest.fixture
    def setup_users(self, db):
        """Create test users."""
        customer = User.objects.create_user(
            username='test.customer@example.com',
            email='test.customer@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Customer',
            role='owner',
        )
        vet = User.objects.create_user(
            username='test.vet@example.com',
            email='test.vet@example.com',
            password='vetpass123',
            first_name='Dr. Test',
            last_name='Vet',
            role='vet',
            is_staff=True,
        )
        staff = User.objects.create_user(
            username='test.staff@example.com',
            email='test.staff@example.com',
            password='staffpass123',
            role='staff',
            is_staff=True,
        )
        return {'customer': customer, 'vet': vet, 'staff': staff}

    @pytest.fixture
    def setup_service(self, db):
        """Create service type."""
        from apps.appointments.models import ServiceType

        return ServiceType.objects.create(
            name='Vacunación',
            duration_minutes=15,
            price=Decimal('350.00'),
            category='clinic',
            is_active=True,
        )

    def test_partial_payment_journey(self, db, setup_users, setup_service):
        """Customer makes partial payment, then completes payment later."""
        from apps.pets.models import Pet
        from apps.appointments.models import Appointment
        from apps.billing.models import Invoice, Payment

        customer = setup_users['customer']
        vet = setup_users['vet']
        staff = setup_users['staff']

        # Create pet and appointment
        pet = Pet.objects.create(
            owner=customer,
            name='Luna',
            species='cat',
            gender='female',
        )

        tomorrow = timezone.now() + timedelta(days=1)
        appointment = Appointment.objects.create(
            owner=customer,
            pet=pet,
            service=setup_service,
            veterinarian=vet,
            scheduled_start=tomorrow,
            scheduled_end=tomorrow + timedelta(minutes=15),
            status='scheduled',
        )

        # Complete appointment
        appointment.status = 'completed'
        appointment.completed_at = timezone.now()
        appointment.save()

        # Get auto-created invoice
        invoice = Invoice.objects.filter(appointment=appointment).first()
        assert invoice is not None

        # Make partial payment (half)
        first_payment = invoice.total / 2
        Payment.objects.create(
            invoice=invoice,
            amount=first_payment,
            payment_method='cash',
            recorded_by=staff,
        )

        invoice.refresh_from_db()
        assert invoice.status == 'partial'
        assert invoice.amount_paid == first_payment

        # Make final payment
        remaining = invoice.get_balance_due()
        Payment.objects.create(
            invoice=invoice,
            amount=remaining,
            payment_method='cash',
            recorded_by=staff,
        )

        invoice.refresh_from_db()
        assert invoice.status == 'paid'
        assert invoice.amount_paid == invoice.total

    def test_cancelled_appointment_no_invoice(self, db, setup_users, setup_service):
        """Cancelled appointment should not create invoice."""
        from apps.pets.models import Pet
        from apps.appointments.models import Appointment
        from apps.billing.models import Invoice

        customer = setup_users['customer']
        vet = setup_users['vet']

        pet = Pet.objects.create(
            owner=customer,
            name='Max',
            species='dog',
            gender='male',
        )

        tomorrow = timezone.now() + timedelta(days=1)
        appointment = Appointment.objects.create(
            owner=customer,
            pet=pet,
            service=setup_service,
            veterinarian=vet,
            scheduled_start=tomorrow,
            scheduled_end=tomorrow + timedelta(minutes=15),
            status='scheduled',
        )

        # Cancel appointment
        appointment.status = 'cancelled'
        appointment.cancellation_reason = 'Customer requested cancellation'
        appointment.cancelled_at = timezone.now()
        appointment.save()

        # No invoice should be created
        invoice = Invoice.objects.filter(appointment=appointment).first()
        assert invoice is None

    def test_multiple_pets_multiple_appointments(self, db, setup_users, setup_service):
        """Customer with multiple pets schedules multiple appointments."""
        from apps.pets.models import Pet
        from apps.appointments.models import Appointment
        from apps.billing.models import Invoice, Payment

        customer = setup_users['customer']
        vet = setup_users['vet']
        staff = setup_users['staff']

        # Create two pets
        pet1 = Pet.objects.create(
            owner=customer,
            name='Buddy',
            species='dog',
            gender='male',
        )
        pet2 = Pet.objects.create(
            owner=customer,
            name='Whiskers',
            species='cat',
            gender='female',
        )

        assert customer.pets.count() == 2

        # Schedule appointments for both pets
        tomorrow = timezone.now() + timedelta(days=1)

        appointment1 = Appointment.objects.create(
            owner=customer,
            pet=pet1,
            service=setup_service,
            veterinarian=vet,
            scheduled_start=tomorrow,
            scheduled_end=tomorrow + timedelta(minutes=15),
            status='scheduled',
        )

        appointment2 = Appointment.objects.create(
            owner=customer,
            pet=pet2,
            service=setup_service,
            veterinarian=vet,
            scheduled_start=tomorrow + timedelta(hours=1),
            scheduled_end=tomorrow + timedelta(hours=1, minutes=15),
            status='scheduled',
        )

        # Complete both appointments
        for appt in [appointment1, appointment2]:
            appt.status = 'completed'
            appt.completed_at = timezone.now()
            appt.save()

        # Should have 2 invoices
        invoices = Invoice.objects.filter(owner=customer)
        assert invoices.count() == 2

        # Pay both invoices
        for invoice in invoices:
            Payment.objects.create(
                invoice=invoice,
                amount=invoice.total,
                payment_method='card',
                recorded_by=staff,
            )

        # Verify all paid
        for invoice in Invoice.objects.filter(owner=customer):
            invoice.refresh_from_db()
            assert invoice.status == 'paid'


@pytest.mark.django_db(transaction=True)
class TestJourneyEdgeCases:
    """Test edge cases in the customer journey."""

    def test_same_day_appointment(self, db):
        """Customer books and completes appointment same day."""
        from apps.pets.models import Pet
        from apps.appointments.models import Appointment, ServiceType
        from apps.billing.models import Invoice, Payment

        # Create users
        customer = User.objects.create_user(
            username='urgent@example.com',
            email='urgent@example.com',
            password='testpass',
            role='owner',
        )
        vet = User.objects.create_user(
            username='vet@example.com',
            email='vet@example.com',
            password='vetpass',
            role='vet',
            is_staff=True,
        )
        staff = User.objects.create_user(
            username='staff@example.com',
            email='staff@example.com',
            password='staffpass',
            role='staff',
            is_staff=True,
        )

        service = ServiceType.objects.create(
            name='Emergencia',
            duration_minutes=45,
            price=Decimal('1000.00'),
            category='emergency',
            is_active=True,
        )

        pet = Pet.objects.create(
            owner=customer,
            name='Emergency Pet',
            species='dog',
        )

        # Same-day appointment
        now = timezone.now()
        appointment = Appointment.objects.create(
            owner=customer,
            pet=pet,
            service=service,
            veterinarian=vet,
            scheduled_start=now,
            scheduled_end=now + timedelta(minutes=45),
            status='scheduled',
        )

        # Fast-track through statuses
        appointment.status = 'confirmed'
        appointment.confirmed_at = now
        appointment.save()

        appointment.status = 'in_progress'
        appointment.save()

        appointment.status = 'completed'
        appointment.completed_at = now + timedelta(minutes=45)
        appointment.save()

        # Invoice created
        invoice = Invoice.objects.filter(appointment=appointment).first()
        assert invoice is not None
        assert invoice.total == Decimal('1160.00')  # 1000 + 16% tax

        # Immediate payment
        Payment.objects.create(
            invoice=invoice,
            amount=invoice.total,
            payment_method='cash',
            recorded_by=staff,
        )

        invoice.refresh_from_db()
        assert invoice.status == 'paid'

    def test_appointment_without_pet(self, db):
        """Some services don't require a pet (e.g., consultation about getting a pet)."""
        from apps.appointments.models import Appointment, ServiceType
        from apps.billing.models import Invoice

        customer = User.objects.create_user(
            username='nopet@example.com',
            email='nopet@example.com',
            password='testpass',
            role='owner',
        )
        vet = User.objects.create_user(
            username='vet2@example.com',
            email='vet2@example.com',
            password='vetpass',
            role='vet',
            is_staff=True,
        )

        # Service that doesn't require a pet
        service = ServiceType.objects.create(
            name='Consulta Pre-Adopción',
            duration_minutes=30,
            price=Decimal('300.00'),
            category='clinic',
            is_active=True,
            requires_pet=False,
        )

        tomorrow = timezone.now() + timedelta(days=1)
        appointment = Appointment.objects.create(
            owner=customer,
            pet=None,  # No pet
            service=service,
            veterinarian=vet,
            scheduled_start=tomorrow,
            scheduled_end=tomorrow + timedelta(minutes=30),
            status='scheduled',
        )

        # Complete appointment
        appointment.status = 'completed'
        appointment.completed_at = timezone.now()
        appointment.save()

        # Invoice still created
        invoice = Invoice.objects.filter(appointment=appointment).first()
        assert invoice is not None
        assert invoice.pet is None
        assert invoice.owner == customer
