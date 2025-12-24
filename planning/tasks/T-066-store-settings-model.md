# T-066: StoreSettings Model

> **STOP! READ THIS FIRST:**
> Before writing ANY code, complete the [TDD STOP GATE](../TDD_STOP_GATE.md)
>
> You must output the confirmation block and write failing tests
> BEFORE any implementation code.

---

**Story**: S-027 - Delivery Module Core
**Priority**: High
**Status**: Pending
**Estimate**: 2 hours

---

## Objective

Create a singleton StoreSettings model to store configurable store-wide settings including shipping cost, tax rate, and free shipping threshold.

---

## Required Reading

- [EPOCH_DELIVERY_MODULE.md](../EPOCH_DELIVERY_MODULE.md)
- [S-027-delivery-module.md](../stories/S-027-delivery-module.md)
- [TDD_STOP_GATE.md](../TDD_STOP_GATE.md)

---

## Test Cases

### Unit Tests (apps/store/tests.py)

```python
class StoreSettingsTests(TestCase):
    """Tests for StoreSettings singleton model."""

    def test_get_instance_creates_singleton(self):
        """get_instance should create settings if not exists."""
        settings = StoreSettings.get_instance()
        self.assertEqual(settings.pk, 1)
        self.assertEqual(StoreSettings.objects.count(), 1)

    def test_get_instance_returns_existing(self):
        """get_instance should return existing settings."""
        StoreSettings.objects.create(pk=1, default_shipping_cost=Decimal('100.00'))
        settings = StoreSettings.get_instance()
        self.assertEqual(settings.default_shipping_cost, Decimal('100.00'))
        self.assertEqual(StoreSettings.objects.count(), 1)

    def test_save_enforces_singleton(self):
        """Multiple saves should not create multiple records."""
        settings1 = StoreSettings.get_instance()
        settings1.default_shipping_cost = Decimal('75.00')
        settings1.save()

        settings2 = StoreSettings(default_shipping_cost=Decimal('80.00'))
        settings2.save()

        self.assertEqual(StoreSettings.objects.count(), 1)
        settings = StoreSettings.get_instance()
        self.assertEqual(settings.default_shipping_cost, Decimal('80.00'))

    def test_default_values(self):
        """Default values should be set correctly."""
        settings = StoreSettings.get_instance()
        self.assertEqual(settings.default_shipping_cost, Decimal('50.00'))
        self.assertEqual(settings.tax_rate, Decimal('0.16'))
        self.assertEqual(settings.default_max_order_quantity, 99)
        self.assertIsNone(settings.free_shipping_threshold)

    def test_free_shipping_applies_when_threshold_met(self):
        """Orders above threshold should get free shipping."""
        settings = StoreSettings.get_instance()
        settings.free_shipping_threshold = Decimal('500.00')
        settings.save()

        # Test helper method
        self.assertEqual(settings.get_shipping_cost(Decimal('400.00')), Decimal('50.00'))
        self.assertEqual(settings.get_shipping_cost(Decimal('500.00')), Decimal('0'))
        self.assertEqual(settings.get_shipping_cost(Decimal('600.00')), Decimal('0'))

    def test_free_shipping_disabled_when_threshold_null(self):
        """When threshold is null, always charge shipping."""
        settings = StoreSettings.get_instance()
        settings.free_shipping_threshold = None
        settings.save()

        self.assertEqual(settings.get_shipping_cost(Decimal('1000.00')), Decimal('50.00'))
```

---

## Implementation

### Model (apps/store/models.py)

```python
class StoreSettings(models.Model):
    """Store-wide configuration (singleton)."""

    default_shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('50.00'),
        help_text="Default shipping cost for delivery orders"
    )
    free_shipping_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Order subtotal for free shipping. Leave blank to disable."
    )
    tax_rate = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal('0.16'),
        help_text="Tax rate as decimal (e.g., 0.16 for 16%)"
    )
    default_max_order_quantity = models.PositiveIntegerField(
        default=99,
        help_text="Default max items per product per order"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Store Settings"
        verbose_name_plural = "Store Settings"

    def __str__(self):
        return "Store Settings"

    def save(self, *args, **kwargs):
        self.pk = 1  # Enforce singleton
        super().save(*args, **kwargs)

    @classmethod
    def get_instance(cls):
        """Get or create the singleton settings instance."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def get_shipping_cost(self, subtotal):
        """Calculate shipping cost based on subtotal and threshold."""
        if self.free_shipping_threshold and subtotal >= self.free_shipping_threshold:
            return Decimal('0')
        return self.default_shipping_cost
```

### Admin (apps/store/admin.py)

```python
@admin.register(StoreSettings)
class StoreSettingsAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'default_shipping_cost', 'tax_rate', 'updated_at']

    def has_add_permission(self, request):
        # Prevent adding more than one
        return not StoreSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
```

---

## Definition of Done

- [ ] StoreSettings model with all fields
- [ ] Singleton pattern enforced (save always uses pk=1)
- [ ] get_instance() classmethod
- [ ] get_shipping_cost() method with threshold logic
- [ ] Admin interface (no add/delete for singleton)
- [ ] Migration created and applied
- [ ] All tests pass (>95% coverage)

---

## Notes

- This model replaces the hardcoded $50 shipping cost in checkout
- Will be used by Order.create_from_cart() and checkout template
- Context processor will be added in T-073 for template access
