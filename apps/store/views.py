"""Store views for e-commerce functionality."""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404
from django.db.models import Q, F

from .models import Category, Product, Cart, CartItem, Order
from apps.delivery.models import Delivery, DeliverySlot


def get_or_create_cart(request):
    """Get or create a cart for the current user/session."""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        # Merge session cart if exists
        if not created:
            session_key = request.session.session_key
            if session_key:
                session_cart = Cart.objects.filter(
                    session_key=session_key, user__isnull=True
                ).first()
                if session_cart:
                    cart.merge_with(session_cart)
        return cart
    else:
        if not request.session.session_key:
            request.session.create()
        cart, created = Cart.objects.get_or_create(
            session_key=request.session.session_key,
            user__isnull=True
        )
        return cart


class ProductListView(ListView):
    """List all active products."""

    model = Product
    template_name = 'store/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)

        # Category filter
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        # Search filter
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(name_es__icontains=search) |
                Q(description__icontains=search)
            )

        # Species filter
        species = self.request.GET.get('species')
        if species:
            # Manual filtering for SQLite compatibility
            pks = [
                p.pk for p in queryset
                if species in p.suitable_for_species
            ]
            queryset = queryset.filter(pk__in=pks)

        # Price range filter
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        # Sorting
        sort = self.request.GET.get('sort', '-created_at')
        if sort in ['price', '-price', 'name', '-name', '-created_at']:
            queryset = queryset.order_by(sort)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(
            is_active=True, parent__isnull=True
        )
        context['cart'] = get_or_create_cart(self.request)
        return context


class ProductDetailView(DetailView):
    """Show product details."""

    model = Product
    template_name = 'store/product_detail.html'
    context_object_name = 'product'

    def get_queryset(self):
        return Product.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart'] = get_or_create_cart(self.request)

        # Related products (same category)
        context['related_products'] = Product.objects.filter(
            category=self.object.category,
            is_active=True
        ).exclude(pk=self.object.pk)[:4]

        return context


class CategoryDetailView(ListView):
    """Show products in a category."""

    model = Product
    template_name = 'store/category_detail.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        self.category = get_object_or_404(
            Category, slug=self.kwargs['slug'], is_active=True
        )
        return Product.objects.filter(
            category=self.category, is_active=True
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['cart'] = get_or_create_cart(self.request)
        return context


class CartView(TemplateView):
    """Show shopping cart."""

    template_name = 'store/cart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart'] = get_or_create_cart(self.request)
        return context


def add_to_cart(request, product_id):
    """Add a product to the cart."""
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    cart = get_or_create_cart(request)

    quantity = int(request.POST.get('quantity', 1))

    # Check max order quantity
    max_qty = product.get_max_order_quantity()
    current_in_cart = 0
    existing_item = cart.items.filter(product=product).first()
    if existing_item:
        current_in_cart = existing_item.quantity

    if current_in_cart + quantity > max_qty:
        messages.error(
            request,
            f'Maximum {max_qty} per order. You already have {current_in_cart} in your cart.'
        )
        return redirect('store:product_detail', slug=product.slug)

    # Check stock
    if product.track_inventory and product.stock_quantity < quantity:
        messages.error(
            request,
            f'Sorry, only {product.stock_quantity} available.'
        )
        return redirect('store:product_detail', slug=product.slug)

    cart.add_item(product, quantity)
    messages.success(request, f'{product.name} added to cart.')

    # Return to referring page or cart
    next_url = request.POST.get('next', request.META.get('HTTP_REFERER'))
    if next_url:
        return redirect(next_url)
    return redirect('store:cart')


def update_cart(request):
    """Update cart item quantity."""
    if request.method == 'POST':
        cart = get_or_create_cart(request)
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))

        product = get_object_or_404(Product, pk=product_id)

        # Ensure quantity is at least 1
        if quantity < 1:
            quantity = 1

        # Check max order quantity
        max_qty = product.get_max_order_quantity()
        if quantity > max_qty:
            messages.error(
                request,
                f'Maximum {max_qty} per order.'
            )
            quantity = max_qty

        # Check stock
        if product.track_inventory and product.stock_quantity < quantity:
            messages.error(
                request,
                f'Sorry, only {product.stock_quantity} available.'
            )
            quantity = product.stock_quantity

        cart.update_item_quantity(product, quantity)

    return redirect('store:cart')


def remove_from_cart(request, product_id):
    """Remove a product from the cart."""
    if request.method == 'POST':
        cart = get_or_create_cart(request)
        product = get_object_or_404(Product, pk=product_id)
        cart.remove_item(product)
        messages.success(request, f'{product.name} removed from cart.')

    return redirect('store:cart')


class CheckoutView(LoginRequiredMixin, TemplateView):
    """Checkout page."""

    template_name = 'store/checkout.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart'] = get_or_create_cart(self.request)
        return context


@login_required
def process_checkout(request):
    """Process checkout and create order."""
    if request.method != 'POST':
        return redirect('store:checkout')

    cart = get_or_create_cart(request)

    if cart.item_count == 0:
        messages.error(request, 'Your cart is empty.')
        return redirect('store:cart')

    fulfillment_method = request.POST.get('fulfillment_method', 'pickup')
    payment_method = request.POST.get('payment_method', 'cash')

    shipping_info = {}
    if fulfillment_method == 'delivery':
        shipping_info = {
            'shipping_name': request.POST.get('shipping_name', ''),
            'shipping_address': request.POST.get('shipping_address', ''),
            'shipping_phone': request.POST.get('shipping_phone', ''),
        }

    # Create order
    order = Order.create_from_cart(
        cart=cart,
        user=request.user,
        fulfillment_method=fulfillment_method,
        payment_method=payment_method,
        **shipping_info
    )

    # Create Delivery record for delivery orders
    if fulfillment_method == 'delivery':
        slot_id = request.POST.get('delivery_slot')
        slot = None
        zone = None
        scheduled_date = None
        scheduled_time_start = None
        scheduled_time_end = None

        if slot_id:
            try:
                slot = DeliverySlot.objects.select_related('zone').get(
                    pk=slot_id,
                    is_active=True,
                    booked_count__lt=F('capacity')
                )
                zone = slot.zone
                scheduled_date = slot.date
                scheduled_time_start = slot.start_time
                scheduled_time_end = slot.end_time
                # Increment booked count
                slot.booked_count = F('booked_count') + 1
                slot.save(update_fields=['booked_count'])
            except DeliverySlot.DoesNotExist:
                pass

        Delivery.objects.create(
            order=order,
            slot=slot,
            zone=zone,
            address=shipping_info.get('shipping_address', ''),
            scheduled_date=scheduled_date,
            scheduled_time_start=scheduled_time_start,
            scheduled_time_end=scheduled_time_end,
            status='pending'
        )

    # Success message based on payment method
    if payment_method == 'card':
        messages.success(
            request,
            f'Order {order.order_number} paid successfully! Thank you for your purchase.'
        )
    elif payment_method == 'cash':
        messages.success(
            request,
            f'Order {order.order_number} created! Please pay in cash when you pick up or receive your order.'
        )
    else:
        messages.success(
            request,
            f'Order {order.order_number} created successfully!'
        )

    return redirect('store:order_detail', order_number=order.order_number)


class OrderListView(LoginRequiredMixin, ListView):
    """List user's orders."""

    model = Order
    template_name = 'store/order_list.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class OrderDetailView(LoginRequiredMixin, DetailView):
    """Show order details."""

    model = Order
    template_name = 'store/order_detail.html'
    context_object_name = 'order'
    slug_field = 'order_number'
    slug_url_kwarg = 'order_number'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.user != self.request.user:
            raise Http404("Order not found")
        return obj
