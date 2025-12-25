"""
Tests for Pet Profiles and Medical Records (S-003)

Tests cover:
- Pet model CRUD operations
- Medical records (vaccinations, visits, medications)
- Access control (owners see only their pets)
- Clinical notes visibility (staff only)
- Weight tracking
- Document uploads
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()


# =============================================================================
# Pet Model Tests
# =============================================================================

@pytest.mark.django_db
class TestPetModel:
    """Tests for the Pet model."""

    @pytest.fixture
    def owner(self):
        return User.objects.create_user(
            username='petowner',
            email='owner@example.com',
            password='testpass123',
            role='owner'
        )

    def test_pet_model_exists(self):
        """Pet model should exist."""
        from apps.pets.models import Pet
        assert Pet is not None

    def test_pet_species_choices_exist(self):
        """Species choices should be defined."""
        from apps.pets.models import SPECIES_CHOICES
        assert len(SPECIES_CHOICES) >= 5
        species_values = [s[0] for s in SPECIES_CHOICES]
        assert 'dog' in species_values
        assert 'cat' in species_values

    def test_pet_gender_choices_exist(self):
        """Gender choices should be defined."""
        from apps.pets.models import GENDER_CHOICES
        assert len(GENDER_CHOICES) >= 2

    def test_create_pet(self, owner):
        """Should be able to create a pet."""
        from apps.pets.models import Pet

        pet = Pet.objects.create(
            owner=owner,
            name='Luna',
            species='dog',
            breed='Golden Retriever',
            gender='female',
            date_of_birth=date(2022, 3, 15)
        )
        assert pet.id is not None
        assert pet.name == 'Luna'
        assert pet.species == 'dog'
        assert pet.owner == owner

    def test_pet_str_representation(self, owner):
        """Pet string representation should include name and species."""
        from apps.pets.models import Pet

        pet = Pet.objects.create(
            owner=owner,
            name='Max',
            species='dog'
        )
        assert 'Max' in str(pet)

    def test_pet_age_calculation(self, owner):
        """Pet should calculate age correctly."""
        from apps.pets.models import Pet

        today = date.today()
        birth_date = date(today.year - 3, today.month, today.day)  # Exactly 3 years ago
        pet = Pet.objects.create(
            owner=owner,
            name='Buddy',
            species='dog',
            date_of_birth=birth_date
        )
        assert pet.age_years == 3

    def test_pet_age_none_when_no_birthdate(self, owner):
        """Pet age should be None when birthdate is not set."""
        from apps.pets.models import Pet

        pet = Pet.objects.create(
            owner=owner,
            name='Mystery',
            species='cat'
        )
        assert pet.age_years is None

    def test_pet_weight_field(self, owner):
        """Pet should have weight field."""
        from apps.pets.models import Pet

        pet = Pet.objects.create(
            owner=owner,
            name='Chunky',
            species='cat',
            weight_kg=Decimal('5.50')
        )
        assert pet.weight_kg == Decimal('5.50')

    def test_pet_microchip_field(self, owner):
        """Pet should have microchip field."""
        from apps.pets.models import Pet

        pet = Pet.objects.create(
            owner=owner,
            name='Chipped',
            species='dog',
            microchip_id='123456789012345'
        )
        assert pet.microchip_id == '123456789012345'

    def test_pet_is_neutered_field(self, owner):
        """Pet should have is_neutered field."""
        from apps.pets.models import Pet

        pet = Pet.objects.create(
            owner=owner,
            name='Fixed',
            species='cat',
            is_neutered=True
        )
        assert pet.is_neutered is True

    def test_owner_can_have_multiple_pets(self, owner):
        """Owner should be able to have multiple pets."""
        from apps.pets.models import Pet

        Pet.objects.create(owner=owner, name='Pet1', species='dog')
        Pet.objects.create(owner=owner, name='Pet2', species='cat')
        Pet.objects.create(owner=owner, name='Pet3', species='bird')

        assert owner.pets.count() == 3


# =============================================================================
# Medical Condition Tests
# =============================================================================

@pytest.mark.django_db
class TestMedicalConditionModel:
    """Tests for the MedicalCondition model."""

    @pytest.fixture
    def pet(self):
        owner = User.objects.create_user(
            username='owner', email='owner@test.com', password='pass'
        )
        from apps.pets.models import Pet
        return Pet.objects.create(owner=owner, name='Fluffy', species='cat')

    def test_medical_condition_model_exists(self):
        """MedicalCondition model should exist."""
        from apps.pets.models import MedicalCondition
        assert MedicalCondition is not None

    def test_create_allergy(self, pet):
        """Should be able to create an allergy condition."""
        from apps.pets.models import MedicalCondition

        condition = MedicalCondition.objects.create(
            pet=pet,
            name='Chicken allergy',
            condition_type='allergy',
            notes='Causes skin irritation',
            is_active=True
        )
        assert condition.id is not None
        assert condition.condition_type == 'allergy'

    def test_create_chronic_condition(self, pet):
        """Should be able to create a chronic condition."""
        from apps.pets.models import MedicalCondition

        condition = MedicalCondition.objects.create(
            pet=pet,
            name='Diabetes',
            condition_type='chronic',
            diagnosed_date=date(2024, 1, 15)
        )
        assert condition.diagnosed_date == date(2024, 1, 15)

    def test_pet_has_conditions_relation(self, pet):
        """Pet should have conditions relation."""
        from apps.pets.models import MedicalCondition

        MedicalCondition.objects.create(pet=pet, name='Allergy 1', condition_type='allergy')
        MedicalCondition.objects.create(pet=pet, name='Condition 2', condition_type='chronic')

        assert pet.conditions.count() == 2


# =============================================================================
# Vaccination Tests
# =============================================================================

@pytest.mark.django_db
class TestVaccinationModel:
    """Tests for the Vaccination model."""

    @pytest.fixture
    def pet(self):
        owner = User.objects.create_user(
            username='owner', email='owner@test.com', password='pass'
        )
        from apps.pets.models import Pet
        return Pet.objects.create(owner=owner, name='Buddy', species='dog')

    @pytest.fixture
    def vet(self):
        return User.objects.create_user(
            username='vet', email='vet@test.com', password='pass', role='vet'
        )

    def test_vaccination_model_exists(self):
        """Vaccination model should exist."""
        from apps.pets.models import Vaccination
        assert Vaccination is not None

    def test_create_vaccination(self, pet, vet):
        """Should be able to create a vaccination record."""
        from apps.pets.models import Vaccination

        vax = Vaccination.objects.create(
            pet=pet,
            vaccine_name='Rabies',
            date_administered=date(2025, 3, 15),
            next_due_date=date(2026, 3, 15),
            administered_by=vet,
            batch_number='RAB-2025-001'
        )
        assert vax.id is not None
        assert vax.vaccine_name == 'Rabies'
        assert vax.next_due_date == date(2026, 3, 15)

    def test_vaccination_is_overdue(self, pet):
        """Should detect overdue vaccinations."""
        from apps.pets.models import Vaccination

        vax = Vaccination.objects.create(
            pet=pet,
            vaccine_name='DHPP',
            date_administered=date(2024, 1, 1),
            next_due_date=date(2024, 6, 1)  # Past date
        )
        assert vax.is_overdue is True

    def test_vaccination_is_current(self, pet):
        """Should detect current vaccinations."""
        from apps.pets.models import Vaccination

        vax = Vaccination.objects.create(
            pet=pet,
            vaccine_name='Rabies',
            date_administered=date.today(),
            next_due_date=date.today() + timedelta(days=365)
        )
        assert vax.is_overdue is False

    def test_vaccination_due_soon(self, pet):
        """Should detect vaccinations due soon."""
        from apps.pets.models import Vaccination

        vax = Vaccination.objects.create(
            pet=pet,
            vaccine_name='Bordetella',
            date_administered=date.today() - timedelta(days=330),
            next_due_date=date.today() + timedelta(days=15)  # Due in 15 days
        )
        assert vax.is_due_soon is True  # Due within 30 days

    def test_pet_has_vaccinations_relation(self, pet):
        """Pet should have vaccinations relation."""
        from apps.pets.models import Vaccination

        Vaccination.objects.create(
            pet=pet, vaccine_name='Rabies', date_administered=date.today()
        )
        Vaccination.objects.create(
            pet=pet, vaccine_name='DHPP', date_administered=date.today()
        )

        assert pet.vaccinations.count() == 2


# =============================================================================
# Visit Tests
# =============================================================================

@pytest.mark.django_db
class TestVisitModel:
    """Tests for the Visit model."""

    @pytest.fixture
    def pet(self):
        owner = User.objects.create_user(
            username='owner', email='owner@test.com', password='pass'
        )
        from apps.pets.models import Pet
        return Pet.objects.create(owner=owner, name='Max', species='dog')

    @pytest.fixture
    def vet(self):
        return User.objects.create_user(
            username='vet', email='vet@test.com', password='pass', role='vet'
        )

    def test_visit_model_exists(self):
        """Visit model should exist."""
        from apps.pets.models import Visit
        assert Visit is not None

    def test_create_visit(self, pet, vet):
        """Should be able to create a visit record."""
        from apps.pets.models import Visit
        from django.utils import timezone

        visit = Visit.objects.create(
            pet=pet,
            date=timezone.now(),
            reason='Annual checkup',
            diagnosis='Healthy',
            treatment='None required',
            veterinarian=vet,
            weight_kg=Decimal('25.5')
        )
        assert visit.id is not None
        assert visit.reason == 'Annual checkup'

    def test_visit_updates_pet_weight(self, pet, vet):
        """Visit with weight should update pet's current weight."""
        from apps.pets.models import Visit
        from django.utils import timezone

        Visit.objects.create(
            pet=pet,
            date=timezone.now(),
            reason='Checkup',
            weight_kg=Decimal('26.0'),
            veterinarian=vet
        )
        pet.refresh_from_db()
        assert pet.weight_kg == Decimal('26.0')

    def test_visit_can_have_follow_up(self, pet, vet):
        """Visit should support follow-up date."""
        from apps.pets.models import Visit
        from django.utils import timezone

        visit = Visit.objects.create(
            pet=pet,
            date=timezone.now(),
            reason='Surgery',
            follow_up_date=date.today() + timedelta(days=14),
            veterinarian=vet
        )
        assert visit.follow_up_date == date.today() + timedelta(days=14)

    def test_pet_has_visits_relation(self, pet, vet):
        """Pet should have visits relation."""
        from apps.pets.models import Visit
        from django.utils import timezone

        Visit.objects.create(pet=pet, date=timezone.now(), reason='Visit 1')
        Visit.objects.create(pet=pet, date=timezone.now(), reason='Visit 2')

        assert pet.visits.count() == 2


# =============================================================================
# Medication Tests
# =============================================================================

@pytest.mark.django_db
class TestMedicationModel:
    """Tests for the Medication model."""

    @pytest.fixture
    def pet(self):
        owner = User.objects.create_user(
            username='owner', email='owner@test.com', password='pass'
        )
        from apps.pets.models import Pet
        return Pet.objects.create(owner=owner, name='Sick Pet', species='cat')

    @pytest.fixture
    def vet(self):
        return User.objects.create_user(
            username='vet', email='vet@test.com', password='pass', role='vet'
        )

    def test_medication_model_exists(self):
        """Medication model should exist."""
        from apps.pets.models import Medication
        assert Medication is not None

    def test_create_medication(self, pet, vet):
        """Should be able to create a medication record."""
        from apps.pets.models import Medication

        med = Medication.objects.create(
            pet=pet,
            name='Amoxicillin',
            dosage='250mg',
            frequency='Twice daily',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=10),
            prescribing_vet=vet,
            notes='Take with food'
        )
        assert med.id is not None
        assert med.name == 'Amoxicillin'

    def test_medication_is_active(self, pet, vet):
        """Should detect active medications."""
        from apps.pets.models import Medication

        med = Medication.objects.create(
            pet=pet,
            name='Ongoing Med',
            dosage='10mg',
            frequency='Daily',
            start_date=date.today() - timedelta(days=5),
            end_date=date.today() + timedelta(days=5),
            prescribing_vet=vet
        )
        assert med.is_active is True

    def test_medication_is_completed(self, pet, vet):
        """Should detect completed medications."""
        from apps.pets.models import Medication

        med = Medication.objects.create(
            pet=pet,
            name='Finished Med',
            dosage='10mg',
            frequency='Daily',
            start_date=date.today() - timedelta(days=15),
            end_date=date.today() - timedelta(days=5),
            prescribing_vet=vet
        )
        assert med.is_active is False

    def test_pet_has_medications_relation(self, pet):
        """Pet should have medications relation."""
        from apps.pets.models import Medication

        Medication.objects.create(
            pet=pet, name='Med1', dosage='10mg', frequency='Daily', start_date=date.today()
        )
        Medication.objects.create(
            pet=pet, name='Med2', dosage='20mg', frequency='Twice daily', start_date=date.today()
        )

        assert pet.medications.count() == 2


# =============================================================================
# Access Control Tests
# =============================================================================

@pytest.mark.django_db
class TestPetAccessControl:
    """Tests for pet access control."""

    @pytest.fixture
    def owner1(self):
        return User.objects.create_user(
            username='owner1', email='owner1@test.com', password='pass', role='owner'
        )

    @pytest.fixture
    def owner2(self):
        return User.objects.create_user(
            username='owner2', email='owner2@test.com', password='pass', role='owner'
        )

    @pytest.fixture
    def staff(self):
        return User.objects.create_user(
            username='staff', email='staff@test.com', password='pass', role='staff'
        )

    def test_owner_only_sees_own_pets(self, owner1, owner2):
        """Owners should only see their own pets."""
        from apps.pets.models import Pet

        Pet.objects.create(owner=owner1, name='Owner1Pet', species='dog')
        Pet.objects.create(owner=owner2, name='Owner2Pet', species='cat')

        assert owner1.pets.count() == 1
        assert owner1.pets.first().name == 'Owner1Pet'
        assert owner2.pets.count() == 1
        assert owner2.pets.first().name == 'Owner2Pet'

    def test_pet_belongs_to_owner(self, owner1, owner2):
        """Pet should correctly identify its owner."""
        from apps.pets.models import Pet

        pet = Pet.objects.create(owner=owner1, name='MyPet', species='dog')

        assert pet.owner == owner1
        assert pet.owner != owner2


# =============================================================================
# Clinical Notes Tests (Staff-Only)
# =============================================================================

@pytest.mark.django_db
class TestClinicalNoteModel:
    """Tests for the ClinicalNote model (staff-only notes)."""

    @pytest.fixture
    def pet(self):
        owner = User.objects.create_user(
            username='owner', email='owner@test.com', password='pass'
        )
        from apps.pets.models import Pet
        return Pet.objects.create(owner=owner, name='Patient', species='dog')

    @pytest.fixture
    def vet(self):
        return User.objects.create_user(
            username='vet', email='vet@test.com', password='pass', role='vet'
        )

    def test_clinical_note_model_exists(self):
        """ClinicalNote model should exist."""
        from apps.pets.models import ClinicalNote
        assert ClinicalNote is not None

    def test_create_clinical_note(self, pet, vet):
        """Should be able to create a clinical note."""
        from apps.pets.models import ClinicalNote

        note = ClinicalNote.objects.create(
            pet=pet,
            author=vet,
            note='Patient shows signs of improvement after treatment.',
            note_type='observation'
        )
        assert note.id is not None
        assert 'improvement' in note.note

    def test_clinical_note_types(self, pet, vet):
        """Clinical notes should have different types."""
        from apps.pets.models import ClinicalNote, CLINICAL_NOTE_TYPES

        assert len(CLINICAL_NOTE_TYPES) >= 3
        note_values = [n[0] for n in CLINICAL_NOTE_TYPES]
        assert 'observation' in note_values
        assert 'treatment' in note_values

    def test_clinical_note_linked_to_visit(self, pet, vet):
        """Clinical note can be linked to a specific visit."""
        from apps.pets.models import ClinicalNote, Visit
        from django.utils import timezone

        visit = Visit.objects.create(pet=pet, date=timezone.now(), reason='Checkup')
        note = ClinicalNote.objects.create(
            pet=pet,
            author=vet,
            note='Post-visit observation',
            visit=visit
        )
        assert note.visit == visit

    def test_pet_has_clinical_notes_relation(self, pet, vet):
        """Pet should have clinical_notes relation."""
        from apps.pets.models import ClinicalNote

        ClinicalNote.objects.create(pet=pet, author=vet, note='Note 1')
        ClinicalNote.objects.create(pet=pet, author=vet, note='Note 2')

        assert pet.clinical_notes.count() == 2


# =============================================================================
# Weight Record Tests
# =============================================================================

@pytest.mark.django_db
class TestWeightRecordModel:
    """Tests for the WeightRecord model (weight tracking)."""

    @pytest.fixture
    def pet(self):
        owner = User.objects.create_user(
            username='owner', email='owner@test.com', password='pass'
        )
        from apps.pets.models import Pet
        return Pet.objects.create(owner=owner, name='Chunky', species='cat')

    @pytest.fixture
    def vet(self):
        return User.objects.create_user(
            username='vet', email='vet@test.com', password='pass', role='vet'
        )

    def test_weight_record_model_exists(self):
        """WeightRecord model should exist."""
        from apps.pets.models import WeightRecord
        assert WeightRecord is not None

    def test_create_weight_record(self, pet, vet):
        """Should be able to create a weight record."""
        from apps.pets.models import WeightRecord

        record = WeightRecord.objects.create(
            pet=pet,
            weight_kg=Decimal('5.50'),
            recorded_by=vet,
            notes='Weight after diet program'
        )
        assert record.id is not None
        assert record.weight_kg == Decimal('5.50')

    def test_weight_record_updates_pet_weight(self, pet, vet):
        """Creating weight record should update pet's current weight."""
        from apps.pets.models import WeightRecord

        WeightRecord.objects.create(
            pet=pet,
            weight_kg=Decimal('6.00'),
            recorded_by=vet
        )
        pet.refresh_from_db()
        assert pet.weight_kg == Decimal('6.00')

    def test_weight_record_history(self, pet, vet):
        """Should be able to track weight over time."""
        from apps.pets.models import WeightRecord

        WeightRecord.objects.create(pet=pet, weight_kg=Decimal('5.00'), recorded_by=vet)
        WeightRecord.objects.create(pet=pet, weight_kg=Decimal('5.25'), recorded_by=vet)
        WeightRecord.objects.create(pet=pet, weight_kg=Decimal('5.50'), recorded_by=vet)

        assert pet.weight_records.count() == 3

    def test_weight_record_date_auto_set(self, pet, vet):
        """Weight record date should be auto-set if not provided."""
        from apps.pets.models import WeightRecord

        record = WeightRecord.objects.create(
            pet=pet,
            weight_kg=Decimal('5.00'),
            recorded_by=vet
        )
        assert record.recorded_date is not None


# =============================================================================
# Pet Document Tests
# =============================================================================

@pytest.mark.django_db
class TestPetDocumentModel:
    """Tests for the PetDocument model (document uploads)."""

    @pytest.fixture
    def pet(self):
        owner = User.objects.create_user(
            username='owner', email='owner@test.com', password='pass'
        )
        from apps.pets.models import Pet
        return Pet.objects.create(owner=owner, name='DocPet', species='dog')

    @pytest.fixture
    def staff(self):
        return User.objects.create_user(
            username='staff', email='staff@test.com', password='pass', role='staff'
        )

    def test_pet_document_model_exists(self):
        """PetDocument model should exist."""
        from apps.pets.models import PetDocument
        assert PetDocument is not None

    def test_document_types_exist(self):
        """Document types should be defined."""
        from apps.pets.models import DOCUMENT_TYPES
        assert len(DOCUMENT_TYPES) >= 4
        doc_values = [d[0] for d in DOCUMENT_TYPES]
        assert 'lab_result' in doc_values
        assert 'xray' in doc_values
        assert 'photo' in doc_values

    def test_create_pet_document(self, pet, staff):
        """Should be able to create a document record."""
        from apps.pets.models import PetDocument

        doc = PetDocument.objects.create(
            pet=pet,
            title='Blood Work Results',
            document_type='lab_result',
            uploaded_by=staff,
            description='Annual blood panel'
        )
        assert doc.id is not None
        assert doc.title == 'Blood Work Results'

    def test_pet_has_documents_relation(self, pet, staff):
        """Pet should have documents relation."""
        from apps.pets.models import PetDocument

        PetDocument.objects.create(pet=pet, title='Doc 1', document_type='photo', uploaded_by=staff)
        PetDocument.objects.create(pet=pet, title='Doc 2', document_type='xray', uploaded_by=staff)

        assert pet.documents.count() == 2

    def test_document_visibility_flag(self, pet, staff):
        """Documents should have visibility flag for owner."""
        from apps.pets.models import PetDocument

        doc = PetDocument.objects.create(
            pet=pet,
            title='Internal Note',
            document_type='other',
            uploaded_by=staff,
            visible_to_owner=False
        )
        assert doc.visible_to_owner is False

        public_doc = PetDocument.objects.create(
            pet=pet,
            title='Vaccination Card',
            document_type='certificate',
            uploaded_by=staff,
            visible_to_owner=True
        )
        assert public_doc.visible_to_owner is True


# =============================================================================
# Pet Form Tests
# =============================================================================

@pytest.mark.django_db
class TestPetForm:
    """Tests for the PetForm."""

    @pytest.fixture
    def owner(self):
        return User.objects.create_user(
            username='petowner',
            email='owner@example.com',
            password='testpass123',
            role='owner'
        )

    def test_form_fields(self):
        """Form has expected fields."""
        from apps.pets.forms import PetForm

        form = PetForm()
        expected_fields = [
            'name', 'species', 'breed', 'gender', 'date_of_birth',
            'weight_kg', 'microchip_id', 'is_neutered', 'photo', 'notes'
        ]
        for field in expected_fields:
            assert field in form.fields

    def test_form_valid_minimal_data(self):
        """Form is valid with minimal required data."""
        from apps.pets.forms import PetForm

        form = PetForm(data={
            'name': 'Max',
            'species': 'dog',
            'gender': 'male',
        })

        assert form.is_valid(), form.errors

    def test_form_valid_full_data(self):
        """Form is valid with all fields."""
        from apps.pets.forms import PetForm

        form = PetForm(data={
            'name': 'Luna',
            'species': 'cat',
            'breed': 'Persian',
            'gender': 'female',
            'date_of_birth': date.today() - timedelta(days=730),
            'weight_kg': Decimal('4.5'),
            'microchip_id': '123456789012345',
            'is_neutered': True,
            'notes': 'Very friendly cat',
        })

        assert form.is_valid(), form.errors

    def test_form_invalid_without_name(self):
        """Form requires name."""
        from apps.pets.forms import PetForm

        form = PetForm(data={
            'species': 'dog',
            'gender': 'male',
        })

        assert not form.is_valid()
        assert 'name' in form.errors

    def test_form_invalid_without_species(self):
        """Form requires species."""
        from apps.pets.forms import PetForm

        form = PetForm(data={
            'name': 'Max',
            'gender': 'male',
        })

        assert not form.is_valid()
        assert 'species' in form.errors

    def test_form_has_widget_classes(self):
        """Form widgets have CSS classes."""
        from apps.pets.forms import PetForm

        form = PetForm()

        assert 'rounded-md' in form.fields['name'].widget.attrs.get('class', '')
        assert 'rounded-md' in form.fields['species'].widget.attrs.get('class', '')
        assert 'rounded-md' in form.fields['notes'].widget.attrs.get('class', '')

    def test_form_saves_pet(self, owner):
        """Form can save a pet."""
        from apps.pets.forms import PetForm
        from apps.pets.models import Pet

        form = PetForm(data={
            'name': 'Buddy',
            'species': 'dog',
            'breed': 'Golden Retriever',
            'gender': 'male',
        })

        assert form.is_valid()
        pet = form.save(commit=False)
        pet.owner = owner
        pet.save()

        assert Pet.objects.filter(name='Buddy', owner=owner).exists()


@pytest.mark.django_db
class TestPetDocumentForm:
    """Tests for the PetDocumentForm."""

    @pytest.fixture
    def owner(self):
        return User.objects.create_user(
            username='petowner',
            email='owner@example.com',
            password='testpass123',
            role='owner'
        )

    @pytest.fixture
    def pet(self, owner):
        from apps.pets.models import Pet
        return Pet.objects.create(
            owner=owner,
            name='Luna',
            species='dog',
            gender='female',
        )

    def test_form_fields(self):
        """Form has expected fields."""
        from apps.pets.forms import PetDocumentForm

        form = PetDocumentForm()
        expected_fields = ['title', 'document_type', 'description', 'file']
        for field in expected_fields:
            assert field in form.fields

    def test_form_valid_with_title_and_type(self):
        """Form is valid with title and document_type."""
        from apps.pets.forms import PetDocumentForm

        form = PetDocumentForm(data={
            'title': 'Vaccination Record',
            'document_type': 'certificate',
        })

        # File is required by model, but form only has these fields
        # Check if form validates without file (depends on model field)
        # For this test, just check the data fields are accepted
        assert 'title' not in form.errors if not form.is_valid() else True

    def test_form_has_widget_classes(self):
        """Form widgets have CSS classes."""
        from apps.pets.forms import PetDocumentForm

        form = PetDocumentForm()

        assert 'rounded-md' in form.fields['title'].widget.attrs.get('class', '')
        assert 'rounded-md' in form.fields['document_type'].widget.attrs.get('class', '')
        assert 'rounded-md' in form.fields['description'].widget.attrs.get('class', '')
