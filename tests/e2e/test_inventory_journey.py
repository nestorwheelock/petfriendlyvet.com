"""E2E test for inventory reorder journey.

Simulates the complete inventory management workflow using actual models.
Tests the inventory automation system.
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta

from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db(transaction=True)
class TestInventoryReorderJourney:
    """Complete inventory reorder journey."""

    @pytest.fixture
    def inventory_manager(self, db):
        """Create inventory manager user."""
        from apps.practice.models import StaffProfile

        user = User.objects.create_user(
            username='inventory@petfriendlyvet.com',
            email='inventory@petfriendlyvet.com',
            password='inv123',
            first_name='Jorge',
            last_name='Inventario',
            role='staff',
            is_staff=True,
        )
        StaffProfile.objects.create(
            user=user,
            role='manager',
        )
        return user

    @pytest.fixture
    def supplier(self, db):
        """Create a supplier."""
        from apps.inventory.models import Supplier

        return Supplier.objects.create(
            name='Distribuidora Veterinaria MX',
            contact_name='Luis Proveedor',
            email='ventas@distvermx.com',
            phone='555-SUPPLY',
            address='Av. Industrial 456, CDMX',
            payment_terms='Net 30',
            lead_time_days=5,
            is_active=True,
        )

    @pytest.fixture
    def stock_location(self, db):
        """Create main stock location."""
        from apps.inventory.models import StockLocation

        return StockLocation.objects.create(
            name='Almacén Principal',
            location_type='warehouse',
            is_active=True,
        )

    @pytest.fixture
    def product(self, db):
        """Create a product for inventory tracking."""
        from apps.store.models import Product, Category

        category = Category.objects.create(
            name='Medicamentos',
            slug='medicamentos',
        )

        return Product.objects.create(
            name='Amoxicillin 250mg',
            name_es='Amoxicilina 250mg',
            name_en='Amoxicillin 250mg',
            slug='amoxicillin-250mg',
            sku='AMX-250',
            category=category,
            price=Decimal('150.00'),
            stock_quantity=30,
            low_stock_threshold=50,
            is_active=True,
        )

    def test_complete_reorder_journey(
        self, db, inventory_manager, supplier, stock_location, product
    ):
        """Test inventory reorder from low stock to replenishment."""
        from apps.inventory.models import (
            StockLevel, StockBatch, StockMovement,
            PurchaseOrder, PurchaseOrderLine, ReorderRule
        )
        from apps.notifications.models import Notification

        # =========================================================================
        # STEP 1: Set Up Reorder Rules
        # =========================================================================
        reorder_rule = ReorderRule.objects.create(
            product=product,
            location=stock_location,
            min_level=Decimal('20'),
            reorder_point=Decimal('50'),
            reorder_quantity=Decimal('200'),
            max_level=Decimal('500'),
            preferred_supplier=supplier,
            is_active=True,
        )

        assert reorder_rule.pk is not None

        # =========================================================================
        # STEP 2: Create Stock Level (Below Reorder Point)
        # =========================================================================
        stock_level = StockLevel.objects.create(
            product=product,
            location=stock_location,
            quantity=Decimal('30'),
            reserved_quantity=Decimal('0'),
        )

        assert stock_level.quantity < reorder_rule.reorder_point

        # =========================================================================
        # STEP 3: Low Stock Alert
        # =========================================================================
        low_stock_notification = Notification.objects.create(
            user=inventory_manager,
            notification_type='low_stock_alert',
            title='Alerta de Stock Bajo',
            message=f'{product.name} está por debajo del punto de reorden.',
            email_sent=True,
            email_sent_at=timezone.now(),
        )

        assert low_stock_notification.pk is not None

        # =========================================================================
        # STEP 4: Create Purchase Order
        # =========================================================================
        import uuid
        po_number = f'PO-{uuid.uuid4().hex[:8].upper()}'

        purchase_order = PurchaseOrder.objects.create(
            po_number=po_number,
            supplier=supplier,
            status='draft',
            expected_date=date.today() + timedelta(days=supplier.lead_time_days),
            delivery_location=stock_location,
            created_by=inventory_manager,
        )

        # Add line item
        unit_cost = Decimal('75.00')
        line = PurchaseOrderLine.objects.create(
            purchase_order=purchase_order,
            product=product,
            quantity_ordered=reorder_rule.reorder_quantity,
            unit_cost=unit_cost,
            line_total=unit_cost * reorder_rule.reorder_quantity,
        )

        # Calculate totals
        purchase_order.subtotal = line.line_total
        purchase_order.total = line.line_total
        purchase_order.save()

        assert purchase_order.pk is not None

        # =========================================================================
        # STEP 5: Submit and Confirm Order
        # =========================================================================
        purchase_order.status = 'submitted'
        purchase_order.order_date = date.today()
        purchase_order.save()

        purchase_order.status = 'confirmed'
        purchase_order.save()

        # =========================================================================
        # STEP 6: Receive Goods
        # =========================================================================
        purchase_order.status = 'received'
        purchase_order.received_date = date.today()
        purchase_order.save()

        # Update line received quantity
        line.quantity_received = line.quantity_ordered
        line.save()

        # Create stock batch
        batch = StockBatch.objects.create(
            product=product,
            location=stock_location,
            batch_number='AMX-2024-001',
            initial_quantity=reorder_rule.reorder_quantity,
            current_quantity=reorder_rule.reorder_quantity,
            received_date=date.today(),
            expiry_date=date.today() + timedelta(days=730),
            unit_cost=unit_cost,
            supplier=supplier,
            purchase_order=purchase_order,
            status='available',
        )

        assert batch.pk is not None

        # Record stock movement
        movement = StockMovement.objects.create(
            product=product,
            batch=batch,
            movement_type='receive',
            to_location=stock_location,
            quantity=reorder_rule.reorder_quantity,
            unit_cost=unit_cost,
            reference_type='purchase_order',
            reference_id=purchase_order.pk,
            recorded_by=inventory_manager,
        )

        assert movement.pk is not None

        # =========================================================================
        # STEP 7: Update Stock Level
        # =========================================================================
        stock_level.quantity += reorder_rule.reorder_quantity
        stock_level.save()

        stock_level.refresh_from_db()
        assert stock_level.quantity == Decimal('230')  # 30 + 200
        assert stock_level.quantity > reorder_rule.reorder_point


@pytest.mark.django_db(transaction=True)
class TestInventoryExpiryManagement:
    """Test inventory expiry date handling."""

    def test_batch_expiry_tracking(self, db):
        """Batches track expiry dates."""
        from apps.inventory.models import StockLocation, StockBatch
        from apps.store.models import Product, Category

        location = StockLocation.objects.create(
            name='Pharmacy',
            location_type='pharmacy',
            is_active=True,
        )

        category = Category.objects.create(name='Test', slug='test')
        product = Product.objects.create(
            name='Test Product',
            name_es='Producto de Prueba',
            name_en='Test Product',
            slug='test-product',
            sku='TEST-001',
            category=category,
            price=Decimal('100.00'),
            is_active=True,
        )

        # Create batch expiring soon
        batch = StockBatch.objects.create(
            product=product,
            location=location,
            batch_number='EXP-SOON',
            initial_quantity=Decimal('50'),
            current_quantity=Decimal('50'),
            received_date=date.today() - timedelta(days=335),
            expiry_date=date.today() + timedelta(days=30),
            unit_cost=Decimal('50.00'),
            status='available',
        )

        # Check expiry
        assert batch.is_expired is False
        assert batch.days_until_expiry == 30

        # Can query expiring batches
        expiring_soon = StockBatch.objects.filter(
            expiry_date__lte=date.today() + timedelta(days=60),
            expiry_date__gt=date.today(),
            current_quantity__gt=0,
        )
        assert expiring_soon.count() >= 1


@pytest.mark.django_db(transaction=True)
class TestInventoryStockMovements:
    """Test stock movement tracking."""

    def test_stock_movement_types(self, db):
        """Different movement types are recorded."""
        from apps.inventory.models import StockLocation, StockMovement
        from apps.store.models import Product, Category

        location = StockLocation.objects.create(
            name='Store',
            location_type='store',
            is_active=True,
        )

        category = Category.objects.create(name='Test2', slug='test2')
        product = Product.objects.create(
            name='Movement Test',
            name_es='Prueba de Movimiento',
            name_en='Movement Test',
            slug='movement-test',
            sku='MOV-001',
            category=category,
            price=Decimal('100.00'),
            is_active=True,
        )

        user = User.objects.create_user(
            username='movement@test.com',
            email='movement@test.com',
            password='test123',
            role='staff',
            is_staff=True,
        )

        # Record different movement types
        movements = [
            ('receive', 100),
            ('sale', -5),
            ('adjustment_remove', -2),
        ]

        for movement_type, qty in movements:
            StockMovement.objects.create(
                product=product,
                movement_type=movement_type,
                to_location=location if qty > 0 else None,
                from_location=location if qty < 0 else None,
                quantity=Decimal(str(abs(qty))),
                recorded_by=user,
            )

        # All movements recorded
        assert StockMovement.objects.filter(product=product).count() == 3
