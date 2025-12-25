"""E2E test for emergency triage journey.

Simulates emergency workflows using the actual model structures.
Tests the emergency response system.
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta

from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db(transaction=True)
class TestEmergencyTriageJourney:
    """Complete emergency triage journey."""

    @pytest.fixture
    def on_call_vet(self, db):
        """Create an on-call veterinarian."""
        from apps.practice.models import StaffProfile

        user = User.objects.create_user(
            username='dr.emergency@petfriendlyvet.com',
            email='dr.emergency@petfriendlyvet.com',
            password='vet123',
            first_name='Dr. Carlos',
            last_name='Urgencias',
            role='vet',
            is_staff=True,
            phone_number='555-EMERGENCY',
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
            username='worried.owner@example.com',
            email='worried.owner@example.com',
            password='owner123',
            first_name='Pedro',
            last_name='Preocupado',
            role='owner',
            phone_number='555-999-1111',
        )

    @pytest.fixture
    def pet(self, db, pet_owner):
        """Create a pet having an emergency."""
        from apps.pets.models import Pet

        return Pet.objects.create(
            owner=pet_owner,
            name='Firulais',
            species='dog',
            breed='Chihuahua',
            gender='male',
            date_of_birth=date.today() - timedelta(days=730),
            weight_kg=Decimal('3.5'),
        )

    def test_complete_emergency_triage_journey(
        self, db, on_call_vet, pet_owner, pet
    ):
        """Test emergency triage workflow."""
        from apps.emergency.models import EmergencyContact, OnCallSchedule
        from apps.appointments.models import Appointment, ServiceType
        from apps.notifications.models import Notification

        # =========================================================================
        # STEP 1: Set Up On-Call Schedule
        # =========================================================================
        on_call = OnCallSchedule.objects.create(
            staff=on_call_vet.staff_profile,
            date=date.today(),
            start_time='00:00:00',
            end_time='23:59:59',
            contact_phone='555-EMERGENCY',
            is_active=True,
            notes='24-hour emergency coverage',
        )

        assert on_call.pk is not None

        # =========================================================================
        # STEP 2: Emergency Contact Initiated
        # =========================================================================
        emergency_contact = EmergencyContact.objects.create(
            owner=pet_owner,
            pet=pet,
            phone='555-999-1111',
            channel='phone',
            reported_symptoms='Vómito con sangre, letargo extremo',
            pet_species='dog',
            pet_age='2 años',
            severity='critical',
            status='initiated',
        )

        assert emergency_contact.pk is not None
        assert emergency_contact.severity == 'critical'

        # =========================================================================
        # STEP 3: Triage and Escalation
        # =========================================================================
        emergency_contact.status = 'triaging'
        emergency_contact.triage_notes = 'Síntomas críticos, requiere atención inmediata'
        emergency_contact.save()

        # Escalate to staff
        emergency_contact.status = 'escalated'
        emergency_contact.escalated_at = timezone.now()
        emergency_contact.handled_by = on_call_vet.staff_profile
        emergency_contact.save()

        # =========================================================================
        # STEP 4: Notify On-Call Vet
        # =========================================================================
        emergency_notification = Notification.objects.create(
            user=on_call_vet,
            notification_type='emergency_alert',
            title='EMERGENCIA: Paciente crítico',
            message=f'Paciente: {pet.name} - {emergency_contact.reported_symptoms}',
            related_pet_id=pet.pk,
            email_sent=True,
            email_sent_at=timezone.now(),
        )

        assert emergency_notification.pk is not None

        # =========================================================================
        # STEP 5: Schedule Emergency Appointment
        # =========================================================================
        emergency_service = ServiceType.objects.create(
            name='Consulta de Emergencia',
            duration_minutes=60,
            price=Decimal('1500.00'),
            category='emergency',
            is_active=True,
        )

        emergency_time = timezone.now()
        emergency_appointment = Appointment.objects.create(
            owner=pet_owner,
            pet=pet,
            service=emergency_service,
            veterinarian=on_call_vet,
            scheduled_start=emergency_time,
            scheduled_end=emergency_time + timedelta(hours=1),
            status='confirmed',
            notes='EMERGENCIA: ' + emergency_contact.reported_symptoms,
        )

        # Link appointment to emergency contact
        emergency_contact.appointment = emergency_appointment
        emergency_contact.save()

        assert emergency_appointment.pk is not None
        assert 'EMERGENCIA' in emergency_appointment.notes

        # =========================================================================
        # STEP 6: Resolve Emergency Contact
        # =========================================================================
        emergency_contact.status = 'resolved'
        emergency_contact.resolved_at = timezone.now()
        emergency_contact.resolution = 'Paciente atendido en emergencia. Tratamiento iniciado.'
        emergency_contact.outcome = 'treated'
        emergency_contact.save()

        # =========================================================================
        # VERIFICATION
        # =========================================================================
        # Emergency was triaged and escalated
        emergency_contact.refresh_from_db()
        assert emergency_contact.status == 'resolved'
        assert emergency_contact.handled_by is not None

        # Appointment was created and linked
        assert emergency_contact.appointment == emergency_appointment

        # Notification was sent
        assert Notification.objects.filter(
            user=on_call_vet,
            notification_type='emergency_alert'
        ).exists()


@pytest.mark.django_db(transaction=True)
class TestEmergencyReferral:
    """Test emergency referral to external hospitals."""

    def test_referral_to_24_hour_hospital(self, db):
        """When no on-call, refer to 24-hour hospital."""
        from apps.emergency.models import EmergencyReferral

        referral_hospital = EmergencyReferral.objects.create(
            name='Hospital Veterinario 24 Horas',
            address='Av. Emergencias 123, CDMX',
            phone='555-24HOURS',
            latitude=Decimal('19.4326'),
            longitude=Decimal('-99.1332'),
            is_24_hours=True,
            services=['emergency', 'surgery', 'icu'],
            species_treated=['dog', 'cat'],
            is_active=True,
        )

        assert referral_hospital.pk is not None
        assert referral_hospital.is_24_hours is True

        # Can query active 24-hour hospitals
        hospitals = EmergencyReferral.objects.filter(
            is_24_hours=True,
            is_active=True,
        )
        assert hospitals.count() >= 1


@pytest.mark.django_db(transaction=True)
class TestEmergencySymptoms:
    """Test emergency symptom management."""

    def test_symptom_severity_levels(self, db):
        """Emergency symptoms have severity levels."""
        from apps.emergency.models import EmergencySymptom

        symptoms = [
            ('paro cardiaco', 'critical'),
            ('dificultad respiratoria', 'urgent'),
            ('vomito', 'moderate'),
            ('comezon leve', 'low'),
        ]

        for keyword, severity in symptoms:
            EmergencySymptom.objects.create(
                keyword=keyword,
                severity=severity,
                description=f'Symptom: {keyword}',
                is_active=True,
            )

        # Can filter by severity
        critical = EmergencySymptom.objects.filter(severity='critical')
        assert critical.count() == 1

        urgent = EmergencySymptom.objects.filter(severity='urgent')
        assert urgent.count() == 1
