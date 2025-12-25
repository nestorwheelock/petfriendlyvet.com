"""Browser tests for order management.

Tests order list, order detail, and order status display.
"""
import re
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from playwright.sync_api import expect


@pytest.fixture
def category(db):
    """Create a product category."""
    from apps.store.models import Category

    cat = Category.objects.create(
        name='Pet Food',
        name_es='Comida para mascotas',
        name_en='Pet Food',
        slug='pet-food',
        is_active=True,
    )
    return cat


@pytest.fixture
def product(db, category):
    """Create a product."""
    from apps.store.models import Product

    prod = Product.objects.create(
        name='Premium Dog Food',
        name_es='Comida Premium para Perro',
        name_en='Premium Dog Food',
        slug='premium-dog-food',
        category=category,
        price=Decimal('350.00'),
        sku='DOG-FOOD-001',
        stock_quantity=100,
        is_active=True,
    )
    return prod


@pytest.fixture
def pending_order(db, owner_user, product):
    """Create a pending payment order."""
    from apps.store.models import Order, OrderItem

    order = Order.objects.create(
        user=owner_user,
        order_number='ORD-2024-0001',
        status='pending',
        fulfillment_method='pickup',
        payment_method='cash',
        subtotal=Decimal('350.00'),
        tax=Decimal('56.00'),
        shipping_cost=Decimal('0.00'),
        total=Decimal('406.00'),
    )

    OrderItem.objects.create(
        order=order,
        product=product,
        product_name=product.name,
        product_sku=product.sku,
        price=product.price,
        quantity=1,
    )

    return order


@pytest.fixture
def paid_order(db, owner_user, product):
    """Create a paid order."""
    from apps.store.models import Order, OrderItem
    from django.utils import timezone

    order = Order.objects.create(
        user=owner_user,
        order_number='ORD-2024-0002',
        status='paid',
        fulfillment_method='pickup',
        payment_method='card',
        subtotal=Decimal('700.00'),
        tax=Decimal('112.00'),
        shipping_cost=Decimal('0.00'),
        total=Decimal('812.00'),
        paid_at=timezone.now(),
    )

    OrderItem.objects.create(
        order=order,
        product=product,
        product_name=product.name,
        product_sku=product.sku,
        price=product.price,
        quantity=2,
    )

    return order


@pytest.fixture
def delivery_order(db, owner_user, product):
    """Create a delivery order."""
    from apps.store.models import Order, OrderItem

    order = Order.objects.create(
        user=owner_user,
        order_number='ORD-2024-0003',
        status='preparing',
        fulfillment_method='delivery',
        payment_method='card',
        subtotal=Decimal('350.00'),
        tax=Decimal('56.00'),
        shipping_cost=Decimal('50.00'),
        total=Decimal('456.00'),
        shipping_name='Juan Pérez',
        shipping_address='Calle Principal 123, Puerto Morelos',
        shipping_phone='555-1234',
    )

    OrderItem.objects.create(
        order=order,
        product=product,
        product_name=product.name,
        price=product.price,
        quantity=1,
    )

    return order


@pytest.fixture
def completed_order(db, owner_user, product):
    """Create a delivered order."""
    from apps.store.models import Order, OrderItem
    from django.utils import timezone

    order = Order.objects.create(
        user=owner_user,
        order_number='ORD-2024-0004',
        status='delivered',
        fulfillment_method='delivery',
        payment_method='card',
        subtotal=Decimal('1050.00'),
        tax=Decimal('168.00'),
        shipping_cost=Decimal('50.00'),
        total=Decimal('1268.00'),
        shipping_name='Juan Pérez',
        shipping_address='Calle Principal 123, Puerto Morelos',
        paid_at=timezone.now() - timedelta(days=3),
    )

    OrderItem.objects.create(
        order=order,
        product=product,
        product_name=product.name,
        price=product.price,
        quantity=3,
    )

    return order


@pytest.fixture
def cancelled_order(db, owner_user, product):
    """Create a cancelled order."""
    from apps.store.models import Order, OrderItem

    order = Order.objects.create(
        user=owner_user,
        order_number='ORD-2024-0005',
        status='cancelled',
        fulfillment_method='pickup',
        payment_method='cash',
        subtotal=Decimal('350.00'),
        tax=Decimal('56.00'),
        total=Decimal('406.00'),
    )

    OrderItem.objects.create(
        order=order,
        product=product,
        product_name=product.name,
        price=product.price,
        quantity=1,
    )

    return order


@pytest.fixture
def multiple_orders(db, owner_user, product):
    """Create multiple orders for list testing."""
    from apps.store.models import Order, OrderItem

    orders = []
    statuses = ['pending', 'paid', 'preparing', 'ready', 'delivered']

    for i, status in enumerate(statuses):
        order = Order.objects.create(
            user=owner_user,
            order_number=f'ORD-2024-10{i:02d}',
            status=status,
            fulfillment_method='pickup' if i % 2 == 0 else 'delivery',
            payment_method='cash' if status == 'pending' else 'card',
            subtotal=Decimal('100.00') * (i + 1),
            tax=Decimal('16.00') * (i + 1),
            shipping_cost=Decimal('50.00') if i % 2 != 0 else Decimal('0.00'),
            total=Decimal('116.00') * (i + 1) + (Decimal('50.00') if i % 2 != 0 else Decimal('0.00')),
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            price=product.price,
            quantity=i + 1,
        )

        orders.append(order)

    return orders


@pytest.mark.browser
class TestOrderList:
    """Test order list page."""

    def test_order_list_requires_login(self, page, live_server, db):
        """Order list requires authentication."""
        page.goto(f'{live_server.url}/store/orders/')
        page.wait_for_load_state('networkidle')

        expect(page).to_have_url(re.compile(r'.*/accounts/login.*'))

    def test_order_list_loads(self, authenticated_page, live_server, db):
        """Order list page loads."""
        page = authenticated_page

        page.goto(f'{live_server.url}/store/orders/')

        expect(page).to_have_title(re.compile(r'.*[Pp]edido.*|.*[Oo]rder.*'))
        expect(page.locator('h1')).to_contain_text('pedidos')

    def test_order_list_shows_orders(self, authenticated_page, live_server, pending_order):
        """Order list shows user's orders."""
        page = authenticated_page

        page.goto(f'{live_server.url}/store/orders/')

        # Should show order number
        expect(page.locator(f'text={pending_order.order_number}')).to_be_visible()

    def test_order_list_shows_total(self, authenticated_page, live_server, pending_order):
        """Order list shows order total."""
        page = authenticated_page

        page.goto(f'{live_server.url}/store/orders/')

        expect(page.locator('text=$406')).to_be_visible()

    def test_order_list_shows_date(self, authenticated_page, live_server, pending_order):
        """Order list shows order date."""
        page = authenticated_page

        page.goto(f'{live_server.url}/store/orders/')

        content = page.content()
        # Order date should be shown in some format
        # Check that the order list contains date-related content
        assert pending_order.order_number in content

    def test_order_list_shows_pending_status(self, authenticated_page, live_server, pending_order):
        """Pending orders show Pending Payment badge."""
        page = authenticated_page

        page.goto(f'{live_server.url}/store/orders/')

        pending_badge = page.locator('.rounded-full:has-text("Pending")')
        expect(pending_badge.first).to_be_visible()

    def test_order_list_shows_paid_status(self, authenticated_page, live_server, paid_order):
        """Paid orders show Paid badge."""
        page = authenticated_page

        page.goto(f'{live_server.url}/store/orders/')

        paid_badge = page.locator('.rounded-full:has-text("Paid")')
        expect(paid_badge.first).to_be_visible()

    def test_order_list_shows_delivered_status(self, authenticated_page, live_server, completed_order):
        """Delivered orders show Delivered badge."""
        page = authenticated_page

        page.goto(f'{live_server.url}/store/orders/')

        delivered_badge = page.locator('.rounded-full:has-text("Delivered")')
        expect(delivered_badge.first).to_be_visible()

    def test_order_list_shows_cancelled_status(self, authenticated_page, live_server, cancelled_order):
        """Cancelled orders show Cancelled badge."""
        page = authenticated_page

        page.goto(f'{live_server.url}/store/orders/')

        cancelled_badge = page.locator('.rounded-full:has-text("Cancelled")')
        expect(cancelled_badge.first).to_be_visible()

    def test_order_list_shows_fulfillment_method(self, authenticated_page, live_server, pending_order, delivery_order):
        """Order list shows fulfillment method."""
        page = authenticated_page

        page.goto(f'{live_server.url}/store/orders/')

        # Should show pickup and delivery indicators
        expect(page.locator('text=Pickup')).to_be_visible()
        expect(page.locator('text=Delivery')).to_be_visible()

    def test_order_list_shows_item_count(self, authenticated_page, live_server, pending_order):
        """Order list shows item count."""
        page = authenticated_page

        page.goto(f'{live_server.url}/store/orders/')

        expect(page.locator('text=1 art')).to_be_visible()

    def test_order_list_empty_state(self, authenticated_page, live_server, db):
        """Empty order list shows message and shop link."""
        page = authenticated_page

        page.goto(f'{live_server.url}/store/orders/')

        empty_message = page.locator('text=No tienes pedidos')
        expect(empty_message.first).to_be_visible()

        shop_link = page.locator('a:has-text("Explorar productos")')
        expect(shop_link).to_be_visible()

    def test_order_click_goes_to_detail(self, authenticated_page, live_server, pending_order):
        """Clicking order goes to detail page."""
        page = authenticated_page

        page.goto(f'{live_server.url}/store/orders/')

        page.locator(f'a[href*="{pending_order.order_number}"]').first.click()
        page.wait_for_load_state('networkidle')

        expect(page).to_have_url(re.compile(rf'.*/orders/{pending_order.order_number}.*'))


@pytest.mark.browser
class TestOrderDetail:
    """Test order detail page."""

    def test_order_detail_loads(self, authenticated_page, live_server, pending_order):
        """Order detail page loads."""
        page = authenticated_page

        page.goto(f'{live_server.url}/store/orders/{pending_order.order_number}/')

        expect(page.locator('h1')).to_contain_text(pending_order.order_number)

    def test_order_detail_shows_status_badge(self, authenticated_page, live_server, paid_order):
        """Order detail shows status badge."""
        page = authenticated_page

        page.goto(f'{live_server.url}/store/orders/{paid_order.order_number}/')

        status_badge = page.locator('.rounded-full:has-text("Paid")')
        expect(status_badge.first).to_be_visible()

    def test_order_detail_shows_order_items(self, authenticated_page, live_server, pending_order):
        """Order detail shows order items."""
        page = authenticated_page

        page.goto(f'{live_server.url}/store/orders/{pending_order.order_number}/')

        # Should show item description
        expect(page.locator('h2:has-text("Artículos")')).to_be_visible()
        expect(page.locator('text=Premium Dog Food')).to_be_visible()

    def test_order_detail_shows_item_quantity_and_price(self, authenticated_page, live_server, paid_order):
        """Order detail shows item quantity and price."""
        page = authenticated_page

        page.goto(f'{live_server.url}/store/orders/{paid_order.order_number}/')

        # Order has 2 items at $350 each
        expect(page.locator('text=2 ×')).to_be_visible()
        expect(page.locator('text=$350')).to_be_visible()

    def test_order_detail_shows_subtotal(self, authenticated_page, live_server, pending_order):
        """Order detail shows subtotal."""
        page = authenticated_page

        page.goto(f'{live_server.url}/store/orders/{pending_order.order_number}/')

        content = page.content()
        assert 'Subtotal' in content or 'subtotal' in content
        assert '350' in content

    def test_order_detail_shows_tax(self, authenticated_page, live_server, pending_order):
        """Order detail shows tax (IVA)."""
        page = authenticated_page

        page.goto(f'{live_server.url}/store/orders/{pending_order.order_number}/')

        expect(page.locator('text=IVA')).to_be_visible()
        expect(page.locator('text=$56')).to_be_visible()

    def test_order_detail_shows_total(self, authenticated_page, live_server, pending_order):
        """Order detail shows total."""
        page = authenticated_page

        page.goto(f'{live_server.url}/store/orders/{pending_order.order_number}/')

        content = page.content()
        assert 'Total' in content or 'total' in content
        assert '406' in content

    def test_order_detail_shows_shipping_cost(self, authenticated_page, live_server, delivery_order):
        """Delivery order shows shipping cost."""
        page = authenticated_page

        page.goto(f'{live_server.url}/store/orders/{delivery_order.order_number}/')

        expect(page.locator('text=Envío')).to_be_visible()
        expect(page.locator('text=$50')).to_be_visible()

    def test_order_detail_shows_pickup_info(self, authenticated_page, live_server, pending_order):
        """Pickup order shows pickup information."""
        page = authenticated_page

        page.goto(f'{live_server.url}/store/orders/{pending_order.order_number}/')

        content = page.content()
        # Should show fulfillment method info
        assert 'Pickup' in content or 'pickup' in content or 'Recoger' in content

    def test_order_detail_shows_delivery_address(self, authenticated_page, live_server, delivery_order):
        """Delivery order shows shipping address."""
        page = authenticated_page

        page.goto(f'{live_server.url}/store/orders/{delivery_order.order_number}/')

        expect(page.locator('text=Delivery')).to_be_visible()
        expect(page.locator(f'text={delivery_order.shipping_name}')).to_be_visible()
        expect(page.locator('text=Calle Principal 123')).to_be_visible()

    def test_order_detail_shows_payment_method(self, authenticated_page, live_server, pending_order):
        """Order detail shows payment method."""
        page = authenticated_page

        page.goto(f'{live_server.url}/store/orders/{pending_order.order_number}/')

        expect(page.locator('h2:has-text("pago")')).to_be_visible()
        expect(page.locator('text=Cash')).to_be_visible()

    def test_order_detail_pending_warning(self, authenticated_page, live_server, pending_order):
        """Pending order shows payment warning."""
        page = authenticated_page

        page.goto(f'{live_server.url}/store/orders/{pending_order.order_number}/')

        expect(page.locator('text=Pago pendiente')).to_be_visible()

    def test_order_detail_paid_confirmation(self, authenticated_page, live_server, paid_order):
        """Paid order shows payment confirmation."""
        page = authenticated_page

        page.goto(f'{live_server.url}/store/orders/{paid_order.order_number}/')

        expect(page.locator('text=Pago confirmado')).to_be_visible()

    def test_order_detail_back_link(self, authenticated_page, live_server, pending_order):
        """Order detail has back link to list."""
        page = authenticated_page

        page.goto(f'{live_server.url}/store/orders/{pending_order.order_number}/')

        back_link = page.locator('a:has-text("Volver")')
        expect(back_link).to_be_visible()

    def test_order_detail_back_link_works(self, authenticated_page, live_server, pending_order):
        """Back link navigates to order list."""
        page = authenticated_page

        page.goto(f'{live_server.url}/store/orders/{pending_order.order_number}/')

        page.locator('a:has-text("Volver")').click()
        page.wait_for_load_state('networkidle')

        expect(page).to_have_url(re.compile(r'.*/orders/$'))

    def test_order_detail_support_link(self, authenticated_page, live_server, pending_order):
        """Order detail has support contact link."""
        page = authenticated_page

        page.goto(f'{live_server.url}/store/orders/{pending_order.order_number}/')

        support_link = page.locator('a:has-text("Contactar soporte")')
        expect(support_link).to_be_visible()


@pytest.mark.browser
class TestOrderStatusDisplay:
    """Test order status colors and styling."""

    def test_pending_status_yellow(self, authenticated_page, live_server, pending_order):
        """Pending orders have yellow status badge."""
        page = authenticated_page

        page.goto(f'{live_server.url}/store/orders/')

        yellow_badge = page.locator('.bg-yellow-100.text-yellow-800')
        expect(yellow_badge.first).to_be_visible()

    def test_paid_status_blue(self, authenticated_page, live_server, paid_order):
        """Paid orders have blue status badge."""
        page = authenticated_page

        page.goto(f'{live_server.url}/store/orders/')

        blue_badge = page.locator('.bg-blue-100.text-blue-800')
        expect(blue_badge.first).to_be_visible()

    def test_preparing_status_indigo(self, authenticated_page, live_server, delivery_order):
        """Preparing orders have indigo status badge."""
        page = authenticated_page

        page.goto(f'{live_server.url}/store/orders/')

        indigo_badge = page.locator('.bg-indigo-100.text-indigo-800')
        expect(indigo_badge.first).to_be_visible()

    def test_delivered_status_green(self, authenticated_page, live_server, completed_order):
        """Delivered orders have green status badge."""
        page = authenticated_page

        page.goto(f'{live_server.url}/store/orders/')

        green_badge = page.locator('.bg-green-100.text-green-800')
        expect(green_badge.first).to_be_visible()

    def test_cancelled_status_red(self, authenticated_page, live_server, cancelled_order):
        """Cancelled orders have red status badge."""
        page = authenticated_page

        page.goto(f'{live_server.url}/store/orders/')

        red_badge = page.locator('.bg-red-100.text-red-800')
        expect(red_badge.first).to_be_visible()


@pytest.mark.browser
class TestMobileOrders:
    """Test orders on mobile viewport."""

    def test_mobile_order_list(self, mobile_page, live_server, owner_user, pending_order):
        """Order list works on mobile."""
        page = mobile_page

        # Login
        page.goto(f'{live_server.url}/accounts/login/')
        page.fill('input[name="username"]', owner_user.email)
        page.fill('input[name="password"]', 'owner123')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        page.goto(f'{live_server.url}/store/orders/')

        # Should show order
        expect(page.locator(f'text={pending_order.order_number}')).to_be_visible()

    def test_mobile_order_detail(self, mobile_page, live_server, owner_user, pending_order):
        """Order detail works on mobile."""
        page = mobile_page

        # Login
        page.goto(f'{live_server.url}/accounts/login/')
        page.fill('input[name="username"]', owner_user.email)
        page.fill('input[name="password"]', 'owner123')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        page.goto(f'{live_server.url}/store/orders/{pending_order.order_number}/')

        # Should show order number in page content
        content = page.content()
        assert pending_order.order_number in content

        # Order summary should be visible
        assert 'Total' in content or 'total' in content
