# T-037: Shopping Cart

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md and [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Full Stack Developer
**Objective**: Implement shopping cart with Alpine.js
**Related Story**: S-005
**Epoch**: 3
**Estimate**: 4 hours

### Constraints
**Allowed File Paths**: apps/store/, templates/store/, static/js/
**Forbidden Paths**: apps/vet_clinic/

### Deliverables
- [ ] Cart model (database)
- [ ] Session-based cart for guests
- [ ] Cart merge on login
- [ ] Add/update/remove items
- [ ] Cart sidebar component
- [ ] Cart page
- [ ] Price calculations

### Implementation Details

#### Models
```python
class Cart(models.Model):
    """Shopping cart."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='cart'
    )
    session_key = models.CharField(max_length=255, null=True, blank=True, db_index=True)

    # Totals (cached, recalculated on change)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Coupon
    coupon = models.ForeignKey(
        'billing.CouponCode',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def recalculate(self):
        """Recalculate cart totals."""
        self.subtotal = sum(
            item.line_total for item in self.items.all()
        )

        # Apply coupon discount
        self.discount_amount = Decimal('0')
        if self.coupon:
            self.discount_amount = self.coupon.calculate_discount(self.subtotal)

        # Calculate tax (16% IVA)
        taxable = self.subtotal - self.discount_amount
        self.tax_amount = taxable * Decimal('0.16')

        self.total = self.subtotal - self.discount_amount + self.tax_amount
        self.save()


class CartItem(models.Model):
    """Item in shopping cart."""

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    variant = models.ForeignKey('ProductVariant', on_delete=models.CASCADE, null=True, blank=True)

    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    # For prescription items
    prescription = models.ForeignKey(
        'pharmacy.Prescription',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['cart', 'product', 'variant']

    def save(self, *args, **kwargs):
        if self.variant and self.variant.price:
            self.unit_price = self.variant.price
        else:
            self.unit_price = self.product.price
        self.line_total = self.unit_price * self.quantity
        super().save(*args, **kwargs)
        self.cart.recalculate()
```

#### Cart Service
```python
class CartService:
    """Service for cart operations."""

    def get_or_create_cart(self, request) -> Cart:
        """Get or create cart for user/session."""

        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
            # Merge session cart if exists
            if request.session.session_key:
                self._merge_session_cart(request.session.session_key, cart)
        else:
            if not request.session.session_key:
                request.session.create()
            cart, created = Cart.objects.get_or_create(
                session_key=request.session.session_key
            )

        return cart

    def add_item(
        self,
        cart: Cart,
        product: Product,
        quantity: int = 1,
        variant: ProductVariant = None
    ) -> CartItem:
        """Add item to cart."""

        # Check stock
        if product.track_inventory:
            available = variant.stock_quantity if variant else product.stock_quantity
            if quantity > available and not product.allow_backorder:
                raise ValidationError("Cantidad no disponible")

        # Check prescription requirement
        if product.requires_prescription:
            raise ValidationError("Este producto requiere receta")

        # Get or create item
        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            variant=variant,
            defaults={'quantity': quantity}
        )

        if not created:
            item.quantity += quantity
            item.save()

        return item

    def update_quantity(self, cart: Cart, item_id: int, quantity: int):
        """Update item quantity."""
        item = cart.items.get(id=item_id)

        if quantity <= 0:
            item.delete()
        else:
            item.quantity = quantity
            item.save()

        cart.recalculate()

    def remove_item(self, cart: Cart, item_id: int):
        """Remove item from cart."""
        cart.items.filter(id=item_id).delete()
        cart.recalculate()

    def apply_coupon(self, cart: Cart, code: str) -> bool:
        """Apply coupon code."""
        coupon = CouponCode.objects.filter(
            code__iexact=code,
            is_active=True,
            valid_from__lte=timezone.now(),
        ).filter(
            Q(valid_until__isnull=True) | Q(valid_until__gte=timezone.now())
        ).first()

        if coupon and coupon.is_valid_for_cart(cart):
            cart.coupon = coupon
            cart.save()
            cart.recalculate()
            return True
        return False

    def _merge_session_cart(self, session_key: str, user_cart: Cart):
        """Merge session cart into user cart."""
        session_cart = Cart.objects.filter(session_key=session_key).first()
        if session_cart:
            for item in session_cart.items.all():
                self.add_item(
                    user_cart,
                    item.product,
                    item.quantity,
                    item.variant
                )
            session_cart.delete()
```

#### Alpine.js Cart Component
```html
<div x-data="shoppingCart()" @cart-updated.window="refreshCart()">
    <!-- Mini cart icon -->
    <button @click="isOpen = true" class="relative">
        <svg>...</svg>
        <span x-show="itemCount > 0"
              x-text="itemCount"
              class="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-5 h-5 text-xs">
        </span>
    </button>

    <!-- Cart sidebar -->
    <div x-show="isOpen"
         x-transition
         class="fixed inset-y-0 right-0 w-96 bg-white shadow-xl z-50">

        <div class="p-4 border-b flex justify-between">
            <h2 class="text-lg font-semibold">Carrito</h2>
            <button @click="isOpen = false">×</button>
        </div>

        <div class="p-4 overflow-y-auto h-[calc(100vh-200px)]">
            <template x-if="items.length === 0">
                <p class="text-center text-gray-500 py-8">Tu carrito está vacío</p>
            </template>

            <template x-for="item in items" :key="item.id">
                <div class="flex gap-4 py-4 border-b">
                    <img :src="item.image" class="w-16 h-16 object-cover rounded">
                    <div class="flex-grow">
                        <p class="font-medium" x-text="item.name"></p>
                        <p class="text-sm text-gray-600" x-text="'$' + item.unit_price"></p>
                        <div class="flex items-center gap-2 mt-2">
                            <button @click="updateQuantity(item.id, item.quantity - 1)">-</button>
                            <span x-text="item.quantity"></span>
                            <button @click="updateQuantity(item.id, item.quantity + 1)">+</button>
                        </div>
                    </div>
                    <button @click="removeItem(item.id)" class="text-red-500">×</button>
                </div>
            </template>
        </div>

        <div class="p-4 border-t">
            <div class="flex justify-between mb-2">
                <span>Subtotal:</span>
                <span x-text="'$' + subtotal"></span>
            </div>
            <div x-show="discount > 0" class="flex justify-between mb-2 text-green-600">
                <span>Descuento:</span>
                <span x-text="'-$' + discount"></span>
            </div>
            <div class="flex justify-between mb-4 font-bold">
                <span>Total:</span>
                <span x-text="'$' + total"></span>
            </div>
            <a href="/checkout/" class="btn btn-primary w-full">
                Proceder al pago
            </a>
        </div>
    </div>
</div>

<script>
function shoppingCart() {
    return {
        isOpen: false,
        items: [],
        subtotal: 0,
        discount: 0,
        total: 0,

        get itemCount() {
            return this.items.reduce((sum, item) => sum + item.quantity, 0);
        },

        async refreshCart() {
            const response = await fetch('/api/cart/');
            const data = await response.json();
            this.items = data.items;
            this.subtotal = data.subtotal;
            this.discount = data.discount;
            this.total = data.total;
        },

        async updateQuantity(itemId, quantity) {
            await fetch(`/api/cart/items/${itemId}/`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ quantity })
            });
            this.refreshCart();
        },

        async removeItem(itemId) {
            await fetch(`/api/cart/items/${itemId}/`, {
                method: 'DELETE',
                headers: { 'X-CSRFToken': getCookie('csrftoken') }
            });
            this.refreshCart();
        },

        init() {
            this.refreshCart();
        }
    }
}
</script>
```

### Test Cases
- [ ] Cart creates for user/session
- [ ] Items add correctly
- [ ] Quantity updates
- [ ] Items remove
- [ ] Totals calculate correctly
- [ ] Coupon applies
- [ ] Cart merges on login
- [ ] Stock validation works

### Definition of Done
- [ ] Full cart functionality
- [ ] Alpine.js component working
- [ ] Session/user carts work
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-036: Product & Category Models
- T-002: Base Templates
