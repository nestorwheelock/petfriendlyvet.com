# I-001: Editable Cart Quantity with Max Limit

**Type**: Enhancement
**Priority**: Medium
**Status**: COMPLETED

## Description

The cart quantity should be an editable input field that allows users to type a specific quantity directly, rather than only using +/- buttons. The quantity should not exceed a configurable maximum set per product.

## Requirements

### 1. Editable Quantity Input
- Replace the quantity display `<span>` with an `<input type="number">`
- Allow users to type a quantity directly
- Submit on blur or Enter key
- Minimum value: 1

### 2. Global Default Max Quantity (Settings)
- Add `STORE_DEFAULT_MAX_ORDER_QUANTITY` to Django settings
- Default value: 99
- Used when product doesn't specify its own limit

### 3. Per-Product Maximum Quantity Override
- Add `max_order_quantity` field to Product model
- Nullable - when null, uses global default from settings
- Validate quantity does not exceed this limit in:
  - Cart template (HTML `max` attribute)
  - Cart update view (server-side validation)
  - Add to cart view (server-side validation)

### 4. User Feedback
- Show error message if user tries to exceed max
- Consider showing max available: "Max: 10 per order"

## Technical Implementation

### Settings Changes
```python
# config/settings/base.py

# Store Configuration
STORE_DEFAULT_MAX_ORDER_QUANTITY = 99  # Default max items per product per order
```

### Model Changes
```python
# apps/store/models.py
from django.conf import settings

class Product(models.Model):
    # ... existing fields ...
    max_order_quantity = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum quantity per order. Leave blank to use default from settings."
    )

    def get_max_order_quantity(self):
        """Return max order quantity, falling back to settings default."""
        if self.max_order_quantity is not None:
            return self.max_order_quantity
        return getattr(settings, 'STORE_DEFAULT_MAX_ORDER_QUANTITY', 99)
```

### Template Changes
```html
<!-- Replace span with input -->
<input type="number"
       name="quantity"
       value="{{ item.quantity }}"
       min="1"
       max="{{ item.product.get_max_order_quantity }}"
       class="w-16 text-center border rounded">
```

### View Changes
```python
def update_cart(request):
    # ... existing code ...
    max_qty = product.get_max_order_quantity()
    if quantity > max_qty:
        messages.error(request, f'Maximum {max_qty} per order.')
        quantity = max_qty
    # ... continue ...
```

## Acceptance Criteria

- [x] `STORE_DEFAULT_MAX_ORDER_QUANTITY` setting added (default: 99)
- [x] Product model has nullable `max_order_quantity` field
- [x] Product model has `get_max_order_quantity()` method
- [x] Quantity field is editable (type="number")
- [x] Field has min=1 enforced
- [x] Field has max from `product.get_max_order_quantity()`
- [x] Server validates max quantity on update
- [x] Server validates max quantity on add to cart
- [x] +/- buttons still work alongside input
- [x] Error message shown when max exceeded
- [x] Migration created for new field

## Notes

- Consider stock_quantity as another limit (can't order more than in stock)
- The two limits should work together: `min(max_order_quantity, stock_quantity)`
