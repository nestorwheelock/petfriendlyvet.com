# T-041: Inventory Management

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement comprehensive inventory tracking system
**Related Story**: S-024
**Epoch**: 3
**Estimate**: 4 hours

### Constraints
**Allowed File Paths**: apps/inventory/
**Forbidden Paths**: None

### Deliverables
- [ ] StockLevel model
- [ ] StockMovement model
- [ ] Batch/lot tracking
- [ ] Expiry management
- [ ] Reorder alerts
- [ ] Stock counts

### Implementation Details

#### Models
```python
class Supplier(models.Model):
    """Product supplier."""

    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)

    # Contact
    contact_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    # Terms
    payment_terms = models.CharField(max_length=50, default='net30')
    lead_time_days = models.IntegerField(default=7)
    minimum_order = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)


class StockLocation(models.Model):
    """Physical location for inventory."""

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)


class StockLevel(models.Model):
    """Current stock level by product and location."""

    product = models.ForeignKey('store.Product', on_delete=models.CASCADE, related_name='stock_levels')
    variant = models.ForeignKey('store.ProductVariant', on_delete=models.CASCADE, null=True, blank=True)
    location = models.ForeignKey(StockLocation, on_delete=models.CASCADE)

    quantity = models.IntegerField(default=0)
    reserved_quantity = models.IntegerField(default=0)  # For pending orders

    # Thresholds
    reorder_point = models.IntegerField(default=5)
    reorder_quantity = models.IntegerField(default=10)

    last_counted = models.DateTimeField(null=True)
    last_movement = models.DateTimeField(null=True)

    class Meta:
        unique_together = ['product', 'variant', 'location']

    @property
    def available_quantity(self):
        return self.quantity - self.reserved_quantity

    @property
    def needs_reorder(self):
        return self.available_quantity <= self.reorder_point


class StockBatch(models.Model):
    """Batch/lot tracking for products."""

    product = models.ForeignKey('store.Product', on_delete=models.CASCADE, related_name='batches')
    variant = models.ForeignKey('store.ProductVariant', on_delete=models.CASCADE, null=True, blank=True)
    location = models.ForeignKey(StockLocation, on_delete=models.CASCADE)

    batch_number = models.CharField(max_length=100)
    lot_number = models.CharField(max_length=100, blank=True)

    quantity = models.IntegerField()
    expiry_date = models.DateField(null=True, blank=True)
    manufacture_date = models.DateField(null=True, blank=True)

    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True)
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    received_date = models.DateField()
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['expiry_date', 'received_date']  # FEFO

    @property
    def is_expired(self):
        return self.expiry_date and self.expiry_date < timezone.now().date()

    @property
    def days_until_expiry(self):
        if not self.expiry_date:
            return None
        return (self.expiry_date - timezone.now().date()).days


class StockMovement(models.Model):
    """Record of stock changes."""

    MOVEMENT_TYPES = [
        ('receive', 'Received'),
        ('sale', 'Sale'),
        ('return', 'Customer Return'),
        ('adjustment_plus', 'Adjustment (+)'),
        ('adjustment_minus', 'Adjustment (-)'),
        ('transfer', 'Transfer'),
        ('damage', 'Damaged'),
        ('expired', 'Expired'),
        ('count', 'Stock Count'),
    ]

    product = models.ForeignKey('store.Product', on_delete=models.CASCADE, related_name='stock_movements')
    variant = models.ForeignKey('store.ProductVariant', on_delete=models.CASCADE, null=True, blank=True)
    location = models.ForeignKey(StockLocation, on_delete=models.CASCADE)
    batch = models.ForeignKey(StockBatch, on_delete=models.SET_NULL, null=True, blank=True)

    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()  # Positive for in, negative for out
    balance_after = models.IntegerField()

    # References
    order = models.ForeignKey('store.Order', on_delete=models.SET_NULL, null=True, blank=True)
    purchase_order = models.ForeignKey('PurchaseOrder', on_delete=models.SET_NULL, null=True, blank=True)
    stock_count = models.ForeignKey('StockCount', on_delete=models.SET_NULL, null=True, blank=True)
    transfer_to = models.ForeignKey(StockLocation, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']


class PurchaseOrder(models.Model):
    """Purchase order for restocking."""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('confirmed', 'Confirmed'),
        ('partial', 'Partially Received'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]

    order_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    order_date = models.DateField()
    expected_date = models.DateField(null=True)
    received_date = models.DateField(null=True)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class PurchaseOrderItem(models.Model):
    """Item in purchase order."""

    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('store.Product', on_delete=models.PROTECT)
    variant = models.ForeignKey('store.ProductVariant', on_delete=models.SET_NULL, null=True, blank=True)

    quantity_ordered = models.IntegerField()
    quantity_received = models.IntegerField(default=0)

    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)


class StockCount(models.Model):
    """Physical inventory count."""

    location = models.ForeignKey(StockLocation, on_delete=models.CASCADE)
    count_date = models.DateField()
    counted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    status = models.CharField(max_length=20, choices=[
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], default='in_progress')

    notes = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True)


class StockCountLine(models.Model):
    """Individual product count in stock count."""

    count = models.ForeignKey(StockCount, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey('store.Product', on_delete=models.CASCADE)
    variant = models.ForeignKey('store.ProductVariant', on_delete=models.CASCADE, null=True, blank=True)

    expected_quantity = models.IntegerField()
    counted_quantity = models.IntegerField(null=True)
    variance = models.IntegerField(null=True)

    notes = models.TextField(blank=True)
```

#### Inventory Service
```python
class InventoryService:
    """Inventory management operations."""

    def receive_stock(
        self,
        product: Product,
        quantity: int,
        location: StockLocation,
        batch_info: dict = None,
        purchase_order: PurchaseOrder = None,
        user: User = None
    ) -> StockMovement:
        """Receive stock from supplier."""

        # Create batch if provided
        batch = None
        if batch_info:
            batch = StockBatch.objects.create(
                product=product,
                location=location,
                quantity=quantity,
                **batch_info
            )

        # Update stock level
        stock_level, _ = StockLevel.objects.get_or_create(
            product=product,
            variant=None,
            location=location
        )
        stock_level.quantity += quantity
        stock_level.last_movement = timezone.now()
        stock_level.save()

        # Record movement
        return StockMovement.objects.create(
            product=product,
            location=location,
            batch=batch,
            movement_type='receive',
            quantity=quantity,
            balance_after=stock_level.quantity,
            purchase_order=purchase_order,
            recorded_by=user
        )

    def get_expiring_products(self, days_ahead: int = 30) -> QuerySet:
        """Get products expiring soon."""
        threshold = timezone.now().date() + timedelta(days=days_ahead)
        return StockBatch.objects.filter(
            expiry_date__lte=threshold,
            expiry_date__gt=timezone.now().date(),
            quantity__gt=0
        ).select_related('product').order_by('expiry_date')

    def generate_reorder_list(self) -> list:
        """Generate list of products needing reorder."""
        return StockLevel.objects.filter(
            quantity__lte=F('reorder_point'),
            product__is_active=True
        ).select_related('product', 'location')
```

### Test Cases
- [ ] Stock levels track correctly
- [ ] Batches created on receive
- [ ] Movements logged
- [ ] Expiry dates tracked
- [ ] Reorder alerts work
- [ ] Stock counts reconcile
- [ ] Purchase orders flow

### Definition of Done
- [ ] All models migrated
- [ ] FEFO ordering works
- [ ] Expiry alerts functional
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-036: Product & Category Models
