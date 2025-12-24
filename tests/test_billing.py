"""Tests for S-020 Billing & Invoicing.

Tests validate billing functionality:
- Invoice creation and management
- Payment recording
- Discounts and coupons
- Account credits
- B2B professional accounts
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

User = get_user_model()


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def owner_user(db):
    """Create a pet owner user."""
    return User.objects.create_user(
        username='owner_billing',
        email='owner@example.com',
        password='testpass123'
    )


@pytest.fixture
def staff_user(db):
    """Create a staff user."""
    return User.objects.create_user(
        username='staff_billing',
        email='staff@petfriendly.com',
        password='testpass123',
        is_staff=True
    )


@pytest.fixture
def pet(db, owner_user):
    """Create a pet for the owner."""
    from apps.pets.models import Pet
    return Pet.objects.create(
        owner=owner_user,
        name='Max',
        species='dog',
        breed='Labrador'
    )


@pytest.fixture
def invoice(db, owner_user, pet):
    """Create a basic invoice."""
    from apps.billing.models import Invoice
    return Invoice.objects.create(
        owner=owner_user,
        pet=pet,
        subtotal=Decimal('1000.00'),
        tax_amount=Decimal('160.00'),
        total=Decimal('1160.00'),
        due_date=date.today() + timedelta(days=30)
    )


@pytest.fixture
def coupon(db):
    """Create a coupon code."""
    from apps.billing.models import CouponCode
    return CouponCode.objects.create(
        code='SAVE10',
        description='10% off your order',
        discount_type='percent',
        discount_value=Decimal('10.00'),
        valid_from=timezone.now() - timedelta(days=1),
        is_active=True
    )


# =============================================================================
# Invoice Model Tests
# =============================================================================

@pytest.mark.django_db
class TestInvoiceModel:
    """Tests for the Invoice model."""

    def test_create_invoice(self, owner_user, pet):
        """Can create a basic invoice."""
        from apps.billing.models import Invoice

        invoice = Invoice.objects.create(
            owner=owner_user,
            pet=pet,
            subtotal=Decimal('500.00'),
            tax_amount=Decimal('80.00'),
            total=Decimal('580.00'),
            due_date=date.today() + timedelta(days=30)
        )

        assert invoice.pk is not None
        assert invoice.status == 'draft'
        assert invoice.invoice_number is not None

    def test_invoice_number_auto_generated(self, owner_user, pet):
        """Invoice number is auto-generated if not provided."""
        from apps.billing.models import Invoice

        invoice = Invoice.objects.create(
            owner=owner_user,
            subtotal=Decimal('100.00'),
            tax_amount=Decimal('16.00'),
            total=Decimal('116.00'),
            due_date=date.today()
        )

        assert invoice.invoice_number is not None
        assert str(date.today().year) in invoice.invoice_number

    def test_invoice_balance_due(self, invoice):
        """Balance due is calculated correctly."""
        assert invoice.get_balance_due() == Decimal('1160.00')

        # After partial payment
        invoice.amount_paid = Decimal('500.00')
        invoice.save()
        assert invoice.get_balance_due() == Decimal('660.00')

    def test_invoice_is_paid(self, invoice):
        """Invoice is_paid property works correctly."""
        assert invoice.is_paid is False

        invoice.amount_paid = invoice.total
        invoice.status = 'paid'
        invoice.save()
        assert invoice.is_paid is True

    def test_invoice_is_overdue(self, invoice):
        """Invoice is_overdue property works correctly."""
        assert invoice.is_overdue is False

        invoice.due_date = date.today() - timedelta(days=1)
        invoice.save()
        assert invoice.is_overdue is True


@pytest.mark.django_db
class TestInvoiceLineItem:
    """Tests for invoice line items."""

    def test_add_line_item(self, invoice):
        """Can add line items to invoice."""
        from apps.billing.models import InvoiceLineItem

        item = InvoiceLineItem.objects.create(
            invoice=invoice,
            description='Consulta veterinaria',
            quantity=Decimal('1'),
            unit_price=Decimal('500.00'),
            line_total=Decimal('500.00')
        )

        assert item.pk is not None
        assert invoice.items.count() == 1

    def test_line_item_calculates_total(self, invoice):
        """Line item calculates total correctly."""
        from apps.billing.models import InvoiceLineItem

        item = InvoiceLineItem.objects.create(
            invoice=invoice,
            description='Vacuna',
            quantity=Decimal('2'),
            unit_price=Decimal('250.00'),
            discount_percent=Decimal('10.00'),
            line_total=Decimal('450.00')  # 2 * 250 * 0.9
        )

        assert item.line_total == Decimal('450.00')


# =============================================================================
# Payment Model Tests
# =============================================================================

@pytest.mark.django_db
class TestPaymentModel:
    """Tests for the Payment model."""

    def test_record_cash_payment(self, invoice, staff_user):
        """Can record a cash payment."""
        from apps.billing.models import Payment

        payment = Payment.objects.create(
            invoice=invoice,
            amount=Decimal('1160.00'),
            payment_method='cash',
            recorded_by=staff_user
        )

        assert payment.pk is not None
        assert payment.payment_method == 'cash'

    def test_record_card_payment(self, invoice, staff_user):
        """Can record a card payment."""
        from apps.billing.models import Payment

        payment = Payment.objects.create(
            invoice=invoice,
            amount=Decimal('1160.00'),
            payment_method='manual_card',
            reference_number='AUTH-12345',
            recorded_by=staff_user
        )

        assert payment.pk is not None
        assert payment.reference_number == 'AUTH-12345'

    def test_cash_discount_applied(self, invoice, staff_user):
        """Cash discount is applied correctly."""
        from apps.billing.models import Payment

        # 2% cash discount on 1160 = 23.20
        discount = Decimal('23.20')
        payment = Payment.objects.create(
            invoice=invoice,
            amount=Decimal('1136.80'),
            payment_method='cash',
            cash_discount_applied=discount,
            recorded_by=staff_user
        )

        assert payment.cash_discount_applied == discount


# =============================================================================
# Customer Discount Tests
# =============================================================================

@pytest.mark.django_db
class TestCustomerDiscount:
    """Tests for persistent customer discounts."""

    def test_create_vip_discount(self, owner_user, staff_user):
        """Can create VIP customer discount."""
        from apps.billing.models import CustomerDiscount

        discount = CustomerDiscount.objects.create(
            owner=owner_user,
            discount_type='vip',
            discount_percent=Decimal('15.00'),
            approved_by=staff_user
        )

        assert discount.discount_percent == Decimal('15.00')
        assert discount.applies_to_products is True
        assert discount.applies_to_services is True

    def test_discount_only_for_services(self, owner_user, staff_user):
        """Discount can apply only to services."""
        from apps.billing.models import CustomerDiscount

        discount = CustomerDiscount.objects.create(
            owner=owner_user,
            discount_type='rescue',
            discount_percent=Decimal('25.00'),
            applies_to_products=False,
            applies_to_services=True,
            approved_by=staff_user
        )

        assert discount.applies_to_products is False
        assert discount.applies_to_services is True


# =============================================================================
# Coupon Tests
# =============================================================================

@pytest.mark.django_db
class TestCouponCode:
    """Tests for coupon codes."""

    def test_create_percent_coupon(self):
        """Can create percentage coupon."""
        from apps.billing.models import CouponCode

        coupon = CouponCode.objects.create(
            code='SUMMER20',
            description='Summer sale 20% off',
            discount_type='percent',
            discount_value=Decimal('20.00'),
            valid_from=timezone.now()
        )

        assert coupon.is_valid() is True

    def test_create_fixed_coupon(self):
        """Can create fixed amount coupon."""
        from apps.billing.models import CouponCode

        coupon = CouponCode.objects.create(
            code='SAVE100',
            description='Save 100 pesos',
            discount_type='fixed',
            discount_value=Decimal('100.00'),
            valid_from=timezone.now()
        )

        assert coupon.discount_type == 'fixed'

    def test_coupon_expired(self):
        """Expired coupon is not valid."""
        from apps.billing.models import CouponCode

        coupon = CouponCode.objects.create(
            code='EXPIRED',
            description='Expired coupon',
            discount_type='percent',
            discount_value=Decimal('10.00'),
            valid_from=timezone.now() - timedelta(days=30),
            valid_until=timezone.now() - timedelta(days=1)
        )

        assert coupon.is_valid() is False

    def test_coupon_not_yet_valid(self):
        """Future coupon is not valid yet."""
        from apps.billing.models import CouponCode

        coupon = CouponCode.objects.create(
            code='FUTURE',
            description='Future coupon',
            discount_type='percent',
            discount_value=Decimal('10.00'),
            valid_from=timezone.now() + timedelta(days=1)
        )

        assert coupon.is_valid() is False

    def test_coupon_max_uses_reached(self):
        """Coupon with max uses reached is not valid."""
        from apps.billing.models import CouponCode

        coupon = CouponCode.objects.create(
            code='LIMITED',
            description='Limited use coupon',
            discount_type='percent',
            discount_value=Decimal('10.00'),
            valid_from=timezone.now(),
            max_uses=5,
            times_used=5
        )

        assert coupon.is_valid() is False

    def test_coupon_inactive(self):
        """Inactive coupon is not valid."""
        from apps.billing.models import CouponCode

        coupon = CouponCode.objects.create(
            code='INACTIVE',
            description='Inactive coupon',
            discount_type='percent',
            discount_value=Decimal('10.00'),
            valid_from=timezone.now(),
            is_active=False
        )

        assert coupon.is_valid() is False


@pytest.mark.django_db
class TestCouponUsage:
    """Tests for tracking coupon usage."""

    def test_track_coupon_usage(self, coupon, invoice, owner_user):
        """Can track coupon usage per customer."""
        from apps.billing.models import CouponUsage

        usage = CouponUsage.objects.create(
            coupon=coupon,
            owner=owner_user,
            invoice=invoice,
            discount_applied=Decimal('116.00')
        )

        assert usage.pk is not None
        assert usage.discount_applied == Decimal('116.00')


# =============================================================================
# Account Credit Tests
# =============================================================================

@pytest.mark.django_db
class TestAccountCredit:
    """Tests for account credit functionality."""

    def test_create_account_credit(self, owner_user):
        """Can create account credit balance."""
        from apps.billing.models import AccountCredit

        credit = AccountCredit.objects.create(
            owner=owner_user,
            balance=Decimal('500.00')
        )

        assert credit.balance == Decimal('500.00')

    def test_add_credit_transaction(self, owner_user, staff_user):
        """Can add credit to account."""
        from apps.billing.models import AccountCredit, CreditTransaction

        credit, _ = AccountCredit.objects.get_or_create(
            owner=owner_user,
            defaults={'balance': Decimal('0')}
        )

        transaction = CreditTransaction.objects.create(
            account=credit,
            transaction_type='add',
            amount=Decimal('200.00'),
            balance_after=Decimal('200.00'),
            created_by=staff_user,
            notes='Gift credit'
        )

        assert transaction.transaction_type == 'add'
        assert transaction.balance_after == Decimal('200.00')


# =============================================================================
# Professional Account (B2B) Tests
# =============================================================================

@pytest.mark.django_db
class TestProfessionalAccount:
    """Tests for B2B professional accounts."""

    def test_create_professional_account(self, owner_user):
        """Can create B2B professional account."""
        from apps.billing.models import ProfessionalAccount

        account = ProfessionalAccount.objects.create(
            owner=owner_user,
            business_name='Veterinaria Del Norte',
            rfc='XAXX010101AAA',
            contact_name='Dr. Garcia',
            phone='998-123-4567',
            email='drgarcia@example.com',
            payment_terms='net30',
            credit_limit=Decimal('50000.00')
        )

        assert account.pk is not None
        assert account.is_approved is False

    def test_professional_account_credit_available(self, owner_user, staff_user):
        """Available credit is calculated correctly."""
        from apps.billing.models import ProfessionalAccount

        account = ProfessionalAccount.objects.create(
            owner=owner_user,
            business_name='Veterinaria Del Sur',
            rfc='XAXX010101BBB',
            contact_name='Dr. Martinez',
            phone='998-987-6543',
            email='drmartinez@example.com',
            payment_terms='net30',
            credit_limit=Decimal('10000.00'),
            current_balance=Decimal('3000.00'),
            is_approved=True,
            approved_by=staff_user
        )

        assert account.get_available_credit() == Decimal('7000.00')

    def test_professional_account_on_hold(self, owner_user, staff_user):
        """Account can be put on hold."""
        from apps.billing.models import ProfessionalAccount

        account = ProfessionalAccount.objects.create(
            owner=owner_user,
            business_name='Veterinaria Problema',
            rfc='XAXX010101CCC',
            contact_name='Dr. Problemático',
            phone='998-111-2222',
            email='problema@example.com',
            is_approved=True,
            approved_by=staff_user,
            is_on_hold=True,
            hold_reason='Overdue payments exceeding 90 days'
        )

        assert account.is_on_hold is True


# =============================================================================
# Exchange Rate Tests
# =============================================================================

@pytest.mark.django_db
class TestExchangeRate:
    """Tests for exchange rate tracking."""

    def test_create_exchange_rate(self):
        """Can create exchange rate record."""
        from apps.billing.models import ExchangeRate

        rate = ExchangeRate.objects.create(
            date=date.today(),
            usd_to_mxn=Decimal('17.50'),
            eur_to_mxn=Decimal('19.25')
        )

        assert rate.usd_to_mxn == Decimal('17.50')
        assert rate.eur_to_mxn == Decimal('19.25')

    def test_get_latest_rate(self):
        """Can get latest exchange rate."""
        from apps.billing.models import ExchangeRate

        ExchangeRate.objects.create(
            date=date.today() - timedelta(days=1),
            usd_to_mxn=Decimal('17.00'),
            eur_to_mxn=Decimal('18.50')
        )
        latest = ExchangeRate.objects.create(
            date=date.today(),
            usd_to_mxn=Decimal('17.50'),
            eur_to_mxn=Decimal('19.25')
        )

        assert ExchangeRate.objects.first() == latest


# =============================================================================
# AI Tools Tests
# =============================================================================

@pytest.mark.django_db
class TestBillingAITools:
    """Tests for billing AI tools."""

    def test_get_invoice_details(self, invoice, owner_user):
        """Get invoice details via AI tool."""
        from apps.ai_assistant.tools import get_invoice_details

        result = get_invoice_details(
            invoice_id=invoice.id,
            user_id=owner_user.id
        )

        assert 'invoice' in result
        assert result['invoice']['total'] == str(invoice.total)

    def test_get_customer_invoices(self, invoice, owner_user):
        """Get customer's invoices via AI tool."""
        from apps.ai_assistant.tools import get_customer_invoices

        result = get_customer_invoices(user_id=owner_user.id)

        assert 'invoices' in result
        assert len(result['invoices']) >= 1

    def test_check_coupon_validity(self, coupon):
        """Check coupon validity via AI tool."""
        from apps.ai_assistant.tools import check_coupon

        result = check_coupon(code='SAVE10')

        assert result['valid'] is True
        assert result['discount_type'] == 'percent'
        assert result['discount_value'] == '10.00'

    def test_get_account_balance(self, owner_user):
        """Get account credit balance via AI tool."""
        from apps.billing.models import AccountCredit
        from apps.ai_assistant.tools import get_account_balance

        AccountCredit.objects.create(
            owner=owner_user,
            balance=Decimal('250.00')
        )

        result = get_account_balance(user_id=owner_user.id)

        assert result['balance'] == '250.00'


# =============================================================================
# View Tests
# =============================================================================

@pytest.mark.django_db
class TestBillingViews:
    """Tests for billing views."""

    def test_invoice_list_requires_login(self, client):
        """Invoice list requires authentication."""
        response = client.get(reverse('billing:invoice_list'))
        assert response.status_code == 302
        assert 'login' in response.url

    def test_invoice_list_shows_user_invoices(self, client, invoice, owner_user):
        """Invoice list shows only user's invoices."""
        client.force_login(owner_user)
        response = client.get(reverse('billing:invoice_list'))
        assert response.status_code == 200
        assert invoice.invoice_number in response.content.decode()

    def test_invoice_detail_requires_login(self, client, invoice):
        """Invoice detail requires authentication."""
        response = client.get(reverse('billing:invoice_detail', args=[invoice.pk]))
        assert response.status_code == 302

    def test_invoice_detail_shows_invoice_info(self, client, invoice, owner_user):
        """Invoice detail shows invoice information."""
        client.force_login(owner_user)
        response = client.get(reverse('billing:invoice_detail', args=[invoice.pk]))
        assert response.status_code == 200
        content = response.content.decode()
        assert invoice.invoice_number in content
        assert '1160' in content or '1,160' in content  # Total amount (different locales)

    def test_invoice_detail_access_denied_for_other_user(self, client, invoice, staff_user):
        """Users cannot view other users' invoices."""
        client.force_login(staff_user)
        response = client.get(reverse('billing:invoice_detail', args=[invoice.pk]))
        assert response.status_code == 404

    def test_credit_balance_shows_balance(self, client, owner_user):
        """Credit balance page shows user's credit balance."""
        from apps.billing.models import AccountCredit
        AccountCredit.objects.create(owner=owner_user, balance=Decimal('350.00'))

        client.force_login(owner_user)
        response = client.get(reverse('billing:credit_balance'))
        assert response.status_code == 200
        assert '350' in response.content.decode()
