"""Tests for Accounting app (TDD first)."""
import pytest
from decimal import Decimal
from datetime import date

from apps.accounts.models import User

pytestmark = pytest.mark.django_db


class TestAccountModel:
    """Tests for Account (Chart of Accounts) model."""

    def test_create_account(self):
        """Test creating an account."""
        from apps.accounting.models import Account

        account = Account.objects.create(
            code='1000',
            name='Cash',
            account_type='asset',
        )

        assert account.code == '1000'
        assert account.account_type == 'asset'
        assert account.balance == 0

    def test_account_hierarchy(self):
        """Test account parent-child relationship."""
        from apps.accounting.models import Account

        parent = Account.objects.create(
            code='1000',
            name='Current Assets',
            account_type='asset',
        )
        child = Account.objects.create(
            code='1010',
            name='Checking Account',
            account_type='asset',
            parent=parent,
        )

        assert child.parent == parent


class TestJournalEntryModel:
    """Tests for JournalEntry model."""

    def test_create_journal_entry(self, user):
        """Test creating a journal entry."""
        from apps.accounting.models import JournalEntry

        entry = JournalEntry.objects.create(
            date=date.today(),
            reference='JE-001',
            description='Opening balance',
            created_by=user,
        )

        assert entry.reference == 'JE-001'
        assert entry.is_posted is False

    def test_post_journal_entry(self, user):
        """Test posting a journal entry."""
        from apps.accounting.models import JournalEntry

        entry = JournalEntry.objects.create(
            date=date.today(),
            reference='JE-002',
            description='Test entry',
            created_by=user,
        )

        entry.is_posted = True
        entry.save()
        assert entry.is_posted is True


class TestJournalLineModel:
    """Tests for JournalLine model."""

    def test_create_journal_line(self, user, journal_entry, account):
        """Test creating a journal line."""
        from apps.accounting.models import JournalLine

        line = JournalLine.objects.create(
            entry=journal_entry,
            account=account,
            debit=Decimal('1000.00'),
            credit=Decimal('0.00'),
            description='Cash received',
        )

        assert line.debit == Decimal('1000.00')
        assert line.credit == Decimal('0.00')


class TestVendorModel:
    """Tests for Vendor model."""

    def test_create_vendor(self):
        """Test creating a vendor."""
        from apps.accounting.models import Vendor

        vendor = Vendor.objects.create(
            name='Pet Supplies Inc',
            contact_name='John Doe',
            email='john@petsupplies.com',
            phone='555-1234',
        )

        assert vendor.name == 'Pet Supplies Inc'
        assert vendor.is_active is True


class TestBillModel:
    """Tests for Bill (Accounts Payable) model."""

    def test_create_bill(self, vendor):
        """Test creating a bill."""
        from apps.accounting.models import Bill

        bill = Bill.objects.create(
            vendor=vendor,
            bill_number='INV-001',
            bill_date=date.today(),
            due_date=date.today(),
            subtotal=Decimal('1000.00'),
            tax=Decimal('160.00'),
            total=Decimal('1160.00'),
        )

        assert bill.status == 'draft'
        assert bill.total == Decimal('1160.00')


class TestBillPaymentModel:
    """Tests for BillPayment model."""

    def test_create_bill_payment(self, bill, bank_account):
        """Test creating a bill payment."""
        from apps.accounting.models import BillPayment

        payment = BillPayment.objects.create(
            bill=bill,
            date=date.today(),
            amount=Decimal('1160.00'),
            payment_method='transfer',
            bank_account=bank_account,
        )

        assert payment.amount == Decimal('1160.00')


class TestBudgetModel:
    """Tests for Budget model."""

    def test_create_budget(self, account):
        """Test creating a budget."""
        from apps.accounting.models import Budget

        budget = Budget.objects.create(
            account=account,
            year=2025,
            jan=Decimal('5000.00'),
            feb=Decimal('5000.00'),
        )

        assert budget.year == 2025
        assert budget.jan == Decimal('5000.00')


class TestAccountingAITools:
    """Tests for Accounting AI tools."""

    def test_get_chart_account_balance_tool_exists(self):
        """Test get_chart_account_balance tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('get_chart_account_balance')
        assert tool is not None

    def test_get_financial_summary_tool_exists(self):
        """Test get_financial_summary tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('get_financial_summary')
        assert tool is not None

    def test_record_expense_tool_exists(self):
        """Test record_expense tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('record_expense')
        assert tool is not None


# Fixtures
@pytest.fixture
def user():
    """Create a test user."""
    return User.objects.create_user(
        username='accountinguser',
        email='accounting@example.com',
        password='testpass123',
        first_name='Accounting',
        last_name='User',
    )


@pytest.fixture
def account():
    """Create a test account."""
    from apps.accounting.models import Account
    return Account.objects.create(
        code='1000',
        name='Cash',
        account_type='asset',
    )


@pytest.fixture
def bank_account():
    """Create a bank account."""
    from apps.accounting.models import Account
    return Account.objects.create(
        code='1010',
        name='Checking Account',
        account_type='asset',
        is_bank=True,
    )


@pytest.fixture
def journal_entry(user):
    """Create a journal entry."""
    from apps.accounting.models import JournalEntry
    return JournalEntry.objects.create(
        date=date.today(),
        reference='JE-TEST',
        description='Test entry',
        created_by=user,
    )


@pytest.fixture
def vendor():
    """Create a vendor."""
    from apps.accounting.models import Vendor
    return Vendor.objects.create(
        name='Test Vendor',
        email='vendor@example.com',
    )


@pytest.fixture
def bill(vendor):
    """Create a bill."""
    from apps.accounting.models import Bill
    return Bill.objects.create(
        vendor=vendor,
        bill_number='BILL-TEST',
        bill_date=date.today(),
        due_date=date.today(),
        subtotal=Decimal('1000.00'),
        tax=Decimal('160.00'),
        total=Decimal('1160.00'),
    )
