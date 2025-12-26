"""
Tests for navigation context processor.
TDD tests for unified staff and customer navigation.
"""

import pytest
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse

from apps.accounts.models import User
from apps.core.context_processors import navigation


@pytest.fixture
def rf():
    """Request factory."""
    return RequestFactory()


@pytest.fixture
def staff_user(db):
    """Staff user fixture."""
    user = User.objects.create_user(
        username='staffuser',
        email='staff@example.com',
        password='testpass123',
        is_staff=True,
    )
    return user


@pytest.fixture
def customer_user(db):
    """Regular customer user fixture."""
    user = User.objects.create_user(
        username='customeruser',
        email='customer@example.com',
        password='testpass123',
        is_staff=False,
    )
    return user


@pytest.fixture
def anonymous_user():
    """Anonymous user fixture."""
    return AnonymousUser()


class TestNavigationContextProcessor:
    """Tests for the navigation context processor."""

    def test_returns_empty_nav_for_anonymous_user(self, rf, anonymous_user):
        """Anonymous users get no navigation."""
        request = rf.get('/')
        request.user = anonymous_user

        context = navigation(request)

        assert context['staff_nav'] == []
        assert context['portal_nav'] == []
        assert context['active_nav'] == ''

    def test_returns_staff_nav_for_staff_user(self, rf, staff_user):
        """Staff users get staff navigation."""
        request = rf.get('/')
        request.user = staff_user

        context = navigation(request)

        assert len(context['staff_nav']) > 0
        assert context['portal_nav'] == []

    def test_returns_portal_nav_for_customer(self, rf, customer_user):
        """Customer users get portal navigation."""
        request = rf.get('/')
        request.user = customer_user

        context = navigation(request)

        assert context['staff_nav'] == []
        assert len(context['portal_nav']) > 0


class TestStaffNavigation:
    """Tests for staff navigation structure."""

    def test_staff_nav_has_correct_modules(self, rf, staff_user):
        """Staff nav includes all 10 modules."""
        request = rf.get('/')
        request.user = staff_user

        context = navigation(request)
        nav = context['staff_nav']

        nav_ids = [item['id'] for item in nav]

        assert 'practice' in nav_ids
        assert 'inventory' in nav_ids
        assert 'referrals' in nav_ids
        assert 'delivery' in nav_ids
        assert 'crm' in nav_ids
        assert 'marketing' in nav_ids
        assert 'accounting' in nav_ids
        assert 'reports' in nav_ids
        assert 'audit' in nav_ids
        assert 'ai_chat' in nav_ids

    def test_staff_nav_item_has_required_fields(self, rf, staff_user):
        """Each nav item has id, icon, label, and url."""
        request = rf.get('/')
        request.user = staff_user

        context = navigation(request)
        nav = context['staff_nav']

        for item in nav:
            assert 'id' in item
            assert 'icon' in item
            assert 'label' in item
            assert 'url' in item

    def test_staff_nav_has_sections(self, rf, staff_user):
        """Staff nav items are grouped by section."""
        request = rf.get('/')
        request.user = staff_user

        context = navigation(request)
        nav = context['staff_nav']

        sections = set()
        for item in nav:
            if 'section' in item:
                sections.add(item['section'])

        assert 'Operations' in sections
        assert 'Customers' in sections
        assert 'Finance' in sections
        assert 'Admin' in sections


class TestPortalNavigation:
    """Tests for customer portal navigation structure."""

    def test_portal_nav_has_correct_sections(self, rf, customer_user):
        """Portal nav includes all customer sections."""
        request = rf.get('/')
        request.user = customer_user

        context = navigation(request)
        nav = context['portal_nav']

        nav_ids = [item['id'] for item in nav]

        assert 'pets' in nav_ids
        assert 'appointments' in nav_ids
        assert 'pharmacy' in nav_ids
        assert 'orders' in nav_ids
        assert 'billing' in nav_ids
        assert 'loyalty' in nav_ids
        assert 'emergency' in nav_ids
        assert 'profile' in nav_ids

    def test_portal_nav_item_has_required_fields(self, rf, customer_user):
        """Each portal nav item has id, icon, label, and url."""
        request = rf.get('/')
        request.user = customer_user

        context = navigation(request)
        nav = context['portal_nav']

        for item in nav:
            assert 'id' in item
            assert 'icon' in item
            assert 'label' in item
            assert 'url' in item

    def test_portal_nav_has_sections(self, rf, customer_user):
        """Portal nav items are grouped by section."""
        request = rf.get('/')
        request.user = customer_user

        context = navigation(request)
        nav = context['portal_nav']

        sections = set()
        for item in nav:
            if 'section' in item:
                sections.add(item['section'])

        assert 'My Account' in sections
        assert 'Shopping' in sections
        assert 'Help' in sections


class TestActiveNavDetection:
    """Tests for detecting the active navigation item."""

    def test_detects_practice_as_active(self, rf, staff_user):
        """Detects practice as active from URL."""
        request = rf.get('/practice/')
        request.user = staff_user
        request.resolver_match = type('obj', (object,), {'namespace': 'practice'})()

        context = navigation(request)

        assert context['active_nav'] == 'practice'

    def test_detects_inventory_as_active(self, rf, staff_user):
        """Detects inventory as active from URL."""
        request = rf.get('/inventory/')
        request.user = staff_user
        request.resolver_match = type('obj', (object,), {'namespace': 'inventory'})()

        context = navigation(request)

        assert context['active_nav'] == 'inventory'

    def test_detects_pets_as_active_for_portal(self, rf, customer_user):
        """Detects pets as active from URL for customers."""
        request = rf.get('/pets/')
        request.user = customer_user
        request.resolver_match = type('obj', (object,), {'namespace': 'pets'})()

        context = navigation(request)

        assert context['active_nav'] == 'pets'

    def test_no_active_nav_without_resolver_match(self, rf, staff_user):
        """Returns empty active_nav when no resolver_match."""
        request = rf.get('/')
        request.user = staff_user
        request.resolver_match = None

        context = navigation(request)

        assert context['active_nav'] == ''

    def test_handles_nested_namespace(self, rf, staff_user):
        """Handles nested namespaces like delivery:delivery_admin."""
        request = rf.get('/delivery/admin/')
        request.user = staff_user
        request.resolver_match = type('obj', (object,), {'namespace': 'delivery:delivery_admin'})()

        context = navigation(request)

        assert context['active_nav'] == 'delivery'

    def test_maps_marketing_namespace(self, rf, staff_user):
        """Maps marketing namespace to marketing nav item."""
        request = rf.get('/marketing/')
        request.user = staff_user
        request.resolver_match = type('obj', (object,), {'namespace': 'marketing'})()

        context = navigation(request)

        assert context['active_nav'] == 'marketing'

    def test_maps_ai_assistant_namespace(self, rf, staff_user):
        """Maps ai_assistant namespace to ai_chat nav item."""
        request = rf.get('/chat/admin/')
        request.user = staff_user
        request.resolver_match = type('obj', (object,), {'namespace': 'ai_assistant'})()

        context = navigation(request)

        assert context['active_nav'] == 'ai_chat'

    def test_handles_unmapped_nested_namespace(self, rf, customer_user):
        """Handles nested namespaces not in the mapping."""
        request = rf.get('/store/orders/')
        request.user = customer_user
        request.resolver_match = type('obj', (object,), {'namespace': 'store:orders'})()

        context = navigation(request)

        assert context['active_nav'] == 'store'


class TestStaffOnlyPermissions:
    """Tests for staff-only navigation access."""

    def test_superuser_gets_staff_nav(self, rf, db):
        """Superusers get staff navigation."""
        superuser = User.objects.create_superuser(
            username='adminuser',
            email='admin@example.com',
            password='testpass123',
        )
        request = rf.get('/')
        request.user = superuser

        context = navigation(request)

        assert len(context['staff_nav']) > 0

    def test_regular_user_no_staff_nav(self, rf, customer_user):
        """Regular users don't get staff nav."""
        request = rf.get('/')
        request.user = customer_user

        context = navigation(request)

        assert context['staff_nav'] == []
