"""
Tests for Document Management (S-013)

Tests cover:
- Pet document uploads
- Document list views
- Document access control
- File validation
"""
import pytest
from datetime import date
from io import BytesIO
from PIL import Image
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()


def create_test_image():
    """Create a test image file."""
    file = BytesIO()
    image = Image.new('RGB', (100, 100), color='red')
    image.save(file, 'PNG')
    file.seek(0)
    return SimpleUploadedFile(
        'test_image.png',
        file.read(),
        content_type='image/png'
    )


def create_test_pdf():
    """Create a test PDF file."""
    content = b'%PDF-1.4 test content'
    return SimpleUploadedFile(
        'test_document.pdf',
        content,
        content_type='application/pdf'
    )


# =============================================================================
# Document Model Tests
# =============================================================================

@pytest.mark.django_db
class TestPetDocumentModel:
    """Tests for the PetDocument model."""

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
            species='dog'
        )

    def test_create_document(self, pet, owner):
        """Can create a pet document."""
        from apps.pets.models import PetDocument

        doc = PetDocument.objects.create(
            pet=pet,
            title='Vaccination Certificate',
            document_type='certificate',
            description='Annual vaccination certificate',
            uploaded_by=owner
        )

        assert doc.pk is not None
        assert doc.pet == pet
        assert doc.visible_to_owner is True

    def test_document_str(self, pet, owner):
        """Document string representation."""
        from apps.pets.models import PetDocument

        doc = PetDocument.objects.create(
            pet=pet,
            title='X-Ray Results',
            document_type='xray',
            uploaded_by=owner
        )

        assert 'Luna' in str(doc)
        assert 'X-Ray' in str(doc)

    def test_document_types(self, pet, owner):
        """All document types are valid."""
        from apps.pets.models import PetDocument, DOCUMENT_TYPES

        for doc_type, _ in DOCUMENT_TYPES:
            doc = PetDocument.objects.create(
                pet=pet,
                title=f'Test {doc_type}',
                document_type=doc_type,
                uploaded_by=owner
            )
            assert doc.document_type == doc_type


# =============================================================================
# Document Upload Tests
# =============================================================================

@pytest.mark.django_db
class TestDocumentUpload:
    """Tests for document upload functionality."""

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
            species='dog'
        )

    def test_upload_document_requires_login(self, client, pet):
        """Document upload requires authentication."""
        url = reverse('pets:document_upload', kwargs={'pet_pk': pet.pk})
        response = client.get(url)
        assert response.status_code == 302

    def test_upload_document_form_displayed(self, client, owner, pet):
        """Upload form is displayed for pet owner."""
        client.force_login(owner)
        url = reverse('pets:document_upload', kwargs={'pet_pk': pet.pk})
        response = client.get(url)

        assert response.status_code == 200
        assert b'Upload' in response.content or b'upload' in response.content

    def test_upload_image_document(self, client, owner, pet):
        """Can upload image document."""
        from apps.pets.models import PetDocument

        client.force_login(owner)
        url = reverse('pets:document_upload', kwargs={'pet_pk': pet.pk})

        response = client.post(url, {
            'title': 'Luna Photo',
            'document_type': 'photo',
            'description': 'Recent photo',
            'file': create_test_image()
        })

        assert PetDocument.objects.filter(pet=pet, title='Luna Photo').exists()

    def test_upload_pdf_document(self, client, owner, pet):
        """Can upload PDF document."""
        from apps.pets.models import PetDocument

        client.force_login(owner)
        url = reverse('pets:document_upload', kwargs={'pet_pk': pet.pk})

        response = client.post(url, {
            'title': 'Lab Results',
            'document_type': 'lab_result',
            'description': 'Blood work results',
            'file': create_test_pdf()
        })

        assert PetDocument.objects.filter(pet=pet, title='Lab Results').exists()

    def test_cannot_upload_to_other_user_pet(self, client, pet):
        """Cannot upload documents to another user's pet."""
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass'
        )

        client.force_login(other_user)
        url = reverse('pets:document_upload', kwargs={'pet_pk': pet.pk})
        response = client.get(url)

        assert response.status_code == 404


# =============================================================================
# Document List Tests
# =============================================================================

@pytest.mark.django_db
class TestDocumentList:
    """Tests for document list views."""

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
            species='dog'
        )

    @pytest.fixture
    def documents(self, pet, owner):
        from apps.pets.models import PetDocument

        docs = []
        docs.append(PetDocument.objects.create(
            pet=pet,
            title='Vaccination Record',
            document_type='certificate',
            uploaded_by=owner,
            visible_to_owner=True
        ))
        docs.append(PetDocument.objects.create(
            pet=pet,
            title='X-Ray Image',
            document_type='xray',
            uploaded_by=owner,
            visible_to_owner=True
        ))
        docs.append(PetDocument.objects.create(
            pet=pet,
            title='Internal Notes',
            document_type='other',
            uploaded_by=owner,
            visible_to_owner=False  # Staff only
        ))
        return docs

    def test_document_list_requires_login(self, client, pet):
        """Document list requires authentication."""
        url = reverse('pets:document_list', kwargs={'pet_pk': pet.pk})
        response = client.get(url)
        assert response.status_code == 302

    def test_document_list_shows_visible_documents(self, client, owner, pet, documents):
        """Shows only owner-visible documents to owner."""
        client.force_login(owner)
        url = reverse('pets:document_list', kwargs={'pet_pk': pet.pk})
        response = client.get(url)

        assert response.status_code == 200
        assert b'Vaccination Record' in response.content
        assert b'X-Ray Image' in response.content
        assert b'Internal Notes' not in response.content

    def test_staff_sees_all_documents(self, client, pet, documents):
        """Staff can see all documents including internal."""
        staff = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='testpass',
            role='staff'
        )

        client.force_login(staff)
        url = reverse('pets:document_list', kwargs={'pet_pk': pet.pk})
        response = client.get(url)

        assert response.status_code == 200
        assert b'Internal Notes' in response.content

    def test_cannot_view_other_user_documents(self, client, pet, documents):
        """Cannot view another user's pet documents."""
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass'
        )

        client.force_login(other_user)
        url = reverse('pets:document_list', kwargs={'pet_pk': pet.pk})
        response = client.get(url)

        assert response.status_code == 404


# =============================================================================
# Document Delete Tests
# =============================================================================

@pytest.mark.django_db
class TestDocumentDelete:
    """Tests for document deletion."""

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
            species='dog'
        )

    @pytest.fixture
    def document(self, pet, owner):
        from apps.pets.models import PetDocument
        return PetDocument.objects.create(
            pet=pet,
            title='Test Document',
            document_type='other',
            uploaded_by=owner
        )

    def test_delete_document_requires_login(self, client, pet, document):
        """Document deletion requires authentication."""
        url = reverse('pets:document_delete', kwargs={
            'pet_pk': pet.pk,
            'pk': document.pk
        })
        response = client.post(url)
        assert response.status_code == 302

    def test_owner_can_delete_own_document(self, client, owner, pet, document):
        """Owner can delete their own documents."""
        from apps.pets.models import PetDocument

        client.force_login(owner)
        url = reverse('pets:document_delete', kwargs={
            'pet_pk': pet.pk,
            'pk': document.pk
        })
        response = client.post(url)

        assert not PetDocument.objects.filter(pk=document.pk).exists()

    def test_cannot_delete_other_user_document(self, client, pet, document):
        """Cannot delete another user's document."""
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass'
        )

        client.force_login(other_user)
        url = reverse('pets:document_delete', kwargs={
            'pet_pk': pet.pk,
            'pk': document.pk
        })
        response = client.post(url)

        assert response.status_code == 404


# =============================================================================
# Document Form Tests
# =============================================================================

@pytest.mark.django_db
class TestDocumentForm:
    """Tests for document upload form."""

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
            species='dog'
        )

    def test_form_validates_required_fields(self, client, owner, pet):
        """Form requires title and type."""
        client.force_login(owner)
        url = reverse('pets:document_upload', kwargs={'pet_pk': pet.pk})

        response = client.post(url, {
            'description': 'Missing title and type'
        })

        # Should not create document
        from apps.pets.models import PetDocument
        assert PetDocument.objects.filter(pet=pet).count() == 0

    def test_form_with_all_fields(self, client, owner, pet):
        """Form accepts all fields."""
        from apps.pets.models import PetDocument

        client.force_login(owner)
        url = reverse('pets:document_upload', kwargs={'pet_pk': pet.pk})

        response = client.post(url, {
            'title': 'Complete Document',
            'document_type': 'certificate',
            'description': 'Full description here',
            'file': create_test_image()
        })

        doc = PetDocument.objects.get(pet=pet, title='Complete Document')
        assert doc.description == 'Full description here'
        assert doc.document_type == 'certificate'
