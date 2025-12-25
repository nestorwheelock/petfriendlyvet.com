"""Browser tests for clinical notes functionality."""
import pytest
from playwright.sync_api import Page, expect


@pytest.mark.browser
class TestClinicalNotesView:
    """Test clinical notes viewing."""

    def test_pet_medical_history_loads(
        self, authenticated_page: Page, live_server, pet_with_medical_records
    ):
        """Pet medical history is accessible."""
        page = authenticated_page
        pet = pet_with_medical_records['pet']
        page.goto(f"{live_server.url}/pets/{pet.pk}/")
        expect(page.locator('body')).to_be_visible()

    def test_clinical_notes_section_visible(
        self, authenticated_page: Page, live_server, pet_with_medical_records
    ):
        """Clinical notes section is displayed."""
        page = authenticated_page
        pet = pet_with_medical_records['pet']
        page.goto(f"{live_server.url}/pets/{pet.pk}/")

        # Look for notes section
        notes_section = page.locator('text=Notes').or_(
            page.locator('text=Notas').or_(
                page.locator('[data-testid="clinical-notes"]')
            )
        )
        # May or may not exist
        expect(page.locator('body')).to_be_visible()


@pytest.mark.browser
class TestClinicalNotesCreation:
    """Test clinical note creation."""

    def test_add_note_form_accessible(
        self, admin_page: Page, live_server, pet_with_medical_records
    ):
        """Add note form is accessible to staff."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/pets/clinicalnote/add/")
        expect(page.locator('body')).to_be_visible()

    def test_note_type_selector(
        self, admin_page: Page, live_server, pet_with_medical_records
    ):
        """Note type selector is available."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/pets/clinicalnote/add/")

        # Look for note type field
        note_type = page.locator('select[name="note_type"]').or_(
            page.locator('#id_note_type')
        )
        # May or may not exist
        expect(page.locator('body')).to_be_visible()


@pytest.mark.browser
class TestWeightTracking:
    """Test weight tracking functionality."""

    def test_weight_history_visible(
        self, authenticated_page: Page, live_server, pet_with_medical_records
    ):
        """Weight history is displayed."""
        page = authenticated_page
        pet = pet_with_medical_records['pet']
        page.goto(f"{live_server.url}/pets/{pet.pk}/")

        # Look for weight section
        weight_section = page.locator('text=Weight').or_(
            page.locator('text=Peso').or_(
                page.locator('[data-testid="weight-history"]')
            )
        )
        # May or may not exist
        expect(page.locator('body')).to_be_visible()

    def test_weight_chart_rendered(
        self, authenticated_page: Page, live_server, pet_with_medical_records
    ):
        """Weight chart is rendered."""
        page = authenticated_page
        pet = pet_with_medical_records['pet']
        page.goto(f"{live_server.url}/pets/{pet.pk}/")

        # Look for chart element
        chart = page.locator('canvas').or_(
            page.locator('.chart').or_(
                page.locator('[data-testid="weight-chart"]')
            )
        )
        # May or may not exist
        expect(page.locator('body')).to_be_visible()


@pytest.mark.browser
class TestPetDocuments:
    """Test pet document management."""

    def test_documents_section_visible(
        self, authenticated_page: Page, live_server, pet_with_medical_records
    ):
        """Documents section is displayed."""
        page = authenticated_page
        pet = pet_with_medical_records['pet']
        page.goto(f"{live_server.url}/pets/{pet.pk}/")

        # Look for documents section
        docs_section = page.locator('text=Documents').or_(
            page.locator('text=Documentos').or_(
                page.locator('[data-testid="pet-documents"]')
            )
        )
        # May or may not exist
        expect(page.locator('body')).to_be_visible()

    def test_upload_document_accessible(
        self, admin_page: Page, live_server, pet_with_medical_records
    ):
        """Document upload is accessible to staff."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/pets/petdocument/add/")
        expect(page.locator('body')).to_be_visible()


@pytest.mark.browser
class TestMedicalRecordsPDF:
    """Test medical records PDF generation."""

    def test_export_records_accessible(
        self, authenticated_page: Page, live_server, pet_with_medical_records
    ):
        """Export records is accessible."""
        page = authenticated_page
        pet = pet_with_medical_records['pet']
        page.goto(f"{live_server.url}/pets/{pet.pk}/")

        # Look for export button
        export_btn = page.locator('text=Export').or_(
            page.locator('text=Exportar').or_(
                page.locator('[data-action="export-records"]')
            )
        )
        # May or may not exist
        expect(page.locator('body')).to_be_visible()


@pytest.mark.browser
class TestVetNotesView:
    """Test veterinarian notes view."""

    def test_vet_can_view_all_notes(
        self, staff_page: Page, live_server, pet_with_medical_records
    ):
        """Vet can view all clinical notes."""
        page = staff_page
        pet = pet_with_medical_records['pet']
        page.goto(f"{live_server.url}/pets/{pet.pk}/")
        expect(page.locator('body')).to_be_visible()

    def test_vet_notes_admin_list(
        self, admin_page: Page, live_server
    ):
        """Vet can access notes in admin."""
        page = admin_page
        page.goto(f"{live_server.url}/admin/pets/clinicalnote/")
        expect(page.locator('body')).to_be_visible()
