# Inventory Module

The `apps.inventory` module provides comprehensive inventory management for veterinary clinic products, medications, and supplies, including batch/lot tracking, expiration management, and purchase order processing.

## Table of Contents

- [Overview](#overview)
- [Models](#models)
  - [StockLocation](#stocklocation)
  - [StockLevel](#stocklevel)
  - [StockBatch](#stockbatch)
  - [StockMovement](#stockmovement)
  - [Supplier](#supplier)
  - [ProductSupplier](#productsupplier)
  - [ReorderRule](#reorderrule)
  - [PurchaseOrder](#purchaseorder)
  - [StockCount](#stockcount)
  - [ControlledSubstanceLog](#controlledsubstancelog)
- [Staff Views](#staff-views)
- [Stock Management](#stock-management)
- [Batch Tracking](#batch-tracking)
- [Purchase Orders](#purchase-orders)
- [Reorder Rules](#reorder-rules)
- [Physical Inventory](#physical-inventory)
- [Integration Points](#integration-points)
- [Query Examples](#query-examples)
- [Testing](#testing)

## Overview

The inventory module handles:

- **Multi-location stock tracking** - Store floor, pharmacy, refrigerated, controlled substances
- **Batch/lot management** - Expiration dates, FEFO (First Expired, First Out) ordering
- **Stock movements** - Receipts, sales, transfers, adjustments with full audit trail
- **Supplier management** - Vendor database with product-supplier relationships
- **Purchase orders** - Draft, submit, receive workflow
- **Reorder automation** - Min/max levels, auto-PO generation
- **Physical inventory** - Cycle counts, spot checks, discrepancy tracking
- **Controlled substances** - DEA-compliant logging (integrates with pharmacy)

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  StockLocation  │────▶│   StockLevel    │◀────│    Product      │
│ (where stored)  │     │ (qty per loc)   │     │  (from store)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   StockBatch    │────▶│  StockMovement  │◀────│  PurchaseOrder  │
│ (lot/expiry)    │     │  (audit trail)  │     │  (from supplier)│
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Models

### StockLocation

Physical storage locations within the clinic.

```python
class StockLocation(models.Model):
    LOCATION_TYPES = [
        ('store', 'Store Floor'),
        ('pharmacy', 'Pharmacy'),
        ('clinic', 'Clinic Storage'),
        ('refrigerated', 'Refrigerated'),
        ('controlled', 'Controlled Substances'),
        ('warehouse', 'Warehouse/Backstock'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    location_type = models.CharField(max_length=20, choices=LOCATION_TYPES)
    requires_temperature_control = models.BooleanField(default=False)
    requires_restricted_access = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
```

**Usage:**
```python
from apps.inventory.models import StockLocation

# Create locations
pharmacy = StockLocation.objects.create(
    name='Main Pharmacy',
    location_type='pharmacy',
    requires_restricted_access=True
)

fridge = StockLocation.objects.create(
    name='Vaccine Refrigerator',
    location_type='refrigerated',
    requires_temperature_control=True
)
```

### StockLevel

Current stock quantity for a product at a specific location.

```python
class StockLevel(models.Model):
    product = models.ForeignKey('store.Product', related_name='stock_levels')
    location = models.ForeignKey(StockLocation, related_name='stock_levels')

    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    reserved_quantity = models.DecimalField(default=0)  # For pending orders

    min_level = models.DecimalField(null=True)  # Override product default
    reorder_quantity = models.DecimalField(null=True)

    last_counted = models.DateTimeField(null=True)
    last_movement = models.DateTimeField(null=True)

    class Meta:
        unique_together = ['product', 'location']
```

**Properties:**

| Property | Returns | Description |
|----------|---------|-------------|
| `available_quantity` | Decimal | `quantity - reserved_quantity` |
| `is_below_minimum` | bool | Stock at or below min level |

### StockBatch

Batch/lot tracking with expiration dates for FEFO management.

```python
class StockBatch(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('low', 'Low Stock'),
        ('depleted', 'Depleted'),
        ('expired', 'Expired'),
        ('recalled', 'Recalled'),
        ('damaged', 'Damaged'),
    ]

    product = models.ForeignKey('store.Product', related_name='batches')
    location = models.ForeignKey(StockLocation, related_name='batches')

    batch_number = models.CharField(max_length=100)
    lot_number = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100)

    initial_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    current_quantity = models.DecimalField(max_digits=10, decimal_places=2)

    manufacture_date = models.DateField(null=True)
    expiry_date = models.DateField(null=True)
    received_date = models.DateField()

    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)

    supplier = models.ForeignKey('Supplier', null=True)
    purchase_order = models.ForeignKey('PurchaseOrder', null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    class Meta:
        ordering = ['expiry_date', 'received_date']  # FEFO order
```

**Properties:**

| Property | Returns | Description |
|----------|---------|-------------|
| `is_expired` | bool | Expiry date has passed |
| `days_until_expiry` | int/None | Days until expiration (negative if expired) |

### StockMovement

Audit trail for all stock changes.

```python
class StockMovement(models.Model):
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

    product = models.ForeignKey('store.Product', related_name='movements')
    batch = models.ForeignKey(StockBatch, null=True, related_name='movements')

    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)

    from_location = models.ForeignKey(StockLocation, null=True, related_name='movements_out')
    to_location = models.ForeignKey(StockLocation, null=True, related_name='movements_in')

    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cost = models.DecimalField(null=True)

    reference_type = models.CharField(max_length=50)  # 'order', 'prescription', etc.
    reference_id = models.IntegerField(null=True)

    reason = models.TextField()
    authorized_by = models.ForeignKey(User, null=True, related_name='authorized_movements')
    recorded_by = models.ForeignKey(User, related_name='recorded_movements')

    created_at = models.DateTimeField(auto_now_add=True)
```

### Supplier

Vendor/supplier database.

```python
class Supplier(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50)

    contact_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()

    rfc = models.CharField(max_length=13)  # Mexican Tax ID
    payment_terms = models.CharField(max_length=50)  # 'net30', 'prepaid'

    lead_time_days = models.IntegerField(null=True)
    categories = models.JSONField(default=list)  # Product categories supplied

    is_active = models.BooleanField(default=True)
    is_preferred = models.BooleanField(default=False)
```

### ProductSupplier

Many-to-many relationship between products and suppliers with pricing.

```python
class ProductSupplier(models.Model):
    product = models.ForeignKey('store.Product', related_name='suppliers')
    supplier = models.ForeignKey(Supplier, related_name='products')

    supplier_sku = models.CharField(max_length=100)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_order_quantity = models.DecimalField(default=1)

    is_preferred = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    last_ordered = models.DateField(null=True)
    last_price = models.DecimalField(null=True)

    class Meta:
        unique_together = ['product', 'supplier']
```

### ReorderRule

Automatic reorder configuration.

```python
class ReorderRule(models.Model):
    product = models.ForeignKey('store.Product', related_name='reorder_rules')
    location = models.ForeignKey(StockLocation, null=True)  # null = all locations

    min_level = models.DecimalField(max_digits=10, decimal_places=2)
    reorder_point = models.DecimalField(max_digits=10, decimal_places=2)
    reorder_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    max_level = models.DecimalField(null=True)

    preferred_supplier = models.ForeignKey(Supplier, null=True)

    is_active = models.BooleanField(default=True)
    auto_create_po = models.BooleanField(default=False)

    class Meta:
        unique_together = ['product', 'location']
```

### PurchaseOrder

Purchase orders to suppliers.

```python
class PurchaseOrder(models.Model):
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
    supplier = models.ForeignKey(Supplier, related_name='purchase_orders')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    order_date = models.DateField(null=True)
    expected_date = models.DateField(null=True)
    received_date = models.DateField(null=True)

    subtotal = models.DecimalField(max_digits=15, decimal_places=2)
    tax = models.DecimalField(max_digits=15, decimal_places=2)
    shipping = models.DecimalField(max_digits=15, decimal_places=2)
    total = models.DecimalField(max_digits=15, decimal_places=2)

    delivery_location = models.ForeignKey(StockLocation, null=True)
    shipping_address = models.TextField()

    created_by = models.ForeignKey(User, related_name='+')
    approved_by = models.ForeignKey(User, null=True, related_name='+')
```

### StockCount

Physical inventory counts.

```python
class StockCount(models.Model):
    STATUS_CHOICES = [
        ('draft', 'In Progress'),
        ('submitted', 'Submitted for Review'),
        ('approved', 'Approved'),
        ('posted', 'Posted to Stock'),
        ('cancelled', 'Cancelled'),
    ]

    COUNT_TYPE_CHOICES = [
        ('full', 'Full Count'),
        ('cycle', 'Cycle Count'),
        ('spot', 'Spot Check'),
    ]

    location = models.ForeignKey(StockLocation, related_name='stock_counts')
    count_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    count_type = models.CharField(max_length=20, choices=COUNT_TYPE_CHOICES)

    total_products = models.IntegerField(default=0)
    products_counted = models.IntegerField(default=0)
    discrepancies_found = models.IntegerField(default=0)
    discrepancy_value = models.DecimalField(max_digits=15, decimal_places=2)

    counted_by = models.ForeignKey(User, related_name='+')
    approved_by = models.ForeignKey(User, null=True, related_name='+')
```

### ControlledSubstanceLog

DEA-compliant tracking for Schedule II-V medications.

```python
class ControlledSubstanceLog(models.Model):
    LOG_TYPES = [
        ('receive', 'Received'),
        ('dispense', 'Dispensed'),
        ('waste', 'Waste/Disposal'),
        ('return', 'Returned'),
        ('transfer', 'Transferred'),
        ('adjustment', 'Adjustment'),
    ]

    product = models.ForeignKey('store.Product', related_name='controlled_logs')
    batch = models.ForeignKey(StockBatch, null=True, related_name='controlled_logs')

    log_type = models.CharField(max_length=20, choices=LOG_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)

    pet = models.ForeignKey('pets.Pet', null=True)
    owner = models.ForeignKey(User, null=True)
    prescription = models.ForeignKey('pharmacy.Prescription', null=True)

    waste_reason = models.TextField()
    waste_witnessed_by = models.ForeignKey(User, null=True)

    recorded_by = models.ForeignKey(User, related_name='controlled_substance_recordings')
    created_at = models.DateTimeField(auto_now_add=True)
```

## Staff Views

All inventory views require staff login (`@staff_member_required`).

### Staff Token URL Routing (IMPORTANT)

The staff portal uses dynamic URL routing with session-based tokens for security. When creating templates for staff views, you **MUST** use the staff token URL pattern instead of Django's `{% url %}` template tag.

**Pattern:**
```
/staff-{{ staff_token }}/operations/inventory/[path]/
```

**Why this matters:**
- The `staff_token` is a 6-character session-based token that changes each login
- URLs like `/operations/inventory/` are blocked by middleware without the token
- Django's `{% url 'inventory:xxx' %}` generates paths without the token
- The `staff_token` context variable is provided by the `navigation` context processor

**Correct Usage (in templates):**
```html
<!-- Link to inventory dashboard -->
<a href="/staff-{{ staff_token }}/operations/inventory/">Dashboard</a>

<!-- Link to specific view with pk -->
<a href="/staff-{{ staff_token }}/operations/inventory/purchase-orders/{{ po.pk }}/">
    View PO
</a>

<!-- Form action -->
<form action="/staff-{{ staff_token }}/operations/inventory/stock-counts/{{ count.pk }}/approve/" method="post">
```

**INCORRECT (do NOT use):**
```html
<!-- These generate URLs without the staff token and will fail -->
<a href="{% url 'inventory:dashboard' %}">Dashboard</a>
<a href="{% url 'inventory:purchase_order_detail' pk=po.pk %}">View PO</a>
```

**Available Paths:**
| Template Path | Maps To |
|---------------|---------|
| `operations/inventory/` | Dashboard |
| `operations/inventory/stock/` | Stock Levels |
| `operations/inventory/batches/` | Batch List |
| `operations/inventory/movements/` | Movement List |
| `operations/inventory/movements/add/` | Add Movement |
| `operations/inventory/suppliers/` | Supplier List |
| `operations/inventory/purchase-orders/` | PO List |
| `operations/inventory/purchase-orders/create/` | Create PO |
| `operations/inventory/purchase-orders/<pk>/` | PO Detail |
| `operations/inventory/purchase-orders/<pk>/receive/` | Receive PO |
| `operations/inventory/stock-counts/` | Stock Count List |
| `operations/inventory/stock-counts/create/` | Create Count |
| `operations/inventory/stock-counts/<pk>/` | Count Detail |
| `operations/inventory/stock-counts/<pk>/entry/` | Count Entry |
| `operations/inventory/transfers/create/` | Create Transfer |
| `operations/inventory/alerts/` | Stock Alerts |
| `operations/inventory/expiring/` | Expiring Items |

**Testing with Staff Token URLs:**
```python
def get_staff_url(client, path):
    """Build staff token URL for testing."""
    session = client.session
    token = session.get('staff_token')
    if token:
        return f'/staff-{token}/{path}'
    return f'/{path}'

# Usage in tests:
def test_movement_add(self, authenticated_client):
    url = get_staff_url(authenticated_client, 'operations/inventory/movements/add/')
    response = authenticated_client.get(url)
    assert response.status_code == 200
```

### URL Patterns

| URL | View | Description |
|-----|------|-------------|
| `/inventory/` | `dashboard` | Dashboard with alerts and metrics |
| `/inventory/stock/` | `stock_levels` | Stock levels by product/location |
| `/inventory/batches/` | `batch_list` | Batch list with expiry info |
| `/inventory/batches/<id>/` | `batch_detail` | Batch details and movements |
| `/inventory/movements/` | `movement_list` | Stock movement history |
| `/inventory/movements/add/` | `movement_add` | Record new movement |
| `/inventory/suppliers/` | `supplier_list` | Supplier directory |
| `/inventory/suppliers/<id>/` | `supplier_detail` | Supplier details and orders |
| `/inventory/purchase-orders/` | `purchase_order_list` | Purchase order list |
| `/inventory/purchase-orders/<id>/` | `purchase_order_detail` | PO details |
| `/inventory/alerts/` | `alerts` | Low stock and expired alerts |
| `/inventory/expiring/` | `expiring_items` | Items expiring soon |

### Dashboard Metrics

The dashboard displays:

- **Low stock count** - Items at or below minimum level
- **Expiring soon** - Items expiring within 30 days
- **Expired count** - Items past expiration date
- **Pending POs** - Purchase orders in progress
- **Recent movements** - Last 10 stock movements
- **Total stock value** - Sum of (quantity * unit_cost) for all batches

## Stock Management

### Recording Stock Receipt

```python
from apps.inventory.models import StockBatch, StockMovement, StockLevel
from decimal import Decimal

def receive_stock(product, location, quantity, batch_number, expiry_date,
                  unit_cost, supplier, purchase_order, user):
    """Receive stock from supplier."""

    # Create batch
    batch = StockBatch.objects.create(
        product=product,
        location=location,
        batch_number=batch_number,
        initial_quantity=quantity,
        current_quantity=quantity,
        expiry_date=expiry_date,
        received_date=timezone.now().date(),
        unit_cost=unit_cost,
        supplier=supplier,
        purchase_order=purchase_order,
        status='available'
    )

    # Update stock level
    stock_level, created = StockLevel.objects.get_or_create(
        product=product,
        location=location,
        defaults={'quantity': Decimal('0')}
    )
    stock_level.quantity += quantity
    stock_level.last_movement = timezone.now()
    stock_level.save()

    # Record movement
    StockMovement.objects.create(
        product=product,
        batch=batch,
        movement_type='receive',
        to_location=location,
        quantity=quantity,
        unit_cost=unit_cost,
        reference_type='purchase_order',
        reference_id=purchase_order.pk if purchase_order else None,
        recorded_by=user
    )

    return batch
```

### Recording Stock Sale/Dispense

```python
def dispense_stock(product, location, quantity, reference_type, reference_id, user):
    """Dispense stock using FEFO (First Expired, First Out)."""

    # Get available batches in FEFO order
    batches = StockBatch.objects.filter(
        product=product,
        location=location,
        status='available',
        current_quantity__gt=0
    ).order_by('expiry_date', 'received_date')

    remaining = quantity
    movements = []

    for batch in batches:
        if remaining <= 0:
            break

        take = min(batch.current_quantity, remaining)
        batch.current_quantity -= take

        if batch.current_quantity == 0:
            batch.status = 'depleted'
        batch.save()

        movements.append(StockMovement.objects.create(
            product=product,
            batch=batch,
            movement_type='dispense',
            from_location=location,
            quantity=take,
            reference_type=reference_type,
            reference_id=reference_id,
            recorded_by=user
        ))

        remaining -= take

    # Update stock level
    stock_level = StockLevel.objects.get(product=product, location=location)
    stock_level.quantity -= quantity
    stock_level.last_movement = timezone.now()
    stock_level.save()

    return movements
```

### Inter-Location Transfer

```python
def transfer_stock(product, from_location, to_location, quantity, batch, user, reason=''):
    """Transfer stock between locations."""

    # Deduct from source
    batch.current_quantity -= quantity
    batch.save()

    # Create or update batch at destination
    dest_batch, created = StockBatch.objects.get_or_create(
        product=product,
        location=to_location,
        batch_number=batch.batch_number,
        defaults={
            'initial_quantity': quantity,
            'current_quantity': quantity,
            'expiry_date': batch.expiry_date,
            'received_date': timezone.now().date(),
            'unit_cost': batch.unit_cost,
        }
    )
    if not created:
        dest_batch.current_quantity += quantity
        dest_batch.save()

    # Record movements
    StockMovement.objects.create(
        product=product,
        batch=batch,
        movement_type='transfer_out',
        from_location=from_location,
        quantity=quantity,
        reason=reason,
        recorded_by=user
    )

    StockMovement.objects.create(
        product=product,
        batch=dest_batch,
        movement_type='transfer_in',
        to_location=to_location,
        quantity=quantity,
        reason=reason,
        recorded_by=user
    )

    # Update stock levels
    from_level = StockLevel.objects.get(product=product, location=from_location)
    from_level.quantity -= quantity
    from_level.save()

    to_level, _ = StockLevel.objects.get_or_create(
        product=product, location=to_location,
        defaults={'quantity': Decimal('0')}
    )
    to_level.quantity += quantity
    to_level.save()
```

## Batch Tracking

### FEFO (First Expired, First Out)

Batches are ordered by expiry date for automatic FEFO dispensing:

```python
# Default ordering in model
class Meta:
    ordering = ['expiry_date', 'received_date']

# Query for dispensing
available_batches = StockBatch.objects.filter(
    product=product,
    location=location,
    status='available',
    current_quantity__gt=0
).order_by('expiry_date', 'received_date')  # FEFO order
```

### Expiration Alerts

```python
from datetime import timedelta
from django.utils import timezone

# Items expiring within 30 days
expiring_soon = StockBatch.objects.filter(
    expiry_date__lte=timezone.now().date() + timedelta(days=30),
    expiry_date__gt=timezone.now().date(),
    current_quantity__gt=0,
    status='available'
)

# Already expired
expired = StockBatch.objects.filter(
    expiry_date__lt=timezone.now().date(),
    current_quantity__gt=0,
    status='available'  # Should be updated to 'expired'
)
```

## Purchase Orders

### PO Lifecycle

```
┌─────────┐     ┌───────────┐     ┌───────────┐     ┌─────────┐
│  Draft  │────▶│ Submitted │────▶│ Confirmed │────▶│ Shipped │
└─────────┘     └───────────┘     └───────────┘     └─────────┘
                                                          │
                      ┌───────────┐                       │
                      │ Partially │◀──────────────────────┤
                      │ Received  │                       │
                      └───────────┘                       ▼
                            │                       ┌─────────┐
                            └──────────────────────▶│Received │
                                                    └─────────┘
```

### Creating a Purchase Order

```python
from apps.inventory.models import PurchaseOrder, PurchaseOrderLine

def create_purchase_order(supplier, items, location, user):
    """Create a new purchase order."""

    # Generate PO number
    last_po = PurchaseOrder.objects.order_by('-id').first()
    po_number = f"PO-{(last_po.id + 1) if last_po else 1:06d}"

    po = PurchaseOrder.objects.create(
        po_number=po_number,
        supplier=supplier,
        status='draft',
        delivery_location=location,
        created_by=user,
        subtotal=Decimal('0'),
        tax=Decimal('0'),
        total=Decimal('0')
    )

    subtotal = Decimal('0')
    for item in items:
        line_total = item['quantity'] * item['unit_cost']
        PurchaseOrderLine.objects.create(
            purchase_order=po,
            product=item['product'],
            quantity_ordered=item['quantity'],
            unit_cost=item['unit_cost'],
            line_total=line_total
        )
        subtotal += line_total

    po.subtotal = subtotal
    po.tax = subtotal * Decimal('0.16')  # 16% IVA
    po.total = po.subtotal + po.tax
    po.save()

    return po
```

## Reorder Rules

### Checking Reorder Points

```python
from apps.inventory.models import ReorderRule, StockLevel

def check_reorder_points():
    """Find products that need reordering."""

    needs_reorder = []

    for rule in ReorderRule.objects.filter(is_active=True).select_related('product'):
        if rule.location:
            levels = StockLevel.objects.filter(
                product=rule.product,
                location=rule.location
            )
        else:
            levels = StockLevel.objects.filter(product=rule.product)

        total_qty = sum(level.quantity for level in levels)

        if total_qty <= rule.reorder_point:
            needs_reorder.append({
                'product': rule.product,
                'current_qty': total_qty,
                'reorder_point': rule.reorder_point,
                'reorder_qty': rule.reorder_quantity,
                'preferred_supplier': rule.preferred_supplier,
                'auto_create_po': rule.auto_create_po
            })

    return needs_reorder
```

## Physical Inventory

### Creating a Stock Count

```python
from apps.inventory.models import StockCount, StockCountLine, StockLevel

def start_stock_count(location, count_type, user, product_filter=None):
    """Initialize a physical inventory count."""

    stock_count = StockCount.objects.create(
        location=location,
        count_date=timezone.now().date(),
        status='draft',
        count_type=count_type,
        product_filter=product_filter or {},
        counted_by=user
    )

    # Get products to count
    stock_levels = StockLevel.objects.filter(location=location)

    if product_filter:
        # Apply filters (category, etc.)
        pass

    for level in stock_levels:
        StockCountLine.objects.create(
            stock_count=stock_count,
            product=level.product,
            system_quantity=level.quantity
        )

    stock_count.total_products = stock_levels.count()
    stock_count.save()

    return stock_count
```

### Recording Count and Posting Adjustments

```python
def post_count_adjustments(stock_count, user):
    """Post inventory adjustments from count."""

    for line in stock_count.lines.filter(adjustment_posted=False):
        if line.counted_quantity is None:
            continue

        discrepancy = line.counted_quantity - line.system_quantity

        if discrepancy != 0:
            # Create adjustment movement
            movement_type = 'adjustment_add' if discrepancy > 0 else 'adjustment_remove'

            StockMovement.objects.create(
                product=line.product,
                movement_type=movement_type,
                to_location=stock_count.location if discrepancy > 0 else None,
                from_location=stock_count.location if discrepancy < 0 else None,
                quantity=abs(discrepancy),
                reason=f"Physical count adjustment: {line.adjustment_reason}",
                authorized_by=stock_count.approved_by,
                recorded_by=user
            )

            # Update stock level
            level = StockLevel.objects.get(
                product=line.product,
                location=stock_count.location
            )
            level.quantity = line.counted_quantity
            level.last_counted = timezone.now()
            level.save()

            line.adjustment_posted = True
            line.save()

    stock_count.status = 'posted'
    stock_count.save()
```

## Integration Points

### With Store/Orders

```python
# When order is placed, reserve stock
def reserve_for_order(order):
    for item in order.items.all():
        level = StockLevel.objects.get(
            product=item.product,
            location=default_location
        )
        level.reserved_quantity += item.quantity
        level.save()

# When order is fulfilled, dispense
def fulfill_order(order, user):
    for item in order.items.all():
        dispense_stock(
            product=item.product,
            location=default_location,
            quantity=item.quantity,
            reference_type='order',
            reference_id=order.pk,
            user=user
        )
```

### With Pharmacy/Prescriptions

```python
# When prescription is filled
def fill_prescription(prescription_fill, user):
    dispense_stock(
        product=prescription_fill.prescription.medication.product,
        location=pharmacy_location,
        quantity=prescription_fill.quantity_dispensed,
        reference_type='prescription',
        reference_id=prescription_fill.prescription.pk,
        user=user
    )
```

### With Audit Logging

Inventory pages are automatically audited:
- `/inventory/*` → `inventory.dashboard`, `inventory.stock`, etc.
- All paths logged with `sensitivity='normal'`

## Query Examples

### Low Stock Report

```python
from django.db.models import F

low_stock = StockLevel.objects.filter(
    quantity__lte=F('min_level')
).exclude(
    min_level__isnull=True
).select_related('product', 'location')
```

### Stock Valuation

```python
from django.db.models import Sum, F

total_value = StockBatch.objects.filter(
    status='available',
    current_quantity__gt=0
).aggregate(
    value=Sum(F('current_quantity') * F('unit_cost'))
)['value']
```

### Movement History for Product

```python
movements = StockMovement.objects.filter(
    product=product
).select_related(
    'batch', 'from_location', 'to_location', 'recorded_by'
).order_by('-created_at')
```

### Pending Purchase Orders by Supplier

```python
pending = PurchaseOrder.objects.filter(
    supplier=supplier,
    status__in=['submitted', 'confirmed', 'shipped']
).order_by('expected_date')
```

## Testing

### Unit Tests

Location: `tests/test_inventory.py`

```bash
python -m pytest tests/test_inventory.py -v
```

### Browser Tests

Location: `tests/e2e/browser/test_inventory.py`

```bash
python -m pytest tests/e2e/browser/test_inventory.py -v

# With visible browser
python -m pytest tests/e2e/browser/test_inventory.py -v --headed
```

### Test Coverage

Tests cover:
- Stock location CRUD
- Stock level tracking and calculations
- Batch creation and FEFO ordering
- Stock movements (all types)
- Supplier management
- Purchase order lifecycle
- Reorder rule evaluation
- Physical inventory counts
- Controlled substance logging
