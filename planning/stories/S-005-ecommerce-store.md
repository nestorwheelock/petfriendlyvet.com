# S-005: E-Commerce Store

**Story Type:** User Story
**Priority:** High
**Epoch:** 3
**Status:** PENDING

## User Story

**As a** pet owner
**I want to** browse and purchase pet products online
**So that** I can buy food, toys, and supplies without visiting the store

**As a** pet owner
**I want to** ask the AI for product recommendations
**So that** I can find the right products for my pet's needs

## Acceptance Criteria

### Product Catalog
- [ ] Products organized by categories
- [ ] Product detail pages with images, description, price
- [ ] Stock availability displayed
- [ ] Bilingual product information
- [ ] Search and filter functionality

### Shopping Cart
- [ ] Add/remove products from cart
- [ ] Update quantities
- [ ] Cart persists across sessions (for logged-in users)
- [ ] Cart icon shows item count
- [ ] Cart accessible from any page

### Checkout
- [ ] Shipping address collection (for delivery)
- [ ] Pickup option available
- [ ] Stripe payment integration
- [ ] Order confirmation page
- [ ] Email receipt sent

### AI Integration
- [ ] AI can search products via chat
- [ ] AI can add items to cart
- [ ] AI can recommend products based on pet type
- [ ] AI can check product availability
- [ ] AI can help with reordering previous purchases

### Order Management
- [ ] Users can view order history
- [ ] Order status tracking
- [ ] Staff can view and manage orders
- [ ] Staff can update order status

## Example AI Conversations

### Product Search
```
User: Do you have Hills Science Diet for large breed puppies?
AI: Yes! We have Hills Science Diet options for large breed puppies:

    🦴 **Hills Science Diet Large Breed Puppy**

    1. **Chicken & Oats (12kg)** - $1,450 MXN
       ✅ In Stock (5 available)

    2. **Lamb & Rice (12kg)** - $1,520 MXN
       ✅ In Stock (3 available)

    3. **Chicken & Oats (6kg)** - $850 MXN
       ⚠️ Low Stock (2 remaining)

    Would you like me to add any of these to your cart?

User: Add the 12kg chicken one
AI: Added to cart! 🛒

    ✅ Hills Science Diet Large Breed Puppy - Chicken & Oats (12kg)
    Price: $1,450 MXN

    Your cart now has 1 item totaling $1,450 MXN.

    Would you like to continue shopping or proceed to checkout?
```

### Personalized Recommendations
```
User: What food do you recommend for Luna?
AI: Based on Luna's profile (Golden Retriever, 3 years, 28kg):

    🌟 **Recommended for Adult Large Breed Dogs:**

    1. **Royal Canin Golden Retriever Adult (12kg)** - $1,680 MXN
       Specifically formulated for Golden Retrievers

    2. **Hills Science Diet Adult Large Breed (12kg)** - $1,450 MXN
       Great for maintaining healthy weight

    3. **Purina Pro Plan Large Breed Adult (15kg)** - $1,350 MXN
       High protein, supports active dogs

    Luna last ate Royal Canin (purchased 6 weeks ago).
    Would you like to reorder the same food?
```

### Reorder
```
User: I need to reorder Luna's food
AI: I see Luna's previous orders:

    📦 Last ordered (Nov 5, 2025):
    • Royal Canin Golden Retriever Adult (12kg) - $1,680 MXN

    Would you like me to add the same item to your cart?

User: Yes please
AI: Done! Added to cart:

    ✅ Royal Canin Golden Retriever Adult (12kg) - $1,680 MXN

    Ready to checkout? You can pick up at the clinic or we can
    arrange delivery in Puerto Morelos.
```

## Technical Requirements

### Package: django-simple-store

```python
# models.py

class Category(models.Model):
    name = models.CharField(max_length=100)
    name_es = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='categories/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Categories'


class Product(models.Model):
    name = models.CharField(max_length=200)
    name_es = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    description = models.TextField(blank=True)
    description_es = models.TextField(blank=True)
    description_en = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    sku = models.CharField(max_length=50, unique=True)
    stock_quantity = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=5)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # For pet-specific recommendations
    suitable_for_species = models.JSONField(default=list)  # ['dog', 'cat']
    suitable_for_sizes = models.JSONField(default=list)  # ['small', 'medium', 'large']
    suitable_for_ages = models.JSONField(default=list)  # ['puppy', 'adult', 'senior']

    @property
    def is_in_stock(self):
        return self.stock_quantity > 0

    @property
    def is_low_stock(self):
        return 0 < self.stock_quantity <= self.low_stock_threshold


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.IntegerField(default=0)


class Cart(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=255, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    @property
    def subtotal(self):
        return self.product.price * self.quantity


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready for Pickup'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    FULFILLMENT_CHOICES = [
        ('pickup', 'Pickup at Clinic'),
        ('delivery', 'Delivery'),
    ]

    user = models.ForeignKey(User, on_delete=models.PROTECT)
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    fulfillment_method = models.CharField(max_length=20, choices=FULFILLMENT_CHOICES)

    # Shipping info (for delivery)
    shipping_name = models.CharField(max_length=200, blank=True)
    shipping_address = models.TextField(blank=True)
    shipping_phone = models.CharField(max_length=20, blank=True)

    # Totals
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    # Payment
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    paid_at = models.DateTimeField(null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    notes = models.TextField(blank=True)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    product_name = models.CharField(max_length=200)  # Snapshot at time of order
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()

    @property
    def subtotal(self):
        return self.price * self.quantity
```

### AI Tools (Epoch 3)

```python
STORE_TOOLS = [
    {
        "name": "search_products",
        "description": "Search for products in the store",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "category": {"type": "string"},
                "species": {"type": "string", "enum": ["dog", "cat", "bird", "other"]},
                "max_price": {"type": "number"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_product_details",
        "description": "Get detailed information about a product",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "integer"}
            },
            "required": ["product_id"]
        }
    },
    {
        "name": "add_to_cart",
        "description": "Add a product to the shopping cart",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "integer"},
                "quantity": {"type": "integer", "default": 1}
            },
            "required": ["product_id"]
        }
    },
    {
        "name": "get_cart",
        "description": "Get the current shopping cart contents",
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "name": "update_cart_item",
        "description": "Update quantity of an item in cart",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "integer"},
                "quantity": {"type": "integer"}
            },
            "required": ["product_id", "quantity"]
        }
    },
    {
        "name": "remove_from_cart",
        "description": "Remove an item from the cart",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "integer"}
            },
            "required": ["product_id"]
        }
    },
    {
        "name": "get_recommendations",
        "description": "Get product recommendations for a pet",
        "parameters": {
            "type": "object",
            "properties": {
                "pet_id": {"type": "integer"},
                "category": {"type": "string"}
            }
        }
    },
    {
        "name": "get_order_history",
        "description": "Get the user's past orders",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 5}
            }
        }
    },
    {
        "name": "reorder",
        "description": "Add items from a previous order to cart",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "integer"}
            },
            "required": ["order_id"]
        }
    }
]

# Admin store tools
ADMIN_STORE_TOOLS = [
    {
        "name": "update_stock",
        "description": "Update product stock quantity",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "integer"},
                "quantity": {"type": "integer"},
                "operation": {"type": "string", "enum": ["set", "add", "subtract"]}
            },
            "required": ["product_id", "quantity"]
        }
    },
    {
        "name": "get_low_stock_products",
        "description": "Get products that are low on stock",
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "name": "update_order_status",
        "description": "Update the status of an order",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "integer"},
                "status": {"type": "string"}
            },
            "required": ["order_id", "status"]
        }
    },
    {
        "name": "get_pending_orders",
        "description": "Get orders that need attention",
        "parameters": {"type": "object", "properties": {}}
    }
]
```

## Definition of Done

- [ ] Product catalog displaying with categories
- [ ] Product search and filtering working
- [ ] Shopping cart functional (add, update, remove)
- [ ] Stripe checkout integration complete
- [ ] Order confirmation emails sent
- [ ] Order history viewable by users
- [ ] AI can search, add to cart, and recommend products
- [ ] Reorder functionality working
- [ ] Staff can manage orders via AI
- [ ] Stock tracking functional
- [ ] Tests written and passing (>95% coverage)

## Dependencies

- S-001: Foundation + AI Core
- S-002: AI Chat Interface
- S-003: Pet Profiles (for recommendations)
- Stripe account configured
- Product inventory data from client

## Notes

- Currency is Mexican Pesos (MXN)
- Delivery available within Puerto Morelos area
- Consider adding product bundles in future
- Inventory sync with physical store TBD

## Development Process

**Before implementing this story**, review and follow the **23-Step TDD Cycle** in:
- `CLAUDE.md` - Global development workflow
- `planning/TASK_BREAKDOWN.md` - Specific tasks for this story

Tests must be written before implementation. >95% coverage required.
