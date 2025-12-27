# T-073: Checkout Integration with StoreSettings

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
**Dependencies**: T-066 (StoreSettings), T-072 (Admin interfaces)

---

## Objective

Integrate checkout with StoreSettings to use dynamic shipping cost instead of hardcoded $50.

---

## Test Cases

```python
class CheckoutStoreSettingsIntegrationTests(TestCase):
    """Tests for checkout integration with StoreSettings."""

    def setUp(self):
        self.user = User.objects.create_user('test', 't@test.com', 'pass')
        self.category = Category.objects.create(name='Test', slug='test')
        self.product = Product.objects.create(
            name='Product', slug='product', category=self.category,
            price=Decimal('100.00')
        )
        self.cart = Cart.objects.create(user=self.user)
        self.cart.add_item(self.product, 1)
        self.client.login(username='test', password='pass')

    def test_checkout_uses_store_settings_shipping(self):
        """Checkout shows shipping cost from StoreSettings."""
        settings = StoreSettings.get_instance()
        settings.default_shipping_cost = Decimal('75.00')
        settings.save()

        response = self.client.get(reverse('store:checkout'))
        self.assertContains(response, '75.00')

    def test_order_uses_store_settings_shipping(self):
        """Order.create_from_cart uses StoreSettings shipping cost."""
        settings = StoreSettings.get_instance()
        settings.default_shipping_cost = Decimal('60.00')
        settings.save()

        order = Order.create_from_cart(
            cart=self.cart,
            user=self.user,
            fulfillment_method='delivery',
            shipping_address='Test'
        )
        self.assertEqual(order.shipping_cost, Decimal('60.00'))

    def test_free_shipping_applied_when_threshold_met(self):
        """Free shipping when order meets threshold."""
        settings = StoreSettings.get_instance()
        settings.default_shipping_cost = Decimal('50.00')
        settings.free_shipping_threshold = Decimal('500.00')
        settings.save()

        # Add more to cart to meet threshold
        self.cart.add_item(self.product, 5)  # 600 total

        order = Order.create_from_cart(
            cart=self.cart,
            user=self.user,
            fulfillment_method='delivery',
            shipping_address='Test'
        )
        self.assertEqual(order.shipping_cost, Decimal('0'))

    def test_checkout_context_includes_store_settings(self):
        """Checkout template receives store_settings context."""
        response = self.client.get(reverse('store:checkout'))
        self.assertIn('store_settings', response.context)

    def test_store_settings_in_js(self):
        """JavaScript receives correct shipping cost."""
        settings = StoreSettings.get_instance()
        settings.default_shipping_cost = Decimal('45.00')
        settings.save()

        response = self.client.get(reverse('store:checkout'))
        self.assertContains(response, 'shippingCost: 45.00')
```

---

## Implementation

### 1. Context Processor (apps/store/context_processors.py)

```python
from apps.store.models import StoreSettings

def store_settings(request):
    """Add store settings to template context."""
    return {
        'store_settings': StoreSettings.get_instance()
    }
```

### 2. Add to settings.py

```python
TEMPLATES = [
    {
        ...
        'OPTIONS': {
            'context_processors': [
                ...
                'apps.store.context_processors.store_settings',
            ],
        },
    },
]
```

### 3. Update Order.create_from_cart (apps/store/models.py)

```python
@classmethod
def create_from_cart(cls, cart, user, fulfillment_method='pickup', ...):
    settings = StoreSettings.get_instance()

    subtotal = cart.total
    tax = subtotal * settings.tax_rate

    if fulfillment_method == 'delivery':
        shipping_cost = settings.get_shipping_cost(subtotal)
    else:
        shipping_cost = Decimal('0')

    total = subtotal + tax + shipping_cost

    order = cls.objects.create(
        ...
        shipping_cost=shipping_cost,
        tax=tax,
        total=total,
    )
    ...
```

### 4. Update Checkout Template (templates/store/checkout.html)

```html
<script>
function checkoutForm(subtotal) {
    return {
        method: 'pickup',
        payment: 'cash',
        subtotal: subtotal,
        taxRate: {{ store_settings.tax_rate }},
        shippingCost: {{ store_settings.default_shipping_cost }},
        freeShippingThreshold: {% if store_settings.free_shipping_threshold %}{{ store_settings.free_shipping_threshold }}{% else %}null{% endif %},
        tax: 0,
        total: 0,

        updateTotals() {
            this.tax = this.subtotal * this.taxRate;

            let shipping = 0;
            if (this.method === 'delivery') {
                if (this.freeShippingThreshold && this.subtotal >= this.freeShippingThreshold) {
                    shipping = 0;
                } else {
                    shipping = this.shippingCost;
                }
            }

            this.total = this.subtotal + this.tax + shipping;

            document.getElementById('tax-amount').textContent = '$' + this.tax.toFixed(2);
            document.getElementById('total-amount').textContent = '$' + this.total.toFixed(2);

            // Update shipping display
            const shippingEl = document.getElementById('shipping-amount');
            if (shippingEl) {
                shippingEl.textContent = '$' + shipping.toFixed(2);
            }
        }
    }
}
</script>
```

### 5. Update Checkout View (apps/store/views.py)

```python
class CheckoutView(LoginRequiredMixin, TemplateView):
    template_name = 'store/checkout.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart'] = get_or_create_cart(self.request)
        # store_settings now available via context processor
        return context
```

---

## Definition of Done

- [ ] Context processor created and registered
- [ ] Order.create_from_cart uses StoreSettings
- [ ] Checkout template uses dynamic values
- [ ] Free shipping threshold works
- [ ] JavaScript calculations use StoreSettings values
- [ ] All tests pass (>95% coverage)
- [ ] Hardcoded $50 shipping removed
