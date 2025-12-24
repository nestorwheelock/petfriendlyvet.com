"""Playwright browser test fixtures.

Provides fixtures for browser-based E2E testing with Django live server.

Note: We set DJANGO_ALLOW_ASYNC_UNSAFE=true to allow Django's synchronous
database operations within pytest-playwright's async context. This is safe
for testing but should not be used in production.

Note: Browser tests may conflict with async tests in the same run. For best
results, run browser tests separately: pytest -m browser
"""
import os
import pytest
from decimal import Decimal

# Allow Django to run synchronous DB operations in async context (for Playwright)
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")

from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture(scope='session')
def browser_context_args(browser_context_args):
    """Configure browser context for all tests."""
    return {
        **browser_context_args,
        'viewport': {'width': 1280, 'height': 720},
        'locale': 'es-MX',
        'timezone_id': 'America/Mexico_City',
    }


@pytest.fixture
def live_server_url(live_server):
    """Get the live server URL."""
    return live_server.url


@pytest.fixture
def authenticated_page(page, live_server, owner_user):
    """Page with authenticated owner user session."""
    # Login the user
    page.goto(f'{live_server.url}/accounts/login/')

    # Fill login form - use email since the form expects email format
    page.fill('input[name="username"]', owner_user.email)
    page.fill('input[name="password"]', 'owner123')
    page.click('button[type="submit"]')

    # Wait for redirect/authentication
    page.wait_for_load_state('networkidle')

    return page


@pytest.fixture
def staff_page(page, live_server, staff_user):
    """Page with authenticated staff user session."""
    page.goto(f'{live_server.url}/accounts/login/')

    # Use email since the form expects email format
    page.fill('input[name="username"]', staff_user.email)
    page.fill('input[name="password"]', 'staff123')
    page.click('button[type="submit"]')

    page.wait_for_load_state('networkidle')

    return page


@pytest.fixture
def driver_page(page, live_server, driver_user):
    """Page with authenticated driver user session."""
    page.goto(f'{live_server.url}/accounts/login/')

    # Use email since the form expects email format
    page.fill('input[name="username"]', driver_user.email)
    page.fill('input[name="password"]', 'driver123')
    page.click('button[type="submit"]')

    page.wait_for_load_state('networkidle')

    return page


@pytest.fixture
def mobile_page(page, live_server):
    """Page configured for mobile viewport."""
    page.set_viewport_size({'width': 375, 'height': 667})
    return page


@pytest.fixture
def store_with_products(db):
    """Set up store with products for browser tests."""
    from apps.store.models import Category, Product

    category = Category.objects.create(
        name='Test Category',
        name_es='Categoría de Prueba',
        name_en='Test Category',
        slug='test-category',
        is_active=True,
    )

    products = []
    for i in range(5):
        products.append(Product.objects.create(
            name=f'Test Product {i+1}',
            name_es=f'Producto de Prueba {i+1}',
            name_en=f'Test Product {i+1}',
            slug=f'test-product-{i+1}',
            category=category,
            price=Decimal(f'{(i+1) * 100}.00'),
            stock_quantity=50,
            sku=f'TEST-{i+1:03d}',
            is_active=True,
        ))

    return {'category': category, 'products': products}
