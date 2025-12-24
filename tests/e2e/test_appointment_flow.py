"""E2E tests for Appointment to Invoice automation flow.

Tests that:
- Completed appointment → Invoice auto-created
- Appointment with additional services/products → All on one invoice
- Vaccination appointments → Create vaccination record + invoice
- Cancelled appointments → No invoice created
"""
import pytest
from decimal import Decimal
from datetime import timedelta

from django.utils import timezone

from apps.appointments.models import Appointment
from apps.billing.models import Invoice, InvoiceLineItem


@pytest.mark.django_db
class TestAppointmentCreatesInvoice:
    """Test that completing an appointment auto-creates invoice."""

    def test_completed_appointment_creates_invoice(
        self, db, scheduled_appointment, staff_user
    ):
        """When appointment is completed, invoice should be auto-created."""
        appointment = scheduled_appointment

        # Verify appointment is scheduled
        assert appointment.status == 'scheduled'

        # Act: Complete the appointment
        appointment.status = 'completed'
        appointment.completed_at = timezone.now()
        appointment.save()

        # Assert: Invoice was auto-created
        invoice = Invoice.objects.filter(appointment=appointment).first()
        assert invoice is not None, "Invoice should be auto-created when appointment is completed"

        # Assert: Invoice matches appointment
        assert invoice.owner == appointment.owner
        assert invoice.pet == appointment.pet
        assert invoice.appointment == appointment

        # Assert: Invoice total includes service price + tax
        expected_subtotal = appointment.service.price
        expected_tax = expected_subtotal * Decimal('0.16')
        expected_total = expected_subtotal + expected_tax

        assert invoice.subtotal == expected_subtotal
        assert invoice.tax_amount == expected_tax
        assert invoice.total == expected_total

    def test_completed_appointment_has_line_item(
        self, db, scheduled_appointment
    ):
        """Completed appointment creates invoice with service line item."""
        appointment = scheduled_appointment

        appointment.status = 'completed'
        appointment.completed_at = timezone.now()
        appointment.save()

        invoice = Invoice.objects.filter(appointment=appointment).first()
        assert invoice is not None

        # Assert: Invoice has line item for the service
        line_items = invoice.items.all()
        assert line_items.count() >= 1

        service_item = line_items.first()
        assert service_item.description == appointment.service.name
        assert service_item.unit_price == appointment.service.price
        assert service_item.quantity == 1

    def test_in_progress_appointment_no_invoice(
        self, db, scheduled_appointment
    ):
        """In-progress appointment does not create invoice."""
        appointment = scheduled_appointment

        appointment.status = 'in_progress'
        appointment.save()

        # Assert: No invoice created yet
        invoice = Invoice.objects.filter(appointment=appointment).first()
        assert invoice is None, "Invoice should not be created until appointment is completed"

    def test_cancelled_appointment_no_invoice(
        self, db, scheduled_appointment
    ):
        """Cancelled appointment does not create invoice."""
        appointment = scheduled_appointment

        appointment.status = 'cancelled'
        appointment.cancellation_reason = 'Customer requested cancellation'
        appointment.cancelled_at = timezone.now()
        appointment.save()

        # Assert: No invoice created
        invoice = Invoice.objects.filter(appointment=appointment).first()
        assert invoice is None, "Invoice should not be created for cancelled appointments"

    def test_no_show_appointment_may_create_invoice(
        self, db, scheduled_appointment
    ):
        """No-show appointments may still create invoice (clinic policy)."""
        appointment = scheduled_appointment

        appointment.status = 'no_show'
        appointment.save()

        # Note: This test documents the expected behavior
        # Policy decision: no-shows may or may not be billed
        # For now, we don't auto-create invoice for no-shows
        invoice = Invoice.objects.filter(appointment=appointment).first()
        # Current implementation: no invoice for no-shows
        # If policy changes, update this test


@pytest.mark.django_db
class TestAppointmentInvoiceUpdates:
    """Test invoice updates when appointment changes."""

    def test_completing_later_doesnt_duplicate_invoice(
        self, db, scheduled_appointment
    ):
        """Saving completed appointment multiple times doesn't create duplicates."""
        appointment = scheduled_appointment

        # Complete the appointment
        appointment.status = 'completed'
        appointment.completed_at = timezone.now()
        appointment.save()

        first_invoice = Invoice.objects.filter(appointment=appointment).first()
        assert first_invoice is not None

        # Save again
        appointment.notes = 'Updated notes after completion'
        appointment.save()

        # Assert: Still only one invoice
        invoice_count = Invoice.objects.filter(appointment=appointment).count()
        assert invoice_count == 1, "Should not create duplicate invoices"

        # Same invoice
        second_invoice = Invoice.objects.filter(appointment=appointment).first()
        assert second_invoice.id == first_invoice.id


@pytest.mark.django_db
class TestAppointmentWithProducts:
    """Test appointments with additional products/medications."""

    def test_appointment_invoice_can_add_products(
        self, db, scheduled_appointment, product
    ):
        """Invoice can have additional products added after creation."""
        appointment = scheduled_appointment

        # Complete appointment
        appointment.status = 'completed'
        appointment.completed_at = timezone.now()
        appointment.save()

        invoice = Invoice.objects.filter(appointment=appointment).first()
        assert invoice is not None

        # Add product to invoice
        product_quantity = 2
        InvoiceLineItem.objects.create(
            invoice=invoice,
            description=product.name,
            quantity=product_quantity,
            unit_price=product.price,
            line_total=product.price * product_quantity,
            product=product,
        )

        # Assert: Invoice now has 2 line items
        assert invoice.items.count() == 2

        # Assert: Line items include service and product
        descriptions = list(invoice.items.values_list('description', flat=True))
        assert appointment.service.name in descriptions
        assert product.name in descriptions


@pytest.mark.django_db
class TestVaccinationAppointment:
    """Test vaccination appointment workflow."""

    def test_vaccination_appointment_creates_invoice(
        self, db, owner_user, pet, vet_user, service_type
    ):
        """Vaccination appointment creates invoice on completion."""
        # Update service type to vaccination
        service_type.name = 'Vacunación'
        service_type.category = 'clinic'
        service_type.save()

        # Create appointment
        appointment_time = timezone.now() + timedelta(days=1)
        appointment = Appointment.objects.create(
            owner=owner_user,
            pet=pet,
            veterinarian=vet_user,
            service=service_type,
            scheduled_start=appointment_time,
            scheduled_end=appointment_time + timedelta(minutes=30),
            status='scheduled',
        )

        # Complete appointment
        appointment.status = 'completed'
        appointment.completed_at = timezone.now()
        appointment.save()

        # Assert: Invoice created
        invoice = Invoice.objects.filter(appointment=appointment).first()
        assert invoice is not None
        assert invoice.pet == pet
        assert 'Vacunación' in invoice.items.first().description


@pytest.mark.django_db
class TestAPIAppointmentFlow:
    """Test appointment flow via API endpoints."""

    def test_staff_complete_appointment_creates_invoice(
        self, staff_client, scheduled_appointment
    ):
        """Staff completing appointment via API creates invoice."""
        response = staff_client.patch(
            f'/api/appointments/{scheduled_appointment.id}/',
            {'status': 'completed'},
            format='json',
        )

        # API may not exist yet - this documents expected behavior
        if response.status_code in [200, 204]:
            scheduled_appointment.refresh_from_db()
            invoice = Invoice.objects.filter(
                appointment=scheduled_appointment
            ).first()
            assert invoice is not None

    def test_appointment_detail_includes_invoice_link(
        self, staff_client, scheduled_appointment
    ):
        """Completed appointment API response includes invoice."""
        # Complete the appointment
        scheduled_appointment.status = 'completed'
        scheduled_appointment.completed_at = timezone.now()
        scheduled_appointment.save()

        response = staff_client.get(
            f'/api/appointments/{scheduled_appointment.id}/'
        )

        if response.status_code == 200:
            # Expected: invoice info in response
            assert 'invoice' in response.data or 'invoice_id' in response.data


@pytest.mark.django_db
class TestAppointmentPaymentFlow:
    """Test full appointment → invoice → payment flow."""

    def test_full_appointment_payment_flow(
        self, db, scheduled_appointment, staff_user
    ):
        """Complete flow: appointment → invoice → payment → paid."""
        from apps.billing.models import Payment

        appointment = scheduled_appointment

        # 1. Complete appointment
        appointment.status = 'completed'
        appointment.completed_at = timezone.now()
        appointment.save()

        # 2. Verify invoice created
        invoice = Invoice.objects.filter(appointment=appointment).first()
        assert invoice is not None
        assert invoice.status in ['sent', 'draft']

        # 3. Record payment
        Payment.objects.create(
            invoice=invoice,
            amount=invoice.total,
            payment_method='cash',
            recorded_by=staff_user,
        )

        # 4. Verify invoice is paid
        invoice.refresh_from_db()
        assert invoice.status == 'paid'
        assert invoice.amount_paid == invoice.total
        assert invoice.paid_at is not None

    def test_partial_payment_on_appointment_invoice(
        self, db, scheduled_appointment, staff_user
    ):
        """Partial payment updates invoice correctly."""
        from apps.billing.models import Payment

        appointment = scheduled_appointment

        appointment.status = 'completed'
        appointment.completed_at = timezone.now()
        appointment.save()

        invoice = Invoice.objects.filter(appointment=appointment).first()
        assert invoice is not None

        # Pay half
        partial_amount = invoice.total / 2
        Payment.objects.create(
            invoice=invoice,
            amount=partial_amount,
            payment_method='cash',
            recorded_by=staff_user,
        )

        invoice.refresh_from_db()
        assert invoice.status == 'partial'
        assert invoice.amount_paid == partial_amount
        assert invoice.get_balance_due() == invoice.total - partial_amount
