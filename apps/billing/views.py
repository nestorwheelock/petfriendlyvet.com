"""Views for billing and invoicing."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.views.generic import ListView, DetailView, TemplateView

from .models import Invoice, AccountCredit, CreditTransaction


class InvoiceListView(LoginRequiredMixin, ListView):
    """List invoices for the current user."""

    model = Invoice
    template_name = 'billing/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 20

    def get_queryset(self):
        """Return only invoices belonging to the current user."""
        return Invoice.objects.filter(
            owner=self.request.user
        ).order_by('-created_at')


class InvoiceDetailView(LoginRequiredMixin, DetailView):
    """Display invoice details."""

    model = Invoice
    template_name = 'billing/invoice_detail.html'
    context_object_name = 'invoice'

    def get_queryset(self):
        """Return only invoices belonging to the current user."""
        return Invoice.objects.filter(owner=self.request.user)

    def get_object(self, queryset=None):
        """Get the invoice or raise 404."""
        try:
            return super().get_object(queryset)
        except Invoice.DoesNotExist:
            raise Http404("Invoice not found")


class CreditBalanceView(LoginRequiredMixin, TemplateView):
    """Display account credit balance and history."""

    template_name = 'billing/credit_balance.html'

    def get_context_data(self, **kwargs):
        """Add credit balance and transactions to context."""
        context = super().get_context_data(**kwargs)

        try:
            credit = AccountCredit.objects.get(owner=self.request.user)
            context['credit'] = credit
            context['transactions'] = CreditTransaction.objects.filter(
                account=credit
            ).order_by('-created_at')[:20]
        except AccountCredit.DoesNotExist:
            context['credit'] = None
            context['transactions'] = []

        return context
