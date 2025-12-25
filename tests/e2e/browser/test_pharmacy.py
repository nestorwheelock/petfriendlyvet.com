"""Browser tests for pharmacy and prescription management.

Tests prescription viewing, refill requests, and pharmacy workflows.
"""
import re
from datetime import datetime, timedelta, date
from decimal import Decimal

import pytest
from playwright.sync_api import expect


@pytest.fixture
def medication(db):
    """Create a medication."""
    from apps.pharmacy.models import Medication

    med = Medication.objects.create(
        name='Amoxicillin',
        name_es='Amoxicilina',
        generic_name='Amoxicillin',
        drug_class='Antibiotic',
        is_controlled=False,
        requires_prescription=True,
        dosage_forms=['capsule', 'liquid'],
        strengths=['250mg', '500mg'],
        is_active=True,
    )
    return med


@pytest.fixture
def controlled_medication(db):
    """Create a controlled substance medication."""
    from apps.pharmacy.models import Medication

    med = Medication.objects.create(
        name='Tramadol',
        name_es='Tramadol',
        generic_name='Tramadol',
        drug_class='Opioid analgesic',
        schedule='IV',
        is_controlled=True,
        requires_prescription=True,
        dosage_forms=['tablet'],
        strengths=['50mg', '100mg'],
        is_active=True,
    )
    return med


@pytest.fixture
def staff_profile(db, staff_user):
    """Create staff profile for prescribing vet."""
    from apps.practice.models import StaffProfile

    profile = StaffProfile.objects.create(
        user=staff_user,
        role='veterinarian',
        title='Dr. Staff',
        can_prescribe=True,
    )
    return profile


@pytest.fixture
def pet_for_prescription(db, owner_user):
    """Create a pet for prescriptions."""
    from apps.pets.models import Pet

    pet = Pet.objects.create(
        owner=owner_user,
        name='Rocky',
        species='dog',
        breed='Beagle',
        gender='male',
        date_of_birth=datetime(2019, 5, 15).date(),
    )
    return pet


@pytest.fixture
def active_prescription(db, owner_user, pet_for_prescription, medication, staff_profile):
    """Create an active prescription with refills available."""
    from apps.pharmacy.models import Prescription

    prescription = Prescription.objects.create(
        owner=owner_user,
        pet=pet_for_prescription,
        prescribing_vet=staff_profile,
        medication=medication,
        strength='250mg',
        dosage_form='capsule',
        quantity=30,
        dosage='1 capsule',
        frequency='twice daily',
        duration='14 days',
        instructions='Give with food to prevent stomach upset',
        refills_authorized=3,
        refills_remaining=2,
        prescribed_date=date.today() - timedelta(days=7),
        expiration_date=date.today() + timedelta(days=358),
        status='active',
    )
    return prescription


@pytest.fixture
def expired_prescription(db, owner_user, pet_for_prescription, medication, staff_profile):
    """Create an expired prescription."""
    from apps.pharmacy.models import Prescription

    prescription = Prescription.objects.create(
        owner=owner_user,
        pet=pet_for_prescription,
        prescribing_vet=staff_profile,
        medication=medication,
        strength='500mg',
        dosage_form='capsule',
        quantity=20,
        dosage='1 capsule',
        frequency='once daily',
        duration='20 days',
        refills_authorized=2,
        refills_remaining=1,
        prescribed_date=date.today() - timedelta(days=400),
        expiration_date=date.today() - timedelta(days=35),
        status='expired',
    )
    return prescription


@pytest.fixture
def controlled_prescription(db, owner_user, pet_for_prescription, controlled_medication, staff_profile):
    """Create a controlled substance prescription."""
    from apps.pharmacy.models import Prescription

    prescription = Prescription.objects.create(
        owner=owner_user,
        pet=pet_for_prescription,
        prescribing_vet=staff_profile,
        medication=controlled_medication,
        strength='50mg',
        dosage_form='tablet',
        quantity=20,
        dosage='1 tablet',
        frequency='every 8 hours as needed',
        duration='5 days',
        refills_authorized=0,
        refills_remaining=0,
        prescribed_date=date.today() - timedelta(days=2),
        expiration_date=date.today() + timedelta(days=28),
        status='active',
        dea_number='AB1234567',
    )
    return prescription


@pytest.fixture
def prescription_with_fills(db, active_prescription, staff_profile):
    """Create a prescription with fill history."""
    from apps.pharmacy.models import PrescriptionFill

    # Original fill
    fill1 = PrescriptionFill.objects.create(
        prescription=active_prescription,
        fill_number=0,
        quantity_dispensed=30,
        dispensed_by=staff_profile,
        status='picked_up',
        fulfillment_method='pickup',
    )

    # First refill
    fill2 = PrescriptionFill.objects.create(
        prescription=active_prescription,
        fill_number=1,
        quantity_dispensed=30,
        dispensed_by=staff_profile,
        status='delivered',
        fulfillment_method='delivery',
    )

    return active_prescription, [fill1, fill2]


@pytest.fixture
def refill_request(db, active_prescription, owner_user):
    """Create a pending refill request."""
    from apps.pharmacy.models import RefillRequest

    request = RefillRequest.objects.create(
        prescription=active_prescription,
        requested_by=owner_user,
        notes='Need this refilled soon, running low',
        status='pending',
    )
    return request


@pytest.mark.browser
class TestPrescriptionList:
    """Test prescription list page."""

    def test_prescription_list_requires_login(self, page, live_server, db):
        """Prescription list requires authentication."""
        page.goto(f'{live_server.url}/pharmacy/prescriptions/')
        page.wait_for_load_state('networkidle')

        expect(page).to_have_url(re.compile(r'.*/accounts/login.*'))

    def test_prescription_list_loads(self, authenticated_page, live_server, db):
        """Prescription list page loads."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pharmacy/prescriptions/')

        expect(page).to_have_title(re.compile(r'.*[Pp]rescription.*'))
        expect(page.locator('h1')).to_contain_text('Prescriptions')

    def test_prescription_list_shows_prescriptions(self, authenticated_page, live_server, active_prescription):
        """Prescription list shows user's prescriptions."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pharmacy/prescriptions/')

        # Should show medication name
        expect(page.locator(f'text={active_prescription.medication.name}')).to_be_visible()

        # Should show pet name
        expect(page.locator(f'text={active_prescription.pet.name}')).to_be_visible()

    def test_prescription_list_shows_dosage_info(self, authenticated_page, live_server, active_prescription):
        """Prescription list shows dosage and frequency."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pharmacy/prescriptions/')

        content = page.content()
        assert active_prescription.dosage in content
        assert active_prescription.frequency in content

    def test_prescription_list_shows_active_status(self, authenticated_page, live_server, active_prescription):
        """Active prescriptions show Active badge."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pharmacy/prescriptions/')

        # Check for active status indicator (text or badge)
        content = page.content()
        assert 'Active' in content or 'Activ' in content

    def test_prescription_list_shows_expired_status(self, authenticated_page, live_server, expired_prescription):
        """Expired prescriptions show Expired badge."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pharmacy/prescriptions/')

        expired_badge = page.locator('.rounded-full:has-text("Expired")')
        expect(expired_badge.first).to_be_visible()

    def test_prescription_list_shows_refills_remaining(self, authenticated_page, live_server, active_prescription):
        """Prescription list shows refills remaining."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pharmacy/prescriptions/')

        refills_text = page.locator(f'text={active_prescription.refills_remaining}')
        expect(refills_text.first).to_be_visible()

    def test_prescription_list_empty_state(self, authenticated_page, live_server, db):
        """Empty prescription list shows message."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pharmacy/prescriptions/')

        empty_message = page.locator('text=No prescriptions')
        expect(empty_message.first).to_be_visible()

    def test_prescription_list_has_refill_list_link(self, authenticated_page, live_server, db):
        """Prescription list has link to refill requests."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pharmacy/prescriptions/')

        refill_link = page.locator('a[href*="refill"]:has-text("Refill")')
        expect(refill_link.first).to_be_visible()

    def test_prescription_click_goes_to_detail(self, authenticated_page, live_server, active_prescription):
        """Clicking prescription goes to detail page."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pharmacy/prescriptions/')

        page.locator(f'a[href*="{active_prescription.pk}"]').first.click()
        page.wait_for_load_state('networkidle')

        expect(page).to_have_url(re.compile(rf'.*/prescriptions/{active_prescription.pk}.*'))


@pytest.mark.browser
class TestPrescriptionDetail:
    """Test prescription detail page."""

    def test_prescription_detail_loads(self, authenticated_page, live_server, active_prescription):
        """Prescription detail page loads."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pharmacy/prescriptions/{active_prescription.pk}/')

        expect(page.locator('h1')).to_contain_text(active_prescription.medication.name)

    def test_prescription_detail_shows_strength(self, authenticated_page, live_server, active_prescription):
        """Prescription detail shows strength and form."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pharmacy/prescriptions/{active_prescription.pk}/')

        content = page.content()
        assert active_prescription.strength in content
        assert active_prescription.dosage_form in content

    def test_prescription_detail_shows_pet_name(self, authenticated_page, live_server, active_prescription):
        """Prescription detail shows pet name."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pharmacy/prescriptions/{active_prescription.pk}/')

        expect(page.locator(f'text={active_prescription.pet.name}')).to_be_visible()

    def test_prescription_detail_shows_dosage_info(self, authenticated_page, live_server, active_prescription):
        """Prescription detail shows dosage, frequency, duration."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pharmacy/prescriptions/{active_prescription.pk}/')

        content = page.content()
        assert active_prescription.dosage in content
        assert active_prescription.frequency in content
        assert active_prescription.duration in content

    def test_prescription_detail_shows_quantity(self, authenticated_page, live_server, active_prescription):
        """Prescription detail shows quantity."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pharmacy/prescriptions/{active_prescription.pk}/')

        expect(page.locator(f'text={active_prescription.quantity}')).to_be_visible()

    def test_prescription_detail_shows_instructions(self, authenticated_page, live_server, active_prescription):
        """Prescription detail shows instructions."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pharmacy/prescriptions/{active_prescription.pk}/')

        expect(page.locator('text=Give with food')).to_be_visible()

    def test_prescription_detail_shows_refills_info(self, authenticated_page, live_server, active_prescription):
        """Prescription detail shows refills remaining of authorized."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pharmacy/prescriptions/{active_prescription.pk}/')

        content = page.content()
        assert str(active_prescription.refills_remaining) in content
        assert str(active_prescription.refills_authorized) in content

    def test_prescription_detail_has_refill_button(self, authenticated_page, live_server, active_prescription):
        """Active prescription with refills has Request Refill button."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pharmacy/prescriptions/{active_prescription.pk}/')

        refill_button = page.locator('a:has-text("Request Refill")')
        expect(refill_button).to_be_visible()

    def test_prescription_detail_no_refill_for_expired(self, authenticated_page, live_server, expired_prescription):
        """Expired prescription does not have refill button."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pharmacy/prescriptions/{expired_prescription.pk}/')

        refill_button = page.locator('a:has-text("Request Refill")')
        expect(refill_button).to_have_count(0)

    def test_prescription_detail_controlled_substance_warning(self, authenticated_page, live_server, controlled_prescription):
        """Controlled substance shows warning message."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pharmacy/prescriptions/{controlled_prescription.pk}/')

        warning = page.locator('text=Controlled Substance')
        expect(warning).to_be_visible()

    def test_prescription_detail_back_link(self, authenticated_page, live_server, active_prescription):
        """Prescription detail has back link to list."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pharmacy/prescriptions/{active_prescription.pk}/')

        back_link = page.locator('a:has-text("Back to Prescriptions")')
        expect(back_link).to_be_visible()

    def test_prescription_detail_back_link_works(self, authenticated_page, live_server, active_prescription):
        """Back link navigates to prescription list."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pharmacy/prescriptions/{active_prescription.pk}/')

        page.locator('a:has-text("Back to Prescriptions")').click()
        page.wait_for_load_state('networkidle')

        expect(page).to_have_url(re.compile(r'.*/prescriptions/$'))


@pytest.mark.browser
class TestPrescriptionFillHistory:
    """Test prescription fill history display."""

    def test_prescription_shows_fill_history(self, authenticated_page, live_server, prescription_with_fills):
        """Prescription detail shows fill history."""
        page = authenticated_page
        prescription, fills = prescription_with_fills

        page.goto(f'{live_server.url}/pharmacy/prescriptions/{prescription.pk}/')

        expect(page.locator('h2:has-text("Fill History")')).to_be_visible()

    def test_fill_history_shows_fill_numbers(self, authenticated_page, live_server, prescription_with_fills):
        """Fill history shows fill numbers."""
        page = authenticated_page
        prescription, fills = prescription_with_fills

        page.goto(f'{live_server.url}/pharmacy/prescriptions/{prescription.pk}/')

        expect(page.locator('text=Fill #0')).to_be_visible()
        expect(page.locator('text=Fill #1')).to_be_visible()

    def test_fill_history_shows_status(self, authenticated_page, live_server, prescription_with_fills):
        """Fill history shows fill status."""
        page = authenticated_page
        prescription, fills = prescription_with_fills

        page.goto(f'{live_server.url}/pharmacy/prescriptions/{prescription.pk}/')

        # Should show status badges
        expect(page.locator('.rounded-full:has-text("Picked Up")')).to_be_visible()


@pytest.mark.browser
class TestRefillRequest:
    """Test refill request workflow."""

    def test_refill_request_page_loads(self, authenticated_page, live_server, active_prescription):
        """Refill request page loads."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pharmacy/prescriptions/{active_prescription.pk}/refill/')

        expect(page.locator('h1')).to_contain_text('Request Refill')

    def test_refill_request_shows_prescription_summary(self, authenticated_page, live_server, active_prescription):
        """Refill request shows prescription summary."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pharmacy/prescriptions/{active_prescription.pk}/refill/')

        content = page.content()
        assert active_prescription.medication.name in content
        assert active_prescription.pet.name in content

    def test_refill_request_shows_refills_remaining(self, authenticated_page, live_server, active_prescription):
        """Refill request shows refills remaining."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pharmacy/prescriptions/{active_prescription.pk}/refill/')

        # Page should contain refills remaining info
        content = page.content()
        assert str(active_prescription.refills_remaining) in content

    def test_refill_request_has_notes_field(self, authenticated_page, live_server, active_prescription):
        """Refill request form has notes field."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pharmacy/prescriptions/{active_prescription.pk}/refill/')

        expect(page.locator('textarea[name="notes"]')).to_be_visible()

    def test_refill_request_submit_successfully(self, authenticated_page, live_server, active_prescription, owner_user):
        """User can submit refill request."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pharmacy/prescriptions/{active_prescription.pk}/refill/')

        # Add notes
        page.fill('textarea[name="notes"]', 'Need this urgently, running low')

        # Submit
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # Should redirect to refill list
        expect(page).to_have_url(re.compile(r'.*/refills.*'))

        # Refill request should exist
        from apps.pharmacy.models import RefillRequest
        assert RefillRequest.objects.filter(
            prescription=active_prescription,
            requested_by=owner_user
        ).exists()

    def test_refill_request_cancel_button(self, authenticated_page, live_server, active_prescription):
        """Cancel button returns to prescription detail."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pharmacy/prescriptions/{active_prescription.pk}/refill/')

        page.click('a:has-text("Cancel")')
        page.wait_for_load_state('networkidle')

        expect(page).to_have_url(re.compile(rf'.*/prescriptions/{active_prescription.pk}.*'))

    def test_refill_request_back_link(self, authenticated_page, live_server, active_prescription):
        """Refill request has back link to prescription."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pharmacy/prescriptions/{active_prescription.pk}/refill/')

        back_link = page.locator('a:has-text("Back to Prescription")')
        expect(back_link).to_be_visible()


@pytest.mark.browser
class TestRefillList:
    """Test refill request list page."""

    def test_refill_list_loads(self, authenticated_page, live_server, db):
        """Refill list page loads."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pharmacy/refills/')

        expect(page.locator('h1')).to_contain_text('Refill')

    def test_refill_list_shows_requests(self, authenticated_page, live_server, refill_request):
        """Refill list shows user's refill requests."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pharmacy/refills/')

        # Should show medication name
        expect(page.locator(f'text={refill_request.prescription.medication.name}')).to_be_visible()

    def test_refill_list_shows_status(self, authenticated_page, live_server, refill_request):
        """Refill list shows request status."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pharmacy/refills/')

        status_badge = page.locator('.rounded-full:has-text("Pending")')
        expect(status_badge.first).to_be_visible()

    def test_refill_list_shows_pet_name(self, authenticated_page, live_server, refill_request):
        """Refill list shows pet name."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pharmacy/refills/')

        expect(page.locator(f'text={refill_request.prescription.pet.name}')).to_be_visible()


@pytest.mark.browser
class TestRefillDetail:
    """Test refill request detail page."""

    def test_refill_detail_loads(self, authenticated_page, live_server, refill_request):
        """Refill detail page loads."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pharmacy/refills/{refill_request.pk}/')

        # Medication name should be on the page (may appear multiple times)
        expect(page.locator(f'text={refill_request.prescription.medication.name}').first).to_be_visible()

    def test_refill_detail_shows_notes(self, authenticated_page, live_server, refill_request):
        """Refill detail shows notes."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pharmacy/refills/{refill_request.pk}/')

        expect(page.locator('text=running low')).to_be_visible()

    def test_refill_detail_shows_status(self, authenticated_page, live_server, refill_request):
        """Refill detail shows status."""
        page = authenticated_page

        page.goto(f'{live_server.url}/pharmacy/refills/{refill_request.pk}/')

        status_badge = page.locator('.rounded-full:has-text("Pending")')
        expect(status_badge.first).to_be_visible()


@pytest.mark.browser
class TestMobilePharmacy:
    """Test pharmacy on mobile viewport."""

    def test_mobile_prescription_list(self, mobile_page, live_server, owner_user, active_prescription):
        """Prescription list works on mobile."""
        page = mobile_page

        # Login
        page.goto(f'{live_server.url}/accounts/login/')
        page.fill('input[name="username"]', owner_user.email)
        page.fill('input[name="password"]', 'owner123')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        page.goto(f'{live_server.url}/pharmacy/prescriptions/')

        # Should show prescriptions
        expect(page.locator(f'text={active_prescription.medication.name}')).to_be_visible()

    def test_mobile_prescription_detail(self, mobile_page, live_server, owner_user, active_prescription):
        """Prescription detail works on mobile."""
        page = mobile_page

        # Login
        page.goto(f'{live_server.url}/accounts/login/')
        page.fill('input[name="username"]', owner_user.email)
        page.fill('input[name="password"]', 'owner123')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        page.goto(f'{live_server.url}/pharmacy/prescriptions/{active_prescription.pk}/')

        # Should show medication name
        expect(page.locator('h1')).to_contain_text(active_prescription.medication.name)

        # Refill button should be visible
        expect(page.locator('a:has-text("Request Refill")')).to_be_visible()

    def test_mobile_refill_form(self, mobile_page, live_server, owner_user, active_prescription):
        """Refill form works on mobile."""
        page = mobile_page

        # Login
        page.goto(f'{live_server.url}/accounts/login/')
        page.fill('input[name="username"]', owner_user.email)
        page.fill('input[name="password"]', 'owner123')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        page.goto(f'{live_server.url}/pharmacy/prescriptions/{active_prescription.pk}/refill/')

        # Form should be usable (exclude chat widget submit button)
        expect(page.locator('textarea[name="notes"]')).to_be_visible()
        expect(page.locator('main button[type="submit"]')).to_be_visible()
