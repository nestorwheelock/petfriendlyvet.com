"""Inventory app views for staff inventory management."""
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Q, F
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from datetime import timedelta

from apps.core.utils import staff_redirect

from .models import (
    InventoryItem,
    LocationType,
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
    from apps.inventory.models import StockCount, ReorderRule
    from django.db.models import Count

    today = timezone.now().date()
    expiry_threshold = today + timedelta(days=30)

    # === SUMMARY KPIs ===
    # Total inventory value
    total_value = StockBatch.objects.filter(
        status='available',
        current_quantity__gt=0
    ).aggregate(
        value=Sum(F('current_quantity') * F('unit_cost'))
    )['value'] or 0

    # Total unique products tracked
    total_products = StockLevel.objects.values('product').distinct().count()

    # Total stock locations
    total_locations = StockLocation.objects.filter(is_active=True).count()

    # === ALERT COUNTS ===
    # Low stock items (quantity at or below min_level)
    low_stock_items = StockLevel.objects.filter(
        quantity__lte=F('min_level')
    ).exclude(min_level__isnull=True).select_related('product', 'location')
    low_stock_count = low_stock_items.count()

    # Out of stock items (quantity = 0)
    out_of_stock_items = StockLevel.objects.filter(
        quantity=0
    ).select_related('product', 'location')
    out_of_stock_count = out_of_stock_items.count()

    # Expiring soon (within 30 days)
    expiring_batches = StockBatch.objects.filter(
        expiry_date__lte=expiry_threshold,
        expiry_date__gte=today,
        current_quantity__gt=0,
        status='available'
    ).select_related('product', 'location').order_by('expiry_date')
    expiring_count = expiring_batches.count()

    # Expired items (past expiry date, still in stock)
    expired_batches = StockBatch.objects.filter(
        expiry_date__lt=today,
        current_quantity__gt=0,
        status='available'
    ).select_related('product', 'location').order_by('expiry_date')
    expired_count = expired_batches.count()

    # === REORDER SUGGESTIONS ===
    # Items that have hit reorder point based on ReorderRule
    reorder_suggestions = []
    reorder_rules = ReorderRule.objects.filter(
        is_active=True
    ).select_related('product', 'preferred_supplier', 'location')

    for rule in reorder_rules:
        # Get current stock for this product/location combo
        stock_filter = {'product': rule.product}
        if rule.location:
            stock_filter['location'] = rule.location

        current_stock = StockLevel.objects.filter(**stock_filter).aggregate(
            total=Sum('quantity')
        )['total'] or 0

        if current_stock <= rule.reorder_point:
            reorder_suggestions.append({
                'rule': rule,
                'current_stock': current_stock,
                'shortfall': rule.reorder_point - current_stock,
            })

    # === PENDING ACTIONS ===
    # Pending purchase orders
    pending_po_count = PurchaseOrder.objects.filter(
        status__in=['draft', 'submitted', 'confirmed', 'shipped']
    ).count()

    # Draft POs awaiting submission
    draft_pos = PurchaseOrder.objects.filter(
        status='draft'
    ).select_related('supplier').order_by('-created_at')[:5]

    # POs ready to receive
    pos_to_receive = PurchaseOrder.objects.filter(
        status__in=['confirmed', 'shipped']
    ).select_related('supplier').order_by('-created_at')[:5]

    # Stock counts in progress
    counts_in_progress = StockCount.objects.filter(
        status__in=['draft', 'submitted']
    ).select_related('location', 'counted_by').order_by('-created_at')[:5]

    # === RECENT ACTIVITY ===
    recent_movements = StockMovement.objects.select_related(
        'product', 'from_location', 'to_location', 'recorded_by'
    ).order_by('-created_at')[:10]

    # === LOCATIONS WITH STOCK SUMMARY ===
    locations = StockLocation.objects.filter(is_active=True).prefetch_related(
        'location_type'
    ).annotate(
        item_count=Count('stock_levels'),
        low_stock_items=Count('stock_levels', filter=Q(
            stock_levels__quantity__lte=F('stock_levels__min_level')
        ))
    )

    context = {
        # Summary KPIs
        'total_value': total_value,
        'total_products': total_products,
        'total_locations': total_locations,
        # Alert counts
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'expiring_count': expiring_count,
        'expired_count': expired_count,
        # Alert items (for detail display)
        'low_stock_items': low_stock_items[:5],
        'out_of_stock_items': out_of_stock_items[:5],
        'expiring_batches': expiring_batches[:5],
        'expired_batches': expired_batches[:5],
        # Reorder suggestions
        'reorder_suggestions': reorder_suggestions[:5],
        # Pending actions
        'pending_po_count': pending_po_count,
        'draft_pos': draft_pos,
        'pos_to_receive': pos_to_receive,
        'counts_in_progress': counts_in_progress,
        # Activity & locations
        'recent_movements': recent_movements,
        'locations': locations,
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
    from apps.inventory.forms import StockMovementForm
    from apps.inventory.services import update_stock_level, update_batch_quantity

    if request.method == 'POST':
        form = StockMovementForm(request.POST)
        if form.is_valid():
            movement = form.save(commit=False)
            movement.recorded_by = request.user
            movement.save()

            # Update stock level
            update_stock_level(movement)

            # Update batch quantity if specified
            if movement.batch:
                update_batch_quantity(movement)

            messages.success(request, 'Stock movement recorded successfully.')
            return staff_redirect(request, 'inventory:movements')
    else:
        form = StockMovementForm()

    context = {
        'form': form,
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
def supplier_create(request):
    """Create a new supplier."""
    from apps.inventory.forms import SupplierForm

    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save()
            messages.success(request, f'Supplier {supplier.name} created.')
            return staff_redirect(request, 'inventory:supplier_detail', pk=supplier.pk)
    else:
        form = SupplierForm()

    context = {
        'form': form,
    }
    return render(request, 'inventory/supplier_form.html', context)


@staff_member_required
def supplier_edit(request, pk):
    """Edit an existing supplier."""
    from apps.inventory.forms import SupplierForm

    supplier = get_object_or_404(Supplier, pk=pk)

    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, f'Supplier {supplier.name} updated.')
            return staff_redirect(request, 'inventory:supplier_detail', pk=supplier.pk)
    else:
        form = SupplierForm(instance=supplier)

    context = {
        'form': form,
        'supplier': supplier,
    }
    return render(request, 'inventory/supplier_form.html', context)


# =============================================================================
# Stock Location CRUD Views
# =============================================================================

@staff_member_required
def stock_location_list(request):
    """List all stock locations."""
    locations = StockLocation.objects.all().order_by('name')

    context = {
        'locations': locations,
    }
    return render(request, 'inventory/location_list.html', context)


@staff_member_required
def stock_location_create(request):
    """Create a new stock location."""
    from apps.inventory.forms import StockLocationForm

    if request.method == 'POST':
        form = StockLocationForm(request.POST)
        if form.is_valid():
            location = form.save()
            messages.success(request, f'Location {location.name} created.')
            return staff_redirect(request, 'inventory:locations')
    else:
        form = StockLocationForm()

    context = {
        'form': form,
    }
    return render(request, 'inventory/location_form.html', context)


@staff_member_required
def stock_location_edit(request, pk):
    """Edit an existing stock location."""
    from apps.inventory.forms import StockLocationForm

    location = get_object_or_404(StockLocation, pk=pk)

    if request.method == 'POST':
        form = StockLocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            messages.success(request, f'Location {location.name} updated.')
            return staff_redirect(request, 'inventory:locations')
    else:
        form = StockLocationForm(instance=location)

    context = {
        'form': form,
        'location': location,
    }
    return render(request, 'inventory/location_form.html', context)


# =============================================================================
# Location Type CRUD Views
# =============================================================================

@staff_member_required
def location_type_list(request):
    """List all location types."""
    location_types = LocationType.objects.all().order_by('name')

    context = {
        'location_types': location_types,
    }
    return render(request, 'inventory/location_type_list.html', context)


@staff_member_required
def location_type_create(request):
    """Create a new location type."""
    from apps.inventory.forms import LocationTypeForm

    if request.method == 'POST':
        form = LocationTypeForm(request.POST)
        if form.is_valid():
            location_type = form.save()
            messages.success(request, f'Location type "{location_type.name}" created.')
            return staff_redirect(request, 'inventory:location_types')
    else:
        form = LocationTypeForm()

    context = {
        'form': form,
    }
    return render(request, 'inventory/location_type_form.html', context)


@staff_member_required
def location_type_edit(request, pk):
    """Edit a location type."""
    from apps.inventory.forms import LocationTypeForm

    location_type = get_object_or_404(LocationType, pk=pk)

    if request.method == 'POST':
        form = LocationTypeForm(request.POST, instance=location_type)
        if form.is_valid():
            form.save()
            messages.success(request, f'Location type "{location_type.name}" updated.')
            return staff_redirect(request, 'inventory:location_types')
    else:
        form = LocationTypeForm(instance=location_type)

    context = {
        'form': form,
        'location_type': location_type,
    }
    return render(request, 'inventory/location_type_form.html', context)


@staff_member_required
def location_type_delete(request, pk):
    """Delete a location type."""
    from django.db.models import ProtectedError

    location_type = get_object_or_404(LocationType, pk=pk)

    if request.method == 'POST':
        try:
            name = location_type.name
            location_type.delete()
            messages.success(request, f'Location type "{name}" deleted.')
        except ProtectedError:
            messages.error(
                request,
                f'Cannot delete "{location_type.name}" - it is in use by locations.'
            )
    return staff_redirect(request, 'inventory:location_types')


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


# =============================================================================
# Purchase Order Workflow Views
# =============================================================================

@staff_member_required
def purchase_order_create(request):
    """Create a new purchase order."""
    from apps.inventory.forms import PurchaseOrderForm

    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST)
        if form.is_valid():
            po = form.save(commit=False)
            po.created_by = request.user
            po.save()
            messages.success(request, f'Purchase order {po.po_number} created.')
            return staff_redirect(request, 'inventory:purchase_order_detail', pk=po.pk)
    else:
        form = PurchaseOrderForm()

    context = {
        'form': form,
    }
    return render(request, 'inventory/purchase_order_form.html', context)


@staff_member_required
def purchase_order_edit(request, pk):
    """Edit a draft purchase order."""
    from apps.inventory.forms import PurchaseOrderForm

    po = get_object_or_404(PurchaseOrder, pk=pk)

    if po.status != 'draft':
        messages.error(request, 'Only draft orders can be edited.')
        return staff_redirect(request, 'inventory:purchase_order_detail', pk=pk)

    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST, instance=po)
        if form.is_valid():
            form.save()
            messages.success(request, f'Purchase order {po.po_number} updated.')
            return staff_redirect(request, 'inventory:purchase_order_detail', pk=po.pk)
    else:
        form = PurchaseOrderForm(instance=po)

    context = {
        'form': form,
        'order': po,
    }
    return render(request, 'inventory/purchase_order_form.html', context)


@staff_member_required
def purchase_order_submit(request, pk):
    """Submit a draft PO for processing."""
    po = get_object_or_404(PurchaseOrder, pk=pk)

    if po.status != 'draft':
        messages.error(request, 'Only draft orders can be submitted.')
    else:
        po.status = 'submitted'
        po.order_date = timezone.now().date()
        po.save()
        messages.success(request, f'Purchase order {po.po_number} submitted.')

    return staff_redirect(request, 'inventory:purchase_order_detail', pk=pk)


@staff_member_required
def purchase_order_receive(request, pk):
    """Receive items against a purchase order."""
    from decimal import Decimal
    from apps.inventory.services import receive_purchase_order_line

    po = get_object_or_404(
        PurchaseOrder.objects.select_related('supplier', 'delivery_location'),
        pk=pk
    )
    lines = po.lines.select_related('product')

    if request.method == 'POST':
        received_any = False
        for line in lines:
            qty_key = f'line_{line.id}_quantity'
            batch_key = f'line_{line.id}_batch_number'

            qty_str = request.POST.get(qty_key, '')
            batch_number = request.POST.get(batch_key, '')

            if qty_str and batch_number:
                try:
                    qty = Decimal(qty_str)
                    if qty > 0:
                        lot_number = request.POST.get(f'line_{line.id}_lot_number', '')
                        expiry_str = request.POST.get(f'line_{line.id}_expiry_date', '')
                        expiry_date = None
                        if expiry_str:
                            from datetime import datetime
                            expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d').date()

                        receive_purchase_order_line(
                            po_line=line,
                            quantity_received=qty,
                            batch_number=batch_number,
                            received_by=request.user,
                            lot_number=lot_number,
                            expiry_date=expiry_date
                        )
                        received_any = True
                except (ValueError, TypeError):
                    pass

        if received_any:
            messages.success(request, 'Items received successfully.')
        return staff_redirect(request, 'inventory:purchase_order_detail', pk=pk)

    context = {
        'order': po,
        'lines': lines,
    }
    return render(request, 'inventory/purchase_order_receive.html', context)


# =============================================================================
# Stock Count Workflow Views
# =============================================================================

@staff_member_required
def stock_count_list(request):
    """List all stock counts."""
    from apps.inventory.models import StockCount

    status = request.GET.get('status', '')
    counts = StockCount.objects.select_related('location', 'counted_by')

    if status:
        counts = counts.filter(status=status)

    counts = counts.order_by('-created_at')

    context = {
        'counts': counts,
        'current_status': status,
        'status_choices': StockCount.STATUS_CHOICES,
    }
    return render(request, 'inventory/stock_count_list.html', context)


@staff_member_required
def stock_count_create(request):
    """Start a new stock count."""
    from apps.inventory.forms import StockCountForm
    from apps.inventory.services import create_stock_count_with_lines

    if request.method == 'POST':
        form = StockCountForm(request.POST)
        if form.is_valid():
            stock_count = create_stock_count_with_lines(
                location=form.cleaned_data['location'],
                count_type=form.cleaned_data['count_type'],
                counted_by=request.user
            )
            messages.success(request, 'Stock count started. Enter your counts.')
            return staff_redirect(request, 'inventory:stock_count_entry', pk=stock_count.pk)
    else:
        form = StockCountForm()

    context = {
        'form': form,
    }
    return render(request, 'inventory/stock_count_form.html', context)


@staff_member_required
def stock_count_detail(request, pk):
    """View stock count details."""
    from apps.inventory.models import StockCount

    count = get_object_or_404(
        StockCount.objects.select_related('location', 'counted_by', 'approved_by'),
        pk=pk
    )
    lines = count.lines.select_related('product')

    context = {
        'count': count,
        'lines': lines,
    }
    return render(request, 'inventory/stock_count_detail.html', context)


@staff_member_required
def stock_count_entry(request, pk):
    """Enter count quantities for a stock count."""
    from decimal import Decimal
    from apps.inventory.models import StockCount

    count = get_object_or_404(StockCount, pk=pk)

    if count.status not in ['draft']:
        messages.error(request, 'This count is no longer editable.')
        return staff_redirect(request, 'inventory:stock_count_detail', pk=pk)

    lines = count.lines.select_related('product')

    if request.method == 'POST':
        for line in lines:
            counted_key = f'line_{line.id}_counted'
            reason_key = f'line_{line.id}_reason'

            counted_str = request.POST.get(counted_key, '')
            reason = request.POST.get(reason_key, '')

            if counted_str:
                try:
                    line.counted_quantity = Decimal(counted_str)
                    line.adjustment_reason = reason
                    line.counted_at = timezone.now()
                    line.discrepancy = line.counted_quantity - line.system_quantity
                    line.save()
                except (ValueError, TypeError):
                    pass

        messages.success(request, 'Counts saved.')

        if 'submit_for_review' in request.POST:
            count.status = 'submitted'
            count.save()
            return staff_redirect(request, 'inventory:stock_count_detail', pk=pk)

        return staff_redirect(request, 'inventory:stock_count_entry', pk=pk)

    context = {
        'count': count,
        'lines': lines,
    }
    return render(request, 'inventory/stock_count_entry.html', context)


@staff_member_required
def stock_count_approve(request, pk):
    """Approve and post stock count adjustments."""
    from apps.inventory.models import StockCount
    from apps.inventory.services import post_count_adjustments

    count = get_object_or_404(StockCount, pk=pk)

    if count.status not in ['submitted', 'approved']:
        messages.error(request, 'This count cannot be approved yet.')
        return staff_redirect(request, 'inventory:stock_count_detail', pk=pk)

    if request.method == 'POST':
        post_count_adjustments(count, approved_by=request.user)
        messages.success(request, 'Stock count adjustments posted.')

    return staff_redirect(request, 'inventory:stock_count_detail', pk=pk)


# =============================================================================
# Transfer Workflow Views
# =============================================================================

@staff_member_required
def transfer_create(request):
    """Create a stock transfer between locations."""
    from apps.inventory.forms import StockTransferForm
    from apps.inventory.services import update_stock_level, update_batch_quantity

    if request.method == 'POST':
        form = StockTransferForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            # Create transfer out movement
            movement_out = StockMovement.objects.create(
                product=data['product'],
                batch=data.get('batch'),
                movement_type='transfer_out',
                from_location=data['from_location'],
                to_location=data['to_location'],
                quantity=data['quantity'],
                reason=data.get('reason', ''),
                recorded_by=request.user
            )

            # Update stock levels
            update_stock_level(movement_out)

            # Update batch quantity if specified
            if movement_out.batch:
                update_batch_quantity(movement_out)

            messages.success(request, 'Stock transfer completed.')
            return staff_redirect(request, 'inventory:movements')
    else:
        form = StockTransferForm()

    context = {
        'form': form,
    }
    return render(request, 'inventory/transfer_form.html', context)


# =============================================================================
# Purchase Order Line CRUD Views
# =============================================================================

@staff_member_required
def po_line_add(request, po_pk):
    """Add a line item to a purchase order."""
    from apps.inventory.forms import PurchaseOrderLineForm
    from apps.inventory.models import PurchaseOrderLine

    po = get_object_or_404(PurchaseOrder, pk=po_pk)

    if po.status != 'draft':
        messages.error(request, 'Can only add lines to draft orders.')
        return staff_redirect(request, 'inventory:purchase_order_detail', pk=po_pk)

    if request.method == 'POST':
        form = PurchaseOrderLineForm(request.POST)
        if form.is_valid():
            line = form.save(commit=False)
            line.purchase_order = po
            line.save()
            # Update PO totals
            po.update_totals()
            messages.success(request, 'Line item added.')
            return staff_redirect(request, 'inventory:purchase_order_detail', pk=po_pk)
    else:
        form = PurchaseOrderLineForm()

    context = {
        'form': form,
        'order': po,
    }
    return render(request, 'inventory/po_line_form.html', context)


@staff_member_required
def po_line_edit(request, po_pk, pk):
    """Edit a purchase order line item."""
    from apps.inventory.forms import PurchaseOrderLineForm
    from apps.inventory.models import PurchaseOrderLine

    po = get_object_or_404(PurchaseOrder, pk=po_pk)
    line = get_object_or_404(PurchaseOrderLine, pk=pk, purchase_order=po)

    if po.status != 'draft':
        messages.error(request, 'Can only edit lines on draft orders.')
        return staff_redirect(request, 'inventory:purchase_order_detail', pk=po_pk)

    if request.method == 'POST':
        form = PurchaseOrderLineForm(request.POST, instance=line)
        if form.is_valid():
            form.save()
            po.update_totals()
            messages.success(request, 'Line item updated.')
            return staff_redirect(request, 'inventory:purchase_order_detail', pk=po_pk)
    else:
        form = PurchaseOrderLineForm(instance=line)

    context = {
        'form': form,
        'order': po,
        'line': line,
    }
    return render(request, 'inventory/po_line_form.html', context)


@staff_member_required
def po_line_delete(request, po_pk, pk):
    """Delete a purchase order line item."""
    from apps.inventory.models import PurchaseOrderLine

    po = get_object_or_404(PurchaseOrder, pk=po_pk)
    line = get_object_or_404(PurchaseOrderLine, pk=pk, purchase_order=po)

    if po.status != 'draft':
        messages.error(request, 'Can only delete lines from draft orders.')
        return staff_redirect(request, 'inventory:purchase_order_detail', pk=po_pk)

    if request.method == 'POST':
        line.delete()
        po.update_totals()
        messages.success(request, 'Line item deleted.')

    return staff_redirect(request, 'inventory:purchase_order_detail', pk=po_pk)


# =============================================================================
# Reorder Rule CRUD Views
# =============================================================================

@staff_member_required
def reorder_rule_list(request):
    """List all reorder rules."""
    from apps.inventory.models import ReorderRule

    rules = ReorderRule.objects.select_related(
        'product', 'location', 'preferred_supplier'
    ).order_by('product__name')

    context = {
        'rules': rules,
    }
    return render(request, 'inventory/reorder_rule_list.html', context)


@staff_member_required
def reorder_rule_create(request):
    """Create a new reorder rule."""
    from apps.inventory.forms import ReorderRuleForm

    if request.method == 'POST':
        form = ReorderRuleForm(request.POST)
        if form.is_valid():
            rule = form.save()
            messages.success(request, f'Reorder rule for {rule.product.name} created.')
            return staff_redirect(request, 'inventory:reorder_rules')
    else:
        form = ReorderRuleForm()

    context = {
        'form': form,
    }
    return render(request, 'inventory/reorder_rule_form.html', context)


@staff_member_required
def reorder_rule_edit(request, pk):
    """Edit a reorder rule."""
    from apps.inventory.forms import ReorderRuleForm
    from apps.inventory.models import ReorderRule

    rule = get_object_or_404(ReorderRule, pk=pk)

    if request.method == 'POST':
        form = ReorderRuleForm(request.POST, instance=rule)
        if form.is_valid():
            form.save()
            messages.success(request, f'Reorder rule for {rule.product.name} updated.')
            return staff_redirect(request, 'inventory:reorder_rules')
    else:
        form = ReorderRuleForm(instance=rule)

    context = {
        'form': form,
        'rule': rule,
    }
    return render(request, 'inventory/reorder_rule_form.html', context)


# =============================================================================
# Product-Supplier Link CRUD Views
# =============================================================================

@staff_member_required
def product_supplier_list(request):
    """List all product-supplier links."""
    from apps.inventory.models import ProductSupplier

    links = ProductSupplier.objects.select_related(
        'product', 'supplier'
    ).order_by('product__name', 'supplier__name')

    context = {
        'links': links,
    }
    return render(request, 'inventory/product_supplier_list.html', context)


@staff_member_required
def product_supplier_create(request):
    """Create a new product-supplier link."""
    from apps.inventory.forms import ProductSupplierForm

    if request.method == 'POST':
        form = ProductSupplierForm(request.POST)
        if form.is_valid():
            link = form.save()
            messages.success(request, f'Link created: {link.product.name} - {link.supplier.name}')
            return staff_redirect(request, 'inventory:product_suppliers')
    else:
        form = ProductSupplierForm()

    context = {
        'form': form,
    }
    return render(request, 'inventory/product_supplier_form.html', context)


@staff_member_required
def product_supplier_edit(request, pk):
    """Edit a product-supplier link."""
    from apps.inventory.forms import ProductSupplierForm
    from apps.inventory.models import ProductSupplier

    link = get_object_or_404(ProductSupplier, pk=pk)

    if request.method == 'POST':
        form = ProductSupplierForm(request.POST, instance=link)
        if form.is_valid():
            form.save()
            messages.success(request, f'Link updated: {link.product.name} - {link.supplier.name}')
            return staff_redirect(request, 'inventory:product_suppliers')
    else:
        form = ProductSupplierForm(instance=link)

    context = {
        'form': form,
        'link': link,
    }
    return render(request, 'inventory/product_supplier_form.html', context)


# =============================================================================
# Stock Batch CRUD Views
# =============================================================================

@staff_member_required
def batch_create(request):
    """Create a new stock batch."""
    from apps.inventory.forms import StockBatchForm

    if request.method == 'POST':
        form = StockBatchForm(request.POST)
        if form.is_valid():
            batch = form.save()
            messages.success(request, f'Batch {batch.batch_number} created.')
            return staff_redirect(request, 'inventory:batches')
    else:
        form = StockBatchForm()

    context = {
        'form': form,
    }
    return render(request, 'inventory/batch_form.html', context)


@staff_member_required
def batch_edit(request, pk):
    """Edit a stock batch."""
    from apps.inventory.forms import StockBatchForm

    batch = get_object_or_404(StockBatch, pk=pk)

    if request.method == 'POST':
        form = StockBatchForm(request.POST, instance=batch)
        if form.is_valid():
            form.save()
            messages.success(request, f'Batch {batch.batch_number} updated.')
            return staff_redirect(request, 'inventory:batches')
    else:
        form = StockBatchForm(instance=batch)

    context = {
        'form': form,
        'batch': batch,
    }
    return render(request, 'inventory/batch_form.html', context)


# =============================================================================
# Stock Level CRUD Views
# =============================================================================

@staff_member_required
def stock_level_create(request):
    """Create a new stock level."""
    from apps.inventory.forms import StockLevelForm

    if request.method == 'POST':
        form = StockLevelForm(request.POST)
        if form.is_valid():
            level = form.save()
            messages.success(request, f'Stock level for {level.product.name} at {level.location.name} created.')
            return staff_redirect(request, 'inventory:stock')
    else:
        form = StockLevelForm()

    context = {
        'form': form,
    }
    return render(request, 'inventory/stock_level_form.html', context)


@staff_member_required
def stock_level_edit(request, pk):
    """Edit a stock level."""
    from apps.inventory.forms import StockLevelForm

    stock_level = get_object_or_404(StockLevel, pk=pk)

    if request.method == 'POST':
        form = StockLevelForm(request.POST, instance=stock_level)
        if form.is_valid():
            form.save()
            messages.success(request, f'Stock level updated.')
            return staff_redirect(request, 'inventory:stock')
    else:
        form = StockLevelForm(instance=stock_level)

    context = {
        'form': form,
        'stock_level': stock_level,
    }
    return render(request, 'inventory/stock_level_form.html', context)


@staff_member_required
def stock_level_adjust(request, pk):
    """Adjust stock level quantity."""
    from decimal import Decimal
    from apps.inventory.forms import StockLevelAdjustmentForm
    from apps.inventory.models import StockMovement

    stock_level = get_object_or_404(StockLevel, pk=pk)

    if request.method == 'POST':
        form = StockLevelAdjustmentForm(request.POST)
        if form.is_valid():
            adjustment = form.cleaned_data['adjustment']
            reason = form.cleaned_data['reason']

            # Update stock level
            stock_level.quantity += adjustment
            stock_level.save()

            # Create movement record
            movement_type = 'adjustment_add' if adjustment > 0 else 'adjustment_remove'
            StockMovement.objects.create(
                product=stock_level.product,
                movement_type=movement_type,
                quantity=abs(adjustment),
                from_location=stock_level.location if adjustment < 0 else None,
                to_location=stock_level.location if adjustment > 0 else None,
                reason=reason,
                recorded_by=request.user
            )

            messages.success(request, f'Stock level adjusted by {adjustment}.')
            return staff_redirect(request, 'inventory:stock')
    else:
        form = StockLevelAdjustmentForm()

    context = {
        'form': form,
        'stock_level': stock_level,
    }
    return render(request, 'inventory/stock_level_adjust.html', context)


# =============================================================================
# Inventory Item CRUD Views
# =============================================================================

@staff_member_required
def inventory_item_list(request):
    """List all inventory items with filtering."""
    item_type = request.GET.get('item_type', '')
    search = request.GET.get('search', '')

    items = InventoryItem.objects.select_related(
        'sat_product_code', 'sat_unit_code', 'tax_rate'
    )

    if item_type:
        items = items.filter(item_type=item_type)

    if search:
        items = items.filter(
            Q(name__icontains=search) |
            Q(sku__icontains=search) |
            Q(description__icontains=search)
        )

    items = items.order_by('name')

    context = {
        'items': items,
        'current_type': item_type,
        'search': search,
        'item_type_choices': InventoryItem.ITEM_TYPE_CHOICES,
    }
    return render(request, 'inventory/item_list.html', context)


@staff_member_required
def inventory_item_create(request):
    """Create a new inventory item."""
    from apps.inventory.forms import InventoryItemForm

    if request.method == 'POST':
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            item = form.save()
            messages.success(request, f'Inventory item "{item.name}" created.')
            return staff_redirect(request, 'inventory:item_detail', pk=item.pk)
    else:
        form = InventoryItemForm()

    context = {
        'form': form,
    }
    return render(request, 'inventory/item_form.html', context)


@staff_member_required
def inventory_item_detail(request, pk):
    """View inventory item details."""
    item = get_object_or_404(
        InventoryItem.objects.select_related(
            'sat_product_code', 'sat_unit_code', 'tax_rate'
        ),
        pk=pk
    )

    context = {
        'item': item,
    }
    return render(request, 'inventory/item_detail.html', context)


@staff_member_required
def inventory_item_edit(request, pk):
    """Edit an inventory item."""
    from apps.inventory.forms import InventoryItemForm

    item = get_object_or_404(InventoryItem, pk=pk)

    if request.method == 'POST':
        form = InventoryItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f'Inventory item "{item.name}" updated.')
            return staff_redirect(request, 'inventory:item_detail', pk=item.pk)
    else:
        form = InventoryItemForm(instance=item)

    context = {
        'form': form,
        'item': item,
    }
    return render(request, 'inventory/item_form.html', context)
