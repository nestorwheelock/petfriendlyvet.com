# T-064: Accounting & Financial Models

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md and [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement double-entry accounting system models
**Related Story**: S-026
**Epoch**: 6
**Estimate**: 5 hours

### Constraints
**Allowed File Paths**: apps/accounting/
**Forbidden Paths**: None

### Deliverables
- [ ] Chart of accounts model
- [ ] Journal entry models
- [ ] Accounts payable models
- [ ] Bank reconciliation models
- [ ] Budget models
- [ ] Accounting service

### Wireframe Reference
See: `planning/wireframes/22-accounting-dashboard.txt`

### Implementation Details

#### Models
```python
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from decimal import Decimal

User = get_user_model()


class Account(models.Model):
    """Chart of accounts."""

    ACCOUNT_TYPES = [
        ('asset', 'Activo'),
        ('liability', 'Pasivo'),
        ('equity', 'Capital'),
        ('revenue', 'Ingreso'),
        ('expense', 'Gasto'),
    ]

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    name_es = models.CharField(max_length=200, blank=True)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)

    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE,
        null=True, blank=True, related_name='children'
    )

    description = models.TextField(blank=True)

    # Special flags
    is_bank = models.BooleanField(default=False)
    is_ar = models.BooleanField(default=False)  # Accounts Receivable
    is_ap = models.BooleanField(default=False)  # Accounts Payable
    is_cash = models.BooleanField(default=False)
    is_tax = models.BooleanField(default=False)  # IVA accounts

    # Current balance (cached)
    balance = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )
    balance_updated = models.DateTimeField(null=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def normal_balance(self):
        """Return expected balance direction."""
        if self.account_type in ['asset', 'expense']:
            return 'debit'
        return 'credit'

    def recalculate_balance(self):
        """Recalculate balance from journal lines."""
        from django.db.models import Sum

        lines = self.journal_lines.filter(entry__is_posted=True)

        debits = lines.aggregate(Sum('debit'))['debit__sum'] or Decimal('0')
        credits = lines.aggregate(Sum('credit'))['credit__sum'] or Decimal('0')

        if self.normal_balance == 'debit':
            self.balance = debits - credits
        else:
            self.balance = credits - debits

        self.balance_updated = timezone.now()
        self.save()


class FiscalPeriod(models.Model):
    """Fiscal periods for closing."""

    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()

    is_closed = models.BooleanField(default=False)
    closed_at = models.DateTimeField(null=True)
    closed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True
    )

    class Meta:
        ordering = ['-start_date']


class JournalEntry(models.Model):
    """Double-entry journal entry."""

    entry_number = models.CharField(max_length=50, unique=True)
    date = models.DateField()
    description = models.TextField()

    ENTRY_TYPES = [
        ('manual', 'Manual'),
        ('invoice', 'Factura'),
        ('payment', 'Pago'),
        ('adjustment', 'Ajuste'),
        ('closing', 'Cierre'),
    ]
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPES, default='manual')

    # Source documents
    invoice = models.ForeignKey(
        'billing.Invoice', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='journal_entries'
    )
    bill = models.ForeignKey(
        'Bill', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='journal_entries'
    )
    payment = models.ForeignKey(
        'billing.Payment', on_delete=models.SET_NULL,
        null=True, blank=True
    )

    # Period
    fiscal_period = models.ForeignKey(
        FiscalPeriod, on_delete=models.PROTECT,
        null=True, blank=True
    )

    # Status
    is_posted = models.BooleanField(default=False)
    posted_at = models.DateTimeField(null=True)
    posted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='posted_entries'
    )

    is_reversed = models.BooleanField(default=False)
    reversed_by_entry = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reverses'
    )

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, related_name='journal_entries'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name_plural = 'Journal Entries'

    def clean(self):
        """Validate entry is balanced."""
        if self.pk:
            total_debits = sum(l.debit for l in self.lines.all())
            total_credits = sum(l.credit for l in self.lines.all())

            if total_debits != total_credits:
                raise ValidationError(
                    f"Entry is not balanced. Debits: {total_debits}, Credits: {total_credits}"
                )

    def post(self, user):
        """Post entry and update account balances."""
        if self.is_posted:
            raise ValueError("Entry already posted")

        # Check period is open
        if self.fiscal_period and self.fiscal_period.is_closed:
            raise ValueError("Cannot post to closed period")

        self.is_posted = True
        self.posted_at = timezone.now()
        self.posted_by = user
        self.save()

        # Update account balances
        for line in self.lines.all():
            line.account.recalculate_balance()


class JournalLine(models.Model):
    """Individual debit/credit line."""

    entry = models.ForeignKey(
        JournalEntry, on_delete=models.CASCADE,
        related_name='lines'
    )
    account = models.ForeignKey(
        Account, on_delete=models.PROTECT,
        related_name='journal_lines'
    )

    debit = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )
    credit = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )

    description = models.CharField(max_length=200, blank=True)

    # Reference
    owner = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+'
    )
    vendor = models.ForeignKey(
        'Vendor', on_delete=models.SET_NULL,
        null=True, blank=True
    )

    class Meta:
        ordering = ['id']

    def clean(self):
        if self.debit > 0 and self.credit > 0:
            raise ValidationError("Line cannot have both debit and credit")
        if self.debit == 0 and self.credit == 0:
            raise ValidationError("Line must have debit or credit")


class Vendor(models.Model):
    """Supplier/vendor for accounts payable."""

    name = models.CharField(max_length=200)
    rfc = models.CharField(max_length=13, blank=True)  # Tax ID
    business_name = models.CharField(max_length=200, blank=True)

    # Contact
    contact_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    # Banking
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account = models.CharField(max_length=50, blank=True)
    clabe = models.CharField(max_length=18, blank=True)

    # Terms
    PAYMENT_TERMS = [
        ('immediate', 'Inmediato'),
        ('net15', 'Neto 15'),
        ('net30', 'Neto 30'),
        ('net60', 'Neto 60'),
    ]
    payment_terms = models.CharField(
        max_length=20, choices=PAYMENT_TERMS, default='net30'
    )

    default_expense_account = models.ForeignKey(
        Account, on_delete=models.SET_NULL,
        null=True, blank=True
    )

    # Balance
    balance = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']


class Bill(models.Model):
    """Vendor invoice (accounts payable)."""

    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('pending', 'Pendiente'),
        ('partial', 'Pago Parcial'),
        ('paid', 'Pagado'),
        ('cancelled', 'Cancelado'),
    ]

    vendor = models.ForeignKey(
        Vendor, on_delete=models.PROTECT,
        related_name='bills'
    )

    bill_number = models.CharField(max_length=100)
    bill_date = models.DateField()
    due_date = models.DateField()

    # Amounts
    subtotal = models.DecimalField(max_digits=15, decimal_places=2)
    tax = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # CFDI received from vendor
    cfdi_uuid = models.UUIDField(null=True, blank=True)
    cfdi_xml = models.TextField(blank=True)
    cfdi_pdf = models.FileField(upload_to='bills/cfdi/', null=True, blank=True)

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-bill_date']
        unique_together = ['vendor', 'bill_number']

    @property
    def amount_due(self):
        return self.total - self.amount_paid


class BillLine(models.Model):
    """Line item on vendor bill."""

    bill = models.ForeignKey(
        Bill, on_delete=models.CASCADE,
        related_name='lines'
    )

    description = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    amount = models.DecimalField(max_digits=15, decimal_places=2)

    expense_account = models.ForeignKey(
        Account, on_delete=models.PROTECT
    )

    # Link to inventory if product purchase
    product = models.ForeignKey(
        'store.Product', on_delete=models.SET_NULL,
        null=True, blank=True
    )


class BillPayment(models.Model):
    """Payment to vendor."""

    bill = models.ForeignKey(
        Bill, on_delete=models.PROTECT,
        related_name='payments'
    )

    date = models.DateField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)

    PAYMENT_METHODS = [
        ('check', 'Cheque'),
        ('transfer', 'Transferencia'),
        ('cash', 'Efectivo'),
        ('card', 'Tarjeta'),
    ]
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    reference = models.CharField(max_length=100, blank=True)

    bank_account = models.ForeignKey(
        Account, on_delete=models.PROTECT,
        related_name='bill_payments'
    )

    # Journal entry created
    journal_entry = models.ForeignKey(
        JournalEntry, on_delete=models.SET_NULL,
        null=True, blank=True
    )

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)


class BankReconciliation(models.Model):
    """Bank statement reconciliation."""

    bank_account = models.ForeignKey(
        Account, on_delete=models.PROTECT,
        related_name='reconciliations'
    )

    statement_date = models.DateField()
    statement_ending_balance = models.DecimalField(
        max_digits=15, decimal_places=2
    )

    # Calculated
    book_balance = models.DecimalField(
        max_digits=15, decimal_places=2, null=True
    )
    outstanding_deposits = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )
    outstanding_payments = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )
    adjusted_book_balance = models.DecimalField(
        max_digits=15, decimal_places=2, null=True
    )
    difference = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )

    is_reconciled = models.BooleanField(default=False)
    reconciled_at = models.DateTimeField(null=True)
    reconciled_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True
    )

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ReconciliationLine(models.Model):
    """Individual reconciliation item."""

    reconciliation = models.ForeignKey(
        BankReconciliation, on_delete=models.CASCADE,
        related_name='lines'
    )

    journal_line = models.ForeignKey(
        JournalLine, on_delete=models.CASCADE
    )

    is_cleared = models.BooleanField(default=False)
    cleared_date = models.DateField(null=True)


class Budget(models.Model):
    """Annual budget by account."""

    account = models.ForeignKey(
        Account, on_delete=models.CASCADE,
        related_name='budgets'
    )
    year = models.IntegerField()

    jan = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    feb = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    mar = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    apr = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    may = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    jun = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    jul = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    aug = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    sep = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    oct = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    nov = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    dec = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    class Meta:
        unique_together = ['account', 'year']

    @property
    def annual_total(self):
        return sum([
            self.jan, self.feb, self.mar, self.apr,
            self.may, self.jun, self.jul, self.aug,
            self.sep, self.oct, self.nov, self.dec
        ])
```

#### Accounting Service
```python
from datetime import date
from decimal import Decimal
from django.db import transaction


class AccountingService:
    """Accounting operations."""

    @transaction.atomic
    def create_invoice_entry(self, invoice) -> JournalEntry:
        """Create journal entry from customer invoice."""

        entry = JournalEntry.objects.create(
            entry_number=self._next_entry_number(),
            date=invoice.created_at.date(),
            description=f"Factura {invoice.invoice_number}",
            entry_type='invoice',
            invoice=invoice
        )

        # Debit AR
        ar_account = Account.objects.get(is_ar=True)
        JournalLine.objects.create(
            entry=entry,
            account=ar_account,
            debit=invoice.total,
            owner=invoice.owner
        )

        # Credit Revenue
        revenue_account = Account.objects.get(code='4000')  # Sales
        JournalLine.objects.create(
            entry=entry,
            account=revenue_account,
            credit=invoice.subtotal
        )

        # Credit IVA Payable
        if invoice.tax_amount > 0:
            iva_account = Account.objects.get(code='2100')  # IVA Payable
            JournalLine.objects.create(
                entry=entry,
                account=iva_account,
                credit=invoice.tax_amount
            )

        return entry

    @transaction.atomic
    def create_payment_entry(self, payment) -> JournalEntry:
        """Create journal entry from payment."""

        entry = JournalEntry.objects.create(
            entry_number=self._next_entry_number(),
            date=payment.created_at.date(),
            description=f"Pago recibido - {payment.invoice.invoice_number}",
            entry_type='payment',
            payment=payment
        )

        # Debit Bank/Cash
        if payment.payment_method == 'cash':
            cash_account = Account.objects.get(is_cash=True)
            JournalLine.objects.create(
                entry=entry,
                account=cash_account,
                debit=payment.amount
            )
        else:
            bank_account = Account.objects.get(is_bank=True)
            JournalLine.objects.create(
                entry=entry,
                account=bank_account,
                debit=payment.amount
            )

        # Credit AR
        ar_account = Account.objects.get(is_ar=True)
        JournalLine.objects.create(
            entry=entry,
            account=ar_account,
            credit=payment.amount,
            owner=payment.invoice.owner
        )

        return entry

    @transaction.atomic
    def create_bill_entry(self, bill) -> JournalEntry:
        """Create journal entry from vendor bill."""

        entry = JournalEntry.objects.create(
            entry_number=self._next_entry_number(),
            date=bill.bill_date,
            description=f"Factura proveedor {bill.vendor.name} - {bill.bill_number}",
            entry_type='invoice',
            bill=bill
        )

        # Credit AP
        ap_account = Account.objects.get(is_ap=True)
        JournalLine.objects.create(
            entry=entry,
            account=ap_account,
            credit=bill.total,
            vendor=bill.vendor
        )

        # Debit Expenses (from bill lines)
        for line in bill.lines.all():
            JournalLine.objects.create(
                entry=entry,
                account=line.expense_account,
                debit=line.amount,
                description=line.description
            )

        # Debit IVA Recoverable
        if bill.tax > 0:
            iva_account = Account.objects.get(code='1500')  # IVA Recoverable
            JournalLine.objects.create(
                entry=entry,
                account=iva_account,
                debit=bill.tax
            )

        return entry

    def get_trial_balance(self, as_of_date: date) -> list:
        """Get trial balance as of date."""

        accounts = Account.objects.filter(is_active=True).order_by('code')

        result = []
        total_debit = Decimal('0')
        total_credit = Decimal('0')

        for account in accounts:
            # Get balance from posted entries up to date
            lines = account.journal_lines.filter(
                entry__is_posted=True,
                entry__date__lte=as_of_date
            )

            debits = sum(l.debit for l in lines)
            credits = sum(l.credit for l in lines)

            if account.normal_balance == 'debit':
                balance = debits - credits
                if balance >= 0:
                    debit_bal = balance
                    credit_bal = Decimal('0')
                else:
                    debit_bal = Decimal('0')
                    credit_bal = abs(balance)
            else:
                balance = credits - debits
                if balance >= 0:
                    credit_bal = balance
                    debit_bal = Decimal('0')
                else:
                    credit_bal = Decimal('0')
                    debit_bal = abs(balance)

            if debit_bal or credit_bal:
                result.append({
                    'account': account,
                    'debit': debit_bal,
                    'credit': credit_bal
                })
                total_debit += debit_bal
                total_credit += credit_bal

        return {
            'accounts': result,
            'total_debit': total_debit,
            'total_credit': total_credit,
            'is_balanced': total_debit == total_credit
        }

    def get_income_statement(
        self, start_date: date, end_date: date
    ) -> dict:
        """Generate income statement."""

        revenue_accounts = Account.objects.filter(
            account_type='revenue', is_active=True
        )
        expense_accounts = Account.objects.filter(
            account_type='expense', is_active=True
        )

        def get_period_balance(accounts):
            result = []
            for account in accounts:
                lines = account.journal_lines.filter(
                    entry__is_posted=True,
                    entry__date__gte=start_date,
                    entry__date__lte=end_date
                )
                credits = sum(l.credit for l in lines)
                debits = sum(l.debit for l in lines)
                balance = credits - debits if account.account_type == 'revenue' else debits - credits
                if balance:
                    result.append({
                        'account': account,
                        'balance': balance
                    })
            return result

        revenue = get_period_balance(revenue_accounts)
        expenses = get_period_balance(expense_accounts)

        total_revenue = sum(r['balance'] for r in revenue)
        total_expenses = sum(e['balance'] for e in expenses)
        net_income = total_revenue - total_expenses

        return {
            'period_start': start_date,
            'period_end': end_date,
            'revenue': revenue,
            'expenses': expenses,
            'total_revenue': total_revenue,
            'total_expenses': total_expenses,
            'net_income': net_income
        }

    def _next_entry_number(self) -> str:
        """Generate next journal entry number."""
        from django.db.models import Max
        import re

        last = JournalEntry.objects.aggregate(Max('entry_number'))['entry_number__max']
        if not last:
            return 'JE-0001'

        match = re.search(r'(\d+)$', last)
        if match:
            num = int(match.group(1)) + 1
            return f'JE-{num:04d}'
        return 'JE-0001'
```

### Test Cases
- [ ] Chart of accounts CRUD works
- [ ] Journal entries balance
- [ ] Posting updates balances
- [ ] AP/AR tracking works
- [ ] Bill creation works
- [ ] Bill payment records correctly
- [ ] Trial balance balances
- [ ] Income statement accurate

### Definition of Done
- [ ] Double-entry system complete
- [ ] AP workflow functional
- [ ] Bank reconciliation works
- [ ] Financial statements accurate
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-040: Billing/Invoicing
