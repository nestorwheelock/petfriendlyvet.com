"""Factories for appointments app models."""
import factory
from factory.django import DjangoModelFactory
from faker import Faker
from datetime import time, timedelta
from decimal import Decimal

from apps.appointments.models import Appointment, ServiceType, ScheduleBlock
from .accounts import OwnerFactory, VetFactory
from .pets import PetFactory

fake = Faker(['es_MX', 'en_US'])


class ServiceTypeFactory(DjangoModelFactory):
    """Factory for service types."""

    class Meta:
        model = ServiceType
        django_get_or_create = ('name',)

    name = factory.LazyAttribute(lambda o: fake.random_element([
        'Consulta General', 'Vacunación', 'Esterilización',
        'Limpieza Dental', 'Emergencia', 'Chequeo'
    ]))
    description = factory.LazyAttribute(lambda o: fake.paragraph())
    duration_minutes = factory.LazyAttribute(lambda o: fake.random_element([15, 30, 45, 60, 90]))
    price = factory.LazyAttribute(
        lambda o: Decimal(str(fake.pyfloat(min_value=200, max_value=2000, right_digits=2)))
    )
    category = factory.LazyAttribute(lambda o: fake.random_element(['clinic', 'surgery', 'emergency']))
    is_active = True


class ScheduleBlockFactory(DjangoModelFactory):
    """Factory for schedule blocks (staff availability)."""

    class Meta:
        model = ScheduleBlock

    staff = factory.SubFactory(VetFactory)
    day_of_week = factory.LazyAttribute(lambda o: fake.random_int(0, 6))
    start_time = factory.LazyAttribute(lambda o: time(fake.random_int(8, 12), 0))
    end_time = factory.LazyAttribute(lambda o: time(fake.random_int(13, 18), 0))
    is_available = True


class AppointmentFactory(DjangoModelFactory):
    """Factory for appointments."""

    class Meta:
        model = Appointment

    owner = factory.SubFactory(OwnerFactory)
    pet = factory.SubFactory(PetFactory)
    veterinarian = factory.SubFactory(VetFactory)
    service = factory.SubFactory(ServiceTypeFactory)
    scheduled_start = factory.LazyAttribute(
        lambda o: fake.date_time_between(start_date='-30d', end_date='+30d')
    )
    scheduled_end = factory.LazyAttribute(
        lambda o: o.scheduled_start + timedelta(minutes=30)
    )
    status = factory.LazyAttribute(
        lambda o: fake.random_element(['scheduled', 'confirmed', 'completed', 'cancelled', 'no_show'])
    )
    notes = factory.LazyAttribute(lambda o: fake.paragraph() if fake.boolean(30) else '')
