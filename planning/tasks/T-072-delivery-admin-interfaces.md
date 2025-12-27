# T-072: Delivery Admin Interfaces

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
**Dependencies**: T-071 (Supporting models)

---

## Objective

Create Django admin interfaces for all delivery models.

---

## Test Cases

```python
class DeliveryAdminTests(TestCase):
    """Tests for delivery admin interfaces."""

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            'admin', 'admin@test.com', 'password'
        )
        self.client.login(username='admin', password='password')

    def test_delivery_zone_admin_accessible(self):
        """DeliveryZone admin is accessible."""
        response = self.client.get('/admin/delivery/deliveryzone/')
        self.assertEqual(response.status_code, 200)

    def test_delivery_slot_admin_accessible(self):
        """DeliverySlot admin is accessible."""
        response = self.client.get('/admin/delivery/deliveryslot/')
        self.assertEqual(response.status_code, 200)

    def test_delivery_driver_admin_accessible(self):
        """DeliveryDriver admin is accessible."""
        response = self.client.get('/admin/delivery/deliverydriver/')
        self.assertEqual(response.status_code, 200)

    def test_delivery_admin_accessible(self):
        """Delivery admin is accessible."""
        response = self.client.get('/admin/delivery/delivery/')
        self.assertEqual(response.status_code, 200)

    def test_store_settings_admin_accessible(self):
        """StoreSettings admin is accessible."""
        response = self.client.get('/admin/store/storesettings/')
        self.assertEqual(response.status_code, 200)

    def test_store_settings_singleton(self):
        """StoreSettings admin prevents adding second instance."""
        StoreSettings.objects.create(pk=1)
        response = self.client.get('/admin/store/storesettings/add/')
        # Should redirect or show error since singleton exists
        self.assertIn(response.status_code, [302, 403])
```

---

## Implementation

### StoreSettings Admin (apps/store/admin.py)

```python
@admin.register(StoreSettings)
class StoreSettingsAdmin(admin.ModelAdmin):
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
            'fields': ('default_shipping_cost', 'free_shipping_threshold')
        }),
        ('Tax', {
            'fields': ('tax_rate',)
        }),
        ('Order Limits', {
            'fields': ('default_max_order_quantity',)
        }),
        ('Metadata', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        return not StoreSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
```

### Delivery Admin (apps/delivery/admin.py)

```python
@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'delivery_fee', 'estimated_time_minutes', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name']
    ordering = ['code']


@admin.register(DeliverySlot)
class DeliverySlotAdmin(admin.ModelAdmin):
    list_display = ['date', 'start_time', 'end_time', 'zone', 'capacity', 'booked_count', 'is_available']
    list_filter = ['zone', 'date', 'is_active']
    date_hierarchy = 'date'
    ordering = ['-date', 'start_time']


@admin.register(DeliveryDriver)
class DeliveryDriverAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'driver_type',
        'phone',
        'vehicle_type',
        'is_active',
        'is_available',
        'total_deliveries',
        'average_rating'
    ]
    list_filter = ['driver_type', 'is_active', 'is_available', 'vehicle_type']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'phone', 'rfc']
    filter_horizontal = ['zones']

    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'driver_type', 'phone')
        }),
        ('Employee Info', {
            'fields': ('staff_profile',),
            'classes': ('collapse',)
        }),
        ('Contractor Info', {
            'fields': ('vendor', 'rfc', 'curp', 'rate_per_delivery', 'rate_per_km'),
            'classes': ('collapse',)
        }),
        ('Onboarding Documents', {
            'fields': ('contract_signed', 'contract_document', 'id_document'),
            'classes': ('collapse',)
        }),
        ('Vehicle', {
            'fields': ('vehicle_type', 'license_plate')
        }),
        ('Zones', {
            'fields': ('zones',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_available')
        }),
        ('Performance', {
            'fields': ('total_deliveries', 'successful_deliveries', 'average_rating'),
            'classes': ('collapse',)
        }),
    )


class DeliveryStatusHistoryInline(admin.TabularInline):
    model = DeliveryStatusHistory
    extra = 0
    readonly_fields = ['from_status', 'to_status', 'changed_by', 'latitude', 'longitude', 'created_at']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class DeliveryProofInline(admin.TabularInline):
    model = DeliveryProof
    extra = 0
    readonly_fields = ['proof_type', 'image', 'latitude', 'longitude', 'created_at']


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = [
        'delivery_number',
        'order',
        'status',
        'driver',
        'zone',
        'scheduled_date',
        'created_at'
    ]
    list_filter = ['status', 'zone', 'driver', 'scheduled_date']
    search_fields = ['delivery_number', 'order__order_number', 'address']
    date_hierarchy = 'created_at'
    readonly_fields = ['delivery_number', 'created_at', 'updated_at']
    inlines = [DeliveryStatusHistoryInline, DeliveryProofInline]

    fieldsets = (
        ('Delivery Info', {
            'fields': ('delivery_number', 'order', 'status')
        }),
        ('Assignment', {
            'fields': ('driver', 'zone', 'slot')
        }),
        ('Address', {
            'fields': ('address', 'latitude', 'longitude')
        }),
        ('Schedule', {
            'fields': ('scheduled_date', 'scheduled_time_start', 'scheduled_time_end')
        }),
        ('Status Timestamps', {
            'fields': (
                'assigned_at', 'picked_up_at', 'out_for_delivery_at',
                'arrived_at', 'delivered_at', 'failed_at'
            ),
            'classes': ('collapse',)
        }),
        ('Failure', {
            'fields': ('failure_reason',),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes', 'driver_notes'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DeliveryRating)
class DeliveryRatingAdmin(admin.ModelAdmin):
    list_display = ['delivery', 'rating', 'driver_rating', 'timeliness_rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['delivery__delivery_number', 'feedback']


@admin.register(DeliveryNotification)
class DeliveryNotificationAdmin(admin.ModelAdmin):
    list_display = ['delivery', 'notification_type', 'channel', 'sent_at', 'failed']
    list_filter = ['notification_type', 'channel', 'failed']
    search_fields = ['delivery__delivery_number']
    date_hierarchy = 'sent_at'
```

---

## Definition of Done

- [ ] StoreSettingsAdmin with singleton enforcement
- [ ] DeliveryZoneAdmin with filters and search
- [ ] DeliverySlotAdmin with date hierarchy
- [ ] DeliveryDriverAdmin with fieldsets for employee/contractor
- [ ] DeliveryAdmin with inlines for history and proofs
- [ ] DeliveryRatingAdmin and DeliveryNotificationAdmin
- [ ] All tests pass
- [ ] Admin interfaces accessible and functional
