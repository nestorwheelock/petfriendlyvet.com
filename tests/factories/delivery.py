"""Factories for delivery app models."""
import factory
from factory.django import DjangoModelFactory
from faker import Faker
from datetime import date, time, timedelta
from decimal import Decimal

from apps.delivery.models import DeliveryZone, DeliverySlot, DeliveryDriver, Delivery
from .accounts import UserFactory, StaffFactory

fake = Faker(['es_MX', 'en_US'])

CDMX_ZONES = [
    ('CDMX-CENTRO', 'Centro Histórico', 50),
    ('CDMX-ROMA', 'Roma/Condesa', 45),
    ('CDMX-POLANCO', 'Polanco', 55),
    ('CDMX-COYOACAN', 'Coyoacán', 60),
    ('CDMX-SANTAFE', 'Santa Fe', 75),
    ('CDMX-NARVARTE', 'Narvarte/Del Valle', 50),
]


class DeliveryZoneFactory(DjangoModelFactory):
    """Factory for delivery zones."""

    class Meta:
        model = DeliveryZone
        django_get_or_create = ('code',)

    @factory.lazy_attribute
    def code(self):
        zone = fake.random_element(CDMX_ZONES)
        return zone[0]

    @factory.lazy_attribute
    def name(self):
        zone = fake.random_element(CDMX_ZONES)
        return zone[1]

    delivery_fee = factory.LazyAttribute(
        lambda o: Decimal(str(fake.random_element([45, 50, 55, 60, 75])))
    )
    estimated_time_minutes = factory.LazyAttribute(lambda o: fake.random_int(25, 60))
    is_active = True


class DeliverySlotFactory(DjangoModelFactory):
    """Factory for delivery slots."""

    class Meta:
        model = DeliverySlot

    zone = factory.SubFactory(DeliveryZoneFactory)
    date = factory.LazyAttribute(
        lambda o: fake.date_between(start_date='today', end_date='+14d')
    )
    start_time = factory.LazyAttribute(
        lambda o: time(fake.random_element([9, 12, 15]), 0)
    )
    end_time = factory.LazyAttribute(
        lambda o: time(o.start_time.hour + 3, 0)
    )
    capacity = factory.LazyAttribute(lambda o: fake.random_int(8, 15))
    booked_count = factory.LazyAttribute(lambda o: fake.random_int(0, 5))
    is_active = True


class DeliveryDriverFactory(DjangoModelFactory):
    """Factory for delivery drivers."""

    class Meta:
        model = DeliveryDriver

    user = factory.SubFactory(UserFactory)
    driver_type = factory.LazyAttribute(
        lambda o: fake.random_element(['employee', 'contractor'])
    )
    phone = factory.LazyAttribute(lambda o: fake.phone_number()[:20])
    vehicle_type = factory.LazyAttribute(
        lambda o: fake.random_element(['motorcycle', 'car', 'bicycle'])
    )
    license_plate = factory.LazyAttribute(lambda o: fake.bothify('???-###').upper())
    max_deliveries_per_day = factory.LazyAttribute(lambda o: fake.random_int(10, 20))
    is_active = True
    is_available = True

    # Contractor fields
    rfc = factory.LazyAttribute(
        lambda o: fake.bothify('????######???').upper() if o.driver_type == 'contractor' else ''
    )
    rate_per_delivery = factory.LazyAttribute(
        lambda o: Decimal('35.00') if o.driver_type == 'contractor' else None
    )
    rate_per_km = factory.LazyAttribute(
        lambda o: Decimal('5.00') if o.driver_type == 'contractor' else None
    )

    @factory.post_generation
    def zones(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for zone in extracted:
                self.zones.add(zone)


class DeliveryFactory(DjangoModelFactory):
    """Factory for deliveries."""

    class Meta:
        model = Delivery

    # Note: order should be set explicitly
    zone = factory.SubFactory(DeliveryZoneFactory)
    slot = factory.SubFactory(DeliverySlotFactory)
    driver = factory.SubFactory(DeliveryDriverFactory)
    status = factory.LazyAttribute(
        lambda o: fake.random_element(['pending', 'assigned', 'picked_up', 'out_for_delivery', 'delivered'])
    )
    address = factory.LazyAttribute(lambda o: fake.address())
    latitude = factory.LazyAttribute(
        lambda o: Decimal(str(fake.pyfloat(min_value=19.3, max_value=19.5, right_digits=6)))
    )
    longitude = factory.LazyAttribute(
        lambda o: Decimal(str(fake.pyfloat(min_value=-99.2, max_value=-99.1, right_digits=6)))
    )
    scheduled_date = factory.LazyAttribute(lambda o: o.slot.date if o.slot else date.today())
    notes = factory.LazyAttribute(lambda o: fake.sentence() if fake.boolean(30) else '')
