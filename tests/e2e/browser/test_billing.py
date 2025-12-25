"""Browser tests for billing and invoicing.

Tests invoice viewing, credit balance, and payment history.
"""
import re
from datetime import datetime, timedelta, date
from decimal import Decimal

import pytest
from playwright.sync_api import expect


@pytest.fixture
def pet_for_invoice(db, owner_user):
    """Create a pet for invoice tests."""
    from apps.pets.models import Pet

    pet = Pet.objects.create(
        owner=owner_user,
        name='Bella',
        species='dog',
        breed='Poodle',
        gender='female',
    )
    return pet


@pytest.fixture
def paid_invoice(db, owner_user, pet_for_invoice):
    """Create a paid invoice."""
    from apps.billing.models import Invoice, InvoiceLineItem

    invoice = Invoice.objects.create(
        owner=owner_user,
        pet=pet_for_invoice,
        subtotal=Decimal('500.00'),
        tax_amount=Decimal('80.00'),
        total=Decimal('580.00'),
        amount_paid=Decimal('580.00'),
        status='paid',
        due_date=date.today() - timedelta(days=7),
        paid_at=datetime.now() - timedelta(days=5),
    )

    # Add line items
    InvoiceLineItem.objects.create(
        invoice=invoice,
        description='Consulta General',
        quantity=Decimal('1'),
        unit_price=Decimal('300.00'),
        line_total=Decimal('300.00'),
    )
    InvoiceLineItem.objects.create(
        invoice=invoice,
        description='Vacuna Antirrábica',
        quantity=Decimal('1'),
        unit_price=Decimal('200.00'),
        line_total=Decimal('200.00'),
    )

    return invoice


@pytest.fixture
def unpaid_invoice(db, owner_user, pet_for_invoice):
    """Create an unpaid invoice."""
    from apps.billing.models import Invoice, InvoiceLineItem

    invoice = Invoice.objects.create(
        owner=owner_user,
        pet=pet_for_invoice,
        subtotal=Decimal('1200.00'),
        discount_amount=Decimal('120.00'),
        tax_amount=Decimal('172.80'),
        total=Decimal('1252.80'),
        amount_paid=Decimal('0.00'),
        status='sent',
        due_date=date.today() + timedelta(days=14),
    )

    InvoiceLineItem.objects.create(
        invoice=invoice,
        description='Cirugía de esterilización',
        quantity=Decimal('1'),
        unit_price=Decimal('1200.00'),
        discount_percent=Decimal('10.00'),
        line_total=Decimal('1080.00'),
    )

    return invoice


@pytest.fixture
def overdue_invoice(db, owner_user, pet_for_invoice):
    """Create an overdue invoice."""
    from apps.billing.models import Invoice, InvoiceLineItem

    invoice = Invoice.objects.create(
        owner=owner_user,
        pet=pet_for_invoice,
        subtotal=Decimal('350.00'),
        tax_amount=Decimal('56.00'),
        total=Decimal('406.00'),
        amount_paid=Decimal('0.00'),
        status='overdue',
        due_date=date.today() - timedelta(days=30),
    )

    InvoiceLineItem.objects.create(
        invoice=invoice,
        description='Análisis de sangre',
        quantity=Decimal('1'),
        unit_price=Decimal('350.00'),
        line_total=Decimal('350.00'),
    )

    return invoice


@pytest.fixture
def partial_invoice(db, owner_user, pet_for_invoice):
    """Create a partially paid invoice."""
    from apps.billing.models import Invoice, InvoiceLineItem

    invoice = Invoice.objects.create(
        owner=owner_user,
        pet=pet_for_invoice,
        subtotal=Decimal('800.00'),
        tax_amount=Decimal('128.00'),
        total=Decimal('928.00'),
        amount_paid=Decimal('500.00'),
        status='partial',
        due_date=date.today() + timedelta(days=7),
    )

    InvoiceLineItem.objects.create(
        invoice=invoice,
        description='Limpieza dental',
        quantity=Decimal('1'),
        unit_price=Decimal('800.00'),
        line_total=Decimal('800.00'),
    )

    return invoice


@pytest.fixture
def multiple_invoices(db, owner_user, pet_for_invoice):
    """Create multiple invoices for list testing."""
    from apps.billing.models import Invoice

    invoices = []
    for i in range(5):
        status = ['paid', 'sent', 'partial', 'overdue', 'paid'][i]
        invoice = Invoice.objects.create(
            owner=owner_user,
            pet=pet_for_invoice,
            subtotal=Decimal('100.00') * (i + 1),
            tax_amount=Decimal('16.00') * (i + 1),
            total=Decimal('116.00') * (i + 1),
            amount_paid=Decimal('116.00') * (i + 1) if status == 'paid' else Decimal('0.00'),
            status=status,
            due_date=date.today() + timedelta(days=i * 7),
        )
        invoices.append(invoice)
    return invoices


@pytest.fixture
def account_credit(db, owner_user):
    """Create account credit with transactions."""
    from apps.billing.models import AccountCredit, CreditTransaction

    credit = AccountCredit.objects.create(
        owner=owner_user,
        balance=Decimal('250.00'),
    )

    # Add transaction history
    CreditTransaction.objects.create(
        account=credit,
        transaction_type='add',
        amount=Decimal('500.00'),
        balance_after=Decimal('500.00'),
        notes='Referral bonus',
    )
    CreditTransaction.objects.create(
        account=credit,
        transaction_type='purchase',
        amount=Decimal('250.00'),
        balance_after=Decimal('250.00'),
        notes='Applied to order #123',
    )

    return credit


@pytest.mark.browser
class TestInvoiceList:
    """Test invoice list page."""

    def test_invoice_list_requires_login(self, page, live_server, db):
        """Invoice list requires authentication."""
        page.goto(f'{live_server.url}/billing/invoices/')
        page.wait_for_load_state('networkidle')

        expect(page).to_have_url(re.compile(r'.*/accounts/login.*'))

    def test_invoice_list_loads(self, authenticated_page, live_server, db):
        """Invoice list page loads."""
        page = authenticated_page

        page.goto(f'{live_server.url}/billing/invoices/')

        expect(page).to_have_title(re.compile(r'.*[Ii]nvoice.*'))
        expect(page.locator('h1')).to_contain_text('Invoices')

    def test_invoice_list_shows_invoices(self, authenticated_page, live_server, paid_invoice):
        """Invoice list shows user's invoices."""
        page = authenticated_page

        page.goto(f'{live_server.url}/billing/invoices/')

        # Should show invoice number
        expect(page.locator(f'text={paid_invoice.invoice_number}')).to_be_visible()

    def test_invoice_list_shows_total(self, authenticated_page, live_server, paid_invoice):
        """Invoice list shows invoice total."""
        page = authenticated_page

        page.goto(f'{live_server.url}/billing/invoices/')

        # Should show total amount formatted (may use comma or period as decimal separator)
        content = page.content()
        assert '580' in content

    def test_invoice_list_shows_pet_name(self, authenticated_page, live_server, paid_invoice):
        """Invoice list shows pet name."""
        page = authenticated_page

        page.goto(f'{live_server.url}/billing/invoices/')

        expect(page.locator(f'text={paid_invoice.pet.name}')).to_be_visible()

    def test_invoice_list_shows_paid_status(self, authenticated_page, live_server, paid_invoice):
        """Paid invoices show Paid badge."""
        page = authenticated_page

        page.goto(f'{live_server.url}/billing/invoices/')

        paid_badge = page.locator('.rounded-full:has-text("Paid")')
        expect(paid_badge.first).to_be_visible()

    def test_invoice_list_shows_overdue_status(self, authenticated_page, live_server, overdue_invoice):
        """Overdue invoices show Overdue badge."""
        page = authenticated_page

        page.goto(f'{live_server.url}/billing/invoices/')

        overdue_badge = page.locator('.rounded-full:has-text("Overdue")')
        expect(overdue_badge.first).to_be_visible()

    def test_invoice_list_shows_partial_status(self, authenticated_page, live_server, partial_invoice):
        """Partially paid invoices show status."""
        page = authenticated_page

        page.goto(f'{live_server.url}/billing/invoices/')

        partial_badge = page.locator('.rounded-full:has-text("Partial")')
        expect(partial_badge.first).to_be_visible()

    def test_invoice_list_empty_state(self, authenticated_page, live_server, db):
        """Empty invoice list shows message."""
        page = authenticated_page

        page.goto(f'{live_server.url}/billing/invoices/')

        empty_message = page.locator('text=No invoices')
        expect(empty_message.first).to_be_visible()

    def test_invoice_click_goes_to_detail(self, authenticated_page, live_server, paid_invoice):
        """Clicking invoice goes to detail page."""
        page = authenticated_page

        page.goto(f'{live_server.url}/billing/invoices/')

        page.locator(f'a[href*="{paid_invoice.pk}"]').first.click()
        page.wait_for_load_state('networkidle')

        expect(page).to_have_url(re.compile(rf'.*/invoices/{paid_invoice.pk}.*'))


@pytest.mark.browser
class TestInvoiceDetail:
    """Test invoice detail page."""

    def test_invoice_detail_loads(self, authenticated_page, live_server, paid_invoice):
        """Invoice detail page loads."""
        page = authenticated_page

        page.goto(f'{live_server.url}/billing/invoices/{paid_invoice.pk}/')

        expect(page.locator('h1')).to_contain_text(paid_invoice.invoice_number)

    def test_invoice_detail_shows_pet_name(self, authenticated_page, live_server, paid_invoice):
        """Invoice detail shows pet name."""
        page = authenticated_page

        page.goto(f'{live_server.url}/billing/invoices/{paid_invoice.pk}/')

        expect(page.locator(f'text={paid_invoice.pet.name}')).to_be_visible()

    def test_invoice_detail_shows_line_items(self, authenticated_page, live_server, paid_invoice):
        """Invoice detail shows line items."""
        page = authenticated_page

        page.goto(f'{live_server.url}/billing/invoices/{paid_invoice.pk}/')

        # Should show item descriptions
        expect(page.locator('text=Consulta General')).to_be_visible()
        expect(page.locator('text=Vacuna Antirrábica')).to_be_visible()

    def test_invoice_detail_shows_item_prices(self, authenticated_page, live_server, paid_invoice):
        """Invoice detail shows item prices."""
        page = authenticated_page

        page.goto(f'{live_server.url}/billing/invoices/{paid_invoice.pk}/')

        content = page.content()
        # Locale may use comma or period as decimal separator
        assert '300' in content
        assert '200' in content

    def test_invoice_detail_shows_subtotal(self, authenticated_page, live_server, paid_invoice):
        """Invoice detail shows subtotal."""
        page = authenticated_page

        page.goto(f'{live_server.url}/billing/invoices/{paid_invoice.pk}/')

        content = page.content()
        assert '500' in content

    def test_invoice_detail_shows_tax(self, authenticated_page, live_server, paid_invoice):
        """Invoice detail shows tax amount."""
        page = authenticated_page

        page.goto(f'{live_server.url}/billing/invoices/{paid_invoice.pk}/')

        content = page.content()
        assert '80' in content

    def test_invoice_detail_shows_total(self, authenticated_page, live_server, paid_invoice):
        """Invoice detail shows total."""
        page = authenticated_page

        page.goto(f'{live_server.url}/billing/invoices/{paid_invoice.pk}/')

        content = page.content()
        assert '580' in content

    def test_invoice_detail_shows_discount(self, authenticated_page, live_server, unpaid_invoice):
        """Invoice with discount shows discount amount."""
        page = authenticated_page

        page.goto(f'{live_server.url}/billing/invoices/{unpaid_invoice.pk}/')

        content = page.content()
        assert 'Discount' in content or 'discount' in content or 'Descuento' in content
        assert '120' in content

    def test_invoice_detail_shows_due_date(self, authenticated_page, live_server, unpaid_invoice):
        """Invoice detail shows due date."""
        page = authenticated_page

        page.goto(f'{live_server.url}/billing/invoices/{unpaid_invoice.pk}/')

        expect(page.locator('text=Due Date')).to_be_visible()

    def test_invoice_detail_shows_overdue_indicator(self, authenticated_page, live_server, overdue_invoice):
        """Overdue invoice shows overdue indicator."""
        page = authenticated_page

        page.goto(f'{live_server.url}/billing/invoices/{overdue_invoice.pk}/')

        content = page.content()
        assert 'Overdue' in content or 'overdue' in content

    def test_invoice_detail_shows_balance_due(self, authenticated_page, live_server, partial_invoice):
        """Partial invoice shows balance due."""
        page = authenticated_page

        page.goto(f'{live_server.url}/billing/invoices/{partial_invoice.pk}/')

        content = page.content()
        # Check balance due is shown (928.00 - 500.00 = 428.00)
        # Locale may use comma or period as decimal separator
        assert '428' in content

    def test_invoice_detail_shows_amount_paid(self, authenticated_page, live_server, partial_invoice):
        """Partial invoice shows amount paid."""
        page = authenticated_page

        page.goto(f'{live_server.url}/billing/invoices/{partial_invoice.pk}/')

        content = page.content()
        # Locale may use comma or period as decimal separator
        # Check for 500 which is the amount paid
        assert '500' in content

    def test_invoice_detail_shows_payment_info(self, authenticated_page, live_server, unpaid_invoice):
        """Unpaid invoice shows payment info."""
        page = authenticated_page

        page.goto(f'{live_server.url}/billing/invoices/{unpaid_invoice.pk}/')

        # Should show payment instructions
        expect(page.locator('text=payment options')).to_be_visible()

    def test_invoice_detail_back_link(self, authenticated_page, live_server, paid_invoice):
        """Invoice detail has back link to list."""
        page = authenticated_page

        page.goto(f'{live_server.url}/billing/invoices/{paid_invoice.pk}/')

        back_link = page.locator('a:has-text("Back to Invoices")')
        expect(back_link).to_be_visible()

    def test_invoice_detail_back_link_works(self, authenticated_page, live_server, paid_invoice):
        """Back link navigates to invoice list."""
        page = authenticated_page

        page.goto(f'{live_server.url}/billing/invoices/{paid_invoice.pk}/')

        page.locator('a:has-text("Back to Invoices")').click()
        page.wait_for_load_state('networkidle')

        expect(page).to_have_url(re.compile(r'.*/invoices/$'))


@pytest.mark.browser
class TestCreditBalance:
    """Test credit balance page."""

    def test_credit_balance_requires_login(self, page, live_server, db):
        """Credit balance page requires authentication."""
        page.goto(f'{live_server.url}/billing/credit/')
        page.wait_for_load_state('networkidle')

        expect(page).to_have_url(re.compile(r'.*/accounts/login.*'))

    def test_credit_balance_loads(self, authenticated_page, live_server, db):
        """Credit balance page loads."""
        page = authenticated_page

        page.goto(f'{live_server.url}/billing/credit/')

        expect(page).to_have_title(re.compile(r'.*[Cc]redit.*'))
        expect(page.locator('h1')).to_contain_text('Credit')

    def test_credit_balance_shows_current_balance(self, authenticated_page, live_server, account_credit):
        """Credit balance shows current balance."""
        page = authenticated_page

        page.goto(f'{live_server.url}/billing/credit/')

        content = page.content()
        # Locale may use comma or period as decimal separator
        assert '250' in content

    def test_credit_balance_shows_zero_for_no_credit(self, authenticated_page, live_server, db):
        """Shows $0.00 when no credit account exists."""
        page = authenticated_page

        page.goto(f'{live_server.url}/billing/credit/')

        expect(page.locator('text=$0.00')).to_be_visible()

    def test_credit_balance_shows_transaction_history(self, authenticated_page, live_server, account_credit):
        """Credit balance shows transaction history."""
        page = authenticated_page

        page.goto(f'{live_server.url}/billing/credit/')

        expect(page.locator('h2:has-text("Transaction History")')).to_be_visible()

    def test_credit_balance_shows_transaction_types(self, authenticated_page, live_server, account_credit):
        """Credit balance shows transaction type labels."""
        page = authenticated_page

        page.goto(f'{live_server.url}/billing/credit/')

        expect(page.locator('text=Added Credit')).to_be_visible()
        expect(page.locator('text=Purchase Applied')).to_be_visible()

    def test_credit_balance_shows_transaction_amounts(self, authenticated_page, live_server, account_credit):
        """Credit balance shows transaction amounts."""
        page = authenticated_page

        page.goto(f'{live_server.url}/billing/credit/')

        content = page.content()
        # Locale may use comma or period as decimal separator
        assert '500' in content
        assert '250' in content

    def test_credit_balance_shows_transaction_notes(self, authenticated_page, live_server, account_credit):
        """Credit balance shows transaction notes."""
        page = authenticated_page

        page.goto(f'{live_server.url}/billing/credit/')

        expect(page.locator('text=Referral bonus')).to_be_visible()

    def test_credit_balance_empty_transactions(self, authenticated_page, live_server, db):
        """Shows empty state when no transactions."""
        page = authenticated_page

        page.goto(f'{live_server.url}/billing/credit/')

        empty_message = page.locator('text=No transactions yet')
        expect(empty_message.first).to_be_visible()


@pytest.mark.browser
class TestInvoiceStatusStyling:
    """Test invoice status colors and styling."""

    def test_paid_invoice_green_header(self, authenticated_page, live_server, paid_invoice):
        """Paid invoice detail has green header background."""
        page = authenticated_page

        page.goto(f'{live_server.url}/billing/invoices/{paid_invoice.pk}/')

        # Check for green background class
        header = page.locator('.bg-green-50')
        expect(header).to_be_visible()

    def test_overdue_invoice_red_header(self, authenticated_page, live_server, overdue_invoice):
        """Overdue invoice detail has red header or overdue indicator."""
        page = authenticated_page

        page.goto(f'{live_server.url}/billing/invoices/{overdue_invoice.pk}/')

        content = page.content()
        # Should show overdue status indicator (red styling or text)
        assert 'Overdue' in content or 'overdue' in content or 'bg-red' in content

    def test_partial_invoice_yellow_header(self, authenticated_page, live_server, partial_invoice):
        """Partial invoice detail has yellow header background."""
        page = authenticated_page

        page.goto(f'{live_server.url}/billing/invoices/{partial_invoice.pk}/')

        # Check for yellow background class
        header = page.locator('.bg-yellow-50')
        expect(header).to_be_visible()


@pytest.mark.browser
class TestMobileBilling:
    """Test billing on mobile viewport."""

    def test_mobile_invoice_list(self, mobile_page, live_server, owner_user, paid_invoice):
        """Invoice list works on mobile."""
        page = mobile_page

        # Login
        page.goto(f'{live_server.url}/accounts/login/')
        page.fill('input[name="username"]', owner_user.email)
        page.fill('input[name="password"]', 'owner123')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        page.goto(f'{live_server.url}/billing/invoices/')

        # Should show invoice
        expect(page.locator(f'text={paid_invoice.invoice_number}')).to_be_visible()

    def test_mobile_invoice_detail(self, mobile_page, live_server, owner_user, paid_invoice):
        """Invoice detail works on mobile."""
        page = mobile_page

        # Login
        page.goto(f'{live_server.url}/accounts/login/')
        page.fill('input[name="username"]', owner_user.email)
        page.fill('input[name="password"]', 'owner123')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        page.goto(f'{live_server.url}/billing/invoices/{paid_invoice.pk}/')

        # Should show invoice number
        expect(page.locator('h1')).to_contain_text(paid_invoice.invoice_number)

        # Line items table should be visible
        expect(page.locator('table')).to_be_visible()

    def test_mobile_credit_balance(self, mobile_page, live_server, owner_user, account_credit):
        """Credit balance works on mobile."""
        page = mobile_page

        # Login
        page.goto(f'{live_server.url}/accounts/login/')
        page.fill('input[name="username"]', owner_user.email)
        page.fill('input[name="password"]', 'owner123')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        page.goto(f'{live_server.url}/billing/credit/')

        # Should show balance
        content = page.content()
        # Locale may use comma or period as decimal separator
        assert '250' in content
