"""Inventory app views for staff inventory management."""
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Q, F
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from datetime import timedelta

from .models import (
    PurchaseOrder,
    StockBatch,
    StockLevel,
    StockLocation,
    StockMovement,
    Supplier,
)


@staff_member_required
def dashboard(request):
    """Inventory dashboard with key metrics and alerts."""
    # Get stock alerts
    low_stock_count = StockLevel.objects.filter(
        quantity__lte=F('min_level')
    ).exclude(min_level__isnull=True).count()

    # Expiring soon (within 30 days)
    expiry_threshold = timezone.now().date() + timedelta(days=30)
    expiring_count = StockBatch.objects.filter(
        expiry_date__lte=expiry_threshold,
        expiry_date__gte=timezone.now().date(),
        current_quantity__gt=0,
        status='available'
    ).count()

    # Expired items
    expired_count = StockBatch.objects.filter(
        expiry_date__lt=timezone.now().date(),
        current_quantity__gt=0,
        status='available'
    ).count()

    # Pending purchase orders
    pending_po_count = PurchaseOrder.objects.filter(
        status__in=['draft', 'submitted', 'confirmed', 'shipped']
    ).count()

    # Recent movements
    recent_movements = StockMovement.objects.select_related(
        'product', 'from_location', 'to_location', 'recorded_by'
    ).order_by('-created_at')[:10]

    # Stock locations
    locations = StockLocation.objects.filter(is_active=True)

    # Total stock value (simplified calculation)
    total_value = StockBatch.objects.filter(
        status='available',
        current_quantity__gt=0
    ).aggregate(
        value=Sum(F('current_quantity') * F('unit_cost'))
    )['value'] or 0

    context = {
        'low_stock_count': low_stock_count,
        'expiring_count': expiring_count,
        'expired_count': expired_count,
        'pending_po_count': pending_po_count,
        'recent_movements': recent_movements,
        'locations': locations,
        'total_value': total_value,
    }
    return render(request, 'inventory/dashboard.html', context)


@staff_member_required
def stock_levels(request):
    """List stock levels by product and location."""
    location_id = request.GET.get('location')
    search = request.GET.get('search', '')

    stock = StockLevel.objects.select_related('product', 'location')

    if location_id:
        stock = stock.filter(location_id=location_id)

    if search:
        stock = stock.filter(
            Q(product__name__icontains=search) |
            Q(product__sku__icontains=search)
        )

    # Group by low stock status
    low_stock = stock.filter(quantity__lte=F('min_level')).exclude(min_level__isnull=True)
    normal_stock = stock.exclude(pk__in=low_stock)

    locations = StockLocation.objects.filter(is_active=True)

    context = {
        'low_stock': low_stock,
        'normal_stock': normal_stock,
        'locations': locations,
        'current_location': location_id,
        'search': search,
    }
    return render(request, 'inventory/stock_levels.html', context)


@staff_member_required
def batch_list(request):
    """List stock batches with filtering."""
    status = request.GET.get('status', '')
    location_id = request.GET.get('location')

    batches = StockBatch.objects.select_related(
        'product', 'location', 'supplier'
    ).filter(current_quantity__gt=0)

    if status:
        batches = batches.filter(status=status)

    if location_id:
        batches = batches.filter(location_id=location_id)

    # Default: order by expiry date (FEFO)
    batches = batches.order_by('expiry_date', 'received_date')

    locations = StockLocation.objects.filter(is_active=True)

    context = {
        'batches': batches,
        'locations': locations,
        'current_status': status,
        'current_location': location_id,
        'status_choices': StockBatch.STATUS_CHOICES,
    }
    return render(request, 'inventory/batch_list.html', context)


@staff_member_required
def batch_detail(request, pk):
    """View batch details and movement history."""
    batch = get_object_or_404(
        StockBatch.objects.select_related('product', 'location', 'supplier'),
        pk=pk
    )

    movements = batch.movements.select_related(
        'recorded_by', 'from_location', 'to_location'
    ).order_by('-created_at')

    context = {
        'batch': batch,
        'movements': movements,
    }
    return render(request, 'inventory/batch_detail.html', context)


@staff_member_required
def movement_list(request):
    """Stock movement history."""
    movement_type = request.GET.get('type', '')
    location_id = request.GET.get('location')

    movements = StockMovement.objects.select_related(
        'product', 'batch', 'from_location', 'to_location', 'recorded_by'
    )

    if movement_type:
        movements = movements.filter(movement_type=movement_type)

    if location_id:
        movements = movements.filter(
            Q(from_location_id=location_id) | Q(to_location_id=location_id)
        )

    movements = movements.order_by('-created_at')[:100]

    locations = StockLocation.objects.filter(is_active=True)

    context = {
        'movements': movements,
        'locations': locations,
        'current_type': movement_type,
        'current_location': location_id,
        'movement_types': StockMovement.MOVEMENT_TYPES,
    }
    return render(request, 'inventory/movement_list.html', context)


@staff_member_required
def movement_add(request):
    """Record a new stock movement."""
    if request.method == 'POST':
        # Handle form submission
        messages.success(request, 'Stock movement recorded successfully.')
        return redirect('inventory:movements')

    locations = StockLocation.objects.filter(is_active=True)

    context = {
        'locations': locations,
        'movement_types': StockMovement.MOVEMENT_TYPES,
    }
    return render(request, 'inventory/movement_add.html', context)


@staff_member_required
def supplier_list(request):
    """List suppliers."""
    search = request.GET.get('search', '')

    suppliers = Supplier.objects.filter(is_active=True)

    if search:
        suppliers = suppliers.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search) |
            Q(contact_name__icontains=search)
        )

    context = {
        'suppliers': suppliers,
        'search': search,
    }
    return render(request, 'inventory/supplier_list.html', context)


@staff_member_required
def supplier_detail(request, pk):
    """View supplier details and order history."""
    supplier = get_object_or_404(Supplier, pk=pk)

    orders = supplier.purchase_orders.order_by('-created_at')[:20]
    products = supplier.products.select_related('product')[:50]

    context = {
        'supplier': supplier,
        'orders': orders,
        'products': products,
    }
    return render(request, 'inventory/supplier_detail.html', context)


@staff_member_required
def purchase_order_list(request):
    """List purchase orders."""
    status = request.GET.get('status', '')

    orders = PurchaseOrder.objects.select_related(
        'supplier', 'created_by', 'delivery_location'
    )

    if status:
        orders = orders.filter(status=status)

    orders = orders.order_by('-created_at')

    context = {
        'orders': orders,
        'current_status': status,
        'status_choices': PurchaseOrder.STATUS_CHOICES,
    }
    return render(request, 'inventory/purchase_order_list.html', context)


@staff_member_required
def purchase_order_detail(request, pk):
    """View purchase order details."""
    order = get_object_or_404(
        PurchaseOrder.objects.select_related('supplier', 'created_by', 'delivery_location'),
        pk=pk
    )

    lines = order.lines.select_related('product')

    context = {
        'order': order,
        'lines': lines,
    }
    return render(request, 'inventory/purchase_order_detail.html', context)


@staff_member_required
def alerts(request):
    """Stock alerts - low stock and reorder suggestions."""
    # Low stock items
    low_stock = StockLevel.objects.select_related(
        'product', 'location'
    ).filter(
        quantity__lte=F('min_level')
    ).exclude(min_level__isnull=True).order_by('quantity')

    # Items at zero stock
    out_of_stock = StockLevel.objects.select_related(
        'product', 'location'
    ).filter(quantity=0)

    # Expired items
    expired = StockBatch.objects.select_related(
        'product', 'location'
    ).filter(
        expiry_date__lt=timezone.now().date(),
        current_quantity__gt=0,
        status='available'
    )

    context = {
        'low_stock': low_stock,
        'out_of_stock': out_of_stock,
        'expired': expired,
    }
    return render(request, 'inventory/alerts.html', context)


@staff_member_required
def expiring_items(request):
    """Items expiring soon."""
    days = int(request.GET.get('days', 30))
    expiry_threshold = timezone.now().date() + timedelta(days=days)

    expiring = StockBatch.objects.select_related(
        'product', 'location'
    ).filter(
        expiry_date__lte=expiry_threshold,
        expiry_date__gte=timezone.now().date(),
        current_quantity__gt=0,
        status='available'
    ).order_by('expiry_date')

    context = {
        'expiring': expiring,
        'days': days,
    }
    return render(request, 'inventory/expiring.html', context)
