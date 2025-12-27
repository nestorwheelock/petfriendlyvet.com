# T-038: Checkout & Stripe Integration

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md and [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Full Stack Developer
**Objective**: Implement checkout flow with Stripe payment processing
**Related Story**: S-005, S-020
**Epoch**: 3
**Estimate**: 6 hours

### Constraints
**Allowed File Paths**: apps/store/, apps/billing/, templates/checkout/
**Forbidden Paths**: None

### Deliverables
- [ ] Order model
- [ ] Checkout flow views
- [ ] Stripe payment integration
- [ ] Order confirmation
- [ ] Email receipts
- [ ] Webhook handling

### Wireframe Reference
See: `planning/wireframes/07-cart-checkout.txt`

### Implementation Details

#### Order Models
```python
class Order(models.Model):
    """Customer order."""

    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('paid', 'Pagado'),
        ('preparing', 'Preparando'),
        ('ready', 'Listo para recoger'),
        ('shipped', 'Enviado'),
        ('delivered', 'Entregado'),
        ('cancelled', 'Cancelado'),
        ('refunded', 'Reembolsado'),
    ]

    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    # Order number
    order_number = models.CharField(max_length=50, unique=True)

    # Customer
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='orders')
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)

    # Billing
    billing_name = models.CharField(max_length=200)
    billing_address = models.TextField(blank=True)
    billing_rfc = models.CharField(max_length=13, blank=True)  # For CFDI

    # Shipping/Pickup
    fulfillment_type = models.CharField(max_length=20, choices=[
        ('pickup', 'Recoger en tienda'),
        ('delivery', 'Entrega a domicilio'),
    ], default='pickup')
    shipping_address = models.TextField(blank=True)
    shipping_notes = models.TextField(blank=True)

    # Amounts
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    # Currency
    currency = models.CharField(max_length=3, default='MXN')

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')

    # Coupon
    coupon_code = models.CharField(max_length=50, blank=True)
    coupon = models.ForeignKey('billing.CouponCode', on_delete=models.SET_NULL, null=True, blank=True)

    # Payment
    payment_method = models.CharField(max_length=50, blank=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    stripe_checkout_session_id = models.CharField(max_length=255, blank=True)

    # Notes
    customer_notes = models.TextField(blank=True)
    staff_notes = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True)
    fulfilled_at = models.DateTimeField(null=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_order_number():
        prefix = timezone.now().strftime('%Y%m')
        random_part = ''.join(random.choices('0123456789', k=6))
        return f"PF-{prefix}-{random_part}"


class OrderItem(models.Model):
    """Item in an order."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True)
    variant = models.ForeignKey('ProductVariant', on_delete=models.SET_NULL, null=True, blank=True)

    # Snapshot at time of order
    product_name = models.CharField(max_length=500)
    variant_name = models.CharField(max_length=200, blank=True)
    sku = models.CharField(max_length=100)

    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    # Prescription link if applicable
    prescription = models.ForeignKey(
        'pharmacy.Prescription',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
```

#### Stripe Integration
```python
import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """Stripe payment processing."""

    def create_checkout_session(self, order: Order, success_url: str, cancel_url: str) -> str:
        """Create Stripe Checkout session."""

        line_items = [
            {
                'price_data': {
                    'currency': 'mxn',
                    'product_data': {
                        'name': item.product_name,
                        'description': item.variant_name or None,
                    },
                    'unit_amount': int(item.unit_price * 100),  # Centavos
                },
                'quantity': item.quantity,
            }
            for item in order.items.all()
        ]

        # Add discount if coupon
        discounts = []
        if order.discount_amount > 0:
            # Create coupon in Stripe
            stripe_coupon = stripe.Coupon.create(
                amount_off=int(order.discount_amount * 100),
                currency='mxn',
                name=order.coupon_code or 'Descuento',
                duration='once',
            )
            discounts = [{'coupon': stripe_coupon.id}]

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=order.email,
            metadata={
                'order_id': order.id,
                'order_number': order.order_number,
            },
            discounts=discounts,
        )

        order.stripe_checkout_session_id = session.id
        order.save()

        return session.url

    def create_payment_intent(self, order: Order) -> dict:
        """Create PaymentIntent for custom checkout."""

        intent = stripe.PaymentIntent.create(
            amount=int(order.total * 100),  # Centavos
            currency='mxn',
            metadata={
                'order_id': order.id,
                'order_number': order.order_number,
            },
            automatic_payment_methods={'enabled': True},
        )

        order.stripe_payment_intent_id = intent.id
        order.save()

        return {
            'client_secret': intent.client_secret,
            'payment_intent_id': intent.id,
        }

    def handle_webhook(self, payload: bytes, sig_header: str):
        """Handle Stripe webhook."""

        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            self._handle_checkout_complete(session)

        elif event['type'] == 'payment_intent.succeeded':
            intent = event['data']['object']
            self._handle_payment_success(intent)

        elif event['type'] == 'payment_intent.payment_failed':
            intent = event['data']['object']
            self._handle_payment_failed(intent)

    def _handle_checkout_complete(self, session):
        """Handle successful checkout."""
        order = Order.objects.get(stripe_checkout_session_id=session['id'])
        order.payment_status = 'paid'
        order.status = 'processing'
        order.paid_at = timezone.now()
        order.payment_method = 'stripe_checkout'
        order.save()

        # Deduct inventory
        self._deduct_inventory(order)

        # Send confirmation
        send_order_confirmation.delay(order.id)

    def _deduct_inventory(self, order: Order):
        """Deduct inventory for order items."""
        for item in order.items.all():
            if item.variant:
                ProductVariant.objects.filter(id=item.variant_id).update(
                    stock_quantity=F('stock_quantity') - item.quantity
                )
            elif item.product and item.product.track_inventory:
                Product.objects.filter(id=item.product_id).update(
                    stock_quantity=F('stock_quantity') - item.quantity
                )
```

#### Checkout Views
```python
class CheckoutView(LoginRequiredMixin, FormView):
    """Checkout page."""

    template_name = 'checkout/checkout.html'
    form_class = CheckoutForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart'] = CartService().get_or_create_cart(self.request)
        return context

    def form_valid(self, form):
        cart = CartService().get_or_create_cart(self.request)

        # Validate cart not empty
        if not cart.items.exists():
            messages.error(self.request, "Tu carrito está vacío")
            return redirect('store:cart')

        # Create order
        order = self.create_order(cart, form.cleaned_data)

        # Create Stripe session
        stripe_service = StripeService()
        checkout_url = stripe_service.create_checkout_session(
            order,
            success_url=self.request.build_absolute_uri(
                reverse('checkout:success') + f'?order={order.order_number}'
            ),
            cancel_url=self.request.build_absolute_uri(reverse('checkout:checkout'))
        )

        return redirect(checkout_url)

    def create_order(self, cart: Cart, data: dict) -> Order:
        """Create order from cart."""

        order = Order.objects.create(
            user=self.request.user,
            email=data['email'],
            phone=data.get('phone', ''),
            billing_name=data['billing_name'],
            billing_address=data.get('billing_address', ''),
            billing_rfc=data.get('billing_rfc', ''),
            fulfillment_type=data['fulfillment_type'],
            shipping_address=data.get('shipping_address', ''),
            subtotal=cart.subtotal,
            discount_amount=cart.discount_amount,
            tax_amount=cart.tax_amount,
            total=cart.total,
            coupon=cart.coupon,
            coupon_code=cart.coupon.code if cart.coupon else '',
            customer_notes=data.get('notes', ''),
        )

        # Create order items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                variant=cart_item.variant,
                product_name=cart_item.product.name,
                variant_name=cart_item.variant.name if cart_item.variant else '',
                sku=cart_item.variant.sku if cart_item.variant else cart_item.product.sku,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price,
                line_total=cart_item.line_total,
                prescription=cart_item.prescription,
            )

        # Clear cart
        cart.items.all().delete()
        cart.coupon = None
        cart.recalculate()

        return order
```

### Webhook Endpoint
```python
@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhooks."""

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        StripeService().handle_webhook(payload, sig_header)
        return HttpResponse(status=200)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return HttpResponse(status=400)
```

### Test Cases
- [ ] Order creates from cart
- [ ] Stripe session creates
- [ ] Webhook processes payment
- [ ] Inventory deducted
- [ ] Confirmation email sent
- [ ] Order status updates
- [ ] Refund processing works

### Definition of Done
- [ ] Full checkout working
- [ ] Stripe integration complete
- [ ] Webhooks reliable
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-036: Product & Category Models
- T-037: Shopping Cart

### Environment Variables
```
STRIPE_PUBLISHABLE_KEY=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
```
