# S-020: Billing & Invoicing

**Story Type:** User Story
**Priority:** High
**Epoch:** 3 (with E-Commerce)
**Status:** PENDING
**Module:** django-simple-store + django-billing

## User Story

**As a** clinic owner
**I want to** manage payments, invoices, and billing in one system
**So that** I have clear financial records and comply with Mexican tax law

**As a** pet owner
**I want to** pay for services flexibly and receive proper invoices
**So that** I can manage my pet care expenses conveniently

**As a** B2B client (other veterinarian)
**I want to** have a professional account with credit terms
**So that** I can send lab samples and pay on a monthly statement

## Acceptance Criteria

### Payment Processing
- [ ] Stripe integration for online card payments
- [ ] Cash payment recording with 2-3% discount auto-applied
- [ ] Manual card entry for in-person transactions (no POS hardware)
- [ ] Saved payment methods for repeat customers
- [ ] Subscription billing for wellness plans

### Multi-Currency Support
- [ ] Primary currency: MXN (Mexican Peso)
- [ ] Display USD/EUR equivalents for tourists/expats
- [ ] Daily exchange rates from Banco de Mexico API
- [ ] All transactions recorded in MXN

### Invoicing
- [ ] Auto-generate invoices from services/products
- [ ] Itemized line items with descriptions
- [ ] IVA (16%) tax calculation
- [ ] Sequential invoice numbering by year
- [ ] PDF generation with clinic branding
- [ ] Email/WhatsApp invoice delivery

### CFDI (Mexican Tax Compliance)
- [ ] CFDI generation via PAC (Facturama)
- [ ] SAT-compliant XML and PDF
- [ ] Folio fiscal tracking
- [ ] Support for factura, nota de credito, recibo de pago
- [ ] Client RFC storage and validation
- [ ] Uso de CFDI categorization

### Payment Reminders
- [ ] Automated reminder scheduling
- [ ] Escalation (1, 3, 7 days overdue)
- [ ] Multi-channel delivery (email, SMS, WhatsApp)
- [ ] Pause reminders option

### Prepayments & Credits
- [ ] Service packages (bundle discounts)
- [ ] Account credit (add funds, auto-apply)
- [ ] Wellness plan subscriptions (monthly billing)
- [ ] Track package redemptions

### Discounts & Promotions
- [ ] Coupon codes (% or fixed amount)
- [ ] Cash discount (2-3% auto-apply)
- [ ] Customer discount tiers (VIP, rescue, breeder, staff)
- [ ] Usage limits and expiration dates

### B2B Professional Accounts
- [ ] Credit accounts with approval workflow
- [ ] Payment terms (Net-15, Net-30, Net-60)
- [ ] Credit limit management
- [ ] Monthly statement generation
- [ ] Bulk invoicing for multiple samples
- [ ] Account aging reports (30/60/90 days)
- [ ] Credit hold when overdue
- [ ] Professional/wholesale pricing

## Technical Requirements

### Payment Provider

**Primary: Stripe**
- Card payments online
- Subscription billing
- Saved payment methods
- Payment intents for secure checkout

**Future: PayPal**
- Placeholder for later integration

### CFDI Provider

**Recommendation: Facturama**

| Provider | Cost | Features |
|----------|------|----------|
| **Facturama** | ~$0.80/CFDI | Good API, Mexican company, Python SDK |
| **SW Sapien** | ~$0.70/CFDI | High volume discounts |
| **Finkok** | ~$0.90/CFDI | Reliable, good support |

### Models

```python
class Invoice(models.Model):
    """Invoice for services/products"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]

    # Identification
    invoice_number = models.CharField(max_length=50, unique=True)
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    pet = models.ForeignKey('vet_clinic.Pet', on_delete=models.SET_NULL, null=True)

    # Amounts (all in MXN)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2)  # IVA 16%
    total = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Currency display
    display_currency = models.CharField(max_length=3, default='MXN')
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, null=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    due_date = models.DateField()

    # Related
    appointment = models.ForeignKey(
        'appointments.Appointment', null=True, on_delete=models.SET_NULL
    )
    order = models.ForeignKey('store.Order', null=True, on_delete=models.SET_NULL)

    # CFDI
    cfdi_uuid = models.UUIDField(null=True, blank=True)  # Folio fiscal
    cfdi_xml = models.TextField(blank=True)
    cfdi_pdf = models.FileField(upload_to='cfdi/', null=True)
    cfdi_status = models.CharField(max_length=20, blank=True)
    # 'pending', 'stamped', 'cancelled'

    # Client tax info (for CFDI)
    client_rfc = models.CharField(max_length=13, blank=True)
    client_razon_social = models.CharField(max_length=300, blank=True)
    uso_cfdi = models.CharField(max_length=10, blank=True)  # G03, etc.
    regimen_fiscal = models.CharField(max_length=10, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True)
    paid_at = models.DateTimeField(null=True)

    class Meta:
        ordering = ['-created_at']

    def get_balance_due(self):
        return self.total - self.amount_paid


class InvoiceLineItem(models.Model):
    """Individual line items on invoice"""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')

    # Item details
    description = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    # Reference (optional)
    service = models.ForeignKey(
        'appointments.ServiceType', null=True, on_delete=models.SET_NULL
    )
    product = models.ForeignKey('store.Product', null=True, on_delete=models.SET_NULL)

    # SAT codes for CFDI
    clave_producto_sat = models.CharField(max_length=10, blank=True)
    clave_unidad_sat = models.CharField(max_length=5, blank=True)

    class Meta:
        ordering = ['id']


class Payment(models.Model):
    """Payment record"""
    PAYMENT_METHODS = [
        ('stripe_card', 'Card (Online)'),
        ('stripe_subscription', 'Subscription'),
        ('manual_card', 'Card (In-Person)'),
        ('cash', 'Cash'),
        ('account_credit', 'Account Credit'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name='payments')

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)

    # Stripe
    stripe_payment_intent = models.CharField(max_length=100, blank=True)
    stripe_charge_id = models.CharField(max_length=100, blank=True)

    # Manual entry
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    # Cash discount applied
    cash_discount_applied = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Recorded by
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class CustomerDiscount(models.Model):
    """Persistent discount levels for customers"""
    DISCOUNT_TYPES = [
        ('vip', 'VIP Client'),
        ('rescue', 'Rescue Organization'),
        ('breeder', 'Breeder'),
        ('staff', 'Staff/Family'),
        ('professional', 'Professional (B2B)'),
        ('custom', 'Custom'),
    ]

    owner = models.OneToOneField(User, on_delete=models.CASCADE)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2)
    applies_to_products = models.BooleanField(default=True)
    applies_to_services = models.BooleanField(default=True)

    notes = models.TextField(blank=True)
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='+'
    )
    created_at = models.DateTimeField(auto_now_add=True)


class CouponCode(models.Model):
    """Promotional coupon codes"""
    code = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=200)

    # Discount
    DISCOUNT_TYPES = [
        ('percent', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)

    # Restrictions
    minimum_purchase = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_uses = models.IntegerField(null=True, blank=True)
    max_uses_per_customer = models.IntegerField(default=1)
    valid_products = models.ManyToManyField('store.Product', blank=True)
    valid_services = models.ManyToManyField('appointments.ServiceType', blank=True)

    # Validity
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    # Tracking
    times_used = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        from django.utils import timezone
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
    """Track coupon usage per customer"""
    coupon = models.ForeignKey(CouponCode, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    discount_applied = models.DecimalField(max_digits=10, decimal_places=2)
    used_at = models.DateTimeField(auto_now_add=True)


class PrepaidPackage(models.Model):
    """Service packages purchased in advance"""
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    name = models.CharField(max_length=200)
    services_included = models.JSONField(default=list)
    # e.g., [{"service_id": 1, "quantity": 5, "name": "Grooming"}, ...]

    services_remaining = models.JSONField(default=list)

    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True)

    expires_at = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def redeem_service(self, service_id):
        """Redeem one service from the package"""
        pass  # Implement redemption logic


class AccountCredit(models.Model):
    """Credit balance on account"""
    owner = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)


class CreditTransaction(models.Model):
    """Credit additions and deductions"""
    account = models.ForeignKey(AccountCredit, on_delete=models.CASCADE)

    TRANSACTION_TYPES = [
        ('add', 'Added Credit'),
        ('purchase', 'Purchase Applied'),
        ('refund', 'Refund to Credit'),
        ('expired', 'Expired'),
        ('adjustment', 'Manual Adjustment'),
    ]

    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)

    related_invoice = models.ForeignKey(Invoice, null=True, on_delete=models.SET_NULL)
    notes = models.TextField(blank=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class WellnessPlan(models.Model):
    """Subscription wellness plans"""
    name = models.CharField(max_length=200)
    name_es = models.CharField(max_length=200)
    description = models.TextField()
    description_es = models.TextField()

    species = models.JSONField(default=list)  # ["dog", "cat"]

    # Pricing
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2)
    annual_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    annual_savings = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    # Included services
    included_services = models.JSONField(default=list)
    # [{"service_id": 1, "per_month": 1}, {"service_id": 2, "per_year": 2}]

    # Additional benefits
    product_discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    service_discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    is_active = models.BooleanField(default=True)
    stripe_price_id_monthly = models.CharField(max_length=100, blank=True)
    stripe_price_id_annual = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)


class WellnessPlanSubscription(models.Model):
    """Customer subscription to wellness plan"""
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    pet = models.ForeignKey('vet_clinic.Pet', on_delete=models.CASCADE)
    plan = models.ForeignKey(WellnessPlan, on_delete=models.PROTECT)

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
        ('past_due', 'Past Due'),
        ('expired', 'Expired'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    billing_cycle = models.CharField(max_length=10)  # 'monthly' or 'annual'

    # Stripe
    stripe_subscription_id = models.CharField(max_length=100)
    stripe_customer_id = models.CharField(max_length=100)

    current_period_start = models.DateField()
    current_period_end = models.DateField()

    # Usage tracking
    services_used_this_period = models.JSONField(default=dict)
    # {"service_1": 2, "service_2": 0}

    created_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancel_reason = models.TextField(blank=True)


class ProfessionalAccount(models.Model):
    """B2B account for other veterinarians"""
    owner = models.OneToOneField(User, on_delete=models.CASCADE)

    # Business info
    business_name = models.CharField(max_length=200)
    rfc = models.CharField(max_length=13)  # Tax ID
    contact_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    address = models.TextField(blank=True)

    # Credit terms
    PAYMENT_TERMS = [
        ('prepaid', 'Prepaid'),
        ('net15', 'Net 15'),
        ('net30', 'Net 30'),
        ('net60', 'Net 60'),
    ]

    payment_terms = models.CharField(max_length=10, choices=PAYMENT_TERMS, default='prepaid')
    credit_limit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    current_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Status
    is_approved = models.BooleanField(default=False)
    is_on_hold = models.BooleanField(default=False)
    hold_reason = models.TextField(blank=True)

    # Professional pricing
    uses_wholesale_pricing = models.BooleanField(default=True)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Approval
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='+'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_available_credit(self):
        return self.credit_limit - self.current_balance


class ProfessionalStatement(models.Model):
    """Monthly statement for B2B accounts"""
    account = models.ForeignKey(ProfessionalAccount, on_delete=models.CASCADE)

    period_start = models.DateField()
    period_end = models.DateField()

    opening_balance = models.DecimalField(max_digits=10, decimal_places=2)
    charges = models.DecimalField(max_digits=10, decimal_places=2)
    payments = models.DecimalField(max_digits=10, decimal_places=2)
    closing_balance = models.DecimalField(max_digits=10, decimal_places=2)

    invoices = models.ManyToManyField(Invoice)

    pdf = models.FileField(upload_to='statements/')
    sent_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-period_end']


class PaymentReminder(models.Model):
    """Track payment reminders sent"""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='reminders')

    reminder_number = models.IntegerField()  # 1st, 2nd, 3rd
    CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
    ]
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)

    sent_at = models.DateTimeField()
    opened_at = models.DateTimeField(null=True, blank=True)

    # Response
    resulted_in_payment = models.BooleanField(default=False)


class ExchangeRate(models.Model):
    """Daily exchange rates from Banco de Mexico"""
    date = models.DateField(unique=True)
    usd_to_mxn = models.DecimalField(max_digits=10, decimal_places=4)
    eur_to_mxn = models.DecimalField(max_digits=10, decimal_places=4)
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
```

### AI Tools

```python
BILLING_TOOLS = [
    {
        "name": "create_invoice",
        "description": "Create an invoice for services or products",
        "parameters": {
            "type": "object",
            "properties": {
                "owner_id": {"type": "integer"},
                "items": {"type": "array"},
                "due_date": {"type": "string"},
                "apply_discounts": {"type": "boolean"}
            },
            "required": ["owner_id", "items"]
        }
    },
    {
        "name": "record_payment",
        "description": "Record a payment against an invoice",
        "parameters": {
            "type": "object",
            "properties": {
                "invoice_id": {"type": "integer"},
                "amount": {"type": "number"},
                "payment_method": {"type": "string"},
                "reference": {"type": "string"}
            },
            "required": ["invoice_id", "amount", "payment_method"]
        }
    },
    {
        "name": "apply_coupon",
        "description": "Apply a coupon code to an order",
        "parameters": {
            "type": "object",
            "properties": {
                "coupon_code": {"type": "string"},
                "order_id": {"type": "integer"}
            },
            "required": ["coupon_code", "order_id"]
        }
    },
    {
        "name": "check_account_balance",
        "description": "Check customer's account credit balance",
        "parameters": {
            "type": "object",
            "properties": {
                "owner_id": {"type": "integer"}
            },
            "required": ["owner_id"]
        }
    },
    {
        "name": "add_account_credit",
        "description": "Add credit to customer account",
        "parameters": {
            "type": "object",
            "properties": {
                "owner_id": {"type": "integer"},
                "amount": {"type": "number"},
                "notes": {"type": "string"}
            },
            "required": ["owner_id", "amount"]
        }
    },
    {
        "name": "get_b2b_account_status",
        "description": "Get professional account balance and status",
        "parameters": {
            "type": "object",
            "properties": {
                "account_id": {"type": "integer"}
            },
            "required": ["account_id"]
        }
    },
    {
        "name": "generate_cfdi",
        "description": "Generate CFDI (Mexican tax invoice) for an invoice",
        "parameters": {
            "type": "object",
            "properties": {
                "invoice_id": {"type": "integer"},
                "rfc": {"type": "string"},
                "uso_cfdi": {"type": "string"},
                "regimen_fiscal": {"type": "string"}
            },
            "required": ["invoice_id"]
        }
    },
    {
        "name": "send_payment_reminder",
        "description": "Send payment reminder for overdue invoice",
        "parameters": {
            "type": "object",
            "properties": {
                "invoice_id": {"type": "integer"},
                "channel": {"type": "string"}
            },
            "required": ["invoice_id"]
        }
    },
    {
        "name": "create_wellness_subscription",
        "description": "Subscribe pet to wellness plan",
        "parameters": {
            "type": "object",
            "properties": {
                "pet_id": {"type": "integer"},
                "plan_id": {"type": "integer"},
                "billing_cycle": {"type": "string"}
            },
            "required": ["pet_id", "plan_id"]
        }
    },
    {
        "name": "get_exchange_rate",
        "description": "Get current exchange rate for currency display",
        "parameters": {
            "type": "object",
            "properties": {
                "currency": {"type": "string"}
            }
        }
    }
]
```

## Example AI Conversations

### Customer Payment
```
Owner: I'd like to pay for today's visit

AI: Your invoice for Luna's checkup is ready:

    📋 Invoice #2025-0847
    ────────────────────────────
    Consulta general       $450.00
    Vacuna polivalente     $380.00
    Desparasitante         $150.00
    ────────────────────────────
    Subtotal:              $980.00
    IVA (16%):             $156.80
    ────────────────────────────
    TOTAL:               $1,136.80 MXN
                         (~$67.00 USD)

    💳 How would you like to pay?
    1. Card (online - Stripe)
    2. Cash (2% discount = $1,114.06)
    3. Use account credit ($245.00 available)
    4. Apply coupon code

Owner: Cash please

AI: ✅ Cash payment recorded!

    Amount due:          $1,136.80
    Cash discount (2%):    -$22.74
    ────────────────────────────
    You paid:            $1,114.06

    📄 CFDI (factura) details:
    Do you need a factura? If yes, provide:
    - RFC
    - Uso de CFDI (typically G03 - Gastos en general)

    Or reply "no factura" for simplified receipt.

Owner: RFC XAXX010101000

AI: ✅ Generating CFDI...

    📄 Factura generated:
    • Folio fiscal: 8A3F2B1C-...
    • XML and PDF ready

    Sent to your email: owner@email.com

    Thank you for your visit!
```

### B2B Cytology Services
```
Dr. García: I need to send 3 samples for cytology

AI: Good morning, Dr. García!

    Your professional account status:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Credit Terms: Net-30
    Credit Limit: $15,000.00
    Current Balance: $2,340.00
    Available Credit: $12,660.00
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    Cytology services (professional pricing):
    • Skin cytology: $180.00 (retail: $280)
    • Fine needle aspirate: $220.00 (retail: $350)
    • Ear cytology: $120.00 (retail: $180)

    For 3 samples, would you like me to:
    1. Create a bulk invoice for all samples
    2. Add to your monthly statement
    3. Process as separate invoices

Dr. García: Monthly statement please, 2 skin and 1 FNA

AI: ✅ Added to your account:

    2x Skin cytology @ $180.00  = $360.00
    1x Fine needle aspirate     = $220.00
    ────────────────────────────
    Subtotal:                    $580.00
    IVA (16%):                    $92.80
    ────────────────────────────
    Added to statement:          $672.80

    📊 Updated account balance: $3,012.80
    📅 Statement due: January 15, 2026

    Sample pickup instructions:
    Label samples with clinic name and patient ID.
    Results will be sent within 48-72 hours.
```

### Wellness Plan Signup
```
Owner: What wellness plans do you have?

AI: We offer 3 wellness plans to keep your pet healthy:

    🐕 PLAN BÁSICO - $450/month
    Includes:
    • 1 consultation per month
    • Annual vaccines
    • 10% off products

    🐕 PLAN COMPLETO - $750/month
    Includes:
    • 2 consultations per month
    • Annual vaccines + deworming
    • 1 dental cleaning per year
    • 15% off products

    🐕 PLAN PREMIUM - $1,200/month
    Includes:
    • Unlimited consultations
    • All vaccines + preventive care
    • 2 dental cleanings per year
    • Blood panel annually
    • 20% off all products

    💰 Pay annually and save 2 months!

    Which plan interests you for Max?

Owner: Plan Completo monthly

AI: Great choice! Setting up Plan Completo for Max:

    📋 PLAN COMPLETO
    ────────────────────────────
    Monthly: $750.00 MXN
    First payment today: $750.00

    Included each month:
    ✓ 2 consultations
    ✓ 15% off all products

    Included annually:
    ✓ All core vaccines
    ✓ Deworming (4x/year)
    ✓ 1 dental cleaning

    💳 Please complete payment to activate:
    [PAY WITH CARD]

    Or reply "pay cash" to pay in person.
```

## Definition of Done

- [ ] Stripe integration for online payments
- [ ] Cash payment with discount
- [ ] Manual card entry for in-person
- [ ] Invoice generation with line items
- [ ] IVA tax calculation
- [ ] CFDI generation via Facturama
- [ ] Multi-currency display (MXN/USD/EUR)
- [ ] Payment reminders with escalation
- [ ] Coupon codes with validation
- [ ] Customer discount tiers
- [ ] Account credit system
- [ ] Service package redemption
- [ ] Wellness plan subscriptions
- [ ] B2B professional accounts
- [ ] Monthly statements for B2B
- [ ] Account aging reports
- [ ] Exchange rate fetching
- [ ] Tests written and passing (>95% coverage)
- [ ] Documentation updated

## Dependencies

- S-005: E-Commerce Store (products, orders)
- S-004: Appointment Booking (services)
- S-016: Loyalty & Rewards (spending tiers)
- S-006: Omnichannel (reminders)

## Notes

- CFDI is legally required in Mexico - cannot skip
- Consider using Facturama sandbox for testing
- Cash discount should be reflected in CFDI correctly
- B2B accounts need approval workflow
- Monthly statement generation should be automated
- Consider credit card surcharge laws in Mexico
- Stripe works well in Mexico with MXN
