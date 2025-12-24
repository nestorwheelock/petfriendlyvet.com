"""Admin configuration for billing app.

Provides staff interface for:
- Viewing and managing invoices
- Recording payments (cash, card, transfer)
- Managing discounts and credits
"""
from decimal import Decimal

from django import forms
from django.contrib import admin, messages
from django.db.models import Sum
from django.shortcuts import redirect, get_object_or_404
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html

from .models import (
    Invoice, InvoiceLineItem, Payment,
    CustomerDiscount, CouponCode, AccountCredit,
    ProfessionalAccount, ExchangeRate
)
from .services import PaymentService


class PaymentRecordForm(forms.Form):
    """Form for recording a payment."""
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={'class': 'vTextField', 'step': '0.01'})
    )
    payment_method = forms.ChoiceField(
        choices=Payment.PAYMENT_METHODS,
        widget=forms.Select(attrs={'class': 'vTextField'})
    )
    reference_number = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'vTextField'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'vLargeTextField', 'rows': 3})
    )
    cash_discount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        initial=Decimal('0'),
        required=False,
        widget=forms.NumberInput(attrs={'class': 'vTextField', 'step': '0.01'})
    )


class InvoiceLineItemInline(admin.TabularInline):
    """Inline for invoice line items."""
    model = InvoiceLineItem
    extra = 0
    readonly_fields = ['line_total']
    fields = ['description', 'quantity', 'unit_price', 'discount_percent', 'line_total']


class PaymentInline(admin.TabularInline):
    """Inline for viewing payments (read-only)."""
    model = Payment
    extra = 0
    readonly_fields = [
        'amount', 'payment_method', 'reference_number',
        'recorded_by', 'created_at', 'notes'
    ]
    fields = readonly_fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """Admin for invoices with payment recording capability."""

    list_display = [
        'invoice_number', 'owner_name', 'status_badge', 'total_display',
        'amount_paid_display', 'balance_due_display', 'due_date', 'created_at',
        'payment_actions'
    ]
    list_filter = ['status', 'created_at', 'due_date']
    search_fields = ['invoice_number', 'owner__username', 'owner__email', 'owner__first_name', 'owner__last_name']
    readonly_fields = [
        'invoice_number', 'created_at', 'updated_at', 'sent_at', 'paid_at',
        'balance_due_display', 'payment_summary'
    ]
    date_hierarchy = 'created_at'
    inlines = [InvoiceLineItemInline, PaymentInline]

    fieldsets = (
        ('Invoice Info', {
            'fields': ('invoice_number', 'owner', 'pet', 'status', 'due_date')
        }),
        ('Related Records', {
            'fields': ('order', 'appointment'),
            'classes': ('collapse',)
        }),
        ('Amounts', {
            'fields': ('subtotal', 'discount_amount', 'tax_amount', 'total', 'amount_paid', 'balance_due_display')
        }),
        ('Payment Summary', {
            'fields': ('payment_summary',),
        }),
        ('Mexican Tax (CFDI)', {
            'fields': ('client_rfc', 'client_razon_social', 'uso_cfdi', 'regimen_fiscal', 'cfdi_uuid', 'cfdi_status'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'sent_at', 'paid_at'),
            'classes': ('collapse',)
        }),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:invoice_id>/record-payment/',
                self.admin_site.admin_view(self.record_payment_view),
                name='billing_invoice_record_payment'
            ),
            path(
                '<int:invoice_id>/mark-paid/',
                self.admin_site.admin_view(self.mark_paid_view),
                name='billing_invoice_mark_paid'
            ),
            path(
                '<int:invoice_id>/send/',
                self.admin_site.admin_view(self.send_invoice_view),
                name='billing_invoice_send'
            ),
        ]
        return custom_urls + urls

    def owner_name(self, obj):
        return obj.owner.get_full_name() or obj.owner.username
    owner_name.short_description = 'Customer'
    owner_name.admin_order_field = 'owner__first_name'

    def status_badge(self, obj):
        colors = {
            'draft': '#6c757d',
            'sent': '#17a2b8',
            'paid': '#28a745',
            'partial': '#ffc107',
            'overdue': '#dc3545',
            'cancelled': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'

    def total_display(self, obj):
        return f"${obj.total:,.2f}"
    total_display.short_description = 'Total'
    total_display.admin_order_field = 'total'

    def amount_paid_display(self, obj):
        return f"${obj.amount_paid:,.2f}"
    amount_paid_display.short_description = 'Paid'
    amount_paid_display.admin_order_field = 'amount_paid'

    def balance_due_display(self, obj):
        balance = obj.get_balance_due()
        if balance > 0:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">${:,.2f}</span>',
                balance
            )
        return format_html('<span style="color: #28a745;">$0.00</span>')
    balance_due_display.short_description = 'Balance Due'

    def payment_summary(self, obj):
        """Show summary of all payments."""
        payments = obj.payments.all()
        if not payments:
            return "No payments recorded"

        html = '<table style="width: 100%; border-collapse: collapse;">'
        html += '<tr style="background: #f5f5f5;"><th>Date</th><th>Method</th><th>Amount</th><th>By</th></tr>'
        for p in payments:
            html += f'<tr><td>{p.created_at.strftime("%Y-%m-%d %H:%M")}</td>'
            html += f'<td>{p.get_payment_method_display()}</td>'
            html += f'<td>${p.amount:,.2f}</td>'
            html += f'<td>{p.recorded_by.username if p.recorded_by else "-"}</td></tr>'
        html += '</table>'
        return format_html(html)
    payment_summary.short_description = 'Payments'

    def payment_actions(self, obj):
        """Action buttons for payments."""
        if obj.status in ['paid', 'cancelled']:
            return '-'

        balance = obj.get_balance_due()
        if balance <= 0:
            return '-'

        record_url = reverse('admin:billing_invoice_record_payment', args=[obj.id])
        mark_paid_url = reverse('admin:billing_invoice_mark_paid', args=[obj.id])

        return format_html(
            '<a class="button" href="{}" style="margin-right: 5px;">Record Payment</a>'
            '<a class="button" href="{}" style="background: #28a745; color: white;">Mark Paid</a>',
            record_url, mark_paid_url
        )
    payment_actions.short_description = 'Actions'

    def record_payment_view(self, request, invoice_id):
        """View for recording a payment against an invoice."""
        invoice = get_object_or_404(Invoice, pk=invoice_id)
        balance = invoice.get_balance_due()

        if request.method == 'POST':
            form = PaymentRecordForm(request.POST)
            if form.is_valid():
                amount = form.cleaned_data['amount']
                payment_method = form.cleaned_data['payment_method']
                reference_number = form.cleaned_data.get('reference_number', '')
                notes = form.cleaned_data.get('notes', '')
                cash_discount = form.cleaned_data.get('cash_discount') or Decimal('0')

                # Record the payment
                payment = PaymentService.record_payment(
                    invoice=invoice,
                    amount=amount,
                    payment_method=payment_method,
                    recorded_by=request.user,
                    reference_number=reference_number,
                    notes=notes,
                    cash_discount=cash_discount,
                )

                messages.success(
                    request,
                    f'Payment of ${amount:,.2f} recorded successfully. '
                    f'New balance: ${invoice.get_balance_due():,.2f}'
                )
                return redirect('admin:billing_invoice_change', invoice_id)
        else:
            form = PaymentRecordForm(initial={'amount': balance})

        context = {
            **self.admin_site.each_context(request),
            'title': f'Record Payment - {invoice.invoice_number}',
            'invoice': invoice,
            'form': form,
            'balance': balance,
            'opts': self.model._meta,
        }
        return TemplateResponse(request, 'admin/billing/invoice/record_payment.html', context)

    def mark_paid_view(self, request, invoice_id):
        """Quick action to mark invoice as fully paid with cash."""
        invoice = get_object_or_404(Invoice, pk=invoice_id)
        balance = invoice.get_balance_due()

        if balance > 0:
            PaymentService.record_payment(
                invoice=invoice,
                amount=balance,
                payment_method='cash',
                recorded_by=request.user,
                notes='Marked as paid via admin',
            )
            messages.success(request, f'Invoice {invoice.invoice_number} marked as paid.')
        else:
            messages.info(request, 'Invoice already fully paid.')

        return redirect('admin:billing_invoice_changelist')

    def send_invoice_view(self, request, invoice_id):
        """Mark invoice as sent."""
        invoice = get_object_or_404(Invoice, pk=invoice_id)
        if invoice.status == 'draft':
            invoice.status = 'sent'
            invoice.sent_at = timezone.now()
            invoice.save()
            messages.success(request, f'Invoice {invoice.invoice_number} marked as sent.')
        return redirect('admin:billing_invoice_change', invoice_id)

    actions = ['mark_as_sent', 'mark_as_overdue', 'export_invoices']

    @admin.action(description='Mark selected invoices as sent')
    def mark_as_sent(self, request, queryset):
        updated = queryset.filter(status='draft').update(
            status='sent',
            sent_at=timezone.now()
        )
        messages.success(request, f'{updated} invoice(s) marked as sent.')

    @admin.action(description='Mark overdue invoices')
    def mark_as_overdue(self, request, queryset):
        from datetime import date
        updated = queryset.filter(
            status__in=['sent', 'partial'],
            due_date__lt=date.today()
        ).update(status='overdue')
        messages.success(request, f'{updated} invoice(s) marked as overdue.')

    @admin.action(description='Export selected invoices')
    def export_invoices(self, request, queryset):
        # Placeholder for export functionality
        messages.info(request, f'Export of {queryset.count()} invoices would go here.')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin for viewing all payments."""

    list_display = [
        'id', 'invoice_link', 'customer_name', 'amount_display',
        'payment_method', 'reference_number', 'recorded_by', 'created_at'
    ]
    list_filter = ['payment_method', 'created_at']
    search_fields = [
        'invoice__invoice_number', 'reference_number',
        'invoice__owner__username', 'invoice__owner__email'
    ]
    readonly_fields = [
        'invoice', 'amount', 'payment_method', 'stripe_payment_intent',
        'stripe_charge_id', 'reference_number', 'notes', 'cash_discount_applied',
        'recorded_by', 'created_at'
    ]
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        # Payments should be added via Invoice admin
        return False

    def has_delete_permission(self, request, obj=None):
        # Payments should not be deleted (audit trail)
        return False

    def invoice_link(self, obj):
        url = reverse('admin:billing_invoice_change', args=[obj.invoice.id])
        return format_html('<a href="{}">{}</a>', url, obj.invoice.invoice_number)
    invoice_link.short_description = 'Invoice'

    def customer_name(self, obj):
        return obj.invoice.owner.get_full_name() or obj.invoice.owner.username
    customer_name.short_description = 'Customer'

    def amount_display(self, obj):
        return f"${obj.amount:,.2f}"
    amount_display.short_description = 'Amount'
    amount_display.admin_order_field = 'amount'


@admin.register(CustomerDiscount)
class CustomerDiscountAdmin(admin.ModelAdmin):
    """Admin for customer discount levels."""

    list_display = ['owner', 'discount_type', 'discount_percent', 'applies_to_products', 'applies_to_services']
    list_filter = ['discount_type', 'applies_to_products', 'applies_to_services']
    search_fields = ['owner__username', 'owner__email']


@admin.register(CouponCode)
class CouponCodeAdmin(admin.ModelAdmin):
    """Admin for coupon codes."""

    list_display = ['code', 'discount_type', 'discount_value', 'is_active', 'uses_display', 'valid_until']
    list_filter = ['is_active', 'discount_type', 'valid_until']
    search_fields = ['code', 'description']

    def uses_display(self, obj):
        if obj.max_uses:
            return f"{obj.times_used}/{obj.max_uses}"
        return f"{obj.times_used}/∞"
    uses_display.short_description = 'Uses'


@admin.register(AccountCredit)
class AccountCreditAdmin(admin.ModelAdmin):
    """Admin for customer account credits."""

    list_display = ['owner', 'balance', 'updated_at']
    search_fields = ['owner__username', 'owner__email']
    readonly_fields = ['updated_at']


@admin.register(ProfessionalAccount)
class ProfessionalAccountAdmin(admin.ModelAdmin):
    """Admin for B2B professional accounts."""

    list_display = ['business_name', 'email', 'credit_limit', 'current_balance', 'is_approved']
    list_filter = ['is_approved']
    search_fields = ['business_name', 'email', 'rfc']


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    """Admin for exchange rates."""

    list_display = ['date', 'usd_to_mxn', 'eur_to_mxn', 'fetched_at']
    list_filter = ['date']
