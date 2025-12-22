# T-065: Accounting Dashboard & Views

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Full Stack Developer
**Objective**: Implement accounting dashboard and financial management interface
**Related Story**: S-026
**Epoch**: 6
**Estimate**: 5 hours

### Constraints
**Allowed File Paths**: apps/accounting/, templates/admin/accounting/
**Forbidden Paths**: None

### Deliverables
- [ ] Accounting dashboard
- [ ] Chart of accounts view
- [ ] Journal entry interface
- [ ] AP management
- [ ] Bank reconciliation UI
- [ ] Financial statements

### Wireframe Reference
See: `planning/wireframes/22-accounting-dashboard.txt`

### Implementation Details

#### Views
```python
from django.views.generic import (
    TemplateView, ListView, DetailView, CreateView, UpdateView
)
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import timedelta


class AccountingDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Main accounting dashboard."""

    template_name = 'admin/accounting/dashboard.html'
    permission_required = 'accounting.view_account'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Cash position
        cash_accounts = Account.objects.filter(
            Q(is_bank=True) | Q(is_cash=True),
            is_active=True
        )
        context['cash_balance'] = sum(a.balance for a in cash_accounts)

        # Accounts Receivable
        ar_account = Account.objects.filter(is_ar=True).first()
        context['ar_balance'] = ar_account.balance if ar_account else 0

        # Accounts Payable
        ap_account = Account.objects.filter(is_ap=True).first()
        context['ap_balance'] = ap_account.balance if ap_account else 0

        # Bills due soon
        context['bills_due'] = Bill.objects.filter(
            status__in=['pending', 'partial'],
            due_date__lte=timezone.now().date() + timedelta(days=7)
        ).order_by('due_date')[:5]

        # Overdue invoices
        from apps.billing.models import Invoice
        context['overdue_invoices'] = Invoice.objects.filter(
            status='overdue'
        ).order_by('due_date')[:5]

        # Recent journal entries
        context['recent_entries'] = JournalEntry.objects.filter(
            is_posted=True
        ).order_by('-date', '-created_at')[:10]

        # This month P&L summary
        today = timezone.now().date()
        month_start = today.replace(day=1)

        service = AccountingService()
        pl = service.get_income_statement(month_start, today)
        context['month_revenue'] = pl['total_revenue']
        context['month_expenses'] = pl['total_expenses']
        context['month_net_income'] = pl['net_income']

        return context


class ChartOfAccountsView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Chart of accounts listing."""

    model = Account
    template_name = 'admin/accounting/chart_of_accounts.html'
    context_object_name = 'accounts'
    permission_required = 'accounting.view_account'

    def get_queryset(self):
        return Account.objects.filter(
            parent__isnull=True,  # Top-level only
            is_active=True
        ).prefetch_related('children').order_by('code')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Group by type
        context['asset_accounts'] = Account.objects.filter(
            account_type='asset', is_active=True
        ).order_by('code')
        context['liability_accounts'] = Account.objects.filter(
            account_type='liability', is_active=True
        ).order_by('code')
        context['equity_accounts'] = Account.objects.filter(
            account_type='equity', is_active=True
        ).order_by('code')
        context['revenue_accounts'] = Account.objects.filter(
            account_type='revenue', is_active=True
        ).order_by('code')
        context['expense_accounts'] = Account.objects.filter(
            account_type='expense', is_active=True
        ).order_by('code')

        return context


class AccountDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Account detail with transaction history."""

    model = Account
    template_name = 'admin/accounting/account_detail.html'
    context_object_name = 'account'
    permission_required = 'accounting.view_account'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Recent transactions
        context['transactions'] = self.object.journal_lines.filter(
            entry__is_posted=True
        ).select_related('entry').order_by('-entry__date', '-entry__created_at')[:50]

        # Running balance
        transactions = context['transactions']
        balance = self.object.balance
        for txn in transactions:
            txn.running_balance = balance
            if self.object.normal_balance == 'debit':
                balance -= txn.debit - txn.credit
            else:
                balance -= txn.credit - txn.debit

        return context


class JournalEntryListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """List of journal entries."""

    model = JournalEntry
    template_name = 'admin/accounting/journal_entries.html'
    context_object_name = 'entries'
    permission_required = 'accounting.view_journalentry'
    paginate_by = 25

    def get_queryset(self):
        queryset = JournalEntry.objects.prefetch_related('lines__account')

        # Filter by status
        status = self.request.GET.get('status')
        if status == 'posted':
            queryset = queryset.filter(is_posted=True)
        elif status == 'draft':
            queryset = queryset.filter(is_posted=False)

        # Date range
        start = self.request.GET.get('start')
        end = self.request.GET.get('end')
        if start:
            queryset = queryset.filter(date__gte=start)
        if end:
            queryset = queryset.filter(date__lte=end)

        return queryset.order_by('-date', '-created_at')


class JournalEntryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create manual journal entry."""

    model = JournalEntry
    template_name = 'admin/accounting/journal_entry_form.html'
    permission_required = 'accounting.add_journalentry'
    fields = ['date', 'description']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['accounts'] = Account.objects.filter(is_active=True).order_by('code')
        return context

    def form_valid(self, form):
        form.instance.entry_number = AccountingService()._next_entry_number()
        form.instance.entry_type = 'manual'
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class JournalEntryDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Journal entry detail."""

    model = JournalEntry
    template_name = 'admin/accounting/journal_entry_detail.html'
    context_object_name = 'entry'
    permission_required = 'accounting.view_journalentry'

    def post(self, request, *args, **kwargs):
        """Handle post action."""
        entry = self.get_object()
        if 'post' in request.POST:
            try:
                entry.post(request.user)
                messages.success(request, "Entrada contable registrada correctamente.")
            except ValueError as e:
                messages.error(request, str(e))
        return redirect(entry)


class BillListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """List of vendor bills."""

    model = Bill
    template_name = 'admin/accounting/bills.html'
    context_object_name = 'bills'
    permission_required = 'accounting.view_bill'
    paginate_by = 25

    def get_queryset(self):
        queryset = Bill.objects.select_related('vendor')

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        vendor = self.request.GET.get('vendor')
        if vendor:
            queryset = queryset.filter(vendor_id=vendor)

        return queryset.order_by('-bill_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vendors'] = Vendor.objects.filter(is_active=True)

        # Summary stats
        pending = Bill.objects.filter(status__in=['pending', 'partial'])
        context['total_pending'] = pending.aggregate(
            total=Sum('total') - Sum('amount_paid')
        )['total'] or 0
        context['overdue_count'] = pending.filter(
            due_date__lt=timezone.now().date()
        ).count()

        return context


class BillCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create vendor bill."""

    model = Bill
    template_name = 'admin/accounting/bill_form.html'
    permission_required = 'accounting.add_bill'
    fields = ['vendor', 'bill_number', 'bill_date', 'due_date', 'notes']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vendors'] = Vendor.objects.filter(is_active=True)
        context['expense_accounts'] = Account.objects.filter(
            account_type='expense', is_active=True
        )
        return context


class BillDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Bill detail with payment form."""

    model = Bill
    template_name = 'admin/accounting/bill_detail.html'
    context_object_name = 'bill'
    permission_required = 'accounting.view_bill'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['payments'] = self.object.payments.order_by('-date')
        context['bank_accounts'] = Account.objects.filter(
            Q(is_bank=True) | Q(is_cash=True),
            is_active=True
        )
        return context


class BankReconciliationView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Bank reconciliation interface."""

    template_name = 'admin/accounting/bank_reconciliation.html'
    permission_required = 'accounting.add_bankreconciliation'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        account_id = self.request.GET.get('account')
        if account_id:
            account = Account.objects.get(id=account_id)
            context['account'] = account

            # Uncleared transactions
            context['uncleared'] = JournalLine.objects.filter(
                account=account,
                entry__is_posted=True
            ).exclude(
                id__in=ReconciliationLine.objects.filter(
                    is_cleared=True
                ).values_list('journal_line_id', flat=True)
            ).select_related('entry').order_by('entry__date')

            # Book balance
            context['book_balance'] = account.balance

        context['bank_accounts'] = Account.objects.filter(
            is_bank=True, is_active=True
        )

        return context


class TrialBalanceView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Trial balance report."""

    template_name = 'admin/accounting/trial_balance.html'
    permission_required = 'accounting.view_account'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        as_of = self.request.GET.get('as_of', timezone.now().date())
        if isinstance(as_of, str):
            from datetime import datetime
            as_of = datetime.strptime(as_of, '%Y-%m-%d').date()

        service = AccountingService()
        trial_balance = service.get_trial_balance(as_of)

        context['as_of_date'] = as_of
        context['accounts'] = trial_balance['accounts']
        context['total_debit'] = trial_balance['total_debit']
        context['total_credit'] = trial_balance['total_credit']
        context['is_balanced'] = trial_balance['is_balanced']

        return context


class IncomeStatementView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Income statement report."""

    template_name = 'admin/accounting/income_statement.html'
    permission_required = 'accounting.view_account'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        today = timezone.now().date()
        start = self.request.GET.get('start', today.replace(day=1))
        end = self.request.GET.get('end', today)

        if isinstance(start, str):
            from datetime import datetime
            start = datetime.strptime(start, '%Y-%m-%d').date()
            end = datetime.strptime(end, '%Y-%m-%d').date()

        service = AccountingService()
        statement = service.get_income_statement(start, end)

        context.update(statement)

        return context


class BalanceSheetView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Balance sheet report."""

    template_name = 'admin/accounting/balance_sheet.html'
    permission_required = 'accounting.view_account'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        as_of = self.request.GET.get('as_of', timezone.now().date())

        # Assets
        context['assets'] = Account.objects.filter(
            account_type='asset', is_active=True, balance__ne=0
        ).order_by('code')
        context['total_assets'] = sum(a.balance for a in context['assets'])

        # Liabilities
        context['liabilities'] = Account.objects.filter(
            account_type='liability', is_active=True, balance__ne=0
        ).order_by('code')
        context['total_liabilities'] = sum(a.balance for a in context['liabilities'])

        # Equity
        context['equity'] = Account.objects.filter(
            account_type='equity', is_active=True, balance__ne=0
        ).order_by('code')
        context['total_equity'] = sum(a.balance for a in context['equity'])

        # Retained earnings (current year net income)
        # Simplified - in production would calculate from beginning of fiscal year
        service = AccountingService()
        today = timezone.now().date()
        year_start = today.replace(month=1, day=1)
        pl = service.get_income_statement(year_start, as_of)
        context['retained_earnings'] = pl['net_income']

        context['total_liabilities_equity'] = (
            context['total_liabilities'] +
            context['total_equity'] +
            context['retained_earnings']
        )

        context['as_of_date'] = as_of

        return context
```

#### Dashboard Template
```html
{% extends "admin/base.html" %}
{% load i18n humanize %}

{% block content %}
<div class="container mx-auto px-4 py-8">
    <h1 class="text-2xl font-bold mb-6">{% trans 'Contabilidad' %}</h1>

    <!-- Key Metrics -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg shadow p-6">
            <p class="text-gray-600 text-sm">{% trans 'Efectivo Disponible' %}</p>
            <p class="text-3xl font-bold text-green-600">
                ${{ cash_balance|floatformat:2|intcomma }}
            </p>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
            <p class="text-gray-600 text-sm">{% trans 'Cuentas por Cobrar' %}</p>
            <p class="text-3xl font-bold text-blue-600">
                ${{ ar_balance|floatformat:2|intcomma }}
            </p>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
            <p class="text-gray-600 text-sm">{% trans 'Cuentas por Pagar' %}</p>
            <p class="text-3xl font-bold text-red-600">
                ${{ ap_balance|floatformat:2|intcomma }}
            </p>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
            <p class="text-gray-600 text-sm">{% trans 'Utilidad del Mes' %}</p>
            <p class="text-3xl font-bold {% if month_net_income >= 0 %}text-green-600{% else %}text-red-600{% endif %}">
                ${{ month_net_income|floatformat:2|intcomma }}
            </p>
        </div>
    </div>

    <!-- Quick Actions -->
    <div class="flex flex-wrap gap-4 mb-8">
        <a href="{% url 'accounting:journal_entry_create' %}"
           class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
            {% trans 'Nueva Entrada' %}
        </a>
        <a href="{% url 'accounting:bill_create' %}"
           class="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700">
            {% trans 'Registrar Factura' %}
        </a>
        <a href="{% url 'accounting:reconciliation' %}"
           class="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700">
            {% trans 'Conciliación' %}
        </a>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <!-- Bills Due -->
        <div class="bg-white rounded-lg shadow">
            <div class="p-4 border-b flex justify-between">
                <h2 class="font-semibold">{% trans 'Facturas por Pagar' %}</h2>
                <a href="{% url 'accounting:bills' %}" class="text-blue-600 text-sm">
                    {% trans 'Ver todas' %}
                </a>
            </div>
            <div class="p-4">
                {% for bill in bills_due %}
                <div class="flex justify-between items-center py-2 border-b last:border-0">
                    <div>
                        <p class="font-medium">{{ bill.vendor.name }}</p>
                        <p class="text-sm text-gray-600">{{ bill.bill_number }}</p>
                    </div>
                    <div class="text-right">
                        <p class="font-medium">${{ bill.amount_due|floatformat:2|intcomma }}</p>
                        <p class="text-sm {% if bill.due_date < today %}text-red-600{% else %}text-gray-500{% endif %}">
                            {{ bill.due_date|date:"d M" }}
                        </p>
                    </div>
                </div>
                {% empty %}
                <p class="text-gray-500">{% trans 'No hay facturas pendientes' %}</p>
                {% endfor %}
            </div>
        </div>

        <!-- Recent Entries -->
        <div class="bg-white rounded-lg shadow">
            <div class="p-4 border-b flex justify-between">
                <h2 class="font-semibold">{% trans 'Entradas Recientes' %}</h2>
                <a href="{% url 'accounting:journal_entries' %}" class="text-blue-600 text-sm">
                    {% trans 'Ver todas' %}
                </a>
            </div>
            <div class="p-4">
                {% for entry in recent_entries %}
                <div class="flex justify-between items-center py-2 border-b last:border-0">
                    <div>
                        <p class="font-medium">{{ entry.entry_number }}</p>
                        <p class="text-sm text-gray-600">{{ entry.description|truncatechars:40 }}</p>
                    </div>
                    <span class="text-sm text-gray-500">{{ entry.date|date:"d M" }}</span>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>

    <!-- Reports Links -->
    <div class="mt-8 bg-white rounded-lg shadow p-6">
        <h2 class="font-semibold mb-4">{% trans 'Reportes Financieros' %}</h2>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <a href="{% url 'accounting:trial_balance' %}"
               class="block p-4 border rounded hover:bg-gray-50 text-center">
                <span class="text-2xl">📊</span>
                <p class="mt-2">{% trans 'Balanza de Comprobación' %}</p>
            </a>
            <a href="{% url 'accounting:income_statement' %}"
               class="block p-4 border rounded hover:bg-gray-50 text-center">
                <span class="text-2xl">📈</span>
                <p class="mt-2">{% trans 'Estado de Resultados' %}</p>
            </a>
            <a href="{% url 'accounting:balance_sheet' %}"
               class="block p-4 border rounded hover:bg-gray-50 text-center">
                <span class="text-2xl">📑</span>
                <p class="mt-2">{% trans 'Balance General' %}</p>
            </a>
            <a href="{% url 'accounting:chart_of_accounts' %}"
               class="block p-4 border rounded hover:bg-gray-50 text-center">
                <span class="text-2xl">📋</span>
                <p class="mt-2">{% trans 'Catálogo de Cuentas' %}</p>
            </a>
        </div>
    </div>
</div>
{% endblock %}
```

### Test Cases
- [ ] Dashboard loads with correct data
- [ ] Chart of accounts displays hierarchy
- [ ] Journal entry creation works
- [ ] Journal entry posting works
- [ ] Bill creation and payment works
- [ ] Bank reconciliation functions
- [ ] Trial balance balances
- [ ] Income statement accurate
- [ ] Balance sheet accurate

### Definition of Done
- [ ] All views implemented
- [ ] Dashboard responsive
- [ ] Reports export to PDF
- [ ] HTMX interactions smooth
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-064: Accounting Models
- T-002: Base Templates
