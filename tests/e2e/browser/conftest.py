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
    """Page with authenticated owner user session (alias for owner_page)."""
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
def owner_page(page, live_server, owner_user):
    """Page with authenticated pet owner session."""
    page.goto(f'{live_server.url}/accounts/login/')

    page.fill('input[name="username"]', owner_user.email)
    page.fill('input[name="password"]', 'owner123')
    page.click('button[type="submit"]')

    page.wait_for_load_state('networkidle')

    return page


@pytest.fixture
def staff_page(page, live_server, staff_user):
    """Page with authenticated staff user session."""
    page.goto(f'{live_server.url}/accounts/login/')

    page.fill('input[name="username"]', staff_user.email)
    page.fill('input[name="password"]', 'staff123')
    page.click('button[type="submit"]')

    page.wait_for_load_state('networkidle')

    return page


@pytest.fixture
def vet_page(page, live_server, vet_user):
    """Page with authenticated veterinarian session."""
    page.goto(f'{live_server.url}/accounts/login/')

    page.fill('input[name="username"]', vet_user.email)
    page.fill('input[name="password"]', 'vet123')
    page.click('button[type="submit"]')

    page.wait_for_load_state('networkidle')

    return page


@pytest.fixture
def admin_user(db):
    """Create a superuser for admin access."""
    email = 'admin@test.petfriendlyvet.com'
    user = User.objects.create_superuser(
        username=email,
        email=email,
        password='admin123',
        first_name='Admin',
        last_name='User',
    )
    return user


@pytest.fixture
def admin_page(page, live_server, admin_user):
    """Page with authenticated admin user session."""
    page.goto(f'{live_server.url}/accounts/login/')

    page.fill('input[name="username"]', admin_user.email)
    page.fill('input[name="password"]', 'admin123')
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


@pytest.fixture
def pet_with_vaccinations(db, owner_user):
    """Pet with vaccination records."""
    from datetime import date, timedelta
    from apps.pets.models import Pet, Vaccination

    pet = Pet.objects.create(
        owner=owner_user,
        name='Vacunado',
        species='dog',
        breed='Labrador',
        gender='male',
        date_of_birth=date.today() - timedelta(days=365),
    )

    Vaccination.objects.create(
        pet=pet,
        vaccine_name='Rabies',
        date_administered=date.today() - timedelta(days=30),
        next_due_date=date.today() + timedelta(days=335),
        batch_number='VAX-001',
    )

    return {'pet': pet}


@pytest.fixture
def pet_with_overdue_vaccination(db, owner_user):
    """Pet with overdue vaccination."""
    from datetime import date, timedelta
    from apps.pets.models import Pet, Vaccination

    pet = Pet.objects.create(
        owner=owner_user,
        name='NecesitaVacuna',
        species='dog',
        breed='Beagle',
        gender='female',
        date_of_birth=date.today() - timedelta(days=730),
    )

    Vaccination.objects.create(
        pet=pet,
        vaccine_name='Distemper',
        date_administered=date.today() - timedelta(days=400),
        next_due_date=date.today() - timedelta(days=35),  # Overdue
        batch_number='VAX-002',
    )

    return {'pet': pet}


@pytest.fixture
def pet_with_medical_records(db, owner_user, vet_user):
    """Pet with complete medical records."""
    from datetime import date, timedelta
    from decimal import Decimal
    from apps.pets.models import Pet, ClinicalNote, WeightRecord

    pet = Pet.objects.create(
        owner=owner_user,
        name='Documentado',
        species='cat',
        breed='Siamese',
        gender='female',
        date_of_birth=date.today() - timedelta(days=500),
        weight_kg=Decimal('4.5'),
    )

    ClinicalNote.objects.create(
        pet=pet,
        author=vet_user,
        note_type='observation',
        note='Healthy cat, good appetite.',
    )

    WeightRecord.objects.create(
        pet=pet,
        weight_kg=Decimal('4.5'),
        recorded_by=vet_user,
    )

    return {'pet': pet}


@pytest.fixture
def emergency_setup(db, vet_user, owner_user):
    """Emergency system setup."""
    from datetime import date, time, timedelta
    from apps.practice.models import StaffProfile
    from apps.emergency.models import OnCallSchedule, EmergencySymptom
    from apps.pets.models import Pet

    staff_profile, _ = StaffProfile.objects.get_or_create(
        user=vet_user,
        defaults={'role': 'veterinarian', 'can_prescribe': True}
    )

    on_call = OnCallSchedule.objects.create(
        staff=staff_profile,
        date=date.today(),
        start_time=time(0, 0),
        end_time=time(23, 59),
        contact_phone='555-EMERGENCY',
        is_active=True,
    )

    pet = Pet.objects.create(
        owner=owner_user,
        name='Emergencia',
        species='dog',
        breed='Poodle',
        gender='male',
        date_of_birth=date.today() - timedelta(days=365),
    )

    return {'on_call': on_call, 'pet': pet, 'staff': staff_profile}


@pytest.fixture
def loyalty_program_setup(db, owner_user):
    """Loyalty program setup."""
    from decimal import Decimal
    from apps.loyalty.models import LoyaltyProgram, LoyaltyTier, LoyaltyAccount

    program = LoyaltyProgram.objects.create(
        name='PetFriendly Rewards',
        description='Earn points with every purchase',
        points_per_currency=Decimal('1.0'),
        is_active=True,
    )

    tier = LoyaltyTier.objects.create(
        program=program,
        name='Bronze',
        min_points=0,
        discount_percent=Decimal('5.0'),
        points_multiplier=Decimal('1.0'),
        display_order=1,
    )

    account = LoyaltyAccount.objects.create(
        user=owner_user,
        program=program,
        tier=tier,
        points_balance=500,
        lifetime_points=500,
    )

    return {'program': program, 'tier': tier, 'account': account}


@pytest.fixture
def staff_schedule_setup(db, staff_user):
    """Staff scheduling setup."""
    from datetime import date, time
    from apps.practice.models import StaffProfile, Shift

    profile, _ = StaffProfile.objects.get_or_create(
        user=staff_user,
        defaults={'role': 'receptionist'}
    )

    shift = Shift.objects.create(
        staff=profile,
        date=date.today(),
        start_time=time(9, 0),
        end_time=time(17, 0),
    )

    return {'profile': profile, 'shift': shift}
