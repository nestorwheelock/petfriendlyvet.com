"""Tests for S-005 E-Commerce Store.

Tests validate e-commerce functionality:
- Category model
- Product model with images
- Cart and CartItem
- Order and OrderItem
- Product search and filtering
- Stock management
"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model

User = get_user_model()


# =============================================================================
# Category Model Tests
# =============================================================================

@pytest.mark.django_db
class TestCategoryModel:
    """Tests for the Category model."""

    def test_create_category(self):
        """Can create a category."""
        from apps.store.models import Category

        category = Category.objects.create(
            name='Dog Food',
            name_es='Comida para Perros',
            name_en='Dog Food',
            slug='dog-food'
        )

        assert category.pk is not None
        assert category.name == 'Dog Food'
        assert category.is_active is True

    def test_category_str(self):
        """Category string representation."""
        from apps.store.models import Category

        category = Category.objects.create(
            name='Cat Food',
            name_es='Comida para Gatos',
            name_en='Cat Food',
            slug='cat-food'
        )

        assert str(category) == 'Cat Food'

    def test_category_hierarchy(self):
        """Categories support parent-child hierarchy."""
        from apps.store.models import Category

        parent = Category.objects.create(
            name='Food',
            name_es='Comida',
            name_en='Food',
            slug='food'
        )
        child = Category.objects.create(
            name='Dog Food',
            name_es='Comida para Perros',
            name_en='Dog Food',
            slug='dog-food',
            parent=parent
        )

        assert child.parent == parent
        assert parent.children.count() == 1

    def test_category_ordering(self):
        """Categories are ordered by order field then name."""
        from apps.store.models import Category

        cat_b = Category.objects.create(
            name='B Category', name_es='B', name_en='B',
            slug='b-cat', order=2
        )
        cat_a = Category.objects.create(
            name='A Category', name_es='A', name_en='A',
            slug='a-cat', order=1
        )

        categories = list(Category.objects.all())
        assert categories[0] == cat_a
        assert categories[1] == cat_b


# =============================================================================
# Product Model Tests
# =============================================================================

@pytest.mark.django_db
class TestProductModel:
    """Tests for the Product model."""

    @pytest.fixture
    def category(self):
        from apps.store.models import Category
        return Category.objects.create(
            name='Dog Food',
            name_es='Comida para Perros',
            name_en='Dog Food',
            slug='dog-food'
        )

    def test_create_product(self, category):
        """Can create a product."""
        from apps.store.models import Product

        product = Product.objects.create(
            name='Premium Dog Food',
            name_es='Comida Premium para Perros',
            name_en='Premium Dog Food',
            slug='premium-dog-food',
            category=category,
            price=Decimal('450.00'),
            sku='DOG-FOOD-001',
            stock_quantity=50
        )

        assert product.pk is not None
        assert product.price == Decimal('450.00')
        assert product.is_active is True

    def test_product_str(self, category):
        """Product string representation."""
        from apps.store.models import Product

        product = Product.objects.create(
            name='Premium Dog Food',
            name_es='Comida Premium',
            name_en='Premium Dog Food',
            slug='premium-dog-food',
            category=category,
            price=Decimal('450.00'),
            sku='DOG-FOOD-002'
        )

        assert str(product) == 'Premium Dog Food'

    def test_product_is_in_stock(self, category):
        """Product is_in_stock property works correctly."""
        from apps.store.models import Product

        product = Product.objects.create(
            name='Test Product',
            name_es='Producto',
            name_en='Test Product',
            slug='test-product',
            category=category,
            price=Decimal('100.00'),
            sku='TEST-001',
            stock_quantity=10
        )

        assert product.is_in_stock is True

        product.stock_quantity = 0
        assert product.is_in_stock is False

    def test_product_is_low_stock(self, category):
        """Product is_low_stock property works correctly."""
        from apps.store.models import Product

        product = Product.objects.create(
            name='Test Product',
            name_es='Producto',
            name_en='Test Product',
            slug='test-low-stock',
            category=category,
            price=Decimal('100.00'),
            sku='TEST-002',
            stock_quantity=3,
            low_stock_threshold=5
        )

        assert product.is_low_stock is True

        product.stock_quantity = 10
        assert product.is_low_stock is False

    def test_product_suitable_for_filters(self, category):
        """Product has species/size/age filters."""
        from apps.store.models import Product

        product = Product.objects.create(
            name='Large Breed Dog Food',
            name_es='Comida Raza Grande',
            name_en='Large Breed Dog Food',
            slug='large-breed-food',
            category=category,
            price=Decimal('550.00'),
            sku='DOG-LARGE-001',
            suitable_for_species=['dog'],
            suitable_for_sizes=['large'],
            suitable_for_ages=['adult', 'senior']
        )

        assert 'dog' in product.suitable_for_species
        assert 'large' in product.suitable_for_sizes
        assert 'adult' in product.suitable_for_ages

    def test_product_compare_at_price(self, category):
        """Product can have a compare_at_price for sales."""
        from apps.store.models import Product

        product = Product.objects.create(
            name='Sale Product',
            name_es='Producto en Oferta',
            name_en='Sale Product',
            slug='sale-product',
            category=category,
            price=Decimal('80.00'),
            compare_at_price=Decimal('100.00'),
            sku='SALE-001'
        )

        assert product.price == Decimal('80.00')
        assert product.compare_at_price == Decimal('100.00')


# =============================================================================
# ProductImage Model Tests
# =============================================================================

@pytest.mark.django_db
class TestProductImageModel:
    """Tests for the ProductImage model."""

    @pytest.fixture
    def product(self):
        from apps.store.models import Category, Product
        category = Category.objects.create(
            name='Test', name_es='Test', name_en='Test', slug='test-cat'
        )
        return Product.objects.create(
            name='Test Product',
            name_es='Producto',
            name_en='Test Product',
            slug='test-img-product',
            category=category,
            price=Decimal('100.00'),
            sku='IMG-TEST-001'
        )

    def test_create_product_image(self, product):
        """Can create a product image."""
        from apps.store.models import ProductImage

        image = ProductImage.objects.create(
            product=product,
            alt_text='Product image',
            is_primary=True
        )

        assert image.pk is not None
        assert image.product == product
        assert image.is_primary is True

    def test_product_images_ordering(self, product):
        """Product images are ordered by order field."""
        from apps.store.models import ProductImage

        img2 = ProductImage.objects.create(
            product=product, alt_text='Second', order=2
        )
        img1 = ProductImage.objects.create(
            product=product, alt_text='First', order=1
        )

        images = list(product.images.all())
        assert images[0] == img1
        assert images[1] == img2


# =============================================================================
# Cart Model Tests
# =============================================================================

@pytest.mark.django_db
class TestCartModel:
    """Tests for the Cart model."""

    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='shopper',
            email='shopper@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def category(self):
        from apps.store.models import Category
        return Category.objects.create(
            name='Products', name_es='Productos', name_en='Products',
            slug='products'
        )

    @pytest.fixture
    def product(self, category):
        from apps.store.models import Product
        return Product.objects.create(
            name='Test Product',
            name_es='Producto',
            name_en='Test Product',
            slug='cart-test-product',
            category=category,
            price=Decimal('100.00'),
            sku='CART-TEST-001',
            stock_quantity=50
        )

    def test_create_cart_for_user(self, user):
        """Can create a cart for a logged-in user."""
        from apps.store.models import Cart

        cart = Cart.objects.create(user=user)

        assert cart.pk is not None
        assert cart.user == user

    def test_create_cart_for_session(self):
        """Can create a cart for anonymous session."""
        from apps.store.models import Cart

        cart = Cart.objects.create(session_key='abc123')

        assert cart.pk is not None
        assert cart.session_key == 'abc123'
        assert cart.user is None

    def test_cart_total(self, user, product):
        """Cart total is calculated correctly."""
        from apps.store.models import Cart, CartItem

        cart = Cart.objects.create(user=user)
        CartItem.objects.create(cart=cart, product=product, quantity=2)

        assert cart.total == Decimal('200.00')

    def test_cart_item_count(self, user, product):
        """Cart item_count returns sum of quantities."""
        from apps.store.models import Cart, CartItem, Product, Category

        cart = Cart.objects.create(user=user)
        CartItem.objects.create(cart=cart, product=product, quantity=2)

        # Create another product
        product2 = Product.objects.create(
            name='Product 2',
            name_es='Producto 2',
            name_en='Product 2',
            slug='product-2',
            category=product.category,
            price=Decimal('50.00'),
            sku='CART-TEST-002'
        )
        CartItem.objects.create(cart=cart, product=product2, quantity=3)

        assert cart.item_count == 5


# =============================================================================
# CartItem Model Tests
# =============================================================================

@pytest.mark.django_db
class TestCartItemModel:
    """Tests for the CartItem model."""

    @pytest.fixture
    def cart(self):
        from apps.store.models import Cart
        return Cart.objects.create(session_key='test-session')

    @pytest.fixture
    def product(self):
        from apps.store.models import Category, Product
        category = Category.objects.create(
            name='Test', name_es='Test', name_en='Test', slug='test-item-cat'
        )
        return Product.objects.create(
            name='Test Product',
            name_es='Producto',
            name_en='Test Product',
            slug='cart-item-product',
            category=category,
            price=Decimal('75.50'),
            sku='ITEM-TEST-001'
        )

    def test_create_cart_item(self, cart, product):
        """Can create a cart item."""
        from apps.store.models import CartItem

        item = CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=2
        )

        assert item.pk is not None
        assert item.quantity == 2

    def test_cart_item_subtotal(self, cart, product):
        """CartItem subtotal is calculated correctly."""
        from apps.store.models import CartItem

        item = CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=3
        )

        # 75.50 * 3 = 226.50
        assert item.subtotal == Decimal('226.50')


# =============================================================================
# Order Model Tests
# =============================================================================

@pytest.mark.django_db
class TestOrderModel:
    """Tests for the Order model."""

    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='buyer',
            email='buyer@example.com',
            password='testpass123'
        )

    def test_create_order(self, user):
        """Can create an order."""
        from apps.store.models import Order

        order = Order.objects.create(
            user=user,
            order_number='ORD-2025-0001',
            fulfillment_method='pickup',
            subtotal=Decimal('500.00'),
            tax=Decimal('80.00'),
            total=Decimal('580.00')
        )

        assert order.pk is not None
        assert order.status == 'pending'
        assert order.order_number == 'ORD-2025-0001'

    def test_order_str(self, user):
        """Order string representation."""
        from apps.store.models import Order

        order = Order.objects.create(
            user=user,
            order_number='ORD-2025-0002',
            fulfillment_method='pickup',
            subtotal=Decimal('100.00'),
            tax=Decimal('16.00'),
            total=Decimal('116.00')
        )

        assert 'ORD-2025-0002' in str(order)

    def test_order_with_delivery(self, user):
        """Order can have delivery information."""
        from apps.store.models import Order

        order = Order.objects.create(
            user=user,
            order_number='ORD-2025-0003',
            fulfillment_method='delivery',
            shipping_name='Juan Pérez',
            shipping_address='Av. Principal 123, Puerto Morelos',
            shipping_phone='998-123-4567',
            subtotal=Decimal('400.00'),
            shipping_cost=Decimal('50.00'),
            tax=Decimal('72.00'),
            total=Decimal('522.00')
        )

        assert order.fulfillment_method == 'delivery'
        assert order.shipping_name == 'Juan Pérez'
        assert order.shipping_cost == Decimal('50.00')

    def test_order_statuses(self, user):
        """Order can transition through statuses."""
        from apps.store.models import Order

        order = Order.objects.create(
            user=user,
            order_number='ORD-2025-0004',
            fulfillment_method='pickup',
            subtotal=Decimal('100.00'),
            tax=Decimal('16.00'),
            total=Decimal('116.00')
        )

        assert order.status == 'pending'

        order.status = 'paid'
        order.save()
        order.refresh_from_db()
        assert order.status == 'paid'

        order.status = 'ready'
        order.save()
        order.refresh_from_db()
        assert order.status == 'ready'

    def test_order_payment_methods(self, user):
        """Order supports different payment methods."""
        from apps.store.models import Order

        # Cash payment (default)
        order_cash = Order.objects.create(
            user=user,
            order_number='ORD-2025-CASH',
            fulfillment_method='pickup',
            payment_method='cash',
            subtotal=Decimal('100.00'),
            tax=Decimal('16.00'),
            total=Decimal('116.00')
        )
        assert order_cash.payment_method == 'cash'
        assert order_cash.status == 'pending'

        # Card payment
        order_card = Order.objects.create(
            user=user,
            order_number='ORD-2025-CARD',
            fulfillment_method='pickup',
            payment_method='card',
            subtotal=Decimal('100.00'),
            tax=Decimal('16.00'),
            total=Decimal('116.00')
        )
        assert order_card.payment_method == 'card'

        # Transfer payment
        order_transfer = Order.objects.create(
            user=user,
            order_number='ORD-2025-XFER',
            fulfillment_method='delivery',
            payment_method='transfer',
            subtotal=Decimal('100.00'),
            shipping_cost=Decimal('50.00'),
            tax=Decimal('16.00'),
            total=Decimal('166.00')
        )
        assert order_transfer.payment_method == 'transfer'

    def test_create_from_cart_with_payment_method(self, user):
        """Order creation from cart respects payment method."""
        from apps.store.models import Order, Cart, Category, Product

        category = Category.objects.create(
            name='Test', name_es='Test', name_en='Test', slug='pay-method-cat'
        )
        product = Product.objects.create(
            name='Test Product',
            name_es='Producto',
            name_en='Test Product',
            slug='pay-method-product',
            category=category,
            price=Decimal('100.00'),
            sku='PAY-TEST-001',
            stock_quantity=10
        )
        cart = Cart.objects.create(user=user)
        cart.add_item(product, 1)

        # Cash order stays pending
        order_cash = Order.create_from_cart(
            cart=cart,
            user=user,
            fulfillment_method='pickup',
            payment_method='cash'
        )
        assert order_cash.payment_method == 'cash'
        assert order_cash.status == 'pending'
        assert order_cash.paid_at is None

        # Create new cart for card test
        cart2 = Cart.objects.create(user=user)
        cart2.add_item(product, 1)

        # Card order is auto-paid
        order_card = Order.create_from_cart(
            cart=cart2,
            user=user,
            fulfillment_method='pickup',
            payment_method='card'
        )
        assert order_card.payment_method == 'card'
        assert order_card.status == 'paid'
        assert order_card.paid_at is not None


# =============================================================================
# OrderItem Model Tests
# =============================================================================

@pytest.mark.django_db
class TestOrderItemModel:
    """Tests for the OrderItem model."""

    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='orderer',
            email='orderer@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def order(self, user):
        from apps.store.models import Order
        return Order.objects.create(
            user=user,
            order_number='ORD-ITEM-001',
            fulfillment_method='pickup',
            subtotal=Decimal('200.00'),
            tax=Decimal('32.00'),
            total=Decimal('232.00')
        )

    @pytest.fixture
    def product(self):
        from apps.store.models import Category, Product
        category = Category.objects.create(
            name='Test', name_es='Test', name_en='Test', slug='order-item-cat'
        )
        return Product.objects.create(
            name='Order Product',
            name_es='Producto',
            name_en='Order Product',
            slug='order-item-product',
            category=category,
            price=Decimal('100.00'),
            sku='ORDER-ITEM-001'
        )

    def test_create_order_item(self, order, product):
        """Can create an order item."""
        from apps.store.models import OrderItem

        item = OrderItem.objects.create(
            order=order,
            product=product,
            product_name='Order Product',
            price=Decimal('100.00'),
            quantity=2
        )

        assert item.pk is not None
        assert item.product_name == 'Order Product'

    def test_order_item_subtotal(self, order, product):
        """OrderItem subtotal is calculated correctly."""
        from apps.store.models import OrderItem

        item = OrderItem.objects.create(
            order=order,
            product=product,
            product_name='Order Product',
            price=Decimal('100.00'),
            quantity=2
        )

        assert item.subtotal == Decimal('200.00')

    def test_order_item_preserves_price(self, order, product):
        """OrderItem preserves price at time of order."""
        from apps.store.models import OrderItem

        item = OrderItem.objects.create(
            order=order,
            product=product,
            product_name='Order Product',
            price=Decimal('100.00'),
            quantity=1
        )

        # Product price changes
        product.price = Decimal('150.00')
        product.save()

        # Order item price stays the same
        item.refresh_from_db()
        assert item.price == Decimal('100.00')


# =============================================================================
# Product Search and Filtering Tests
# =============================================================================

@pytest.mark.django_db
class TestProductSearchAndFiltering:
    """Tests for product search and filtering."""

    @pytest.fixture
    def products(self):
        from apps.store.models import Category, Product

        food_cat = Category.objects.create(
            name='Food', name_es='Comida', name_en='Food', slug='food'
        )
        toys_cat = Category.objects.create(
            name='Toys', name_es='Juguetes', name_en='Toys', slug='toys'
        )

        products = []
        products.append(Product.objects.create(
            name='Dog Food Premium',
            name_es='Comida Premium Perro',
            name_en='Dog Food Premium',
            slug='dog-food-premium',
            category=food_cat,
            price=Decimal('450.00'),
            sku='SEARCH-001',
            stock_quantity=20,
            suitable_for_species=['dog'],
            suitable_for_sizes=['medium', 'large'],
            is_active=True
        ))
        products.append(Product.objects.create(
            name='Cat Food Deluxe',
            name_es='Comida Deluxe Gato',
            name_en='Cat Food Deluxe',
            slug='cat-food-deluxe',
            category=food_cat,
            price=Decimal('350.00'),
            sku='SEARCH-002',
            stock_quantity=15,
            suitable_for_species=['cat'],
            is_active=True
        ))
        products.append(Product.objects.create(
            name='Dog Chew Toy',
            name_es='Juguete Masticable',
            name_en='Dog Chew Toy',
            slug='dog-chew-toy',
            category=toys_cat,
            price=Decimal('120.00'),
            sku='SEARCH-003',
            stock_quantity=30,
            suitable_for_species=['dog'],
            is_active=True
        ))
        products.append(Product.objects.create(
            name='Inactive Product',
            name_es='Producto Inactivo',
            name_en='Inactive Product',
            slug='inactive-product',
            category=food_cat,
            price=Decimal('100.00'),
            sku='SEARCH-004',
            is_active=False
        ))

        return products

    def test_filter_by_category(self, products):
        """Can filter products by category."""
        from apps.store.models import Product, Category

        food_cat = Category.objects.get(slug='food')
        food_products = Product.objects.filter(
            category=food_cat, is_active=True
        )

        assert food_products.count() == 2

    def test_filter_by_species(self, products):
        """Can filter products by species."""
        from apps.store.models import Product

        # Filter products that have 'dog' in suitable_for_species
        # Use icontains for SQLite compatibility
        dog_products = [
            p for p in Product.objects.filter(is_active=True)
            if 'dog' in p.suitable_for_species
        ]

        assert len(dog_products) == 2

    def test_filter_active_only(self, products):
        """Only active products are shown by default."""
        from apps.store.models import Product

        active = Product.objects.filter(is_active=True)
        all_products = Product.objects.all()

        assert active.count() == 3
        assert all_products.count() == 4

    def test_search_by_name(self, products):
        """Can search products by name."""
        from apps.store.models import Product

        results = Product.objects.filter(
            name__icontains='dog',
            is_active=True
        )

        assert results.count() == 2

    def test_filter_by_price_range(self, products):
        """Can filter products by price range."""
        from apps.store.models import Product

        results = Product.objects.filter(
            price__gte=Decimal('100.00'),
            price__lte=Decimal('400.00'),
            is_active=True
        )

        assert results.count() == 2  # Cat food (350) and Dog toy (120)


# =============================================================================
# Store View Tests
# =============================================================================

@pytest.mark.django_db
class TestStoreViews:
    """Tests for store views."""

    @pytest.fixture
    def category(self):
        from apps.store.models import Category
        return Category.objects.create(
            name='Dog Food',
            name_es='Comida para Perros',
            name_en='Dog Food',
            slug='dog-food',
            is_active=True
        )

    @pytest.fixture
    def product(self, category):
        from apps.store.models import Product
        return Product.objects.create(
            name='Premium Dog Food',
            name_es='Comida Premium',
            name_en='Premium Dog Food',
            slug='premium-dog-food',
            category=category,
            price=Decimal('450.00'),
            sku='VIEW-TEST-001',
            stock_quantity=20,
            is_active=True
        )

    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='shopper',
            email='shopper@example.com',
            password='testpass123'
        )

    def test_product_list_view(self, client, product):
        """Product list view shows active products."""
        from django.urls import reverse
        url = reverse('store:product_list')
        response = client.get(url)

        assert response.status_code == 200
        assert b'Premium Dog Food' in response.content

    def test_product_list_filters_inactive(self, client, category):
        """Product list view only shows active products."""
        from apps.store.models import Product
        from django.urls import reverse

        Product.objects.create(
            name='Inactive Product',
            name_es='Inactivo',
            name_en='Inactive',
            slug='inactive-view',
            category=category,
            price=Decimal('100.00'),
            sku='INACTIVE-001',
            is_active=False
        )

        url = reverse('store:product_list')
        response = client.get(url)

        assert response.status_code == 200
        assert b'Inactive Product' not in response.content

    def test_product_detail_view(self, client, product):
        """Product detail view shows product info."""
        from django.urls import reverse
        url = reverse('store:product_detail', kwargs={'slug': product.slug})
        response = client.get(url)

        assert response.status_code == 200
        assert b'Premium Dog Food' in response.content
        # Price may be formatted with comma or period depending on locale
        assert b'450' in response.content

    def test_category_view(self, client, product, category):
        """Category view shows products in category."""
        from django.urls import reverse
        url = reverse('store:category_detail', kwargs={'slug': category.slug})
        response = client.get(url)

        assert response.status_code == 200
        assert b'Premium Dog Food' in response.content

    def test_cart_view_empty(self, client):
        """Cart view shows empty cart."""
        from django.urls import reverse
        url = reverse('store:cart')
        response = client.get(url)

        assert response.status_code == 200

    def test_add_to_cart(self, client, product):
        """Can add product to cart."""
        from django.urls import reverse
        url = reverse('store:add_to_cart', kwargs={'product_id': product.pk})
        response = client.post(url, {'quantity': 2})

        # Should redirect to cart
        assert response.status_code == 302

    def test_cart_shows_items(self, client, product):
        """Cart shows added items."""
        from apps.store.models import Cart, CartItem
        from django.urls import reverse

        # Create a cart with session
        session = client.session
        session.create()
        cart = Cart.objects.create(session_key=session.session_key)
        CartItem.objects.create(cart=cart, product=product, quantity=2)

        url = reverse('store:cart')
        response = client.get(url)

        assert response.status_code == 200

    def test_update_cart_quantity(self, client, product):
        """Can update cart item quantity."""
        from apps.store.models import Cart, CartItem
        from django.urls import reverse

        session = client.session
        session.create()
        cart = Cart.objects.create(session_key=session.session_key)
        CartItem.objects.create(cart=cart, product=product, quantity=1)

        url = reverse('store:update_cart')
        response = client.post(url, {
            'product_id': product.pk,
            'quantity': 3
        })

        assert response.status_code == 302

    def test_remove_from_cart(self, client, product):
        """Can remove item from cart."""
        from apps.store.models import Cart, CartItem
        from django.urls import reverse

        session = client.session
        session.create()
        cart = Cart.objects.create(session_key=session.session_key)
        CartItem.objects.create(cart=cart, product=product, quantity=1)

        url = reverse('store:remove_from_cart', kwargs={'product_id': product.pk})
        response = client.post(url)

        assert response.status_code == 302


@pytest.mark.django_db
class TestCheckoutViews:
    """Tests for checkout views."""

    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='buyer',
            email='buyer@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def cart_with_items(self, user):
        from apps.store.models import Cart, CartItem, Category, Product

        category = Category.objects.create(
            name='Test', name_es='Test', name_en='Test', slug='checkout-cat'
        )
        product = Product.objects.create(
            name='Checkout Product',
            name_es='Producto',
            name_en='Checkout Product',
            slug='checkout-product',
            category=category,
            price=Decimal('100.00'),
            sku='CHECKOUT-001',
            stock_quantity=10
        )

        cart = Cart.objects.create(user=user)
        CartItem.objects.create(cart=cart, product=product, quantity=2)

        return cart

    def test_checkout_requires_login(self, client):
        """Checkout requires authentication."""
        from django.urls import reverse
        url = reverse('store:checkout')
        response = client.get(url)

        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_checkout_view_logged_in(self, client, user, cart_with_items):
        """Logged in user can access checkout."""
        from django.urls import reverse

        client.force_login(user)
        url = reverse('store:checkout')
        response = client.get(url)

        assert response.status_code == 200


@pytest.mark.django_db
class TestOrderViews:
    """Tests for order views."""

    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='orderer',
            email='orderer@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def order(self, user):
        from apps.store.models import Order
        return Order.objects.create(
            user=user,
            order_number='ORD-VIEW-001',
            fulfillment_method='pickup',
            subtotal=Decimal('100.00'),
            tax=Decimal('16.00'),
            total=Decimal('116.00'),
            status='paid'
        )

    def test_order_list_requires_login(self, client):
        """Order list requires authentication."""
        from django.urls import reverse
        url = reverse('store:order_list')
        response = client.get(url)

        assert response.status_code == 302

    def test_order_list_shows_user_orders(self, client, user, order):
        """Order list shows user's orders."""
        from django.urls import reverse

        client.force_login(user)
        url = reverse('store:order_list')
        response = client.get(url)

        assert response.status_code == 200
        assert b'ORD-VIEW-001' in response.content

    def test_order_detail_view(self, client, user, order):
        """Order detail shows order info."""
        from django.urls import reverse

        client.force_login(user)
        url = reverse('store:order_detail', kwargs={'order_number': order.order_number})
        response = client.get(url)

        assert response.status_code == 200
        assert b'ORD-VIEW-001' in response.content

    def test_cannot_view_other_user_order(self, client, order):
        """Cannot view another user's order."""
        from django.urls import reverse

        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass'
        )
        client.force_login(other_user)

        url = reverse('store:order_detail', kwargs={'order_number': order.order_number})
        response = client.get(url)

        assert response.status_code == 404


# =============================================================================
# AI Store Tools Tests
# =============================================================================

@pytest.mark.django_db
class TestStoreAITools:
    """Tests for store-related AI tools."""

    @pytest.fixture
    def category(self):
        """Create a test category."""
        from apps.store.models import Category
        return Category.objects.create(
            name='Pet Food',
            name_es='Comida para Mascotas',
            slug='pet-food'
        )

    @pytest.fixture
    def products(self, category):
        """Create test products."""
        from apps.store.models import Product
        from decimal import Decimal
        import uuid

        products = []
        products.append(Product.objects.create(
            name='Dog Food Premium',
            name_es='Comida para Perros Premium',
            slug='dog-food-premium',
            sku=f'DOG-FOOD-{uuid.uuid4().hex[:8].upper()}',
            category=category,
            price=Decimal('450.00'),
            stock_quantity=100,
            suitable_for_species=['dog'],
            is_featured=True
        ))
        products.append(Product.objects.create(
            name='Cat Food Deluxe',
            name_es='Comida para Gatos Deluxe',
            slug='cat-food-deluxe',
            sku=f'CAT-FOOD-{uuid.uuid4().hex[:8].upper()}',
            category=category,
            price=Decimal('350.00'),
            compare_at_price=Decimal('400.00'),
            stock_quantity=50,
            suitable_for_species=['cat']
        ))
        products.append(Product.objects.create(
            name='Universal Treats',
            name_es='Premios Universales',
            slug='universal-treats',
            sku=f'TREATS-{uuid.uuid4().hex[:8].upper()}',
            category=category,
            price=Decimal('150.00'),
            stock_quantity=0,  # Out of stock
            suitable_for_species=['dog', 'cat']
        ))
        return products

    @pytest.fixture
    def user(self):
        """Create a test user."""
        return User.objects.create_user(
            username='aitools_test',
            email='aitools@test.com',
            password='testpass123'
        )

    @pytest.fixture
    def pet(self, user):
        """Create a test pet."""
        from apps.pets.models import Pet
        return Pet.objects.create(
            name='Buddy',
            species='dog',
            owner=user
        )

    # --- search_products tests ---

    def test_search_products_basic(self, products):
        """Search products returns results."""
        from apps.ai_assistant.tools import search_products

        result = search_products()

        # Should return 2 in-stock products (excludes out of stock by default)
        assert 'products' in result
        assert result['count'] == 2

    def test_search_products_by_query(self, products):
        """Search products by text query."""
        from apps.ai_assistant.tools import search_products

        result = search_products(query='Dog')

        assert result['count'] == 1
        assert result['products'][0]['name'] == 'Dog Food Premium'

    def test_search_products_by_species(self, products):
        """Search products by species."""
        from apps.ai_assistant.tools import search_products

        result = search_products(species='cat')

        assert result['count'] == 1
        assert 'Cat' in result['products'][0]['name']

    def test_search_products_by_category(self, category, products):
        """Search products by category slug."""
        from apps.ai_assistant.tools import search_products

        result = search_products(category='pet-food')

        assert result['count'] == 2

    def test_search_products_include_out_of_stock(self, products):
        """Search products including out of stock."""
        from apps.ai_assistant.tools import search_products

        result = search_products(in_stock_only=False)

        assert result['count'] == 3

    def test_search_products_by_max_price(self, products):
        """Search products with max price filter."""
        from apps.ai_assistant.tools import search_products

        result = search_products(max_price=200, in_stock_only=False)

        assert result['count'] == 1
        assert result['products'][0]['name'] == 'Universal Treats'

    # --- get_product_details tests ---

    def test_get_product_details_by_id(self, products):
        """Get product details by ID."""
        from apps.ai_assistant.tools import get_product_details

        product = products[0]
        result = get_product_details(product_id=product.id)

        assert result['id'] == product.id
        assert result['name'] == 'Dog Food Premium'
        assert result['price'] == '450.00'
        assert result['is_in_stock'] is True

    def test_get_product_details_by_slug(self, products):
        """Get product details by slug."""
        from apps.ai_assistant.tools import get_product_details

        result = get_product_details(slug='cat-food-deluxe')

        assert result['name'] == 'Cat Food Deluxe'
        assert result['compare_at_price'] == '400.00'  # Has compare_at_price
        assert result['discount_percentage'] > 0  # Indicates sale

    def test_get_product_details_not_found(self):
        """Get product details for non-existent product."""
        from apps.ai_assistant.tools import get_product_details

        result = get_product_details(product_id=99999)

        assert 'error' in result
        assert 'not found' in result['error']

    def test_get_product_details_requires_id_or_slug(self):
        """Get product details requires either product_id or slug."""
        from apps.ai_assistant.tools import get_product_details

        result = get_product_details()

        assert 'error' in result
        assert 'required' in result['error']

    # --- get_store_categories tests ---

    def test_get_store_categories(self, category):
        """Get store categories."""
        from apps.ai_assistant.tools import get_store_categories

        result = get_store_categories()

        assert 'categories' in result
        assert len(result['categories']) >= 1
        category_names = [c['name'] for c in result['categories']]
        assert 'Pet Food' in category_names

    def test_get_store_categories_with_count(self, category, products):
        """Get store categories with product count."""
        from apps.ai_assistant.tools import get_store_categories

        result = get_store_categories(include_product_count=True)

        pet_food_cat = next(c for c in result['categories'] if c['name'] == 'Pet Food')
        assert 'product_count' in pet_food_cat
        assert pet_food_cat['product_count'] == 3

    def test_get_store_categories_with_subcategories(self, category):
        """Get store categories with subcategories."""
        from apps.store.models import Category
        from apps.ai_assistant.tools import get_store_categories

        # Create subcategory
        Category.objects.create(
            name='Dog Food',
            name_es='Comida para Perros',
            slug='dog-food',
            parent=category
        )

        result = get_store_categories()

        pet_food_cat = next(c for c in result['categories'] if c['name'] == 'Pet Food')
        assert 'subcategories' in pet_food_cat
        assert len(pet_food_cat['subcategories']) == 1

    # --- get_user_cart tests ---

    def test_get_user_cart_empty(self, user):
        """Get empty user cart."""
        from apps.ai_assistant.tools import get_user_cart

        result = get_user_cart(user_id=user.id)

        assert 'cart_id' in result
        assert result['item_count'] == 0
        # Empty cart returns '0' (Decimal to string)
        assert result['total'] in ('0', '0.00')
        assert result['items'] == []

    def test_get_user_cart_with_items(self, user, products):
        """Get user cart with items."""
        from apps.store.models import Cart
        from apps.ai_assistant.tools import get_user_cart

        cart = Cart.objects.create(user=user)
        cart.add_item(products[0], quantity=2)

        result = get_user_cart(user_id=user.id)

        assert result['item_count'] == 2
        assert len(result['items']) == 1
        assert result['items'][0]['product_name'] == 'Dog Food Premium'
        assert result['items'][0]['quantity'] == 2

    def test_get_user_cart_user_not_found(self):
        """Get cart for non-existent user."""
        from apps.ai_assistant.tools import get_user_cart

        result = get_user_cart(user_id=99999)

        assert 'error' in result
        assert 'not found' in result['error']

    # --- add_product_to_cart tests ---

    def test_add_product_to_cart(self, user, products):
        """Add product to cart."""
        from apps.ai_assistant.tools import add_product_to_cart

        result = add_product_to_cart(
            user_id=user.id,
            product_id=products[0].id,
            quantity=1
        )

        assert result['success'] is True
        assert 'Dog Food Premium' in result['message']
        assert result['cart_item_count'] == 1

    def test_add_product_to_cart_multiple_quantity(self, user, products):
        """Add multiple quantity of product to cart."""
        from apps.ai_assistant.tools import add_product_to_cart

        result = add_product_to_cart(
            user_id=user.id,
            product_id=products[0].id,
            quantity=3
        )

        assert result['success'] is True
        assert result['cart_item_count'] == 3

    def test_add_product_to_cart_out_of_stock(self, user, products):
        """Cannot add out of stock product to cart."""
        from apps.ai_assistant.tools import add_product_to_cart

        # products[2] is out of stock
        result = add_product_to_cart(
            user_id=user.id,
            product_id=products[2].id,
            quantity=1
        )

        assert 'error' in result
        assert 'stock' in result['error'].lower()

    def test_add_product_to_cart_user_not_found(self, products):
        """Cannot add product for non-existent user."""
        from apps.ai_assistant.tools import add_product_to_cart

        result = add_product_to_cart(
            user_id=99999,
            product_id=products[0].id,
            quantity=1
        )

        assert 'error' in result
        assert 'not found' in result['error']

    def test_add_product_to_cart_product_not_found(self, user):
        """Cannot add non-existent product to cart."""
        from apps.ai_assistant.tools import add_product_to_cart

        result = add_product_to_cart(
            user_id=user.id,
            product_id=99999,
            quantity=1
        )

        assert 'error' in result
        assert 'not found' in result['error']

    # --- get_user_orders tests ---

    def test_get_user_orders_empty(self, user):
        """Get orders for user with no orders."""
        from apps.ai_assistant.tools import get_user_orders

        result = get_user_orders(user_id=user.id)

        assert result['orders'] == []
        assert result['count'] == 0

    def test_get_user_orders_with_orders(self, user):
        """Get orders for user with orders."""
        from apps.store.models import Order
        from decimal import Decimal
        from apps.ai_assistant.tools import get_user_orders

        Order.objects.create(
            user=user,
            order_number='ORD-2025-001',
            fulfillment_method='pickup',
            payment_method='cash',
            subtotal=Decimal('100.00'),
            tax=Decimal('16.00'),
            total=Decimal('116.00')
        )

        result = get_user_orders(user_id=user.id)

        assert result['count'] == 1
        assert result['orders'][0]['order_number'] == 'ORD-2025-001'

    def test_get_user_orders_filtered_by_status(self, user):
        """Get orders filtered by status."""
        from apps.store.models import Order
        from decimal import Decimal
        from apps.ai_assistant.tools import get_user_orders

        Order.objects.create(
            user=user,
            order_number='ORD-PENDING',
            fulfillment_method='pickup',
            status='pending',
            subtotal=Decimal('100.00'),
            tax=Decimal('16.00'),
            total=Decimal('116.00')
        )
        Order.objects.create(
            user=user,
            order_number='ORD-PAID',
            fulfillment_method='pickup',
            status='paid',
            subtotal=Decimal('200.00'),
            tax=Decimal('32.00'),
            total=Decimal('232.00')
        )

        result = get_user_orders(user_id=user.id, status='paid')

        assert result['count'] == 1
        assert result['orders'][0]['order_number'] == 'ORD-PAID'

    def test_get_user_orders_user_not_found(self):
        """Get orders for non-existent user."""
        from apps.ai_assistant.tools import get_user_orders

        result = get_user_orders(user_id=99999)

        assert 'error' in result
        assert 'not found' in result['error']

    # --- get_order_details tests ---

    def test_get_order_details(self, user, products):
        """Get order details."""
        from apps.store.models import Order, OrderItem
        from decimal import Decimal
        from apps.ai_assistant.tools import get_order_details

        order = Order.objects.create(
            user=user,
            order_number='ORD-DETAIL-001',
            fulfillment_method='pickup',
            payment_method='cash',
            subtotal=Decimal('450.00'),
            tax=Decimal('72.00'),
            total=Decimal('522.00')
        )
        OrderItem.objects.create(
            order=order,
            product=products[0],
            product_name=products[0].name,
            product_sku=products[0].sku,
            quantity=1,
            price=products[0].price
        )

        result = get_order_details(user_id=user.id, order_number='ORD-DETAIL-001')

        assert result['order_number'] == 'ORD-DETAIL-001'
        assert result['status'] == 'pending'
        assert result['total'] == '522.00'
        assert len(result['items']) == 1
        assert result['items'][0]['product_name'] == 'Dog Food Premium'

    def test_get_order_details_access_denied(self, user, products):
        """Cannot get details of another user's order."""
        from apps.store.models import Order
        from decimal import Decimal
        from apps.ai_assistant.tools import get_order_details

        other_user = User.objects.create_user(
            username='other_order_user',
            email='other_order@test.com',
            password='testpass'
        )
        Order.objects.create(
            user=other_user,
            order_number='ORD-OTHER-001',
            fulfillment_method='pickup',
            subtotal=Decimal('100.00'),
            tax=Decimal('16.00'),
            total=Decimal('116.00')
        )

        result = get_order_details(user_id=user.id, order_number='ORD-OTHER-001')

        assert 'error' in result
        assert 'denied' in result['error'].lower()

    def test_get_order_details_not_found(self, user):
        """Get details for non-existent order."""
        from apps.ai_assistant.tools import get_order_details

        result = get_order_details(user_id=user.id, order_number='ORD-NOTEXIST')

        assert 'error' in result
        assert 'not found' in result['error']

    # --- get_product_recommendations tests ---

    def test_get_product_recommendations(self, user, pet, products):
        """Get product recommendations for pet."""
        from apps.ai_assistant.tools import get_product_recommendations

        result = get_product_recommendations(pet_id=pet.id, user_id=user.id)

        assert result['pet_name'] == 'Buddy'
        assert result['pet_species'] == 'dog'
        assert 'recommendations' in result
        # Should recommend dog-suitable products
        product_names = [r['name'] for r in result['recommendations']]
        assert 'Dog Food Premium' in product_names

    def test_get_product_recommendations_with_category(self, user, pet, category, products):
        """Get product recommendations filtered by category."""
        from apps.ai_assistant.tools import get_product_recommendations

        result = get_product_recommendations(
            pet_id=pet.id,
            user_id=user.id,
            category='pet-food'
        )

        assert 'recommendations' in result
        # All recommendations should be from pet-food category
        for rec in result['recommendations']:
            assert rec['category'] == 'Pet Food'

    def test_get_product_recommendations_pet_not_found(self, user):
        """Get recommendations for non-existent pet."""
        from apps.ai_assistant.tools import get_product_recommendations

        result = get_product_recommendations(pet_id=99999, user_id=user.id)

        assert 'error' in result
        assert 'not found' in result['error']

    def test_get_product_recommendations_access_denied(self, user, products):
        """Cannot get recommendations for another user's pet."""
        from apps.pets.models import Pet
        from apps.ai_assistant.tools import get_product_recommendations

        other_user = User.objects.create_user(
            username='other_pet_user',
            email='other_pet@test.com',
            password='testpass'
        )
        other_pet = Pet.objects.create(
            name='OtherPet',
            species='cat',
            owner=other_user
        )

        result = get_product_recommendations(pet_id=other_pet.id, user_id=user.id)

        assert 'error' in result
        assert 'denied' in result['error'].lower()
