"""Tests for inventory architecture refactor models."""
import pytest
from decimal import Decimal

from django.db import IntegrityError


@pytest.mark.django_db
class TestProductTypeModel:
    """Test ProductType model for dynamic product classification."""

    def test_product_type_creation(self):
        """Can create a product type."""
        from apps.store.models import ProductType

        pt = ProductType.objects.create(
            code='physical',
            name='Physical Product',
            description='Tangible items that require inventory tracking',
            requires_inventory=True,
            requires_service_module=False,
        )
        assert pt.pk is not None
        assert pt.code == 'physical'

    def test_product_type_code_unique(self):
        """Product type code must be unique."""
        from apps.store.models import ProductType

        ProductType.objects.create(code='physical', name='Physical')
        with pytest.raises(IntegrityError):
            ProductType.objects.create(code='physical', name='Another Physical')

    def test_product_type_str(self):
        """String representation is the name."""
        from apps.store.models import ProductType

        pt = ProductType.objects.create(code='service', name='Service')
        assert str(pt) == 'Service'

    def test_default_product_types_exist(self):
        """After migration, default types should exist."""
        from apps.store.models import ProductType
        from django.core.management import call_command

        call_command('populate_product_types')

        assert ProductType.objects.filter(code='physical').exists()
        assert ProductType.objects.filter(code='service').exists()
        assert ProductType.objects.filter(code='bundle').exists()
        assert ProductType.objects.filter(code='dropship').exists()


@pytest.mark.django_db
class TestInventoryCategoryModel:
    """Test InventoryCategory model for internal inventory organization."""

    def test_inventory_category_creation(self):
        """Can create an inventory category."""
        from apps.inventory.models import InventoryCategory

        cat = InventoryCategory.objects.create(
            code='medication',
            name='Medications',
            description='Pharmaceutical products',
            requires_refrigeration=False,
            requires_controlled_access=False,
            is_pharmaceutical=True,
        )
        assert cat.pk is not None
        assert cat.code == 'medication'

    def test_inventory_category_code_unique(self):
        """Category code must be unique."""
        from apps.inventory.models import InventoryCategory

        InventoryCategory.objects.create(code='general', name='General')
        with pytest.raises(IntegrityError):
            InventoryCategory.objects.create(code='general', name='Another General')

    def test_inventory_category_str(self):
        """String representation is the name."""
        from apps.inventory.models import InventoryCategory

        cat = InventoryCategory.objects.create(code='food', name='Pet Food')
        assert str(cat) == 'Pet Food'

    def test_default_categories_exist(self):
        """After migration, default categories should exist."""
        from apps.inventory.models import InventoryCategory
        from django.core.management import call_command

        call_command('populate_inventory_categories')

        assert InventoryCategory.objects.filter(code='medication').exists()
        assert InventoryCategory.objects.filter(code='food').exists()
        assert InventoryCategory.objects.filter(code='accessory').exists()
        assert InventoryCategory.objects.filter(code='supply').exists()


@pytest.mark.django_db
class TestVetProcedureModel:
    """Test VetProcedure model for veterinary services."""

    def test_vet_procedure_creation(self):
        """Can create a veterinary procedure."""
        from apps.practice.models import VetProcedure, ProcedureCategory
        from apps.billing.models import SATProductCode, SATUnitCode
        from django.core.management import call_command

        # Need SAT codes first
        call_command('populate_sat_codes')

        cat = ProcedureCategory.objects.create(
            code='consultation',
            name='Consultation',
        )

        proc = VetProcedure.objects.create(
            code='CONSULT-GEN',
            name='Consulta General',
            name_es='Consulta General',
            category=cat,
            base_price=Decimal('500.00'),
            duration_minutes=30,
            sat_product_code=SATProductCode.objects.get(code='85121800'),
            sat_unit_code=SATUnitCode.objects.get(code='E48'),
        )
        assert proc.pk is not None
        assert proc.code == 'CONSULT-GEN'

    def test_vet_procedure_code_unique(self):
        """Procedure code must be unique."""
        from apps.practice.models import VetProcedure, ProcedureCategory

        cat = ProcedureCategory.objects.create(code='test', name='Test')
        VetProcedure.objects.create(code='TEST-001', name='Test 1', category=cat)
        with pytest.raises(IntegrityError):
            VetProcedure.objects.create(code='TEST-001', name='Test 2', category=cat)

    def test_vet_procedure_str(self):
        """String representation is the name."""
        from apps.practice.models import VetProcedure, ProcedureCategory

        cat = ProcedureCategory.objects.create(code='test2', name='Test2')
        proc = VetProcedure.objects.create(code='TEST-002', name='Vaccination', category=cat)
        assert str(proc) == 'Vaccination'

    def test_procedure_category_creation(self):
        """Can create a procedure category."""
        from apps.practice.models import ProcedureCategory

        cat = ProcedureCategory.objects.create(
            code='surgery',
            name='Surgery',
            description='Surgical procedures',
        )
        assert cat.pk is not None
        assert str(cat) == 'Surgery'


@pytest.mark.django_db
class TestTagModel:
    """Test Tag model for flexible labeling."""

    def test_tag_creation(self):
        """Can create a tag."""
        from apps.core.models import Tag

        tag = Tag.objects.create(
            name='Bestseller',
            slug='bestseller',
            color='#10B981',
        )
        assert tag.pk is not None
        assert tag.slug == 'bestseller'

    def test_tag_slug_unique(self):
        """Tag slug must be unique."""
        from apps.core.models import Tag

        Tag.objects.create(name='Sale', slug='sale')
        with pytest.raises(IntegrityError):
            Tag.objects.create(name='On Sale', slug='sale')

    def test_tag_str(self):
        """String representation is the name."""
        from apps.core.models import Tag

        tag = Tag.objects.create(name='New Arrival', slug='new-arrival')
        assert str(tag) == 'New Arrival'
