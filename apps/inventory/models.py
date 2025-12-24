"""Inventory management models for S-024.

Provides:
- StockLocation: Physical storage locations
- StockLevel: Current stock levels per product/location
- StockBatch: Batch/lot tracking with expiry dates
- StockMovement: Stock movement audit trail
- Supplier: Product suppliers
- ProductSupplier: Product-supplier relationships
- ReorderRule: Automatic reorder rules
- PurchaseOrder/PurchaseOrderLine: Purchase orders
- StockCount/StockCountLine: Physical inventory counts
- ControlledSubstanceLog: Controlled substance tracking
"""
from decimal import Decimal

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

User = get_user_model()


class StockLocation(models.Model):
    """Physical storage location."""

    LOCATION_TYPES = [
        ('store', _('Store Floor')),
        ('pharmacy', _('Pharmacy')),
        ('clinic', _('Clinic Storage')),
        ('refrigerated', _('Refrigerated')),
        ('controlled', _('Controlled Substances')),
        ('warehouse', _('Warehouse/Backstock')),
    ]

    name = models.CharField(_('name'), max_length=100)
    description = models.TextField(_('description'), blank=True)
    location_type = models.CharField(
        _('location type'),
        max_length=20,
        choices=LOCATION_TYPES,
        default='store'
    )
    requires_temperature_control = models.BooleanField(
        _('requires temperature control'),
        default=False
    )
    requires_restricted_access = models.BooleanField(
        _('requires restricted access'),
        default=False
    )
    is_active = models.BooleanField(_('active'), default=True)

    class Meta:
        ordering = ['name']
        verbose_name = _('stock location')
        verbose_name_plural = _('stock locations')

    def __str__(self):
        return self.name


class StockLevel(models.Model):
    """Current stock level for a product at a location."""

    product = models.ForeignKey(
        'store.Product',
        on_delete=models.CASCADE,
        related_name='stock_levels',
        verbose_name=_('product')
    )
    location = models.ForeignKey(
        StockLocation,
        on_delete=models.CASCADE,
        related_name='stock_levels',
        verbose_name=_('location')
    )

    quantity = models.DecimalField(
        _('quantity'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0')
    )
    reserved_quantity = models.DecimalField(
        _('reserved quantity'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0'),
        help_text=_('Reserved for pending orders')
    )

    min_level = models.DecimalField(
        _('minimum level'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Override product default')
    )
    reorder_quantity = models.DecimalField(
        _('reorder quantity'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    last_counted = models.DateTimeField(_('last counted'), null=True, blank=True)
    last_movement = models.DateTimeField(_('last movement'), null=True, blank=True)

    class Meta:
        unique_together = ['product', 'location']
        verbose_name = _('stock level')
        verbose_name_plural = _('stock levels')

    def __str__(self):
        return f"{self.product.name} @ {self.location.name}: {self.quantity}"

    @property
    def available_quantity(self):
        """Get available quantity (total minus reserved)."""
        return self.quantity - self.reserved_quantity

    @property
    def is_below_minimum(self):
        """Check if stock is at or below minimum level."""
        min_level = self.min_level
        if min_level is None:
            min_level = getattr(self.product, 'low_stock_threshold', 0) or Decimal('0')
        return self.quantity <= min_level


class StockBatch(models.Model):
    """Batch/lot of a product with expiry tracking."""

    STATUS_CHOICES = [
        ('available', _('Available')),
        ('low', _('Low Stock')),
        ('depleted', _('Depleted')),
        ('expired', _('Expired')),
        ('recalled', _('Recalled')),
        ('damaged', _('Damaged')),
    ]

    product = models.ForeignKey(
        'store.Product',
        on_delete=models.CASCADE,
        related_name='batches',
        verbose_name=_('product')
    )
    location = models.ForeignKey(
        StockLocation,
        on_delete=models.CASCADE,
        related_name='batches',
        verbose_name=_('location')
    )

    batch_number = models.CharField(_('batch number'), max_length=100)
    lot_number = models.CharField(_('lot number'), max_length=100, blank=True)
    serial_number = models.CharField(_('serial number'), max_length=100, blank=True)

    initial_quantity = models.DecimalField(
        _('initial quantity'),
        max_digits=10,
        decimal_places=2
    )
    current_quantity = models.DecimalField(
        _('current quantity'),
        max_digits=10,
        decimal_places=2
    )

    manufacture_date = models.DateField(_('manufacture date'), null=True, blank=True)
    expiry_date = models.DateField(_('expiry date'), null=True, blank=True)
    received_date = models.DateField(_('received date'))

    unit_cost = models.DecimalField(
        _('unit cost'),
        max_digits=10,
        decimal_places=2
    )

    supplier = models.ForeignKey(
        'Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='batches',
        verbose_name=_('supplier')
    )
    purchase_order = models.ForeignKey(
        'PurchaseOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='batches',
        verbose_name=_('purchase order')
    )

    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='available'
    )
    notes = models.TextField(_('notes'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        ordering = ['expiry_date', 'received_date']  # FEFO order
        verbose_name = _('stock batch')
        verbose_name_plural = _('stock batches')

    def __str__(self):
        return f"{self.product.name} - {self.batch_number}"

    @property
    def is_expired(self):
        """Check if batch is expired."""
        if not self.expiry_date:
            return False
        return self.expiry_date < timezone.now().date()

    @property
    def days_until_expiry(self):
        """Get days until expiry (negative if expired)."""
        if not self.expiry_date:
            return None
        return (self.expiry_date - timezone.now().date()).days


class StockMovement(models.Model):
    """Record of stock movement (in, out, transfer, adjustment)."""

    MOVEMENT_TYPES = [
        # Inbound
        ('receive', _('Received from Supplier')),
        ('return_customer', _('Customer Return')),
        ('transfer_in', _('Transfer In')),
        ('adjustment_add', _('Adjustment (Add)')),
        # Outbound
        ('sale', _('Sale')),
        ('dispense', _('Prescription Dispensed')),
        ('return_supplier', _('Return to Supplier')),
        ('transfer_out', _('Transfer Out')),
        ('adjustment_remove', _('Adjustment (Remove)')),
        ('expired', _('Expired/Disposed')),
        ('damaged', _('Damaged')),
        ('loss', _('Loss/Shrinkage')),
        ('sample', _('Sample/Promo')),
    ]

    product = models.ForeignKey(
        'store.Product',
        on_delete=models.CASCADE,
        related_name='movements',
        verbose_name=_('product')
    )
    batch = models.ForeignKey(
        StockBatch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movements',
        verbose_name=_('batch')
    )

    movement_type = models.CharField(
        _('movement type'),
        max_length=20,
        choices=MOVEMENT_TYPES
    )

    from_location = models.ForeignKey(
        StockLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movements_out',
        verbose_name=_('from location')
    )
    to_location = models.ForeignKey(
        StockLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movements_in',
        verbose_name=_('to location')
    )

    quantity = models.DecimalField(
        _('quantity'),
        max_digits=10,
        decimal_places=2
    )
    unit_cost = models.DecimalField(
        _('unit cost'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    reference_type = models.CharField(
        _('reference type'),
        max_length=50,
        blank=True,
        help_text=_('order, invoice, purchase_order, prescription, adjustment, etc.')
    )
    reference_id = models.IntegerField(
        _('reference ID'),
        null=True,
        blank=True
    )

    reason = models.TextField(_('reason'), blank=True)
    authorized_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='authorized_movements',
        verbose_name=_('authorized by')
    )

    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='recorded_movements',
        verbose_name=_('recorded by')
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('stock movement')
        verbose_name_plural = _('stock movements')

    def __str__(self):
        return f"{self.movement_type}: {self.quantity} x {self.product.name}"


class Supplier(models.Model):
    """Product supplier/vendor."""

    name = models.CharField(_('name'), max_length=200)
    code = models.CharField(_('code'), max_length=50, blank=True)

    contact_name = models.CharField(_('contact name'), max_length=200, blank=True)
    email = models.EmailField(_('email'), blank=True)
    phone = models.CharField(_('phone'), max_length=20, blank=True)
    address = models.TextField(_('address'), blank=True)

    rfc = models.CharField(_('RFC'), max_length=13, blank=True, help_text=_('Tax ID'))
    payment_terms = models.CharField(
        _('payment terms'),
        max_length=50,
        blank=True,
        help_text=_('net30, prepaid, etc.')
    )

    lead_time_days = models.IntegerField(
        _('lead time (days)'),
        null=True,
        blank=True
    )
    categories = models.JSONField(
        _('categories'),
        default=list,
        help_text=_('Categories this supplier provides')
    )

    is_active = models.BooleanField(_('active'), default=True)
    is_preferred = models.BooleanField(_('preferred'), default=False)

    notes = models.TextField(_('notes'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = _('supplier')
        verbose_name_plural = _('suppliers')

    def __str__(self):
        return self.name


class ProductSupplier(models.Model):
    """Link products to their suppliers."""

    product = models.ForeignKey(
        'store.Product',
        on_delete=models.CASCADE,
        related_name='suppliers',
        verbose_name=_('product')
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name=_('supplier')
    )

    supplier_sku = models.CharField(_('supplier SKU'), max_length=100, blank=True)
    unit_cost = models.DecimalField(
        _('unit cost'),
        max_digits=10,
        decimal_places=2
    )
    minimum_order_quantity = models.DecimalField(
        _('minimum order quantity'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('1')
    )

    is_preferred = models.BooleanField(_('preferred'), default=False)
    is_active = models.BooleanField(_('active'), default=True)

    last_ordered = models.DateField(_('last ordered'), null=True, blank=True)
    last_price = models.DecimalField(
        _('last price'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    class Meta:
        unique_together = ['product', 'supplier']
        verbose_name = _('product supplier')
        verbose_name_plural = _('product suppliers')

    def __str__(self):
        return f"{self.product.name} from {self.supplier.name}"


class ReorderRule(models.Model):
    """Automatic reorder rules for products."""

    product = models.ForeignKey(
        'store.Product',
        on_delete=models.CASCADE,
        related_name='reorder_rules',
        verbose_name=_('product')
    )
    location = models.ForeignKey(
        StockLocation,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reorder_rules',
        verbose_name=_('location'),
        help_text=_('If null, applies to all locations')
    )

    min_level = models.DecimalField(
        _('minimum level'),
        max_digits=10,
        decimal_places=2
    )
    reorder_point = models.DecimalField(
        _('reorder point'),
        max_digits=10,
        decimal_places=2
    )
    reorder_quantity = models.DecimalField(
        _('reorder quantity'),
        max_digits=10,
        decimal_places=2
    )
    max_level = models.DecimalField(
        _('maximum level'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    preferred_supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reorder_rules',
        verbose_name=_('preferred supplier')
    )

    is_active = models.BooleanField(_('active'), default=True)
    auto_create_po = models.BooleanField(
        _('auto create PO'),
        default=False,
        help_text=_('Automatically create purchase order when below reorder point')
    )

    class Meta:
        unique_together = ['product', 'location']
        verbose_name = _('reorder rule')
        verbose_name_plural = _('reorder rules')

    def __str__(self):
        loc = self.location.name if self.location else 'All Locations'
        return f"Reorder {self.product.name} @ {loc}"


class PurchaseOrder(models.Model):
    """Purchase order to supplier."""

    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('submitted', _('Submitted')),
        ('confirmed', _('Confirmed by Supplier')),
        ('shipped', _('Shipped')),
        ('partial', _('Partially Received')),
        ('received', _('Fully Received')),
        ('cancelled', _('Cancelled')),
    ]

    po_number = models.CharField(_('PO number'), max_length=50, unique=True)
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name='purchase_orders',
        verbose_name=_('supplier')
    )

    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    order_date = models.DateField(_('order date'), null=True, blank=True)
    expected_date = models.DateField(_('expected date'), null=True, blank=True)
    received_date = models.DateField(_('received date'), null=True, blank=True)

    subtotal = models.DecimalField(
        _('subtotal'),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0')
    )
    tax = models.DecimalField(
        _('tax'),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0')
    )
    shipping = models.DecimalField(
        _('shipping'),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0')
    )
    total = models.DecimalField(
        _('total'),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0')
    )

    delivery_location = models.ForeignKey(
        StockLocation,
        on_delete=models.SET_NULL,
        null=True,
        related_name='purchase_orders',
        verbose_name=_('delivery location')
    )
    shipping_address = models.TextField(_('shipping address'), blank=True)

    notes = models.TextField(_('notes'), blank=True)
    internal_notes = models.TextField(_('internal notes'), blank=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='+',
        verbose_name=_('created by')
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        verbose_name=_('approved by')
    )

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('purchase order')
        verbose_name_plural = _('purchase orders')

    def __str__(self):
        return f"PO {self.po_number}"


class PurchaseOrderLine(models.Model):
    """Line item on purchase order."""

    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=_('purchase order')
    )
    product = models.ForeignKey(
        'store.Product',
        on_delete=models.PROTECT,
        related_name='purchase_order_lines',
        verbose_name=_('product')
    )

    quantity_ordered = models.DecimalField(
        _('quantity ordered'),
        max_digits=10,
        decimal_places=2
    )
    quantity_received = models.DecimalField(
        _('quantity received'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0')
    )

    unit_cost = models.DecimalField(
        _('unit cost'),
        max_digits=10,
        decimal_places=2
    )
    line_total = models.DecimalField(
        _('line total'),
        max_digits=15,
        decimal_places=2
    )

    supplier_sku = models.CharField(_('supplier SKU'), max_length=100, blank=True)
    notes = models.TextField(_('notes'), blank=True)

    class Meta:
        verbose_name = _('purchase order line')
        verbose_name_plural = _('purchase order lines')

    def __str__(self):
        return f"{self.quantity_ordered} x {self.product.name}"


class StockCount(models.Model):
    """Physical inventory count."""

    STATUS_CHOICES = [
        ('draft', _('In Progress')),
        ('submitted', _('Submitted for Review')),
        ('approved', _('Approved')),
        ('posted', _('Posted to Stock')),
        ('cancelled', _('Cancelled')),
    ]

    COUNT_TYPE_CHOICES = [
        ('full', _('Full Count')),
        ('cycle', _('Cycle Count')),
        ('spot', _('Spot Check')),
    ]

    location = models.ForeignKey(
        StockLocation,
        on_delete=models.CASCADE,
        related_name='stock_counts',
        verbose_name=_('location')
    )
    count_date = models.DateField(_('count date'))
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    count_type = models.CharField(
        _('count type'),
        max_length=20,
        choices=COUNT_TYPE_CHOICES,
        default='full'
    )
    product_filter = models.JSONField(
        _('product filter'),
        default=dict,
        blank=True,
        help_text=_('Filter to specific products/categories')
    )

    total_products = models.IntegerField(_('total products'), default=0)
    products_counted = models.IntegerField(_('products counted'), default=0)
    discrepancies_found = models.IntegerField(_('discrepancies found'), default=0)
    discrepancy_value = models.DecimalField(
        _('discrepancy value'),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0')
    )

    notes = models.TextField(_('notes'), blank=True)

    counted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='+',
        verbose_name=_('counted by')
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        verbose_name=_('approved by')
    )
    approved_at = models.DateTimeField(_('approved at'), null=True, blank=True)

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('stock count')
        verbose_name_plural = _('stock counts')

    def __str__(self):
        return f"Count @ {self.location.name} - {self.count_date}"


class StockCountLine(models.Model):
    """Individual product count in an inventory count."""

    stock_count = models.ForeignKey(
        StockCount,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=_('stock count')
    )
    product = models.ForeignKey(
        'store.Product',
        on_delete=models.CASCADE,
        related_name='count_lines',
        verbose_name=_('product')
    )
    batch = models.ForeignKey(
        StockBatch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='count_lines',
        verbose_name=_('batch')
    )

    system_quantity = models.DecimalField(
        _('system quantity'),
        max_digits=10,
        decimal_places=2
    )
    counted_quantity = models.DecimalField(
        _('counted quantity'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    discrepancy = models.DecimalField(
        _('discrepancy'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    discrepancy_value = models.DecimalField(
        _('discrepancy value'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    adjustment_reason = models.TextField(_('adjustment reason'), blank=True)
    adjustment_posted = models.BooleanField(_('adjustment posted'), default=False)

    counted_at = models.DateTimeField(_('counted at'), null=True, blank=True)

    class Meta:
        verbose_name = _('stock count line')
        verbose_name_plural = _('stock count lines')

    def __str__(self):
        return f"{self.product.name}: {self.system_quantity} -> {self.counted_quantity}"


class ControlledSubstanceLog(models.Model):
    """Special tracking for controlled substances."""

    LOG_TYPES = [
        ('receive', _('Received')),
        ('dispense', _('Dispensed')),
        ('waste', _('Waste/Disposal')),
        ('return', _('Returned')),
        ('transfer', _('Transferred')),
        ('adjustment', _('Adjustment')),
    ]

    product = models.ForeignKey(
        'store.Product',
        on_delete=models.CASCADE,
        related_name='controlled_logs',
        verbose_name=_('product')
    )
    batch = models.ForeignKey(
        StockBatch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='controlled_logs',
        verbose_name=_('batch')
    )

    log_type = models.CharField(
        _('log type'),
        max_length=20,
        choices=LOG_TYPES
    )
    quantity = models.DecimalField(
        _('quantity'),
        max_digits=10,
        decimal_places=2
    )
    balance_after = models.DecimalField(
        _('balance after'),
        max_digits=10,
        decimal_places=2
    )

    pet = models.ForeignKey(
        'pets.Pet',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='controlled_substance_logs',
        verbose_name=_('pet')
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        verbose_name=_('owner')
    )
    prescription = models.ForeignKey(
        'pharmacy.Prescription',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='controlled_logs',
        verbose_name=_('prescription')
    )

    waste_reason = models.TextField(_('waste reason'), blank=True)
    waste_witnessed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        verbose_name=_('waste witnessed by')
    )

    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='controlled_substance_recordings',
        verbose_name=_('recorded by')
    )
    notes = models.TextField(_('notes'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('controlled substance log')
        verbose_name_plural = _('controlled substance logs')

    def __str__(self):
        return f"{self.log_type}: {self.quantity} x {self.product.name}"
