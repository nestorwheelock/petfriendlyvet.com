# S-026: Accounting & Financial Management

**Story Type:** User Story
**Priority:** Medium
**Epoch:** 6 (with Practice Management)
**Status:** PENDING
**Module:** django-accounting (NEW reusable package)

## User Story

**As a** clinic owner
**I want to** have complete financial visibility in one system
**So that** I can manage the business without switching between platforms

**As a** bookkeeper/accountant
**I want to** maintain proper double-entry accounting records
**So that** financial statements are accurate and auditable

**As a** clinic manager
**I want to** track accounts payable and receivable
**So that** I can manage cash flow effectively

## Important Note

**This is a FULL double-entry accounting system** that can:
- Replace external accounting software (QuickBooks, Contpaqi, etc.)
- OR sync with external systems for consolidated reporting

The goal is independence from other platforms while maintaining integration options.

## Acceptance Criteria

### Chart of Accounts
- [ ] Standard veterinary chart of accounts template
- [ ] Asset, Liability, Equity, Revenue, Expense accounts
- [ ] Sub-account hierarchy support
- [ ] Account types (bank, AR, AP, income, expense, etc.)
- [ ] Customizable account codes
- [ ] Active/inactive status

### General Ledger
- [ ] All transactions recorded via journal entries
- [ ] Automatic journal entries from billing/invoicing
- [ ] Manual journal entries for adjustments
- [ ] Complete audit trail (immutable)
- [ ] Period close/lock functionality
- [ ] Fiscal year management

### Accounts Receivable
- [ ] Integration with S-020 Billing
- [ ] Customer balance tracking
- [ ] Aging reports (30/60/90/120 days)
- [ ] Payment application
- [ ] Credit memos
- [ ] Bad debt write-off

### Accounts Payable
- [ ] Vendor/supplier management
- [ ] Purchase order tracking (from S-024)
- [ ] Vendor invoices (bills)
- [ ] Payment scheduling
- [ ] Check/payment runs
- [ ] AP aging reports
- [ ] Vendor statements

### Bank Reconciliation
- [ ] Import bank statements (CSV, OFX)
- [ ] Match transactions automatically
- [ ] Manual matching for unrecognized items
- [ ] Reconciliation reports
- [ ] Uncleared transactions tracking
- [ ] Multiple bank accounts

### Financial Statements
- [ ] Profit & Loss (Income Statement)
- [ ] Balance Sheet
- [ ] Cash Flow Statement
- [ ] Custom date ranges
- [ ] Comparative periods (vs last month, vs last year)
- [ ] PDF export

### Budgeting
- [ ] Annual budget by account
- [ ] Monthly budget breakdown
- [ ] Budget vs actual reports
- [ ] Variance analysis
- [ ] Budget alerts (over/under)

### Tax Reporting (Mexico)
- [ ] IVA (VAT) tracking and reporting
- [ ] CFDI integration (from S-020)
- [ ] Tax liability accounts
- [ ] Annual tax summaries
- [ ] ISR (income tax) preparation support
- [ ] DIOT generation (for SAT)

### Payroll Integration
- [ ] Track payroll expenses
- [ ] Payroll liability accounts
- [ ] Integration with external payroll systems
- [ ] Import/export payroll journals

### External Sync
- [ ] Export to QuickBooks format
- [ ] Export to Excel/CSV
- [ ] Export to Contpaqi format (Mexico)
- [ ] API for third-party integrations
- [ ] Sync schedules (if using external system)

## Technical Requirements

### Models

```python
class FiscalYear(models.Model):
    """Fiscal year for accounting periods"""
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()

    is_current = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-start_date']


class AccountingPeriod(models.Model):
    """Monthly accounting period"""
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.CASCADE, related_name='periods')

    name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('locked', 'Locked'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')

    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['start_date']


class Account(models.Model):
    """Chart of accounts"""
    ACCOUNT_TYPES = [
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('equity', 'Equity'),
        ('revenue', 'Revenue'),
        ('expense', 'Expense'),
    ]

    ACCOUNT_SUBTYPES = [
        # Assets
        ('bank', 'Bank Account'),
        ('cash', 'Cash'),
        ('accounts_receivable', 'Accounts Receivable'),
        ('inventory', 'Inventory'),
        ('prepaid', 'Prepaid Expenses'),
        ('fixed_asset', 'Fixed Asset'),
        ('accumulated_depreciation', 'Accumulated Depreciation'),
        ('other_asset', 'Other Asset'),

        # Liabilities
        ('accounts_payable', 'Accounts Payable'),
        ('credit_card', 'Credit Card'),
        ('payroll_liability', 'Payroll Liability'),
        ('tax_payable', 'Tax Payable'),
        ('loan', 'Loan'),
        ('other_liability', 'Other Liability'),

        # Equity
        ('owners_equity', "Owner's Equity"),
        ('retained_earnings', 'Retained Earnings'),

        # Revenue
        ('service_revenue', 'Service Revenue'),
        ('product_revenue', 'Product Revenue'),
        ('other_income', 'Other Income'),

        # Expense
        ('cost_of_goods', 'Cost of Goods Sold'),
        ('payroll_expense', 'Payroll Expense'),
        ('rent', 'Rent'),
        ('utilities', 'Utilities'),
        ('supplies', 'Supplies'),
        ('professional_fees', 'Professional Fees'),
        ('depreciation', 'Depreciation'),
        ('other_expense', 'Other Expense'),
    ]

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    name_es = models.CharField(max_length=200, blank=True)

    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    account_subtype = models.CharField(max_length=30, choices=ACCOUNT_SUBTYPES, blank=True)

    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    # Special flags
    is_bank = models.BooleanField(default=False)
    is_ar = models.BooleanField(default=False)  # Accounts Receivable
    is_ap = models.BooleanField(default=False)  # Accounts Payable
    is_tax = models.BooleanField(default=False)

    # Balances (cached for performance)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_date = models.DateField(null=True, blank=True)

    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code']

    @property
    def is_debit_positive(self):
        """Assets and Expenses increase with debits"""
        return self.account_type in ['asset', 'expense']


class JournalEntry(models.Model):
    """Double-entry journal entry header"""
    ENTRY_TYPES = [
        ('standard', 'Standard'),
        ('adjusting', 'Adjusting'),
        ('closing', 'Closing'),
        ('reversing', 'Reversing'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('voided', 'Voided'),
    ]

    entry_number = models.CharField(max_length=50, unique=True)
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPES, default='standard')

    date = models.DateField()
    period = models.ForeignKey(AccountingPeriod, on_delete=models.PROTECT)

    description = models.TextField()
    reference = models.CharField(max_length=100, blank=True)

    # Source documents (generic relation alternative)
    source_type = models.CharField(max_length=50, blank=True)
    # invoice, bill, payment, payroll, adjustment, etc.
    source_id = models.IntegerField(null=True, blank=True)

    # Related documents
    invoice = models.ForeignKey('billing.Invoice', on_delete=models.SET_NULL, null=True, blank=True)
    bill = models.ForeignKey('Bill', on_delete=models.SET_NULL, null=True, blank=True)
    payment = models.ForeignKey('billing.Payment', on_delete=models.SET_NULL, null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Totals (for validation)
    total_debit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_credit = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Audit
    is_posted = models.BooleanField(default=False)
    posted_at = models.DateTimeField(null=True, blank=True)
    posted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    voided_at = models.DateTimeField(null=True, blank=True)
    voided_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    void_reason = models.TextField(blank=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-entry_number']
        verbose_name_plural = 'Journal entries'

    def is_balanced(self):
        return self.total_debit == self.total_credit


class JournalLine(models.Model):
    """Individual debit/credit line in journal entry"""
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='journal_lines')

    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    description = models.CharField(max_length=500, blank=True)

    # For tracking by entity
    customer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    vendor = models.ForeignKey('Vendor', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['id']


class Vendor(models.Model):
    """Supplier/vendor for accounts payable"""
    code = models.CharField(max_length=50, blank=True)
    name = models.CharField(max_length=200)

    # Contact
    contact_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    # Tax
    rfc = models.CharField(max_length=13, blank=True)  # Tax ID
    tax_regime = models.CharField(max_length=100, blank=True)

    # Terms
    PAYMENT_TERMS = [
        ('prepaid', 'Prepaid'),
        ('on_receipt', 'On Receipt'),
        ('net15', 'Net 15'),
        ('net30', 'Net 30'),
        ('net45', 'Net 45'),
        ('net60', 'Net 60'),
    ]
    payment_terms = models.CharField(max_length=20, choices=PAYMENT_TERMS, default='net30')

    # Default accounts
    default_expense_account = models.ForeignKey(
        Account, on_delete=models.SET_NULL, null=True, blank=True,
        limit_choices_to={'account_type': 'expense'}
    )

    # Balances
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    is_active = models.BooleanField(default=True)
    is_1099 = models.BooleanField(default=False)  # For tax reporting

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']


class Bill(models.Model):
    """Vendor invoice (accounts payable)"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]

    bill_number = models.CharField(max_length=100)
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name='bills')

    bill_date = models.DateField()
    due_date = models.DateField()
    received_date = models.DateField(null=True, blank=True)

    # Reference
    vendor_invoice_number = models.CharField(max_length=100, blank=True)
    purchase_order = models.ForeignKey(
        'inventory.PurchaseOrder', on_delete=models.SET_NULL, null=True, blank=True
    )

    # Amounts
    subtotal = models.DecimalField(max_digits=15, decimal_places=2)
    tax = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    @property
    def balance_due(self):
        return self.total - self.amount_paid

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # CFDI (if received from vendor)
    cfdi_uuid = models.UUIDField(null=True, blank=True)
    cfdi_xml = models.TextField(blank=True)

    # Journal entry
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.SET_NULL, null=True, blank=True)

    # Approval
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    approved_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-bill_date']
        unique_together = ['vendor', 'vendor_invoice_number']


class BillLine(models.Model):
    """Line item on vendor bill"""
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='lines')

    description = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    amount = models.DecimalField(max_digits=15, decimal_places=2)

    expense_account = models.ForeignKey(
        Account, on_delete=models.PROTECT,
        limit_choices_to={'account_type': 'expense'}
    )

    # Link to inventory if product purchase
    product = models.ForeignKey('store.Product', on_delete=models.SET_NULL, null=True, blank=True)

    # SAT codes if CFDI
    clave_producto_sat = models.CharField(max_length=10, blank=True)


class BillPayment(models.Model):
    """Payment to vendor"""
    bill = models.ForeignKey(Bill, on_delete=models.PROTECT, related_name='payments')

    date = models.DateField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)

    PAYMENT_METHODS = [
        ('check', 'Check'),
        ('transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
    ]
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    reference = models.CharField(max_length=100, blank=True)
    check_number = models.CharField(max_length=50, blank=True)

    bank_account = models.ForeignKey(
        Account, on_delete=models.PROTECT,
        limit_choices_to={'is_bank': True}
    )

    # Journal entry
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.SET_NULL, null=True, blank=True)

    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class BankAccount(models.Model):
    """Bank account details for reconciliation"""
    account = models.OneToOneField(
        Account, on_delete=models.CASCADE,
        limit_choices_to={'is_bank': True}
    )

    bank_name = models.CharField(max_length=200)
    account_number = models.CharField(max_length=50)
    routing_number = models.CharField(max_length=50, blank=True)
    clabe = models.CharField(max_length=18, blank=True)  # Mexico interbank code

    currency = models.CharField(max_length=3, default='MXN')

    # Balances
    last_statement_date = models.DateField(null=True, blank=True)
    last_statement_balance = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    last_reconciled_date = models.DateField(null=True, blank=True)

    is_active = models.BooleanField(default=True)


class BankReconciliation(models.Model):
    """Bank statement reconciliation"""
    bank_account = models.ForeignKey(BankAccount, on_delete=models.PROTECT, related_name='reconciliations')

    statement_date = models.DateField()
    statement_balance = models.DecimalField(max_digits=15, decimal_places=2)

    # Calculated fields
    book_balance = models.DecimalField(max_digits=15, decimal_places=2)
    adjusted_book_balance = models.DecimalField(max_digits=15, decimal_places=2)
    difference = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Status
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('reconciled', 'Reconciled'),
        ('approved', 'Approved'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')

    # Audit
    reconciled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    reconciled_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    approved_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class BankTransaction(models.Model):
    """Individual bank transaction for reconciliation"""
    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='transactions')
    reconciliation = models.ForeignKey(
        BankReconciliation, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='transactions'
    )

    date = models.DateField()
    description = models.CharField(max_length=500)
    reference = models.CharField(max_length=100, blank=True)

    amount = models.DecimalField(max_digits=15, decimal_places=2)
    # Positive = deposit, Negative = withdrawal

    # Matching
    STATUS_CHOICES = [
        ('unmatched', 'Unmatched'),
        ('matched', 'Matched'),
        ('manual', 'Manually Matched'),
        ('excluded', 'Excluded'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unmatched')

    matched_journal_line = models.ForeignKey(
        JournalLine, on_delete=models.SET_NULL, null=True, blank=True
    )

    # Import
    import_source = models.CharField(max_length=50, blank=True)
    # csv, ofx, manual

    created_at = models.DateTimeField(auto_now_add=True)


class Budget(models.Model):
    """Annual budget by account"""
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.CASCADE, related_name='budgets')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='budgets')

    # Monthly budgets
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

    @property
    def annual_total(self):
        return sum([
            self.jan, self.feb, self.mar, self.apr, self.may, self.jun,
            self.jul, self.aug, self.sep, self.oct, self.nov, self.dec
        ])

    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['fiscal_year', 'account']


class TaxLiability(models.Model):
    """Track tax liabilities (IVA, ISR, etc.)"""
    TAX_TYPES = [
        ('iva', 'IVA (VAT)'),
        ('isr', 'ISR (Income Tax)'),
        ('payroll', 'Payroll Taxes'),
        ('other', 'Other'),
    ]

    tax_type = models.CharField(max_length=20, choices=TAX_TYPES)
    period = models.ForeignKey(AccountingPeriod, on_delete=models.PROTECT)

    # Amounts
    collected = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    # Tax collected from customers

    paid = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    # Tax paid to vendors (creditable)

    payable = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    # Net amount owed to government

    # Payment
    paid_to_government = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    payment_date = models.DateField(null=True, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['tax_type', 'period']
        verbose_name_plural = 'Tax liabilities'
```

### AI Tools

```python
ACCOUNTING_TOOLS = [
    {
        "name": "get_account_balance",
        "description": "Get balance for an account or account type",
        "parameters": {
            "type": "object",
            "properties": {
                "account_code": {"type": "string"},
                "account_type": {"type": "string"},
                "as_of_date": {"type": "string"}
            }
        }
    },
    {
        "name": "get_financial_statement",
        "description": "Generate a financial statement",
        "parameters": {
            "type": "object",
            "properties": {
                "statement_type": {"type": "string", "enum": ["profit_loss", "balance_sheet", "cash_flow"]},
                "start_date": {"type": "string"},
                "end_date": {"type": "string"},
                "compare_to": {"type": "string"}
            },
            "required": ["statement_type", "end_date"]
        }
    },
    {
        "name": "get_ar_aging",
        "description": "Get accounts receivable aging report",
        "parameters": {
            "type": "object",
            "properties": {
                "as_of_date": {"type": "string"}
            }
        }
    },
    {
        "name": "get_ap_aging",
        "description": "Get accounts payable aging report",
        "parameters": {
            "type": "object",
            "properties": {
                "as_of_date": {"type": "string"}
            }
        }
    },
    {
        "name": "record_bill",
        "description": "Record a vendor bill",
        "parameters": {
            "type": "object",
            "properties": {
                "vendor_id": {"type": "integer"},
                "bill_date": {"type": "string"},
                "due_date": {"type": "string"},
                "items": {"type": "array"},
                "vendor_invoice_number": {"type": "string"}
            },
            "required": ["vendor_id", "bill_date", "items"]
        }
    },
    {
        "name": "pay_bill",
        "description": "Record payment for a vendor bill",
        "parameters": {
            "type": "object",
            "properties": {
                "bill_id": {"type": "integer"},
                "amount": {"type": "number"},
                "payment_method": {"type": "string"},
                "bank_account_id": {"type": "integer"},
                "reference": {"type": "string"}
            },
            "required": ["bill_id", "amount", "payment_method", "bank_account_id"]
        }
    },
    {
        "name": "create_journal_entry",
        "description": "Create a manual journal entry",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {"type": "string"},
                "description": {"type": "string"},
                "lines": {"type": "array"}
            },
            "required": ["date", "description", "lines"]
        }
    },
    {
        "name": "reconcile_bank",
        "description": "Start or continue bank reconciliation",
        "parameters": {
            "type": "object",
            "properties": {
                "bank_account_id": {"type": "integer"},
                "statement_date": {"type": "string"},
                "statement_balance": {"type": "number"}
            },
            "required": ["bank_account_id", "statement_date", "statement_balance"]
        }
    },
    {
        "name": "get_budget_variance",
        "description": "Get budget vs actual variance report",
        "parameters": {
            "type": "object",
            "properties": {
                "fiscal_year_id": {"type": "integer"},
                "period": {"type": "string"}
            },
            "required": ["fiscal_year_id"]
        }
    }
]
```

## Example AI Conversations

### Financial Overview
```
Dr. Pablo: How are we doing financially this month?

AI: 📊 FINANCIAL SUMMARY - December 2025
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    💰 PROFIT & LOSS (Month to Date)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    Revenue:
    • Service Revenue:    $87,450 MXN
    • Product Sales:      $34,200 MXN
    • Lab Services:       $12,800 MXN
    ─────────────────────────────────
    Total Revenue:       $134,450 MXN

    Expenses:
    • Payroll:           $45,000 MXN
    • Inventory/COGS:    $28,500 MXN
    • Rent:              $12,000 MXN
    • Utilities:          $3,200 MXN
    • Supplies:           $5,400 MXN
    • Other:              $8,900 MXN
    ─────────────────────────────────
    Total Expenses:     $103,000 MXN

    📈 NET INCOME:       $31,450 MXN

    vs Last Month: +12%
    vs Budget: +8%

    💵 CASH POSITION
    • Banamex Checking:  $156,780 MXN
    • Petty Cash:          $5,000 MXN

    📋 Would you like to see:
    1. Full income statement
    2. Outstanding receivables
    3. Bills to pay
    4. Budget variance details
```

### Accounts Payable
```
Staff: What bills are due this week?

AI: 📋 BILLS DUE THIS WEEK (Dec 21-27)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    🔴 OVERDUE (Pay immediately):
    None ✓

    🟡 DUE THIS WEEK:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    1. VetPharm - Invoice #VP-2025-892
       Due: December 22
       Amount: $8,540 MXN
       Items: Medications restocking

    2. Servicios Eléctricos
       Due: December 23
       Amount: $3,200 MXN
       Items: December electricity

    3. PetMed Supplier - Invoice #PMS-4521
       Due: December 25
       Amount: $4,280 MXN
       Items: Flea/tick products

    ─────────────────────────────────
    Total Due This Week: $16,020 MXN

    💰 Current Bank Balance: $156,780 MXN
    ✅ Sufficient funds available

    Would you like to:
    1. Schedule payments for all
    2. Pay VetPharm now (most urgent)
    3. View payment history
```

### Bank Reconciliation
```
Staff: I need to reconcile the bank account

AI: 🏦 BANK RECONCILIATION
    ━━━━━━━━━━━━━━━━━━━━━━━

    Account: Banamex Checking
    Last reconciled: November 30, 2025

    Enter your bank statement info:
    • Statement Date: [December 31, 2025]
    • Statement Ending Balance: [$XXX,XXX.XX]

Staff: December 20, balance $158,450

AI: 🏦 RECONCILIATION - December 20, 2025
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    Bank Statement Balance:  $158,450.00
    Book Balance:            $156,780.00
    ─────────────────────────────────────
    Difference:               $1,670.00

    📋 UNCLEARED ITEMS:

    Outstanding Checks:
    □ #1234 - VetPharm      -$2,500.00 (Dec 15)
    □ #1235 - Rent          -$12,000.00 (Dec 18)
    Total Outstanding:      -$14,500.00

    Deposits in Transit:
    □ Card payments Dec 20  +$12,830.00
    Total in Transit:       +$12,830.00

    Bank Fees Not Recorded:
    • Monthly fee            -$350.00
    • Wire fee               -$150.00
    Total Fees:              -$500.00

    Interest Earned:         +$20.00

    ─────────────────────────────────────
    Adjusted Book Balance:  $158,450.00
    Bank Statement:         $158,450.00
    Difference:                  $0.00 ✓

    ✅ Account reconciles!

    Record bank fees and interest?
```

## Standard Chart of Accounts (Veterinary Clinic)

```
1000 - ASSETS
├── 1100 - Current Assets
│   ├── 1110 - Banamex Checking
│   ├── 1120 - Petty Cash
│   ├── 1200 - Accounts Receivable
│   ├── 1300 - Inventory - Medications
│   ├── 1310 - Inventory - Products
│   └── 1400 - Prepaid Expenses
├── 1500 - Fixed Assets
│   ├── 1510 - Medical Equipment
│   ├── 1520 - Office Equipment
│   ├── 1530 - Furniture & Fixtures
│   └── 1590 - Accumulated Depreciation

2000 - LIABILITIES
├── 2100 - Current Liabilities
│   ├── 2110 - Accounts Payable
│   ├── 2200 - Credit Cards
│   ├── 2300 - Payroll Liabilities
│   ├── 2400 - IVA Payable
│   └── 2500 - Customer Deposits
└── 2600 - Long-term Liabilities
    └── 2610 - Loans Payable

3000 - EQUITY
├── 3100 - Owner's Capital
└── 3200 - Retained Earnings

4000 - REVENUE
├── 4100 - Service Revenue
│   ├── 4110 - Consultations
│   ├── 4120 - Vaccinations
│   ├── 4130 - Surgery
│   ├── 4140 - Lab Services
│   └── 4150 - Emergency Services
├── 4200 - Product Sales
│   ├── 4210 - Medications
│   ├── 4220 - Pet Food
│   └── 4230 - Accessories
└── 4900 - Other Income

5000 - COST OF GOODS SOLD
├── 5100 - COGS - Medications
├── 5200 - COGS - Pet Food
└── 5300 - COGS - Accessories

6000 - OPERATING EXPENSES
├── 6100 - Payroll Expense
├── 6200 - Rent
├── 6300 - Utilities
├── 6400 - Insurance
├── 6500 - Medical Supplies
├── 6600 - Office Supplies
├── 6700 - Professional Fees
├── 6800 - Depreciation
└── 6900 - Other Expenses
```

## Definition of Done

- [ ] Chart of accounts with hierarchy
- [ ] Journal entry system (double-entry)
- [ ] Automatic entries from billing
- [ ] Accounts payable workflow
- [ ] Vendor management
- [ ] Bank reconciliation
- [ ] Financial statements (P&L, Balance Sheet)
- [ ] Budget tracking
- [ ] Tax liability tracking
- [ ] Period close functionality
- [ ] Export capabilities
- [ ] AI tools for financial queries
- [ ] Tests written and passing (>95% coverage)

## Dependencies

- S-020: Billing (AR integration)
- S-024: Inventory (COGS, purchase orders)
- S-017: Reports (financial dashboards)

## Notes

- Double-entry is non-negotiable for audit compliance
- Journal entries are immutable (void instead of delete)
- Period close prevents backdated entries
- Consider Mexican accounting standards (NIF)
- Bank reconciliation is critical for cash control
- May need certified accountant review for tax compliance
- Integration with SAT systems (CFDI) already in S-020

## Development Process

**Before implementing this story**, review and follow the **23-Step TDD Cycle** in:
- `CLAUDE.md` - Global development workflow
- `planning/TASK_BREAKDOWN.md` - Specific tasks for this story

Tests must be written before implementation. >95% coverage required.
