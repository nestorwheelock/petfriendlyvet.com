"""Admin configuration for the store app."""
from django.contrib import admin

from .models import (
    Category, Product, ProductImage, Cart, CartItem,
    Order, OrderItem, StoreSettings
)


@admin.register(StoreSettings)
class StoreSettingsAdmin(admin.ModelAdmin):
    """Admin for store-wide settings (singleton)."""

    list_display = [
        'id',
        'default_shipping_cost',
        'free_shipping_threshold',
        'tax_rate',
        'default_max_order_quantity',
        'updated_at'
    ]
    readonly_fields = ['updated_at']

    fieldsets = (
        ('Shipping', {
            'fields': ('default_shipping_cost', 'free_shipping_threshold'),
            'description': 'Configure delivery shipping costs.'
        }),
        ('Tax', {
            'fields': ('tax_rate',),
            'description': 'Tax rate as decimal (e.g., 0.16 for 16% IVA).'
        }),
        ('Order Limits', {
            'fields': ('default_max_order_quantity',),
            'description': 'Default maximum quantity per product per order.'
        }),
        ('Metadata', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        """Prevent adding more than one settings instance."""
        return not StoreSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Prevent deleting the singleton settings."""
        return False


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin for product categories."""

    list_display = ['name', 'name_es', 'slug', 'parent', 'is_active', 'order']
    list_filter = ['is_active', 'parent']
    search_fields = ['name', 'name_es', 'name_en', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']


class ProductImageInline(admin.TabularInline):
    """Inline for product images."""

    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'is_primary', 'order']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin for products."""

    list_display = [
        'name', 'sku', 'category', 'price', 'stock_quantity',
        'is_active', 'is_featured'
    ]
    list_filter = ['is_active', 'is_featured', 'category', 'track_inventory']
    search_fields = ['name', 'name_es', 'name_en', 'sku', 'barcode']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]
    ordering = ['-created_at']

    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'name_es', 'name_en', 'slug', 'category')
        }),
        ('Description', {
            'fields': ('description', 'description_es', 'description_en'),
            'classes': ('collapse',)
        }),
        ('Pricing', {
            'fields': ('price', 'compare_at_price')
        }),
        ('Identification', {
            'fields': ('sku', 'barcode')
        }),
        ('Inventory', {
            'fields': (
                'stock_quantity', 'low_stock_threshold',
                'track_inventory', 'max_order_quantity'
            )
        }),
        ('Physical', {
            'fields': ('weight_kg',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured')
        }),
        ('Pet Filters', {
            'fields': (
                'suitable_for_species', 'suitable_for_sizes', 'suitable_for_ages'
            ),
            'classes': ('collapse',)
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
    )


class CartItemInline(admin.TabularInline):
    """Inline for cart items."""

    model = CartItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'subtotal']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Admin for shopping carts."""

    list_display = ['id', 'user', 'session_key', 'item_count', 'total', 'updated_at']
    list_filter = ['updated_at']
    search_fields = ['user__username', 'user__email', 'session_key']
    inlines = [CartItemInline]
    readonly_fields = ['total', 'item_count']


class OrderItemInline(admin.TabularInline):
    """Inline for order items."""

    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'product_name', 'price', 'quantity', 'subtotal']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin for orders."""

    list_display = [
        'order_number', 'user', 'status', 'fulfillment_method',
        'payment_method', 'total', 'created_at'
    ]
    list_filter = ['status', 'fulfillment_method', 'payment_method', 'created_at']
    search_fields = ['order_number', 'user__username', 'user__email', 'shipping_name']
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline]
    readonly_fields = [
        'order_number', 'subtotal', 'discount_amount',
        'shipping_cost', 'tax', 'total', 'created_at', 'updated_at'
    ]

    fieldsets = (
        ('Order Info', {
            'fields': ('order_number', 'user', 'status')
        }),
        ('Fulfillment', {
            'fields': ('fulfillment_method', 'payment_method')
        }),
        ('Shipping', {
            'fields': ('shipping_name', 'shipping_address', 'shipping_phone'),
            'classes': ('collapse',)
        }),
        ('Totals', {
            'fields': (
                'subtotal', 'discount_amount', 'shipping_cost', 'tax', 'total'
            )
        }),
        ('Payment', {
            'fields': ('stripe_payment_intent_id', 'stripe_charge_id', 'paid_at'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes', 'internal_notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
