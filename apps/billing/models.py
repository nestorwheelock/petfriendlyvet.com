"""Billing models for invoicing and payment management.

Provides:
- Invoice: Bill for services/products with line items
- Payment: Payment records against invoices
- CustomerDiscount: Persistent discount levels for customers
- CouponCode: Promotional coupon codes
- AccountCredit: Customer credit balance
- ProfessionalAccount: B2B accounts for other veterinarians
- ExchangeRate: Currency exchange rates
"""
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class Invoice(models.Model):
    """Invoice for services or products."""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]

    # Identification
    invoice_number = models.CharField(max_length=50, unique=True, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='invoices'
    )
    pet = models.ForeignKey(
        'pets.Pet',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices'
    )

    # Amounts (all in MXN)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))

    # Currency display
    display_currency = models.CharField(max_length=3, default='MXN')
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    due_date = models.DateField()

    # Related records
    appointment = models.ForeignKey(
        'appointments.Appointment',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='invoices'
    )
    order = models.ForeignKey(
        'store.Order',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='invoices'
    )

    # CFDI (Mexican tax compliance)
    cfdi_uuid = models.UUIDField(null=True, blank=True)
    cfdi_xml = models.TextField(blank=True)
    cfdi_pdf = models.FileField(upload_to='cfdi/', null=True, blank=True)
    cfdi_status = models.CharField(max_length=20, blank=True)

    # Client tax info for CFDI
    client_rfc = models.CharField(max_length=13, blank=True)
    client_razon_social = models.CharField(max_length=300, blank=True)
    uso_cfdi = models.CharField(max_length=10, blank=True)
    regimen_fiscal = models.CharField(max_length=10, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Invoice {self.invoice_number}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        super().save(*args, **kwargs)

    @classmethod
    def generate_invoice_number(cls):
        """Generate a unique invoice number."""
        import random
        year = date.today().year
        while True:
            random_part = random.randint(1000, 9999)
            invoice_number = f"INV-{year}-{random_part:04d}"
            if not cls.objects.filter(invoice_number=invoice_number).exists():
                return invoice_number

    def get_balance_due(self):
        """Calculate remaining balance due."""
        return self.total - self.amount_paid

    @property
    def is_paid(self):
        """Check if invoice is fully paid."""
        return self.status == 'paid' and self.amount_paid >= self.total

    @property
    def is_overdue(self):
        """Check if invoice is past due date and unpaid."""
        if self.status == 'paid':
            return False
        return date.today() > self.due_date


class InvoiceLineItem(models.Model):
    """Individual line item on an invoice."""

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items'
    )

    # Item details
    description = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0'))
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    # Reference (optional)
    service = models.ForeignKey(
        'services.Service',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    product = models.ForeignKey(
        'store.Product',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    # SAT codes for CFDI
    clave_producto_sat = models.CharField(max_length=10, blank=True)
    clave_unidad_sat = models.CharField(max_length=5, blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.quantity}x {self.description}"


class Payment(models.Model):
    """Payment record against an invoice."""

    PAYMENT_METHODS = [
        ('stripe_card', 'Card (Online)'),
        ('stripe_subscription', 'Subscription'),
        ('manual_card', 'Card (In-Person)'),
        ('cash', 'Cash'),
        ('account_credit', 'Account Credit'),
        ('bank_transfer', 'Bank Transfer'),
        ('paypal', 'PayPal'),
    ]

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.PROTECT,
        related_name='payments'
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)

    # Stripe fields
    stripe_payment_intent = models.CharField(max_length=100, blank=True)
    stripe_charge_id = models.CharField(max_length=100, blank=True)

    # Manual entry fields
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    # Cash discount applied
    cash_discount_applied = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0')
    )

    # Recorded by
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment of ${self.amount} on {self.invoice}"


class CustomerDiscount(models.Model):
    """Persistent discount level for a customer."""

    DISCOUNT_TYPES = [
        ('vip', 'VIP Client'),
        ('rescue', 'Rescue Organization'),
        ('breeder', 'Breeder'),
        ('staff', 'Staff/Family'),
        ('professional', 'Professional (B2B)'),
        ('custom', 'Custom'),
    ]

    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='customer_discount'
    )
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2)
    applies_to_products = models.BooleanField(default=True)
    applies_to_services = models.BooleanField(default=True)

    notes = models.TextField(blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.owner} - {self.discount_percent}% ({self.get_discount_type_display()})"


class CouponCode(models.Model):
    """Promotional coupon code."""

    DISCOUNT_TYPES = [
        ('percent', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]

    code = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=200)

    # Discount
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)

    # Restrictions
    minimum_purchase = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    max_uses = models.IntegerField(null=True, blank=True)
    max_uses_per_customer = models.IntegerField(default=1)
    valid_products = models.ManyToManyField('store.Product', blank=True)
    valid_services = models.ManyToManyField('services.Service', blank=True)

    # Validity
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    # Tracking
    times_used = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code

    def is_valid(self):
        """Check if coupon is currently valid."""
        now = timezone.now()
        if not self.is_active:
            return False
        if now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        if self.max_uses and self.times_used >= self.max_uses:
            return False
        return True


class CouponUsage(models.Model):
    """Track coupon usage per customer."""

    coupon = models.ForeignKey(
        CouponCode,
        on_delete=models.CASCADE,
        related_name='usages'
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='coupon_usages'
    )
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='coupon_usage'
    )
    discount_applied = models.DecimalField(max_digits=10, decimal_places=2)
    used_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.owner} used {self.coupon.code}"


class AccountCredit(models.Model):
    """Credit balance on customer account."""

    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='account_credit'
    )
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.owner} - ${self.balance}"


class CreditTransaction(models.Model):
    """Credit additions and deductions."""

    TRANSACTION_TYPES = [
        ('add', 'Added Credit'),
        ('purchase', 'Purchase Applied'),
        ('refund', 'Refund to Credit'),
        ('expired', 'Expired'),
        ('adjustment', 'Manual Adjustment'),
    ]

    account = models.ForeignKey(
        AccountCredit,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)

    related_invoice = models.ForeignKey(
        Invoice,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    notes = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_type}: ${self.amount}"


class ProfessionalAccount(models.Model):
    """B2B account for other veterinarians."""

    PAYMENT_TERMS = [
        ('prepaid', 'Prepaid'),
        ('net15', 'Net 15'),
        ('net30', 'Net 30'),
        ('net60', 'Net 60'),
    ]

    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='professional_account'
    )

    # Business info
    business_name = models.CharField(max_length=200)
    rfc = models.CharField(max_length=13)
    contact_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    address = models.TextField(blank=True)

    # Credit terms
    payment_terms = models.CharField(max_length=10, choices=PAYMENT_TERMS, default='prepaid')
    credit_limit = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    current_balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))

    # Status
    is_approved = models.BooleanField(default=False)
    is_on_hold = models.BooleanField(default=False)
    hold_reason = models.TextField(blank=True)

    # Professional pricing
    uses_wholesale_pricing = models.BooleanField(default=True)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0'))

    # Approval
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.business_name

    def get_available_credit(self):
        """Calculate available credit."""
        return self.credit_limit - self.current_balance


class ProfessionalStatement(models.Model):
    """Monthly statement for B2B accounts."""

    account = models.ForeignKey(
        ProfessionalAccount,
        on_delete=models.CASCADE,
        related_name='statements'
    )

    period_start = models.DateField()
    period_end = models.DateField()

    opening_balance = models.DecimalField(max_digits=10, decimal_places=2)
    charges = models.DecimalField(max_digits=10, decimal_places=2)
    payments = models.DecimalField(max_digits=10, decimal_places=2)
    closing_balance = models.DecimalField(max_digits=10, decimal_places=2)

    invoices = models.ManyToManyField(Invoice)

    pdf = models.FileField(upload_to='statements/', null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-period_end']

    def __str__(self):
        return f"{self.account} - {self.period_start} to {self.period_end}"


class PaymentReminder(models.Model):
    """Track payment reminders sent."""

    CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
    ]

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='reminders'
    )

    reminder_number = models.IntegerField()
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)

    sent_at = models.DateTimeField()
    opened_at = models.DateTimeField(null=True, blank=True)

    resulted_in_payment = models.BooleanField(default=False)

    def __str__(self):
        return f"Reminder #{self.reminder_number} for {self.invoice}"


class ExchangeRate(models.Model):
    """Daily exchange rates from Banco de Mexico."""

    date = models.DateField(unique=True)
    usd_to_mxn = models.DecimalField(max_digits=10, decimal_places=4)
    eur_to_mxn = models.DecimalField(max_digits=10, decimal_places=4)
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.date}: USD={self.usd_to_mxn}, EUR={self.eur_to_mxn}"
