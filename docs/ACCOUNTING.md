# Accounting Module

The `apps.accounting` module provides double-entry bookkeeping with chart of accounts, journal entries, vendor management, bills, and bank reconciliation.

## Table of Contents

- [Overview](#overview)
- [Models](#models)
  - [Account](#account)
  - [JournalEntry](#journalentry)
  - [JournalLine](#journalline)
  - [Vendor](#vendor)
  - [Bill](#bill)
  - [BillLine](#billline)
  - [BillPayment](#billpayment)
  - [Budget](#budget)
  - [BankReconciliation](#bankreconciliation)
- [Workflows](#workflows)
- [Integration Points](#integration-points)
- [Query Examples](#query-examples)
- [Testing](#testing)

## Overview

The accounting module provides:

- **Chart of Accounts** - Asset, liability, equity, revenue, expense accounts
- **Double-Entry Bookkeeping** - Balanced journal entries with debits/credits
- **Accounts Payable** - Vendor management, bills, payments
- **Budgeting** - Annual budget by account with monthly breakdown
- **Bank Reconciliation** - Match bank statements to ledger

## Models

Location: `apps/accounting/models.py`

### Account

Chart of accounts with hierarchical structure.

```python
ACCOUNT_TYPES = [
    ('asset', 'Asset'),
    ('liability', 'Liability'),
    ('equity', 'Equity'),
    ('revenue', 'Revenue'),
    ('expense', 'Expense'),
]

class Account(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    parent = models.ForeignKey('self', null=True, on_delete=models.CASCADE, related_name='children')
    description = models.TextField(blank=True)
    is_bank = models.BooleanField(default=False)
    is_ar = models.BooleanField(default=False)  # Accounts Receivable
    is_ap = models.BooleanField(default=False)  # Accounts Payable
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `code` | CharField | Account code (e.g., 1000, 2100) |
| `account_type` | CharField | Asset, liability, equity, revenue, expense |
| `is_bank` | Boolean | Flag for bank accounts |
| `is_ar` | Boolean | Flag for accounts receivable |
| `is_ap` | Boolean | Flag for accounts payable |

### JournalEntry

Double-entry journal entry (header).

```python
class JournalEntry(models.Model):
    date = models.DateField()
    reference = models.CharField(max_length=100)
    description = models.TextField()
    is_posted = models.BooleanField(default=False)
    posted_at = models.DateTimeField(null=True)
    posted_by = models.ForeignKey(User, null=True, related_name='posted_journal_entries')
    created_by = models.ForeignKey(User, null=True, related_name='journal_entries')

    @property
    def total_debit(self):
        return sum(line.debit for line in self.lines.all())

    @property
    def total_credit(self):
        return sum(line.credit for line in self.lines.all())

    @property
    def is_balanced(self):
        return self.total_debit == self.total_credit
```

### JournalLine

Individual debit/credit line in a journal entry.

```python
class JournalLine(models.Model):
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='journal_lines')
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    description = models.CharField(max_length=200, blank=True)
```

### Vendor

Supplier/vendor for accounts payable.

```python
PAYMENT_TERMS = [
    ('prepaid', 'Prepaid'),
    ('net15', 'Net 15'),
    ('net30', 'Net 30'),
    ('net60', 'Net 60'),
]

class Vendor(models.Model):
    name = models.CharField(max_length=200)
    rfc = models.CharField(max_length=13, blank=True)  # Mexican tax ID
    contact_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    payment_terms = models.CharField(max_length=10, choices=PAYMENT_TERMS, default='net30')
    default_expense_account = models.ForeignKey(Account, null=True, on_delete=models.SET_NULL)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
```

### Bill

Vendor invoice (accounts payable).

```python
STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('pending', 'Pending Payment'),
    ('partial', 'Partially Paid'),
    ('paid', 'Paid'),
    ('cancelled', 'Cancelled'),
]

class Bill(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name='bills')
    bill_number = models.CharField(max_length=100)
    bill_date = models.DateField()
    due_date = models.DateField()
    subtotal = models.DecimalField(max_digits=15, decimal_places=2)
    tax = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    cfdi_uuid = models.UUIDField(null=True)  # Mexican electronic invoice
    cfdi_xml = models.TextField(blank=True)

    @property
    def balance_due(self):
        return self.total - self.amount_paid
```

### BillLine

Line item on vendor bill.

```python
class BillLine(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='lines')
    description = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    expense_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='bill_lines')
```

### BillPayment

Payment to vendor.

```python
PAYMENT_METHODS = [
    ('check', 'Check'),
    ('transfer', 'Bank Transfer'),
    ('cash', 'Cash'),
    ('card', 'Credit Card'),
]

class BillPayment(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.PROTECT, related_name='payments')
    date = models.DateField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    reference = models.CharField(max_length=100, blank=True)
    bank_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='bill_payments')
```

### Budget

Annual budget by account with monthly breakdown.

```python
class Budget(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='budgets')
    year = models.IntegerField()
    jan = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    feb = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    # ... mar through dec
    dec = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    @property
    def annual_total(self):
        return sum([self.jan, self.feb, ..., self.dec])

    class Meta:
        unique_together = ['account', 'year']
```

### BankReconciliation

Bank statement reconciliation.

```python
class BankReconciliation(models.Model):
    bank_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='reconciliations')
    statement_date = models.DateField()
    statement_balance = models.DecimalField(max_digits=15, decimal_places=2)
    is_reconciled = models.BooleanField(default=False)
    reconciled_at = models.DateTimeField(null=True)
    reconciled_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    difference = models.DecimalField(max_digits=15, decimal_places=2, default=0)
```

## Workflows

### Creating a Journal Entry

```python
from apps.accounting.models import Account, JournalEntry, JournalLine
from decimal import Decimal

# Create balanced journal entry
entry = JournalEntry.objects.create(
    date=date.today(),
    reference='JE-001',
    description='Record monthly rent expense',
    created_by=user,
)

# Debit expense, credit bank
JournalLine.objects.create(
    entry=entry,
    account=Account.objects.get(code='6200'),  # Rent Expense
    debit=Decimal('15000.00'),
    credit=Decimal('0'),
)
JournalLine.objects.create(
    entry=entry,
    account=Account.objects.get(code='1100'),  # Bank
    debit=Decimal('0'),
    credit=Decimal('15000.00'),
)

# Validate and post
if entry.is_balanced:
    entry.is_posted = True
    entry.posted_at = timezone.now()
    entry.posted_by = user
    entry.save()
```

### Recording a Vendor Bill

```python
from apps.accounting.models import Vendor, Bill, BillLine, Account

# Create bill
bill = Bill.objects.create(
    vendor=Vendor.objects.get(name='Medical Supplies Inc'),
    bill_number='INV-12345',
    bill_date=date.today(),
    due_date=date.today() + timedelta(days=30),
    subtotal=Decimal('5000.00'),
    tax=Decimal('800.00'),
    total=Decimal('5800.00'),
    status='pending',
)

# Add line items
BillLine.objects.create(
    bill=bill,
    description='Surgical supplies',
    quantity=1,
    unit_price=Decimal('5000.00'),
    amount=Decimal('5000.00'),
    expense_account=Account.objects.get(code='5100'),  # Supplies expense
)
```

### Making a Payment

```python
from apps.accounting.models import Bill, BillPayment
from django.utils import timezone

bill = Bill.objects.get(pk=bill_id)

payment = BillPayment.objects.create(
    bill=bill,
    date=date.today(),
    amount=Decimal('5800.00'),
    payment_method='transfer',
    reference='TRF-2025-001',
    bank_account=Account.objects.get(is_bank=True),
)

# Update bill status
bill.amount_paid += payment.amount
if bill.balance_due == 0:
    bill.status = 'paid'
elif bill.amount_paid > 0:
    bill.status = 'partial'
bill.save()
```

## Integration Points

### With Billing Module

```python
# When customer invoice is paid, record journal entry
from apps.accounting.models import JournalEntry, JournalLine

def record_payment_received(invoice, payment):
    entry = JournalEntry.objects.create(
        date=payment.date,
        reference=f'PMT-{payment.pk}',
        description=f'Payment received for Invoice {invoice.number}',
    )
    # Debit bank, credit accounts receivable
    # ... create journal lines
```

### With Inventory

```python
# Record inventory purchase
from apps.inventory.models import PurchaseOrder
from apps.accounting.models import Bill

def create_bill_from_po(purchase_order):
    bill = Bill.objects.create(
        vendor=purchase_order.supplier.vendor,
        bill_number=purchase_order.invoice_number,
        # ... copy amounts
    )
    for line in purchase_order.items.all():
        BillLine.objects.create(
            bill=bill,
            description=line.product.name,
            quantity=line.quantity,
            unit_price=line.unit_cost,
            amount=line.total,
            expense_account=Account.objects.get(code='1200'),  # Inventory
        )
```

## Query Examples

```python
from apps.accounting.models import Account, JournalEntry, Bill, Vendor, Budget
from django.db.models import Sum
from datetime import date

# Account balances by type
asset_total = Account.objects.filter(
    account_type='asset',
    is_active=True
).aggregate(total=Sum('balance'))

# Unpaid bills
overdue = Bill.objects.filter(
    status='pending',
    due_date__lt=date.today()
)

# Vendor balances
vendors_with_balance = Vendor.objects.filter(
    balance__gt=0,
    is_active=True
).order_by('-balance')

# Monthly expenses
from django.db.models.functions import TruncMonth
monthly = JournalLine.objects.filter(
    account__account_type='expense',
    entry__is_posted=True,
    debit__gt=0
).annotate(
    month=TruncMonth('entry__date')
).values('month').annotate(
    total=Sum('debit')
).order_by('month')

# Budget vs actual
year = date.today().year
budget = Budget.objects.filter(year=year, account__account_type='expense')
```

## Testing

Location: `tests/test_accounting.py`

```bash
python -m pytest tests/test_accounting.py -v
```
