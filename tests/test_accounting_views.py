"""
Tests for Accounting Views (TDD)

Tests cover:
- Accounting Dashboard view (staff only)
- Chart of Accounts view
- Journal entry views
- Vendor views
- Bill views
- Budget view
- Bank reconciliation views
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.accounting.models import (
    Account, JournalEntry, JournalLine, Vendor, Bill, BillLine,
    BillPayment, Budget, BankReconciliation
)

User = get_user_model()

pytestmark = pytest.mark.django_db


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def staff_user():
    """Create a staff user."""
    return User.objects.create_user(
        username='staffuser',
        email='staff@test.com',
        password='testpass123',
        is_staff=True
    )


@pytest.fixture
def regular_user():
    """Create a regular (non-staff) user."""
    return User.objects.create_user(
        username='regularuser',
        email='regular@test.com',
        password='testpass123',
        is_staff=False
    )


@pytest.fixture
def cash_account():
    """Create a cash account."""
    return Account.objects.create(
        code='1000',
        name='Cash',
        account_type='asset',
        balance=Decimal('5000.00')
    )


@pytest.fixture
def bank_account():
    """Create a bank account."""
    return Account.objects.create(
        code='1010',
        name='Checking Account',
        account_type='asset',
        is_bank=True,
        balance=Decimal('25000.00')
    )


@pytest.fixture
def expense_account():
    """Create an expense account."""
    return Account.objects.create(
        code='5000',
        name='Supplies Expense',
        account_type='expense'
    )


@pytest.fixture
def revenue_account():
    """Create a revenue account."""
    return Account.objects.create(
        code='4000',
        name='Service Revenue',
        account_type='revenue',
        balance=Decimal('15000.00')
    )


@pytest.fixture
def journal_entry(staff_user, cash_account, revenue_account):
    """Create a journal entry with lines."""
    entry = JournalEntry.objects.create(
        date=date.today(),
        reference='JE-001',
        description='Payment received for services',
        created_by=staff_user
    )
    JournalLine.objects.create(
        entry=entry,
        account=cash_account,
        debit=Decimal('500.00'),
        credit=Decimal('0.00')
    )
    JournalLine.objects.create(
        entry=entry,
        account=revenue_account,
        debit=Decimal('0.00'),
        credit=Decimal('500.00')
    )
    return entry


@pytest.fixture
def vendor():
    """Create a vendor."""
    return Vendor.objects.create(
        name='Pet Supplies Inc',
        contact_name='John Doe',
        email='john@petsupplies.com',
        phone='555-1234',
        payment_terms='net30'
    )


@pytest.fixture
def bill(vendor, expense_account):
    """Create a bill with lines."""
    bill = Bill.objects.create(
        vendor=vendor,
        bill_number='INV-001',
        bill_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        subtotal=Decimal('1000.00'),
        tax=Decimal('160.00'),
        total=Decimal('1160.00'),
        status='pending'
    )
    BillLine.objects.create(
        bill=bill,
        description='Pet food supplies',
        quantity=Decimal('10'),
        unit_price=Decimal('100.00'),
        amount=Decimal('1000.00'),
        expense_account=expense_account
    )
    return bill


@pytest.fixture
def budget(expense_account):
    """Create a budget."""
    return Budget.objects.create(
        account=expense_account,
        year=2025,
        jan=Decimal('5000.00'),
        feb=Decimal('5000.00'),
        mar=Decimal('5000.00')
    )


@pytest.fixture
def bank_reconciliation(bank_account, staff_user):
    """Create a bank reconciliation."""
    return BankReconciliation.objects.create(
        bank_account=bank_account,
        statement_date=date.today(),
        statement_balance=Decimal('25000.00')
    )


# =============================================================================
# Accounting Dashboard Tests
# =============================================================================

class TestAccountingDashboard:
    """Tests for the Accounting Dashboard view."""

    def test_dashboard_requires_authentication(self, client):
        """Anonymous users should be redirected to login."""
        url = reverse('accounting:dashboard')
        response = client.get(url)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_dashboard_requires_staff(self, client, regular_user):
        """Non-staff users should be denied access."""
        client.force_login(regular_user)
        url = reverse('accounting:dashboard')
        response = client.get(url)
        assert response.status_code == 403

    def test_dashboard_accessible_by_staff(self, client, staff_user):
        """Staff users should access the dashboard."""
        client.force_login(staff_user)
        url = reverse('accounting:dashboard')
        response = client.get(url)
        assert response.status_code == 200

    def test_dashboard_shows_account_summary(self, client, staff_user, cash_account, bank_account, revenue_account):
        """Dashboard should show account type summaries."""
        client.force_login(staff_user)
        url = reverse('accounting:dashboard')
        response = client.get(url)
        assert response.status_code == 200
        assert 'total_assets' in response.context
        assert 'total_revenue' in response.context

    def test_dashboard_shows_recent_journal_entries(self, client, staff_user, journal_entry):
        """Dashboard should show recent journal entries."""
        client.force_login(staff_user)
        url = reverse('accounting:dashboard')
        response = client.get(url)
        assert response.status_code == 200
        assert 'recent_journals' in response.context

    def test_dashboard_shows_pending_bills(self, client, staff_user, bill):
        """Dashboard should show pending bills."""
        client.force_login(staff_user)
        url = reverse('accounting:dashboard')
        response = client.get(url)
        assert response.status_code == 200
        assert 'pending_bills' in response.context


# =============================================================================
# Chart of Accounts Tests
# =============================================================================

class TestChartOfAccounts:
    """Tests for Chart of Accounts views."""

    def test_account_list_requires_staff(self, client, regular_user):
        """Non-staff users should be denied access."""
        client.force_login(regular_user)
        url = reverse('accounting:account_list')
        response = client.get(url)
        assert response.status_code == 403

    def test_account_list_shows_all_accounts(self, client, staff_user, cash_account, bank_account, expense_account):
        """Account list should show all accounts."""
        client.force_login(staff_user)
        url = reverse('accounting:account_list')
        response = client.get(url)
        assert response.status_code == 200
        assert 'accounts' in response.context
        assert len(response.context['accounts']) >= 3

    def test_account_list_grouped_by_type(self, client, staff_user, cash_account, expense_account, revenue_account):
        """Account list should group accounts by type."""
        client.force_login(staff_user)
        url = reverse('accounting:account_list')
        response = client.get(url)
        assert response.status_code == 200
        # Check accounts are grouped
        assert 'asset_accounts' in response.context or 'accounts_by_type' in response.context

    def test_account_detail_shows_balance(self, client, staff_user, cash_account):
        """Account detail should show current balance."""
        client.force_login(staff_user)
        url = reverse('accounting:account_detail', kwargs={'pk': cash_account.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert response.context['account'] == cash_account

    def test_account_detail_shows_transactions(self, client, staff_user, cash_account, journal_entry):
        """Account detail should show related transactions."""
        client.force_login(staff_user)
        url = reverse('accounting:account_detail', kwargs={'pk': cash_account.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert 'transactions' in response.context

    def test_account_create_requires_staff(self, client, regular_user):
        """Non-staff users should be denied access to create."""
        client.force_login(regular_user)
        url = reverse('accounting:account_create')
        response = client.get(url)
        assert response.status_code == 403

    def test_account_create_form_renders(self, client, staff_user):
        """Account create form should render for staff."""
        client.force_login(staff_user)
        url = reverse('accounting:account_create')
        response = client.get(url)
        assert response.status_code == 200
        assert 'form' in response.context

    def test_account_create_success(self, client, staff_user):
        """Staff can create a new account."""
        client.force_login(staff_user)
        url = reverse('accounting:account_create')
        data = {
            'code': '1100',
            'name': 'Petty Cash',
            'account_type': 'asset',
            'description': 'Small cash fund',
            'is_active': True,
        }
        response = client.post(url, data)
        assert response.status_code == 302  # Redirect on success
        assert Account.objects.filter(code='1100').exists()

    def test_account_update_requires_staff(self, client, regular_user, cash_account):
        """Non-staff users should be denied access to update."""
        client.force_login(regular_user)
        url = reverse('accounting:account_update', kwargs={'pk': cash_account.pk})
        response = client.get(url)
        assert response.status_code == 403

    def test_account_update_form_renders(self, client, staff_user, cash_account):
        """Account update form should render with existing data."""
        client.force_login(staff_user)
        url = reverse('accounting:account_update', kwargs={'pk': cash_account.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['object'] == cash_account

    def test_account_update_success(self, client, staff_user, cash_account):
        """Staff can update an existing account."""
        client.force_login(staff_user)
        url = reverse('accounting:account_update', kwargs={'pk': cash_account.pk})
        data = {
            'code': '1000',
            'name': 'Cash on Hand',  # Changed name
            'account_type': 'asset',
            'description': 'Updated description',
            'is_active': True,
        }
        response = client.post(url, data)
        assert response.status_code == 302  # Redirect on success
        cash_account.refresh_from_db()
        assert cash_account.name == 'Cash on Hand'

    def test_account_delete_requires_staff(self, client, regular_user, cash_account):
        """Non-staff users should be denied access to delete."""
        client.force_login(regular_user)
        url = reverse('accounting:account_delete', kwargs={'pk': cash_account.pk})
        response = client.get(url)
        assert response.status_code == 403

    def test_account_delete_confirmation_renders(self, client, staff_user, cash_account):
        """Account delete confirmation should render."""
        client.force_login(staff_user)
        url = reverse('accounting:account_delete', kwargs={'pk': cash_account.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert 'account' in response.context

    def test_account_delete_soft_deletes(self, client, staff_user, cash_account):
        """Deleting an account should soft delete (deactivate) it."""
        client.force_login(staff_user)
        url = reverse('accounting:account_delete', kwargs={'pk': cash_account.pk})
        response = client.post(url)
        assert response.status_code == 302  # Redirect on success
        cash_account.refresh_from_db()
        assert cash_account.is_active is False


# =============================================================================
# Journal Entry Tests
# =============================================================================

class TestJournalEntries:
    """Tests for Journal Entry views."""

    def test_journal_list_requires_staff(self, client, regular_user):
        """Non-staff users should be denied access."""
        client.force_login(regular_user)
        url = reverse('accounting:journal_list')
        response = client.get(url)
        assert response.status_code == 403

    def test_journal_list_shows_entries(self, client, staff_user, journal_entry):
        """Journal list should show all entries."""
        client.force_login(staff_user)
        url = reverse('accounting:journal_list')
        response = client.get(url)
        assert response.status_code == 200
        assert 'journals' in response.context
        assert journal_entry in response.context['journals']

    def test_journal_list_is_paginated(self, client, staff_user):
        """Journal list should be paginated."""
        client.force_login(staff_user)
        url = reverse('accounting:journal_list')
        response = client.get(url)
        assert response.status_code == 200
        assert 'is_paginated' in response.context or hasattr(response.context.get('journals'), 'paginator')

    def test_journal_detail_shows_lines(self, client, staff_user, journal_entry):
        """Journal detail should show all lines."""
        client.force_login(staff_user)
        url = reverse('accounting:journal_detail', kwargs={'pk': journal_entry.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert response.context['journal'] == journal_entry
        assert 'lines' in response.context
        assert len(response.context['lines']) == 2

    def test_journal_detail_shows_balanced_status(self, client, staff_user, journal_entry):
        """Journal detail should show if entry is balanced."""
        client.force_login(staff_user)
        url = reverse('accounting:journal_detail', kwargs={'pk': journal_entry.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert response.context['journal'].is_balanced


# =============================================================================
# Vendor Tests
# =============================================================================

class TestVendors:
    """Tests for Vendor views."""

    def test_vendor_list_requires_staff(self, client, regular_user):
        """Non-staff users should be denied access."""
        client.force_login(regular_user)
        url = reverse('accounting:vendor_list')
        response = client.get(url)
        assert response.status_code == 403

    def test_vendor_list_shows_vendors(self, client, staff_user, vendor):
        """Vendor list should show all vendors."""
        client.force_login(staff_user)
        url = reverse('accounting:vendor_list')
        response = client.get(url)
        assert response.status_code == 200
        assert 'vendors' in response.context
        assert vendor in response.context['vendors']

    def test_vendor_detail_shows_info(self, client, staff_user, vendor):
        """Vendor detail should show vendor information."""
        client.force_login(staff_user)
        url = reverse('accounting:vendor_detail', kwargs={'pk': vendor.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert response.context['vendor'] == vendor

    def test_vendor_detail_shows_bills(self, client, staff_user, vendor, bill):
        """Vendor detail should show related bills."""
        client.force_login(staff_user)
        url = reverse('accounting:vendor_detail', kwargs={'pk': vendor.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert 'bills' in response.context


# =============================================================================
# Bill Tests
# =============================================================================

class TestBills:
    """Tests for Bill views."""

    def test_bill_list_requires_staff(self, client, regular_user):
        """Non-staff users should be denied access."""
        client.force_login(regular_user)
        url = reverse('accounting:bill_list')
        response = client.get(url)
        assert response.status_code == 403

    def test_bill_list_shows_bills(self, client, staff_user, bill):
        """Bill list should show all bills."""
        client.force_login(staff_user)
        url = reverse('accounting:bill_list')
        response = client.get(url)
        assert response.status_code == 200
        assert 'bills' in response.context
        assert bill in response.context['bills']

    def test_bill_list_filter_by_status(self, client, staff_user, bill):
        """Bill list should filter by status."""
        client.force_login(staff_user)
        url = reverse('accounting:bill_list') + '?status=pending'
        response = client.get(url)
        assert response.status_code == 200

    def test_bill_detail_shows_lines(self, client, staff_user, bill):
        """Bill detail should show all line items."""
        client.force_login(staff_user)
        url = reverse('accounting:bill_detail', kwargs={'pk': bill.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert response.context['bill'] == bill
        assert 'lines' in response.context

    def test_bill_detail_shows_payments(self, client, staff_user, bill, bank_account):
        """Bill detail should show payment history."""
        # Create a payment
        BillPayment.objects.create(
            bill=bill,
            date=date.today(),
            amount=Decimal('500.00'),
            payment_method='transfer',
            bank_account=bank_account
        )

        client.force_login(staff_user)
        url = reverse('accounting:bill_detail', kwargs={'pk': bill.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert 'payments' in response.context


# =============================================================================
# Budget Tests
# =============================================================================

class TestBudgets:
    """Tests for Budget views."""

    def test_budget_list_requires_staff(self, client, regular_user):
        """Non-staff users should be denied access."""
        client.force_login(regular_user)
        url = reverse('accounting:budget_list')
        response = client.get(url)
        assert response.status_code == 403

    def test_budget_list_shows_budgets(self, client, staff_user, budget):
        """Budget list should show all budgets."""
        client.force_login(staff_user)
        url = reverse('accounting:budget_list')
        response = client.get(url)
        assert response.status_code == 200
        assert 'budgets' in response.context

    def test_budget_list_filter_by_year(self, client, staff_user, budget):
        """Budget list should filter by year."""
        client.force_login(staff_user)
        url = reverse('accounting:budget_list') + '?year=2025'
        response = client.get(url)
        assert response.status_code == 200


# =============================================================================
# Bank Reconciliation Tests
# =============================================================================

class TestBankReconciliation:
    """Tests for Bank Reconciliation views."""

    def test_reconciliation_list_requires_staff(self, client, regular_user):
        """Non-staff users should be denied access."""
        client.force_login(regular_user)
        url = reverse('accounting:reconciliation_list')
        response = client.get(url)
        assert response.status_code == 403

    def test_reconciliation_list_shows_reconciliations(self, client, staff_user, bank_reconciliation):
        """Reconciliation list should show all reconciliations."""
        client.force_login(staff_user)
        url = reverse('accounting:reconciliation_list')
        response = client.get(url)
        assert response.status_code == 200
        assert 'reconciliations' in response.context

    def test_reconciliation_detail_shows_info(self, client, staff_user, bank_reconciliation):
        """Reconciliation detail should show reconciliation info."""
        client.force_login(staff_user)
        url = reverse('accounting:reconciliation_detail', kwargs={'pk': bank_reconciliation.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert response.context['reconciliation'] == bank_reconciliation
