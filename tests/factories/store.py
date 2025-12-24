"""Factories for store app models."""
import factory
from factory.django import DjangoModelFactory
from faker import Faker
from decimal import Decimal

from apps.store.models import Product, Category, Cart, CartItem, Order, OrderItem
from .accounts import OwnerFactory

fake = Faker(['es_MX', 'en_US'])

PRODUCT_CATEGORIES = [
    ('Alimentos', ['Croquetas Premium', 'Croquetas Cachorro', 'Alimento Húmedo', 'Snacks', 'Dieta Especial']),
    ('Medicamentos', ['Antiparasitarios', 'Antibióticos', 'Antiinflamatorios', 'Vitaminas', 'Suplementos']),
    ('Accesorios', ['Collares', 'Correas', 'Platos', 'Camas', 'Juguetes', 'Transportadoras']),
    ('Higiene', ['Shampoo', 'Cepillos', 'Cortauñas', 'Limpiador de Oídos', 'Pañales']),
    ('Veterinaria', ['Vacunas', 'Consultas', 'Cirugías', 'Análisis', 'Radiografías']),
]


class CategoryFactory(DjangoModelFactory):
    """Factory for product categories."""

    class Meta:
        model = Category
        django_get_or_create = ('slug',)

    name = factory.LazyAttribute(lambda o: fake.random_element([c[0] for c in PRODUCT_CATEGORIES]))
    name_es = factory.LazyAttribute(lambda o: o.name)
    name_en = factory.LazyAttribute(lambda o: o.name)
    slug = factory.LazyAttribute(lambda o: fake.unique.slug())
    description = factory.LazyAttribute(lambda o: fake.paragraph())
    description_es = factory.LazyAttribute(lambda o: o.description)
    description_en = factory.LazyAttribute(lambda o: o.description)
    is_active = True


class ProductFactory(DjangoModelFactory):
    """Factory for products."""

    class Meta:
        model = Product

    name = factory.LazyAttribute(lambda o: fake.random_element([
        'Croquetas Premium Adulto 15kg', 'Royal Canin Cachorro 3kg',
        'Frontline Plus', 'Nexgard Masticable', 'Collar Antipulgas',
        'Shampoo Medicado', 'Vitaminas para Pelo', 'Snacks Dentales',
        'Cama Ortopédica', 'Juguete Kong', 'Correa Retráctil',
        'Transportadora Mediana', 'Plato Antiderrame', 'Cepillo Furminator'
    ]))
    name_es = factory.LazyAttribute(lambda o: o.name)
    name_en = factory.LazyAttribute(lambda o: o.name)
    slug = factory.LazyAttribute(lambda o: fake.unique.slug())
    description = factory.LazyAttribute(lambda o: fake.paragraph())
    description_es = factory.LazyAttribute(lambda o: o.description)
    description_en = factory.LazyAttribute(lambda o: o.description)
    price = factory.LazyAttribute(
        lambda o: Decimal(str(fake.pyfloat(min_value=50, max_value=2000, right_digits=2)))
    )
    category = factory.SubFactory(CategoryFactory)
    stock_quantity = factory.LazyAttribute(lambda o: fake.random_int(0, 100))
    sku = factory.LazyAttribute(lambda o: fake.unique.bothify('SKU-????-####'))
    is_active = True


class CartFactory(DjangoModelFactory):
    """Factory for shopping carts."""

    class Meta:
        model = Cart

    user = factory.SubFactory(OwnerFactory)


class CartItemFactory(DjangoModelFactory):
    """Factory for cart items."""

    class Meta:
        model = CartItem

    cart = factory.SubFactory(CartFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = factory.LazyAttribute(lambda o: fake.random_int(1, 5))


class OrderFactory(DjangoModelFactory):
    """Factory for orders."""

    class Meta:
        model = Order

    user = factory.SubFactory(OwnerFactory)
    order_number = factory.LazyAttribute(lambda o: Order.generate_order_number())
    status = factory.LazyAttribute(
        lambda o: fake.random_element(['pending', 'paid', 'preparing', 'ready', 'shipped', 'delivered', 'cancelled'])
    )
    fulfillment_method = factory.LazyAttribute(
        lambda o: fake.random_element(['pickup', 'delivery'])
    )
    payment_method = factory.LazyAttribute(
        lambda o: fake.random_element(['cash', 'card', 'transfer'])
    )
    shipping_address = factory.LazyAttribute(
        lambda o: fake.address() if o.fulfillment_method == 'delivery' else ''
    )
    shipping_phone = factory.LazyAttribute(lambda o: fake.phone_number()[:20])
    subtotal = factory.LazyAttribute(
        lambda o: Decimal(str(fake.pyfloat(min_value=100, max_value=5000, right_digits=2)))
    )
    shipping_cost = factory.LazyAttribute(
        lambda o: Decimal('50.00') if o.fulfillment_method == 'delivery' else Decimal('0')
    )
    tax = factory.LazyAttribute(
        lambda o: o.subtotal * Decimal('0.16')
    )
    total = factory.LazyAttribute(
        lambda o: o.subtotal + o.shipping_cost + o.tax
    )
    notes = factory.LazyAttribute(lambda o: fake.sentence() if fake.boolean(30) else '')


class OrderItemFactory(DjangoModelFactory):
    """Factory for order items."""

    class Meta:
        model = OrderItem

    order = factory.SubFactory(OrderFactory)
    product = factory.SubFactory(ProductFactory)
    product_name = factory.LazyAttribute(lambda o: o.product.name)
    product_sku = factory.LazyAttribute(lambda o: o.product.sku)
    price = factory.LazyAttribute(lambda o: o.product.price)
    quantity = factory.LazyAttribute(lambda o: fake.random_int(1, 3))
