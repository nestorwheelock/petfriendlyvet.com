# T-070: Delivery Model and Status Workflow

> **STOP! READ THIS FIRST:**
> Before writing ANY code, complete the [TDD STOP GATE](../TDD_STOP_GATE.md)
>
> You must output the confirmation block and write failing tests
> BEFORE any implementation code.

---

**Story**: S-027 - Delivery Module Core
**Priority**: High
**Status**: Pending
**Estimate**: 3 hours
**Dependencies**: T-069 (DeliveryDriver model)

---

## Objective

Create the main Delivery model with status workflow, linking orders to delivery execution.

---

## Status Workflow

```
pending → assigned → picked_up → out_for_delivery → arrived → delivered
                                                           ↘ failed → returned
```

Valid transitions:
- pending → assigned
- assigned → picked_up, pending (unassign)
- picked_up → out_for_delivery
- out_for_delivery → arrived, failed
- arrived → delivered, failed
- failed → returned, assigned (retry)
- returned → (terminal)
- delivered → (terminal)

---

## Test Cases

```python
class DeliveryTests(TestCase):
    """Tests for Delivery model."""

    def setUp(self):
        self.user = User.objects.create_user('customer', 'c@test.com', 'pass')
        self.category = Category.objects.create(name='Test', slug='test')
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            category=self.category,
            price=Decimal('100.00')
        )
        self.cart = Cart.objects.create(user=self.user)
        self.cart.add_item(self.product, 1)
        self.order = Order.create_from_cart(
            cart=self.cart,
            user=self.user,
            fulfillment_method='delivery',
            shipping_address='Test Address'
        )
        self.zone = DeliveryZone.objects.create(code='CENTRO', name='Centro')

    def test_create_delivery_from_order(self):
        """Can create delivery from order."""
        delivery = Delivery.objects.create(
            order=self.order,
            zone=self.zone,
            address=self.order.shipping_address
        )
        self.assertEqual(delivery.status, 'pending')
        self.assertIsNotNone(delivery.delivery_number)

    def test_delivery_number_generation(self):
        """Delivery number is generated automatically."""
        delivery = Delivery.objects.create(
            order=self.order,
            zone=self.zone
        )
        self.assertTrue(delivery.delivery_number.startswith('DEL-'))

    def test_status_transition_assign(self):
        """Can transition from pending to assigned."""
        driver_user = User.objects.create_user('driver', 'd@test.com', 'pass')
        driver = DeliveryDriver.objects.create(user=driver_user)

        delivery = Delivery.objects.create(order=self.order, zone=self.zone)
        delivery.assign_driver(driver)

        self.assertEqual(delivery.status, 'assigned')
        self.assertEqual(delivery.driver, driver)

    def test_status_transition_pickup(self):
        """Can transition from assigned to picked_up."""
        driver_user = User.objects.create_user('driver', 'd@test.com', 'pass')
        driver = DeliveryDriver.objects.create(user=driver_user)

        delivery = Delivery.objects.create(order=self.order, zone=self.zone)
        delivery.assign_driver(driver)
        delivery.mark_picked_up()

        self.assertEqual(delivery.status, 'picked_up')
        self.assertIsNotNone(delivery.picked_up_at)

    def test_status_transition_out_for_delivery(self):
        """Can transition to out_for_delivery."""
        driver_user = User.objects.create_user('driver', 'd@test.com', 'pass')
        driver = DeliveryDriver.objects.create(user=driver_user)

        delivery = Delivery.objects.create(order=self.order, zone=self.zone)
        delivery.assign_driver(driver)
        delivery.mark_picked_up()
        delivery.mark_out_for_delivery()

        self.assertEqual(delivery.status, 'out_for_delivery')
        self.assertIsNotNone(delivery.out_for_delivery_at)

    def test_status_transition_delivered(self):
        """Can transition to delivered."""
        driver_user = User.objects.create_user('driver', 'd@test.com', 'pass')
        driver = DeliveryDriver.objects.create(user=driver_user)

        delivery = Delivery.objects.create(order=self.order, zone=self.zone)
        delivery.assign_driver(driver)
        delivery.mark_picked_up()
        delivery.mark_out_for_delivery()
        delivery.mark_arrived()
        delivery.mark_delivered()

        self.assertEqual(delivery.status, 'delivered')
        self.assertIsNotNone(delivery.delivered_at)

    def test_invalid_transition_raises_error(self):
        """Invalid status transition raises error."""
        delivery = Delivery.objects.create(order=self.order, zone=self.zone)

        with self.assertRaises(ValueError):
            delivery.mark_picked_up()  # Can't pickup without assignment

    def test_status_history_created(self):
        """Status changes create history records."""
        driver_user = User.objects.create_user('driver', 'd@test.com', 'pass')
        driver = DeliveryDriver.objects.create(user=driver_user)

        delivery = Delivery.objects.create(order=self.order, zone=self.zone)
        delivery.assign_driver(driver)

        self.assertEqual(delivery.status_history.count(), 1)
        history = delivery.status_history.first()
        self.assertEqual(history.from_status, 'pending')
        self.assertEqual(history.to_status, 'assigned')
```

---

## Implementation

### Model

```python
DELIVERY_STATUSES = [
    ('pending', 'Pending'),
    ('assigned', 'Assigned'),
    ('picked_up', 'Picked Up'),
    ('out_for_delivery', 'Out for Delivery'),
    ('arrived', 'Arrived'),
    ('delivered', 'Delivered'),
    ('failed', 'Failed'),
    ('returned', 'Returned'),
]

VALID_TRANSITIONS = {
    'pending': ['assigned'],
    'assigned': ['picked_up', 'pending'],
    'picked_up': ['out_for_delivery'],
    'out_for_delivery': ['arrived', 'failed'],
    'arrived': ['delivered', 'failed'],
    'failed': ['returned', 'assigned'],
    'returned': [],
    'delivered': [],
}


class Delivery(models.Model):
    """Main delivery record linking order to execution."""

    delivery_number = models.CharField(max_length=20, unique=True, editable=False)
    order = models.OneToOneField(
        'store.Order',
        on_delete=models.CASCADE,
        related_name='delivery'
    )
    driver = models.ForeignKey(
        DeliveryDriver,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deliveries'
    )
    slot = models.ForeignKey(
        DeliverySlot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deliveries'
    )
    zone = models.ForeignKey(
        DeliveryZone,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deliveries'
    )

    status = models.CharField(
        max_length=20,
        choices=DELIVERY_STATUSES,
        default='pending'
    )

    # Address
    address = models.TextField(blank=True)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )

    # Scheduling
    scheduled_date = models.DateField(null=True, blank=True)
    scheduled_time_start = models.TimeField(null=True, blank=True)
    scheduled_time_end = models.TimeField(null=True, blank=True)

    # Status timestamps
    assigned_at = models.DateTimeField(null=True, blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    out_for_delivery_at = models.DateTimeField(null=True, blank=True)
    arrived_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)

    # Failure info
    failure_reason = models.TextField(blank=True)

    # Notes
    notes = models.TextField(blank=True)
    driver_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.delivery_number

    def save(self, *args, **kwargs):
        if not self.delivery_number:
            self.delivery_number = self._generate_delivery_number()
        super().save(*args, **kwargs)

    def _generate_delivery_number(self):
        """Generate unique delivery number."""
        from datetime import datetime
        prefix = datetime.now().strftime('DEL-%Y-%m')
        last = Delivery.objects.filter(
            delivery_number__startswith=prefix
        ).order_by('-delivery_number').first()

        if last:
            last_num = int(last.delivery_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        return f"{prefix}-{new_num:05d}"

    def _change_status(self, new_status, changed_by=None, latitude=None, longitude=None):
        """Change status with validation and history."""
        if new_status not in VALID_TRANSITIONS.get(self.status, []):
            raise ValueError(
                f"Cannot transition from {self.status} to {new_status}"
            )

        old_status = self.status
        self.status = new_status

        # Update timestamp
        now = timezone.now()
        timestamp_field = f"{new_status}_at"
        if hasattr(self, timestamp_field):
            setattr(self, timestamp_field, now)

        self.save()

        # Create history
        DeliveryStatusHistory.objects.create(
            delivery=self,
            from_status=old_status,
            to_status=new_status,
            changed_by=changed_by,
            latitude=latitude,
            longitude=longitude
        )

    def assign_driver(self, driver, assigned_by=None):
        """Assign driver to delivery."""
        self.driver = driver
        self._change_status('assigned', assigned_by)

    def mark_picked_up(self, changed_by=None, latitude=None, longitude=None):
        self._change_status('picked_up', changed_by, latitude, longitude)

    def mark_out_for_delivery(self, changed_by=None, latitude=None, longitude=None):
        self._change_status('out_for_delivery', changed_by, latitude, longitude)

    def mark_arrived(self, changed_by=None, latitude=None, longitude=None):
        self._change_status('arrived', changed_by, latitude, longitude)

    def mark_delivered(self, changed_by=None, latitude=None, longitude=None):
        self._change_status('delivered', changed_by, latitude, longitude)

    def mark_failed(self, reason, changed_by=None, latitude=None, longitude=None):
        self.failure_reason = reason
        self._change_status('failed', changed_by, latitude, longitude)


class DeliveryStatusHistory(models.Model):
    """Audit trail for delivery status changes."""

    delivery = models.ForeignKey(
        Delivery,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    from_status = models.CharField(max_length=20, choices=DELIVERY_STATUSES)
    to_status = models.CharField(max_length=20, choices=DELIVERY_STATUSES)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.delivery}: {self.from_status} → {self.to_status}"
```

---

## Definition of Done

- [ ] Delivery model with all fields
- [ ] DeliveryStatusHistory model
- [ ] Status workflow with valid transitions
- [ ] Transition methods (assign_driver, mark_*, etc.)
- [ ] Automatic delivery number generation
- [ ] History records created on status change
- [ ] All tests pass (>95% coverage)
- [ ] Migrations created
