# T-040: Billing & Invoicing System

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md and [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement comprehensive billing with CFDI support
**Related Story**: S-020
**Epoch**: 3
**Estimate**: 6 hours

### Constraints
**Allowed File Paths**: apps/billing/
**Forbidden Paths**: None

### Deliverables
- [ ] Invoice model
- [ ] Payment model
- [ ] CFDI integration (Facturama)
- [ ] Discount/coupon system
- [ ] B2B professional accounts
- [ ] Payment reminders

### Implementation Details

See full model definitions in: `planning/stories/S-020-billing-invoicing.md`

#### Key Models
- Invoice, InvoiceLineItem
- Payment
- CouponCode
- CustomerDiscount
- PrepaidPackage
- WellnessPlan, WellnessPlanSubscription
- ProfessionalAccount
- PaymentReminder

#### CFDI Integration
```python
class CFDIService:
    """Mexican tax invoice generation via Facturama."""

    def __init__(self):
        self.client = facturama.Client(
            settings.FACTURAMA_USER,
            settings.FACTURAMA_PASSWORD,
            sandbox=settings.FACTURAMA_SANDBOX
        )

    def generate_cfdi(self, invoice: Invoice, rfc: str, uso_cfdi: str) -> dict:
        """Generate CFDI for invoice."""

        cfdi_data = {
            "Receiver": {
                "Rfc": rfc,
                "Name": invoice.owner.get_full_name(),
                "CfdiUse": uso_cfdi,
                "FiscalRegime": "612",  # Physical person with business
                "TaxZipCode": "77580",  # Puerto Morelos
            },
            "CfdiType": "I",  # Income
            "PaymentForm": self._get_payment_form(invoice),
            "PaymentMethod": "PUE",  # Single payment
            "Currency": "MXN",
            "Items": [
                {
                    "ProductCode": item.clave_producto_sat or "01010101",
                    "Description": item.description,
                    "UnitCode": item.clave_unidad_sat or "E48",
                    "UnitPrice": float(item.unit_price),
                    "Quantity": float(item.quantity),
                    "Subtotal": float(item.line_total),
                    "Taxes": [{
                        "Name": "IVA",
                        "Rate": 0.16,
                        "Total": float(item.line_total * Decimal('0.16')),
                    }],
                    "Total": float(item.line_total * Decimal('1.16')),
                }
                for item in invoice.items.all()
            ],
        }

        response = self.client.create_cfdi(cfdi_data)

        # Update invoice
        invoice.cfdi_uuid = response['Complement']['TaxStamp']['Uuid']
        invoice.cfdi_xml = response['OriginalString']
        invoice.cfdi_status = 'stamped'
        invoice.save()

        # Download PDF
        pdf_content = self.client.get_pdf(response['Id'])
        invoice.cfdi_pdf.save(
            f"cfdi_{invoice.invoice_number}.pdf",
            ContentFile(pdf_content)
        )

        return {
            "uuid": invoice.cfdi_uuid,
            "pdf_url": invoice.cfdi_pdf.url
        }

    def _get_payment_form(self, invoice: Invoice) -> str:
        """Map payment method to SAT code."""
        mapping = {
            'cash': '01',
            'stripe_card': '04',
            'manual_card': '04',
            'bank_transfer': '03',
            'paypal': '31',
        }
        payment = invoice.payments.first()
        return mapping.get(payment.payment_method if payment else 'cash', '99')
```

#### Discount System
```python
class DiscountService:
    """Calculate and apply discounts."""

    def calculate_order_discount(self, user: User, items: list, coupon: CouponCode = None) -> Decimal:
        """Calculate total discount for order."""

        discount = Decimal('0')

        # Customer-level discount
        customer_discount = CustomerDiscount.objects.filter(owner=user).first()
        if customer_discount:
            for item in items:
                if item.is_service and customer_discount.applies_to_services:
                    discount += item.line_total * (customer_discount.discount_percent / 100)
                elif not item.is_service and customer_discount.applies_to_products:
                    discount += item.line_total * (customer_discount.discount_percent / 100)

        # Coupon discount (additional)
        if coupon:
            subtotal = sum(item.line_total for item in items)
            if coupon.discount_type == 'percent':
                discount += subtotal * (coupon.discount_value / 100)
            else:
                discount += coupon.discount_value

        return discount

    def apply_loyalty_discount(self, user: User, amount: Decimal) -> Decimal:
        """Apply loyalty tier discount."""
        membership = LoyaltyMembership.objects.filter(user=user).first()
        if membership and membership.tier:
            return amount * (membership.tier.discount_percent / 100)
        return Decimal('0')
```

#### B2B Professional Accounts
```python
class ProfessionalAccountService:
    """Manage B2B accounts for other veterinarians."""

    def check_credit(self, account: ProfessionalAccount, amount: Decimal) -> bool:
        """Check if account has sufficient credit."""
        available = account.credit_limit - account.current_balance
        return available >= amount and not account.is_on_hold

    def charge_to_account(self, account: ProfessionalAccount, invoice: Invoice):
        """Charge invoice to professional account."""

        if not self.check_credit(account, invoice.total):
            raise ValidationError("Crédito insuficiente")

        account.current_balance += invoice.total
        account.save()

        # Record payment as "on account"
        Payment.objects.create(
            invoice=invoice,
            amount=invoice.total,
            payment_method='account_credit',
            notes=f"Cargo a cuenta profesional {account.business_name}"
        )

        invoice.status = 'paid'
        invoice.save()

    def generate_statement(self, account: ProfessionalAccount, period_start: date, period_end: date):
        """Generate monthly statement."""

        invoices = Invoice.objects.filter(
            owner=account.owner,
            created_at__date__range=(period_start, period_end)
        )

        statement = ProfessionalStatement.objects.create(
            account=account,
            period_start=period_start,
            period_end=period_end,
            opening_balance=self._get_balance_at(account, period_start),
            charges=invoices.aggregate(Sum('total'))['total__sum'] or 0,
            payments=self._get_payments(account, period_start, period_end),
            closing_balance=account.current_balance
        )
        statement.invoices.set(invoices)

        # Generate PDF
        pdf = self._generate_statement_pdf(statement)
        statement.pdf.save(f"statement_{statement.id}.pdf", ContentFile(pdf))

        return statement
```

### Test Cases
- [ ] Invoice creation works
- [ ] CFDI generates correctly
- [ ] Payments record properly
- [ ] Coupons apply correctly
- [ ] Customer discounts work
- [ ] B2B credit checking works
- [ ] Statements generate

### Definition of Done
- [ ] All billing models migrated
- [ ] CFDI integration working
- [ ] Discount system complete
- [ ] B2B accounts functional
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-038: Checkout & Stripe Integration

### Environment Variables
```
FACTURAMA_USER=
FACTURAMA_PASSWORD=
FACTURAMA_SANDBOX=true
```
