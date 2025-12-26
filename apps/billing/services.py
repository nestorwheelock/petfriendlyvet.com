"""Billing services for invoice creation and payment processing.

Provides:
- InvoiceService: Create invoices from orders and appointments
- PaymentService: Record and process payments
- calculate_tax: Calculate tax for an amount
- get_cfdi_tax_node: Generate CFDI-compliant tax node data
- seed_default_tax_rates: Seed default Mexico tax rates
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from .models import Invoice, InvoiceLineItem, Payment


class InvoiceService:
    """Service for creating and managing invoices."""

    TAX_RATE = Decimal('0.16')  # IVA 16%
    DEFAULT_PAYMENT_TERMS_DAYS = 7

    @classmethod
    @transaction.atomic
    def create_from_order(cls, order, status: str = None) -> Invoice:
        """Create an invoice from a store order.

        Args:
            order: Order instance to create invoice from
            status: Override invoice status (defaults based on order.status)

        Returns:
            Created Invoice instance
        """
        from apps.store.models import Order

        # Determine invoice status based on order payment status
        if status is None:
            if order.status == 'paid' and order.paid_at:
                status = 'paid'
            elif order.status in ['preparing', 'shipped', 'delivered']:
                status = 'paid'
            else:
                status = 'sent'

        # Calculate amounts from order
        subtotal = order.subtotal + order.shipping_cost
        tax_amount = order.tax
        total = order.total
        discount_amount = order.discount_amount

        # Set due date and paid_at
        due_date = date.today() + timedelta(days=cls.DEFAULT_PAYMENT_TERMS_DAYS)
        paid_at = order.paid_at if status == 'paid' else None
        amount_paid = total if status == 'paid' else Decimal('0')

        # Create invoice
        invoice = Invoice.objects.create(
            owner=order.user,
            order=order,
            subtotal=subtotal,
            discount_amount=discount_amount,
            tax_amount=tax_amount,
            total=total,
            amount_paid=amount_paid,
            status=status,
            due_date=due_date,
            paid_at=paid_at,
        )

        # Create line items from order items
        for order_item in order.items.all():
            InvoiceLineItem.objects.create(
                invoice=invoice,
                description=order_item.product_name,
                quantity=order_item.quantity,
                unit_price=order_item.price,
                line_total=order_item.subtotal,
                product=order_item.product,
                clave_producto_sat='43231500',  # General merchandise
                clave_unidad_sat='H87',  # Piece
            )

        # Add shipping as line item if present
        if order.shipping_cost > 0:
            InvoiceLineItem.objects.create(
                invoice=invoice,
                description='Shipping / Envío',
                quantity=1,
                unit_price=order.shipping_cost,
                line_total=order.shipping_cost,
                clave_producto_sat='78102200',  # Delivery services
                clave_unidad_sat='E48',  # Unit of service
            )

        return invoice

    @classmethod
    @transaction.atomic
    def create_from_appointment(cls, appointment, status: str = 'sent') -> Invoice:
        """Create an invoice from an appointment.

        Args:
            appointment: Appointment instance to create invoice from
            status: Invoice status (defaults to 'sent')

        Returns:
            Created Invoice instance
        """
        service = appointment.service
        subtotal = service.price
        tax_amount = subtotal * cls.TAX_RATE
        total = subtotal + tax_amount

        due_date = date.today() + timedelta(days=cls.DEFAULT_PAYMENT_TERMS_DAYS)

        invoice = Invoice.objects.create(
            owner=appointment.owner,
            pet=appointment.pet,
            appointment=appointment,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total=total,
            status=status,
            due_date=due_date,
        )

        # Create line item for the service
        InvoiceLineItem.objects.create(
            invoice=invoice,
            description=service.name,
            quantity=1,
            unit_price=service.price,
            line_total=service.price,
            service=appointment.service if hasattr(appointment, 'billing_service') else None,
            clave_producto_sat='85121800',  # Veterinary services
            clave_unidad_sat='E48',  # Unit of service
        )

        return invoice

    @classmethod
    def get_or_create_for_order(cls, order) -> Invoice:
        """Get existing invoice for order or create one.

        Args:
            order: Order instance

        Returns:
            Invoice instance (existing or newly created)
        """
        existing = Invoice.objects.filter(order=order).first()
        if existing:
            return existing
        return cls.create_from_order(order)

    @classmethod
    def get_or_create_for_appointment(cls, appointment) -> Invoice:
        """Get existing invoice for appointment or create one.

        Args:
            appointment: Appointment instance

        Returns:
            Invoice instance (existing or newly created)
        """
        existing = Invoice.objects.filter(appointment=appointment).first()
        if existing:
            return existing
        return cls.create_from_appointment(appointment)


class PaymentService:
    """Service for recording and processing payments."""

    @classmethod
    @transaction.atomic
    def record_payment(
        cls,
        invoice: Invoice,
        amount: Decimal,
        payment_method: str,
        recorded_by=None,
        reference_number: str = '',
        notes: str = '',
        cash_discount: Decimal = Decimal('0'),
    ) -> Payment:
        """Record a payment against an invoice.

        Args:
            invoice: Invoice to record payment against
            amount: Payment amount
            payment_method: Payment method code
            recorded_by: User recording the payment
            reference_number: Optional payment reference
            notes: Optional notes
            cash_discount: Optional cash discount applied

        Returns:
            Created Payment instance
        """
        payment = Payment.objects.create(
            invoice=invoice,
            amount=amount,
            payment_method=payment_method,
            recorded_by=recorded_by,
            reference_number=reference_number,
            notes=notes,
            cash_discount_applied=cash_discount,
        )

        # Update invoice balance
        cls.update_invoice_balance(invoice)

        return payment

    @classmethod
    def update_invoice_balance(cls, invoice: Invoice) -> None:
        """Update invoice amount_paid and status based on payments.

        Args:
            invoice: Invoice to update
        """
        total_paid = invoice.payments.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')

        invoice.amount_paid = total_paid

        if total_paid >= invoice.total:
            invoice.status = 'paid'
            if not invoice.paid_at:
                invoice.paid_at = timezone.now()
        elif total_paid > 0:
            invoice.status = 'partial'
        else:
            # Keep current status if no payments
            pass

        invoice.save()

    @classmethod
    def get_outstanding_balance(cls, invoice: Invoice) -> Decimal:
        """Get remaining balance on invoice.

        Args:
            invoice: Invoice to check

        Returns:
            Outstanding balance amount
        """
        return invoice.total - invoice.amount_paid

    @classmethod
    def is_fully_paid(cls, invoice: Invoice) -> bool:
        """Check if invoice is fully paid.

        Args:
            invoice: Invoice to check

        Returns:
            True if fully paid
        """
        return invoice.amount_paid >= invoice.total


# Tax calculation functions for Mexico SAT compliance

def calculate_tax(amount, tax_rate, include_in_price=False):
    """Calculate tax for an amount.

    Args:
        amount: Base amount (Decimal or float)
        tax_rate: TaxRate instance
        include_in_price: If True, tax is included in amount (extract it)

    Returns:
        dict with subtotal, tax_amount, total, tax_rate
    """
    amount = Decimal(str(amount))
    rate = tax_rate.rate

    if tax_rate.sat_tipo_factor == 'Exento':
        return {
            'subtotal': amount,
            'tax_amount': Decimal('0.00'),
            'total': amount,
            'tax_rate': tax_rate,
        }

    if include_in_price:
        # Extract tax from total
        subtotal = amount / (1 + rate)
        tax_amount = amount - subtotal
    else:
        # Add tax to subtotal
        subtotal = amount
        tax_amount = amount * rate

    return {
        'subtotal': subtotal.quantize(Decimal('0.01')),
        'tax_amount': tax_amount.quantize(Decimal('0.01')),
        'total': (subtotal + tax_amount).quantize(Decimal('0.01')),
        'tax_rate': tax_rate,
    }


def get_cfdi_tax_node(tax_calculation):
    """Generate SAT CFDI tax node data.

    Args:
        tax_calculation: dict returned by calculate_tax

    Returns:
        dict ready for CFDI XML generation
    """
    tax_rate = tax_calculation['tax_rate']

    if tax_rate.sat_tipo_factor == 'Exento':
        return {
            'Impuesto': tax_rate.sat_impuesto_code,
            'TipoFactor': 'Exento',
        }

    return {
        'Base': str(tax_calculation['subtotal']),
        'Impuesto': tax_rate.sat_impuesto_code,
        'TipoFactor': tax_rate.sat_tipo_factor,
        'TasaOCuota': f"{tax_rate.rate:.6f}",
        'Importe': str(tax_calculation['tax_amount']),
    }


def seed_default_tax_rates():
    """Seed default Mexico tax rates.

    Creates standard IVA rates if they don't exist:
    - IVA 16% (default)
    - IVA 0%
    - IVA Exento
    - IEPS 8% (common for some products)
    """
    from .models import TaxRate

    default_rates = [
        {
            'code': 'IVA16',
            'name': 'IVA 16%',
            'tax_type': 'iva',
            'rate': Decimal('0.1600'),
            'sat_impuesto_code': '002',
            'sat_tipo_factor': 'Tasa',
            'is_default': True,
        },
        {
            'code': 'IVA0',
            'name': 'IVA 0%',
            'tax_type': 'iva',
            'rate': Decimal('0.0000'),
            'sat_impuesto_code': '002',
            'sat_tipo_factor': 'Tasa',
            'is_default': False,
        },
        {
            'code': 'IVA_EXEMPT',
            'name': 'IVA Exento',
            'tax_type': 'iva',
            'rate': Decimal('0.0000'),
            'sat_impuesto_code': '002',
            'sat_tipo_factor': 'Exento',
            'is_default': False,
        },
        {
            'code': 'IEPS8',
            'name': 'IEPS 8%',
            'tax_type': 'ieps',
            'rate': Decimal('0.0800'),
            'sat_impuesto_code': '003',
            'sat_tipo_factor': 'Tasa',
            'is_default': False,
        },
    ]

    for rate_data in default_rates:
        TaxRate.objects.get_or_create(
            code=rate_data['code'],
            defaults=rate_data
        )
