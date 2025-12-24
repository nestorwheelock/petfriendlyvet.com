"""
Generate comprehensive test scenarios for the Pet-Friendly Vet application.

This command creates realistic test data including:
- Clinic setup (staff, vets, services, products)
- Customers with various pet profiles
- Medical histories (normal and abnormal)
- Appointments, visits, orders, deliveries
- Simulated workflows and edge cases

Usage:
    python manage.py generate_test_scenarios
    python manage.py generate_test_scenarios --customers 50
    python manage.py generate_test_scenarios --clear
"""
import random
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from faker import Faker

User = get_user_model()
fake = Faker(['es_MX', 'en_US'])


class Command(BaseCommand):
    help = 'Generate comprehensive test scenarios with realistic data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--customers',
            type=int,
            default=10,
            help='Number of customers to create (default: 10)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing test data before generating'
        )
        parser.add_argument(
            '--skip-clinic',
            action='store_true',
            help='Skip clinic setup (use existing staff/products)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('🏥 Pet-Friendly Vet - Test Scenario Generator'))
        self.stdout.write('=' * 60)

        if options['clear']:
            self.clear_test_data()

        if not options['skip_clinic']:
            self.setup_clinic()

        self.create_customer_scenarios(options['customers'])
        self.create_workflow_scenarios()

        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS('✅ Test scenarios generated successfully!'))
        self.print_summary()

    def clear_test_data(self):
        """Clear existing test data."""
        self.stdout.write(self.style.WARNING('🗑️  Clearing existing test data...'))

        from apps.pets.models import Pet, Visit, Vaccination
        from apps.appointments.models import Appointment
        from apps.store.models import Order, Cart
        from apps.delivery.models import Delivery
        from apps.crm.models import OwnerProfile, Interaction

        # Clear in order of dependencies
        Delivery.objects.all().delete()
        Order.objects.all().delete()
        Cart.objects.all().delete()
        Appointment.objects.all().delete()
        Visit.objects.all().delete()
        Vaccination.objects.all().delete()
        Pet.objects.all().delete()
        Interaction.objects.all().delete()
        OwnerProfile.objects.all().delete()

        # Clear test users (keep superusers)
        User.objects.filter(is_superuser=False, email__contains='test').delete()

        self.stdout.write('  Cleared existing test data')

    def setup_clinic(self):
        """Set up clinic infrastructure: staff, vets, products, services."""
        self.stdout.write(self.style.NOTICE('\n📋 PHASE 1: Clinic Setup'))

        self.create_staff()
        self.create_service_types()
        self.create_products()
        self.create_delivery_infrastructure()

    def create_staff(self):
        """Create clinic staff and veterinarians."""
        self.stdout.write('  Creating staff and veterinarians...')

        # Head Veterinarian
        self.head_vet, _ = User.objects.get_or_create(
            username='dr_rodriguez',
            defaults={
                'email': 'dr.rodriguez@petfriendlyvet.test',
                'first_name': 'Carlos',
                'last_name': 'Rodríguez García',
                'role': 'vet',
                'is_staff': True,
                'phone_number': '555-0001',
            }
        )
        self.head_vet.set_password('vet123')
        self.head_vet.save()

        # Associate Veterinarians
        vets_data = [
            ('dra_martinez', 'María', 'Martínez López', '555-0002'),
            ('dr_gonzalez', 'Roberto', 'González Hernández', '555-0003'),
            ('dra_sanchez', 'Ana', 'Sánchez Pérez', '555-0004'),
        ]

        self.vets = [self.head_vet]
        for username, first, last, phone in vets_data:
            vet, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@petfriendlyvet.test',
                    'first_name': first,
                    'last_name': last,
                    'role': 'vet',
                    'is_staff': True,
                    'phone_number': phone,
                }
            )
            vet.set_password('vet123')
            vet.save()
            self.vets.append(vet)

        # Receptionist/Staff
        staff_data = [
            ('recepcion1', 'Laura', 'Flores', '555-0010'),
            ('recepcion2', 'Pedro', 'Ramírez', '555-0011'),
        ]

        self.staff = []
        for username, first, last, phone in staff_data:
            staff, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@petfriendlyvet.test',
                    'first_name': first,
                    'last_name': last,
                    'role': 'staff',
                    'is_staff': True,
                    'phone_number': phone,
                }
            )
            staff.set_password('staff123')
            staff.save()
            self.staff.append(staff)

        self.stdout.write(f'    Created {len(self.vets)} veterinarians, {len(self.staff)} staff')

    def create_service_types(self):
        """Create appointment service types."""
        self.stdout.write('  Creating service types...')

        from apps.appointments.models import ServiceType

        services_data = [
            ('Consulta General', 30, 500, 'clinic', 'Consulta veterinaria estándar'),
            ('Vacunación', 15, 350, 'clinic', 'Aplicación de vacunas'),
            ('Esterilización', 90, 1800, 'surgery', 'Cirugía de esterilización'),
            ('Limpieza Dental', 60, 1500, 'surgery', 'Profilaxis dental con anestesia'),
            ('Consulta de Seguimiento', 20, 300, 'clinic', 'Revisión post-tratamiento'),
            ('Emergencia', 45, 800, 'emergency', 'Atención de emergencias'),
            ('Chequeo Geriátrico', 45, 650, 'clinic', 'Evaluación completa para mascotas senior'),
            ('Desparasitación', 15, 200, 'clinic', 'Aplicación de antiparasitarios'),
        ]

        self.services = {}
        for name, duration, price, category, desc in services_data:
            service, _ = ServiceType.objects.get_or_create(
                name=name,
                defaults={
                    'duration_minutes': duration,
                    'price': Decimal(str(price)),
                    'category': category,
                    'description': desc,
                    'is_active': True,
                }
            )
            # Store by simplified key for easy access
            key = name.lower().replace(' ', '_').replace('ó', 'o').replace('á', 'a').replace('í', 'i')
            self.services[key] = service

        self.stdout.write(f'    Created {len(services_data)} service types')

    def create_products(self):
        """Create product catalog with realistic pricing."""
        self.stdout.write('  Creating product catalog...')

        from apps.store.models import Product, Category

        categories_products = {
            'Alimentos': [
                ('Royal Canin Adulto 15kg', 1850.00, 'Alimento premium para perros adultos'),
                ('Royal Canin Cachorro 3kg', 520.00, 'Alimento para cachorros'),
                ('Hills Science Diet 7kg', 980.00, 'Alimento científico para perros'),
                ('Whiskas Adulto 10kg', 650.00, 'Alimento para gatos adultos'),
                ('Pro Plan Gato 3kg', 480.00, 'Alimento premium para gatos'),
                ('Snacks Dentales Pedigree', 120.00, 'Snacks para limpieza dental'),
            ],
            'Medicamentos': [
                ('Nexgard 10-25kg', 450.00, 'Antiparasitario oral mensual'),
                ('Frontline Plus Perro', 380.00, 'Antipulgas y garrapatas'),
                ('Apoquel 16mg (30 tabs)', 2800.00, 'Antialérgico para perros'),
                ('Rimadyl 75mg (60 tabs)', 1200.00, 'Antiinflamatorio'),
                ('Amoxicilina 500mg (20 caps)', 180.00, 'Antibiótico'),
                ('Metronidazol 250mg (30 tabs)', 150.00, 'Antibiótico/antiparasitario'),
            ],
            'Accesorios': [
                ('Collar Ajustable Mediano', 180.00, 'Collar de nylon resistente'),
                ('Correa Retráctil 5m', 350.00, 'Correa extensible'),
                ('Cama Ortopédica Grande', 890.00, 'Cama con memoria para articulaciones'),
                ('Transportadora Mediana', 650.00, 'Transportadora aprobada para viaje'),
                ('Juguete Kong Classic', 280.00, 'Juguete rellenable resistente'),
                ('Plato Antiderrame Doble', 220.00, 'Plato para comida y agua'),
            ],
            'Higiene': [
                ('Shampoo Medicado Virbac', 320.00, 'Shampoo para problemas de piel'),
                ('Limpiador de Oídos', 180.00, 'Solución ótica'),
                ('Cepillo Furminator', 580.00, 'Cepillo para pelaje'),
                ('Pasta Dental Enzymatic', 150.00, 'Pasta dental para mascotas'),
                ('Cortauñas Profesional', 180.00, 'Cortauñas de acero'),
            ],
            'Servicios': [
                ('Consulta General', 500.00, 'Consulta veterinaria estándar'),
                ('Vacuna Antirrábica', 350.00, 'Vacuna contra la rabia'),
                ('Vacuna Múltiple Canina', 450.00, 'Vacuna polivalente para perros'),
                ('Esterilización Perro Pequeño', 1800.00, 'Cirugía de esterilización'),
                ('Limpieza Dental', 1500.00, 'Profilaxis dental con anestesia'),
                ('Radiografía', 800.00, 'Estudio radiográfico'),
                ('Ultrasonido', 1200.00, 'Estudio de ultrasonido'),
                ('Análisis de Sangre Completo', 950.00, 'Biometría y química sanguínea'),
            ],
        }

        from django.utils.text import slugify

        product_count = 0
        for cat_name, products in categories_products.items():
            cat_slug = slugify(cat_name)
            category, _ = Category.objects.get_or_create(
                slug=cat_slug,
                defaults={
                    'name': cat_name,
                    'name_es': cat_name,
                    'name_en': cat_name,
                    'description': f'Categoría de {cat_name.lower()}',
                    'description_es': f'Categoría de {cat_name.lower()}',
                    'description_en': f'Category of {cat_name.lower()}',
                }
            )

            for name, price, description in products:
                slug = fake.unique.slug()
                Product.objects.get_or_create(
                    sku=f'SKU-{fake.unique.numerify("####")}',
                    defaults={
                        'name': name,
                        'name_es': name,
                        'name_en': name,
                        'slug': slug,
                        'category': category,
                        'price': Decimal(str(price)),
                        'description': description,
                        'description_es': description,
                        'description_en': description,
                        'stock_quantity': random.randint(5, 50),
                        'is_active': True,
                    }
                )
                product_count += 1

        self.stdout.write(f'    Created {product_count} products in {len(categories_products)} categories')

    def create_delivery_infrastructure(self):
        """Create delivery zones, slots, and drivers."""
        self.stdout.write('  Creating delivery infrastructure...')

        from apps.delivery.models import DeliveryZone, DeliverySlot, DeliveryDriver

        # Zones
        zones_data = [
            ('CDMX-CENTRO', 'Centro Histórico', 50, 30),
            ('CDMX-ROMA', 'Roma/Condesa', 45, 25),
            ('CDMX-POLANCO', 'Polanco', 55, 35),
            ('CDMX-COYOACAN', 'Coyoacán', 60, 40),
            ('CDMX-SANTAFE', 'Santa Fe', 75, 50),
            ('CDMX-NARVARTE', 'Narvarte/Del Valle', 50, 30),
        ]

        self.zones = []
        for code, name, fee, minutes in zones_data:
            zone, _ = DeliveryZone.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'delivery_fee': Decimal(str(fee)),
                    'estimated_time_minutes': minutes,
                }
            )
            self.zones.append(zone)

        # Slots for next 7 days (for each zone)
        slot_times = [(9, 12), (12, 15), (15, 18)]
        today = date.today()
        slots_created = 0

        for zone in self.zones:
            for day_offset in range(7):
                slot_date = today + timedelta(days=day_offset)
                for start_hour, end_hour in slot_times:
                    DeliverySlot.objects.get_or_create(
                        zone=zone,
                        date=slot_date,
                        start_time=time(start_hour, 0),
                        defaults={
                            'end_time': time(end_hour, 0),
                            'capacity': 10,
                            'booked_count': 0,
                        }
                    )
                    slots_created += 1

        # Drivers
        drivers_data = [
            ('driver_carlos', 'Carlos', 'Hernández', 'employee', 'motorcycle'),
            ('driver_maria', 'María', 'López', 'employee', 'car'),
            ('driver_juan', 'Juan', 'García', 'contractor', 'motorcycle'),
            ('driver_ana', 'Ana', 'Martínez', 'contractor', 'bicycle'),
        ]

        self.drivers = []
        for username, first, last, dtype, vehicle in drivers_data:
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@petfriendlyvet.test',
                    'first_name': first,
                    'last_name': last,
                }
            )
            user.set_password('driver123')
            user.save()

            driver, _ = DeliveryDriver.objects.get_or_create(
                user=user,
                defaults={
                    'driver_type': dtype,
                    'vehicle_type': vehicle,
                    'license_plate': fake.bothify('???-###').upper(),
                    'phone': fake.phone_number()[:15],
                    'max_deliveries_per_day': 15 if dtype == 'employee' else 20,
                    'rate_per_delivery': Decimal('35.00') if dtype == 'contractor' else None,
                    'rate_per_km': Decimal('5.00') if dtype == 'contractor' else None,
                    'rfc': fake.bothify('????######???').upper() if dtype == 'contractor' else '',
                }
            )
            driver.zones.set(self.zones[:3])
            self.drivers.append(driver)

        self.stdout.write(f'    Created {len(self.zones)} zones, {slots_created} slots, {len(self.drivers)} drivers')

    def create_customer_scenarios(self, num_customers):
        """Create customers with diverse pet scenarios."""
        self.stdout.write(self.style.NOTICE(f'\n👥 PHASE 2: Creating {num_customers} Customer Scenarios'))

        from apps.pets.models import Pet, MedicalCondition, Vaccination, Visit, Medication, ClinicalNote
        from apps.crm.models import OwnerProfile, CustomerTag, Interaction
        from apps.appointments.models import Appointment

        # Create tags
        tags_data = ['VIP', 'Nuevo Cliente', 'Frecuente', 'Referido', 'Moroso', 'Rescate']
        tags = []
        for tag_name in tags_data:
            tag, _ = CustomerTag.objects.get_or_create(
                name=tag_name,
                defaults={'color': fake.hex_color()}
            )
            tags.append(tag)

        # Customer scenarios - each with different characteristics
        scenarios = [
            self._scenario_new_puppy_owner,
            self._scenario_senior_pet_owner,
            self._scenario_multi_pet_household,
            self._scenario_rescue_pet_owner,
            self._scenario_chronic_condition_pet,
            self._scenario_emergency_case,
            self._scenario_regular_checkup_client,
            self._scenario_luxury_pet_owner,
            self._scenario_breeder_client,
            self._scenario_problem_client,
        ]

        for i in range(num_customers):
            scenario_func = scenarios[i % len(scenarios)]
            scenario_func(i + 1, tags)

        self.stdout.write(f'    Created {num_customers} customers with varied scenarios')

    def _scenario_new_puppy_owner(self, num, tags):
        """New owner with a puppy needing vaccinations."""
        self.stdout.write(f'  [{num}] 🐕 New Puppy Owner scenario...')

        from apps.pets.models import Pet, Vaccination, Visit
        from apps.crm.models import OwnerProfile
        from apps.appointments.models import Appointment

        user = self._create_customer(f'puppy_owner_{num}')
        profile = OwnerProfile.objects.create(
            user=user,
            preferred_contact_method='whatsapp',
            referral_source='Instagram',
            total_visits=2,
        )
        profile.tags.add(tags[1])  # Nuevo Cliente

        # Young puppy
        puppy = Pet.objects.create(
            owner=user,
            name=random.choice(['Max', 'Luna', 'Rocky', 'Bella']),
            species='dog',
            breed=random.choice(['Golden Retriever', 'Labrador', 'French Bulldog']),
            gender=random.choice(['male', 'female']),
            date_of_birth=date.today() - timedelta(days=random.randint(60, 120)),
            weight_kg=Decimal(str(random.uniform(3, 8))),
            is_neutered=False,
        )

        # First vaccination
        Vaccination.objects.create(
            pet=puppy,
            vaccine_name='Puppy DP',
            date_administered=date.today() - timedelta(days=14),
            next_due_date=date.today() + timedelta(days=14),
            administered_by=random.choice(self.vets),
        )

        # First visit
        Visit.objects.create(
            pet=puppy,
            date=timezone.now() - timedelta(days=14),
            reason='Primera consulta cachorro',
            diagnosis='Cachorro sano, iniciando esquema de vacunación',
            treatment='Desparasitación y primera vacuna',
            veterinarian=random.choice(self.vets),
            weight_kg=puppy.weight_kg,
        )

        # Upcoming vaccination appointment
        Appointment.objects.create(
            owner=user,
            pet=puppy,
            veterinarian=random.choice(self.vets),
            service=self.services.get('vacunacion', list(self.services.values())[0]),
            scheduled_start=timezone.now() + timedelta(days=random.randint(7, 14)),
            scheduled_end=timezone.now() + timedelta(days=random.randint(7, 14), minutes=30),
            status='confirmed',
            notes='Segunda vacuna puppy',
        )

    def _scenario_senior_pet_owner(self, num, tags):
        """Owner with an elderly pet with age-related issues."""
        self.stdout.write(f'  [{num}] 🐕‍🦺 Senior Pet scenario...')

        from apps.pets.models import Pet, MedicalCondition, Vaccination, Visit, Medication
        from apps.crm.models import OwnerProfile

        user = self._create_customer(f'senior_pet_{num}')
        profile = OwnerProfile.objects.create(
            user=user,
            preferred_contact_method='phone',
            total_visits=15,
            total_spent=Decimal('12500.00'),
        )
        profile.tags.add(tags[2])  # Frecuente

        # Senior dog
        dog = Pet.objects.create(
            owner=user,
            name=random.choice(['Canela', 'Firulais', 'Toby', 'Princesa']),
            species='dog',
            breed=random.choice(['Mestizo', 'Cocker Spaniel', 'Beagle']),
            gender=random.choice(['male', 'female']),
            date_of_birth=date.today() - timedelta(days=random.randint(3650, 5000)),  # 10-14 years
            weight_kg=Decimal(str(random.uniform(8, 20))),
            is_neutered=True,
            notes='Paciente geriátrico, requiere atención especial',
        )

        # Chronic conditions
        MedicalCondition.objects.create(
            pet=dog,
            name='Artritis',
            condition_type='chronic',
            diagnosed_date=date.today() - timedelta(days=365),
            notes='Artritis degenerativa en patas traseras',
            is_active=True,
        )

        MedicalCondition.objects.create(
            pet=dog,
            name='Enfermedad Renal Crónica Estadio II',
            condition_type='chronic',
            diagnosed_date=date.today() - timedelta(days=180),
            notes='Requiere dieta especial y monitoreo',
            is_active=True,
        )

        # Ongoing medication
        Medication.objects.create(
            pet=dog,
            name='Rimadyl',
            dosage='50mg',
            frequency='Cada 12 horas',
            start_date=date.today() - timedelta(days=90),
            prescribing_vet=random.choice(self.vets),
            notes='Para manejo del dolor articular',
        )

        # Regular visits
        for i in range(3):
            Visit.objects.create(
                pet=dog,
                date=timezone.now() - timedelta(days=30 * (i + 1)),
                reason='Control geriátrico' if i > 0 else 'Chequeo general',
                diagnosis='Estable con tratamiento actual',
                veterinarian=random.choice(self.vets),
                weight_kg=dog.weight_kg,
            )

        # Annual vaccines
        Vaccination.objects.create(
            pet=dog,
            vaccine_name='Rabia',
            date_administered=date.today() - timedelta(days=180),
            next_due_date=date.today() + timedelta(days=185),
            administered_by=random.choice(self.vets),
        )

    def _scenario_multi_pet_household(self, num, tags):
        """Family with multiple pets of different species."""
        self.stdout.write(f'  [{num}] 🏠 Multi-Pet Household scenario...')

        from apps.pets.models import Pet, Vaccination
        from apps.crm.models import OwnerProfile

        user = self._create_customer(f'multi_pet_{num}')
        profile = OwnerProfile.objects.create(
            user=user,
            preferred_contact_method='email',
            total_visits=8,
            total_spent=Decimal('8500.00'),
            notes='Familia con múltiples mascotas',
        )
        profile.tags.add(tags[2])  # Frecuente

        # Dog
        dog = Pet.objects.create(
            owner=user,
            name='Thor',
            species='dog',
            breed='Pastor Alemán',
            gender='male',
            date_of_birth=date.today() - timedelta(days=random.randint(730, 1825)),
            weight_kg=Decimal('32.5'),
            is_neutered=True,
        )

        # Cat
        cat = Pet.objects.create(
            owner=user,
            name='Michi',
            species='cat',
            breed='Siamés',
            gender='female',
            date_of_birth=date.today() - timedelta(days=random.randint(365, 1460)),
            weight_kg=Decimal('4.2'),
            is_neutered=True,
        )

        # Rabbit
        rabbit = Pet.objects.create(
            owner=user,
            name='Copito',
            species='rabbit',
            breed='Holland Lop',
            gender='male',
            date_of_birth=date.today() - timedelta(days=random.randint(180, 730)),
            weight_kg=Decimal('2.1'),
        )

        # Vaccinations for each
        for pet in [dog, cat]:
            Vaccination.objects.create(
                pet=pet,
                vaccine_name='Rabia',
                date_administered=date.today() - timedelta(days=random.randint(30, 300)),
                next_due_date=date.today() + timedelta(days=random.randint(60, 330)),
                administered_by=random.choice(self.vets),
            )

    def _scenario_rescue_pet_owner(self, num, tags):
        """Owner who adopted a rescue with unknown history."""
        self.stdout.write(f'  [{num}] 🐾 Rescue Pet scenario...')

        from apps.pets.models import Pet, MedicalCondition, Visit
        from apps.crm.models import OwnerProfile

        user = self._create_customer(f'rescue_{num}')
        profile = OwnerProfile.objects.create(
            user=user,
            preferred_contact_method='whatsapp',
            referral_source='Fundación Rescate Animal',
            total_visits=3,
        )
        profile.tags.add(tags[5])  # Rescate

        # Rescue dog with issues
        dog = Pet.objects.create(
            owner=user,
            name='Lucky',
            species='dog',
            breed='Mestizo',
            gender='male',
            date_of_birth=date.today() - timedelta(days=random.randint(730, 2190)),  # Estimated age
            weight_kg=Decimal(str(random.uniform(10, 20))),
            is_neutered=True,
            notes='Adoptado de la calle. Historia médica desconocida.',
        )

        # Past trauma/condition
        MedicalCondition.objects.create(
            pet=dog,
            name='Ansiedad por separación',
            condition_type='other',
            diagnosed_date=date.today() - timedelta(days=60),
            notes='Probablemente relacionado con abandono previo',
            is_active=True,
        )

        MedicalCondition.objects.create(
            pet=dog,
            name='Cicatriz en pata derecha',
            condition_type='injury',
            diagnosed_date=date.today() - timedelta(days=90),
            notes='Lesión antigua, completamente sanada',
            is_active=False,
        )

        # Initial evaluation visit
        Visit.objects.create(
            pet=dog,
            date=timezone.now() - timedelta(days=90),
            reason='Evaluación inicial post-adopción',
            diagnosis='Desnutrición leve, parásitos intestinales. Por lo demás sano.',
            treatment='Desparasitación, suplementos vitamínicos, dieta de recuperación',
            veterinarian=random.choice(self.vets),
            weight_kg=Decimal(str(float(dog.weight_kg) - 2)),
        )

    def _scenario_chronic_condition_pet(self, num, tags):
        """Pet with a chronic condition requiring ongoing care."""
        self.stdout.write(f'  [{num}] 💊 Chronic Condition scenario...')

        from apps.pets.models import Pet, MedicalCondition, Medication, Visit
        from apps.crm.models import OwnerProfile

        user = self._create_customer(f'chronic_{num}')
        profile = OwnerProfile.objects.create(
            user=user,
            preferred_contact_method='phone',
            total_visits=20,
            total_spent=Decimal('25000.00'),
            notes='Cliente frecuente por condición crónica de mascota',
        )
        profile.tags.add(tags[0], tags[2])  # VIP, Frecuente

        # Diabetic cat
        cat = Pet.objects.create(
            owner=user,
            name='Garfield',
            species='cat',
            breed='Mestizo',
            gender='male',
            date_of_birth=date.today() - timedelta(days=random.randint(2555, 4380)),  # 7-12 years
            weight_kg=Decimal('6.8'),
            is_neutered=True,
            notes='Diabético. Requiere insulina dos veces al día.',
        )

        MedicalCondition.objects.create(
            pet=cat,
            name='Diabetes Mellitus',
            condition_type='chronic',
            diagnosed_date=date.today() - timedelta(days=365),
            notes='Controlado con insulina. Curva de glucosa estable.',
            is_active=True,
        )

        Medication.objects.create(
            pet=cat,
            name='Insulina Lantus',
            dosage='2 unidades',
            frequency='Cada 12 horas',
            start_date=date.today() - timedelta(days=365),
            prescribing_vet=random.choice(self.vets),
            notes='Administrar con comida. Monitorear signos de hipoglucemia.',
        )

        # Regular glucose monitoring visits
        for i in range(6):
            Visit.objects.create(
                pet=cat,
                date=timezone.now() - timedelta(days=30 * i),
                reason='Control de glucosa',
                diagnosis=f'Glucosa: {random.randint(100, 180)} mg/dL. {"Estable" if i < 4 else "Ajustar dosis"}',
                veterinarian=random.choice(self.vets),
                weight_kg=cat.weight_kg,
            )

    def _scenario_emergency_case(self, num, tags):
        """Recent emergency case requiring follow-up."""
        self.stdout.write(f'  [{num}] 🚨 Emergency Case scenario...')

        from apps.pets.models import Pet, Visit, Medication, ClinicalNote
        from apps.crm.models import OwnerProfile
        from apps.appointments.models import Appointment

        user = self._create_customer(f'emergency_{num}')
        profile = OwnerProfile.objects.create(
            user=user,
            preferred_contact_method='phone',
            total_visits=3,
            total_spent=Decimal('4500.00'),
        )

        # Dog that ate something toxic
        dog = Pet.objects.create(
            owner=user,
            name='Rocco',
            species='dog',
            breed='Bulldog Francés',
            gender='male',
            date_of_birth=date.today() - timedelta(days=random.randint(365, 1095)),
            weight_kg=Decimal('12.5'),
            is_neutered=True,
        )

        # Emergency visit
        Visit.objects.create(
            pet=dog,
            date=timezone.now() - timedelta(days=3),
            reason='EMERGENCIA: Ingesta de chocolate',
            diagnosis='Intoxicación por teobromina. Signos vitales estables post-tratamiento.',
            treatment='Inducción al vómito, carbón activado, fluidos IV, monitoreo 24hrs',
            veterinarian=self.head_vet,
            weight_kg=dog.weight_kg,
            follow_up_date=date.today() + timedelta(days=4),
        )

        ClinicalNote.objects.create(
            pet=dog,
            author=self.head_vet,
            note='Paciente ingirió aproximadamente 100g de chocolate oscuro. Propietario trajo empaque. Tratamiento inmediato exitoso. Alta con instrucciones de monitoreo.',
            note_type='treatment',
        )

        Medication.objects.create(
            pet=dog,
            name='Famotidina',
            dosage='10mg',
            frequency='Cada 12 horas',
            start_date=date.today() - timedelta(days=3),
            end_date=date.today() + timedelta(days=4),
            prescribing_vet=self.head_vet,
            notes='Protector gástrico post-intoxicación',
        )

        # Follow-up appointment
        Appointment.objects.create(
            owner=user,
            pet=dog,
            veterinarian=self.head_vet,
            service=self.services.get('consulta_de_seguimiento', list(self.services.values())[0]),
            scheduled_start=timezone.now() + timedelta(days=4),
            scheduled_end=timezone.now() + timedelta(days=4, minutes=30),
            status='confirmed',
            notes='Seguimiento post-intoxicación',
        )

    def _scenario_regular_checkup_client(self, num, tags):
        """Regular client with healthy pets."""
        self.stdout.write(f'  [{num}] ✅ Regular Checkup Client scenario...')

        from apps.pets.models import Pet, Vaccination, Visit
        from apps.crm.models import OwnerProfile

        user = self._create_customer(f'regular_{num}')
        profile = OwnerProfile.objects.create(
            user=user,
            preferred_contact_method='email',
            total_visits=10,
            total_spent=Decimal('6500.00'),
        )
        profile.tags.add(tags[2])  # Frecuente

        dog = Pet.objects.create(
            owner=user,
            name=random.choice(['Bruno', 'Coco', 'Nala', 'Simba']),
            species='dog',
            breed=random.choice(['Schnauzer', 'Poodle', 'Beagle']),
            gender=random.choice(['male', 'female']),
            date_of_birth=date.today() - timedelta(days=random.randint(730, 2555)),
            weight_kg=Decimal(str(random.uniform(8, 15))),
            is_neutered=True,
        )

        # All vaccines up to date
        vaccines = ['Rabia', 'Múltiple Canina', 'Bordetella']
        for vaccine in vaccines:
            Vaccination.objects.create(
                pet=dog,
                vaccine_name=vaccine,
                date_administered=date.today() - timedelta(days=random.randint(60, 300)),
                next_due_date=date.today() + timedelta(days=random.randint(60, 300)),
                administered_by=random.choice(self.vets),
            )

        # Regular annual visits
        for i in range(2):
            Visit.objects.create(
                pet=dog,
                date=timezone.now() - timedelta(days=365 * i + random.randint(0, 30)),
                reason='Chequeo anual',
                diagnosis='Paciente sano. Sin hallazgos anormales.',
                treatment='Desparasitación preventiva',
                veterinarian=random.choice(self.vets),
                weight_kg=dog.weight_kg,
            )

    def _scenario_luxury_pet_owner(self, num, tags):
        """High-end client with premium services."""
        self.stdout.write(f'  [{num}] 👑 Luxury Pet Owner scenario...')

        from apps.pets.models import Pet, Vaccination
        from apps.crm.models import OwnerProfile
        from apps.store.models import Order, OrderItem, Product

        user = self._create_customer(f'luxury_{num}')
        profile = OwnerProfile.objects.create(
            user=user,
            preferred_contact_method='whatsapp',
            preferred_language='en',
            total_visits=12,
            total_spent=Decimal('45000.00'),
            notes='Cliente premium. Prefiere productos de alta gama.',
        )
        profile.tags.add(tags[0])  # VIP

        # Purebred show dog
        dog = Pet.objects.create(
            owner=user,
            name='Duchess',
            species='dog',
            breed='Yorkshire Terrier',
            gender='female',
            date_of_birth=date.today() - timedelta(days=random.randint(365, 1460)),
            weight_kg=Decimal('3.2'),
            is_neutered=False,
            microchip_id=fake.numerify('###############'),
            notes='Pedigree registrado. Participante en exposiciones.',
        )

        # Premium vaccinations
        for vaccine in ['Rabia', 'Múltiple Canina', 'Leptospirosis', 'Bordetella']:
            Vaccination.objects.create(
                pet=dog,
                vaccine_name=vaccine,
                date_administered=date.today() - timedelta(days=random.randint(30, 180)),
                next_due_date=date.today() + timedelta(days=random.randint(180, 330)),
                administered_by=self.head_vet,
            )

        # Premium product orders
        premium_products = list(Product.objects.filter(price__gte=500)[:3])
        if premium_products:
            subtotal = sum(p.price for p in premium_products)
            shipping_cost = Decimal('50.00')
            tax = subtotal * Decimal('0.16')
            total = subtotal + shipping_cost + tax
            order = Order.objects.create(
                user=user,
                order_number=Order.generate_order_number(),
                status='delivered',
                fulfillment_method='delivery',
                payment_method='card',
                shipping_address=fake.address(),
                subtotal=subtotal,
                shipping_cost=shipping_cost,
                tax=tax,
                total=total,
            )
            for product in premium_products:
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_name=product.name,
                    product_sku=product.sku,
                    price=product.price,
                    quantity=1,
                )

    def _scenario_breeder_client(self, num, tags):
        """Professional breeder with multiple litters."""
        self.stdout.write(f'  [{num}] 🐶 Breeder Client scenario...')

        from apps.pets.models import Pet, Vaccination
        from apps.crm.models import OwnerProfile

        user = self._create_customer(f'breeder_{num}')
        profile = OwnerProfile.objects.create(
            user=user,
            preferred_contact_method='phone',
            total_visits=25,
            total_spent=Decimal('35000.00'),
            notes='Criador profesional de Golden Retrievers',
        )
        profile.tags.add(tags[0], tags[2])  # VIP, Frecuente

        # Breeding female
        mother = Pet.objects.create(
            owner=user,
            name='Goldie',
            species='dog',
            breed='Golden Retriever',
            gender='female',
            date_of_birth=date.today() - timedelta(days=random.randint(1095, 1825)),
            weight_kg=Decimal('28.5'),
            is_neutered=False,
            microchip_id=fake.numerify('###############'),
            notes='Reproductora activa. Último parto hace 6 meses.',
        )

        # Puppies from last litter
        for i in range(4):
            puppy = Pet.objects.create(
                owner=user,
                name=f'Puppy {i + 1}',
                species='dog',
                breed='Golden Retriever',
                gender=random.choice(['male', 'female']),
                date_of_birth=date.today() - timedelta(days=60),
                weight_kg=Decimal(str(random.uniform(4, 6))),
                is_neutered=False,
                notes='Camada para venta',
            )

            Vaccination.objects.create(
                pet=puppy,
                vaccine_name='Puppy DP',
                date_administered=date.today() - timedelta(days=14),
                next_due_date=date.today() + timedelta(days=14),
                administered_by=random.choice(self.vets),
            )

    def _scenario_problem_client(self, num, tags):
        """Difficult client with payment issues or complaints."""
        self.stdout.write(f'  [{num}] ⚠️ Problem Client scenario...')

        from apps.pets.models import Pet
        from apps.crm.models import OwnerProfile, Interaction, CustomerNote

        user = self._create_customer(f'problem_{num}')
        profile = OwnerProfile.objects.create(
            user=user,
            preferred_contact_method='phone',
            total_visits=5,
            total_spent=Decimal('1200.00'),
            notes='⚠️ ATENCIÓN: Historial de pagos pendientes',
        )
        profile.tags.add(tags[4])  # Moroso

        dog = Pet.objects.create(
            owner=user,
            name='Bandido',
            species='dog',
            breed='Pitbull',
            gender='male',
            date_of_birth=date.today() - timedelta(days=random.randint(730, 1825)),
            weight_kg=Decimal('28.0'),
            is_neutered=False,
        )

        # Problem interactions
        Interaction.objects.create(
            owner_profile=profile,
            interaction_type='call',
            channel='phone',
            direction='outbound',
            subject='Cobranza - Factura pendiente',
            notes='Cliente no contesta. Tercer intento de contacto.',
            handled_by=random.choice(self.staff),
            outcome='Sin respuesta',
            follow_up_required=True,
            follow_up_date=date.today() + timedelta(days=7),
        )

        CustomerNote.objects.create(
            owner_profile=profile,
            author=random.choice(self.staff),
            content='Cliente tiene $1,500 pendientes de pago desde hace 45 días. Ha prometido pagar pero no ha cumplido. Considerar requerir pago por adelantado en próximas visitas.',
            is_pinned=True,
            is_private=False,
        )

    def _create_customer(self, username_base):
        """Create a customer user."""
        user, _ = User.objects.get_or_create(
            username=username_base,
            defaults={
                'email': f'{username_base}@test.petfriendlyvet.com',
                'first_name': fake.first_name(),
                'last_name': fake.last_name(),
                'phone_number': fake.phone_number()[:15],
                'role': 'owner',
            }
        )
        user.set_password('customer123')
        user.save()
        return user

    def create_workflow_scenarios(self):
        """Create additional workflow scenarios."""
        self.stdout.write(self.style.NOTICE('\n🔄 PHASE 3: Workflow Scenarios'))

        self.create_pending_appointments()
        self.create_pending_orders()

    def create_pending_appointments(self):
        """Create appointments for today and upcoming days."""
        self.stdout.write('  Creating pending appointments...')

        from apps.appointments.models import Appointment
        from apps.pets.models import Pet

        pets = list(Pet.objects.all()[:10])
        if not pets:
            return

        service_keys = ['consulta_general', 'vacunacion', 'chequeo_geriatrico', 'desparasitacion']
        for i, pet in enumerate(pets):
            service_key = random.choice(service_keys)
            service = self.services.get(service_key, list(self.services.values())[0])
            Appointment.objects.create(
                owner=pet.owner,
                pet=pet,
                veterinarian=random.choice(self.vets),
                service=service,
                scheduled_start=timezone.now() + timedelta(hours=random.randint(1, 72)),
                scheduled_end=timezone.now() + timedelta(hours=random.randint(1, 72), minutes=30),
                status=random.choice(['scheduled', 'confirmed']),
                notes=random.choice(['Consulta general', 'Vacunación', 'Revisión']),
            )

        self.stdout.write(f'    Created {len(pets)} upcoming appointments')

    def create_pending_orders(self):
        """Create pending orders for testing."""
        self.stdout.write('  Creating pending orders...')

        from apps.store.models import Order, OrderItem, Product

        products = list(Product.objects.filter(is_active=True)[:10])
        customers = list(User.objects.filter(role='owner')[:5])

        if not products or not customers:
            return

        orders_created = 0
        for customer in customers:
            order_products = random.sample(products, min(3, len(products)))
            quantities = {p.id: random.randint(1, 3) for p in order_products}

            subtotal = sum(p.price * quantities[p.id] for p in order_products)
            fulfillment = random.choice(['pickup', 'delivery'])
            shipping_cost = Decimal('50.00') if fulfillment == 'delivery' else Decimal('0')
            tax = subtotal * Decimal('0.16')
            total = subtotal + shipping_cost + tax

            order = Order.objects.create(
                user=customer,
                order_number=Order.generate_order_number(),
                status=random.choice(['pending', 'paid', 'preparing']),
                fulfillment_method=fulfillment,
                payment_method=random.choice(['cash', 'card']),
                shipping_address=fake.address() if fulfillment == 'delivery' else '',
                subtotal=subtotal,
                shipping_cost=shipping_cost,
                tax=tax,
                total=total,
            )

            for product in order_products:
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_name=product.name,
                    product_sku=product.sku,
                    price=product.price,
                    quantity=quantities[product.id],
                )
            orders_created += 1

        self.stdout.write(f'    Created {orders_created} pending orders')

    def print_summary(self):
        """Print summary of generated data."""
        from apps.pets.models import Pet, Visit, Vaccination
        from apps.appointments.models import Appointment
        from apps.store.models import Product, Order
        from apps.crm.models import OwnerProfile

        self.stdout.write('\n📊 Data Summary:')
        self.stdout.write(f'  👥 Customers (OwnerProfiles): {OwnerProfile.objects.count()}')
        self.stdout.write(f'  🐾 Pets: {Pet.objects.count()}')
        self.stdout.write(f'  💉 Vaccinations: {Vaccination.objects.count()}')
        self.stdout.write(f'  🏥 Visits: {Visit.objects.count()}')
        self.stdout.write(f'  📅 Appointments: {Appointment.objects.count()}')
        self.stdout.write(f'  🛒 Products: {Product.objects.count()}')
        self.stdout.write(f'  📦 Orders: {Order.objects.count()}')

        self.stdout.write('\n🔑 Test Credentials:')
        self.stdout.write('  Vets: dr_rodriguez/vet123, dra_martinez/vet123')
        self.stdout.write('  Staff: recepcion1/staff123')
        self.stdout.write('  Drivers: driver_carlos/driver123')
        self.stdout.write('  Customers: puppy_owner_1/customer123, etc.')
