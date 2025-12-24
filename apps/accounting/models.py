"""Accounting models for double-entry bookkeeping."""
from django.db import models
from django.conf import settings


class Account(models.Model):
    """Chart of accounts."""

    ACCOUNT_TYPES = [
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('equity', 'Equity'),
        ('revenue', 'Revenue'),
        ('expense', 'Expense'),
    ]

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='children'
    )

    description = models.TextField(blank=True)

    is_bank = models.BooleanField(default=False)
    is_ar = models.BooleanField(default=False)
    is_ap = models.BooleanField(default=False)

    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class JournalEntry(models.Model):
    """Double-entry journal entry."""

    date = models.DateField()
    reference = models.CharField(max_length=100)
    description = models.TextField()

    is_posted = models.BooleanField(default=False)
    posted_at = models.DateTimeField(null=True, blank=True)
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posted_journal_entries'
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='journal_entries'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name_plural = 'Journal entries'

    def __str__(self):
        return f"{self.reference} - {self.date}"

    @property
    def total_debit(self):
        return sum(line.debit for line in self.lines.all())

    @property
    def total_credit(self):
        return sum(line.credit for line in self.lines.all())

    @property
    def is_balanced(self):
        return self.total_debit == self.total_credit


class JournalLine(models.Model):
    """Individual debit/credit line."""

    entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='journal_lines'
    )

    debit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    credit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    description = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.account.code} - Dr: {self.debit} / Cr: {self.credit}"


class Vendor(models.Model):
    """Supplier/vendor for accounts payable."""

    name = models.CharField(max_length=200)
    rfc = models.CharField(max_length=13, blank=True)
    contact_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    PAYMENT_TERMS = [
        ('prepaid', 'Prepaid'),
        ('net15', 'Net 15'),
        ('net30', 'Net 30'),
        ('net60', 'Net 60'),
    ]
    payment_terms = models.CharField(
        max_length=10,
        choices=PAYMENT_TERMS,
        default='net30'
    )

    default_expense_account = models.ForeignKey(
        Account,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='default_for_vendors'
    )

    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Bill(models.Model):
    """Vendor invoice (accounts payable)."""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Payment'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]

    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.PROTECT,
        related_name='bills'
    )
    bill_number = models.CharField(max_length=100)
    bill_date = models.DateField()
    due_date = models.DateField()

    subtotal = models.DecimalField(max_digits=15, decimal_places=2)
    tax = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2)
    amount_paid = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    cfdi_uuid = models.UUIDField(null=True, blank=True)
    cfdi_xml = models.TextField(blank=True)

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-bill_date']

    def __str__(self):
        return f"{self.vendor.name} - {self.bill_number}"

    @property
    def balance_due(self):
        return self.total - self.amount_paid


class BillLine(models.Model):
    """Line item on vendor bill."""

    bill = models.ForeignKey(
        Bill,
        on_delete=models.CASCADE,
        related_name='lines'
    )

    description = models.CharField(max_length=500)
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1
    )
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    amount = models.DecimalField(max_digits=15, decimal_places=2)

    expense_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='bill_lines'
    )

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.description} - {self.amount}"


class BillPayment(models.Model):
    """Payment to vendor."""

    PAYMENT_METHODS = [
        ('check', 'Check'),
        ('transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('card', 'Credit Card'),
    ]

    bill = models.ForeignKey(
        Bill,
        on_delete=models.PROTECT,
        related_name='payments'
    )

    date = models.DateField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)

    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    reference = models.CharField(max_length=100, blank=True)

    bank_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='bill_payments'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.bill.vendor.name} - {self.amount}"


class Budget(models.Model):
    """Annual budget by account."""

    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
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
        ordering = ['year', 'account__code']

    def __str__(self):
        return f"{self.account.code} - {self.year}"

    @property
    def annual_total(self):
        return sum([
            self.jan, self.feb, self.mar, self.apr,
            self.may, self.jun, self.jul, self.aug,
            self.sep, self.oct, self.nov, self.dec
        ])


class BankReconciliation(models.Model):
    """Bank statement reconciliation."""

    bank_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='reconciliations'
    )
    statement_date = models.DateField()
    statement_balance = models.DecimalField(max_digits=15, decimal_places=2)

    is_reconciled = models.BooleanField(default=False)
    reconciled_at = models.DateTimeField(null=True, blank=True)
    reconciled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    difference = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-statement_date']

    def __str__(self):
        return f"{self.bank_account.name} - {self.statement_date}"
