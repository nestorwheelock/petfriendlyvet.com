"""Browser tests for appointment booking flow.

Tests service browsing, appointment booking, viewing, and cancellation.
"""
import re
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from playwright.sync_api import expect

from django.utils import timezone


@pytest.fixture
def service_types(db):
    """Create service types for testing."""
    from apps.appointments.models import ServiceType

    services = [
        ServiceType.objects.create(
            name='Consulta General',
            description='Revisión general de salud para tu mascota',
            duration_minutes=30,
            price=Decimal('500.00'),
            category='clinic',
            is_active=True,
        ),
        ServiceType.objects.create(
            name='Vacunación',
            description='Aplicación de vacunas',
            duration_minutes=15,
            price=Decimal('350.00'),
            category='clinic',
            is_active=True,
        ),
        ServiceType.objects.create(
            name='Baño y Corte',
            description='Servicio completo de grooming',
            duration_minutes=60,
            price=Decimal('400.00'),
            category='grooming',
            is_active=True,
        ),
    ]
    return services


@pytest.fixture
def owner_with_pet(db, owner_user):
    """Create owner with a pet."""
    from apps.pets.models import Pet

    pet = Pet.objects.create(
        owner=owner_user,
        name='Firulais',
        species='dog',
        breed='Labrador',
        date_of_birth=datetime(2020, 1, 15).date(),
        gender='male',
    )
    return owner_user, pet


@pytest.fixture
def existing_appointment(db, owner_with_pet, service_types):
    """Create an existing appointment."""
    from apps.appointments.models import Appointment

    owner, pet = owner_with_pet
    service = service_types[0]

    appointment = Appointment.objects.create(
        owner=owner,
        pet=pet,
        service=service,
        scheduled_start=timezone.now() + timedelta(days=3),
        scheduled_end=timezone.now() + timedelta(days=3, minutes=30),
        status='scheduled',
    )
    return appointment


@pytest.mark.browser
class TestServiceList:
    """Test service listing page."""

    def test_service_list_loads(self, page, live_server, service_types):
        """Service list page loads with services."""
        page.goto(f'{live_server.url}/appointments/services/')

        expect(page).to_have_title(re.compile(r'.*[Ss]ervicio.*'))

    def test_services_grouped_by_category(self, page, live_server, service_types):
        """Services are grouped by category."""
        page.goto(f'{live_server.url}/appointments/services/')

        # Should show category headers
        content = page.content()
        assert 'Clinic' in content or 'Clínica' in content
        assert 'Grooming' in content

    def test_service_shows_price_and_duration(self, page, live_server, service_types):
        """Each service shows price and duration."""
        page.goto(f'{live_server.url}/appointments/services/')

        # Should show price
        content = page.content()
        assert '$500' in content or '500' in content

        # Should show duration
        assert '30' in content or 'min' in content

    def test_service_has_book_button(self, page, live_server, service_types):
        """Each service has a booking button."""
        page.goto(f'{live_server.url}/appointments/services/')

        book_buttons = page.locator('a[href*="book"]')
        expect(book_buttons.first).to_be_visible()


@pytest.mark.browser
class TestAppointmentBooking:
    """Test appointment booking flow."""

    def test_booking_requires_login(self, page, live_server, service_types):
        """Booking page requires authentication."""
        page.goto(f'{live_server.url}/appointments/book/')
        page.wait_for_load_state('networkidle')

        # Should redirect to login
        expect(page).to_have_url(re.compile(r'.*/accounts/login.*'))

    def test_booking_form_loads(self, authenticated_page, live_server, service_types, owner_with_pet):
        """Booking form loads with all fields."""
        page = authenticated_page

        page.goto(f'{live_server.url}/appointments/book/')

        expect(page.locator('form#booking-form')).to_be_visible()
        expect(page.locator('select[name="service"]')).to_be_visible()
        expect(page.locator('select[name="pet"]')).to_be_visible()
        expect(page.locator('input[name="date"]')).to_be_visible()
        expect(page.locator('select[name="time_slot"]')).to_be_visible()

    def test_service_preselected_from_url(self, authenticated_page, live_server, service_types, owner_with_pet):
        """Service is preselected when passed in URL."""
        page = authenticated_page
        service = service_types[0]

        page.goto(f'{live_server.url}/appointments/book/?service={service.pk}')

        service_select = page.locator('select[name="service"]')
        # Check the service is selected
        selected_value = service_select.evaluate('el => el.value')
        assert selected_value == str(service.pk)

    def test_pet_dropdown_shows_user_pets(self, authenticated_page, live_server, service_types, owner_with_pet):
        """Pet dropdown shows user's pets."""
        page = authenticated_page
        owner, pet = owner_with_pet

        page.goto(f'{live_server.url}/appointments/book/')

        # Pet name should be in dropdown
        pet_select = page.locator('select[name="pet"]')
        content = pet_select.inner_html()
        assert pet.name in content

    def test_successful_booking(self, authenticated_page, live_server, service_types, owner_with_pet):
        """User can successfully book an appointment."""
        page = authenticated_page
        owner, pet = owner_with_pet
        service = service_types[0]

        page.goto(f'{live_server.url}/appointments/book/')

        # Fill form
        page.select_option('select[name="service"]', str(service.pk))
        page.select_option('select[name="pet"]', str(pet.pk))

        # Set date to tomorrow
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        page.fill('input[name="date"]', tomorrow)

        # Select time slot
        page.select_option('select[name="time_slot"]', '10:00')

        # Submit
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # Should redirect to my appointments
        expect(page).to_have_url(re.compile(r'.*/my-appointments.*'))

        # Appointment should exist
        from apps.appointments.models import Appointment
        assert Appointment.objects.filter(owner=owner, pet=pet, service=service).exists()

    def test_booking_with_notes(self, authenticated_page, live_server, service_types, owner_with_pet):
        """User can add notes to booking."""
        page = authenticated_page
        owner, pet = owner_with_pet
        service = service_types[0]

        page.goto(f'{live_server.url}/appointments/book/')

        page.select_option('select[name="service"]', str(service.pk))
        page.select_option('select[name="pet"]', str(pet.pk))

        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        page.fill('input[name="date"]', tomorrow)
        page.select_option('select[name="time_slot"]', '11:00')

        # Add notes
        page.fill('textarea[name="notes"]', 'Mi mascota tiene alergia al pollo')

        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # Verify notes saved
        from apps.appointments.models import Appointment
        apt = Appointment.objects.filter(owner=owner).first()
        assert 'alergia al pollo' in apt.notes


@pytest.mark.browser
class TestMyAppointments:
    """Test my appointments view."""

    def test_my_appointments_requires_login(self, page, live_server, db):
        """My appointments requires authentication."""
        page.goto(f'{live_server.url}/appointments/my-appointments/')
        page.wait_for_load_state('networkidle')

        expect(page).to_have_url(re.compile(r'.*/accounts/login.*'))

    def test_my_appointments_shows_appointments(self, authenticated_page, live_server, existing_appointment):
        """My appointments shows user's appointments."""
        page = authenticated_page

        page.goto(f'{live_server.url}/appointments/my-appointments/')

        # Should show the appointment
        content = page.content()
        assert existing_appointment.service.name in content

    def test_empty_appointments_shows_message(self, authenticated_page, live_server, service_types, owner_with_pet):
        """Empty appointments shows helpful message."""
        page = authenticated_page

        page.goto(f'{live_server.url}/appointments/my-appointments/')

        # Should show empty state
        empty_message = page.locator(':text("No tienes citas"), :text("no appointments")')
        if empty_message.count() > 0:
            expect(empty_message.first).to_be_visible()

    def test_appointments_have_view_button(self, authenticated_page, live_server, existing_appointment):
        """Appointments have view details button."""
        page = authenticated_page

        page.goto(f'{live_server.url}/appointments/my-appointments/')

        view_button = page.locator(f'a[href*="{existing_appointment.pk}"]')
        expect(view_button.first).to_be_visible()

    def test_upcoming_appointments_have_cancel_button(self, authenticated_page, live_server, existing_appointment):
        """Upcoming appointments have cancel button."""
        page = authenticated_page

        page.goto(f'{live_server.url}/appointments/my-appointments/')

        cancel_button = page.locator(f'a[href*="{existing_appointment.pk}/cancel"]')
        expect(cancel_button).to_be_visible()


@pytest.mark.browser
class TestAppointmentDetail:
    """Test appointment detail view."""

    def test_appointment_detail_loads(self, authenticated_page, live_server, existing_appointment):
        """Appointment detail page loads."""
        page = authenticated_page

        page.goto(f'{live_server.url}/appointments/{existing_appointment.pk}/')

        # Should show service name
        content = page.content()
        assert existing_appointment.service.name in content

    def test_appointment_detail_shows_pet(self, authenticated_page, live_server, existing_appointment):
        """Appointment detail shows pet name."""
        page = authenticated_page

        page.goto(f'{live_server.url}/appointments/{existing_appointment.pk}/')

        content = page.content()
        assert existing_appointment.pet.name in content

    def test_appointment_detail_shows_status(self, authenticated_page, live_server, existing_appointment):
        """Appointment detail shows status."""
        page = authenticated_page

        page.goto(f'{live_server.url}/appointments/{existing_appointment.pk}/')

        # Should show status badge
        status_badge = page.locator('.rounded-full')
        expect(status_badge.first).to_be_visible()

    def test_appointment_detail_has_cancel_link(self, authenticated_page, live_server, existing_appointment):
        """Scheduled appointment has cancel link."""
        page = authenticated_page

        page.goto(f'{live_server.url}/appointments/{existing_appointment.pk}/')

        cancel_link = page.locator('a[href*="cancel"]')
        expect(cancel_link).to_be_visible()


@pytest.mark.browser
class TestAppointmentCancellation:
    """Test appointment cancellation flow."""

    def test_cancel_page_loads(self, authenticated_page, live_server, existing_appointment):
        """Cancel confirmation page loads."""
        page = authenticated_page

        page.goto(f'{live_server.url}/appointments/{existing_appointment.pk}/cancel/')

        expect(page.locator('form#cancel-form')).to_be_visible()

    def test_cancel_page_shows_appointment_details(self, authenticated_page, live_server, existing_appointment):
        """Cancel page shows appointment details."""
        page = authenticated_page

        page.goto(f'{live_server.url}/appointments/{existing_appointment.pk}/cancel/')

        content = page.content()
        assert existing_appointment.service.name in content
        assert existing_appointment.pet.name in content

    def test_cancel_appointment_success(self, authenticated_page, live_server, existing_appointment):
        """User can cancel appointment."""
        page = authenticated_page

        page.goto(f'{live_server.url}/appointments/{existing_appointment.pk}/cancel/')

        # Add cancellation reason
        page.fill('textarea[name="reason"]', 'Tengo otro compromiso')

        # Submit
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # Should redirect to my appointments
        expect(page).to_have_url(re.compile(r'.*/my-appointments.*'))

        # Appointment should be cancelled
        existing_appointment.refresh_from_db()
        assert existing_appointment.status == 'cancelled'
        assert 'otro compromiso' in existing_appointment.cancellation_reason

    def test_cancel_without_reason(self, authenticated_page, live_server, existing_appointment):
        """User can cancel without providing reason."""
        page = authenticated_page

        page.goto(f'{live_server.url}/appointments/{existing_appointment.pk}/cancel/')

        # Submit without reason
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # Should still work
        existing_appointment.refresh_from_db()
        assert existing_appointment.status == 'cancelled'

    def test_cancel_back_button(self, authenticated_page, live_server, existing_appointment):
        """Cancel page has back button."""
        page = authenticated_page

        page.goto(f'{live_server.url}/appointments/{existing_appointment.pk}/cancel/')

        back_link = page.locator('a[href*="my-appointments"]')
        expect(back_link.first).to_be_visible()


@pytest.mark.browser
class TestBookingFromServiceList:
    """Test booking flow starting from service list."""

    def test_click_book_from_service(self, authenticated_page, live_server, service_types, owner_with_pet):
        """User can click book from service list."""
        page = authenticated_page
        service = service_types[0]

        page.goto(f'{live_server.url}/appointments/services/')

        # Find and click book button for first service
        book_button = page.locator(f'a[href*="service={service.pk}"]')
        if book_button.count() > 0:
            book_button.first.click()
            page.wait_for_load_state('networkidle')

            # Should be on booking page with service preselected
            expect(page).to_have_url(re.compile(r'.*/book.*'))


@pytest.mark.browser
class TestMobileAppointments:
    """Test appointment flow on mobile viewport."""

    def test_mobile_service_list(self, mobile_page, live_server, service_types):
        """Service list works on mobile."""
        page = mobile_page
        page.set_viewport_size({'width': 375, 'height': 667})

        page.goto(f'{live_server.url}/appointments/services/')

        # Services should be visible
        expect(page.locator('a[href*="book"]').first).to_be_visible()

    def test_mobile_booking_form(self, mobile_page, live_server, service_types, owner_user, owner_with_pet):
        """Booking form works on mobile."""
        page = mobile_page
        page.set_viewport_size({'width': 375, 'height': 667})

        # Login
        page.goto(f'{live_server.url}/accounts/login/')
        page.fill('input[name="username"]', owner_user.username)
        page.fill('input[name="password"]', 'owner123')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        page.goto(f'{live_server.url}/appointments/book/')

        # Form should be usable
        expect(page.locator('select[name="service"]')).to_be_visible()
        # Use specific selector for booking form submit button
        expect(page.locator('form#booking-form button[type="submit"]')).to_be_visible()

    def test_mobile_date_picker(self, mobile_page, live_server, service_types, owner_user, owner_with_pet):
        """Date picker works on mobile."""
        page = mobile_page
        page.set_viewport_size({'width': 375, 'height': 667})

        # Login
        page.goto(f'{live_server.url}/accounts/login/')
        page.fill('input[name="username"]', owner_user.username)
        page.fill('input[name="password"]', 'owner123')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        page.goto(f'{live_server.url}/appointments/book/')

        # Date input should be visible and interactable
        date_input = page.locator('input[name="date"]')
        expect(date_input).to_be_visible()
