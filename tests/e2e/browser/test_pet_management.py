"""Browser tests for pet management.

Tests pet CRUD operations, dashboard, and pet profiles.
"""
import re
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from playwright.sync_api import expect


@pytest.fixture
def pet_with_records(db, owner_user):
    """Create a pet with vaccinations and medical conditions."""
    from apps.pets.models import Pet, Vaccination, MedicalCondition

    pet = Pet.objects.create(
        owner=owner_user,
        name='Max',
        species='dog',
        breed='Golden Retriever',
        gender='male',
        date_of_birth=datetime(2020, 3, 15).date(),
        weight_kg=Decimal('28.5'),
        microchip_id='123456789012345',
        is_neutered=True,
        notes='Very friendly, loves treats',
    )

    # Add vaccination
    Vaccination.objects.create(
        pet=pet,
        vaccine_name='Rabies',
        date_administered=datetime(2023, 6, 15).date(),
        next_due_date=datetime(2024, 6, 15).date(),
        notes='Annual vaccination',
    )

    # Add medical condition
    MedicalCondition.objects.create(
        pet=pet,
        name='Hip Dysplasia',
        condition_type='chronic',
        diagnosed_date=datetime(2022, 9, 1).date(),
        notes='Mild, managed with supplements',
        is_active=True,
    )

    return pet


@pytest.fixture
def multiple_pets(db, owner_user):
    """Create multiple pets for list testing."""
    from apps.pets.models import Pet

    pets = [
        Pet.objects.create(
            owner=owner_user,
            name='Buddy',
            species='dog',
            breed='Labrador',
            gender='male',
            date_of_birth=datetime(2019, 5, 10).date(),
            weight_kg=Decimal('32.0'),
        ),
        Pet.objects.create(
            owner=owner_user,
            name='Whiskers',
            species='cat',
            breed='Persian',
            gender='female',
            date_of_birth=datetime(2021, 8, 22).date(),
            weight_kg=Decimal('4.5'),
        ),
        Pet.objects.create(
            owner=owner_user,
            name='Tweety',
            species='bird',
            breed='Canary',
            gender='unknown',
        ),
    ]
    return pets


@pytest.mark.browser
class TestOwnerDashboard:
    """Test owner dashboard functionality."""

    def test_dashboard_requires_login(self, page, live_server, db):
        """Dashboard requires authentication."""
        page.goto(f'{live_server.url}/pets/')
        page.wait_for_load_state('networkidle')

        expect(page).to_have_url(re.compile(r'.*/accounts/login.*'))

    def test_dashboard_loads_for_authenticated_user(self, authenticated_page, live_server, db):
        """Dashboard loads for authenticated users."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pets/')

        expect(page).to_have_title(re.compile(r'.*[Dd]ashboard.*'))
        expect(page.locator('h1')).to_contain_text('Dashboard')

    def test_dashboard_shows_pets_section(self, authenticated_page, live_server, multiple_pets):
        """Dashboard shows My Pets section with pets."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pets/')

        # Should show pets section header
        expect(page.locator('h2:has-text("My Pets")')).to_be_visible()

        # Should show each pet
        for pet in multiple_pets:
            expect(page.locator(f'text={pet.name}')).to_be_visible()

    def test_dashboard_shows_add_pet_button(self, authenticated_page, live_server, db):
        """Dashboard has Add Pet button."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pets/')

        add_button = page.locator('a[href*="add"]:has-text("Add Pet")')
        expect(add_button.first).to_be_visible()

    def test_dashboard_shows_empty_state(self, authenticated_page, live_server, db):
        """Dashboard shows empty state when no pets."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pets/')

        # Should show empty state message
        empty_message = page.locator('text=No pets yet')
        expect(empty_message.first).to_be_visible()

    def test_dashboard_pet_links_to_detail(self, authenticated_page, live_server, multiple_pets):
        """Clicking pet on dashboard goes to detail page."""
        page = authenticated_page
        pet = multiple_pets[0]

        page.goto(f'{live_server.url}/pets/')

        # Click on pet name/card
        page.locator(f'a:has-text("{pet.name}")').first.click()
        page.wait_for_load_state('networkidle')

        expect(page).to_have_url(re.compile(rf'.*/pets/{pet.pk}.*'))

    def test_dashboard_shows_upcoming_appointments(self, authenticated_page, live_server, pet_with_records):
        """Dashboard shows upcoming appointments section."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pets/')

        # Should show appointments section
        expect(page.locator('h2:has-text("Upcoming Appointments")')).to_be_visible()


@pytest.mark.browser
class TestPetList:
    """Test pet list page."""

    def test_pet_list_loads(self, authenticated_page, live_server, db):
        """Pet list page loads."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pets/pets/')

        expect(page).to_have_title(re.compile(r'.*[Pp]ets.*'))
        expect(page.locator('h1')).to_contain_text('My Pets')

    def test_pet_list_shows_all_pets(self, authenticated_page, live_server, multiple_pets):
        """Pet list shows all user's pets."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pets/pets/')

        for pet in multiple_pets:
            expect(page.locator(f'text={pet.name}')).to_be_visible()
            expect(page.locator(f'text={pet.get_species_display()}')).to_be_visible()

    def test_pet_list_shows_pet_details(self, authenticated_page, live_server, multiple_pets):
        """Pet cards show breed and age."""
        page = authenticated_page
        pet = multiple_pets[0]  # Buddy the Labrador

        page.goto(f'{live_server.url}/pets/pets/')

        # Should show breed
        expect(page.locator(f'text={pet.breed}')).to_be_visible()

    def test_pet_list_has_add_button(self, authenticated_page, live_server, db):
        """Pet list has Add Pet button."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pets/pets/')

        add_button = page.locator('a[href*="add"]:has-text("Add Pet")')
        expect(add_button.first).to_be_visible()

    def test_pet_list_click_goes_to_detail(self, authenticated_page, live_server, multiple_pets):
        """Clicking pet card goes to detail page."""
        page = authenticated_page
        pet = multiple_pets[0]

        page.goto(f'{live_server.url}/pets/pets/')

        # Click on pet card
        page.locator(f'a[href*="{pet.pk}"]').first.click()
        page.wait_for_load_state('networkidle')

        expect(page).to_have_url(re.compile(rf'.*/pets/{pet.pk}.*'))


@pytest.mark.browser
class TestPetDetail:
    """Test pet detail page."""

    def test_pet_detail_loads(self, authenticated_page, live_server, pet_with_records):
        """Pet detail page loads."""
        page = authenticated_page
        pet = pet_with_records

        page.goto(f'{live_server.url}/pets/pets/{pet.pk}/')

        expect(page.locator('h1')).to_contain_text(pet.name)

    def test_pet_detail_shows_species_and_breed(self, authenticated_page, live_server, pet_with_records):
        """Pet detail shows species and breed."""
        page = authenticated_page
        pet = pet_with_records

        page.goto(f'{live_server.url}/pets/pets/{pet.pk}/')

        content = page.content()
        assert 'Golden Retriever' in content
        assert 'Dog' in content or 'dog' in content

    def test_pet_detail_shows_basic_info(self, authenticated_page, live_server, pet_with_records):
        """Pet detail shows basic information."""
        page = authenticated_page
        pet = pet_with_records

        page.goto(f'{live_server.url}/pets/pets/{pet.pk}/')

        content = page.content()
        # Should show weight (may use comma or period as decimal separator depending on locale)
        assert '28.5' in content or '28,5' in content

        # Should show microchip
        assert pet.microchip_id in content

    def test_pet_detail_shows_gender_badge(self, authenticated_page, live_server, pet_with_records):
        """Pet detail shows gender badge."""
        page = authenticated_page
        pet = pet_with_records

        page.goto(f'{live_server.url}/pets/pets/{pet.pk}/')

        # Should show Male badge
        expect(page.locator('.rounded-full:has-text("Male")')).to_be_visible()

    def test_pet_detail_shows_neutered_badge(self, authenticated_page, live_server, pet_with_records):
        """Pet detail shows neutered/spayed badge if applicable."""
        page = authenticated_page
        pet = pet_with_records

        page.goto(f'{live_server.url}/pets/pets/{pet.pk}/')

        # Should show Neutered badge
        neutered_badge = page.locator('.rounded-full:has-text("Neutered"), .rounded-full:has-text("Spayed")')
        expect(neutered_badge).to_be_visible()

    def test_pet_detail_shows_vaccinations(self, authenticated_page, live_server, pet_with_records):
        """Pet detail shows vaccination records."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pets/pets/{pet_with_records.pk}/')

        # Should show vaccinations section
        expect(page.locator('h2:has-text("Vaccinations")')).to_be_visible()

        # Should show Rabies vaccination
        expect(page.locator('text=Rabies')).to_be_visible()

    def test_pet_detail_shows_medical_conditions(self, authenticated_page, live_server, pet_with_records):
        """Pet detail shows medical conditions."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pets/pets/{pet_with_records.pk}/')

        # Should show medical conditions section
        expect(page.locator('h2:has-text("Medical Conditions")')).to_be_visible()

        # Should show Hip Dysplasia
        expect(page.locator('text=Hip Dysplasia')).to_be_visible()

    def test_pet_detail_shows_notes(self, authenticated_page, live_server, pet_with_records):
        """Pet detail shows notes."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pets/pets/{pet_with_records.pk}/')

        expect(page.locator('text=Very friendly, loves treats')).to_be_visible()

    def test_pet_detail_has_edit_button(self, authenticated_page, live_server, pet_with_records):
        """Pet detail has Edit Pet button."""
        page = authenticated_page
        pet = pet_with_records

        page.goto(f'{live_server.url}/pets/pets/{pet.pk}/')

        edit_button = page.locator(f'a[href*="{pet.pk}/edit"]:has-text("Edit")')
        expect(edit_button.first).to_be_visible()

    def test_pet_detail_edit_button_works(self, authenticated_page, live_server, pet_with_records):
        """Edit button navigates to edit page."""
        page = authenticated_page
        pet = pet_with_records

        page.goto(f'{live_server.url}/pets/pets/{pet.pk}/')

        page.locator(f'a[href*="{pet.pk}/edit"]').first.click()
        page.wait_for_load_state('networkidle')

        expect(page).to_have_url(re.compile(rf'.*/pets/{pet.pk}/edit.*'))

    def test_pet_detail_shows_quick_actions(self, authenticated_page, live_server, pet_with_records):
        """Pet detail shows quick actions section."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pets/pets/{pet_with_records.pk}/')

        expect(page.locator('h2:has-text("Quick Actions")')).to_be_visible()


@pytest.mark.browser
class TestPetCreate:
    """Test pet creation."""

    def test_add_pet_page_loads(self, authenticated_page, live_server, db):
        """Add pet page loads."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pets/pets/add/')

        content = page.content()
        assert 'Add' in content or 'New Pet' in content
        # Use more specific selector to exclude language forms and chat widget
        expect(page.locator('main form')).to_be_visible()

    def test_add_pet_form_has_required_fields(self, authenticated_page, live_server, db):
        """Add pet form has all required fields."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pets/pets/add/')

        # Required fields
        expect(page.locator('input[name="name"]')).to_be_visible()
        expect(page.locator('select[name="species"]')).to_be_visible()

        # Optional fields
        expect(page.locator('input[name="breed"]')).to_be_visible()
        expect(page.locator('select[name="gender"]')).to_be_visible()
        expect(page.locator('input[name="date_of_birth"]')).to_be_visible()
        expect(page.locator('input[name="weight_kg"]')).to_be_visible()
        expect(page.locator('input[name="microchip_id"]')).to_be_visible()
        expect(page.locator('input[name="is_neutered"]')).to_be_visible()
        expect(page.locator('textarea[name="notes"]')).to_be_visible()

    def test_add_pet_successfully(self, authenticated_page, live_server, owner_user, db):
        """User can successfully add a pet."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pets/pets/add/')

        # Fill form
        page.fill('input[name="name"]', 'Luna')
        page.select_option('select[name="species"]', 'cat')
        page.fill('input[name="breed"]', 'Siamese')
        page.select_option('select[name="gender"]', 'female')
        page.fill('input[name="date_of_birth"]', '2022-04-10')
        page.fill('input[name="weight_kg"]', '4.2')

        # Submit
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # Should redirect to pet list
        expect(page).to_have_url(re.compile(r'.*/pets/pets.*'))

        # Pet should exist
        from apps.pets.models import Pet
        assert Pet.objects.filter(owner=owner_user, name='Luna').exists()

    def test_add_pet_with_notes(self, authenticated_page, live_server, owner_user, db):
        """User can add notes when creating pet."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pets/pets/add/')

        page.fill('input[name="name"]', 'Rocky')
        page.select_option('select[name="species"]', 'dog')
        page.fill('textarea[name="notes"]', 'Allergic to chicken')

        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        from apps.pets.models import Pet
        pet = Pet.objects.get(owner=owner_user, name='Rocky')
        assert 'Allergic to chicken' in pet.notes

    def test_add_pet_with_neutered_checkbox(self, authenticated_page, live_server, owner_user, db):
        """Neutered checkbox works correctly."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pets/pets/add/')

        page.fill('input[name="name"]', 'Spike')
        page.select_option('select[name="species"]', 'dog')
        page.check('input[name="is_neutered"]')

        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        from apps.pets.models import Pet
        pet = Pet.objects.get(owner=owner_user, name='Spike')
        assert pet.is_neutered is True

    def test_add_pet_validation_name_required(self, authenticated_page, live_server, db):
        """Form shows error if name is empty."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pets/pets/add/')

        # Don't fill name, just submit
        page.select_option('select[name="species"]', 'dog')
        page.click('button[type="submit"]')

        # Should stay on form with error
        # HTML5 validation will prevent submission
        expect(page.locator('input[name="name"]')).to_be_visible()

    def test_add_pet_cancel_button(self, authenticated_page, live_server, db):
        """Cancel button returns to pet list."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pets/pets/add/')

        page.click('a:has-text("Cancel")')
        page.wait_for_load_state('networkidle')

        expect(page).to_have_url(re.compile(r'.*/pets/pets.*'))


@pytest.mark.browser
class TestPetEdit:
    """Test pet editing."""

    def test_edit_pet_page_loads(self, authenticated_page, live_server, pet_with_records):
        """Edit pet page loads with current data."""
        page = authenticated_page
        pet = pet_with_records

        page.goto(f'{live_server.url}/pets/pets/{pet.pk}/edit/')

        expect(page.locator('h1')).to_contain_text('Edit')

        # Should have current values
        expect(page.locator('input[name="name"]')).to_have_value(pet.name)
        expect(page.locator('input[name="breed"]')).to_have_value(pet.breed)

    def test_edit_pet_successfully(self, authenticated_page, live_server, pet_with_records):
        """User can edit pet details."""
        page = authenticated_page
        pet = pet_with_records

        page.goto(f'{live_server.url}/pets/pets/{pet.pk}/edit/')

        # Change name
        page.fill('input[name="name"]', 'Maximus')
        page.fill('input[name="weight_kg"]', '30.0')

        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # Should redirect to pet detail
        expect(page).to_have_url(re.compile(rf'.*/pets/{pet.pk}.*'))

        # Pet should be updated
        pet.refresh_from_db()
        assert pet.name == 'Maximus'
        assert pet.weight_kg == Decimal('30.0')

    def test_edit_pet_change_species(self, authenticated_page, live_server, multiple_pets):
        """User can change pet species."""
        page = authenticated_page
        pet = multiple_pets[0]  # Buddy the dog

        page.goto(f'{live_server.url}/pets/pets/{pet.pk}/edit/')

        page.select_option('select[name="species"]', 'cat')

        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        pet.refresh_from_db()
        assert pet.species == 'cat'

    def test_edit_pet_cancel_returns_to_detail(self, authenticated_page, live_server, pet_with_records):
        """Cancel button returns to pet detail page."""
        page = authenticated_page
        pet = pet_with_records

        page.goto(f'{live_server.url}/pets/pets/{pet.pk}/edit/')

        page.click('a:has-text("Cancel")')
        page.wait_for_load_state('networkidle')

        expect(page).to_have_url(re.compile(rf'.*/pets/{pet.pk}.*'))


@pytest.mark.browser
class TestPetBreadcrumbs:
    """Test navigation breadcrumbs."""

    def test_pet_form_has_breadcrumbs(self, authenticated_page, live_server, db):
        """Pet form shows breadcrumb navigation."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pets/pets/add/')

        # Should show breadcrumb
        expect(page.locator('nav ol')).to_be_visible()
        expect(page.locator('a:has-text("Dashboard")')).to_be_visible()
        expect(page.locator('a:has-text("My Pets")')).to_be_visible()

    def test_pet_detail_has_breadcrumbs(self, authenticated_page, live_server, pet_with_records):
        """Pet detail shows breadcrumb navigation."""
        page = authenticated_page
        pet = pet_with_records

        page.goto(f'{live_server.url}/pets/pets/{pet.pk}/')

        expect(page.locator('nav ol')).to_be_visible()
        expect(page.locator('a:has-text("Dashboard")')).to_be_visible()
        expect(page.locator('a:has-text("My Pets")')).to_be_visible()

    def test_breadcrumb_dashboard_link_works(self, authenticated_page, live_server, pet_with_records):
        """Dashboard breadcrumb link navigates correctly."""
        page = authenticated_page
        pet = pet_with_records

        page.goto(f'{live_server.url}/pets/pets/{pet.pk}/')

        page.locator('a:has-text("Dashboard")').first.click()
        page.wait_for_load_state('networkidle')

        expect(page).to_have_url(re.compile(r'.*/pets/?$'))


@pytest.mark.browser
class TestMobilePetManagement:
    """Test pet management on mobile viewport."""

    def test_mobile_dashboard_loads(self, mobile_page, live_server, owner_user, multiple_pets):
        """Dashboard works on mobile."""
        page = mobile_page

        # Login
        page.goto(f'{live_server.url}/accounts/login/')
        page.fill('input[name="username"]', owner_user.email)
        page.fill('input[name="password"]', 'owner123')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        page.goto(f'{live_server.url}/pets/')

        # Should show pets
        for pet in multiple_pets:
            expect(page.locator(f'text={pet.name}')).to_be_visible()

    def test_mobile_pet_form(self, mobile_page, live_server, owner_user, db):
        """Pet form is usable on mobile."""
        page = mobile_page

        # Login
        page.goto(f'{live_server.url}/accounts/login/')
        page.fill('input[name="username"]', owner_user.email)
        page.fill('input[name="password"]', 'owner123')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        page.goto(f'{live_server.url}/pets/pets/add/')

        # Form should be visible and usable
        expect(page.locator('input[name="name"]')).to_be_visible()
        # Use more specific selector to exclude chat widget submit button
        expect(page.locator('main button[type="submit"]')).to_be_visible()

    def test_mobile_pet_detail(self, mobile_page, live_server, owner_user, pet_with_records):
        """Pet detail page works on mobile."""
        page = mobile_page
        pet = pet_with_records

        # Login
        page.goto(f'{live_server.url}/accounts/login/')
        page.fill('input[name="username"]', owner_user.email)
        page.fill('input[name="password"]', 'owner123')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        page.goto(f'{live_server.url}/pets/pets/{pet.pk}/')

        # Should show pet name
        expect(page.locator('h1')).to_contain_text(pet.name)

        # Edit button should be accessible (use first to handle multiple matches)
        expect(page.locator('a:has-text("Edit")').first).to_be_visible()
