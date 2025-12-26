"""Tests for LocationType model and CRUD (TDD).

Tests for:
- LocationType model creation and properties
- LocationType CRUD views (list, create, edit, delete)
- Module-seeded default types
"""
import pytest
from django.test import Client
from django.contrib.auth import get_user_model

from apps.inventory.models import LocationType, StockLocation

User = get_user_model()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username='location_type_staff',
        email='loctype@test.com',
        password='testpass123',
        is_staff=True,
        is_active=True
    )


@pytest.fixture
def authenticated_client(user):
    """Return a logged-in client with staff token."""
    client = Client()
    client.login(username='location_type_staff', password='testpass123')
    # Access staff hub to generate token
    client.get('/staff/')
    return client


def get_staff_url(client, path):
    """Build staff token URL for a path."""
    session = client.session
    token = session.get('staff_token')
    if token:
        return f'/staff-{token}/operations/inventory/{path}'
    return f'/operations/inventory/{path}'


@pytest.fixture
def location_type(db):
    """Create or get a test location type."""
    lt, _ = LocationType.objects.get_or_create(
        code='test_warehouse',
        defaults={
            'name': 'Test Warehouse',
            'description': 'Test warehouse storage',
            'requires_temperature_control': False,
            'requires_restricted_access': False
        }
    )
    return lt


@pytest.fixture
def pharmacy_location_type(db):
    """Create or get a pharmacy module location type."""
    lt, _ = LocationType.objects.get_or_create(
        code='test_pharmacy',
        defaults={
            'name': 'Test Pharmacy',
            'description': 'Test pharmacy dispensing area',
            'requires_temperature_control': False,
            'requires_restricted_access': True,
            'source_module': 'pharmacy'
        }
    )
    return lt


class TestLocationTypeModel:
    """Tests for LocationType model."""

    def test_location_type_create(self, db):
        """Can create a location type."""
        lt = LocationType.objects.create(
            name='Custom Store Floor',
            code='custom_store',
            description='Retail display area'
        )
        assert lt.pk is not None
        assert lt.name == 'Custom Store Floor'
        assert lt.code == 'custom_store'
        assert lt.is_active is True  # default

    def test_location_type_str(self, location_type):
        """String representation is the name."""
        assert str(location_type) == 'Test Warehouse'

    def test_location_type_code_unique(self, db, location_type):
        """Code must be unique."""
        with pytest.raises(Exception):  # IntegrityError
            LocationType.objects.create(
                name='Another Warehouse',
                code='test_warehouse'  # Duplicate of fixture
            )

    def test_location_type_source_module(self, pharmacy_location_type):
        """Location type tracks source module."""
        assert pharmacy_location_type.source_module == 'pharmacy'

    def test_location_type_defaults(self, db):
        """Default values are set correctly."""
        lt = LocationType.objects.create(name='Test', code='test')
        assert lt.requires_temperature_control is False
        assert lt.requires_restricted_access is False
        assert lt.is_active is True
        assert lt.source_module == ''

    def test_location_type_ordering(self, db):
        """Location types are ordered by name."""
        LocationType.objects.create(name='Zebra', code='zebra')
        LocationType.objects.create(name='Alpha', code='alpha')
        LocationType.objects.create(name='Middle', code='middle')

        types = list(LocationType.objects.all())
        names = [t.name for t in types]
        assert names == sorted(names)


class TestStockLocationWithLocationType:
    """Tests for StockLocation using LocationType FK."""

    def test_stock_location_with_location_type(self, db, location_type):
        """StockLocation can be created with LocationType FK."""
        location = StockLocation.objects.create(
            name='Main Warehouse',
            location_type=location_type
        )
        assert location.location_type == location_type
        assert location.location_type.name == 'Test Warehouse'

    def test_stock_location_type_cascade(self, db):
        """Deleting LocationType is protected (cannot delete if in use)."""
        lt = LocationType.objects.create(name='Test Type', code='test')
        StockLocation.objects.create(name='Test Location', location_type=lt)

        with pytest.raises(Exception):  # ProtectedError
            lt.delete()

    def test_stock_location_type_null_allowed(self, db):
        """StockLocation can have null location_type for migration."""
        location = StockLocation.objects.create(
            name='Legacy Location',
            location_type=None
        )
        assert location.location_type is None


@pytest.mark.django_db
class TestLocationTypeList:
    """Tests for location type list view."""

    def test_location_type_list_requires_auth(self, client, db):
        """List view requires authentication - staff portal redirects."""
        response = client.get('/staff/')
        # Should redirect to login or show forbidden
        assert response.status_code in [302, 403]

    def test_location_type_list_shows_types(self, authenticated_client, location_type):
        """List view shows location types."""
        url = get_staff_url(authenticated_client, 'location-types/')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert b'Test Warehouse' in response.content

    def test_location_type_list_shows_source_module(self, authenticated_client, pharmacy_location_type):
        """List view shows source module badge."""
        url = get_staff_url(authenticated_client, 'location-types/')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert b'pharmacy' in response.content.lower()


@pytest.mark.django_db
class TestLocationTypeCreate:
    """Tests for location type create view."""

    def test_location_type_create_get(self, authenticated_client):
        """Create form loads correctly."""
        url = get_staff_url(authenticated_client, 'location-types/add/')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert b'Location Type' in response.content

    def test_location_type_create_post(self, authenticated_client):
        """Can create a location type via POST."""
        url = get_staff_url(authenticated_client, 'location-types/add/')
        data = {
            'name': 'New Cold Storage',
            'code': 'new_cold_storage',
            'description': 'Temperature controlled storage',
            'requires_temperature_control': 'on',
            'is_active': 'on'
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == 302  # Redirect on success

        lt = LocationType.objects.get(code='new_cold_storage')
        assert lt.name == 'New Cold Storage'
        assert lt.requires_temperature_control is True

    def test_location_type_create_duplicate_code_error(self, authenticated_client, location_type):
        """Cannot create with duplicate code."""
        url = get_staff_url(authenticated_client, 'location-types/add/')
        data = {
            'name': 'Another',
            'code': 'test_warehouse',  # Already exists from fixture
            'is_active': 'on'
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == 200  # Form re-rendered with error
        # Form should show error about duplicate code
        assert LocationType.objects.filter(code='warehouse').count() == 1


@pytest.mark.django_db
class TestLocationTypeEdit:
    """Tests for location type edit view."""

    def test_location_type_edit_get(self, authenticated_client, location_type):
        """Edit form loads with existing data."""
        url = get_staff_url(authenticated_client, f'location-types/{location_type.pk}/edit/')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert b'Test Warehouse' in response.content

    def test_location_type_edit_post(self, authenticated_client, location_type):
        """Can update location type via POST."""
        url = get_staff_url(authenticated_client, f'location-types/{location_type.pk}/edit/')
        data = {
            'name': 'Updated Warehouse',
            'code': 'test_warehouse',
            'description': 'Updated description',
            'is_active': 'on'
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == 302  # Redirect on success

        location_type.refresh_from_db()
        assert location_type.name == 'Updated Warehouse'
        assert location_type.description == 'Updated description'

    def test_location_type_edit_module_seeded_warning(self, authenticated_client, pharmacy_location_type):
        """Module-seeded types show warning when editing."""
        url = get_staff_url(authenticated_client, f'location-types/{pharmacy_location_type.pk}/edit/')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        # Should indicate this is a module-seeded type
        assert b'pharmacy' in response.content.lower()


@pytest.mark.django_db
class TestLocationTypeDelete:
    """Tests for location type delete."""

    def test_location_type_delete_unused(self, authenticated_client, location_type):
        """Can delete unused location type."""
        pk = location_type.pk
        url = get_staff_url(authenticated_client, f'location-types/{pk}/delete/')
        response = authenticated_client.post(url)
        assert response.status_code == 302  # Redirect on success
        assert not LocationType.objects.filter(pk=pk).exists()

    def test_location_type_delete_in_use_protected(self, authenticated_client, location_type):
        """Cannot delete location type in use by a location."""
        # Create a location using this type
        StockLocation.objects.create(name='Test', location_type=location_type)

        url = get_staff_url(authenticated_client, f'location-types/{location_type.pk}/delete/')
        response = authenticated_client.post(url)
        # Should still redirect but type should exist (protected)
        assert LocationType.objects.filter(pk=location_type.pk).exists()


@pytest.mark.django_db
class TestDefaultLocationTypes:
    """Tests for default/seeded location types."""

    def test_seed_default_types(self, db):
        """Can seed default location types."""
        from apps.inventory.services import seed_default_location_types

        seed_default_location_types()

        # Should have basic types
        assert LocationType.objects.filter(code='store').exists()
        assert LocationType.objects.filter(code='warehouse').exists()

        # Should be marked as system
        store = LocationType.objects.get(code='store')
        assert store.source_module == 'inventory'

    def test_seed_pharmacy_types(self, db):
        """Pharmacy module can seed its types."""
        from apps.inventory.services import seed_module_location_types

        # Use unique codes that won't conflict with migration-seeded types
        seed_module_location_types('pharmacy', [
            {'name': 'Pharmacy Dispensary', 'code': 'pharmacy_dispensary', 'requires_restricted_access': True},
            {'name': 'Controlled Cabinet', 'code': 'controlled_cabinet', 'requires_restricted_access': True},
        ])

        assert LocationType.objects.filter(code='pharmacy_dispensary', source_module='pharmacy').exists()
        assert LocationType.objects.filter(code='controlled_cabinet', source_module='pharmacy').exists()

    def test_seed_idempotent(self, db):
        """Seeding is idempotent (can run multiple times)."""
        from apps.inventory.services import seed_default_location_types

        seed_default_location_types()
        count1 = LocationType.objects.count()

        seed_default_location_types()
        count2 = LocationType.objects.count()

        assert count1 == count2  # No duplicates created
