"""Factories for pets app models."""
import factory
from factory.django import DjangoModelFactory
from faker import Faker
from datetime import date, timedelta
from decimal import Decimal

from apps.pets.models import (
    Pet, MedicalCondition, Vaccination, Visit,
    Medication, ClinicalNote, WeightRecord, PetDocument
)
from .accounts import OwnerFactory, VetFactory, StaffFactory

fake = Faker(['es_MX', 'en_US'])

# Realistic pet names by species
DOG_NAMES = ['Max', 'Luna', 'Rocky', 'Bella', 'Charlie', 'Coco', 'Bruno', 'Lola',
             'Thor', 'Nina', 'Duke', 'Canela', 'Rex', 'Mia', 'Zeus', 'Princesa',
             'Toby', 'Kira', 'Lucas', 'Nala', 'Simba', 'Maya', 'Firulais', 'Pelusa']
CAT_NAMES = ['Michi', 'Whiskers', 'Gatito', 'Minino', 'Felix', 'Garfield', 'Pelusa',
             'Bigotes', 'Mittens', 'Shadow', 'Tigre', 'Manchas', 'Nieve', 'Oreo',
             'Simba', 'Miau', 'Luna', 'Cleo', 'Tom', 'Sombra']
BIRD_NAMES = ['Piolín', 'Tweety', 'Rio', 'Kiwi', 'Coco', 'Pepe', 'Loro', 'Canario']
RABBIT_NAMES = ['Bunny', 'Conejo', 'Copito', 'Tambor', 'Pelusa', 'Zanahoria', 'Nieve']

DOG_BREEDS = ['Labrador', 'Golden Retriever', 'Bulldog Francés', 'Chihuahua',
              'Pastor Alemán', 'Poodle', 'Beagle', 'Husky Siberiano', 'Boxer',
              'Schnauzer', 'Pitbull', 'Rottweiler', 'Yorkshire', 'Shih Tzu',
              'Dachshund', 'Mestizo', 'Cocker Spaniel', 'Border Collie']
CAT_BREEDS = ['Siamés', 'Persa', 'Maine Coon', 'Mestizo', 'British Shorthair',
              'Ragdoll', 'Bengal', 'Angora', 'Sphynx', 'Scottish Fold']

VACCINES_DOG = ['Rabia', 'Parvovirus', 'Moquillo', 'Hepatitis', 'Leptospirosis', 'Bordetella']
VACCINES_CAT = ['Rabia', 'Triple Felina', 'Leucemia Felina', 'PIF']
VACCINES_GENERAL = ['Rabia']

CONDITIONS = [
    ('allergy', 'Alergia alimentaria'),
    ('allergy', 'Alergia a pulgas'),
    ('allergy', 'Alergia ambiental'),
    ('chronic', 'Diabetes'),
    ('chronic', 'Artritis'),
    ('chronic', 'Enfermedad renal'),
    ('chronic', 'Hipotiroidismo'),
    ('chronic', 'Epilepsia'),
    ('injury', 'Fractura antigua'),
    ('other', 'Ansiedad por separación'),
    ('other', 'Obesidad'),
]

MEDICATIONS = [
    ('Apoquel', '16mg', 'Una vez al día'),
    ('Rimadyl', '75mg', 'Dos veces al día'),
    ('Metacam', '1.5mg/ml', 'Una vez al día'),
    ('Prednisona', '5mg', 'Una vez al día'),
    ('Amoxicilina', '250mg', 'Cada 12 horas'),
    ('Metronidazol', '250mg', 'Cada 8 horas'),
    ('Omeprazol', '20mg', 'Una vez al día'),
    ('Insulina', '10 unidades', 'Dos veces al día'),
]

VISIT_REASONS = [
    'Consulta de rutina',
    'Vacunación',
    'Problema digestivo',
    'Problema de piel',
    'Cojera',
    'Revisión post-operatoria',
    'Problema dental',
    'Control de peso',
    'Problema respiratorio',
    'Revisión de oídos',
    'Esterilización',
    'Desparasitación',
    'Problema ocular',
    'Chequeo geriátrico',
]


class PetFactory(DjangoModelFactory):
    """Factory for creating Pet instances."""

    class Meta:
        model = Pet

    owner = factory.SubFactory(OwnerFactory)
    name = factory.LazyAttribute(lambda o: fake.random_element(DOG_NAMES))
    species = 'dog'
    breed = factory.LazyAttribute(lambda o: fake.random_element(DOG_BREEDS))
    gender = factory.LazyAttribute(lambda o: fake.random_element(['male', 'female']))
    date_of_birth = factory.LazyAttribute(
        lambda o: fake.date_between(start_date='-15y', end_date='-3m')
    )
    weight_kg = factory.LazyAttribute(
        lambda o: Decimal(str(fake.pyfloat(min_value=2, max_value=40, right_digits=1)))
    )
    is_neutered = factory.LazyAttribute(lambda o: fake.boolean(70))
    microchip_id = factory.LazyAttribute(
        lambda o: fake.numerify('###############') if fake.boolean(60) else ''
    )
    notes = factory.LazyAttribute(lambda o: fake.paragraph() if fake.boolean(30) else '')


class DogFactory(PetFactory):
    """Factory specifically for dogs."""
    species = 'dog'
    name = factory.LazyAttribute(lambda o: fake.random_element(DOG_NAMES))
    breed = factory.LazyAttribute(lambda o: fake.random_element(DOG_BREEDS))
    weight_kg = factory.LazyAttribute(
        lambda o: Decimal(str(fake.pyfloat(min_value=3, max_value=50, right_digits=1)))
    )


class CatFactory(PetFactory):
    """Factory specifically for cats."""
    species = 'cat'
    name = factory.LazyAttribute(lambda o: fake.random_element(CAT_NAMES))
    breed = factory.LazyAttribute(lambda o: fake.random_element(CAT_BREEDS))
    weight_kg = factory.LazyAttribute(
        lambda o: Decimal(str(fake.pyfloat(min_value=2, max_value=8, right_digits=1)))
    )


class BirdFactory(PetFactory):
    """Factory specifically for birds."""
    species = 'bird'
    name = factory.LazyAttribute(lambda o: fake.random_element(BIRD_NAMES))
    breed = factory.LazyAttribute(lambda o: fake.random_element(['Periquito', 'Canario', 'Loro', 'Cotorro', 'Cockatiel']))
    weight_kg = factory.LazyAttribute(
        lambda o: Decimal(str(fake.pyfloat(min_value=0.02, max_value=1, right_digits=2)))
    )


class RabbitFactory(PetFactory):
    """Factory specifically for rabbits."""
    species = 'rabbit'
    name = factory.LazyAttribute(lambda o: fake.random_element(RABBIT_NAMES))
    breed = factory.LazyAttribute(lambda o: fake.random_element(['Holland Lop', 'Mini Rex', 'Angora', 'Cabeza de León', 'Mestizo']))
    weight_kg = factory.LazyAttribute(
        lambda o: Decimal(str(fake.pyfloat(min_value=1, max_value=5, right_digits=1)))
    )


class MedicalConditionFactory(DjangoModelFactory):
    """Factory for medical conditions."""

    class Meta:
        model = MedicalCondition

    pet = factory.SubFactory(PetFactory)

    @factory.lazy_attribute
    def condition_type(self):
        condition = fake.random_element(CONDITIONS)
        return condition[0]

    @factory.lazy_attribute
    def name(self):
        condition = fake.random_element(CONDITIONS)
        return condition[1]

    diagnosed_date = factory.LazyAttribute(
        lambda o: fake.date_between(start_date='-3y', end_date='today')
    )
    notes = factory.LazyAttribute(lambda o: fake.paragraph() if fake.boolean(50) else '')
    is_active = factory.LazyAttribute(lambda o: fake.boolean(80))


class VaccinationFactory(DjangoModelFactory):
    """Factory for vaccination records."""

    class Meta:
        model = Vaccination

    pet = factory.SubFactory(PetFactory)
    vaccine_name = factory.LazyAttribute(lambda o: fake.random_element(VACCINES_DOG))
    date_administered = factory.LazyAttribute(
        lambda o: fake.date_between(start_date='-2y', end_date='today')
    )
    next_due_date = factory.LazyAttribute(
        lambda o: o.date_administered + timedelta(days=365)
    )
    administered_by = factory.SubFactory(VetFactory)
    batch_number = factory.LazyAttribute(lambda o: fake.bothify('???-#####'))
    notes = factory.LazyAttribute(lambda o: fake.sentence() if fake.boolean(20) else '')


class VisitFactory(DjangoModelFactory):
    """Factory for veterinary visits."""

    class Meta:
        model = Visit

    pet = factory.SubFactory(PetFactory)
    date = factory.LazyAttribute(
        lambda o: fake.date_time_between(start_date='-1y', end_date='now')
    )
    reason = factory.LazyAttribute(lambda o: fake.random_element(VISIT_REASONS))
    diagnosis = factory.LazyAttribute(lambda o: fake.paragraph() if fake.boolean(70) else '')
    treatment = factory.LazyAttribute(lambda o: fake.paragraph() if fake.boolean(60) else '')
    veterinarian = factory.SubFactory(VetFactory)
    weight_kg = factory.LazyAttribute(
        lambda o: Decimal(str(fake.pyfloat(min_value=2, max_value=40, right_digits=1)))
    )
    follow_up_date = factory.LazyAttribute(
        lambda o: fake.date_between(start_date='today', end_date='+30d') if fake.boolean(30) else None
    )
    notes = factory.LazyAttribute(lambda o: fake.paragraph() if fake.boolean(40) else '')


class MedicationFactory(DjangoModelFactory):
    """Factory for medications."""

    class Meta:
        model = Medication

    pet = factory.SubFactory(PetFactory)

    @factory.lazy_attribute
    def name(self):
        med = fake.random_element(MEDICATIONS)
        return med[0]

    @factory.lazy_attribute
    def dosage(self):
        med = fake.random_element(MEDICATIONS)
        return med[1]

    @factory.lazy_attribute
    def frequency(self):
        med = fake.random_element(MEDICATIONS)
        return med[2]

    start_date = factory.LazyAttribute(
        lambda o: fake.date_between(start_date='-60d', end_date='today')
    )
    end_date = factory.LazyAttribute(
        lambda o: o.start_date + timedelta(days=fake.random_int(7, 30)) if fake.boolean(70) else None
    )
    prescribing_vet = factory.SubFactory(VetFactory)
    notes = factory.LazyAttribute(lambda o: fake.sentence() if fake.boolean(30) else '')


class ClinicalNoteFactory(DjangoModelFactory):
    """Factory for clinical notes."""

    class Meta:
        model = ClinicalNote

    pet = factory.SubFactory(PetFactory)
    author = factory.SubFactory(VetFactory)
    visit = None  # Can be linked to a visit
    note = factory.LazyAttribute(lambda o: fake.paragraph(nb_sentences=3))
    note_type = factory.LazyAttribute(
        lambda o: fake.random_element(['observation', 'treatment', 'followup', 'lab', 'other'])
    )


class WeightRecordFactory(DjangoModelFactory):
    """Factory for weight records."""

    class Meta:
        model = WeightRecord

    pet = factory.SubFactory(PetFactory)
    weight_kg = factory.LazyAttribute(
        lambda o: Decimal(str(fake.pyfloat(min_value=2, max_value=40, right_digits=1)))
    )
    recorded_by = factory.SubFactory(StaffFactory)
    notes = factory.LazyAttribute(lambda o: fake.sentence() if fake.boolean(20) else '')


class PetDocumentFactory(DjangoModelFactory):
    """Factory for pet documents."""

    class Meta:
        model = PetDocument

    pet = factory.SubFactory(PetFactory)
    title = factory.LazyAttribute(lambda o: fake.sentence(nb_words=4))
    document_type = factory.LazyAttribute(
        lambda o: fake.random_element(['lab_result', 'xray', 'certificate', 'prescription', 'other'])
    )
    description = factory.LazyAttribute(lambda o: fake.paragraph() if fake.boolean(50) else '')
    uploaded_by = factory.SubFactory(StaffFactory)
    visible_to_owner = factory.LazyAttribute(lambda o: fake.boolean(80))
