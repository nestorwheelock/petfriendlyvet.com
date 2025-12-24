"""Admin configuration for Accounting app."""
from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Account,
    JournalEntry,
    JournalLine,
    Vendor,
    Bill,
    BillLine,
    BillPayment,
    Budget,
    BankReconciliation,
)


class JournalLineInline(admin.TabularInline):
    model = JournalLine
    extra = 2
    fields = ['account', 'debit', 'credit', 'description']


class BillLineInline(admin.TabularInline):
    model = BillLine
    extra = 1
    fields = ['description', 'quantity', 'unit_price', 'amount', 'expense_account']


class BillPaymentInline(admin.TabularInline):
    model = BillPayment
    extra = 0
    fields = ['date', 'amount', 'payment_method', 'reference', 'bank_account']


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'name', 'type_badge', 'balance_display',
        'is_bank', 'is_ar', 'is_ap', 'is_active'
    ]
    list_filter = ['account_type', 'is_active', 'is_bank', 'is_ar', 'is_ap']
    search_fields = ['code', 'name']
    ordering = ['code']

    fieldsets = (
        (None, {
            'fields': ('code', 'name', 'account_type', 'parent', 'description')
        }),
        ('Account Flags', {
            'fields': ('is_bank', 'is_ar', 'is_ap', 'is_active')
        }),
        ('Balance', {
            'fields': ('balance',)
        }),
    )

    @admin.display(description='Type')
    def type_badge(self, obj):
        colors = {
            'asset': '#198754',
            'liability': '#dc3545',
            'equity': '#6f42c1',
            'revenue': '#0d6efd',
            'expense': '#fd7e14',
        }
        color = colors.get(obj.account_type, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_account_type_display()
        )

    @admin.display(description='Balance')
    def balance_display(self, obj):
        if obj.balance >= 0:
            return format_html(
                '<span style="color: #198754;">${:,.2f}</span>',
                obj.balance
            )
        return format_html(
            '<span style="color: #dc3545;">-${:,.2f}</span>',
            abs(obj.balance)
        )


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = [
        'reference', 'date', 'description_preview', 'total_debit',
        'posted_badge', 'created_by'
    ]
    list_filter = ['is_posted', 'date']
    search_fields = ['reference', 'description']
    raw_id_fields = ['created_by', 'posted_by']
    date_hierarchy = 'date'
    inlines = [JournalLineInline]

    @admin.display(description='Description')
    def description_preview(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description

    @admin.display(description='Posted')
    def posted_badge(self, obj):
        if obj.is_posted:
            return format_html(
                '<span style="color: #198754; font-weight: bold;">Posted</span>'
            )
        return format_html(
            '<span style="color: #ffc107;">Draft</span>'
        )


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'contact_name', 'email', 'phone',
        'payment_terms', 'balance_display', 'is_active'
    ]
    list_filter = ['is_active', 'payment_terms']
    search_fields = ['name', 'contact_name', 'email']

    fieldsets = (
        (None, {
            'fields': ('name', 'rfc', 'is_active')
        }),
        ('Contact', {
            'fields': ('contact_name', 'email', 'phone', 'address')
        }),
        ('Terms', {
            'fields': ('payment_terms', 'default_expense_account')
        }),
    )

    @admin.display(description='Balance')
    def balance_display(self, obj):
        if obj.balance == 0:
            return format_html('<span style="color: #6c757d;">$0.00</span>')
        return format_html(
            '<span style="color: #dc3545;">${:,.2f}</span>',
            obj.balance
        )


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = [
        'bill_number', 'vendor', 'bill_date', 'due_date',
        'total_display', 'status_badge'
    ]
    list_filter = ['status', 'bill_date', 'vendor']
    search_fields = ['bill_number', 'vendor__name']
    raw_id_fields = ['vendor']
    date_hierarchy = 'bill_date'
    inlines = [BillLineInline, BillPaymentInline]

    fieldsets = (
        (None, {
            'fields': ('vendor', 'bill_number', 'status')
        }),
        ('Dates', {
            'fields': ('bill_date', 'due_date')
        }),
        ('Amounts', {
            'fields': ('subtotal', 'tax', 'total', 'amount_paid')
        }),
        ('CFDI', {
            'fields': ('cfdi_uuid', 'cfdi_xml'),
            'classes': ['collapse']
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )

    @admin.display(description='Total')
    def total_display(self, obj):
        return format_html('${:,.2f}', obj.total)

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'draft': '#6c757d',
            'pending': '#ffc107',
            'partial': '#fd7e14',
            'paid': '#198754',
            'cancelled': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = [
        'account', 'year', 'jan', 'feb', 'mar',
        'annual_total_display'
    ]
    list_filter = ['year', 'account__account_type']
    search_fields = ['account__name', 'account__code']
    raw_id_fields = ['account']

    @admin.display(description='Annual Total')
    def annual_total_display(self, obj):
        return format_html('${:,.2f}', obj.annual_total)


@admin.register(BankReconciliation)
class BankReconciliationAdmin(admin.ModelAdmin):
    list_display = [
        'bank_account', 'statement_date', 'statement_balance',
        'difference', 'reconciled_badge'
    ]
    list_filter = ['is_reconciled', 'bank_account']
    date_hierarchy = 'statement_date'
    raw_id_fields = ['bank_account', 'reconciled_by']

    @admin.display(description='Reconciled')
    def reconciled_badge(self, obj):
        if obj.is_reconciled:
            return format_html(
                '<span style="color: #198754; font-weight: bold;">Yes</span>'
            )
        return format_html(
            '<span style="color: #ffc107;">Pending</span>'
        )
