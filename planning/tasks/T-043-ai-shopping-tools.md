# T-043: AI Shopping Tools

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement AI tools for conversational shopping
**Related Story**: S-005
**Epoch**: 3
**Estimate**: 3 hours

### Constraints
**Allowed File Paths**: apps/store/, apps/ai_assistant/tools/
**Forbidden Paths**: None

### Deliverables
- [ ] search_products tool
- [ ] get_product_details tool
- [ ] add_to_cart tool
- [ ] view_cart tool
- [ ] apply_coupon tool
- [ ] get_recommendations tool

### Implementation Details

#### AI Tool Schemas
```python
STORE_TOOLS = [
    {
        "name": "search_products",
        "description": "Search for products by name, category, or keywords",
        "permission": "public",
        "module": "store",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "category": {
                    "type": "string",
                    "description": "Category slug to filter by"
                },
                "species": {
                    "type": "string",
                    "enum": ["dog", "cat", "bird", "exotic"],
                    "description": "Filter by pet species"
                },
                "max_price": {
                    "type": "number",
                    "description": "Maximum price filter"
                },
                "limit": {
                    "type": "integer",
                    "default": 5,
                    "description": "Number of results to return"
                }
            },
            "required": []
        }
    },
    {
        "name": "get_product_details",
        "description": "Get detailed information about a specific product",
        "permission": "public",
        "module": "store",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "integer",
                    "description": "Product ID"
                },
                "slug": {
                    "type": "string",
                    "description": "Product slug (alternative to ID)"
                }
            },
            "required": []
        }
    },
    {
        "name": "add_to_cart",
        "description": "Add a product to the shopping cart",
        "permission": "customer",
        "module": "store",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "integer",
                    "description": "Product ID to add"
                },
                "quantity": {
                    "type": "integer",
                    "default": 1,
                    "description": "Quantity to add"
                },
                "variant_id": {
                    "type": "integer",
                    "description": "Specific variant ID if applicable"
                }
            },
            "required": ["product_id"]
        }
    },
    {
        "name": "view_cart",
        "description": "View current shopping cart contents",
        "permission": "customer",
        "module": "store",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "update_cart_item",
        "description": "Update quantity or remove item from cart",
        "permission": "customer",
        "module": "store",
        "parameters": {
            "type": "object",
            "properties": {
                "item_id": {
                    "type": "integer",
                    "description": "Cart item ID"
                },
                "quantity": {
                    "type": "integer",
                    "description": "New quantity (0 to remove)"
                }
            },
            "required": ["item_id", "quantity"]
        }
    },
    {
        "name": "apply_coupon",
        "description": "Apply a coupon code to the cart",
        "permission": "customer",
        "module": "store",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Coupon code to apply"
                }
            },
            "required": ["code"]
        }
    },
    {
        "name": "get_recommendations",
        "description": "Get product recommendations based on context",
        "permission": "customer",
        "module": "store",
        "parameters": {
            "type": "object",
            "properties": {
                "pet_id": {
                    "type": "integer",
                    "description": "Pet ID for personalized recommendations"
                },
                "category": {
                    "type": "string",
                    "description": "Category to recommend from"
                },
                "based_on": {
                    "type": "string",
                    "enum": ["purchase_history", "cart", "similar_customers"],
                    "description": "Recommendation strategy"
                }
            },
            "required": []
        }
    }
]
```

#### Tool Implementations
```python
from apps.ai_assistant.decorators import tool
from apps.store.models import Product, Cart, CartItem
from apps.store.services import CartService, RecommendationService


@tool(
    name="search_products",
    description="Search for products by name, category, or keywords",
    permission="public",
    module="store"
)
def search_products(
    query: str = None,
    category: str = None,
    species: str = None,
    max_price: float = None,
    limit: int = 5
) -> dict:
    """Search products."""

    products = Product.objects.filter(
        is_active=True,
        is_published=True
    )

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__icontains=query)
        )

    if category:
        products = products.filter(category__slug=category)

    if species:
        products = products.filter(species__contains=[species])

    if max_price:
        products = products.filter(price__lte=max_price)

    products = products[:limit]

    return {
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "slug": p.slug,
                "price": str(p.price),
                "category": p.category.name,
                "in_stock": p.is_in_stock,
                "requires_prescription": p.requires_prescription,
                "image_url": p.primary_image.url if p.primary_image else None
            }
            for p in products
        ],
        "count": len(products),
        "message": f"Encontré {len(products)} productos"
    }


@tool(
    name="get_product_details",
    description="Get detailed information about a specific product",
    permission="public",
    module="store"
)
def get_product_details(product_id: int = None, slug: str = None) -> dict:
    """Get product details."""

    try:
        if product_id:
            product = Product.objects.get(id=product_id, is_active=True)
        elif slug:
            product = Product.objects.get(slug=slug, is_active=True)
        else:
            return {"error": "Necesito el ID o slug del producto"}

        variants = []
        if product.variants.exists():
            variants = [
                {
                    "id": v.id,
                    "name": v.name,
                    "sku": v.sku,
                    "price": str(v.price) if v.price else str(product.price),
                    "in_stock": v.stock_quantity > 0
                }
                for v in product.variants.all()
            ]

        return {
            "id": product.id,
            "name": product.name,
            "slug": product.slug,
            "description": product.description,
            "price": str(product.price),
            "compare_at_price": str(product.compare_at_price) if product.compare_at_price else None,
            "category": product.category.name,
            "species": product.species,
            "in_stock": product.is_in_stock,
            "stock_quantity": product.stock_quantity if product.track_inventory else None,
            "requires_prescription": product.requires_prescription,
            "variants": variants,
            "images": [img.image.url for img in product.images.all()],
            "url": f"/tienda/producto/{product.slug}/"
        }

    except Product.DoesNotExist:
        return {"error": "Producto no encontrado"}


@tool(
    name="add_to_cart",
    description="Add a product to the shopping cart",
    permission="customer",
    module="store"
)
def add_to_cart(
    product_id: int,
    quantity: int = 1,
    variant_id: int = None,
    context=None
) -> dict:
    """Add product to cart."""

    try:
        product = Product.objects.get(id=product_id, is_active=True)

        # Check prescription requirement
        if product.requires_prescription:
            return {
                "success": False,
                "error": "Este producto requiere receta médica",
                "action_required": "prescription_check"
            }

        # Check stock
        if product.track_inventory:
            available = product.stock_quantity
            if variant_id:
                variant = product.variants.get(id=variant_id)
                available = variant.stock_quantity
            if quantity > available:
                return {
                    "success": False,
                    "error": f"Solo hay {available} unidades disponibles"
                }

        # Add to cart
        cart_service = CartService()
        cart = cart_service.get_or_create_cart(context.request)

        variant = None
        if variant_id:
            variant = product.variants.get(id=variant_id)

        item = cart_service.add_item(cart, product, quantity, variant)

        return {
            "success": True,
            "message": f"Agregué {quantity}x {product.name} al carrito",
            "cart_item_id": item.id,
            "cart_total": str(cart.total),
            "cart_count": cart.items.count()
        }

    except Product.DoesNotExist:
        return {"success": False, "error": "Producto no encontrado"}


@tool(
    name="view_cart",
    description="View current shopping cart contents",
    permission="customer",
    module="store"
)
def view_cart(context=None) -> dict:
    """View cart contents."""

    cart_service = CartService()
    cart = cart_service.get_or_create_cart(context.request)

    items = [
        {
            "id": item.id,
            "product_name": item.product.name,
            "variant_name": item.variant.name if item.variant else None,
            "quantity": item.quantity,
            "unit_price": str(item.unit_price),
            "line_total": str(item.line_total),
            "image_url": item.product.primary_image.url if item.product.primary_image else None
        }
        for item in cart.items.select_related('product', 'variant').all()
    ]

    return {
        "items": items,
        "subtotal": str(cart.subtotal),
        "discount": str(cart.discount_amount),
        "tax": str(cart.tax_amount),
        "total": str(cart.total),
        "item_count": len(items),
        "coupon_applied": cart.coupon.code if cart.coupon else None,
        "checkout_url": "/checkout/" if items else None,
        "message": f"Tu carrito tiene {len(items)} productos por ${cart.total}" if items else "Tu carrito está vacío"
    }


@tool(
    name="apply_coupon",
    description="Apply a coupon code to the cart",
    permission="customer",
    module="store"
)
def apply_coupon(code: str, context=None) -> dict:
    """Apply coupon to cart."""

    cart_service = CartService()
    cart = cart_service.get_or_create_cart(context.request)

    success = cart_service.apply_coupon(cart, code)

    if success:
        return {
            "success": True,
            "message": f"Cupón '{code}' aplicado",
            "discount": str(cart.discount_amount),
            "new_total": str(cart.total)
        }
    else:
        return {
            "success": False,
            "error": "Cupón inválido o expirado"
        }


@tool(
    name="get_recommendations",
    description="Get personalized product recommendations",
    permission="customer",
    module="store"
)
def get_recommendations(
    pet_id: int = None,
    category: str = None,
    based_on: str = "purchase_history",
    context=None
) -> dict:
    """Get product recommendations."""

    rec_service = RecommendationService()

    if pet_id:
        # Recommendations based on pet's needs
        products = rec_service.for_pet(pet_id)
    elif based_on == "cart":
        cart = CartService().get_or_create_cart(context.request)
        products = rec_service.similar_to_cart(cart)
    elif based_on == "purchase_history":
        products = rec_service.from_purchase_history(context.user)
    else:
        products = rec_service.popular_products(category=category)

    return {
        "recommendations": [
            {
                "id": p.id,
                "name": p.name,
                "price": str(p.price),
                "category": p.category.name,
                "reason": p.recommendation_reason if hasattr(p, 'recommendation_reason') else None
            }
            for p in products[:5]
        ],
        "message": "Aquí tienes algunas recomendaciones"
    }
```

#### Recommendation Service
```python
class RecommendationService:
    """Product recommendation engine."""

    def for_pet(self, pet_id: int) -> QuerySet:
        """Recommend products based on pet profile."""

        from apps.vet_clinic.models import Pet
        pet = Pet.objects.get(id=pet_id)

        products = Product.objects.filter(
            is_active=True,
            species__contains=[pet.species]
        )

        # Age-appropriate products
        if pet.age_years and pet.age_years < 1:
            products = products.filter(tags__icontains='puppy')
        elif pet.age_years and pet.age_years > 7:
            products = products.filter(tags__icontains='senior')

        # Size-appropriate products
        if pet.weight_kg:
            if pet.weight_kg < 10:
                products = products.filter(tags__icontains='small')
            elif pet.weight_kg > 25:
                products = products.filter(tags__icontains='large')

        return products.order_by('-is_featured', '-created_at')[:10]

    def from_purchase_history(self, user) -> QuerySet:
        """Recommend based on past purchases."""

        from apps.store.models import Order, OrderItem

        # Get categories from past purchases
        purchased_categories = OrderItem.objects.filter(
            order__user=user
        ).values_list('product__category_id', flat=True).distinct()

        return Product.objects.filter(
            category_id__in=purchased_categories,
            is_active=True
        ).exclude(
            id__in=OrderItem.objects.filter(
                order__user=user
            ).values_list('product_id', flat=True)
        ).order_by('-is_featured')[:10]

    def similar_to_cart(self, cart) -> QuerySet:
        """Recommend products similar to cart items."""

        cart_categories = cart.items.values_list(
            'product__category_id', flat=True
        ).distinct()

        cart_product_ids = cart.items.values_list('product_id', flat=True)

        return Product.objects.filter(
            category_id__in=cart_categories,
            is_active=True
        ).exclude(id__in=cart_product_ids).order_by('-is_featured')[:10]

    def popular_products(self, category: str = None) -> QuerySet:
        """Get popular products."""

        products = Product.objects.filter(
            is_active=True,
            is_featured=True
        )

        if category:
            products = products.filter(category__slug=category)

        return products.order_by('-created_at')[:10]
```

### Test Cases
- [ ] search_products returns results
- [ ] search_products filters work
- [ ] get_product_details returns product
- [ ] add_to_cart adds item
- [ ] add_to_cart checks stock
- [ ] add_to_cart blocks prescription items
- [ ] view_cart returns contents
- [ ] apply_coupon works
- [ ] get_recommendations returns products

### Definition of Done
- [ ] All tools registered
- [ ] Tools handle errors gracefully
- [ ] Recommendations work
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-036: Product & Category Models
- T-037: Shopping Cart
- T-010: Tool Calling Framework
