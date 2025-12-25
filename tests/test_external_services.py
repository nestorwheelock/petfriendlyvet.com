"""
Tests for External Services (S-021)

Tests cover:
- External partner directory
- Referral tracking
- Partner recommendations
"""
import pytest
from datetime import date, timedelta
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


# =============================================================================
# External Partner Model Tests
# =============================================================================

@pytest.mark.django_db
class TestExternalPartnerModel:
    """Tests for the ExternalPartner model."""

    def test_create_grooming_partner(self):
        """Can create a grooming partner."""
        from apps.services.models import ExternalPartner

        partner = ExternalPartner.objects.create(
            name='Happy Paws Grooming',
            partner_type='grooming',
            contact_name='Maria Garcia',
            phone='998-123-4567',
            email='contact@happypaws.com',
            address='Av. Principal 123, Puerto Morelos',
            description='Professional pet grooming services'
        )

        assert partner.pk is not None
        assert partner.partner_type == 'grooming'
        assert partner.is_active is True

    def test_create_boarding_partner(self):
        """Can create a boarding partner."""
        from apps.services.models import ExternalPartner

        partner = ExternalPartner.objects.create(
            name='Pet Paradise Boarding',
            partner_type='boarding',
            contact_name='Juan Lopez',
            phone='998-987-6543',
            email='info@petparadise.com',
            description='Safe and comfortable boarding for your pets'
        )

        assert partner.pk is not None
        assert partner.partner_type == 'boarding'

    def test_partner_str(self):
        """Partner string representation."""
        from apps.services.models import ExternalPartner

        partner = ExternalPartner.objects.create(
            name='Test Partner',
            partner_type='grooming'
        )

        assert 'Test Partner' in str(partner)

    def test_partner_types(self):
        """All partner types are valid."""
        from apps.services.models import ExternalPartner, PARTNER_TYPES

        for partner_type, _ in PARTNER_TYPES:
            partner = ExternalPartner.objects.create(
                name=f'Test {partner_type}',
                partner_type=partner_type
            )
            assert partner.partner_type == partner_type


# =============================================================================
# Referral Model Tests
# =============================================================================

@pytest.mark.django_db
class TestReferralModel:
    """Tests for the Referral model."""

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
    def partner(self):
        from apps.services.models import ExternalPartner
        return ExternalPartner.objects.create(
            name='Happy Paws Grooming',
            partner_type='grooming',
            phone='998-123-4567'
        )

    def test_create_referral(self, pet, partner, owner):
        """Can create a referral."""
        from apps.services.models import Referral

        referral = Referral.objects.create(
            pet=pet,
            partner=partner,
            referred_by=owner,
            service_type='grooming',
            notes='Regular grooming appointment'
        )

        assert referral.pk is not None
        assert referral.status == 'pending'

    def test_referral_str(self, pet, partner, owner):
        """Referral string representation."""
        from apps.services.models import Referral

        referral = Referral.objects.create(
            pet=pet,
            partner=partner,
            referred_by=owner,
            service_type='grooming'
        )

        assert pet.name in str(referral)
        assert partner.name in str(referral)

    def test_complete_referral(self, pet, partner, owner):
        """Can complete a referral with feedback."""
        from apps.services.models import Referral

        referral = Referral.objects.create(
            pet=pet,
            partner=partner,
            referred_by=owner,
            service_type='grooming'
        )

        referral.status = 'completed'
        referral.feedback = 'Excellent service!'
        referral.rating = 5
        referral.save()

        referral.refresh_from_db()
        assert referral.status == 'completed'
        assert referral.rating == 5


# =============================================================================
# Partner Directory View Tests
# =============================================================================

@pytest.mark.django_db
class TestPartnerDirectoryViews:
    """Tests for partner directory views."""

    @pytest.fixture
    def owner(self):
        return User.objects.create_user(
            username='petowner',
            email='owner@example.com',
            password='testpass123',
            role='owner'
        )

    @pytest.fixture
    def partners(self):
        from apps.services.models import ExternalPartner

        partners = []
        partners.append(ExternalPartner.objects.create(
            name='Happy Paws Grooming',
            partner_type='grooming',
            phone='998-123-4567',
            is_active=True
        ))
        partners.append(ExternalPartner.objects.create(
            name='Pet Paradise Boarding',
            partner_type='boarding',
            phone='998-987-6543',
            is_active=True
        ))
        partners.append(ExternalPartner.objects.create(
            name='Inactive Partner',
            partner_type='grooming',
            is_active=False
        ))
        return partners

    def test_partner_list_requires_login(self, client):
        """Partner list requires authentication."""
        url = reverse('services:partner_list')
        response = client.get(url)
        assert response.status_code == 302

    def test_partner_list_shows_active_partners(self, client, owner, partners):
        """Shows only active partners."""
        client.force_login(owner)
        url = reverse('services:partner_list')
        response = client.get(url)

        assert response.status_code == 200
        assert b'Happy Paws Grooming' in response.content
        assert b'Pet Paradise Boarding' in response.content
        assert b'Inactive Partner' not in response.content

    def test_filter_partners_by_type(self, client, owner, partners):
        """Can filter partners by type."""
        client.force_login(owner)
        url = reverse('services:partner_list')
        response = client.get(url, {'type': 'grooming'})

        assert response.status_code == 200
        assert b'Happy Paws Grooming' in response.content
        assert b'Pet Paradise Boarding' not in response.content

    def test_partner_detail_view(self, client, owner, partners):
        """Can view partner details."""
        client.force_login(owner)
        partner = partners[0]
        url = reverse('services:partner_detail', kwargs={'pk': partner.pk})
        response = client.get(url)

        assert response.status_code == 200
        assert b'Happy Paws Grooming' in response.content


# =============================================================================
# Referral View Tests
# =============================================================================

@pytest.mark.django_db
class TestReferralViews:
    """Tests for referral views."""

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
    def partner(self):
        from apps.services.models import ExternalPartner
        return ExternalPartner.objects.create(
            name='Happy Paws Grooming',
            partner_type='grooming',
            phone='998-123-4567',
            is_active=True
        )

    def test_create_referral_requires_login(self, client, partner):
        """Creating referral requires authentication."""
        url = reverse('services:referral_create', kwargs={'partner_pk': partner.pk})
        response = client.get(url)
        assert response.status_code == 302

    def test_create_referral_form_displayed(self, client, owner, pet, partner):
        """Referral form is displayed."""
        client.force_login(owner)
        url = reverse('services:referral_create', kwargs={'partner_pk': partner.pk})
        response = client.get(url)

        assert response.status_code == 200

    def test_create_referral_success(self, client, owner, pet, partner):
        """Can create a referral."""
        from apps.services.models import Referral

        client.force_login(owner)
        url = reverse('services:referral_create', kwargs={'partner_pk': partner.pk})
        response = client.post(url, {
            'pet': pet.pk,
            'service_type': 'grooming',
            'notes': 'Full grooming please'
        })

        assert Referral.objects.filter(pet=pet, partner=partner).exists()

    def test_referral_list_shows_user_referrals(self, client, owner, pet, partner):
        """Shows user's referrals."""
        from apps.services.models import Referral

        Referral.objects.create(
            pet=pet,
            partner=partner,
            referred_by=owner,
            service_type='grooming'
        )

        client.force_login(owner)
        url = reverse('services:referral_list')
        response = client.get(url)

        assert response.status_code == 200
        assert b'Happy Paws Grooming' in response.content
        assert b'Luna' in response.content

    def test_cannot_see_other_user_referrals(self, client, pet, partner, owner):
        """Cannot see another user's referrals."""
        from apps.services.models import Referral

        Referral.objects.create(
            pet=pet,
            partner=partner,
            referred_by=owner,
            service_type='grooming'
        )

        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass'
        )

        client.force_login(other_user)
        url = reverse('services:referral_list')
        response = client.get(url)

        assert b'Luna' not in response.content


# =============================================================================
# External Service AI Tool Tests
# =============================================================================

@pytest.mark.django_db
class TestExternalServiceTools:
    """Tests for external service AI tools."""

    @pytest.fixture
    def partners(self):
        from apps.services.models import ExternalPartner

        partners = []
        partners.append(ExternalPartner.objects.create(
            name='Happy Paws Grooming',
            partner_type='grooming',
            phone='998-123-4567',
            is_active=True
        ))
        partners.append(ExternalPartner.objects.create(
            name='Pet Paradise Boarding',
            partner_type='boarding',
            phone='998-987-6543',
            is_active=True
        ))
        return partners

    def test_list_partners_tool(self, partners):
        """List partners tool returns active partners."""
        from apps.services.tools import list_partners

        result = list_partners()

        assert result['success'] is True
        assert len(result['partners']) == 2

    def test_list_partners_by_type(self, partners):
        """Can filter partners by type."""
        from apps.services.tools import list_partners

        result = list_partners(partner_type='grooming')

        assert result['success'] is True
        assert len(result['partners']) == 1
        assert result['partners'][0]['name'] == 'Happy Paws Grooming'

    def test_get_partner_details_tool(self, partners):
        """Get partner details tool."""
        from apps.services.tools import get_partner_details

        result = get_partner_details(partner_id=partners[0].pk)

        assert result['success'] is True
        assert result['partner']['name'] == 'Happy Paws Grooming'
        assert result['partner']['phone'] == '998-123-4567'

    def test_get_partner_details_not_found(self, db):
        """Get partner details returns error for non-existent partner."""
        from apps.services.tools import get_partner_details

        result = get_partner_details(partner_id=99999)

        assert result['success'] is False
        assert 'Partner not found' in result['error']


# =============================================================================
# Service Model Tests (Veterinary Services)
# =============================================================================

@pytest.mark.django_db
class TestServiceModel:
    """Tests for the Service model (veterinary services)."""

    def test_create_consultation_service(self):
        """Can create a consultation service."""
        from apps.services.models import Service
        from decimal import Decimal

        service = Service.objects.create(
            name='General Consultation',
            name_es='Consulta General',
            description='Standard veterinary consultation',
            category='consultation',
            base_price=Decimal('500.00'),
            duration_minutes=30,
        )

        assert service.pk is not None
        assert service.category == 'consultation'
        assert service.base_price == Decimal('500.00')
        assert service.is_active is True

    def test_create_vaccination_service(self):
        """Can create a vaccination service."""
        from apps.services.models import Service
        from decimal import Decimal

        service = Service.objects.create(
            name='Rabies Vaccination',
            name_es='Vacuna Antirrábica',
            category='vaccination',
            base_price=Decimal('350.00'),
            duration_minutes=15,
        )

        assert service.pk is not None
        assert service.category == 'vaccination'

    def test_create_surgery_service(self):
        """Can create a surgery service."""
        from apps.services.models import Service
        from decimal import Decimal

        service = Service.objects.create(
            name='Spay/Neuter',
            name_es='Esterilización',
            category='surgery',
            base_price=Decimal('2500.00'),
            duration_minutes=120,
            requires_appointment=True,
        )

        assert service.pk is not None
        assert service.category == 'surgery'
        assert service.requires_appointment is True

    def test_service_default_values(self):
        """Service has correct default values."""
        from apps.services.models import Service
        from decimal import Decimal

        service = Service.objects.create(
            name='Test Service',
        )

        assert service.category == 'consultation'
        assert service.base_price == Decimal('0')
        assert service.duration_minutes == 30
        assert service.is_active is True
        assert service.requires_appointment is True
        assert service.clave_unidad_sat == 'E48'

    def test_service_str(self):
        """Service string representation."""
        from apps.services.models import Service

        service = Service.objects.create(
            name='Dental Cleaning',
        )

        assert 'Dental Cleaning' in str(service)

    def test_service_ordering(self):
        """Services are ordered by category then name."""
        from apps.services.models import Service
        from decimal import Decimal

        Service.objects.create(name='Zulu Service', category='vaccination')
        Service.objects.create(name='Alpha Service', category='vaccination')
        Service.objects.create(name='Beta Service', category='consultation')

        services = list(Service.objects.all())
        # consultation comes before vaccination alphabetically
        assert services[0].category == 'consultation'
        assert services[1].category == 'vaccination'

    def test_service_sat_codes(self):
        """Service can have SAT codes for CFDI."""
        from apps.services.models import Service
        from decimal import Decimal

        service = Service.objects.create(
            name='Consulta',
            clave_producto_sat='85121800',
            clave_unidad_sat='E48',
        )

        assert service.clave_producto_sat == '85121800'
        assert service.clave_unidad_sat == 'E48'

    def test_all_service_categories(self):
        """All service categories are valid."""
        from apps.services.models import Service, SERVICE_CATEGORIES

        for category, _ in SERVICE_CATEGORIES:
            service = Service.objects.create(
                name=f'Test {category}',
                category=category
            )
            assert service.category == category


# =============================================================================
# Referral Form Tests
# =============================================================================

@pytest.mark.django_db
class TestReferralForm:
    """Tests for the ReferralForm."""

    @pytest.fixture
    def owner(self):
        return User.objects.create_user(
            username='petowner',
            email='owner@example.com',
            password='testpass123',
            role='owner'
        )

    @pytest.fixture
    def other_owner(self):
        return User.objects.create_user(
            username='other_owner',
            email='other@example.com',
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
    def other_pet(self, other_owner):
        from apps.pets.models import Pet
        return Pet.objects.create(
            owner=other_owner,
            name='Max',
            species='dog'
        )

    def test_form_filters_pets_by_user(self, owner, pet, other_pet):
        """Form only shows user's pets."""
        from apps.services.forms import ReferralForm

        form = ReferralForm(user=owner)
        pet_queryset = form.fields['pet'].queryset

        assert pet in pet_queryset
        assert other_pet not in pet_queryset

    def test_form_valid_with_required_fields(self, owner, pet):
        """Form is valid with required fields."""
        from apps.services.forms import ReferralForm

        form = ReferralForm(data={
            'pet': pet.pk,
            'notes': 'Some notes',
        }, user=owner)

        assert form.is_valid()

    def test_form_valid_with_preferred_date(self, owner, pet):
        """Form accepts preferred date."""
        from apps.services.forms import ReferralForm

        form = ReferralForm(data={
            'pet': pet.pk,
            'preferred_date': date.today() + timedelta(days=7),
            'notes': 'Some notes',
        }, user=owner)

        assert form.is_valid()

    def test_form_invalid_without_pet(self, owner):
        """Form requires pet selection."""
        from apps.services.forms import ReferralForm

        form = ReferralForm(data={
            'notes': 'Some notes',
        }, user=owner)

        assert not form.is_valid()
        assert 'pet' in form.errors

    def test_form_has_widget_classes(self, owner, pet):
        """Form widgets have CSS classes."""
        from apps.services.forms import ReferralForm

        form = ReferralForm(user=owner)

        assert 'rounded-md' in form.fields['pet'].widget.attrs.get('class', '')
        assert 'rounded-md' in form.fields['notes'].widget.attrs.get('class', '')
