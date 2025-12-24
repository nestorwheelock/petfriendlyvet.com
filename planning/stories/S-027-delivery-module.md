# S-027: Delivery Module Core Infrastructure

**Story Type**: Epic / Feature
**Priority**: High
**Estimate**: 5 days
**Sprint**: Delivery Epoch Phase 1
**Status**: IN PROGRESS

---

## User Story

**As a** veterinary practice owner
**I want to** have a comprehensive delivery management system
**So that** I can track deliveries, manage drivers (employees and contractors), provide proof of delivery, and integrate with accounting

---

## Acceptance Criteria

### StoreSettings (Prerequisite)
- [ ] When I access admin, I can configure shipping cost
- [ ] When I configure free shipping threshold, orders above that amount get free shipping
- [ ] When I update tax rate, it reflects in checkout
- [ ] When I update max order quantity, it applies to all products without specific override

### Delivery Models
- [ ] When an order is placed with delivery, a Delivery record is created
- [ ] When a delivery status changes, a StatusHistory record is created
- [ ] When a driver uploads proof, photo and GPS coordinates are captured
- [ ] When a customer rates delivery, the rating is stored

### Driver Management
- [ ] When I add an employee driver, I can link to their StaffProfile
- [ ] When I add a contractor driver, I can link to their Vendor record
- [ ] When I add a contractor, I can record their RFC and CURP
- [ ] When I configure contractor rates, they apply to payment calculations

### Integration
- [ ] When checkout shows delivery option, shipping cost comes from StoreSettings
- [ ] When delivery is completed by contractor, a payable entry is created

---

## Definition of Done

- [ ] StoreSettings model implemented (T-066)
- [ ] All 8 delivery models implemented (T-067-T-071)
- [ ] Admin interfaces for all models (T-072)
- [ ] Checkout integration with StoreSettings (T-073)
- [ ] Tests written and passing (>95% coverage)
- [ ] Migrations created and applied
- [ ] Documentation updated

---

## Technical Notes

### StoreSettings Singleton Pattern
```python
class StoreSettings(models.Model):
    @classmethod
    def get_instance(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        self.pk = 1  # Force singleton
        super().save(*args, **kwargs)
```

### Delivery Status State Machine
```
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
```

### Driver Types
```python
DRIVER_TYPES = [
    ('employee', 'Clinic Employee'),
    ('contractor', 'Independent Contractor'),
]
```

---

## Related Tasks

| Task | Description | Status |
|------|-------------|--------|
| T-066 | StoreSettings model with tests | Pending |
| T-067 | Delivery app structure | Pending |
| T-068 | DeliveryZone and DeliverySlot models | Pending |
| T-069 | DeliveryDriver model | Pending |
| T-070 | Delivery model and status workflow | Pending |
| T-071 | Supporting models (Proof, Rating, etc.) | Pending |
| T-072 | Admin interfaces | Pending |
| T-073 | Checkout integration | Pending |

---

## Dependencies

- `apps/store` - Order model, checkout views
- `apps/practice` - StaffProfile for employee drivers
- `apps/accounting` - Vendor model for contractor integration
- `apps/communications` - Message model for notifications
