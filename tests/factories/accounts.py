"""Factories for accounts app models."""
import factory
from factory.django import DjangoModelFactory
from faker import Faker

from apps.accounts.models import User

fake = Faker(['es_MX', 'en_US'])


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances."""

    class Meta:
        model = User
        django_get_or_create = ('email',)

    username = factory.LazyAttribute(lambda o: fake.unique.user_name())
    email = factory.LazyAttribute(lambda o: fake.unique.email())
    first_name = factory.LazyAttribute(lambda o: fake.first_name())
    last_name = factory.LazyAttribute(lambda o: fake.last_name())
    phone = factory.LazyAttribute(lambda o: fake.phone_number()[:20])
    role = 'owner'
    is_active = True
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')

    @factory.lazy_attribute
    def language(self):
        return fake.random_element(['es', 'en'])


class OwnerFactory(UserFactory):
    """Factory for pet owner users."""
    role = 'owner'


class StaffFactory(UserFactory):
    """Factory for staff users."""
    role = 'staff'
    is_staff = True


class VetFactory(UserFactory):
    """Factory for veterinarian users."""
    role = 'vet'
    is_staff = True
