"""Factories for CRM app models."""
import factory
from factory.django import DjangoModelFactory
from faker import Faker

from apps.crm.models import OwnerProfile, CustomerTag, Interaction, CustomerNote
from .accounts import OwnerFactory, StaffFactory

fake = Faker(['es_MX', 'en_US'])


class CustomerTagFactory(DjangoModelFactory):
    """Factory for customer tags."""

    class Meta:
        model = CustomerTag
        django_get_or_create = ('name',)

    name = factory.LazyAttribute(lambda o: fake.unique.word().title())
    color = factory.LazyAttribute(lambda o: fake.hex_color())
    description = factory.LazyAttribute(lambda o: fake.sentence())
    is_active = True


class OwnerProfileFactory(DjangoModelFactory):
    """Factory for owner CRM profiles."""

    class Meta:
        model = OwnerProfile
        django_get_or_create = ('user',)

    user = factory.SubFactory(OwnerFactory)
    preferred_language = factory.LazyAttribute(lambda o: fake.random_element(['es', 'en']))
    preferred_contact_method = factory.LazyAttribute(
        lambda o: fake.random_element(['whatsapp', 'email', 'sms', 'phone'])
    )
    notes = factory.LazyAttribute(lambda o: fake.paragraph() if fake.boolean(70) else '')
    total_visits = factory.LazyAttribute(lambda o: fake.random_int(0, 20))
    total_spent = factory.LazyAttribute(lambda o: fake.pydecimal(min_value=0, max_value=50000, right_digits=2))
    referral_source = factory.LazyAttribute(
        lambda o: fake.random_element(['Google', 'Facebook', 'Referido', 'Instagram', 'Volante', ''])
    )

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for tag in extracted:
                self.tags.add(tag)


class InteractionFactory(DjangoModelFactory):
    """Factory for customer interactions."""

    class Meta:
        model = Interaction

    owner_profile = factory.SubFactory(OwnerProfileFactory)
    interaction_type = factory.LazyAttribute(
        lambda o: fake.random_element(['call', 'email', 'chat', 'visit', 'whatsapp'])
    )
    channel = factory.LazyAttribute(
        lambda o: fake.random_element(['phone', 'email', 'chat', 'in_person', 'whatsapp'])
    )
    direction = factory.LazyAttribute(lambda o: fake.random_element(['inbound', 'outbound']))
    subject = factory.LazyAttribute(lambda o: fake.sentence(nb_words=5))
    notes = factory.LazyAttribute(lambda o: fake.paragraph())
    handled_by = factory.SubFactory(StaffFactory)
    duration_minutes = factory.LazyAttribute(lambda o: fake.random_int(1, 30) if fake.boolean(50) else None)
    outcome = factory.LazyAttribute(lambda o: fake.sentence(nb_words=3))
    follow_up_required = factory.LazyAttribute(lambda o: fake.boolean(20))


class CustomerNoteFactory(DjangoModelFactory):
    """Factory for customer notes."""

    class Meta:
        model = CustomerNote

    owner_profile = factory.SubFactory(OwnerProfileFactory)
    author = factory.SubFactory(StaffFactory)
    content = factory.LazyAttribute(lambda o: fake.paragraph())
    is_pinned = factory.LazyAttribute(lambda o: fake.boolean(10))
    is_private = factory.LazyAttribute(lambda o: fake.boolean(20))
