"""Factory Boy factories for generating test data."""
from .accounts import UserFactory, OwnerFactory, StaffFactory, VetFactory
from .crm import OwnerProfileFactory, CustomerTagFactory, InteractionFactory
from .pets import (
    PetFactory, DogFactory, CatFactory,
    MedicalConditionFactory, VaccinationFactory,
    VisitFactory, MedicationFactory, ClinicalNoteFactory,
    WeightRecordFactory, PetDocumentFactory
)
from .appointments import AppointmentFactory, ServiceTypeFactory, ScheduleBlockFactory
from .store import CategoryFactory, ProductFactory, OrderFactory, CartFactory, OrderItemFactory
from .delivery import (
    DeliveryZoneFactory, DeliverySlotFactory,
    DeliveryDriverFactory, DeliveryFactory
)

__all__ = [
    # Accounts
    'UserFactory', 'OwnerFactory', 'StaffFactory', 'VetFactory',
    # CRM
    'OwnerProfileFactory', 'CustomerTagFactory', 'InteractionFactory',
    # Pets
    'PetFactory', 'DogFactory', 'CatFactory',
    'MedicalConditionFactory', 'VaccinationFactory',
    'VisitFactory', 'MedicationFactory', 'ClinicalNoteFactory',
    'WeightRecordFactory', 'PetDocumentFactory',
    # Appointments
    'AppointmentFactory', 'ServiceTypeFactory', 'ScheduleBlockFactory',
    # Store
    'CategoryFactory', 'ProductFactory', 'OrderFactory', 'CartFactory', 'OrderItemFactory',
    # Delivery
    'DeliveryZoneFactory', 'DeliverySlotFactory',
    'DeliveryDriverFactory', 'DeliveryFactory',
]
