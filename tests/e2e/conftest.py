"""E2E test fixtures for Pet-Friendly Vet application.

Provides fixtures for testing full application flows through
actual interfaces (views, APIs) rather than direct DB manipulation.
"""
import pytest
from decimal import Decimal
from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.test import Client
from django.utils import timezone
from rest_framework.test import APIClient

User = get_user_model()


# =============================================================================
# USER FIXTURES
# =============================================================================

@pytest.fixture
def owner_user(db):
    """Create a pet owner user."""
    email = 'owner@test.petfriendlyvet.com'
    user = User.objects.create_user(
        username=email,  # Username must match email for login
        email=email,
        password='owner123',
        first_name='Juan',
        last_name='Pérez',
        role='owner',
        phone_number='555-1234',
    )
    return user


@pytest.fixture
def staff_user(db):
    """Create a staff user."""
    email = 'staff@test.petfriendlyvet.com'
    user = User.objects.create_user(
        username=email,  # Username must match email for login
        email=email,
        password='staff123',
        first_name='María',
        last_name='López',
        role='staff',
        is_staff=True,
        phone_number='555-5678',
    )
    return user


@pytest.fixture
def vet_user(db):
    """Create a veterinarian user."""
    email = 'vet@test.petfriendlyvet.com'
    user = User.objects.create_user(
        username=email,  # Username must match email for login
        email=email,
        password='vet123',
        first_name='Dr. Carlos',
        last_name='Rodríguez',
        role='vet',
        is_staff=True,
        phone_number='555-9012',
    )
    return user


@pytest.fixture
def driver_user(db):
    """Create a delivery driver user."""
    email = 'driver@test.petfriendlyvet.com'
    user = User.objects.create_user(
        username=email,  # Username must match email for login
        email=email,
        password='driver123',
        first_name='Pedro',
        last_name='García',
        role='staff',
        phone_number='555-3456',
    )
    return user


# =============================================================================
# CLIENT FIXTURES
# =============================================================================

@pytest.fixture
def api_client():
    """Return a DRF API client."""
    return APIClient()


@pytest.fixture
def owner_client(api_client, owner_user):
    """Return an API client authenticated as owner."""
    api_client.force_authenticate(user=owner_user)
    return api_client


@pytest.fixture
def staff_client(api_client, staff_user):
    """Return an API client authenticated as staff."""
    api_client.force_authenticate(user=staff_user)
    return api_client


@pytest.fixture
def vet_client(api_client, vet_user):
    """Return an API client authenticated as vet."""
    api_client.force_authenticate(user=vet_user)
    return api_client


@pytest.fixture
def driver_client(api_client, driver_user):
    """Return an API client authenticated as driver."""
    api_client.force_authenticate(user=driver_user)
    return api_client


@pytest.fixture
def owner_web_client(client, owner_user):
    """Return a Django test client authenticated as owner."""
    client.force_login(owner_user)
    return client


@pytest.fixture
def staff_web_client(client, staff_user):
    """Return a Django test client authenticated as staff."""
    client.force_login(staff_user)
    return client


# =============================================================================
# STORE FIXTURES
# =============================================================================

@pytest.fixture
def category(db):
    """Create a product category."""
    from apps.store.models import Category
    return Category.objects.create(
        name='Alimentos',
        name_es='Alimentos',
        name_en='Food',
        slug='alimentos',
        description='Alimentos para mascotas',
        description_es='Alimentos para mascotas',
        description_en='Pet food',
        is_active=True,
    )


@pytest.fixture
def product(db, category):
    """Create a product."""
    from apps.store.models import Product
    return Product.objects.create(
        name='Royal Canin Adulto 15kg',
        name_es='Royal Canin Adulto 15kg',
        name_en='Royal Canin Adult 15kg',
        slug='royal-canin-adulto-15kg',
        category=category,
        price=Decimal('1850.00'),
        description='Alimento premium para perros adultos',
        description_es='Alimento premium para perros adultos',
        description_en='Premium food for adult dogs',
        stock_quantity=50,
        sku='SKU-RC-001',
        is_active=True,
    )


@pytest.fixture
def products(db, category):
    """Create multiple products."""
    from apps.store.models import Product
    products_data = [
        ('Royal Canin Adulto 15kg', Decimal('1850.00'), 'SKU-RC-001'),
        ('Nexgard 10-25kg', Decimal('450.00'), 'SKU-NX-001'),
        ('Collar Ajustable', Decimal('180.00'), 'SKU-CA-001'),
    ]
    products = []
    for name, price, sku in products_data:
        products.append(Product.objects.create(
            name=name,
            name_es=name,
            name_en=name,
            slug=name.lower().replace(' ', '-'),
            category=category,
            price=price,
            description=f'Descripción de {name}',
            description_es=f'Descripción de {name}',
            description_en=f'Description of {name}',
            stock_quantity=50,
            sku=sku,
            is_active=True,
        ))
    return products


@pytest.fixture
def cart_with_items(db, owner_user, products):
    """Create a cart with items for the owner."""
    from apps.store.models import Cart, CartItem
    cart = Cart.objects.create(user=owner_user)
    for product in products[:2]:  # Add first 2 products
        CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=1,
        )
    return cart


# =============================================================================
# PET FIXTURES
# =============================================================================

@pytest.fixture
def pet(db, owner_user):
    """Create a pet for the owner."""
    from apps.pets.models import Pet
    return Pet.objects.create(
        owner=owner_user,
        name='Max',
        species='dog',
        breed='Labrador Retriever',
        gender='male',
        date_of_birth=date.today() - timedelta(days=730),  # 2 years old
        weight_kg=Decimal('28.5'),
        is_neutered=True,
    )


# =============================================================================
# SERVICE/APPOINTMENT FIXTURES
# =============================================================================

@pytest.fixture
def service_type(db):
    """Create a service type."""
    from apps.appointments.models import ServiceType
    return ServiceType.objects.create(
        name='Consulta General',
        description='Consulta veterinaria estándar',
        duration_minutes=30,
        price=Decimal('500.00'),
        category='clinic',
        is_active=True,
    )


@pytest.fixture
def billing_service(db):
    """Create a billing service."""
    from apps.services.models import Service
    return Service.objects.create(
        name='General Consultation',
        name_es='Consulta General',
        description='Standard veterinary consultation',
        category='consultation',
        base_price=Decimal('500.00'),
        duration_minutes=30,
        clave_producto_sat='85121800',
        clave_unidad_sat='E48',
        is_active=True,
    )


@pytest.fixture
def scheduled_appointment(db, owner_user, pet, vet_user, service_type):
    """Create a scheduled appointment."""
    from apps.appointments.models import Appointment
    appointment_time = timezone.now() + timedelta(days=1)
    return Appointment.objects.create(
        owner=owner_user,
        pet=pet,
        veterinarian=vet_user,
        service=service_type,
        scheduled_start=appointment_time,
        scheduled_end=appointment_time + timedelta(minutes=30),
        status='scheduled',
        notes='Consulta general programada',
    )


# =============================================================================
# DELIVERY FIXTURES
# =============================================================================

@pytest.fixture
def delivery_zone(db):
    """Create a delivery zone."""
    from apps.delivery.models import DeliveryZone
    return DeliveryZone.objects.create(
        code='CDMX-ROMA',
        name='Roma/Condesa',
        delivery_fee=Decimal('45.00'),
        estimated_time_minutes=25,
        is_active=True,
    )


@pytest.fixture
def delivery_slot(db, delivery_zone):
    """Create a delivery slot."""
    from apps.delivery.models import DeliverySlot
    return DeliverySlot.objects.create(
        zone=delivery_zone,
        date=date.today() + timedelta(days=1),
        start_time=time(9, 0),
        end_time=time(12, 0),
        capacity=10,
        booked_count=0,
        is_active=True,
    )


@pytest.fixture
def delivery_driver(db, driver_user, delivery_zone):
    """Create a delivery driver."""
    from apps.delivery.models import DeliveryDriver
    driver = DeliveryDriver.objects.create(
        user=driver_user,
        driver_type='employee',
        phone='555-3456',
        vehicle_type='motorcycle',
        license_plate='ABC-123',
        max_deliveries_per_day=15,
        is_active=True,
        is_available=True,
    )
    driver.zones.add(delivery_zone)
    return driver


# =============================================================================
# ORDER FIXTURES
# =============================================================================

@pytest.fixture
def order(db, owner_user, products):
    """Create an order."""
    from apps.store.models import Order, OrderItem

    subtotal = sum(p.price for p in products[:2])
    shipping_cost = Decimal('50.00')
    tax = subtotal * Decimal('0.16')
    total = subtotal + shipping_cost + tax

    order = Order.objects.create(
        user=owner_user,
        order_number=Order.generate_order_number(),
        status='pending',
        fulfillment_method='delivery',
        payment_method='card',
        shipping_address='Calle Roma 123, Col. Roma, CDMX',
        shipping_phone='555-1234',
        subtotal=subtotal,
        shipping_cost=shipping_cost,
        tax=tax,
        total=total,
    )

    for product in products[:2]:
        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            product_sku=product.sku,
            price=product.price,
            quantity=1,
        )

    return order


@pytest.fixture
def paid_order(order):
    """Create a paid order."""
    order.status = 'paid'
    order.paid_at = timezone.now()
    order.save()
    return order


# =============================================================================
# CRM FIXTURES
# =============================================================================

@pytest.fixture
def owner_profile(db, owner_user):
    """Create an owner profile."""
    from apps.crm.models import OwnerProfile
    return OwnerProfile.objects.create(
        user=owner_user,
        preferred_contact_method='whatsapp',
        referral_source='Instagram',
        total_visits=0,
        total_spent=Decimal('0'),
    )


@pytest.fixture
def customer_tag(db):
    """Create a customer tag."""
    from apps.crm.models import CustomerTag
    return CustomerTag.objects.create(
        name='VIP',
        color='#FFD700',
    )
