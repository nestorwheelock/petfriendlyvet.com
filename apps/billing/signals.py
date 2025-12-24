"""Django signals for Billing app.

Handles:
- Payment recorded → Update Invoice balance and status
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Payment


@receiver(post_save, sender=Payment)
def update_invoice_on_payment(sender, instance, created, **kwargs):
    """Update invoice balance when a payment is recorded.

    - Sum all payments for the invoice
    - Update invoice.amount_paid
    - Set status to 'partial' or 'paid' based on balance
    - Set paid_at timestamp when fully paid
    """
    from .services import PaymentService

    if created:
        # Only update when a new payment is created
        PaymentService.update_invoice_balance(instance.invoice)
