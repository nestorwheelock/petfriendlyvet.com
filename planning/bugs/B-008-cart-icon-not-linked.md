# B-008: Cart Icon Not Linked and Not Showing Count

**Severity**: Medium
**Affected Component**: Header / Store / Navigation
**Discovered**: December 24, 2025
**Status**: RESOLVED

## Bug Description

The shopping cart icon in the header navigation had two issues:
1. Clicking the cart icon did nothing (href="#" placeholder)
2. Cart item count badge was never displayed (hardcoded hidden with 0)

## Steps to Reproduce

1. Add items to cart via store pages
2. Look at cart icon in header
3. Notice badge doesn't show item count
4. Click cart icon
5. Observe nothing happens (stays on same page)

## Expected Behavior

1. Cart icon should link to the cart page (`/store/cart/`)
2. When cart has items, a badge should show the item count
3. Clicking the icon should navigate to the cart

## Actual Behavior

1. Cart icon had `href="#"` - a dead placeholder link
2. Badge was hardcoded with `class="hidden"` and value `0`
3. No context processor was providing cart data to the header template

## Root Cause

The header template was created with placeholder values that were never connected to actual cart functionality:
- `href="#"` was a placeholder for the real cart URL
- No context processor existed to provide `cart_count` to templates
- Badge display logic was missing

## Fix Applied

### 1. Created cart context processor
**File:** `apps/store/context_processors.py`

```python
def cart(request):
    """Add cart to template context for all pages."""
    cart_obj = None
    cart_count = 0

    if request.user.is_authenticated:
        cart_obj = Cart.objects.filter(user=request.user).first()
    elif hasattr(request, 'session') and request.session.session_key:
        cart_obj = Cart.objects.filter(
            session_key=request.session.session_key,
            user__isnull=True
        ).first()

    if cart_obj:
        cart_count = cart_obj.item_count

    return {'cart': cart_obj, 'cart_count': cart_count}
```

### 2. Added context processor to settings
**File:** `config/settings/base.py`

Added `'apps.store.context_processors.cart'` to template context processors.

### 3. Fixed header template
**File:** `templates/components/header.html`

- Changed `href="#"` to `{% url 'store:cart' %}`
- Added conditional display: `{% if cart_count > 0 %}...{% endif %}`
- Badge now shows actual `{{ cart_count }}`

## Files Modified

1. `apps/store/context_processors.py` - Created new file
2. `config/settings/base.py` - Added context processor
3. `templates/components/header.html` - Fixed cart link and badge

## Verification

1. Navigate to store at `/store/`
2. Add a product to cart
3. Observe cart icon badge shows count (e.g., "1")
4. Click cart icon
5. Should navigate to `/store/cart/` showing cart contents

## Resolution

**Fixed**: December 24, 2025
**Verified**: Pending user verification
