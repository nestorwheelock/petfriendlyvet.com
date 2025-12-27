# T-076: Inventory App Staff-Facing URLs

> **REQUIRED READING:** Before implementation, review [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)

**Story Type**: Task
**Priority**: High (Operations)
**Estimate**: 6 hours
**Status**: Pending
**Discovered By**: QA Browser Tests (2025-12-25)

## Objective

Create staff-facing views and URLs for the Inventory app so clinic staff can manage inventory efficiently without using the Django admin interface.

## Background

Browser E2E tests revealed that the Inventory app only has Django admin interfaces. Staff must use admin for all inventory tasks, which is slow and not optimized for daily operations. They need:
- Quick stock overview dashboard
- Low stock alerts
- Purchase order management
- Batch tracking
- Expiry monitoring
- Movement logging
- Supplier directory

## Required URLs (Staff-facing)

| URL | View | Description |
|-----|------|-------------|
| `/inventory/` | `dashboard` | Stock overview, alerts |
| `/inventory/alerts/` | `low_stock_alerts` | Items below reorder point |
| `/inventory/purchase-orders/` | `po_list` | Purchase orders |
| `/inventory/batches/` | `batch_list` | Stock batches |
| `/inventory/expiring/` | `expiring_soon` | Batches expiring soon |
| `/inventory/movements/` | `movement_log` | Stock movement history |
| `/inventory/suppliers/` | `supplier_list` | Supplier directory |

## Deliverables

### Files to Create
- [ ] `apps/inventory/urls.py` - URL patterns
- [ ] `apps/inventory/views.py` - View functions/classes
- [ ] `templates/inventory/dashboard.html` - Main dashboard
- [ ] `templates/inventory/alerts.html` - Low stock alerts
- [ ] `templates/inventory/purchase_orders.html` - PO management
- [ ] `templates/inventory/batches.html` - Batch list
- [ ] `templates/inventory/expiring.html` - Expiring items
- [ ] `templates/inventory/movements.html` - Movement log
- [ ] `templates/inventory/suppliers.html` - Supplier directory

### Files to Modify
- [ ] `config/urls.py` - Include inventory URLs

## Definition of Done

- [ ] All 7 URLs accessible to staff users only
- [ ] Dashboard shows StockLevel summary
- [ ] Alerts use ReorderRule thresholds
- [ ] PO list shows PurchaseOrder records
- [ ] Batch list shows StockBatch with lot numbers
- [ ] Expiring view filters by expiry date
- [ ] Movements show StockMovement audit trail
- [ ] Suppliers show Supplier directory
- [ ] Tests written with >95% coverage
- [ ] Browser tests updated to validate staff URLs
- [ ] Mobile-responsive templates

## Technical Notes

- Use existing models: `StockLocation`, `StockLevel`, `PurchaseOrder`, `StockBatch`, `StockMovement`, `Supplier`, `ReorderRule`
- All views require @staff_member_required decorator
- Dashboard should show counts for alerts
- Consider filtering and sorting for lists
- Expiring view should highlight urgency levels

## Related

- QA Discovery: `planning/issues/MISSING_CUSTOMER_URLS.md`
- Existing models: `apps/inventory/models.py`
- Existing admin: `apps/inventory/admin.py`
