"""Tests for the store app."""
from decimal import Decimal
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import Category, Product, Cart, CartItem, Order, StoreSettings

User = get_user_model()


class ProductModelTests(TestCase):
    """Tests for the Product model."""

    def setUp(self):
        """Set up test data."""
        self.category = Category.objects.create(
            name='Test Category',
            name_es='Categoría de Prueba',
            name_en='Test Category',
            slug='test-category'
        )
        self.product = Product.objects.create(
            name='Test Product',
            name_es='Producto de Prueba',
            name_en='Test Product',
            slug='test-product',
            category=self.category,
            price=Decimal('100.00'),
            sku='TEST-001',
            stock_quantity=50
        )

    def test_get_max_order_quantity_uses_product_value(self):
        """Test that get_max_order_quantity returns product-specific value when set."""
        self.product.max_order_quantity = 5
        self.product.save()
        self.assertEqual(self.product.get_max_order_quantity(), 5)

    @override_settings(STORE_DEFAULT_MAX_ORDER_QUANTITY=25)
    def test_get_max_order_quantity_uses_settings_default(self):
        """Test that get_max_order_quantity falls back to settings when not set."""
        self.product.max_order_quantity = None
        self.product.save()
        self.assertEqual(self.product.get_max_order_quantity(), 25)

    def test_get_max_order_quantity_default_fallback(self):
        """Test that get_max_order_quantity falls back to 99 if no setting."""
        self.product.max_order_quantity = None
        self.product.save()
        # Default in settings is 99
        self.assertEqual(self.product.get_max_order_quantity(), 99)

    def test_is_in_stock(self):
        """Test is_in_stock property."""
        self.product.stock_quantity = 10
        self.assertTrue(self.product.is_in_stock)

        self.product.stock_quantity = 0
        self.assertFalse(self.product.is_in_stock)

    def test_is_low_stock(self):
        """Test is_low_stock property."""
        self.product.low_stock_threshold = 5

        self.product.stock_quantity = 3
        self.assertTrue(self.product.is_low_stock)

        self.product.stock_quantity = 10
        self.assertFalse(self.product.is_low_stock)

        self.product.stock_quantity = 0
        self.assertFalse(self.product.is_low_stock)

    def test_is_on_sale(self):
        """Test is_on_sale property."""
        self.product.compare_at_price = Decimal('150.00')
        self.assertTrue(self.product.is_on_sale)

        self.product.compare_at_price = None
        self.assertFalse(self.product.is_on_sale)

    def test_discount_percentage(self):
        """Test discount_percentage property."""
        self.product.price = Decimal('75.00')
        self.product.compare_at_price = Decimal('100.00')
        self.assertEqual(self.product.discount_percentage, 25)


class CartModelTests(TestCase):
    """Tests for the Cart model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            name_es='Categoría',
            name_en='Category',
            slug='test-cat'
        )
        self.product1 = Product.objects.create(
            name='Product 1',
            name_es='Producto 1',
            name_en='Product 1',
            slug='product-1',
            category=self.category,
            price=Decimal('50.00'),
            sku='PROD-001'
        )
        self.product2 = Product.objects.create(
            name='Product 2',
            name_es='Producto 2',
            name_en='Product 2',
            slug='product-2',
            category=self.category,
            price=Decimal('75.00'),
            sku='PROD-002'
        )
        self.cart = Cart.objects.create(user=self.user)

    def test_add_item_creates_cart_item(self):
        """Test adding an item to the cart."""
        self.cart.add_item(self.product1, 2)
        self.assertEqual(self.cart.items.count(), 1)
        self.assertEqual(self.cart.items.first().quantity, 2)

    def test_add_item_increases_existing_quantity(self):
        """Test adding more of an existing item."""
        self.cart.add_item(self.product1, 2)
        self.cart.add_item(self.product1, 3)
        self.assertEqual(self.cart.items.count(), 1)
        self.assertEqual(self.cart.items.first().quantity, 5)

    def test_remove_item(self):
        """Test removing an item from the cart."""
        self.cart.add_item(self.product1, 2)
        self.cart.remove_item(self.product1)
        self.assertEqual(self.cart.items.count(), 0)

    def test_update_item_quantity(self):
        """Test updating item quantity."""
        self.cart.add_item(self.product1, 2)
        self.cart.update_item_quantity(self.product1, 5)
        self.assertEqual(self.cart.items.first().quantity, 5)

    def test_update_item_quantity_zero_removes_item(self):
        """Test that setting quantity to 0 removes the item."""
        self.cart.add_item(self.product1, 2)
        self.cart.update_item_quantity(self.product1, 0)
        self.assertEqual(self.cart.items.count(), 0)

    def test_cart_total(self):
        """Test cart total calculation."""
        self.cart.add_item(self.product1, 2)  # 2 x 50 = 100
        self.cart.add_item(self.product2, 1)  # 1 x 75 = 75
        self.assertEqual(self.cart.total, Decimal('175.00'))

    def test_cart_item_count(self):
        """Test cart item count."""
        self.cart.add_item(self.product1, 2)
        self.cart.add_item(self.product2, 3)
        self.assertEqual(self.cart.item_count, 5)

    def test_clear_cart(self):
        """Test clearing the cart."""
        self.cart.add_item(self.product1, 2)
        self.cart.add_item(self.product2, 1)
        self.cart.clear()
        self.assertEqual(self.cart.items.count(), 0)


class CartContextProcessorTests(TestCase):
    """Tests for the cart context processor."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            name_es='Categoría',
            name_en='Category',
            slug='test-cat'
        )
        self.product = Product.objects.create(
            name='Test Product',
            name_es='Producto',
            name_en='Product',
            slug='test-product',
            category=self.category,
            price=Decimal('100.00'),
            sku='TEST-001'
        )

    def test_cart_count_in_context_anonymous(self):
        """Test cart_count is available for anonymous users."""
        response = self.client.get(reverse('store:product_list'))
        self.assertIn('cart_count', response.context)
        self.assertEqual(response.context['cart_count'], 0)

    def test_cart_count_in_context_authenticated(self):
        """Test cart_count is available for authenticated users."""
        self.client.login(username='testuser', password='testpass123')

        # Create a cart with items
        cart = Cart.objects.create(user=self.user)
        cart.add_item(self.product, 3)

        response = self.client.get(reverse('store:product_list'))
        self.assertIn('cart_count', response.context)
        self.assertEqual(response.context['cart_count'], 3)


class AddToCartViewTests(TestCase):
    """Tests for the add_to_cart view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.category = Category.objects.create(
            name='Test Category',
            name_es='Categoría',
            name_en='Category',
            slug='test-cat'
        )
        self.product = Product.objects.create(
            name='Test Product',
            name_es='Producto',
            name_en='Product',
            slug='test-product',
            category=self.category,
            price=Decimal('100.00'),
            sku='TEST-001',
            stock_quantity=50,
            max_order_quantity=10
        )

    def test_add_to_cart_creates_item(self):
        """Test adding a product to cart."""
        response = self.client.post(
            reverse('store:add_to_cart', args=[self.product.pk]),
            {'quantity': 2}
        )
        self.assertEqual(response.status_code, 302)

        # Check cart was created
        cart = Cart.objects.first()
        self.assertIsNotNone(cart)
        self.assertEqual(cart.items.first().quantity, 2)

    def test_add_to_cart_respects_max_quantity(self):
        """Test that add_to_cart respects max_order_quantity."""
        # Try to add more than max
        response = self.client.post(
            reverse('store:add_to_cart', args=[self.product.pk]),
            {'quantity': 15}
        )
        self.assertEqual(response.status_code, 302)

        # Cart may be created but should have no items
        cart = Cart.objects.first()
        if cart:
            self.assertEqual(cart.items.count(), 0)

    def test_add_to_cart_respects_max_with_existing_items(self):
        """Test max quantity validation considers existing cart items."""
        # First add some items
        self.client.post(
            reverse('store:add_to_cart', args=[self.product.pk]),
            {'quantity': 8}
        )

        # Try to add more that would exceed max
        response = self.client.post(
            reverse('store:add_to_cart', args=[self.product.pk]),
            {'quantity': 5}
        )

        # Cart should still have only 8
        cart = Cart.objects.first()
        self.assertEqual(cart.items.first().quantity, 8)

    def test_add_to_cart_respects_stock_quantity(self):
        """Test that add_to_cart respects available stock."""
        self.product.stock_quantity = 3
        self.product.save()

        response = self.client.post(
            reverse('store:add_to_cart', args=[self.product.pk]),
            {'quantity': 5}
        )

        # Cart may be created but should have no items due to insufficient stock
        cart = Cart.objects.first()
        if cart:
            self.assertEqual(cart.items.count(), 0)


class UpdateCartViewTests(TestCase):
    """Tests for the update_cart view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.category = Category.objects.create(
            name='Test Category',
            name_es='Categoría',
            name_en='Category',
            slug='test-cat'
        )
        self.product = Product.objects.create(
            name='Test Product',
            name_es='Producto',
            name_en='Product',
            slug='test-product',
            category=self.category,
            price=Decimal('100.00'),
            sku='TEST-001',
            stock_quantity=50,
            max_order_quantity=10
        )
        # Add item to cart first
        self.client.post(
            reverse('store:add_to_cart', args=[self.product.pk]),
            {'quantity': 2}
        )

    def test_update_cart_changes_quantity(self):
        """Test updating cart item quantity."""
        response = self.client.post(
            reverse('store:update_cart'),
            {'product_id': self.product.pk, 'quantity': 5}
        )
        self.assertEqual(response.status_code, 302)

        cart = Cart.objects.first()
        self.assertEqual(cart.items.first().quantity, 5)

    def test_update_cart_caps_at_max_quantity(self):
        """Test that update_cart caps quantity at max."""
        response = self.client.post(
            reverse('store:update_cart'),
            {'product_id': self.product.pk, 'quantity': 20}
        )

        cart = Cart.objects.first()
        # Should be capped at max_order_quantity (10)
        self.assertEqual(cart.items.first().quantity, 10)

    def test_update_cart_enforces_minimum_one(self):
        """Test that quantity cannot go below 1."""
        response = self.client.post(
            reverse('store:update_cart'),
            {'product_id': self.product.pk, 'quantity': 0}
        )

        cart = Cart.objects.first()
        self.assertEqual(cart.items.first().quantity, 1)

    def test_update_cart_caps_at_stock_quantity(self):
        """Test that update_cart caps at available stock."""
        self.product.stock_quantity = 5
        self.product.max_order_quantity = 20  # Higher than stock
        self.product.save()

        response = self.client.post(
            reverse('store:update_cart'),
            {'product_id': self.product.pk, 'quantity': 15}
        )

        cart = Cart.objects.first()
        # Should be capped at stock_quantity (5)
        self.assertEqual(cart.items.first().quantity, 5)


class RemoveFromCartViewTests(TestCase):
    """Tests for the remove_from_cart view."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        self.category = Category.objects.create(
            name='Test Category',
            name_es='Categoría',
            name_en='Category',
            slug='test-cat'
        )
        self.product = Product.objects.create(
            name='Test Product',
            name_es='Producto',
            name_en='Product',
            slug='test-product',
            category=self.category,
            price=Decimal('100.00'),
            sku='TEST-001'
        )
        # Create cart with item directly
        self.cart = Cart.objects.create(user=self.user)
        self.cart.add_item(self.product, 2)

    def test_remove_from_cart(self):
        """Test removing an item from cart."""
        self.assertEqual(self.cart.items.count(), 1)

        response = self.client.post(
            reverse('store:remove_from_cart', args=[self.product.pk])
        )
        self.assertEqual(response.status_code, 302)

        self.cart.refresh_from_db()
        self.assertEqual(self.cart.items.count(), 0)


class CartItemModelTests(TestCase):
    """Tests for the CartItem model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            name_es='Categoría',
            name_en='Category',
            slug='test-cat'
        )
        self.product = Product.objects.create(
            name='Test Product',
            name_es='Producto',
            name_en='Product',
            slug='test-product',
            category=self.category,
            price=Decimal('45.50'),
            sku='TEST-001'
        )
        self.cart = Cart.objects.create(user=self.user)

    def test_cart_item_subtotal(self):
        """Test cart item subtotal calculation."""
        item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=3
        )
        self.assertEqual(item.subtotal, Decimal('136.50'))


class OrderCreationTests(TestCase):
    """Tests for Order creation and totals."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            name_es='Categoría',
            name_en='Category',
            slug='test-cat'
        )
        self.product = Product.objects.create(
            name='Test Product',
            name_es='Producto',
            name_en='Product',
            slug='test-product',
            category=self.category,
            price=Decimal('100.00'),
            sku='TEST-001'
        )
        self.cart = Cart.objects.create(user=self.user)
        self.cart.add_item(self.product, 2)  # 2 x $100 = $200

    def test_order_pickup_no_shipping_cost(self):
        """Test that pickup orders have no shipping cost."""
        order = Order.create_from_cart(
            cart=self.cart,
            user=self.user,
            fulfillment_method='pickup',
            payment_method='cash'
        )
        self.assertEqual(order.subtotal, Decimal('200.00'))
        self.assertEqual(order.shipping_cost, Decimal('0'))
        self.assertEqual(order.tax, Decimal('32.00'))  # 16% of 200
        self.assertEqual(order.total, Decimal('232.00'))  # 200 + 32

    def test_order_delivery_includes_shipping_cost(self):
        """Test that delivery orders include $50 shipping cost."""
        order = Order.create_from_cart(
            cart=self.cart,
            user=self.user,
            fulfillment_method='delivery',
            payment_method='cash',
            shipping_name='Test User',
            shipping_address='123 Test St',
            shipping_phone='555-1234'
        )
        self.assertEqual(order.subtotal, Decimal('200.00'))
        self.assertEqual(order.shipping_cost, Decimal('50.00'))
        self.assertEqual(order.tax, Decimal('32.00'))  # 16% of 200
        self.assertEqual(order.total, Decimal('282.00'))  # 200 + 32 + 50

    def test_order_stores_shipping_info(self):
        """Test that delivery orders store shipping information."""
        order = Order.create_from_cart(
            cart=self.cart,
            user=self.user,
            fulfillment_method='delivery',
            payment_method='cash',
            shipping_name='John Doe',
            shipping_address='456 Main St, Puerto Morelos',
            shipping_phone='+52 998 123 4567'
        )
        self.assertEqual(order.shipping_name, 'John Doe')
        self.assertEqual(order.shipping_address, '456 Main St, Puerto Morelos')
        self.assertEqual(order.shipping_phone, '+52 998 123 4567')


class StoreSettingsTests(TestCase):
    """Tests for StoreSettings singleton model."""

    def setUp(self):
        """Clear any existing settings for each test."""
        StoreSettings.objects.all().delete()

    def test_get_instance_creates_singleton(self):
        """get_instance should create settings if not exists."""
        settings = StoreSettings.get_instance()
        self.assertEqual(settings.pk, 1)
        self.assertEqual(StoreSettings.objects.count(), 1)

    def test_get_instance_returns_existing(self):
        """get_instance should return existing settings."""
        StoreSettings.objects.create(pk=1, default_shipping_cost=Decimal('100.00'))
        settings = StoreSettings.get_instance()
        self.assertEqual(settings.default_shipping_cost, Decimal('100.00'))
        self.assertEqual(StoreSettings.objects.count(), 1)

    def test_save_enforces_singleton(self):
        """Multiple saves should not create multiple records."""
        settings1 = StoreSettings.get_instance()
        settings1.default_shipping_cost = Decimal('75.00')
        settings1.save()

        settings2 = StoreSettings(default_shipping_cost=Decimal('80.00'))
        settings2.save()

        self.assertEqual(StoreSettings.objects.count(), 1)
        settings = StoreSettings.get_instance()
        self.assertEqual(settings.default_shipping_cost, Decimal('80.00'))

    def test_default_values(self):
        """Default values should be set correctly."""
        settings = StoreSettings.get_instance()
        self.assertEqual(settings.default_shipping_cost, Decimal('50.00'))
        self.assertEqual(settings.tax_rate, Decimal('0.16'))
        self.assertEqual(settings.default_max_order_quantity, 99)
        self.assertIsNone(settings.free_shipping_threshold)

    def test_free_shipping_applies_when_threshold_met(self):
        """Orders above threshold should get free shipping."""
        settings = StoreSettings.get_instance()
        settings.free_shipping_threshold = Decimal('500.00')
        settings.save()

        self.assertEqual(settings.get_shipping_cost(Decimal('400.00')), Decimal('50.00'))
        self.assertEqual(settings.get_shipping_cost(Decimal('500.00')), Decimal('0'))
        self.assertEqual(settings.get_shipping_cost(Decimal('600.00')), Decimal('0'))

    def test_free_shipping_disabled_when_threshold_null(self):
        """When threshold is null, always charge shipping."""
        settings = StoreSettings.get_instance()
        settings.free_shipping_threshold = None
        settings.save()

        self.assertEqual(settings.get_shipping_cost(Decimal('1000.00')), Decimal('50.00'))

    def test_str_representation(self):
        """String representation should be 'Store Settings'."""
        settings = StoreSettings.get_instance()
        self.assertEqual(str(settings), 'Store Settings')
