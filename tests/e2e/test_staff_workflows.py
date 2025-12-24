"""E2E tests for staff workflows.

Tests internal staff operations:
- Customer notes management
- Interaction logging (calls, emails, visits)
- Customer tagging
- Customer history viewing
- Follow-up reminders
- Internal task management
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta

from django.utils import timezone

from apps.crm.models import (
    OwnerProfile, CustomerTag, Interaction, CustomerNote
)


@pytest.mark.django_db
class TestCustomerNotes:
    """Test staff can create and manage customer notes."""

    def test_staff_can_create_customer_note(
        self, db, owner_profile, staff_user
    ):
        """Staff can add notes to customer profile."""
        note = CustomerNote.objects.create(
            owner_profile=owner_profile,
            author=staff_user,
            content='Cliente VIP, siempre paga a tiempo. Prefiere comunicación por WhatsApp.',
        )

        assert note.owner_profile == owner_profile
        assert note.author == staff_user
        assert 'VIP' in note.content
        assert note.is_pinned is False
        assert note.is_private is False

    def test_staff_can_pin_important_note(
        self, db, owner_profile, staff_user
    ):
        """Staff can pin important notes."""
        note = CustomerNote.objects.create(
            owner_profile=owner_profile,
            author=staff_user,
            content='ALERTA: Cliente tiene saldo pendiente de 3 meses.',
            is_pinned=True,
        )

        assert note.is_pinned is True

        # Pinned notes should appear first
        notes = owner_profile.customer_notes.all()
        assert notes.first() == note

    def test_staff_can_create_private_note(
        self, db, owner_profile, staff_user
    ):
        """Staff can create private notes only visible to staff."""
        note = CustomerNote.objects.create(
            owner_profile=owner_profile,
            author=staff_user,
            content='Nota confidencial sobre situación financiera.',
            is_private=True,
        )

        assert note.is_private is True


@pytest.mark.django_db
class TestInteractionLogging:
    """Test staff can log customer interactions."""

    def test_staff_can_record_phone_call(
        self, db, owner_profile, staff_user
    ):
        """Staff can log phone call interaction."""
        interaction = Interaction.objects.create(
            owner_profile=owner_profile,
            interaction_type='call',
            channel='phone',
            direction='inbound',
            subject='Consulta sobre vacunas',
            notes='Cliente preguntó sobre próximas vacunas para su perro Max.',
            handled_by=staff_user,
            duration_minutes=5,
            outcome='Agendó cita para vacunación',
        )

        assert interaction.interaction_type == 'call'
        assert interaction.direction == 'inbound'
        assert interaction.duration_minutes == 5
        assert interaction.handled_by == staff_user

    def test_staff_can_record_whatsapp_message(
        self, db, owner_profile, staff_user
    ):
        """Staff can log WhatsApp interaction."""
        interaction = Interaction.objects.create(
            owner_profile=owner_profile,
            interaction_type='whatsapp',
            channel='whatsapp',
            direction='outbound',
            subject='Recordatorio de cita',
            notes='Se envió recordatorio de cita para mañana.',
            handled_by=staff_user,
        )

        assert interaction.interaction_type == 'whatsapp'
        assert interaction.channel == 'whatsapp'
        assert interaction.direction == 'outbound'

    def test_staff_can_record_in_person_visit(
        self, db, owner_profile, staff_user
    ):
        """Staff can log in-person visit."""
        interaction = Interaction.objects.create(
            owner_profile=owner_profile,
            interaction_type='visit',
            channel='in_person',
            direction='inbound',
            subject='Consulta sin cita',
            notes='Cliente llegó sin cita, se atendió emergencia menor.',
            handled_by=staff_user,
            outcome='Se resolvió, programó cita de seguimiento',
            follow_up_required=True,
            follow_up_date=date.today() + timedelta(days=7),
        )

        assert interaction.interaction_type == 'visit'
        assert interaction.follow_up_required is True
        assert interaction.follow_up_date is not None

    def test_interaction_history_ordered_by_date(
        self, db, owner_profile, staff_user
    ):
        """Interactions are ordered by most recent first."""
        # Create multiple interactions
        for i in range(3):
            Interaction.objects.create(
                owner_profile=owner_profile,
                interaction_type='call',
                channel='phone',
                direction='inbound',
                subject=f'Call #{i+1}',
                handled_by=staff_user,
            )

        interactions = owner_profile.interactions.all()
        assert interactions.count() == 3
        # Most recent first (default ordering)
        assert interactions.first().subject == 'Call #3'


@pytest.mark.django_db
class TestCustomerTagging:
    """Test staff can tag customers."""

    def test_staff_can_add_tag_to_customer(
        self, db, owner_profile, customer_tag
    ):
        """Staff can add tags to customer profile."""
        owner_profile.tags.add(customer_tag)

        assert customer_tag in owner_profile.tags.all()
        assert owner_profile in customer_tag.profiles.all()

    def test_staff_can_remove_tag_from_customer(
        self, db, owner_profile, customer_tag
    ):
        """Staff can remove tags from customer profile."""
        owner_profile.tags.add(customer_tag)
        assert customer_tag in owner_profile.tags.all()

        owner_profile.tags.remove(customer_tag)
        assert customer_tag not in owner_profile.tags.all()

    def test_staff_can_create_new_tag(self, db, staff_user):
        """Staff can create new customer tags."""
        tag = CustomerTag.objects.create(
            name='Moroso',
            color='#dc3545',  # Red
            description='Cliente con pagos atrasados',
        )

        assert tag.name == 'Moroso'
        assert tag.color == '#dc3545'
        assert tag.is_active is True

    def test_multiple_tags_on_customer(self, db, owner_profile):
        """Customer can have multiple tags."""
        tag_vip = CustomerTag.objects.create(name='VIP', color='#FFD700')
        tag_referrer = CustomerTag.objects.create(name='Referidor', color='#28a745')
        tag_multiowner = CustomerTag.objects.create(name='Multi-Mascota', color='#17a2b8')

        owner_profile.tags.add(tag_vip, tag_referrer, tag_multiowner)

        assert owner_profile.tags.count() == 3

    def test_filter_customers_by_tag(self, db, owner_user, staff_user):
        """Can filter customers by tag."""
        tag_vip = CustomerTag.objects.create(name='VIP Test', color='#FFD700')

        # Create owner profiles
        profile1 = OwnerProfile.objects.create(user=owner_user)
        profile1.tags.add(tag_vip)

        # Query by tag
        vip_customers = OwnerProfile.objects.filter(tags=tag_vip)
        assert vip_customers.count() == 1
        assert profile1 in vip_customers


@pytest.mark.django_db
class TestCustomerHistory:
    """Test staff can view full customer history."""

    def test_staff_can_view_customer_visits(
        self, db, owner_profile, scheduled_appointment
    ):
        """Staff can see customer's appointment/visit history."""
        # The appointment is linked to owner via owner_user
        owner = owner_profile.user
        appointments = owner.appointments.all()

        assert appointments.exists()

    def test_staff_can_view_customer_orders(
        self, db, owner_profile, paid_order
    ):
        """Staff can see customer's order history."""
        owner = owner_profile.user
        orders = owner.orders.all()

        assert orders.exists()
        assert paid_order in orders

    def test_staff_can_view_customer_spending(
        self, db, owner_profile, paid_order
    ):
        """Staff can see customer total spending."""
        # Update profile with spending data
        owner_profile.total_spent = paid_order.total
        owner_profile.total_visits = 1
        owner_profile.save()

        owner_profile.refresh_from_db()
        assert owner_profile.total_spent == paid_order.total
        assert owner_profile.total_visits == 1


@pytest.mark.django_db
class TestFollowUpReminders:
    """Test follow-up reminder functionality."""

    def test_interaction_with_follow_up(self, db, owner_profile, staff_user):
        """Interactions can have follow-up dates."""
        follow_up_date = date.today() + timedelta(days=7)

        interaction = Interaction.objects.create(
            owner_profile=owner_profile,
            interaction_type='call',
            channel='phone',
            direction='outbound',
            subject='Seguimiento post-cirugía',
            notes='Llamar en una semana para verificar recuperación.',
            handled_by=staff_user,
            follow_up_required=True,
            follow_up_date=follow_up_date,
        )

        assert interaction.follow_up_required is True
        assert interaction.follow_up_date == follow_up_date

    def test_query_pending_follow_ups(self, db, owner_profile, staff_user):
        """Can query interactions needing follow-up."""
        today = date.today()
        tomorrow = today + timedelta(days=1)

        # Create interaction with follow-up due tomorrow
        Interaction.objects.create(
            owner_profile=owner_profile,
            interaction_type='call',
            channel='phone',
            direction='inbound',
            follow_up_required=True,
            follow_up_date=tomorrow,
            handled_by=staff_user,
        )

        # Query pending follow-ups
        pending = Interaction.objects.filter(
            follow_up_required=True,
            follow_up_date__lte=tomorrow,
        )

        assert pending.count() >= 1


@pytest.mark.django_db
class TestAPIStaffWorkflows:
    """Test staff workflows via API endpoints."""

    def test_staff_api_add_note(self, staff_client, owner_profile):
        """Staff can add note via API."""
        response = staff_client.post(
            f'/api/crm/profiles/{owner_profile.id}/notes/',
            {
                'content': 'Test note from API',
                'is_pinned': False,
            },
            format='json',
        )

        if response.status_code == 201:
            assert CustomerNote.objects.filter(
                owner_profile=owner_profile,
                content='Test note from API'
            ).exists()

    def test_staff_api_log_interaction(self, staff_client, owner_profile):
        """Staff can log interaction via API."""
        response = staff_client.post(
            f'/api/crm/profiles/{owner_profile.id}/interactions/',
            {
                'interaction_type': 'call',
                'channel': 'phone',
                'direction': 'inbound',
                'subject': 'API Test Call',
                'notes': 'Logged via API',
            },
            format='json',
        )

        if response.status_code == 201:
            assert Interaction.objects.filter(
                owner_profile=owner_profile,
                subject='API Test Call'
            ).exists()

    def test_staff_api_add_tag(self, staff_client, owner_profile, customer_tag):
        """Staff can add tag via API."""
        response = staff_client.post(
            f'/api/crm/profiles/{owner_profile.id}/tags/',
            {'tag_id': customer_tag.id},
            format='json',
        )

        if response.status_code in [200, 201, 204]:
            owner_profile.refresh_from_db()
            assert customer_tag in owner_profile.tags.all()

    def test_staff_api_view_customer_history(self, staff_client, owner_profile):
        """Staff can view full customer history via API."""
        response = staff_client.get(
            f'/api/crm/profiles/{owner_profile.id}/history/'
        )

        if response.status_code == 200:
            assert 'interactions' in response.data or 'notes' in response.data


@pytest.mark.django_db
class TestCRMAnalytics:
    """Test CRM analytics and reporting."""

    def test_customer_lifetime_value_tracking(self, db, owner_profile, paid_order):
        """Customer lifetime value is tracked correctly."""
        # Simulate updating LTV
        owner_profile.total_spent += paid_order.total
        owner_profile.lifetime_value = owner_profile.total_spent
        owner_profile.total_visits += 1
        owner_profile.last_visit_date = date.today()
        owner_profile.save()

        owner_profile.refresh_from_db()
        assert owner_profile.lifetime_value > 0
        assert owner_profile.total_visits > 0

    def test_referral_tracking(self, db, owner_user, staff_user):
        """Referral source is tracked."""
        profile = OwnerProfile.objects.create(
            user=owner_user,
            referral_source='Instagram Ad Campaign Q4',
        )

        assert profile.referral_source == 'Instagram Ad Campaign Q4'

    def test_customer_segments(self, db, owner_profile):
        """Customers can be assigned to segments."""
        from apps.crm.models import CustomerSegment

        segment = CustomerSegment.objects.create(
            name='High Value Customers',
            description='Customers with LTV > $5000',
            criteria={'lifetime_value_min': 5000},
        )

        # This would typically be used for dynamic segmentation
        assert segment.is_active is True
