# T-068: DeliveryZone and DeliverySlot Models

> **REQUIRED READING:** Before implementation, review [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)

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
**Dependencies**: T-067 (Delivery app structure)

---

## Objective

Create DeliveryZone and DeliverySlot models for geographic zones and time slot management.

---

## Test Cases

```python
class DeliveryZoneTests(TestCase):
    """Tests for DeliveryZone model."""

    def test_create_zone(self):
        """Can create a delivery zone."""
        zone = DeliveryZone.objects.create(
            code='CENTRO',
            name='Centro Historico',
            delivery_fee=Decimal('50.00'),
            estimated_time_minutes=30
        )
        self.assertEqual(zone.code, 'CENTRO')
        self.assertTrue(zone.is_active)

    def test_zone_str(self):
        """Zone string representation."""
        zone = DeliveryZone.objects.create(code='NORTE', name='Zona Norte')
        self.assertEqual(str(zone), 'NORTE - Zona Norte')

    def test_zone_unique_code(self):
        """Zone codes must be unique."""
        DeliveryZone.objects.create(code='CENTRO', name='Centro')
        with self.assertRaises(IntegrityError):
            DeliveryZone.objects.create(code='CENTRO', name='Centro 2')


class DeliverySlotTests(TestCase):
    """Tests for DeliverySlot model."""

    def setUp(self):
        self.zone = DeliveryZone.objects.create(
            code='CENTRO',
            name='Centro',
            delivery_fee=Decimal('50.00')
        )

    def test_create_slot(self):
        """Can create a delivery slot."""
        from datetime import date, time
        slot = DeliverySlot.objects.create(
            zone=self.zone,
            date=date.today(),
            start_time=time(9, 0),
            end_time=time(12, 0),
            capacity=5
        )
        self.assertEqual(slot.booked_count, 0)
        self.assertEqual(slot.available_capacity, 5)

    def test_slot_availability(self):
        """Slot reports correct availability."""
        from datetime import date, time
        slot = DeliverySlot.objects.create(
            zone=self.zone,
            date=date.today(),
            start_time=time(9, 0),
            end_time=time(12, 0),
            capacity=2,
            booked_count=1
        )
        self.assertEqual(slot.available_capacity, 1)
        self.assertTrue(slot.is_available)

    def test_slot_full(self):
        """Full slot reports not available."""
        from datetime import date, time
        slot = DeliverySlot.objects.create(
            zone=self.zone,
            date=date.today(),
            start_time=time(9, 0),
            end_time=time(12, 0),
            capacity=2,
            booked_count=2
        )
        self.assertFalse(slot.is_available)

    def test_slot_str(self):
        """Slot string representation."""
        from datetime import date, time
        slot = DeliverySlot.objects.create(
            zone=self.zone,
            date=date(2024, 12, 25),
            start_time=time(9, 0),
            end_time=time(12, 0),
            capacity=5
        )
        self.assertIn('2024-12-25', str(slot))
        self.assertIn('09:00', str(slot))
```

---

## Implementation

### Models

```python
class DeliveryZone(models.Model):
    """Geographic delivery zone with specific fees and ETAs."""

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    name_es = models.CharField(max_length=100, blank=True)
    delivery_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('50.00')
    )
    estimated_time_minutes = models.PositiveIntegerField(
        default=45,
        help_text="Estimated delivery time in minutes"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class DeliverySlot(models.Model):
    """Time slot for delivery scheduling."""

    zone = models.ForeignKey(
        DeliveryZone,
        on_delete=models.CASCADE,
        related_name='slots'
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    capacity = models.PositiveIntegerField(default=5)
    booked_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'start_time']
        unique_together = ['zone', 'date', 'start_time']

    def __str__(self):
        return f"{self.date} {self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')} ({self.zone.code})"

    @property
    def available_capacity(self):
        return max(0, self.capacity - self.booked_count)

    @property
    def is_available(self):
        return self.is_active and self.available_capacity > 0
```

---

## Definition of Done

- [ ] DeliveryZone model with all fields
- [ ] DeliverySlot model with all fields
- [ ] Unique constraints enforced
- [ ] available_capacity and is_available properties
- [ ] All tests pass (>95% coverage)
- [ ] Migration created
