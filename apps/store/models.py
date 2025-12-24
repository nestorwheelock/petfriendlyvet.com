"""Store models for e-commerce functionality.

Provides:
- Category: Product categories with hierarchy
- Product: Products with bilingual content and inventory
- ProductImage: Multiple images per product
- Cart/CartItem: Shopping cart functionality
- Order/OrderItem: Order management
"""
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Category(models.Model):
    """Product category with support for hierarchy."""

    name = models.CharField(max_length=100)
    name_es = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='children'
    )
    image = models.ImageField(upload_to='categories/', null=True, blank=True)
    description = models.TextField(blank=True)
    description_es = models.TextField(blank=True)
    description_en = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

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


class Product(models.Model):
    """Product with bilingual content and inventory tracking."""

    name = models.CharField(max_length=200)
    name_es = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products'
    )
    description = models.TextField(blank=True)
    description_es = models.TextField(blank=True)
    description_en = models.TextField(blank=True)

    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Original price for showing discounts'
    )

    # Identification
    sku = models.CharField(max_length=50, unique=True)
    barcode = models.CharField(max_length=100, blank=True)

    # Inventory
    stock_quantity = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=5)
    track_inventory = models.BooleanField(default=True)

    # Physical attributes
    weight_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    # Pet-specific filters for recommendations
    suitable_for_species = models.JSONField(
        default=list,
        blank=True,
        help_text='List of species: dog, cat, bird, etc.'
    )
    suitable_for_sizes = models.JSONField(
        default=list,
        blank=True,
        help_text='List of sizes: small, medium, large, giant'
    )
    suitable_for_ages = models.JSONField(
        default=list,
        blank=True,
        help_text='List of ages: puppy, kitten, adult, senior'
    )

    # SEO
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def is_in_stock(self):
        """Check if product is in stock."""
        return self.stock_quantity > 0

    @property
    def is_low_stock(self):
        """Check if product is low on stock."""
        return 0 < self.stock_quantity <= self.low_stock_threshold

    @property
    def is_on_sale(self):
        """Check if product has a compare_at_price (is on sale)."""
        return (
            self.compare_at_price is not None and
            self.compare_at_price > self.price
        )

    @property
    def discount_percentage(self):
        """Calculate discount percentage if on sale."""
        if not self.is_on_sale:
            return 0
        return int(
            ((self.compare_at_price - self.price) / self.compare_at_price) * 100
        )

    @property
    def primary_image(self):
        """Get the primary image or first image."""
        primary = self.images.filter(is_primary=True).first()
        if primary:
            return primary
        return self.images.first()


class ProductImage(models.Model):
    """Product image with ordering support."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.product.name} - Image {self.order}"

    def save(self, *args, **kwargs):
        """Ensure only one primary image per product."""
        if self.is_primary:
            ProductImage.objects.filter(
                product=self.product,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class Cart(models.Model):
    """Shopping cart for users or anonymous sessions."""

    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='carts'
    )
    session_key = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        if self.user:
            return f"Cart for {self.user.username}"
        return f"Cart {self.session_key}"

    @property
    def total(self):
        """Calculate cart total."""
        return sum(item.subtotal for item in self.items.all())

    @property
    def item_count(self):
        """Get total number of items in cart."""
        return sum(item.quantity for item in self.items.all())

    def add_item(self, product, quantity=1):
        """Add an item to the cart or update quantity if exists."""
        item, created = CartItem.objects.get_or_create(
            cart=self,
            product=product,
            defaults={'quantity': quantity}
        )
        if not created:
            item.quantity += quantity
            item.save()
        return item

    def remove_item(self, product):
        """Remove an item from the cart."""
        CartItem.objects.filter(cart=self, product=product).delete()

    def update_item_quantity(self, product, quantity):
        """Update the quantity of an item in the cart."""
        if quantity <= 0:
            self.remove_item(product)
            return None
        item = CartItem.objects.filter(cart=self, product=product).first()
        if item:
            item.quantity = quantity
            item.save()
        return item

    def clear(self):
        """Remove all items from the cart."""
        self.items.all().delete()

    def merge_with(self, other_cart):
        """Merge another cart into this one (for login)."""
        for item in other_cart.items.all():
            self.add_item(item.product, item.quantity)
        other_cart.delete()


class CartItem(models.Model):
    """Item in a shopping cart."""

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )
    quantity = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['cart', 'product']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    @property
    def subtotal(self):
        """Calculate item subtotal."""
        return self.product.price * self.quantity


class Order(models.Model):
    """Customer order."""

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

    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='orders'
    )
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    fulfillment_method = models.CharField(
        max_length=20,
        choices=FULFILLMENT_CHOICES
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='cash'
    )

    # Shipping info (for delivery)
    shipping_name = models.CharField(max_length=200, blank=True)
    shipping_address = models.TextField(blank=True)
    shipping_phone = models.CharField(max_length=20, blank=True)

    # Totals (in MXN)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    # Payment
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    stripe_charge_id = models.CharField(max_length=255, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    # Notes
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_number}"

    @classmethod
    def generate_order_number(cls):
        """Generate a unique order number."""
        from django.utils import timezone
        import random
        year = timezone.now().year
        while True:
            random_part = random.randint(1000, 9999)
            order_number = f"ORD-{year}-{random_part:04d}"
            if not cls.objects.filter(order_number=order_number).exists():
                return order_number

    @classmethod
    def create_from_cart(cls, cart, user, fulfillment_method, payment_method='cash', **shipping_info):
        """Create an order from a cart."""
        from django.db import transaction
        from django.utils import timezone
        from decimal import Decimal

        with transaction.atomic():
            subtotal = cart.total
            tax = subtotal * Decimal('0.16')  # IVA 16%
            shipping_cost = Decimal('0')

            if fulfillment_method == 'delivery':
                shipping_cost = Decimal('50.00')  # Flat rate for Puerto Morelos

            total = subtotal + tax + shipping_cost

            # Determine initial status based on payment method
            # Card payments are "simulated" as immediately paid
            initial_status = 'pending'
            paid_at = None
            if payment_method == 'card':
                initial_status = 'paid'
                paid_at = timezone.now()

            order = cls.objects.create(
                user=user,
                order_number=cls.generate_order_number(),
                status=initial_status,
                fulfillment_method=fulfillment_method,
                payment_method=payment_method,
                subtotal=subtotal,
                tax=tax,
                shipping_cost=shipping_cost,
                total=total,
                paid_at=paid_at,
                **shipping_info
            )

            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    product_name=cart_item.product.name,
                    price=cart_item.product.price,
                    quantity=cart_item.quantity
                )

                # Deduct stock
                if cart_item.product.track_inventory:
                    cart_item.product.stock_quantity -= cart_item.quantity
                    cart_item.product.save()

            # Clear the cart
            cart.clear()

            return order


class OrderItem(models.Model):
    """Item in an order."""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT
    )
    # Snapshot at time of order
    product_name = models.CharField(max_length=200)
    product_sku = models.CharField(max_length=50, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"

    @property
    def subtotal(self):
        """Calculate item subtotal."""
        return self.price * self.quantity
