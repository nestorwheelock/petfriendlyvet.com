# T-069: DeliveryDriver Model

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
**Dependencies**: T-068 (Zone/Slot models)

---

## Objective

Create DeliveryDriver model supporting both employee and contractor drivers, with RFC/CURP for contractors and A/P integration.

---

## Test Cases

```python
class DeliveryDriverTests(TestCase):
    """Tests for DeliveryDriver model."""

    def test_create_employee_driver(self):
        """Can create an employee driver."""
        user = User.objects.create_user('driver1', 'driver1@test.com', 'pass')
        driver = DeliveryDriver.objects.create(
            user=user,
            driver_type='employee',
            phone='+525551234567'
        )
        self.assertEqual(driver.driver_type, 'employee')
        self.assertTrue(driver.is_employee)
        self.assertFalse(driver.is_contractor)

    def test_create_contractor_driver(self):
        """Can create a contractor driver with RFC/CURP."""
        user = User.objects.create_user('driver2', 'driver2@test.com', 'pass')
        driver = DeliveryDriver.objects.create(
            user=user,
            driver_type='contractor',
            phone='+525551234567',
            rfc='XAXX010101000',
            curp='XEXX010101HNEXXXA4',
            rate_per_delivery=Decimal('35.00')
        )
        self.assertEqual(driver.driver_type, 'contractor')
        self.assertTrue(driver.is_contractor)
        self.assertFalse(driver.is_employee)
        self.assertEqual(driver.rfc, 'XAXX010101000')

    def test_driver_zones_relationship(self):
        """Driver can be assigned to multiple zones."""
        user = User.objects.create_user('driver3', 'driver3@test.com', 'pass')
        driver = DeliveryDriver.objects.create(user=user, driver_type='employee')

        zone1 = DeliveryZone.objects.create(code='CENTRO', name='Centro')
        zone2 = DeliveryZone.objects.create(code='NORTE', name='Norte')

        driver.zones.add(zone1, zone2)
        self.assertEqual(driver.zones.count(), 2)

    def test_driver_availability(self):
        """Driver availability status."""
        user = User.objects.create_user('driver4', 'driver4@test.com', 'pass')
        driver = DeliveryDriver.objects.create(
            user=user,
            driver_type='employee',
            is_active=True,
            is_available=True
        )
        self.assertTrue(driver.is_active)
        self.assertTrue(driver.is_available)

    def test_contractor_requires_payment_info(self):
        """Contractor validation warns if no payment info."""
        user = User.objects.create_user('driver5', 'driver5@test.com', 'pass')
        driver = DeliveryDriver.objects.create(
            user=user,
            driver_type='contractor'
        )
        # Should have warning/validation method
        self.assertFalse(driver.has_complete_payment_info)

    def test_driver_str(self):
        """Driver string representation."""
        user = User.objects.create_user(
            'driver6', 'driver6@test.com', 'pass',
            first_name='Juan', last_name='Garcia'
        )
        driver = DeliveryDriver.objects.create(user=user, driver_type='employee')
        self.assertIn('Juan Garcia', str(driver))
```

---

## Implementation

### Model

```python
DRIVER_TYPES = [
    ('employee', 'Clinic Employee'),
    ('contractor', 'Independent Contractor'),
]

VEHICLE_TYPES = [
    ('motorcycle', 'Motorcycle'),
    ('car', 'Car'),
    ('bicycle', 'Bicycle'),
    ('walk', 'On Foot'),
]

class DeliveryDriver(models.Model):
    """Driver profile for deliveries."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='delivery_driver'
    )
    driver_type = models.CharField(
        max_length=20,
        choices=DRIVER_TYPES,
        default='employee'
    )
    phone = models.CharField(max_length=20, blank=True)

    # Employee fields
    staff_profile = models.ForeignKey(
        'practice.StaffProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delivery_driver'
    )

    # Contractor fields (A/P integration)
    vendor = models.ForeignKey(
        'accounting.Vendor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delivery_drivers'
    )

    # Mexican tax IDs (required for contractors)
    rfc = models.CharField(max_length=13, blank=True, help_text="RFC (Tax ID)")
    curp = models.CharField(max_length=18, blank=True, help_text="CURP (Personal ID)")

    # Payment rates for contractors
    rate_per_delivery = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    rate_per_km = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Contractor onboarding
    contract_signed = models.BooleanField(default=False)
    contract_document = models.FileField(
        upload_to='driver_contracts/',
        null=True,
        blank=True
    )
    id_document = models.FileField(
        upload_to='driver_ids/',
        null=True,
        blank=True
    )

    # Vehicle info
    vehicle_type = models.CharField(
        max_length=20,
        choices=VEHICLE_TYPES,
        default='motorcycle'
    )
    license_plate = models.CharField(max_length=20, blank=True)

    # Zones this driver covers
    zones = models.ManyToManyField(
        DeliveryZone,
        blank=True,
        related_name='drivers'
    )

    # Status
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=False)

    # Performance metrics
    total_deliveries = models.PositiveIntegerField(default=0)
    successful_deliveries = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal('5.00')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_available', 'user__first_name']

    def __str__(self):
        name = self.user.get_full_name() or self.user.username
        return f"{name} ({self.get_driver_type_display()})"

    @property
    def is_employee(self):
        return self.driver_type == 'employee'

    @property
    def is_contractor(self):
        return self.driver_type == 'contractor'

    @property
    def has_complete_payment_info(self):
        """Check if contractor has complete payment info."""
        if self.is_employee:
            return True
        return bool(self.rfc and self.rate_per_delivery and self.vendor)
```

---

## Definition of Done

- [ ] DeliveryDriver model with all fields
- [ ] Support for employee and contractor types
- [ ] RFC/CURP fields for contractors
- [ ] Payment rate fields for contractors
- [ ] Zone relationship (M2M)
- [ ] Properties: is_employee, is_contractor, has_complete_payment_info
- [ ] All tests pass (>95% coverage)
- [ ] Migration created
