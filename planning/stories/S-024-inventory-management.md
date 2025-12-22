# S-024: Inventory Management

> **REQUIRED READING:** Before implementation, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md)

**Story Type:** User Story
**Priority:** High
**Epoch:** 3 (with E-Commerce)
**Status:** PENDING
**Module:** django-simple-store

## User Story

**As a** clinic staff member
**I want to** track inventory levels and expiry dates
**So that** we never run out of essential products or use expired medications

**As a** clinic owner
**I want to** manage stock efficiently with automatic reorder alerts
**So that** I minimize waste and stockouts

**As a** pharmacist/vet tech
**I want to** track controlled substances with proper documentation
**So that** we maintain regulatory compliance

## Acceptance Criteria

### Stock Tracking
- [ ] Current stock levels per product
- [ ] Stock by location (if multiple storage areas)
- [ ] Batch/lot number tracking for medications
- [ ] Expiry date tracking per batch
- [ ] Serial numbers for equipment (optional)
- [ ] Real-time stock visibility

### Stock Movements
- [ ] Automatic deduction on sale
- [ ] Automatic deduction on prescription dispensing
- [ ] Manual adjustments (damage, loss, count correction)
- [ ] Transfers between locations
- [ ] Receiving new stock
- [ ] Stock returns to supplier
- [ ] Complete audit trail of all movements

### Reorder Management
- [ ] Minimum stock levels (reorder point) per product
- [ ] Automatic reorder alerts
- [ ] Suggested reorder quantities
- [ ] Preferred suppliers per product
- [ ] Purchase order generation
- [ ] Order tracking (ordered, shipped, received)
- [ ] Supplier lead time tracking

### Expiry Management
- [ ] Expiring soon alerts (30, 60, 90 days configurable)
- [ ] FEFO recommendations (First Expired, First Out)
- [ ] Expired product flagging
- [ ] Disposal logging with reason
- [ ] Expiry loss reports

### Controlled Substances
- [ ] Special tracking for regulated medications
- [ ] Receiving documentation
- [ ] Dispensing log (who, when, to whom, reason)
- [ ] Waste/disposal documentation
- [ ] Audit reports for compliance
- [ ] Integration with S-010 Pharmacy

### Inventory Counts
- [ ] Physical count entry
- [ ] Count discrepancy reporting
- [ ] Adjustment authorization
- [ ] Count history

### Reporting
- [ ] Stock valuation (FIFO, weighted average)
- [ ] Turnover rates
- [ ] Dead stock identification
- [ ] Expiry loss reports
- [ ] Reorder recommendations
- [ ] Movement history

## Technical Requirements

### Models

```python
class StockLocation(models.Model):
    """Physical storage location"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # Type
    LOCATION_TYPES = [
        ('store', 'Store Floor'),
        ('pharmacy', 'Pharmacy'),
        ('clinic', 'Clinic Storage'),
        ('refrigerated', 'Refrigerated'),
        ('controlled', 'Controlled Substances'),
        ('warehouse', 'Warehouse/Backstock'),
    ]
    location_type = models.CharField(max_length=20, choices=LOCATION_TYPES)

    # Requirements
    requires_temperature_control = models.BooleanField(default=False)
    requires_restricted_access = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']


class StockLevel(models.Model):
    """Current stock level for a product at a location"""
    product = models.ForeignKey('store.Product', on_delete=models.CASCADE, related_name='stock_levels')
    location = models.ForeignKey(StockLocation, on_delete=models.CASCADE)

    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reserved_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # Reserved for pending orders

    # Reorder settings (can override product defaults)
    min_level = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    reorder_quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    last_counted = models.DateTimeField(null=True, blank=True)
    last_movement = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['product', 'location']

    @property
    def available_quantity(self):
        return self.quantity - self.reserved_quantity

    @property
    def is_below_minimum(self):
        min_level = self.min_level or self.product.min_stock_level or 0
        return self.quantity <= min_level


class StockBatch(models.Model):
    """Batch/lot of a product with expiry tracking"""
    product = models.ForeignKey('store.Product', on_delete=models.CASCADE, related_name='batches')
    location = models.ForeignKey(StockLocation, on_delete=models.CASCADE)

    # Identification
    batch_number = models.CharField(max_length=100)
    lot_number = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)

    # Quantity
    initial_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    current_quantity = models.DecimalField(max_digits=10, decimal_places=2)

    # Dates
    manufacture_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    received_date = models.DateField()

    # Cost
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)

    # Supplier
    supplier = models.ForeignKey('Supplier', on_delete=models.SET_NULL, null=True, blank=True)
    purchase_order = models.ForeignKey('PurchaseOrder', on_delete=models.SET_NULL, null=True, blank=True)

    # Status
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('low', 'Low Stock'),
        ('depleted', 'Depleted'),
        ('expired', 'Expired'),
        ('recalled', 'Recalled'),
        ('damaged', 'Damaged'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['expiry_date', 'received_date']  # FEFO order
        verbose_name_plural = 'Stock batches'

    @property
    def is_expired(self):
        if not self.expiry_date:
            return False
        from django.utils import timezone
        return self.expiry_date < timezone.now().date()

    @property
    def days_until_expiry(self):
        if not self.expiry_date:
            return None
        from django.utils import timezone
        return (self.expiry_date - timezone.now().date()).days


class StockMovement(models.Model):
    """Record of stock movement (in, out, transfer, adjustment)"""
    MOVEMENT_TYPES = [
        # Inbound
        ('receive', 'Received from Supplier'),
        ('return_customer', 'Customer Return'),
        ('transfer_in', 'Transfer In'),
        ('adjustment_add', 'Adjustment (Add)'),

        # Outbound
        ('sale', 'Sale'),
        ('dispense', 'Prescription Dispensed'),
        ('return_supplier', 'Return to Supplier'),
        ('transfer_out', 'Transfer Out'),
        ('adjustment_remove', 'Adjustment (Remove)'),
        ('expired', 'Expired/Disposed'),
        ('damaged', 'Damaged'),
        ('loss', 'Loss/Shrinkage'),
        ('sample', 'Sample/Promo'),
    ]

    product = models.ForeignKey('store.Product', on_delete=models.CASCADE, related_name='movements')
    batch = models.ForeignKey(StockBatch, on_delete=models.SET_NULL, null=True, blank=True)

    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)

    # Locations
    from_location = models.ForeignKey(
        StockLocation, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='movements_out'
    )
    to_location = models.ForeignKey(
        StockLocation, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='movements_in'
    )

    # Quantity
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Reference
    reference_type = models.CharField(max_length=50, blank=True)
    # order, invoice, purchase_order, prescription, adjustment, etc.
    reference_id = models.IntegerField(null=True, blank=True)

    # For adjustments
    reason = models.TextField(blank=True)
    authorized_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='authorized_movements'
    )

    # Audit
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class Supplier(models.Model):
    """Product supplier/vendor"""
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, blank=True)

    # Contact
    contact_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    # Business
    rfc = models.CharField(max_length=13, blank=True)  # Tax ID
    payment_terms = models.CharField(max_length=50, blank=True)
    # net30, prepaid, etc.

    # Lead time
    lead_time_days = models.IntegerField(null=True, blank=True)

    # Products
    categories = models.JSONField(default=list)
    # Categories this supplier provides

    # Status
    is_active = models.BooleanField(default=True)
    is_preferred = models.BooleanField(default=False)

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']


class ProductSupplier(models.Model):
    """Link products to their suppliers"""
    product = models.ForeignKey('store.Product', on_delete=models.CASCADE, related_name='suppliers')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='products')

    supplier_sku = models.CharField(max_length=100, blank=True)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_order_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)

    is_preferred = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    last_ordered = models.DateField(null=True, blank=True)
    last_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ['product', 'supplier']


class ReorderRule(models.Model):
    """Automatic reorder rules for products"""
    product = models.ForeignKey('store.Product', on_delete=models.CASCADE, related_name='reorder_rules')
    location = models.ForeignKey(StockLocation, on_delete=models.CASCADE, null=True, blank=True)
    # If null, applies to all locations

    min_level = models.DecimalField(max_digits=10, decimal_places=2)
    reorder_point = models.DecimalField(max_digits=10, decimal_places=2)
    reorder_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    max_level = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    preferred_supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    auto_create_po = models.BooleanField(default=False)
    # Automatically create purchase order when below reorder point

    class Meta:
        unique_together = ['product', 'location']


class PurchaseOrder(models.Model):
    """Purchase order to supplier"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('confirmed', 'Confirmed by Supplier'),
        ('shipped', 'Shipped'),
        ('partial', 'Partially Received'),
        ('received', 'Fully Received'),
        ('cancelled', 'Cancelled'),
    ]

    po_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchase_orders')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Dates
    order_date = models.DateField(null=True, blank=True)
    expected_date = models.DateField(null=True, blank=True)
    received_date = models.DateField(null=True, blank=True)

    # Totals
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    shipping = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Delivery
    delivery_location = models.ForeignKey(StockLocation, on_delete=models.SET_NULL, null=True)
    shipping_address = models.TextField(blank=True)

    # Notes
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)

    # Audit
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']


class PurchaseOrderLine(models.Model):
    """Line item on purchase order"""
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey('store.Product', on_delete=models.PROTECT)

    quantity_ordered = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_received = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=15, decimal_places=2)

    # Supplier reference
    supplier_sku = models.CharField(max_length=100, blank=True)

    notes = models.TextField(blank=True)


class StockCount(models.Model):
    """Physical inventory count"""
    STATUS_CHOICES = [
        ('draft', 'In Progress'),
        ('submitted', 'Submitted for Review'),
        ('approved', 'Approved'),
        ('posted', 'Posted to Stock'),
        ('cancelled', 'Cancelled'),
    ]

    location = models.ForeignKey(StockLocation, on_delete=models.CASCADE)
    count_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Scope
    count_type = models.CharField(max_length=20, default='full')
    # full, cycle, spot
    product_filter = models.JSONField(default=dict, blank=True)
    # Filter to specific products/categories

    # Totals
    total_products = models.IntegerField(default=0)
    products_counted = models.IntegerField(default=0)
    discrepancies_found = models.IntegerField(default=0)
    discrepancy_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Notes
    notes = models.TextField(blank=True)

    # Audit
    counted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    approved_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class StockCountLine(models.Model):
    """Individual product count in an inventory count"""
    stock_count = models.ForeignKey(StockCount, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey('store.Product', on_delete=models.CASCADE)
    batch = models.ForeignKey(StockBatch, on_delete=models.SET_NULL, null=True, blank=True)

    # Quantities
    system_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    counted_quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Discrepancy
    discrepancy = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discrepancy_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Resolution
    adjustment_reason = models.TextField(blank=True)
    adjustment_posted = models.BooleanField(default=False)

    counted_at = models.DateTimeField(null=True, blank=True)


class ControlledSubstanceLog(models.Model):
    """Special tracking for controlled substances"""
    product = models.ForeignKey('store.Product', on_delete=models.CASCADE)
    batch = models.ForeignKey(StockBatch, on_delete=models.SET_NULL, null=True)

    LOG_TYPES = [
        ('receive', 'Received'),
        ('dispense', 'Dispensed'),
        ('waste', 'Waste/Disposal'),
        ('return', 'Returned'),
        ('transfer', 'Transferred'),
        ('adjustment', 'Adjustment'),
    ]

    log_type = models.CharField(max_length=20, choices=LOG_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)

    # For dispensing
    pet = models.ForeignKey('vet_clinic.Pet', on_delete=models.SET_NULL, null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    prescription = models.ForeignKey('pharmacy.Prescription', on_delete=models.SET_NULL, null=True, blank=True)

    # For waste
    waste_reason = models.TextField(blank=True)
    waste_witnessed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+'
    )

    # Audit
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
```

### AI Tools

```python
INVENTORY_TOOLS = [
    {
        "name": "check_stock_level",
        "description": "Check current stock level for a product",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "integer"},
                "location": {"type": "string"}
            },
            "required": ["product_id"]
        }
    },
    {
        "name": "get_expiring_products",
        "description": "Get products expiring within specified days",
        "parameters": {
            "type": "object",
            "properties": {
                "days_ahead": {"type": "integer"},
                "location": {"type": "string"}
            },
            "required": ["days_ahead"]
        }
    },
    {
        "name": "get_low_stock_products",
        "description": "Get products at or below reorder point",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            }
        }
    },
    {
        "name": "generate_reorder_list",
        "description": "Generate list of products that need to be reordered",
        "parameters": {
            "type": "object",
            "properties": {
                "supplier_id": {"type": "integer"}
            }
        }
    },
    {
        "name": "record_stock_adjustment",
        "description": "Record a manual stock adjustment",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "integer"},
                "quantity": {"type": "number"},
                "adjustment_type": {"type": "string"},
                "reason": {"type": "string"}
            },
            "required": ["product_id", "quantity", "adjustment_type", "reason"]
        }
    },
    {
        "name": "receive_stock",
        "description": "Record receiving stock from a purchase order",
        "parameters": {
            "type": "object",
            "properties": {
                "purchase_order_id": {"type": "integer"},
                "items": {"type": "array"}
            },
            "required": ["purchase_order_id", "items"]
        }
    },
    {
        "name": "create_purchase_order",
        "description": "Create a purchase order for a supplier",
        "parameters": {
            "type": "object",
            "properties": {
                "supplier_id": {"type": "integer"},
                "items": {"type": "array"}
            },
            "required": ["supplier_id", "items"]
        }
    },
    {
        "name": "get_stock_valuation",
        "description": "Get total stock valuation",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"},
                "category": {"type": "string"}
            }
        }
    }
]
```

## Example AI Conversations

### Checking Stock Levels
```
Staff: Do we have Apoquel 16mg in stock?

AI: 📦 APOQUEL 16MG STOCK STATUS
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    📍 Pharmacy: 45 tablets
        • Batch AP-2025-001: 30 tablets (exp: June 2026)
        • Batch AP-2025-002: 15 tablets (exp: Aug 2026)

    📍 Store: 120 tablets
        • Batch AP-2025-001: 50 tablets (exp: June 2026)
        • Batch AP-2025-003: 70 tablets (exp: Oct 2026)

    Total Available: 165 tablets
    Reorder Point: 50 tablets
    Status: ✅ Well Stocked

    Average monthly usage: ~40 tablets
    Estimated runway: 4 months
```

### Expiring Products Alert
```
Staff: What's expiring in the next 30 days?

AI: ⚠️ PRODUCTS EXPIRING WITHIN 30 DAYS
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    🔴 CRITICAL (7 days or less):
    1. Metacam 1.5mg/ml (15ml) - 3 bottles
       Expires: December 28, 2025 (7 days)
       Batch: MC-2024-456
       Action: Use immediately or mark down

    🟡 WARNING (8-30 days):
    2. Hills K/D Kidney Care - 5 cans
       Expires: January 10, 2026 (20 days)
       Batch: HD-2024-789
       Action: Promote for sale

    3. Proin 75mg - 28 tablets
       Expires: January 15, 2026 (25 days)
       Batch: PR-2024-123
       Action: Use in upcoming prescriptions

    Total expiring value: $2,340 MXN

    Would you like me to:
    1. Create a markdown promotion
    2. Check if any can be returned to supplier
    3. Schedule disposal for expired items
```

### Reorder Alert
```
AI: 📢 LOW STOCK ALERT
    ━━━━━━━━━━━━━━━━━━━

    The following products need to be reordered:

    🔴 CRITICAL (At or below minimum):
    • Rimadyl 100mg: 8 left (min: 20)
    • NexGard 25-50kg: 3 left (min: 10)

    🟡 WARNING (Below reorder point):
    • Revolution Cat: 12 left (reorder at: 15)
    • Frontline Plus Dog M: 18 left (reorder at: 25)

    Suggested action:
    I can create purchase orders for:
    • VetPharm (Rimadyl, NexGard): ~$8,500 MXN
    • PetMed Supplier (Revolution, Frontline): ~$4,200 MXN

    Create purchase orders?

Staff: Yes, create both

AI: ✅ Purchase orders created:

    PO-2025-0234 - VetPharm
    • Rimadyl 100mg × 100 tablets
    • NexGard 25-50kg × 30 doses
    • Total: $8,540 MXN
    • Expected delivery: 3-5 business days

    PO-2025-0235 - PetMed Supplier
    • Revolution Cat × 50 doses
    • Frontline Plus Dog M × 40 doses
    • Total: $4,280 MXN
    • Expected delivery: 2-3 business days

    📧 Orders emailed to suppliers
    📋 Added to pending orders list
```

### Controlled Substance Dispensing
```
Staff: Dispense tramadol for Luna's prescription

AI: 🔐 CONTROLLED SUBSTANCE DISPENSING
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    Prescription: RX-2025-0892
    Patient: Luna (García)
    Medication: Tramadol 50mg

    Dispensing details:
    • Quantity: 20 tablets
    • From batch: TR-2025-007 (exp: Dec 2026)
    • Current batch balance: 85 tablets

    ⚠️ This requires documentation:

    Dispensed by: [Your name will be recorded]
    Date/Time: December 21, 2025 14:32

    Balance after dispensing: 65 tablets

    Confirm dispensing?

Staff: Confirmed

AI: ✅ Tramadol dispensed and logged

    📋 Controlled Substance Log Entry:
    • Log #: CS-2025-1847
    • Product: Tramadol 50mg
    • Quantity: 20 tablets
    • Balance: 65 tablets remaining
    • Patient: Luna (owner: María García)
    • Prescription: RX-2025-0892
    • Dispensed by: [Staff Name]
    • Time: December 21, 2025 14:32

    Print prescription label?
```

## Definition of Done

- [ ] StockLevel model with location support
- [ ] StockBatch model with expiry tracking
- [ ] StockMovement model with full audit trail
- [ ] Automatic stock deduction on sale
- [ ] Reorder alerts system
- [ ] Purchase order workflow
- [ ] Expiry management with FEFO
- [ ] Stock count/adjustment workflow
- [ ] Controlled substance logging
- [ ] AI tools for inventory queries
- [ ] Reporting dashboard
- [ ] Tests written and passing (>95% coverage)

## Dependencies

- S-005: E-Commerce (Product model)
- S-010: Pharmacy (prescriptions, controlled substances)
- S-020: Billing (purchase order payments)
- S-026: Accounting (inventory valuation)

## Notes

- FEFO (First Expired, First Out) should be default for all medications
- Controlled substance tracking must meet COFEPRIS requirements (Mexico)
- Consider barcode/QR scanning for faster receiving and counting
- Stock valuation affects financial reporting (link to S-026)
- May need temperature logging integration for refrigerated items (future)

## Development Process

**Before implementing this story**, review and follow the **23-Step TDD Cycle** in:
- `CLAUDE.md` - Global development workflow
- `planning/TASK_BREAKDOWN.md` - Specific tasks for this story

Tests must be written before implementation. >95% coverage required.
