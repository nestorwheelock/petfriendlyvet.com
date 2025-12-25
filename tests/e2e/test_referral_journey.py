"""E2E test for specialist referral journey.

Simulates the complete referral workflow:
1. Primary vet examines pet with complex condition
2. Vet creates outbound referral to specialist
3. Referral documents attached
4. Specialist receives and accepts referral
5. Appointment scheduled with visiting specialist
6. Specialist sees patient and documents findings
7. Report sent back to primary vet
8. Referral marked complete with outcome
9. Invoice generated for specialist services

Tests the specialist referral network.
"""
import pytest
from decimal import Decimal
from datetime import date, time, timedelta

from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db(transaction=True)
class TestSpecialistReferralJourney:
    """Complete specialist referral journey."""

    @pytest.fixture
    def primary_vet(self, db):
        """Create primary care veterinarian."""
        from apps.practice.models import StaffProfile

        user = User.objects.create_user(
            username='primary.vet@petfriendlyvet.com',
            email='primary.vet@petfriendlyvet.com',
            password='vet123',
            first_name='Dr. Carlos',
            last_name='Primario',
            role='vet',
            is_staff=True,
        )
        StaffProfile.objects.create(user=user, role='veterinarian', can_prescribe=True)
        return user

    @pytest.fixture
    def customer(self, db):
        """Create pet owner."""
        return User.objects.create_user(
            username='referral.owner@example.com',
            email='referral.owner@example.com',
            password='owner123',
            first_name='Sofia',
            last_name='Dueña',
            role='owner',
            phone_number='555-REF-0001',
        )

    @pytest.fixture
    def pet(self, db, customer):
        """Create pet with medical history."""
        from apps.pets.models import Pet, MedicalCondition

        pet = Pet.objects.create(
            owner=customer,
            name='Luna',
            species='cat',
            breed='Persa',
            gender='female',
            date_of_birth=date.today() - timedelta(days=3650),  # 10 years old
            weight_kg=Decimal('4.5'),
        )

        # Pet has a known heart condition
        MedicalCondition.objects.create(
            pet=pet,
            name='Soplo cardíaco',
            condition_type='chronic',
            diagnosed_date=date.today() - timedelta(days=180),
            notes='Soplo grado III/VI detectado en examen de rutina',
            is_active=True,
        )

        return pet

    @pytest.fixture
    def cardiologist(self, db):
        """Create cardiologist specialist."""
        from apps.referrals.models import Specialist

        return Specialist.objects.create(
            name='Dr. María Corazón',
            specialty='cardiology',
            credentials='DVM, Diplomate ACVIM (Cardiology)',
            is_facility=False,
            email='cardiologist@specialists.com',
            phone='555-HEART-01',
            address='Centro Veterinario Especializado, CDMX',
            city='Ciudad de México',
            latitude=Decimal('19.4326'),
            longitude=Decimal('-99.1332'),
            is_visiting=True,
            visiting_services=['Ecocardiografía', 'Electrocardiograma', 'Consulta cardiológica'],
            equipment_provided=['Ecógrafo cardíaco', 'ECG'],
            relationship_status='active',
            revenue_share_percent=Decimal('30.00'),
            is_active=True,
        )

    def test_complete_referral_journey(
        self, db, primary_vet, customer, pet, cardiologist
    ):
        """
        Test complete referral journey from creation to completion.

        Primary vet refers → Specialist accepts → Patient seen → Report sent
        """
        from apps.referrals.models import (
            Referral, ReferralDocument, ReferralNote,
            VisitingSchedule, VisitingAppointment
        )
        from apps.billing.models import Invoice

        # =========================================================================
        # STEP 1: Primary Vet Creates Referral
        # =========================================================================
        referral = Referral.objects.create(
            direction='outbound',
            pet=pet,
            owner=customer,
            specialist=cardiologist,
            reason='Soplo cardíaco grado III/VI. Requiere ecocardiografía para '
                   'evaluar función cardíaca y determinar tratamiento.',
            clinical_summary='''
            Paciente felino de 10 años con soplo detectado hace 6 meses.
            Sin signos de insuficiencia cardíaca congestiva actualmente.
            Propietaria reporta episodios ocasionales de letargia.
            Peso estable. Apetito normal.
            ''',
            urgency='routine',
            requested_services=['Ecocardiografía', 'Consulta cardiológica'],
            status='draft',
            referred_by=primary_vet,
        )

        assert referral.pk is not None
        assert referral.referral_number is not None
        assert referral.status == 'draft'

        # =========================================================================
        # STEP 2: Attach Medical Documents
        # =========================================================================
        # Medical history document
        history_doc = ReferralDocument.objects.create(
            referral=referral,
            document_type='medical_history',
            title='Historial Médico - Luna',
            description='Historial completo incluyendo vacunaciones y visitas previas',
            is_outgoing=True,
            uploaded_by=primary_vet,
        )

        # Lab results
        lab_doc = ReferralDocument.objects.create(
            referral=referral,
            document_type='lab_results',
            title='Resultados de laboratorio recientes',
            description='Hemograma, química sanguínea y tiroides',
            is_outgoing=True,
            uploaded_by=primary_vet,
        )

        assert referral.documents.count() == 2

        # =========================================================================
        # STEP 3: Send Referral to Specialist
        # =========================================================================
        referral.status = 'sent'
        referral.sent_at = timezone.now()
        referral.save()

        # Add note about sending
        ReferralNote.objects.create(
            referral=referral,
            note='Referido enviado al Dr. María Corazón por correo electrónico',
            is_internal=True,
            author=primary_vet,
        )

        referral.refresh_from_db()
        assert referral.status == 'sent'

        # =========================================================================
        # STEP 4: Specialist Receives and Accepts Referral
        # =========================================================================
        referral.status = 'received'
        referral.save()

        # Specialist adds note
        ReferralNote.objects.create(
            referral=referral,
            note='Referido recibido. Tengo disponibilidad para la próxima visita '
                 'a Pet-Friendly Vet el día 15.',
            is_internal=False,  # Visible to primary vet
            author=None,  # External specialist
        )

        # =========================================================================
        # STEP 5: Schedule Visiting Specialist Appointment
        # =========================================================================
        # Create visiting schedule
        visit_date = date.today() + timedelta(days=10)
        visiting_schedule = VisitingSchedule.objects.create(
            specialist=cardiologist,
            date=visit_date,
            start_time=time(9, 0),
            end_time=time(14, 0),
            max_appointments=6,
            appointments_booked=0,
            services_available=['Ecocardiografía', 'Electrocardiograma', 'Consulta'],
            equipment_bringing=['Ecógrafo cardíaco', 'ECG'],
            status='confirmed',
        )

        # Book appointment for pet
        visiting_appointment = VisitingAppointment.objects.create(
            schedule=visiting_schedule,
            specialist=cardiologist,
            pet=pet,
            owner=customer,
            appointment_time=time(10, 0),
            duration_minutes=45,
            service='Ecocardiografía + Consulta',
            reason=referral.reason,
            status='scheduled',
            referral=referral,
            fee=Decimal('2500.00'),
            pet_friendly_share=Decimal('750.00'),  # 30% revenue share
        )

        # Update referral status
        referral.status = 'scheduled'
        referral.appointment_date = timezone.make_aware(
            timezone.datetime.combine(visit_date, time(10, 0))
        )
        referral.save()

        # Update schedule bookings
        visiting_schedule.appointments_booked += 1
        visiting_schedule.save()

        assert referral.status == 'scheduled'
        assert visiting_appointment.pk is not None

        # =========================================================================
        # STEP 6: Day of Visit - Specialist Examines Patient
        # =========================================================================
        # Check in
        visiting_appointment.status = 'checked_in'
        visiting_appointment.save()

        # In progress
        visiting_appointment.status = 'in_progress'
        visiting_appointment.save()

        # Document findings
        visiting_appointment.findings = '''
        Ecocardiografía realizada.

        Hallazgos:
        - Engrosamiento leve de la válvula mitral
        - Regurgitación mitral leve
        - Función sistólica conservada (FE 65%)
        - No hay evidencia de hipertrofia ventricular
        - Atrio izquierdo ligeramente dilatado (LA:Ao 1.6)

        Conclusión: Enfermedad valvular degenerativa en estadio B1.
        '''
        visiting_appointment.diagnosis = 'Enfermedad valvular mitral degenerativa - Estadio B1 (ACVIM)'
        visiting_appointment.recommendations = '''
        1. No requiere tratamiento médico en este momento
        2. Control ecocardiográfico en 6-12 meses
        3. Monitorear signos de insuficiencia cardíaca (tos, dificultad respiratoria, fatiga)
        4. Dieta baja en sodio recomendada
        5. Evitar ejercicio intenso
        '''
        visiting_appointment.status = 'completed'
        visiting_appointment.follow_up_needed = True
        visiting_appointment.follow_up_notes = 'Repetir ecocardiografía en 6-12 meses'
        visiting_appointment.save()

        # =========================================================================
        # STEP 7: Update Referral with Results
        # =========================================================================
        referral.status = 'seen'
        referral.seen_at = timezone.now()
        referral.specialist_findings = visiting_appointment.findings
        referral.specialist_diagnosis = visiting_appointment.diagnosis
        referral.specialist_recommendations = visiting_appointment.recommendations
        referral.follow_up_needed = True
        referral.follow_up_instructions = 'Control ecocardiográfico en 6-12 meses'
        referral.save()

        # Upload specialist report document
        ReferralDocument.objects.create(
            referral=referral,
            document_type='specialist_report',
            title='Reporte Ecocardiográfico - Luna',
            description='Reporte completo con imágenes y mediciones',
            is_outgoing=False,  # Incoming from specialist
            uploaded_by=None,
        )

        # =========================================================================
        # STEP 8: Complete Referral
        # =========================================================================
        referral.status = 'completed'
        referral.completed_at = timezone.now()
        referral.outcome = 'successful'
        referral.outcome_notes = 'Diagnóstico establecido. Paciente en estadio temprano, buen pronóstico.'
        referral.save()

        # Update specialist stats
        cardiologist.total_referrals_received += 1
        cardiologist.save()

        # =========================================================================
        # STEP 9: Invoice Generated
        # =========================================================================
        # Create invoice for specialist services
        invoice = Invoice.objects.create(
            owner=customer,
            pet=pet,
            subtotal=visiting_appointment.fee,
            tax_amount=visiting_appointment.fee * Decimal('0.16'),
            total=visiting_appointment.fee * Decimal('1.16'),
            due_date=date.today() + timedelta(days=30),
            status='draft',
        )

        # Link to appointment
        visiting_appointment.invoice = invoice
        visiting_appointment.save()

        # Link to referral
        referral.invoice = invoice
        referral.save()

        assert invoice.pk is not None

        # =========================================================================
        # VERIFICATION: Complete Journey
        # =========================================================================
        referral.refresh_from_db()
        visiting_appointment.refresh_from_db()
        cardiologist.refresh_from_db()

        # Referral completed
        assert referral.status == 'completed'
        assert referral.outcome == 'successful'
        assert referral.specialist_diagnosis is not None
        assert referral.documents.count() == 3  # history, labs, report

        # Appointment completed
        assert visiting_appointment.status == 'completed'
        assert visiting_appointment.findings is not None

        # Invoice linked
        assert referral.invoice is not None

        # Specialist stats updated
        assert cardiologist.total_referrals_received >= 1


@pytest.mark.django_db(transaction=True)
class TestInboundReferral:
    """Test inbound referrals from other clinics."""

    def test_inbound_referral_from_external_vet(self, db):
        """Process referral from another veterinary clinic."""
        from apps.referrals.models import Referral
        from apps.pets.models import Pet

        # Create owner and pet (new to our clinic)
        owner = User.objects.create_user(
            username='new.patient@example.com',
            email='new.patient@example.com',
            password='new123',
            first_name='Nueva',
            last_name='Paciente',
            role='owner',
        )

        pet = Pet.objects.create(
            owner=owner,
            name='Referido',
            species='dog',
            breed='Bulldog Francés',
            gender='male',
        )

        # Create inbound referral
        referral = Referral.objects.create(
            direction='inbound',
            pet=pet,
            owner=owner,
            referring_vet_name='Dr. Roberto García',
            referring_clinic='Clínica Veterinaria del Sur',
            referring_contact='555-SUR-0001',
            reason='Paciente con problemas respiratorios crónicos. '
                   'Requiere evaluación por especialista.',
            clinical_summary='Bulldog francés de 3 años con síndrome braquicefálico severo.',
            urgency='urgent',
            status='received',
        )

        assert referral.direction == 'inbound'
        assert referral.referring_clinic == 'Clínica Veterinaria del Sur'

        # Schedule appointment at our clinic
        referral.status = 'scheduled'
        referral.save()

        # Process and complete
        referral.status = 'seen'
        referral.seen_at = timezone.now()
        referral.specialist_findings = 'Síndrome braquicefálico confirmado. Candidato a cirugía.'
        referral.save()

        referral.status = 'completed'
        referral.completed_at = timezone.now()
        referral.outcome = 'referred_again'  # Referred to surgeon
        referral.save()

        referral.refresh_from_db()
        assert referral.status == 'completed'


@pytest.mark.django_db(transaction=True)
class TestReferralUrgencyScenarios:
    """Test different urgency levels for referrals."""

    @pytest.fixture
    def setup_referral_data(self, db):
        """Setup basic referral data."""
        from apps.referrals.models import Specialist
        from apps.pets.models import Pet

        owner = User.objects.create_user(
            username='urgency.test@example.com',
            email='urgency.test@example.com',
            password='test123',
            role='owner',
        )

        pet = Pet.objects.create(
            owner=owner,
            name='Urgente',
            species='dog',
        )

        specialist = Specialist.objects.create(
            name='Dr. Emergencias',
            specialty='emergency',
            phone='555-EMER-01',
            address='Hospital de Emergencias',
            city='CDMX',
            is_24_hours=True,
            is_active=True,
        )

        vet = User.objects.create_user(
            username='vet.urgency@example.com',
            email='vet.urgency@example.com',
            password='vet123',
            role='vet',
            is_staff=True,
        )

        return {'owner': owner, 'pet': pet, 'specialist': specialist, 'vet': vet}

    def test_emergency_referral_same_day(self, setup_referral_data):
        """Emergency referral processed same day."""
        from apps.referrals.models import Referral

        data = setup_referral_data

        referral = Referral.objects.create(
            direction='outbound',
            pet=data['pet'],
            owner=data['owner'],
            specialist=data['specialist'],
            reason='Trauma por atropellamiento. Requiere cirugía de emergencia.',
            urgency='emergency',
            status='sent',
            referred_by=data['vet'],
            sent_at=timezone.now(),
        )

        assert referral.urgency == 'emergency'

        # Emergency referrals should be processed immediately
        referral.status = 'received'
        referral.save()

        # Same day appointment
        referral.appointment_date = timezone.now()
        referral.status = 'scheduled'
        referral.save()

        # Seen same day
        referral.seen_at = timezone.now()
        referral.status = 'seen'
        referral.save()

        assert referral.sent_at.date() == referral.seen_at.date()

    def test_routine_referral_scheduled_weeks_out(self, setup_referral_data):
        """Routine referral can wait for next specialist visit."""
        from apps.referrals.models import Referral

        data = setup_referral_data

        referral = Referral.objects.create(
            direction='outbound',
            pet=data['pet'],
            owner=data['owner'],
            specialist=data['specialist'],
            reason='Revisión de rutina por condición crónica controlada.',
            urgency='routine',
            status='sent',
            referred_by=data['vet'],
            sent_at=timezone.now(),
        )

        assert referral.urgency == 'routine'

        # Routine can be scheduled 2-4 weeks out
        future_date = timezone.now() + timedelta(days=21)
        referral.appointment_date = future_date
        referral.status = 'scheduled'
        referral.save()

        assert (referral.appointment_date.date() - referral.sent_at.date()).days >= 14
