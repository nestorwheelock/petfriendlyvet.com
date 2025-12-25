"""E2E test for clinical notes and documentation journey.

Simulates the complete clinical documentation workflow using the actual
model structures from apps.pets and apps.practice.

Tests the medical records system.
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta

from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db(transaction=True)
class TestClinicalNotesJourney:
    """Complete clinical notes documentation journey."""

    @pytest.fixture
    def veterinarian(self, db):
        """Create a veterinarian."""
        from apps.practice.models import StaffProfile

        user = User.objects.create_user(
            username='dr.notes@petfriendlyvet.com',
            email='dr.notes@petfriendlyvet.com',
            password='vet123',
            first_name='Dr. Elena',
            last_name='Documentación',
            role='vet',
            is_staff=True,
        )
        StaffProfile.objects.create(
            user=user,
            role='veterinarian',
            can_prescribe=True,
        )
        return user

    @pytest.fixture
    def pet_owner(self, db):
        """Create a pet owner."""
        return User.objects.create_user(
            username='patient.owner@example.com',
            email='patient.owner@example.com',
            password='owner123',
            first_name='Roberto',
            last_name='Dueño',
            role='owner',
        )

    @pytest.fixture
    def patient(self, db, pet_owner):
        """Create a patient (pet)."""
        from apps.pets.models import Pet

        return Pet.objects.create(
            owner=pet_owner,
            name='Documentado',
            species='dog',
            breed='Beagle',
            gender='male',
            date_of_birth=date.today() - timedelta(days=365 * 4),
            weight_kg=Decimal('12.5'),
        )

    def test_complete_clinical_notes_journey(
        self, db, veterinarian, pet_owner, patient
    ):
        """Test complete clinical documentation workflow."""
        from apps.pets.models import ClinicalNote, WeightRecord, PetDocument

        # =========================================================================
        # STEP 1: Record Initial Observation
        # =========================================================================
        observation = ClinicalNote.objects.create(
            pet=patient,
            author=veterinarian,
            note_type='observation',
            note='Paciente presenta letargo y pérdida de apetito. '
                 'Temperatura 39.2°C, FC 110 lpm.',
        )

        assert observation.pk is not None
        assert observation.note_type == 'observation'

        # =========================================================================
        # STEP 2: Record Weight
        # =========================================================================
        weight_record = WeightRecord.objects.create(
            pet=patient,
            weight_kg=Decimal('11.8'),
            recorded_by=veterinarian,
            notes='Pérdida de 0.7 kg desde última visita.',
        )

        patient.weight_kg = Decimal('11.8')
        patient.save()

        assert weight_record.pk is not None

        # =========================================================================
        # STEP 3: Record Diagnosis
        # =========================================================================
        diagnosis = ClinicalNote.objects.create(
            pet=patient,
            author=veterinarian,
            note_type='diagnosis',
            note='Diagnóstico presuntivo: Gastritis. '
                 'Hemograma y química sanguínea normales. '
                 'Radiografía sin evidencia de cuerpo extraño.',
        )

        assert diagnosis.pk is not None

        # =========================================================================
        # STEP 4: Record Treatment
        # =========================================================================
        treatment = ClinicalNote.objects.create(
            pet=patient,
            author=veterinarian,
            note_type='treatment',
            note='Tratamiento: Fluidoterapia SC 150ml, '
                 'Maropitant 1mg/kg SC, Famotidina 0.5mg/kg IV. '
                 'Prescripción: Sucralfato 500mg c/8h x 5 días.',
        )

        assert treatment.pk is not None

        # =========================================================================
        # STEP 5: Attach Document
        # =========================================================================
        lab_document = PetDocument.objects.create(
            pet=patient,
            document_type='lab_result',
            title='Hemograma y Química - 2024',
            description='Resultados de laboratorio',
            uploaded_by=veterinarian,
        )

        assert lab_document.pk is not None

        # =========================================================================
        # VERIFICATION
        # =========================================================================
        # All notes recorded
        all_notes = ClinicalNote.objects.filter(pet=patient)
        assert all_notes.count() == 3

        # Weight recorded
        assert WeightRecord.objects.filter(pet=patient).exists()

        # Document attached
        assert PetDocument.objects.filter(pet=patient).exists()


@pytest.mark.django_db(transaction=True)
class TestClinicalNoteTypes:
    """Test different clinical note types."""

    def test_note_types_available(self, db):
        """Different note types can be created."""
        from apps.pets.models import Pet, ClinicalNote

        owner = User.objects.create_user(
            username='types.owner@example.com',
            email='types.owner@example.com',
            password='owner123',
            role='owner',
        )

        vet = User.objects.create_user(
            username='types.vet@example.com',
            email='types.vet@example.com',
            password='vet123',
            role='vet',
            is_staff=True,
        )

        pet = Pet.objects.create(owner=owner, name='Types', species='dog')

        # Create various note types
        note_types = ['observation', 'diagnosis', 'treatment', 'follow_up']

        for note_type in note_types:
            ClinicalNote.objects.create(
                pet=pet,
                author=vet,
                note_type=note_type,
                note=f'Clinical note of type: {note_type}',
            )

        # All note types created
        assert ClinicalNote.objects.filter(pet=pet).count() == len(note_types)


@pytest.mark.django_db(transaction=True)
class TestPetDocuments:
    """Test pet document management."""

    def test_multiple_document_types(self, db):
        """Can attach multiple document types."""
        from apps.pets.models import Pet, PetDocument

        owner = User.objects.create_user(
            username='docs.owner@example.com',
            email='docs.owner@example.com',
            password='owner123',
            role='owner',
        )

        vet = User.objects.create_user(
            username='docs.vet@example.com',
            email='docs.vet@example.com',
            password='vet123',
            role='vet',
            is_staff=True,
        )

        pet = Pet.objects.create(owner=owner, name='Docs', species='cat')

        # Create various document types
        document_types = ['lab_result', 'imaging', 'vaccination', 'other']

        for doc_type in document_types:
            PetDocument.objects.create(
                pet=pet,
                document_type=doc_type,
                title=f'{doc_type.title()} Document',
                description=f'Document of type {doc_type}',
                uploaded_by=vet,
            )

        # All documents attached
        assert PetDocument.objects.filter(pet=pet).count() == len(document_types)
