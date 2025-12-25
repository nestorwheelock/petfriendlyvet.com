# Billing Module

The `apps.billing` module provides comprehensive invoicing, payment processing, credit management, and Mexican tax (CFDI) compliance for the veterinary clinic.

## Table of Contents

- [Overview](#overview)
- [Models](#models)
  - [Invoice](#invoice)
  - [InvoiceLineItem](#invoicelineitem)
  - [Payment](#payment)
  - [CustomerDiscount](#customerdiscount)
  - [CouponCode](#couponcode)
  - [CouponUsage](#couponusage)
  - [AccountCredit](#accountcredit)
  - [CreditTransaction](#credittransaction)
  - [ProfessionalAccount](#professionalaccount)
  - [ProfessionalStatement](#professionalstatement)
  - [PaymentReminder](#paymentreminder)
  - [ExchangeRate](#exchangerate)
- [Services](#services)
  - [InvoiceService](#invoiceservice)
  - [PaymentService](#paymentservice)
- [Views](#views)
- [URL Patterns](#url-patterns)
- [Workflows](#workflows)
  - [Invoice Lifecycle](#invoice-lifecycle)
  - [Payment Processing](#payment-processing)
  - [Credit Management](#credit-management)
  - [B2B Professional Accounts](#b2b-professional-accounts)
- [Mexican Tax Compliance (CFDI)](#mexican-tax-compliance-cfdi)
- [Integration Points](#integration-points)
- [Query Examples](#query-examples)
- [Testing](#testing)

## Overview

The billing module handles:

- **Invoicing** - Create invoices from orders or appointments
- **Payments** - Record payments with multiple methods (cash, card, transfer)
- **Credits** - Customer credit balances and transactions
- **Discounts** - Customer-specific and coupon-based discounts
- **B2B Accounts** - Professional accounts with credit terms
- **CFDI Compliance** - Mexican electronic invoice requirements
- **Payment Reminders** - Automated overdue invoice notifications

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     Order/      │────▶│     Invoice     │────▶│     Payment     │
│   Appointment   │     │   (with items)  │     │   (one or more) │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │  CFDI (Mexican  │
                        │  Tax Invoice)   │
                        └─────────────────┘
```

## Models

### Invoice

Location: `apps/billing/models.py`

Main invoice model representing a bill to a customer.

```python
class Invoice(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]

    # Customer and practice
    customer = models.ForeignKey('crm.Customer', on_delete=models.PROTECT)
    practice = models.ForeignKey('practice.Practice', on_delete=models.PROTECT)

    # Invoice details
    invoice_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Dates
    issue_date = models.DateField()
    due_date = models.DateField()

    # Amounts (calculated fields)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance_due = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # CFDI (Mexican tax compliance)
    cfdi_uuid = models.UUIDField(null=True, blank=True)
    cfdi_xml = models.TextField(blank=True)
    cfdi_pdf = models.FileField(upload_to='cfdi/', null=True, blank=True)
    client_rfc = models.CharField(max_length=13, blank=True)  # Tax ID
    cfdi_uso = models.CharField(max_length=10, blank=True)    # CFDI usage code

    # Related objects
    order = models.ForeignKey('store.Order', on_delete=models.SET_NULL, null=True, blank=True)
    appointment = models.ForeignKey('scheduling.Appointment', on_delete=models.SET_NULL, null=True, blank=True)

    # Metadata
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `invoice_number` | CharField | Unique invoice identifier (e.g., INV-2024-0001) |
| `status` | CharField | Current invoice status |
| `subtotal` | Decimal | Sum of line items before tax |
| `tax_amount` | Decimal | IVA 16% tax |
| `total` | Decimal | Final amount including tax |
| `balance_due` | Decimal | Remaining unpaid amount |
| `cfdi_uuid` | UUID | Mexican tax authority UUID |
| `client_rfc` | CharField | Customer's RFC (tax ID) |

### InvoiceLineItem

Individual items on an invoice.

```python
class InvoiceLineItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    # Optional links to source items
    product = models.ForeignKey('store.Product', on_delete=models.SET_NULL, null=True, blank=True)
    service = models.ForeignKey('services.Service', on_delete=models.SET_NULL, null=True, blank=True)

    # SAT product/service code (for CFDI)
    sat_code = models.CharField(max_length=10, blank=True)
    sat_unit = models.CharField(max_length=10, blank=True)
```

### Payment

Records individual payments against invoices.

```python
class Payment(models.Model):
    METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('transfer', 'Bank Transfer'),
        ('check', 'Check'),
        ('credit', 'Account Credit'),
        ('other', 'Other'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    payment_date = models.DateTimeField()

    # Reference information
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    # Card payments
    card_last_four = models.CharField(max_length=4, blank=True)
    card_brand = models.CharField(max_length=20, blank=True)

    # Staff who recorded payment
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
```

### CustomerDiscount

Permanent discounts assigned to specific customers.

```python
class CustomerDiscount(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]

    customer = models.ForeignKey('crm.Customer', on_delete=models.CASCADE, related_name='discounts')
    name = models.CharField(max_length=100)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    value = models.DecimalField(max_digits=10, decimal_places=2)

    # Validity
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    # Restrictions
    applies_to_services = models.BooleanField(default=True)
    applies_to_products = models.BooleanField(default=True)
    minimum_purchase = models.DecimalField(max_digits=10, decimal_places=2, default=0)
```

### CouponCode

Promotional coupon codes.

```python
class CouponCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    # Discount details
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    value = models.DecimalField(max_digits=10, decimal_places=2)

    # Usage limits
    max_uses = models.PositiveIntegerField(null=True, blank=True)
    max_uses_per_customer = models.PositiveIntegerField(default=1)
    current_uses = models.PositiveIntegerField(default=0)

    # Validity
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)

    # Restrictions
    minimum_purchase = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    first_time_only = models.BooleanField(default=False)
```

### CouponUsage

Tracks when coupons are used.

```python
class CouponUsage(models.Model):
    coupon = models.ForeignKey(CouponCode, on_delete=models.CASCADE, related_name='usages')
    customer = models.ForeignKey('crm.Customer', on_delete=models.CASCADE)
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True)
    discount_applied = models.DecimalField(max_digits=10, decimal_places=2)
    used_at = models.DateTimeField(auto_now_add=True)
```

### AccountCredit

Customer credit balance.

```python
class AccountCredit(models.Model):
    customer = models.OneToOneField('crm.Customer', on_delete=models.CASCADE, related_name='credit_account')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def add_credit(self, amount, reason, recorded_by=None):
        """Add credit to account."""
        self.balance += amount
        self.save()
        CreditTransaction.objects.create(
            account=self,
            amount=amount,
            transaction_type='credit',
            reason=reason,
            recorded_by=recorded_by,
        )

    def use_credit(self, amount, invoice=None, recorded_by=None):
        """Use credit from account."""
        if amount > self.balance:
            raise ValueError("Insufficient credit balance")
        self.balance -= amount
        self.save()
        CreditTransaction.objects.create(
            account=self,
            amount=-amount,
            transaction_type='debit',
            invoice=invoice,
            recorded_by=recorded_by,
        )
```

### CreditTransaction

Individual credit account transactions.

```python
class CreditTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('credit', 'Credit Added'),
        ('debit', 'Credit Used'),
        ('adjustment', 'Adjustment'),
        ('refund', 'Refund'),
    ]

    account = models.ForeignKey(AccountCredit, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    reason = models.CharField(max_length=200, blank=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### ProfessionalAccount

B2B accounts for veterinary professionals with credit terms.

```python
class ProfessionalAccount(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('closed', 'Closed'),
    ]

    # Account holder
    customer = models.OneToOneField('crm.Customer', on_delete=models.CASCADE, related_name='professional_account')
    business_name = models.CharField(max_length=200)
    tax_id = models.CharField(max_length=20)  # RFC

    # Credit terms
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_terms_days = models.PositiveIntegerField(default=30)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    # Contact
    billing_email = models.EmailField()
    billing_address = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def available_credit(self):
        return self.credit_limit - self.current_balance
```

### ProfessionalStatement

Monthly statements for professional accounts.

```python
class ProfessionalStatement(models.Model):
    account = models.ForeignKey(ProfessionalAccount, on_delete=models.CASCADE, related_name='statements')
    statement_date = models.DateField()
    period_start = models.DateField()
    period_end = models.DateField()

    # Amounts
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2)
    charges = models.DecimalField(max_digits=12, decimal_places=2)
    payments = models.DecimalField(max_digits=12, decimal_places=2)
    closing_balance = models.DecimalField(max_digits=12, decimal_places=2)

    # Delivery
    sent_at = models.DateTimeField(null=True, blank=True)
    pdf_file = models.FileField(upload_to='statements/', null=True, blank=True)
```

### PaymentReminder

Automated payment reminders for overdue invoices.

```python
class PaymentReminder(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='reminders')
    reminder_type = models.CharField(max_length=20)  # first, second, final
    sent_at = models.DateTimeField()
    sent_to = models.EmailField()
    opened_at = models.DateTimeField(null=True, blank=True)
```

### ExchangeRate

Currency exchange rates for multi-currency support.

```python
class ExchangeRate(models.Model):
    from_currency = models.CharField(max_length=3)  # USD
    to_currency = models.CharField(max_length=3)    # MXN
    rate = models.DecimalField(max_digits=12, decimal_places=6)
    effective_date = models.DateField()
    source = models.CharField(max_length=50)  # banxico, xe, manual

    class Meta:
        unique_together = ['from_currency', 'to_currency', 'effective_date']
```

## Services

### InvoiceService

Location: `apps/billing/services.py`

Creates invoices from orders or appointments.

```python
class InvoiceService:
    TAX_RATE = Decimal('0.16')  # IVA 16%

    @classmethod
    def create_from_order(cls, order, status: str = None) -> Invoice:
        """Create invoice from a store order."""
        invoice = Invoice.objects.create(
            customer=order.customer,
            practice=order.practice,
            invoice_number=cls._generate_invoice_number(),
            status=status or 'sent',
            issue_date=timezone.now().date(),
            due_date=timezone.now().date() + timedelta(days=30),
            order=order,
        )

        # Create line items from order items
        for item in order.items.all():
            InvoiceLineItem.objects.create(
                invoice=invoice,
                description=item.product.name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                subtotal=item.subtotal,
                product=item.product,
            )

        cls._calculate_totals(invoice)
        return invoice

    @classmethod
    def create_from_appointment(cls, appointment, status: str = 'sent') -> Invoice:
        """Create invoice from an appointment."""
        invoice = Invoice.objects.create(
            customer=appointment.pet.owner,
            practice=appointment.practice,
            invoice_number=cls._generate_invoice_number(),
            status=status,
            issue_date=timezone.now().date(),
            due_date=timezone.now().date() + timedelta(days=30),
            appointment=appointment,
        )

        # Create line item for the service
        InvoiceLineItem.objects.create(
            invoice=invoice,
            description=appointment.service.name,
            quantity=1,
            unit_price=appointment.service.price,
            subtotal=appointment.service.price,
            service=appointment.service,
        )

        cls._calculate_totals(invoice)
        return invoice

    @classmethod
    def _calculate_totals(cls, invoice):
        """Calculate invoice totals from line items."""
        subtotal = invoice.items.aggregate(total=Sum('subtotal'))['total'] or Decimal('0')
        tax_amount = subtotal * cls.TAX_RATE
        total = subtotal + tax_amount

        invoice.subtotal = subtotal
        invoice.tax_amount = tax_amount
        invoice.total = total
        invoice.balance_due = total - invoice.amount_paid
        invoice.save()

    @classmethod
    def _generate_invoice_number(cls) -> str:
        """Generate unique invoice number."""
        year = timezone.now().year
        last_invoice = Invoice.objects.filter(
            invoice_number__startswith=f'INV-{year}-'
        ).order_by('-invoice_number').first()

        if last_invoice:
            last_num = int(last_invoice.invoice_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        return f'INV-{year}-{new_num:04d}'
```

### PaymentService

Records payments and updates invoice balances.

```python
class PaymentService:
    @classmethod
    def record_payment(
        cls,
        invoice: Invoice,
        amount: Decimal,
        payment_method: str,
        reference_number: str = '',
        notes: str = '',
        recorded_by=None,
        card_last_four: str = '',
        card_brand: str = '',
    ) -> Payment:
        """Record a payment against an invoice."""
        payment = Payment.objects.create(
            invoice=invoice,
            amount=amount,
            payment_method=payment_method,
            payment_date=timezone.now(),
            reference_number=reference_number,
            notes=notes,
            recorded_by=recorded_by,
            card_last_four=card_last_four,
            card_brand=card_brand,
        )

        cls.update_invoice_balance(invoice)
        return payment

    @classmethod
    def update_invoice_balance(cls, invoice: Invoice) -> None:
        """Recalculate invoice balance after payment."""
        total_paid = invoice.payments.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')

        invoice.amount_paid = total_paid
        invoice.balance_due = invoice.total - total_paid

        # Update status based on balance
        if invoice.balance_due <= 0:
            invoice.status = 'paid'
        elif total_paid > 0:
            invoice.status = 'partial'

        invoice.save()
```

## Views

Location: `apps/billing/views.py`

### InvoiceListView

List all invoices for the current user/practice.

```python
class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = 'billing/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 25

    def get_queryset(self):
        return Invoice.objects.filter(
            practice=self.request.user.practice
        ).select_related('customer').order_by('-issue_date')
```

### InvoiceDetailView

View individual invoice with line items and payments.

```python
class InvoiceDetailView(LoginRequiredMixin, DetailView):
    model = Invoice
    template_name = 'billing/invoice_detail.html'
    context_object_name = 'invoice'

    def get_queryset(self):
        return Invoice.objects.filter(
            practice=self.request.user.practice
        ).prefetch_related('items', 'payments')
```

### CreditBalanceView

View customer credit account balance and transactions.

```python
class CreditBalanceView(LoginRequiredMixin, TemplateView):
    template_name = 'billing/credit_balance.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.request.user.customer

        try:
            credit_account = customer.credit_account
            context['credit_account'] = credit_account
            context['transactions'] = credit_account.transactions.order_by('-created_at')[:20]
        except AccountCredit.DoesNotExist:
            context['credit_account'] = None

        return context
```

## URL Patterns

Location: `apps/billing/urls.py`

```python
app_name = 'billing'

urlpatterns = [
    path('invoices/', views.InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('credit/', views.CreditBalanceView.as_view(), name='credit_balance'),
]
```

## Workflows

### Invoice Lifecycle

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  DRAFT  │───▶│  SENT   │───▶│ PARTIAL │───▶│  PAID   │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
     │              │              │
     │              ▼              │
     │         ┌─────────┐         │
     └────────▶│ OVERDUE │◀────────┘
               └─────────┘
                    │
                    ▼
              ┌───────────┐
              │ CANCELLED │
              └───────────┘
```

**Status Transitions:**

| From | To | Trigger |
|------|-----|---------|
| draft | sent | Invoice sent to customer |
| sent | partial | Partial payment received |
| sent | paid | Full payment received |
| sent | overdue | Due date passed |
| partial | paid | Remaining balance paid |
| partial | overdue | Due date passed |
| any | cancelled | Invoice cancelled |

### Payment Processing

```python
from apps.billing.services import PaymentService

# Record a cash payment
payment = PaymentService.record_payment(
    invoice=invoice,
    amount=Decimal('500.00'),
    payment_method='cash',
    recorded_by=request.user,
)

# Record a card payment
payment = PaymentService.record_payment(
    invoice=invoice,
    amount=Decimal('1500.00'),
    payment_method='card',
    card_last_four='4242',
    card_brand='Visa',
    reference_number='AUTH-123456',
    recorded_by=request.user,
)

# Apply account credit
from apps.billing.models import AccountCredit

credit_account = customer.credit_account
credit_account.use_credit(
    amount=Decimal('200.00'),
    invoice=invoice,
    recorded_by=request.user,
)
```

### Credit Management

```python
from apps.billing.models import AccountCredit

# Get or create credit account
credit_account, created = AccountCredit.objects.get_or_create(
    customer=customer,
    defaults={'balance': Decimal('0')}
)

# Add credit (e.g., from refund)
credit_account.add_credit(
    amount=Decimal('100.00'),
    reason='Refund for cancelled order #123',
    recorded_by=staff_user,
)

# Use credit for payment
credit_account.use_credit(
    amount=Decimal('50.00'),
    invoice=invoice,
    recorded_by=staff_user,
)

# View transaction history
transactions = credit_account.transactions.order_by('-created_at')
for tx in transactions:
    print(f"{tx.created_at}: {tx.transaction_type} {tx.amount}")
```

### B2B Professional Accounts

```python
from apps.billing.models import ProfessionalAccount

# Create professional account
pro_account = ProfessionalAccount.objects.create(
    customer=customer,
    business_name='Clínica Veterinaria ABC',
    tax_id='ABC123456789',
    credit_limit=Decimal('50000.00'),
    payment_terms_days=30,
    billing_email='billing@clinicaabc.com',
    billing_address='Av. Principal 123, CDMX',
    status='pending',
)

# Approve account
pro_account.status = 'active'
pro_account.approved_by = admin_user
pro_account.approved_at = timezone.now()
pro_account.save()

# Check available credit
available = pro_account.available_credit
if available >= invoice.total:
    # Allow credit purchase
    pro_account.current_balance += invoice.total
    pro_account.save()

# Generate monthly statement
from datetime import date
from dateutil.relativedelta import relativedelta

period_end = date.today().replace(day=1) - timedelta(days=1)
period_start = period_end.replace(day=1)

statement = ProfessionalStatement.objects.create(
    account=pro_account,
    statement_date=date.today(),
    period_start=period_start,
    period_end=period_end,
    opening_balance=previous_balance,
    charges=monthly_charges,
    payments=monthly_payments,
    closing_balance=pro_account.current_balance,
)
```

## Mexican Tax Compliance (CFDI)

The billing module supports CFDI (Comprobante Fiscal Digital por Internet) for Mexican tax compliance.

### Key CFDI Fields

| Field | Description | Example |
|-------|-------------|---------|
| `cfdi_uuid` | SAT-assigned unique identifier | `550e8400-e29b-41d4-a716-446655440000` |
| `cfdi_xml` | XML representation of invoice | `<?xml version="1.0"...` |
| `client_rfc` | Customer's RFC (tax ID) | `XAXX010101000` |
| `cfdi_uso` | CFDI usage code | `G03` (Gastos en general) |
| `sat_code` | SAT product/service code | `01010101` |
| `sat_unit` | SAT unit of measure | `E48` (Servicio) |

### Common CFDI Usage Codes

| Code | Description |
|------|-------------|
| G01 | Adquisición de mercancías |
| G03 | Gastos en general |
| D01 | Honorarios médicos |
| D02 | Gastos médicos por incapacidad |
| P01 | Por definir |

### CFDI Generation Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Invoice Created │────▶│ Request RFC &   │────▶│ Generate CFDI   │
│                 │     │ CFDI Usage      │     │ XML             │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Store UUID &   │◀────│  Receive UUID   │◀────│ Submit to PAC   │
│  PDF            │     │  from SAT       │     │ (CFDI provider) │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Integration Points

### With Store Module

```python
from apps.billing.services import InvoiceService

# After order is completed
def complete_order(order):
    order.status = 'completed'
    order.save()

    # Create invoice
    invoice = InvoiceService.create_from_order(order)
    return invoice
```

### With Scheduling Module

```python
# After appointment is completed
def complete_appointment(appointment):
    appointment.status = 'completed'
    appointment.save()

    # Create invoice
    invoice = InvoiceService.create_from_appointment(appointment)
    return invoice
```

### With CRM Module

```python
from apps.crm.models import Customer
from apps.billing.models import Invoice, AccountCredit

# Get customer billing summary
customer = Customer.objects.get(pk=customer_id)

# All invoices
invoices = Invoice.objects.filter(customer=customer)

# Outstanding balance
outstanding = invoices.filter(
    status__in=['sent', 'partial', 'overdue']
).aggregate(total=Sum('balance_due'))['total']

# Credit balance
try:
    credit = customer.credit_account.balance
except AccountCredit.DoesNotExist:
    credit = Decimal('0')
```

### With Audit Module

Billing pages are automatically logged by AuditMiddleware with `sensitivity='high'`:

- `/billing/invoices/` - Invoice list view
- `/billing/invoices/<id>/` - Invoice detail view

## Query Examples

### Invoice Queries

```python
from apps.billing.models import Invoice
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

# Unpaid invoices
unpaid = Invoice.objects.filter(
    status__in=['sent', 'partial', 'overdue']
)

# Overdue invoices
overdue = Invoice.objects.filter(
    status='overdue'
) | Invoice.objects.filter(
    status__in=['sent', 'partial'],
    due_date__lt=timezone.now().date()
)

# Revenue this month
from datetime import date
first_of_month = date.today().replace(day=1)

monthly_revenue = Invoice.objects.filter(
    status='paid',
    issue_date__gte=first_of_month
).aggregate(total=Sum('total'))['total']

# Top customers by revenue
top_customers = Invoice.objects.filter(
    status='paid'
).values('customer__name').annotate(
    total_revenue=Sum('total'),
    invoice_count=Count('id')
).order_by('-total_revenue')[:10]

# Invoice aging report
aging = {
    'current': Invoice.objects.filter(
        status__in=['sent', 'partial'],
        due_date__gte=timezone.now().date()
    ).aggregate(total=Sum('balance_due'))['total'] or 0,

    '1-30': Invoice.objects.filter(
        status__in=['sent', 'partial', 'overdue'],
        due_date__lt=timezone.now().date(),
        due_date__gte=timezone.now().date() - timedelta(days=30)
    ).aggregate(total=Sum('balance_due'))['total'] or 0,

    '31-60': Invoice.objects.filter(
        status__in=['sent', 'partial', 'overdue'],
        due_date__lt=timezone.now().date() - timedelta(days=30),
        due_date__gte=timezone.now().date() - timedelta(days=60)
    ).aggregate(total=Sum('balance_due'))['total'] or 0,

    '60+': Invoice.objects.filter(
        status__in=['sent', 'partial', 'overdue'],
        due_date__lt=timezone.now().date() - timedelta(days=60)
    ).aggregate(total=Sum('balance_due'))['total'] or 0,
}
```

### Payment Queries

```python
from apps.billing.models import Payment
from django.db.models import Sum

# Payments by method
payments_by_method = Payment.objects.values('payment_method').annotate(
    total=Sum('amount'),
    count=Count('id')
)

# Daily payment totals
from django.db.models.functions import TruncDate

daily_payments = Payment.objects.annotate(
    date=TruncDate('payment_date')
).values('date').annotate(
    total=Sum('amount')
).order_by('-date')[:30]
```

### Coupon Queries

```python
from apps.billing.models import CouponCode, CouponUsage

# Active coupons
active_coupons = CouponCode.objects.filter(
    is_active=True,
    start_date__lte=timezone.now().date(),
    end_date__gte=timezone.now().date()
)

# Coupon usage statistics
coupon_stats = CouponUsage.objects.values('coupon__code').annotate(
    uses=Count('id'),
    total_discount=Sum('discount_applied')
).order_by('-uses')
```

## Testing

### Unit Tests

Location: `tests/test_billing.py`

```bash
# Run billing unit tests
python -m pytest tests/test_billing.py -v
```

### Key Test Scenarios

1. **Invoice Creation**
   - Create invoice from order
   - Create invoice from appointment
   - Calculate totals with IVA 16%
   - Generate unique invoice numbers

2. **Payment Processing**
   - Record full payment
   - Record partial payment
   - Update invoice status after payment
   - Apply account credit

3. **Discount Application**
   - Apply customer discount
   - Apply coupon code
   - Validate coupon restrictions

4. **Professional Accounts**
   - Create and approve account
   - Check credit limits
   - Generate monthly statements

### Browser Tests

Location: `tests/e2e/browser/test_billing.py`

```bash
# Run billing browser tests
python -m pytest tests/e2e/browser/test_billing.py -v

# Run with visible browser
python -m pytest tests/e2e/browser/test_billing.py -v --headed --slowmo=500
```
