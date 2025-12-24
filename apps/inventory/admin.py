from django.contrib import admin
from django.utils.html import format_html

from .models import (
    StockLocation,
    StockLevel,
    StockBatch,
    StockMovement,
    Supplier,
    ProductSupplier,
    ReorderRule,
    PurchaseOrder,
    PurchaseOrderLine,
    StockCount,
    StockCountLine,
    ControlledSubstanceLog,
)


@admin.register(StockLocation)
class StockLocationAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'location_type', 'is_active',
        'requires_temperature_control', 'requires_restricted_access'
    ]
    list_filter = ['location_type', 'is_active', 'requires_temperature_control', 'requires_restricted_access']
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(StockLevel)
class StockLevelAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'location', 'quantity', 'reserved_quantity',
        'available_display', 'min_level', 'status_display'
    ]
    list_filter = ['location']
    search_fields = ['product__name', 'location__name']
    raw_id_fields = ['product']
    ordering = ['product__name', 'location__name']

    @admin.display(description='Available')
    def available_display(self, obj):
        return obj.available_quantity

    @admin.display(description='Status')
    def status_display(self, obj):
        if obj.is_below_minimum:
            return format_html('<span style="color: red;">Low Stock</span>')
        return format_html('<span style="color: green;">OK</span>')


@admin.register(StockBatch)
class StockBatchAdmin(admin.ModelAdmin):
    list_display = [
        'batch_number', 'product', 'location', 'current_quantity',
        'expiry_date', 'days_until_expiry_display', 'status'
    ]
    list_filter = ['status', 'location', 'supplier']
    search_fields = ['batch_number', 'lot_number', 'product__name']
    raw_id_fields = ['product', 'supplier']
    date_hierarchy = 'expiry_date'
    ordering = ['expiry_date']

    @admin.display(description='Days Until Expiry')
    def days_until_expiry_display(self, obj):
        days = obj.days_until_expiry
        if days is None:
            return '-'
        if days < 0:
            return format_html('<span style="color: red;">Expired ({} days)</span>', abs(days))
        if days <= 30:
            return format_html('<span style="color: orange;">{} days</span>', days)
        return f'{days} days'


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'product', 'movement_type', 'quantity', 'from_location',
        'to_location', 'recorded_by', 'created_at'
    ]
    list_filter = ['movement_type', 'from_location', 'to_location', 'created_at']
    search_fields = ['product__name', 'reason']
    raw_id_fields = ['product', 'batch', 'recorded_by', 'authorized_by']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    readonly_fields = ['created_at']


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'contact_name', 'email', 'phone',
        'payment_terms', 'lead_time_days', 'is_active'
    ]
    list_filter = ['is_active', 'payment_terms']
    search_fields = ['name', 'contact_name', 'email']
    ordering = ['name']


@admin.register(ProductSupplier)
class ProductSupplierAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'supplier', 'supplier_sku', 'unit_cost',
        'minimum_order_quantity', 'is_preferred'
    ]
    list_filter = ['is_preferred', 'supplier']
    search_fields = ['product__name', 'supplier__name', 'supplier_sku']
    raw_id_fields = ['product', 'supplier']
    ordering = ['product__name', 'supplier__name']


@admin.register(ReorderRule)
class ReorderRuleAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'location', 'min_level', 'reorder_point',
        'reorder_quantity', 'preferred_supplier', 'is_active'
    ]
    list_filter = ['is_active', 'location']
    search_fields = ['product__name', 'location__name']
    raw_id_fields = ['product', 'preferred_supplier']
    ordering = ['product__name']


class PurchaseOrderLineInline(admin.TabularInline):
    model = PurchaseOrderLine
    extra = 1
    raw_id_fields = ['product']


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = [
        'po_number', 'supplier', 'status', 'order_date',
        'expected_date', 'total', 'created_by'
    ]
    list_filter = ['status', 'supplier', 'order_date']
    search_fields = ['po_number', 'supplier__name']
    date_hierarchy = 'order_date'
    ordering = ['-order_date']
    inlines = [PurchaseOrderLineInline]
    raw_id_fields = ['supplier', 'delivery_location', 'created_by', 'approved_by']


@admin.register(PurchaseOrderLine)
class PurchaseOrderLineAdmin(admin.ModelAdmin):
    list_display = [
        'purchase_order', 'product', 'quantity_ordered',
        'quantity_received', 'unit_cost', 'line_total'
    ]
    list_filter = ['purchase_order__status']
    search_fields = ['product__name', 'purchase_order__po_number']
    raw_id_fields = ['purchase_order', 'product']


class StockCountLineInline(admin.TabularInline):
    model = StockCountLine
    extra = 0
    raw_id_fields = ['product', 'batch']
    readonly_fields = ['discrepancy', 'discrepancy_value']


@admin.register(StockCount)
class StockCountAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'location', 'count_type', 'status', 'count_date', 'counted_by'
    ]
    list_filter = ['status', 'count_type', 'location']
    search_fields = ['location__name']
    date_hierarchy = 'count_date'
    ordering = ['-count_date']
    inlines = [StockCountLineInline]
    raw_id_fields = ['location', 'counted_by', 'approved_by']


@admin.register(StockCountLine)
class StockCountLineAdmin(admin.ModelAdmin):
    list_display = [
        'stock_count', 'product', 'batch', 'system_quantity',
        'counted_quantity', 'discrepancy', 'discrepancy_value'
    ]
    list_filter = ['stock_count__location']
    search_fields = ['product__name', 'batch__batch_number']
    raw_id_fields = ['stock_count', 'product', 'batch']


@admin.register(ControlledSubstanceLog)
class ControlledSubstanceLogAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'product', 'log_type', 'quantity', 'balance_after',
        'pet', 'recorded_by', 'created_at'
    ]
    list_filter = ['log_type', 'product']
    search_fields = ['product__name', 'pet__name', 'notes']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    raw_id_fields = [
        'product', 'batch', 'pet', 'owner', 'prescription',
        'recorded_by', 'waste_witnessed_by'
    ]
    readonly_fields = ['created_at']
