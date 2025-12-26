"""Views for accounting functionality."""
from decimal import Decimal

from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Sum
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
)

from .models import (
    Account, JournalEntry, JournalLine, Vendor, Bill,
    Budget, BankReconciliation
)


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin requiring user to be staff."""

    def test_func(self):
        return self.request.user.is_staff


class AccountingDashboardView(StaffRequiredMixin, TemplateView):
    """Accounting dashboard with financial overview."""

    template_name = 'accounting/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Account summaries by type
        context['total_assets'] = Account.objects.filter(
            account_type='asset', is_active=True
        ).aggregate(total=Sum('balance'))['total'] or Decimal('0.00')

        context['total_liabilities'] = Account.objects.filter(
            account_type='liability', is_active=True
        ).aggregate(total=Sum('balance'))['total'] or Decimal('0.00')

        context['total_revenue'] = Account.objects.filter(
            account_type='revenue', is_active=True
        ).aggregate(total=Sum('balance'))['total'] or Decimal('0.00')

        context['total_expenses'] = Account.objects.filter(
            account_type='expense', is_active=True
        ).aggregate(total=Sum('balance'))['total'] or Decimal('0.00')

        # Recent journal entries
        context['recent_journals'] = JournalEntry.objects.select_related(
            'created_by'
        ).prefetch_related('lines__account').order_by('-date', '-created_at')[:10]

        # Pending bills
        context['pending_bills'] = Bill.objects.filter(
            status__in=['pending', 'partial']
        ).select_related('vendor').order_by('due_date')[:5]

        return context


class AccountListView(StaffRequiredMixin, ListView):
    """Chart of accounts listing."""

    model = Account
    template_name = 'accounting/account_list.html'
    context_object_name = 'accounts'

    def get_queryset(self):
        return Account.objects.filter(is_active=True).order_by('code')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Group accounts by type
        context['accounts_by_type'] = {
            'asset': Account.objects.filter(account_type='asset', is_active=True).order_by('code'),
            'liability': Account.objects.filter(account_type='liability', is_active=True).order_by('code'),
            'equity': Account.objects.filter(account_type='equity', is_active=True).order_by('code'),
            'revenue': Account.objects.filter(account_type='revenue', is_active=True).order_by('code'),
            'expense': Account.objects.filter(account_type='expense', is_active=True).order_by('code'),
        }

        # Also provide individual context variables for template flexibility
        context['asset_accounts'] = context['accounts_by_type']['asset']
        context['liability_accounts'] = context['accounts_by_type']['liability']
        context['equity_accounts'] = context['accounts_by_type']['equity']
        context['revenue_accounts'] = context['accounts_by_type']['revenue']
        context['expense_accounts'] = context['accounts_by_type']['expense']

        return context


class AccountDetailView(StaffRequiredMixin, DetailView):
    """Account detail with transaction history."""

    model = Account
    template_name = 'accounting/account_detail.html'
    context_object_name = 'account'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Recent transactions for this account
        context['transactions'] = JournalLine.objects.filter(
            account=self.object,
            entry__is_posted=True
        ).select_related('entry').order_by('-entry__date', '-entry__created_at')[:50]

        return context


class AccountForm(forms.ModelForm):
    """Form for creating/editing accounts."""

    class Meta:
        model = Account
        fields = ['code', 'name', 'account_type', 'parent', 'description', 'is_bank', 'is_ar', 'is_ap', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-primary-500 focus:border-primary-500',
                'placeholder': '1000'
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-primary-500 focus:border-primary-500',
                'placeholder': 'Account Name'
            }),
            'account_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-primary-500 focus:border-primary-500'
            }),
            'parent': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-primary-500 focus:border-primary-500'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-primary-500 focus:border-primary-500',
                'rows': 3,
                'placeholder': 'Optional description...'
            }),
            'is_bank': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500'
            }),
            'is_ar': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500'
            }),
            'is_ap': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent'].queryset = Account.objects.filter(is_active=True).order_by('code')
        self.fields['parent'].empty_label = _('-- No parent (top level) --')


class AccountCreateView(StaffRequiredMixin, CreateView):
    """Create a new account in the chart of accounts."""

    model = Account
    form_class = AccountForm
    template_name = 'accounting/account_form.html'
    success_url = reverse_lazy('accounting:account_list')

    def form_valid(self, form):
        messages.success(self.request, _('Account "%(name)s" created successfully.') % {'name': form.instance.name})
        return super().form_valid(form)


class AccountUpdateView(StaffRequiredMixin, UpdateView):
    """Update an existing account."""

    model = Account
    form_class = AccountForm
    template_name = 'accounting/account_form.html'

    def get_success_url(self):
        return reverse_lazy('accounting:account_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, _('Account "%(name)s" updated successfully.') % {'name': form.instance.name})
        return super().form_valid(form)


class AccountDeleteView(StaffRequiredMixin, DeleteView):
    """Delete an account (soft delete by deactivating)."""

    model = Account
    template_name = 'accounting/account_confirm_delete.html'
    success_url = reverse_lazy('accounting:account_list')
    context_object_name = 'account'

    def form_valid(self, form):
        from django.http import HttpResponseRedirect
        self.object = self.get_object()
        self.object.is_active = False
        self.object.save(update_fields=['is_active', 'updated_at'])
        messages.success(self.request, _('Account "%(name)s" has been deactivated.') % {'name': self.object.name})
        return HttpResponseRedirect(self.get_success_url())


class JournalListView(StaffRequiredMixin, ListView):
    """List of journal entries."""

    model = JournalEntry
    template_name = 'accounting/journal_list.html'
    context_object_name = 'journals'
    paginate_by = 25

    def get_queryset(self):
        queryset = JournalEntry.objects.select_related(
            'created_by'
        ).prefetch_related('lines__account')

        # Filter by posted status
        status = self.request.GET.get('status')
        if status == 'posted':
            queryset = queryset.filter(is_posted=True)
        elif status == 'draft':
            queryset = queryset.filter(is_posted=False)

        return queryset.order_by('-date', '-created_at')


class JournalDetailView(StaffRequiredMixin, DetailView):
    """Journal entry detail with lines."""

    model = JournalEntry
    template_name = 'accounting/journal_detail.html'
    context_object_name = 'journal'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get all lines for this entry
        context['lines'] = self.object.lines.select_related('account').all()

        return context


class VendorListView(StaffRequiredMixin, ListView):
    """List of vendors."""

    model = Vendor
    template_name = 'accounting/vendor_list.html'
    context_object_name = 'vendors'
    paginate_by = 25

    def get_queryset(self):
        return Vendor.objects.filter(is_active=True).order_by('name')


class VendorDetailView(StaffRequiredMixin, DetailView):
    """Vendor detail with bills."""

    model = Vendor
    template_name = 'accounting/vendor_detail.html'
    context_object_name = 'vendor'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get bills for this vendor
        context['bills'] = self.object.bills.order_by('-bill_date')[:20]

        return context


class BillListView(StaffRequiredMixin, ListView):
    """List of bills."""

    model = Bill
    template_name = 'accounting/bill_list.html'
    context_object_name = 'bills'
    paginate_by = 25

    def get_queryset(self):
        queryset = Bill.objects.select_related('vendor')

        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('-bill_date')


class BillDetailView(StaffRequiredMixin, DetailView):
    """Bill detail with line items and payments."""

    model = Bill
    template_name = 'accounting/bill_detail.html'
    context_object_name = 'bill'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get line items
        context['lines'] = self.object.lines.select_related('expense_account').all()

        # Get payments
        context['payments'] = self.object.payments.select_related('bank_account').order_by('-date')

        return context


class BudgetListView(StaffRequiredMixin, ListView):
    """List of budgets."""

    model = Budget
    template_name = 'accounting/budget_list.html'
    context_object_name = 'budgets'
    paginate_by = 25

    def get_queryset(self):
        queryset = Budget.objects.select_related('account')

        # Filter by year
        year = self.request.GET.get('year')
        if year:
            queryset = queryset.filter(year=year)

        return queryset.order_by('-year', 'account__code')


class ReconciliationListView(StaffRequiredMixin, ListView):
    """List of bank reconciliations."""

    model = BankReconciliation
    template_name = 'accounting/reconciliation_list.html'
    context_object_name = 'reconciliations'
    paginate_by = 25

    def get_queryset(self):
        return BankReconciliation.objects.select_related(
            'bank_account', 'reconciled_by'
        ).order_by('-statement_date')


class ReconciliationDetailView(StaffRequiredMixin, DetailView):
    """Bank reconciliation detail."""

    model = BankReconciliation
    template_name = 'accounting/reconciliation_detail.html'
    context_object_name = 'reconciliation'
