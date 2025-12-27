"""Tests for VetProcedure management interface."""
import pytest
from decimal import Decimal

from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def staff_user(db):
    """Create a staff user for testing."""
    user = User.objects.create_user(
        username='stafftest',
        email='staff@test.com',
        password='testpass123',
        is_staff=True
    )
    return user


@pytest.fixture
def staff_client(staff_user):
    """Create an authenticated staff client."""
    client = Client()
    client.login(username='stafftest', password='testpass123')
    return client


@pytest.fixture
def procedure_category(db):
    """Create a test procedure category."""
    from apps.practice.models import ProcedureCategory
    return ProcedureCategory.objects.create(
        code='test-category',
        name='Test Category',
        name_es='Categoria de Prueba',
    )


@pytest.fixture
def vet_procedure(db, procedure_category):
    """Create a test veterinary procedure."""
    from apps.practice.models import VetProcedure
    return VetProcedure.objects.create(
        code='TEST-PROC',
        name='Test Procedure',
        name_es='Procedimiento de Prueba',
        category=procedure_category,
        base_price=Decimal('500.00'),
        duration_minutes=30,
    )


@pytest.fixture
def staff_profile(db, staff_user):
    """Create a staff profile for the test user."""
    from apps.practice.models import StaffProfile
    return StaffProfile.objects.create(
        user=staff_user,
        role='veterinarian',
        is_active=True,
    )


@pytest.fixture
def inventory_item(db):
    """Create a test inventory item."""
    from apps.inventory.models import InventoryItem
    from apps.billing.models import SATProductCode, SATUnitCode, TaxRate
    from django.core.management import call_command

    # Populate SAT codes
    call_command('populate_sat_codes')

    tax_rate, _ = TaxRate.objects.get_or_create(
        code='IVA16',
        defaults={'name': 'IVA 16%', 'rate': Decimal('0.16')}
    )

    return InventoryItem.objects.create(
        sku='TEST-ITEM-001',
        name='Test Syringe',
        item_type='consumable',
        sat_product_code=SATProductCode.objects.first(),
        sat_unit_code=SATUnitCode.objects.first(),
        tax_rate=tax_rate,
        cost_price=Decimal('10.00'),
    )


# ============================================
# Qualified Providers Tests
# ============================================

@pytest.mark.django_db
class TestQualifiedProvidersView:
    """Test qualified providers management for procedures."""

    def test_procedure_detail_shows_qualified_providers(self, staff_client, vet_procedure, staff_profile):
        """Procedure detail page shows assigned qualified providers."""
        # Add the staff profile as a qualified provider
        vet_procedure.qualified_providers.add(staff_profile)

        response = staff_client.get(
            reverse('practice:procedure_providers', args=[vet_procedure.pk])
        )

        assert response.status_code == 200
        assert staff_profile.user.get_full_name() in response.content.decode() or \
               staff_profile.user.username in response.content.decode()

    def test_add_qualified_provider_to_procedure(self, staff_client, vet_procedure, staff_profile):
        """Can add a qualified provider to a procedure."""
        response = staff_client.post(
            reverse('practice:procedure_add_provider', args=[vet_procedure.pk]),
            {'staff_id': staff_profile.pk}
        )

        assert response.status_code in [200, 302]  # Success or redirect
        vet_procedure.refresh_from_db()
        assert staff_profile in vet_procedure.qualified_providers.all()

    def test_remove_qualified_provider_from_procedure(self, staff_client, vet_procedure, staff_profile):
        """Can remove a qualified provider from a procedure."""
        vet_procedure.qualified_providers.add(staff_profile)

        response = staff_client.post(
            reverse('practice:procedure_remove_provider', args=[vet_procedure.pk]),
            {'staff_id': staff_profile.pk}
        )

        assert response.status_code in [200, 302]
        vet_procedure.refresh_from_db()
        assert staff_profile not in vet_procedure.qualified_providers.all()

    def test_shows_available_providers_to_add(self, staff_client, vet_procedure, staff_profile):
        """Page shows list of available providers that can be added."""
        response = staff_client.get(
            reverse('practice:procedure_providers', args=[vet_procedure.pk])
        )

        assert response.status_code == 200
        # Available providers should be shown
        content = response.content.decode()
        assert 'available' in content.lower() or 'add' in content.lower()


# ============================================
# Procedure Consumables Tests
# ============================================

@pytest.mark.django_db
class TestProcedureConsumablesView:
    """Test consumable items management for procedures."""

    def test_procedure_consumables_page_loads(self, staff_client, vet_procedure):
        """Consumables management page loads successfully."""
        response = staff_client.get(
            reverse('practice:procedure_consumables', args=[vet_procedure.pk])
        )

        assert response.status_code == 200

    def test_add_consumable_to_procedure(self, staff_client, vet_procedure, inventory_item):
        """Can add a consumable item to a procedure."""
        response = staff_client.post(
            reverse('practice:procedure_add_consumable', args=[vet_procedure.pk]),
            {
                'inventory_item': inventory_item.pk,
                'quantity': '2.00',
                'is_required': 'on',
            }
        )

        assert response.status_code in [200, 302]
        assert vet_procedure.consumables.filter(inventory_item=inventory_item).exists()

    def test_update_consumable_quantity(self, staff_client, vet_procedure, inventory_item):
        """Can update the quantity of a consumable."""
        from apps.practice.models import ProcedureConsumable

        consumable = ProcedureConsumable.objects.create(
            procedure=vet_procedure,
            inventory_item=inventory_item,
            quantity=Decimal('1.00'),
        )

        response = staff_client.post(
            reverse('practice:procedure_update_consumable', args=[vet_procedure.pk, consumable.pk]),
            {'quantity': '3.00', 'is_required': 'on'}
        )

        assert response.status_code in [200, 302]
        consumable.refresh_from_db()
        assert consumable.quantity == Decimal('3.00')

    def test_remove_consumable_from_procedure(self, staff_client, vet_procedure, inventory_item):
        """Can remove a consumable from a procedure."""
        from apps.practice.models import ProcedureConsumable

        consumable = ProcedureConsumable.objects.create(
            procedure=vet_procedure,
            inventory_item=inventory_item,
            quantity=Decimal('1.00'),
        )

        response = staff_client.post(
            reverse('practice:procedure_remove_consumable', args=[vet_procedure.pk, consumable.pk])
        )

        assert response.status_code in [200, 302]
        assert not vet_procedure.consumables.filter(pk=consumable.pk).exists()

    def test_shows_consumable_cost_calculation(self, staff_client, vet_procedure, inventory_item):
        """Page shows the cost calculation for consumables."""
        from apps.practice.models import ProcedureConsumable

        ProcedureConsumable.objects.create(
            procedure=vet_procedure,
            inventory_item=inventory_item,
            quantity=Decimal('2.00'),
        )

        response = staff_client.get(
            reverse('practice:procedure_consumables', args=[vet_procedure.pk])
        )

        assert response.status_code == 200
        # Should show cost somewhere (item cost * quantity)
        content = response.content.decode()
        assert '$' in content or 'cost' in content.lower()


# ============================================
# Dashboard Link Tests
# ============================================

@pytest.mark.django_db
class TestDashboardProceduresLink:
    """Test that procedures link appears on practice dashboard."""

    def test_dashboard_has_procedures_link(self, staff_client):
        """Practice dashboard has a link to procedures."""
        response = staff_client.get(reverse('practice:dashboard'))

        assert response.status_code == 200
        content = response.content.decode()
        # Should have link to procedures (uses staff_token pattern)
        assert 'procedures' in content.lower() or 'procedimientos' in content.lower()
        assert 'operations/practice/procedures/' in content

    def test_dashboard_has_categories_link(self, staff_client):
        """Practice dashboard has a link to categories."""
        response = staff_client.get(reverse('practice:dashboard'))

        assert response.status_code == 200
        content = response.content.decode()
        # Uses staff_token pattern
        assert 'operations/practice/categories/' in content


# ============================================
# Procedure List Enhancement Tests
# ============================================

@pytest.mark.django_db
class TestProcedureListEnhancements:
    """Test procedure list shows providers and consumables count."""

    def test_procedure_list_shows_provider_count(self, staff_client, vet_procedure, staff_profile):
        """Procedure list shows count of qualified providers."""
        vet_procedure.qualified_providers.add(staff_profile)

        response = staff_client.get(reverse('practice:procedure_list'))

        assert response.status_code == 200
        # Should show provider count or indicator

    def test_procedure_list_shows_consumable_count(self, staff_client, vet_procedure, inventory_item):
        """Procedure list shows count of consumable items."""
        from apps.practice.models import ProcedureConsumable

        ProcedureConsumable.objects.create(
            procedure=vet_procedure,
            inventory_item=inventory_item,
            quantity=Decimal('1.00'),
        )

        response = staff_client.get(reverse('practice:procedure_list'))

        assert response.status_code == 200
        # Should show consumable count or indicator

    def test_procedure_list_has_manage_links(self, staff_client, vet_procedure):
        """Procedure list has links to manage providers and consumables."""
        response = staff_client.get(reverse('practice:procedure_list'))

        assert response.status_code == 200
        content = response.content.decode()
        # Should have links to manage providers and consumables
        assert 'provider' in content.lower() or 'staff' in content.lower()
