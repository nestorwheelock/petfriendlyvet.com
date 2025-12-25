# Store Module

The `apps.store` module provides e-commerce functionality for the veterinary clinic's online store, including product catalog, shopping cart, checkout, and order management.

## Table of Contents

- [Overview](#overview)
- [Models](#models)
  - [StoreSettings](#storesettings)
  - [Category](#category)
  - [Product](#product)
  - [ProductImage](#productimage)
  - [Cart](#cart)
  - [CartItem](#cartitem)
  - [Order](#order)
  - [OrderItem](#orderitem)
- [Views](#views)
- [URL Patterns](#url-patterns)
- [Workflows](#workflows)
  - [Shopping Flow](#shopping-flow)
  - [Cart Management](#cart-management)
  - [Checkout Process](#checkout-process)
  - [Order Lifecycle](#order-lifecycle)
- [Pet-Based Recommendations](#pet-based-recommendations)
- [Integration Points](#integration-points)
- [Query Examples](#query-examples)
- [Testing](#testing)

## Overview

The store module handles:

- **Product Catalog** - Bilingual products with categories
- **Shopping Cart** - User and session-based carts
- **Checkout** - Order creation with payment options
- **Order Management** - Status tracking and fulfillment
- **Inventory** - Stock tracking and low stock alerts
- **Shipping** - Pickup and delivery options

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Category     │────▶│     Product     │────▶│  ProductImage   │
│   (hierarchy)   │     │   (catalog)     │     │   (gallery)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│      Cart       │────▶│    CartItem     │     │                 │
│  (user/session) │     │   (products)    │     │                 │
└─────────────────┘     └─────────────────┘     │                 │
        │                                       │                 │
        ▼                                       │                 │
┌─────────────────┐     ┌─────────────────┐     │                 │
│     Order       │────▶│   OrderItem     │◀────┘                 │
│   (checkout)    │     │   (snapshot)    │                       │
└─────────────────┘     └─────────────────┘                       │
```

## Models

### StoreSettings

Location: `apps/store/models.py`

Store-wide configuration (singleton pattern).

```python
class StoreSettings(models.Model):
    default_shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('50.00'))
    free_shipping_threshold = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tax_rate = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0.16'))  # IVA 16%
    default_max_order_quantity = models.PositiveIntegerField(default=99)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.pk = 1  # Enforce singleton
        super().save(*args, **kwargs)

    @classmethod
    def get_instance(cls):
        """Get or create the singleton settings instance."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def get_shipping_cost(self, subtotal):
        """Calculate shipping cost based on subtotal and threshold."""
        if self.free_shipping_threshold and subtotal >= self.free_shipping_threshold:
            return Decimal('0')
        return self.default_shipping_cost
```

### Category

Product categories with hierarchy support.

```python
class Category(models.Model):
    name = models.CharField(max_length=100)
    name_es = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    image = models.ImageField(upload_to='categories/', null=True, blank=True)
    description = models.TextField(blank=True)
    description_es = models.TextField(blank=True)
    description_en = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_ancestors(self):
        """Get all ancestor categories."""
        ancestors = []
        current = self.parent
        while current:
            ancestors.insert(0, current)
            current = current.parent
        return ancestors

    def get_descendants(self):
        """Get all descendant categories."""
        descendants = list(self.children.all())
        for child in self.children.all():
            descendants.extend(child.get_descendants())
        return descendants
```

### Product

Products with bilingual content and inventory tracking.

```python
class Product(models.Model):
    name = models.CharField(max_length=200)
    name_es = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    description = models.TextField(blank=True)
    description_es = models.TextField(blank=True)
    description_en = models.TextField(blank=True)

    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Identification
    sku = models.CharField(max_length=50, unique=True)
    barcode = models.CharField(max_length=100, blank=True)

    # Inventory
    stock_quantity = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=5)
    track_inventory = models.BooleanField(default=True)

    # Physical
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    max_order_quantity = models.PositiveIntegerField(null=True, blank=True)

    # Pet-specific filters
    suitable_for_species = models.JSONField(default=list, blank=True)  # ['dog', 'cat']
    suitable_for_sizes = models.JSONField(default=list, blank=True)    # ['small', 'medium', 'large']
    suitable_for_ages = models.JSONField(default=list, blank=True)     # ['puppy', 'adult', 'senior']

    # SEO
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_in_stock(self):
        return self.stock_quantity > 0

    @property
    def is_low_stock(self):
        return 0 < self.stock_quantity <= self.low_stock_threshold

    @property
    def is_on_sale(self):
        return self.compare_at_price is not None and self.compare_at_price > self.price

    @property
    def discount_percentage(self):
        if not self.is_on_sale:
            return 0
        return int(((self.compare_at_price - self.price) / self.compare_at_price) * 100)

    @property
    def primary_image(self):
        primary = self.images.filter(is_primary=True).first()
        return primary or self.images.first()
```

### ProductImage

Product images with ordering support.

```python
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """Ensure only one primary image per product."""
        if self.is_primary:
            ProductImage.objects.filter(product=self.product, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)
```

### Cart

Shopping cart for users or anonymous sessions.

```python
class Cart(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='carts')
    session_key = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())

    def add_item(self, product, quantity=1):
        """Add an item to the cart or update quantity."""
        item, created = CartItem.objects.get_or_create(
            cart=self, product=product, defaults={'quantity': quantity}
        )
        if not created:
            item.quantity += quantity
            item.save()
        return item

    def remove_item(self, product):
        CartItem.objects.filter(cart=self, product=product).delete()

    def update_item_quantity(self, product, quantity):
        if quantity <= 0:
            self.remove_item(product)
            return None
        item = CartItem.objects.filter(cart=self, product=product).first()
        if item:
            item.quantity = quantity
            item.save()
        return item

    def clear(self):
        self.items.all().delete()

    def merge_with(self, other_cart):
        """Merge another cart into this one (for login)."""
        for item in other_cart.items.all():
            self.add_item(item.product, item.quantity)
        other_cart.delete()
```

### CartItem

Item in a shopping cart.

```python
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['cart', 'product']

    @property
    def subtotal(self):
        return self.product.price * self.quantity
```

### Order

Customer order with status tracking.

```python
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready for Pickup'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    FULFILLMENT_CHOICES = [
        ('pickup', 'Pickup at Clinic'),
        ('delivery', 'Delivery'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('transfer', 'Bank Transfer'),
    ]

    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    fulfillment_method = models.CharField(max_length=20, choices=FULFILLMENT_CHOICES)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')

    # Shipping info
    shipping_name = models.CharField(max_length=200, blank=True)
    shipping_address = models.TextField(blank=True)
    shipping_phone = models.CharField(max_length=20, blank=True)

    # Totals (MXN)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    # Payment
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    stripe_charge_id = models.CharField(max_length=255, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def generate_order_number(cls):
        """Generate unique order number: ORD-YYYY-XXXX"""
        year = timezone.now().year
        while True:
            random_part = random.randint(1000, 9999)
            order_number = f"ORD-{year}-{random_part:04d}"
            if not cls.objects.filter(order_number=order_number).exists():
                return order_number

    @classmethod
    def create_from_cart(cls, cart, user, fulfillment_method, payment_method='cash', **shipping_info):
        """Create an order from a cart."""
        # Creates order, order items, deducts stock, clears cart
```

### OrderItem

Snapshot of item at time of order.

```python
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)

    # Snapshot at time of order
    product_name = models.CharField(max_length=200)
    product_sku = models.CharField(max_length=50, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()

    @property
    def subtotal(self):
        return self.price * self.quantity
```

## Views

Location: `apps/store/views.py`

### Product Views

```python
class ProductListView(ListView):
    """List products with filtering and search."""
    # Filters: category, search, species, price range
    # Sorting: price, name, date

class ProductDetailView(DetailView):
    """Show product details with related products."""

class CategoryDetailView(ListView):
    """Show products in a category."""
```

### Cart Views

```python
class CartView(TemplateView):
    """Show shopping cart."""

def add_to_cart(request, product_id):
    """Add product to cart with quantity/stock validation."""

def update_cart(request):
    """Update cart item quantity."""

def remove_from_cart(request, product_id):
    """Remove product from cart."""
```

### Checkout Views

```python
class CheckoutView(LoginRequiredMixin, TemplateView):
    """Checkout page."""

@login_required
def process_checkout(request):
    """Create order from cart."""
```

### Order Views

```python
class OrderListView(LoginRequiredMixin, ListView):
    """List user's orders."""

class OrderDetailView(LoginRequiredMixin, DetailView):
    """Show order details."""
```

## URL Patterns

Location: `apps/store/urls.py`

```python
app_name = 'store'

urlpatterns = [
    # Product catalog
    path('', views.ProductListView.as_view(), name='product_list'),
    path('product/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('category/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),

    # Cart
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),

    # Checkout
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('checkout/process/', views.process_checkout, name='process_checkout'),

    # Orders
    path('orders/', views.OrderListView.as_view(), name='order_list'),
    path('orders/<str:order_number>/', views.OrderDetailView.as_view(), name='order_detail'),
]
```

## Workflows

### Shopping Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Browse    │───▶│   Add to    │───▶│    View     │───▶│  Checkout   │
│  Products   │    │    Cart     │    │    Cart     │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                                │
                                                                ▼
                                                         ┌─────────────┐
                                                         │   Order     │
                                                         │ Confirmation│
                                                         └─────────────┘
```

### Cart Management

```python
from apps.store.models import Cart, Product

# Get or create cart (handles user vs session)
def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        # Merge session cart on login
        if not created:
            session_cart = Cart.objects.filter(
                session_key=request.session.session_key,
                user__isnull=True
            ).first()
            if session_cart:
                cart.merge_with(session_cart)
        return cart
    else:
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(
            session_key=request.session.session_key,
            user__isnull=True
        )
        return cart

# Add to cart
cart.add_item(product, quantity=2)

# Update quantity
cart.update_item_quantity(product, 3)

# Remove item
cart.remove_item(product)

# Clear cart
cart.clear()
```

### Checkout Process

```python
from apps.store.models import Order

# Create order from cart
order = Order.create_from_cart(
    cart=cart,
    user=user,
    fulfillment_method='delivery',
    payment_method='card',
    shipping_name='Juan Pérez',
    shipping_address='Av. Principal 123, Puerto Morelos',
    shipping_phone='555-1234',
)

# Order number: ORD-2024-1234
# Status: 'paid' (if card) or 'pending' (if cash)
# Stock automatically deducted
# Cart automatically cleared
```

### Order Lifecycle

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ PENDING │───▶│  PAID   │───▶│PREPARING│───▶│  READY  │
│(payment)│    │         │    │         │    │(pickup) │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
                                                  │
                                                  ▼
┌─────────┐    ┌─────────┐                  ┌─────────┐
│CANCELLED│    │REFUNDED │                  │DELIVERED│
└─────────┘    └─────────┘                  └─────────┘
```

For delivery orders:
```
PENDING → PAID → PREPARING → SHIPPED → DELIVERED
```

## Pet-Based Recommendations

Products can be filtered by pet attributes:

```python
from apps.store.models import Product

# Products for dogs
dog_products = Product.objects.filter(is_active=True)
dog_products = [p for p in dog_products if 'dog' in p.suitable_for_species]

# Products for large adult dogs
filtered = Product.objects.filter(is_active=True)
filtered = [p for p in filtered
    if 'dog' in p.suitable_for_species
    and 'large' in p.suitable_for_sizes
    and 'adult' in p.suitable_for_ages]

# Recommend products for user's pets
user_pets = user.pets.all()
species_list = list(set(p.species for p in user_pets))
# Filter products matching user's pet species
```

### Species Values
- `dog`, `cat`, `bird`, `rabbit`, `hamster`, `guinea_pig`, `reptile`

### Size Values
- `small`, `medium`, `large`, `giant`

### Age Values
- `puppy`, `kitten`, `adult`, `senior`

## Integration Points

### With Billing Module

```python
from apps.billing.services import InvoiceService
from apps.store.models import Order

# Create invoice from order
order = Order.objects.get(order_number='ORD-2024-1234')
invoice = InvoiceService.create_from_order(order)
```

### With Delivery Module

```python
from apps.delivery.models import Delivery, DeliverySlot

# Create delivery for order
if order.fulfillment_method == 'delivery':
    slot = DeliverySlot.objects.get(pk=slot_id)
    Delivery.objects.create(
        order=order,
        slot=slot,
        zone=slot.zone,
        address=order.shipping_address,
        scheduled_date=slot.date,
        status='pending',
    )
```

### With Inventory Module

```python
from apps.inventory.models import StockMovement

# Stock is automatically deducted in Order.create_from_cart()
# Can also create manual movements:
StockMovement.objects.create(
    stock_level=stock_level,
    movement_type='sale',
    quantity=-order_item.quantity,
    reference=f'Order {order.order_number}',
)
```

## Query Examples

### Product Queries

```python
from apps.store.models import Product, Category
from django.db.models import Q

# Featured products
featured = Product.objects.filter(is_active=True, is_featured=True)

# On sale products
on_sale = Product.objects.filter(
    is_active=True,
    compare_at_price__isnull=False,
    compare_at_price__gt=F('price')
)

# Low stock products
low_stock = Product.objects.filter(
    is_active=True,
    track_inventory=True,
    stock_quantity__gt=0,
    stock_quantity__lte=F('low_stock_threshold')
)

# Out of stock
out_of_stock = Product.objects.filter(
    is_active=True,
    track_inventory=True,
    stock_quantity=0
)

# Search products
query = 'alimento'
results = Product.objects.filter(
    is_active=True
).filter(
    Q(name__icontains=query) |
    Q(name_es__icontains=query) |
    Q(description__icontains=query)
)
```

### Order Queries

```python
from apps.store.models import Order
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth

# Orders by status
pending = Order.objects.filter(status='pending')
preparing = Order.objects.filter(status='preparing')

# Revenue this month
from datetime import date
first_of_month = date.today().replace(day=1)

monthly_revenue = Order.objects.filter(
    status__in=['paid', 'preparing', 'ready', 'shipped', 'delivered'],
    created_at__date__gte=first_of_month
).aggregate(total=Sum('total'))['total'] or 0

# Orders by month
monthly_orders = Order.objects.annotate(
    month=TruncMonth('created_at')
).values('month').annotate(
    count=Count('id'),
    revenue=Sum('total')
).order_by('-month')

# Top products by sales
top_products = OrderItem.objects.values(
    'product__name'
).annotate(
    total_sold=Sum('quantity'),
    revenue=Sum(F('price') * F('quantity'))
).order_by('-total_sold')[:10]
```

### Cart Queries

```python
from apps.store.models import Cart

# Abandoned carts (no update in 24 hours)
from datetime import timedelta
cutoff = timezone.now() - timedelta(hours=24)

abandoned = Cart.objects.filter(
    updated_at__lt=cutoff
).exclude(
    items__isnull=True
)

# Cart value
cart = Cart.objects.get(user=user)
total = cart.total
item_count = cart.item_count
```

## Testing

### Unit Tests

Location: `tests/test_store.py`

```bash
# Run store unit tests
python -m pytest tests/test_store.py -v
```

### Browser Tests

Location: `tests/e2e/browser/test_store.py`

```bash
# Run store browser tests
python -m pytest tests/e2e/browser/test_store.py -v

# Run with visible browser
python -m pytest tests/e2e/browser/test_store.py -v --headed --slowmo=500
```

### Key Test Scenarios

1. **Product Catalog**
   - Category hierarchy
   - Product filtering and search
   - Price and stock display

2. **Shopping Cart**
   - Add/update/remove items
   - Quantity limits
   - Stock validation
   - Session to user cart merge

3. **Checkout**
   - Order creation
   - Payment method handling
   - Stock deduction
   - Delivery integration

4. **Orders**
   - Status transitions
   - Order history
   - Order details
