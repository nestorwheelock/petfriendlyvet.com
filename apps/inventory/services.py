"""Inventory management service functions (S-024).

Business logic for:
- Stock level updates
- Batch quantity management
- PO number generation
- Stock count workflows
- PO receiving workflows
"""
from decimal import Decimal
from typing import Optional

from django.db import transaction
from django.utils import timezone

from apps.inventory.models import (
    LocationType, StockLocation, StockLevel, StockBatch, StockMovement,
    PurchaseOrder, PurchaseOrderLine, StockCount, StockCountLine
)


# Movement types that are inbound (increase stock)
INBOUND_MOVEMENT_TYPES = ['receive', 'return_customer', 'transfer_in', 'adjustment_add']

# Movement types that are outbound (decrease stock)
OUTBOUND_MOVEMENT_TYPES = [
    'sale', 'dispense', 'return_supplier', 'transfer_out',
    'adjustment_remove', 'expired', 'damaged', 'loss', 'sample'
]


def update_stock_level(movement: StockMovement) -> None:
    """
    Update stock levels based on movement type.

    - Inbound types increase to_location quantity
    - Outbound types decrease from_location quantity
    - Transfers do both
    """
    movement_type = movement.movement_type

    # Handle outbound (decrease from source)
    if movement_type in OUTBOUND_MOVEMENT_TYPES and movement.from_location:
        stock_level, created = StockLevel.objects.get_or_create(
            product=movement.product,
            location=movement.from_location,
            defaults={'quantity': Decimal('0')}
        )
        stock_level.quantity -= movement.quantity
        stock_level.last_movement = timezone.now()
        stock_level.save()

    # Handle inbound (increase at destination)
    if movement_type in INBOUND_MOVEMENT_TYPES and movement.to_location:
        stock_level, created = StockLevel.objects.get_or_create(
            product=movement.product,
            location=movement.to_location,
            defaults={'quantity': Decimal('0')}
        )
        stock_level.quantity += movement.quantity
        stock_level.last_movement = timezone.now()
        stock_level.save()

    # Handle transfers (decrease source, increase destination)
    if movement_type == 'transfer_out' and movement.to_location:
        dest_stock, created = StockLevel.objects.get_or_create(
            product=movement.product,
            location=movement.to_location,
            defaults={'quantity': Decimal('0')}
        )
        dest_stock.quantity += movement.quantity
        dest_stock.last_movement = timezone.now()
        dest_stock.save()


def update_batch_quantity(movement: StockMovement) -> None:
    """
    Update batch current_quantity based on movement.

    - Outbound movements deduct from batch
    - Updates batch status if depleted
    """
    if not movement.batch:
        return

    batch = movement.batch
    movement_type = movement.movement_type

    if movement_type in OUTBOUND_MOVEMENT_TYPES:
        batch.current_quantity -= movement.quantity

        # Update status if depleted
        if batch.current_quantity <= 0:
            batch.current_quantity = Decimal('0')
            batch.status = 'depleted'
        elif batch.current_quantity <= batch.initial_quantity * Decimal('0.1'):
            batch.status = 'low'

        batch.save()


def generate_po_number() -> str:
    """
    Generate PO number in format PO-YYYYMMDD-XXX.

    Returns:
        str: Unique PO number
    """
    today = timezone.now().date()
    prefix = f"PO-{today.strftime('%Y%m%d')}"

    # Count existing POs with this prefix
    count = PurchaseOrder.objects.filter(
        po_number__startswith=prefix
    ).count() + 1

    return f"{prefix}-{count:03d}"


@transaction.atomic
def create_stock_count_with_lines(
    location: StockLocation,
    count_type: str,
    counted_by,
    product_filter: Optional[dict] = None
) -> StockCount:
    """
    Create a stock count and populate lines from current stock levels.

    Args:
        location: Stock location to count
        count_type: Type of count (full, cycle, spot)
        counted_by: User performing the count
        product_filter: Optional filter for specific products/categories

    Returns:
        StockCount: Created stock count with lines
    """
    stock_count = StockCount.objects.create(
        location=location,
        count_type=count_type,
        count_date=timezone.now().date(),
        counted_by=counted_by,
        status='draft'
    )

    # Get stock levels at this location
    stock_levels = StockLevel.objects.filter(
        location=location,
        quantity__gt=0
    ).select_related('product')

    # Create count lines for each stock level
    lines_created = 0
    for stock_level in stock_levels:
        StockCountLine.objects.create(
            stock_count=stock_count,
            product=stock_level.product,
            system_quantity=stock_level.quantity
        )
        lines_created += 1

    # Update totals
    stock_count.total_products = lines_created
    stock_count.save()

    return stock_count


@transaction.atomic
def post_count_adjustments(stock_count: StockCount, approved_by) -> None:
    """
    Post count adjustments to update stock levels.

    Creates StockMovement records for discrepancies and updates
    stock levels to match counted quantities.

    Args:
        stock_count: StockCount to post
        approved_by: User approving the adjustments
    """
    discrepancies = 0
    total_discrepancy_value = Decimal('0')

    for line in stock_count.lines.all():
        if line.counted_quantity is None:
            continue

        # Calculate discrepancy
        discrepancy = line.counted_quantity - line.system_quantity
        line.discrepancy = discrepancy

        if discrepancy != 0:
            discrepancies += 1

            # Create adjustment movement
            if discrepancy > 0:
                movement_type = 'adjustment_add'
                to_location = stock_count.location
                from_location = None
            else:
                movement_type = 'adjustment_remove'
                from_location = stock_count.location
                to_location = None

            movement = StockMovement.objects.create(
                product=line.product,
                movement_type=movement_type,
                from_location=from_location,
                to_location=to_location,
                quantity=abs(discrepancy),
                reason=line.adjustment_reason or f'Stock count adjustment',
                reference_type='stock_count',
                reference_id=stock_count.id,
                recorded_by=approved_by
            )

            # Update stock level
            update_stock_level(movement)

            line.adjustment_posted = True

        line.counted_at = timezone.now()
        line.save()

    # Update count status and totals
    stock_count.discrepancies_found = discrepancies
    stock_count.discrepancy_value = total_discrepancy_value
    stock_count.status = 'posted'
    stock_count.approved_by = approved_by
    stock_count.approved_at = timezone.now()
    stock_count.products_counted = stock_count.lines.filter(
        counted_quantity__isnull=False
    ).count()
    stock_count.save()


@transaction.atomic
def receive_purchase_order_line(
    po_line: PurchaseOrderLine,
    quantity_received: Decimal,
    batch_number: str,
    received_by,
    lot_number: str = '',
    expiry_date=None,
    notes: str = ''
) -> StockBatch:
    """
    Receive items against a PO line.

    Creates:
    - StockBatch for the received items
    - StockMovement for the receive action
    - Updates StockLevel
    - Updates PO line and PO status

    Args:
        po_line: PurchaseOrderLine being received
        quantity_received: Quantity to receive
        batch_number: Batch number for new batch
        received_by: User receiving the items
        lot_number: Optional lot number
        expiry_date: Optional expiry date
        notes: Optional notes

    Returns:
        StockBatch: Created stock batch
    """
    po = po_line.purchase_order
    location = po.delivery_location

    # Create stock batch
    batch = StockBatch.objects.create(
        product=po_line.product,
        location=location,
        batch_number=batch_number,
        lot_number=lot_number or '',
        initial_quantity=quantity_received,
        current_quantity=quantity_received,
        received_date=timezone.now().date(),
        expiry_date=expiry_date,
        unit_cost=po_line.unit_cost,
        supplier=po.supplier,
        purchase_order=po,
        status='available',
        notes=notes
    )

    # Create stock movement
    movement = StockMovement.objects.create(
        product=po_line.product,
        batch=batch,
        movement_type='receive',
        to_location=location,
        quantity=quantity_received,
        unit_cost=po_line.unit_cost,
        reference_type='purchase_order',
        reference_id=po.id,
        recorded_by=received_by
    )

    # Update stock level
    update_stock_level(movement)

    # Update PO line
    po_line.quantity_received += quantity_received
    po_line.save()

    # Update PO status
    _update_po_status(po)

    return batch


def _update_po_status(po: PurchaseOrder) -> None:
    """Update PO status based on received quantities."""
    total_ordered = Decimal('0')
    total_received = Decimal('0')

    for line in po.lines.all():
        total_ordered += line.quantity_ordered
        total_received += line.quantity_received

    if total_received >= total_ordered:
        po.status = 'received'
        po.received_date = timezone.now().date()
    elif total_received > 0:
        po.status = 'partial'

    po.save()


def sync_product_stock_quantity(product) -> None:
    """
    Sync Product.stock_quantity with total StockLevel quantities.

    Call this after stock level changes to keep Product model in sync.
    """
    from django.db.models import Sum

    total = StockLevel.objects.filter(
        product=product
    ).aggregate(total=Sum('quantity'))['total'] or Decimal('0')

    if hasattr(product, 'stock_quantity'):
        product.stock_quantity = total
        product.save(update_fields=['stock_quantity'])


# Default location types for inventory module
DEFAULT_LOCATION_TYPES = [
    {
        'name': 'Store Floor',
        'code': 'store',
        'description': 'Retail display area',
        'requires_temperature_control': False,
        'requires_restricted_access': False,
    },
    {
        'name': 'Warehouse',
        'code': 'warehouse',
        'description': 'Backstock and bulk storage',
        'requires_temperature_control': False,
        'requires_restricted_access': False,
    },
    {
        'name': 'Refrigerated',
        'code': 'refrigerated',
        'description': 'Temperature-controlled storage',
        'requires_temperature_control': True,
        'requires_restricted_access': False,
    },
    {
        'name': 'Clinic Storage',
        'code': 'clinic',
        'description': 'Clinical supplies storage',
        'requires_temperature_control': False,
        'requires_restricted_access': False,
    },
]


def seed_default_location_types() -> None:
    """
    Seed default location types for the inventory module.

    Safe to run multiple times (idempotent).
    """
    seed_module_location_types('inventory', DEFAULT_LOCATION_TYPES)


def seed_module_location_types(module_name: str, types: list) -> None:
    """
    Seed location types for a specific module.

    Used by modules to create their own location types on installation.
    E.g., pharmacy module creates 'Pharmacy', 'Controlled Substances' types.

    Args:
        module_name: Name of the module (e.g., 'pharmacy', 'inventory')
        types: List of dicts with location type data

    Safe to run multiple times (uses get_or_create).
    """
    for type_data in types:
        code = type_data.get('code')
        if not code:
            continue

        LocationType.objects.get_or_create(
            code=code,
            defaults={
                'name': type_data.get('name', code.title()),
                'description': type_data.get('description', ''),
                'requires_temperature_control': type_data.get('requires_temperature_control', False),
                'requires_restricted_access': type_data.get('requires_restricted_access', False),
                'source_module': module_name,
            }
        )
