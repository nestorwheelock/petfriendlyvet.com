"""Django signals for Appointments app.

Handles:
- Appointment completed → Auto-create Invoice
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Appointment


@receiver(post_save, sender=Appointment)
def create_invoice_on_completion(sender, instance, **kwargs):
    """Create invoice when appointment is completed.

    Only creates invoice when:
    - Status changes to 'completed'
    - No invoice already exists for this appointment
    """
    from apps.billing.models import Invoice
    from apps.billing.services import InvoiceService

    appointment = instance

    # Only create invoice for completed appointments
    if appointment.status != 'completed':
        return

    # Check if invoice already exists
    existing_invoice = Invoice.objects.filter(appointment=appointment).first()
    if existing_invoice:
        return

    # Create invoice for the completed appointment
    InvoiceService.create_from_appointment(appointment)
