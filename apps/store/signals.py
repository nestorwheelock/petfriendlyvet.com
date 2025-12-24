"""Django signals for Store app.

Handles:
- Order status changes → Auto-create/update Invoice
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Order


@receiver(post_save, sender=Order)
def create_invoice_for_order(sender, instance, created, **kwargs):
    """Create or update invoice when order is saved.

    - New paid orders → Create paid invoice
    - New pending orders → Create sent invoice
    - Order marked paid → Update invoice to paid
    """
    from apps.billing.models import Invoice
    from apps.billing.services import InvoiceService

    order = instance

    # Check if invoice already exists
    existing_invoice = Invoice.objects.filter(order=order).first()

    if existing_invoice:
        # Update existing invoice if order status changed to paid
        if order.status in ['paid', 'preparing', 'shipped', 'delivered']:
            if existing_invoice.status != 'paid':
                existing_invoice.status = 'paid'
                existing_invoice.amount_paid = order.total
                if not existing_invoice.paid_at and order.paid_at:
                    existing_invoice.paid_at = order.paid_at
                existing_invoice.save()
    else:
        # Create new invoice for the order
        # Only create invoices for orders that are confirmed (not cancelled)
        if order.status not in ['cancelled', 'refunded']:
            InvoiceService.create_from_order(order)
