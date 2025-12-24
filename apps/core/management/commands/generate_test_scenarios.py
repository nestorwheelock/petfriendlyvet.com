"""
Generate comprehensive test scenarios for the Pet-Friendly Vet application.

This command creates realistic test data including:
- Clinic setup (staff, vets, services, products)
- Customers with various pet profiles
- Medical histories (normal and abnormal)
- Appointments, visits, orders, deliveries
- Simulated workflows and edge cases
- FULL FINANCIAL SIMULATION:
  - Service pricing (doctor sets prices)
  - Chart of accounts (Mexican accounting)
  - Invoices/facturas with CFDI
  - Customer payments
  - Vendor bills & payments (accounts payable)
  - Inventory & stock movements
  - Pharmacy prescriptions

Usage:
    python manage.py generate_test_scenarios
    python manage.py generate_test_scenarios --customers 50
    python manage.py generate_test_scenarios --clear

    # Simulate 6 months of clinic history (2 new customers/day)
    python manage.py generate_test_scenarios --simulate-history --months 6
"""
import random
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from faker import Faker

User = get_user_model()
fake = Faker(['es_MX', 'en_US'])

# Clinical note templates for realistic documentation
CLINICAL_NOTES = {
    'consultation': [
        "Paciente presenta buen estado general. Mucosas rosadas, tiempo de llenado capilar normal.",
        "Auscultación cardiopulmonar sin alteraciones. Frecuencia cardíaca y respiratoria dentro de rangos normales.",
        "Abdomen blando, no doloroso a la palpación. Sin masas palpables.",
        "Piel y pelaje en buenas condiciones. Sin evidencia de parásitos externos.",
        "Paciente alerta y reactivo. Comportamiento normal durante la consulta.",
        "Se recomienda continuar con alimentación actual y ejercicio moderado.",
        "Propietario refiere que mascota come y bebe con normalidad.",
        "Sin cambios en comportamiento según propietario.",
    ],
    'vaccination': [
        "Se aplica vacuna según protocolo. Paciente toleró bien la aplicación.",
        "Se recomienda observación por 24-48 hrs por posibles reacciones.",
        "Próxima vacuna programada según calendario de vacunación.",
        "Se actualiza cartilla de vacunación.",
        "Paciente en buen estado para recibir vacuna. Sin contraindicaciones.",
    ],
    'followup': [
        "Evolución favorable desde última consulta.",
        "Paciente muestra mejoría significativa.",
        "Se ajusta tratamiento según evolución.",
        "Continuar con medicación indicada.",
        "Propietario reporta mejoría en síntomas.",
        "Herida/lesión cicatrizando adecuadamente.",
    ],
    'illness': [
        "Paciente presenta decaimiento y pérdida de apetito desde hace {} días.",
        "Se observa {} leve. Se indica tratamiento sintomático.",
        "Propietario reporta vómitos/diarrea intermitentes.",
        "Se solicitan estudios complementarios para descartar patología.",
        "Paciente deshidratado. Se administra fluidoterapia.",
        "Se prescribe antibiótico/antiinflamatorio por {} días.",
    ],
    'dental': [
        "Se realiza limpieza dental bajo anestesia general.",
        "Se extraen {} piezas dentales con movilidad grado III.",
        "Sarro moderado/severo. Gingivitis presente.",
        "Paciente recuperó bien de anestesia. Alta con indicaciones.",
    ],
    'surgery': [
        "Cirugía realizada sin complicaciones.",
        "Paciente estable durante procedimiento.",
        "Se indica reposo absoluto por {} días.",
        "Curación cada 48 hrs. Retiro de puntos en 10-14 días.",
        "Collar isabelino obligatorio hasta retiro de puntos.",
    ],
}

VISIT_DIAGNOSES = [
    "Paciente sano. Chequeo rutinario.",
    "Gastroenteritis leve. Tratamiento sintomático.",
    "Otitis externa bilateral. Tratamiento tópico.",
    "Dermatitis alérgica. Se inicia tratamiento.",
    "Conjuntivitis. Colirio indicado.",
    "Parasitosis intestinal. Desparasitación.",
    "Infección urinaria. Antibiótico por 7 días.",
    "Artritis degenerativa. Manejo del dolor.",
    "Obesidad. Plan de alimentación y ejercicio.",
    "Ansiedad por separación. Modificación conductual.",
]

VISIT_TREATMENTS = [
    "Observación. Control en 1 semana si persisten síntomas.",
    "Metronidazol 250mg c/12h x 5 días. Dieta blanda.",
    "Limpieza ótica + gotas Otomax c/12h x 10 días.",
    "Apoquel 16mg c/24h. Baños medicados semanales.",
    "Tobramicina oftálmica c/8h x 7 días.",
    "Fenbendazol 50mg/kg dosis única. Repetir en 15 días.",
    "Enrofloxacina 5mg/kg c/24h x 7 días.",
    "Rimadyl 2mg/kg c/12h. Suplemento articular.",
    "Reducción 20% ración. Caminatas 30 min diarios.",
    "Ejercicio antes de salir. Enriquecimiento ambiental.",
]


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
        parser.add_argument(
            '--simulate-history',
            action='store_true',
            help='Simulate clinic history over time (ignores --customers)'
        )
        parser.add_argument(
            '--months',
            type=int,
            default=6,
            help='Number of months of history to simulate (default: 6)'
        )
        parser.add_argument(
            '--customers-per-day',
            type=int,
            default=2,
            help='Average new customers per day (default: 2)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('🏥 Pet-Friendly Vet - Test Scenario Generator'))
        self.stdout.write('=' * 60)

        if options['clear']:
            self.clear_test_data()

        if not options['skip_clinic']:
            self.setup_clinic()

        if options['simulate_history']:
            # Historical simulation mode
            self.simulate_clinic_history(
                months=options['months'],
                customers_per_day=options['customers_per_day']
            )
        else:
            # Original mode
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
        """Set up clinic infrastructure: staff, vets, products, services, finances."""
        self.stdout.write(self.style.NOTICE('\n📋 PHASE 1: Clinic Setup'))

        self.create_staff()
        self.create_service_types()
        self.create_services_catalog()  # Service pricing for billing
        self.create_products()
        self.create_delivery_infrastructure()
        self.setup_chart_of_accounts()
        self.create_vendors_and_suppliers()
        self.create_inventory_infrastructure()
        self.create_medications_catalog()

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

    def create_services_catalog(self):
        """Create billing services with pricing (doctor sets prices)."""
        self.stdout.write('  Creating services catalog with pricing...')

        from apps.services.models import Service

        # SAT codes for CFDI compliance
        # 85121800 = Servicios de medicina veterinaria
        services_data = [
            # (name, name_es, category, base_price, duration, sat_code)
            ('General Consultation', 'Consulta General', 'consultation', 500.00, 30, '85121800'),
            ('Follow-up Consultation', 'Consulta de Seguimiento', 'consultation', 350.00, 20, '85121800'),
            ('Senior Pet Checkup', 'Chequeo Geriátrico', 'consultation', 650.00, 45, '85121800'),
            ('Emergency Consultation', 'Consulta de Emergencia', 'emergency', 900.00, 45, '85121800'),
            ('Vaccination', 'Vacunación', 'vaccination', 400.00, 15, '85121800'),
            ('Deworming', 'Desparasitación', 'preventive', 250.00, 15, '85121800'),
            ('Rabies Vaccine', 'Vacuna Antirrábica', 'vaccination', 350.00, 15, '85121800'),
            ('Multiple Canine Vaccine', 'Vacuna Múltiple Canina', 'vaccination', 550.00, 15, '85121800'),
            ('Triple Feline Vaccine', 'Vacuna Triple Felina', 'vaccination', 480.00, 15, '85121800'),
            ('Dental Cleaning', 'Limpieza Dental', 'dental', 1800.00, 60, '85121800'),
            ('Tooth Extraction', 'Extracción Dental', 'dental', 500.00, 30, '85121800'),
            ('Spay Surgery', 'Esterilización Hembra', 'surgery', 2200.00, 90, '85121800'),
            ('Neuter Surgery', 'Castración Macho', 'surgery', 1500.00, 60, '85121800'),
            ('Minor Surgery', 'Cirugía Menor', 'surgery', 1200.00, 45, '85121800'),
            ('Major Surgery', 'Cirugía Mayor', 'surgery', 4500.00, 120, '85121800'),
            ('X-Ray', 'Radiografía', 'imaging', 800.00, 30, '85121800'),
            ('Ultrasound', 'Ultrasonido', 'imaging', 1200.00, 45, '85121800'),
            ('Complete Blood Work', 'Análisis de Sangre Completo', 'laboratory', 950.00, 30, '85121800'),
            ('Urinalysis', 'Análisis de Orina', 'laboratory', 350.00, 15, '85121800'),
            ('Stool Analysis', 'Análisis Coprológico', 'laboratory', 280.00, 15, '85121800'),
            ('Skin Scraping', 'Raspado de Piel', 'laboratory', 320.00, 20, '85121800'),
            ('Grooming Bath', 'Baño y Corte', 'grooming', 450.00, 60, '85121800'),
            ('Medicated Bath', 'Baño Medicado', 'grooming', 550.00, 60, '85121800'),
            ('Hospitalization (per day)', 'Hospitalización (por día)', 'other', 800.00, 0, '85121800'),
            ('Euthanasia', 'Eutanasia', 'other', 1500.00, 60, '85121800'),
        ]

        self.billing_services = {}
        for name, name_es, category, price, duration, sat_code in services_data:
            from django.utils.text import slugify
            service, _ = Service.objects.get_or_create(
                name=name,
                defaults={
                    'name_es': name_es,
                    'description': f'{name_es} - servicio veterinario',
                    'category': category,
                    'base_price': Decimal(str(price)),
                    'duration_minutes': duration,
                    'clave_producto_sat': sat_code,
                    'clave_unidad_sat': 'E48',  # Unit of service
                    'is_active': True,
                    'requires_appointment': category not in ['other'],
                }
            )
            key = name.lower().replace(' ', '_').replace('-', '_')
            self.billing_services[key] = service

        self.stdout.write(f'    Created {len(services_data)} billing services with pricing')

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

    def setup_chart_of_accounts(self):
        """Create Mexican-standard chart of accounts for double-entry bookkeeping."""
        self.stdout.write('  Setting up chart of accounts...')

        from apps.accounting.models import Account

        # Mexican standard chart of accounts (Catálogo de Cuentas)
        accounts_data = [
            # Assets (Activos) - 1xxx
            ('1000', 'Activos', 'asset', None, False, False, False),
            ('1100', 'Caja y Bancos', 'asset', '1000', False, False, False),
            ('1101', 'Caja General', 'asset', '1100', False, False, False),
            ('1102', 'Caja Chica', 'asset', '1100', False, False, False),
            ('1110', 'Bancos', 'asset', '1100', True, False, False),
            ('1111', 'BBVA - Cuenta Principal', 'asset', '1110', True, False, False),
            ('1112', 'Santander - Cuenta de Respaldo', 'asset', '1110', True, False, False),
            ('1200', 'Cuentas por Cobrar', 'asset', '1000', False, True, False),
            ('1201', 'Clientes', 'asset', '1200', False, True, False),
            ('1202', 'Documentos por Cobrar', 'asset', '1200', False, True, False),
            ('1300', 'Inventarios', 'asset', '1000', False, False, False),
            ('1301', 'Inventario de Productos', 'asset', '1300', False, False, False),
            ('1302', 'Inventario de Medicamentos', 'asset', '1300', False, False, False),
            ('1400', 'Activo Fijo', 'asset', '1000', False, False, False),
            ('1401', 'Equipo Médico', 'asset', '1400', False, False, False),
            ('1402', 'Mobiliario y Equipo de Oficina', 'asset', '1400', False, False, False),
            ('1403', 'Equipo de Cómputo', 'asset', '1400', False, False, False),
            ('1404', 'Vehículos', 'asset', '1400', False, False, False),

            # Liabilities (Pasivos) - 2xxx
            ('2000', 'Pasivos', 'liability', None, False, False, False),
            ('2100', 'Cuentas por Pagar', 'liability', '2000', False, False, True),
            ('2101', 'Proveedores', 'liability', '2100', False, False, True),
            ('2102', 'Acreedores Diversos', 'liability', '2100', False, False, True),
            ('2200', 'Impuestos por Pagar', 'liability', '2000', False, False, False),
            ('2201', 'IVA Trasladado', 'liability', '2200', False, False, False),
            ('2202', 'ISR por Pagar', 'liability', '2200', False, False, False),
            ('2203', 'Retenciones', 'liability', '2200', False, False, False),
            ('2300', 'Nómina por Pagar', 'liability', '2000', False, False, False),

            # Equity (Capital) - 3xxx
            ('3000', 'Capital Contable', 'equity', None, False, False, False),
            ('3100', 'Capital Social', 'equity', '3000', False, False, False),
            ('3200', 'Resultados de Ejercicios Anteriores', 'equity', '3000', False, False, False),
            ('3300', 'Resultado del Ejercicio', 'equity', '3000', False, False, False),

            # Revenue (Ingresos) - 4xxx
            ('4000', 'Ingresos', 'revenue', None, False, False, False),
            ('4100', 'Ingresos por Servicios', 'revenue', '4000', False, False, False),
            ('4101', 'Consultas Veterinarias', 'revenue', '4100', False, False, False),
            ('4102', 'Cirugías', 'revenue', '4100', False, False, False),
            ('4103', 'Vacunaciones', 'revenue', '4100', False, False, False),
            ('4104', 'Laboratorio e Imagenología', 'revenue', '4100', False, False, False),
            ('4105', 'Hospitalización', 'revenue', '4100', False, False, False),
            ('4106', 'Grooming', 'revenue', '4100', False, False, False),
            ('4200', 'Ingresos por Ventas', 'revenue', '4000', False, False, False),
            ('4201', 'Venta de Productos', 'revenue', '4200', False, False, False),
            ('4202', 'Venta de Medicamentos', 'revenue', '4200', False, False, False),
            ('4300', 'Otros Ingresos', 'revenue', '4000', False, False, False),

            # Expenses (Gastos) - 5xxx
            ('5000', 'Costos y Gastos', 'expense', None, False, False, False),
            ('5100', 'Costo de Ventas', 'expense', '5000', False, False, False),
            ('5101', 'Costo de Productos Vendidos', 'expense', '5100', False, False, False),
            ('5102', 'Costo de Medicamentos', 'expense', '5100', False, False, False),
            ('5200', 'Gastos de Operación', 'expense', '5000', False, False, False),
            ('5201', 'Sueldos y Salarios', 'expense', '5200', False, False, False),
            ('5202', 'Renta', 'expense', '5200', False, False, False),
            ('5203', 'Servicios Públicos', 'expense', '5200', False, False, False),
            ('5204', 'Mantenimiento y Reparaciones', 'expense', '5200', False, False, False),
            ('5205', 'Suministros de Oficina', 'expense', '5200', False, False, False),
            ('5206', 'Publicidad y Marketing', 'expense', '5200', False, False, False),
            ('5207', 'Seguros', 'expense', '5200', False, False, False),
            ('5208', 'Depreciación', 'expense', '5200', False, False, False),
            ('5209', 'Gastos de Envío', 'expense', '5200', False, False, False),
            ('5300', 'Gastos Financieros', 'expense', '5000', False, False, False),
            ('5301', 'Comisiones Bancarias', 'expense', '5300', False, False, False),
            ('5302', 'Intereses Pagados', 'expense', '5300', False, False, False),
        ]

        self.accounts = {}
        for code, name, acc_type, parent_code, is_bank, is_ar, is_ap in accounts_data:
            parent = self.accounts.get(parent_code) if parent_code else None
            account, _ = Account.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'account_type': acc_type,
                    'parent': parent,
                    'is_bank': is_bank,
                    'is_ar': is_ar,
                    'is_ap': is_ap,
                    'is_active': True,
                }
            )
            self.accounts[code] = account

        self.stdout.write(f'    Created {len(accounts_data)} accounts in chart of accounts')

    def create_vendors_and_suppliers(self):
        """Create vendors/suppliers for accounts payable and inventory."""
        self.stdout.write('  Creating vendors and suppliers...')

        from apps.accounting.models import Vendor
        from apps.inventory.models import Supplier

        # Major veterinary product suppliers in Mexico
        vendors_data = [
            ('Vetoquinol México', 'VQM891201ABC', 'veterinary', 'net30', 'Productos veterinarios'),
            ('Royal Canin México', 'RCM950415XYZ', 'food', 'net30', 'Alimentos premium para mascotas'),
            ('Hills Pet Nutrition', 'HPN880520DEF', 'food', 'net30', 'Alimentos científicos'),
            ('Boehringer Ingelheim', 'BIV910615GHI', 'pharma', 'net15', 'Vacunas y medicamentos'),
            ('Zoetis México', 'ZMX850301JKL', 'pharma', 'net30', 'Productos farmacéuticos veterinarios'),
            ('MSD Salud Animal', 'MSA900720MNO', 'pharma', 'net30', 'Medicamentos y biológicos'),
            ('Distribuidora Veterinaria del Centro', 'DVC750810PQR', 'distributor', 'net15', 'Distribución general'),
            ('Equipos Médicos Veterinarios', 'EMV801105STU', 'equipment', 'net60', 'Equipos e instrumental'),
            ('Papelería y Suministros SA', 'PSS930225VWX', 'office', 'net15', 'Suministros de oficina'),
            ('CFE - Comisión Federal de Electricidad', 'CFE800101YZA', 'utility', 'prepaid', 'Electricidad'),
        ]

        self.vendors = {}
        self.suppliers = {}

        for name, rfc, category, terms, desc in vendors_data:
            # Create accounting vendor
            expense_account = self.accounts.get('5101') if category in ['food', 'pharma'] else self.accounts.get('5205')
            vendor, _ = Vendor.objects.get_or_create(
                name=name,
                defaults={
                    'rfc': rfc,
                    'contact_name': fake.name(),
                    'email': f'ventas@{name.lower().replace(" ", "").replace("-", "")[:15]}.com.mx',
                    'phone': fake.phone_number()[:15],
                    'address': fake.address(),
                    'payment_terms': terms,
                    'default_expense_account': expense_account,
                    'is_active': True,
                }
            )
            self.vendors[name] = vendor

            # Create inventory supplier if relevant
            if category in ['food', 'pharma', 'distributor', 'veterinary']:
                supplier, _ = Supplier.objects.get_or_create(
                    name=name,
                    defaults={
                        'code': rfc[:6],
                        'contact_name': vendor.contact_name,
                        'email': vendor.email,
                        'phone': vendor.phone,
                        'address': vendor.address,
                        'rfc': rfc,
                        'payment_terms': terms,
                        'lead_time_days': random.randint(2, 7),
                        'categories': [category],
                        'is_active': True,
                        'is_preferred': category in ['pharma', 'food'],
                    }
                )
                self.suppliers[name] = supplier

        self.stdout.write(f'    Created {len(self.vendors)} vendors, {len(self.suppliers)} inventory suppliers')

    def create_inventory_infrastructure(self):
        """Create inventory locations and initial stock."""
        self.stdout.write('  Creating inventory infrastructure...')

        from apps.inventory.models import StockLocation, StockLevel, StockBatch
        from apps.store.models import Product

        # Stock locations
        locations_data = [
            ('Piso de Tienda', 'store', 'Área de exhibición y venta'),
            ('Farmacia', 'pharmacy', 'Medicamentos y productos controlados'),
            ('Refrigerador', 'refrigerated', 'Vacunas y productos que requieren frío'),
            ('Almacén General', 'warehouse', 'Inventario de respaldo'),
            ('Controlados', 'controlled', 'Sustancias controladas - acceso restringido'),
        ]

        self.stock_locations = {}
        for name, loc_type, desc in locations_data:
            location, _ = StockLocation.objects.get_or_create(
                name=name,
                defaults={
                    'description': desc,
                    'location_type': loc_type,
                    'requires_temperature_control': loc_type == 'refrigerated',
                    'requires_restricted_access': loc_type in ['controlled', 'pharmacy'],
                    'is_active': True,
                }
            )
            self.stock_locations[name] = location

        # Create stock levels for products
        products = Product.objects.filter(is_active=True)
        stock_created = 0
        primary_location = self.stock_locations.get('Piso de Tienda')

        for product in products:
            if primary_location:
                StockLevel.objects.get_or_create(
                    product=product,
                    location=primary_location,
                    defaults={
                        'quantity': Decimal(str(random.randint(10, 50))),
                        'reserved_quantity': Decimal('0'),
                        'min_level': Decimal('5'),
                        'reorder_quantity': Decimal('20'),
                    }
                )
                stock_created += 1

        self.stdout.write(f'    Created {len(self.stock_locations)} locations, {stock_created} stock levels')

    def create_medications_catalog(self):
        """Create pharmacy medication database."""
        self.stdout.write('  Creating medications catalog...')

        from apps.pharmacy.models import Medication

        medications_data = [
            # (name, generic, class, schedule, controlled, species, forms, strengths)
            ('Rimadyl', 'Carprofen', 'AINE', '', False, ['dog'], ['tablet'], ['25mg', '75mg', '100mg']),
            ('Metacam', 'Meloxicam', 'AINE', '', False, ['dog', 'cat'], ['suspension', 'injection'], ['1.5mg/ml', '5mg/ml']),
            ('Cerenia', 'Maropitant', 'Antiemético', '', False, ['dog', 'cat'], ['tablet', 'injection'], ['16mg', '24mg', '60mg']),
            ('Clavamox', 'Amoxicilina/Clavulánico', 'Antibiótico', '', False, ['dog', 'cat'], ['tablet', 'suspension'], ['62.5mg', '125mg', '250mg', '375mg']),
            ('Apoquel', 'Oclacitinib', 'Inmunomodulador', '', False, ['dog'], ['tablet'], ['3.6mg', '5.4mg', '16mg']),
            ('Bravecto', 'Fluralaner', 'Antiparasitario', '', False, ['dog', 'cat'], ['tablet', 'topical'], ['112.5mg', '250mg', '500mg', '1000mg']),
            ('Nexgard', 'Afoxolaner', 'Antiparasitario', '', False, ['dog'], ['chewable'], ['11.3mg', '28.3mg', '68mg', '136mg']),
            ('Frontline Plus', 'Fipronil/S-Metopreno', 'Antiparasitario', '', False, ['dog', 'cat'], ['topical'], ['0.67ml', '1.34ml', '2.68ml', '4.02ml']),
            ('Prednisona', 'Prednisona', 'Corticosteroide', '', False, ['dog', 'cat'], ['tablet'], ['5mg', '10mg', '20mg', '50mg']),
            ('Tramadol', 'Tramadol', 'Analgésico Opioide', 'IV', True, ['dog', 'cat'], ['tablet', 'injection'], ['50mg', '100mg']),
            ('Gabapentina', 'Gabapentina', 'Anticonvulsivo/Analgésico', '', False, ['dog', 'cat'], ['capsule'], ['100mg', '300mg', '400mg']),
            ('Metronidazol', 'Metronidazol', 'Antibiótico/Antiparasitario', '', False, ['dog', 'cat'], ['tablet', 'suspension'], ['250mg', '500mg']),
            ('Omeprazol', 'Omeprazol', 'Inhibidor de Bomba de Protones', '', False, ['dog', 'cat'], ['capsule'], ['10mg', '20mg']),
            ('Insulina Lantus', 'Insulina Glargina', 'Hormona', '', False, ['dog', 'cat'], ['injection'], ['100 UI/ml']),
            ('Ketamina', 'Ketamina', 'Anestésico Disociativo', 'III', True, ['dog', 'cat'], ['injection'], ['100mg/ml']),
            ('Xilazina', 'Xilazina', 'Sedante/Analgésico', 'III', True, ['dog', 'cat', 'horse'], ['injection'], ['20mg/ml', '100mg/ml']),
            ('Propofol', 'Propofol', 'Anestésico General', '', False, ['dog', 'cat'], ['injection'], ['10mg/ml']),
        ]

        self.medications = {}
        for name, generic, drug_class, schedule, controlled, species, forms, strengths in medications_data:
            medication, _ = Medication.objects.get_or_create(
                name=name,
                defaults={
                    'name_es': name,
                    'generic_name': generic,
                    'drug_class': drug_class,
                    'schedule': schedule,
                    'is_controlled': controlled,
                    'requires_prescription': True,
                    'species': species,
                    'dosage_forms': forms,
                    'strengths': strengths,
                    'is_active': True,
                }
            )
            self.medications[name] = medication

        self.stdout.write(f'    Created {len(medications_data)} medications in pharmacy catalog')

    # =========================================================================
    # HISTORICAL SIMULATION MODE
    # =========================================================================

    def simulate_clinic_history(self, months=6, customers_per_day=2):
        """Simulate clinic operations over a period of months."""
        self.stdout.write(self.style.NOTICE(f'\n📅 HISTORICAL SIMULATION: {months} months, ~{customers_per_day} customers/day'))

        from apps.pets.models import Pet, MedicalCondition, Vaccination, Visit, Medication, ClinicalNote, WeightRecord
        from apps.crm.models import OwnerProfile, CustomerTag, Interaction
        from apps.appointments.models import Appointment, ServiceType
        from apps.store.models import Order, OrderItem, Product

        # Create customer tags
        tags_data = ['VIP', 'Nuevo Cliente', 'Frecuente', 'Referido', 'Moroso', 'Rescate']
        self.tags = []
        for tag_name in tags_data:
            tag, _ = CustomerTag.objects.get_or_create(
                name=tag_name,
                defaults={'color': fake.hex_color()}
            )
            self.tags.append(tag)

        # Calculate simulation period
        end_date = date.today()
        start_date = end_date - timedelta(days=months * 30)
        total_days = (end_date - start_date).days

        self.stdout.write(f'  Simulating from {start_date} to {end_date} ({total_days} days)')

        # Track all customers and pets for follow-up visits
        self.all_customers = []
        self.all_pets = []
        self.customer_counter = 0
        self.invoice_counter = 0
        self.bill_counter = 0

        # Statistics
        stats = {
            'customers': 0,
            'pets': 0,
            'appointments_scheduled': 0,
            'appointments_completed': 0,
            'visits': 0,
            'vaccinations': 0,
            'orders': 0,
            'clinical_notes': 0,
            # Financial stats
            'invoices': 0,
            'payments': 0,
            'vendor_bills': 0,
            'total_revenue': Decimal('0'),
            'total_expenses': Decimal('0'),
            'prescriptions': 0,
        }

        # Simulate day by day
        current_date = start_date
        day_num = 0

        while current_date <= end_date:
            day_num += 1

            # Skip Sundays (clinic closed)
            if current_date.weekday() == 6:
                current_date += timedelta(days=1)
                continue

            # Progress indicator every 30 days
            if day_num % 30 == 0:
                self.stdout.write(f'  📆 Day {day_num}/{total_days}: {current_date} - {stats["customers"]} customers, {stats["visits"]} visits')

            # === NEW CUSTOMERS FOR THE DAY ===
            # Vary the number (0-4 new customers, averaging customers_per_day)
            new_customers_today = random.choices(
                [0, 1, 2, 3, 4],
                weights=[10, 25, 35, 20, 10],  # Distribution centered on 2
                k=1
            )[0]

            for _ in range(new_customers_today):
                customer_data = self._create_historical_customer(current_date)
                if customer_data:
                    self.all_customers.append(customer_data)
                    self.all_pets.extend(customer_data['pets'])
                    stats['customers'] += 1
                    stats['pets'] += len(customer_data['pets'])

            # === DAILY APPOINTMENTS (from existing customers) ===
            # Simulate 8-15 appointments per day
            appointments_today = random.randint(8, 15)

            for _ in range(appointments_today):
                if not self.all_pets:
                    continue

                # Pick a random pet from existing customers
                pet = random.choice(self.all_pets)

                # Create and complete an appointment
                appt_result = self._simulate_appointment(pet, current_date)
                if appt_result:
                    stats['appointments_scheduled'] += 1
                    if appt_result.get('completed'):
                        stats['appointments_completed'] += 1
                        stats['visits'] += 1
                        stats['clinical_notes'] += appt_result.get('notes_count', 0)
                        # Financial tracking
                        if appt_result.get('invoice_created'):
                            stats['invoices'] += 1
                            stats['payments'] += 1
                            stats['total_revenue'] += appt_result.get('invoice_total', Decimal('0'))
                        if appt_result.get('prescription'):
                            stats['prescriptions'] += 1
                    if appt_result.get('vaccination'):
                        stats['vaccinations'] += 1

            # === RANDOM ORDERS (some days) ===
            if random.random() < 0.4:  # 40% of days have orders
                orders_today = random.randint(1, 5)
                for _ in range(orders_today):
                    if self.all_customers:
                        customer = random.choice(self.all_customers)
                        order_result = self._create_historical_order(customer['user'], current_date)
                        if order_result:
                            stats['orders'] += 1
                            stats['invoices'] += 1
                            stats['payments'] += 1
                            stats['total_revenue'] += order_result.get('total', Decimal('0'))

            # === VENDOR BILLS (weekly inventory replenishment) ===
            if current_date.weekday() == 1:  # Tuesdays - receive inventory
                bill_result = self._create_vendor_bill(current_date)
                if bill_result:
                    stats['vendor_bills'] += 1
                    stats['total_expenses'] += bill_result.get('total', Decimal('0'))

            current_date += timedelta(days=1)

        # Create some future appointments
        self._create_future_appointments()

        self.stdout.write(self.style.SUCCESS(f'\n  ✅ Historical simulation complete!'))
        self.stdout.write(f'  📊 Generated: {stats["customers"]} customers, {stats["pets"]} pets')
        self.stdout.write(f'  📅 Appointments: {stats["appointments_scheduled"]} scheduled, {stats["appointments_completed"]} completed')
        self.stdout.write(f'  🏥 Visits: {stats["visits"]}, Clinical Notes: {stats["clinical_notes"]}')
        self.stdout.write(f'  💉 Vaccinations: {stats["vaccinations"]}, Prescriptions: {stats["prescriptions"]}')
        self.stdout.write(f'  🛒 Orders: {stats["orders"]}')
        self.stdout.write(self.style.SUCCESS(f'\n  💰 FINANCIAL SUMMARY:'))
        self.stdout.write(f'  📄 Invoices: {stats["invoices"]}, Payments: {stats["payments"]}')
        self.stdout.write(f'  📋 Vendor Bills: {stats["vendor_bills"]}')
        self.stdout.write(f'  💵 Total Revenue: ${stats["total_revenue"]:,.2f} MXN')
        self.stdout.write(f'  💸 Total Expenses: ${stats["total_expenses"]:,.2f} MXN')
        net_income = stats["total_revenue"] - stats["total_expenses"]
        self.stdout.write(f'  📈 Net Income: ${net_income:,.2f} MXN')

    def _create_historical_customer(self, registration_date):
        """Create a customer who registered on a specific date."""
        from apps.pets.models import Pet, Vaccination
        from apps.crm.models import OwnerProfile

        self.customer_counter += 1
        username = f'customer_{self.customer_counter}'

        user = User.objects.create(
            username=username,
            email=f'{username}@test.petfriendlyvet.com',
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            phone_number=fake.phone_number()[:15],
            role='owner',
        )
        user.set_password('customer123')
        user.save()

        # Owner profile
        profile = OwnerProfile.objects.create(
            user=user,
            preferred_contact_method=random.choice(['phone', 'whatsapp', 'email']),
            referral_source=random.choice(['Google', 'Instagram', 'Referido', 'Facebook', 'Paso por aquí']),
            total_visits=0,
            total_spent=Decimal('0'),
        )
        profile.tags.add(self.tags[1])  # Nuevo Cliente

        # Create 1-3 pets
        num_pets = random.choices([1, 2, 3], weights=[60, 30, 10], k=1)[0]
        pets = []

        for _ in range(num_pets):
            pet = self._create_pet_for_customer(user, registration_date)
            pets.append(pet)

        return {
            'user': user,
            'profile': profile,
            'pets': pets,
            'registration_date': registration_date,
        }

    def _create_pet_for_customer(self, owner, registration_date):
        """Create a pet with appropriate age for registration date."""
        from apps.pets.models import Pet

        species = random.choices(
            ['dog', 'cat', 'rabbit', 'bird'],
            weights=[60, 30, 7, 3],
            k=1
        )[0]

        if species == 'dog':
            names = ['Max', 'Luna', 'Rocky', 'Bella', 'Charlie', 'Coco', 'Bruno', 'Lola', 'Thor', 'Nina']
            breeds = ['Labrador', 'Golden Retriever', 'Bulldog Francés', 'Chihuahua', 'Mestizo', 'Poodle', 'Schnauzer']
            weight_range = (3, 40)
        elif species == 'cat':
            names = ['Michi', 'Whiskers', 'Gatito', 'Felix', 'Luna', 'Simba', 'Nala', 'Cleo']
            breeds = ['Siamés', 'Persa', 'Mestizo', 'Maine Coon', 'Angora']
            weight_range = (2, 8)
        elif species == 'rabbit':
            names = ['Bunny', 'Copito', 'Pelusa', 'Tambor', 'Nieve']
            breeds = ['Holland Lop', 'Mini Rex', 'Angora', 'Mestizo']
            weight_range = (1, 4)
        else:  # bird
            names = ['Piolín', 'Tweety', 'Kiwi', 'Coco', 'Loro']
            breeds = ['Periquito', 'Canario', 'Cotorro', 'Loro']
            weight_range = (0.02, 0.5)

        # Age: mostly young to middle-aged pets
        age_days = random.choices(
            [random.randint(60, 365), random.randint(365, 1825), random.randint(1825, 4380)],
            weights=[30, 50, 20],
            k=1
        )[0]

        pet = Pet.objects.create(
            owner=owner,
            name=random.choice(names),
            species=species,
            breed=random.choice(breeds),
            gender=random.choice(['male', 'female']),
            date_of_birth=registration_date - timedelta(days=age_days),
            weight_kg=Decimal(str(round(random.uniform(*weight_range), 1))),
            is_neutered=random.random() < 0.6,
            microchip_id=fake.numerify('###############') if random.random() < 0.4 else '',
        )

        return pet

    def _simulate_appointment(self, pet, appt_date):
        """Simulate an appointment being scheduled and completed with full financial tracking."""
        from apps.pets.models import Visit, Vaccination, ClinicalNote, WeightRecord, Medication
        from apps.appointments.models import Appointment, ServiceType
        from apps.crm.models import OwnerProfile
        from apps.billing.models import Invoice, InvoiceLineItem, Payment
        from apps.services.models import Service
        from apps.pharmacy.models import Prescription, Medication as PharmaMedication

        # Get a random service type
        services = list(ServiceType.objects.filter(is_active=True))
        if not services:
            return None

        service = random.choice(services)
        vet = random.choice(self.vets)

        # Appointment time
        hour = random.choice([9, 10, 11, 12, 14, 15, 16, 17])
        appt_datetime = timezone.make_aware(
            datetime.combine(appt_date, time(hour, random.choice([0, 30])))
        )

        # Create appointment
        appointment = Appointment.objects.create(
            owner=pet.owner,
            pet=pet,
            veterinarian=vet,
            service=service,
            scheduled_start=appt_datetime,
            scheduled_end=appt_datetime + timedelta(minutes=service.duration_minutes),
            status='completed',  # Past appointments are completed
            confirmed_at=appt_datetime - timedelta(days=1),
            completed_at=appt_datetime + timedelta(minutes=service.duration_minutes),
            notes=f"Cita para {service.name}",
        )

        result = {
            'completed': True,
            'notes_count': 0,
            'vaccination': False,
            'invoice_created': False,
            'invoice_total': Decimal('0'),
            'prescription': False,
        }

        # Create the associated visit record
        visit = Visit.objects.create(
            pet=pet,
            date=appt_datetime,
            reason=service.name,
            diagnosis=random.choice(VISIT_DIAGNOSES),
            treatment=random.choice(VISIT_TREATMENTS),
            veterinarian=vet,
            weight_kg=pet.weight_kg + Decimal(str(round(random.uniform(-0.5, 0.5), 1))),
            follow_up_date=appt_date + timedelta(days=random.choice([7, 14, 30])) if random.random() < 0.3 else None,
        )

        # Add clinical notes
        note_type = 'consultation'
        if 'Vacun' in service.name:
            note_type = 'vaccination'
        elif 'Seguimiento' in service.name:
            note_type = 'followup'
        elif 'Dental' in service.name:
            note_type = 'dental'
        elif 'Cirugía' in service.name or 'Esteril' in service.name:
            note_type = 'surgery'

        # 1-3 clinical notes per visit
        num_notes = random.randint(1, 3)
        for _ in range(num_notes):
            note_template = random.choice(CLINICAL_NOTES.get(note_type, CLINICAL_NOTES['consultation']))
            # Replace placeholders if present
            if '{}' in note_template:
                note_template = note_template.format(random.randint(1, 5))

            ClinicalNote.objects.create(
                pet=pet,
                author=vet,
                visit=visit,
                note=note_template,
                note_type=random.choice(['observation', 'treatment', 'followup']),
            )
            result['notes_count'] += 1

        # Record weight
        WeightRecord.objects.create(
            pet=pet,
            weight_kg=visit.weight_kg,
            recorded_by=vet,
        )

        # Vaccination if it's a vaccination appointment
        if 'Vacun' in service.name:
            vaccine_names = ['Rabia', 'Múltiple Canina', 'Bordetella', 'Leptospirosis'] if pet.species == 'dog' else ['Rabia', 'Triple Felina']
            Vaccination.objects.create(
                pet=pet,
                vaccine_name=random.choice(vaccine_names),
                date_administered=appt_date,
                next_due_date=appt_date + timedelta(days=365),
                administered_by=vet,
                batch_number=fake.bothify('VAC-#####'),
            )
            result['vaccination'] = True

        # === CREATE INVOICE (FACTURA) ===
        # Get corresponding billing service
        billing_service = Service.objects.filter(
            name__icontains=service.name.split()[0]
        ).first() or Service.objects.first()

        service_price = billing_service.base_price if billing_service else Decimal(str(service.price))

        subtotal = service_price
        tax_amount = subtotal * Decimal('0.16')  # 16% IVA
        total = subtotal + tax_amount

        self.invoice_counter += 1
        invoice = Invoice.objects.create(
            invoice_number=f'INV-{appt_date.year}-{self.invoice_counter:05d}',
            owner=pet.owner,
            pet=pet,
            appointment=appointment,
            subtotal=subtotal,
            discount_amount=Decimal('0'),
            tax_amount=tax_amount,
            total=total,
            amount_paid=total,
            status='paid',
            due_date=appt_date,
            paid_at=appt_datetime + timedelta(minutes=service.duration_minutes + 10),
        )

        # Invoice line item
        InvoiceLineItem.objects.create(
            invoice=invoice,
            description=service.name,
            quantity=Decimal('1'),
            unit_price=service_price,
            discount_percent=Decimal('0'),
            line_total=service_price,
            service=billing_service,
            clave_producto_sat='85121800',  # Veterinary services
            clave_unidad_sat='E48',  # Service unit
        )

        # Payment record
        Payment.objects.create(
            invoice=invoice,
            amount=total,
            payment_method=random.choice(['cash', 'manual_card', 'bank_transfer']),
            recorded_by=random.choice(self.staff) if hasattr(self, 'staff') and self.staff else vet,
        )

        result['invoice_created'] = True
        result['invoice_total'] = total

        # === CREATE PRESCRIPTION (for some visits) ===
        if random.random() < 0.3:  # 30% of visits get prescriptions
            medications = list(PharmaMedication.objects.filter(is_controlled=False)[:10])
            if medications:
                med = random.choice(medications)
                strengths = med.strengths if isinstance(med.strengths, list) and med.strengths else ['10mg']
                forms = med.dosage_forms if isinstance(med.dosage_forms, list) and med.dosage_forms else ['tablet']

                try:
                    from apps.practice.models import StaffProfile
                    prescribing_vet = StaffProfile.objects.filter(user=vet).first()
                except:
                    prescribing_vet = None

                Prescription.objects.create(
                    pet=pet,
                    owner=pet.owner,
                    prescribing_vet=prescribing_vet,
                    visit=appointment,
                    medication=med,
                    strength=random.choice(strengths),
                    dosage_form=random.choice(forms),
                    quantity=random.randint(10, 30),
                    dosage='1 tableta',
                    frequency='cada 12 horas',
                    duration='7 días',
                    instructions='Administrar con alimento',
                    refills_authorized=random.randint(0, 2),
                    refills_remaining=random.randint(0, 2),
                    prescribed_date=appt_date,
                    expiration_date=appt_date + timedelta(days=180),
                    status='active',
                )
                result['prescription'] = True

                # Also create a Medication record in pets app for tracking
                Medication.objects.create(
                    pet=pet,
                    name=med.name,
                    dosage=random.choice(strengths),
                    frequency='cada 12 horas',
                    start_date=appt_date,
                    end_date=appt_date + timedelta(days=7),
                    prescribing_vet=vet,
                    notes='Prescrito durante consulta',
                )

        # Update owner profile stats
        try:
            profile = pet.owner.owner_profile
            profile.total_visits += 1
            profile.total_spent += service.price
            profile.save()

            # Upgrade to 'Frecuente' if enough visits
            if profile.total_visits >= 5:
                profile.tags.add(self.tags[2])  # Frecuente
                profile.tags.remove(self.tags[1])  # Remove Nuevo Cliente
        except OwnerProfile.DoesNotExist:
            pass

        return result

    def _create_historical_order(self, user, order_date):
        """Create an order placed on a specific date with invoice and payment."""
        from apps.store.models import Order, OrderItem, Product
        from apps.billing.models import Invoice, InvoiceLineItem, Payment

        products = list(Product.objects.filter(is_active=True)[:20])
        if not products:
            return None

        # Pick 1-4 products
        order_products = random.sample(products, min(random.randint(1, 4), len(products)))
        quantities = {p.id: random.randint(1, 3) for p in order_products}

        subtotal = sum(p.price * quantities[p.id] for p in order_products)
        fulfillment = random.choice(['pickup', 'delivery'])
        shipping_cost = Decimal('50.00') if fulfillment == 'delivery' else Decimal('0')
        tax = subtotal * Decimal('0.16')
        total = subtotal + shipping_cost + tax

        # Past orders are mostly delivered
        status = random.choices(
            ['delivered', 'cancelled'],
            weights=[90, 10],
            k=1
        )[0]

        order = Order.objects.create(
            user=user,
            order_number=Order.generate_order_number(),
            status=status,
            fulfillment_method=fulfillment,
            payment_method=random.choice(['cash', 'card']),
            shipping_address=fake.address() if fulfillment == 'delivery' else '',
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            tax=tax,
            total=total,
        )
        # Backdate the order
        order_datetime = timezone.make_aware(datetime.combine(order_date, time(random.randint(9, 18), 0)))
        Order.objects.filter(pk=order.pk).update(created_at=order_datetime)

        for product in order_products:
            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                product_sku=product.sku,
                price=product.price,
                quantity=quantities[product.id],
            )

        # === CREATE INVOICE FOR ORDER ===
        if status != 'cancelled':
            self.invoice_counter += 1
            invoice = Invoice.objects.create(
                invoice_number=f'INV-{order_date.year}-{self.invoice_counter:05d}',
                owner=user,
                order=order,
                subtotal=subtotal,
                discount_amount=Decimal('0'),
                tax_amount=tax,
                total=total,
                amount_paid=total,
                status='paid',
                due_date=order_date,
                paid_at=order_datetime + timedelta(minutes=15),
            )

            # Invoice line items for each product
            for product in order_products:
                InvoiceLineItem.objects.create(
                    invoice=invoice,
                    description=product.name,
                    quantity=Decimal(str(quantities[product.id])),
                    unit_price=product.price,
                    discount_percent=Decimal('0'),
                    line_total=product.price * quantities[product.id],
                    product=product,
                    clave_producto_sat='50000000',  # General products
                    clave_unidad_sat='H87',  # Piece
                )

            # Payment
            Payment.objects.create(
                invoice=invoice,
                amount=total,
                payment_method='manual_card' if order.payment_method == 'card' else 'cash',
                recorded_by=random.choice(self.staff) if hasattr(self, 'staff') and self.staff else None,
            )

        return {'total': total, 'order': order}

    def _create_vendor_bill(self, bill_date):
        """Create a vendor bill for inventory replenishment."""
        from apps.accounting.models import Vendor, Bill, BillLine, BillPayment
        from apps.store.models import Product
        from apps.inventory.models import StockMovement, StockLevel

        if not hasattr(self, 'vendors') or not self.vendors:
            return None

        # Pick a random vendor
        vendor_name = random.choice(list(self.vendors.keys()))
        vendor = self.vendors[vendor_name]

        # Pick 3-8 products to order
        products = list(Product.objects.filter(is_active=True)[:30])
        if not products:
            return None

        order_products = random.sample(products, min(random.randint(3, 8), len(products)))

        # Calculate bill amounts (cost is ~50-70% of retail price)
        lines = []
        subtotal = Decimal('0')
        for product in order_products:
            quantity = random.randint(10, 50)
            unit_cost = product.price * Decimal(str(random.uniform(0.5, 0.7)))
            amount = quantity * unit_cost
            subtotal += amount
            lines.append({
                'product': product,
                'description': product.name,
                'quantity': quantity,
                'unit_cost': unit_cost,
                'amount': amount,
            })

        tax = subtotal * Decimal('0.16')
        total = subtotal + tax

        # Terms-based due date
        if vendor.payment_terms == 'net30':
            due_date = bill_date + timedelta(days=30)
        elif vendor.payment_terms == 'net15':
            due_date = bill_date + timedelta(days=15)
        elif vendor.payment_terms == 'net60':
            due_date = bill_date + timedelta(days=60)
        else:
            due_date = bill_date

        self.bill_counter += 1
        bill = Bill.objects.create(
            vendor=vendor,
            bill_number=f'FAC-{vendor_name[:3].upper()}-{bill_date.year}-{self.bill_counter:04d}',
            bill_date=bill_date,
            due_date=due_date,
            subtotal=subtotal,
            tax=tax,
            total=total,
            amount_paid=Decimal('0'),
            status='pending',
        )

        # Create bill lines
        expense_account = self.accounts.get('5101') if hasattr(self, 'accounts') else None
        for line in lines:
            BillLine.objects.create(
                bill=bill,
                description=line['description'],
                quantity=line['quantity'],
                unit_price=line['unit_cost'],
                amount=line['amount'],
                expense_account=expense_account,
            )

            # Update stock levels
            if hasattr(self, 'stock_locations'):
                primary_location = self.stock_locations.get('Piso de Tienda')
                if primary_location:
                    stock_level, _ = StockLevel.objects.get_or_create(
                        product=line['product'],
                        location=primary_location,
                        defaults={'quantity': Decimal('0')}
                    )
                    stock_level.quantity += line['quantity']
                    stock_level.last_movement = timezone.make_aware(datetime.combine(bill_date, time(10, 0)))
                    stock_level.save()

                    # Create stock movement record
                    StockMovement.objects.create(
                        product=line['product'],
                        movement_type='receive',
                        to_location=primary_location,
                        quantity=line['quantity'],
                        unit_cost=line['unit_cost'],
                        reference_type='bill',
                        reference_id=bill.id,
                        reason=f'Recepción de pedido de {vendor_name}',
                    )

        # Pay old bills (simulate paying bills that are due)
        if random.random() < 0.7:  # 70% chance to pay this bill eventually
            # Most bills get paid within terms
            payment_date = bill_date + timedelta(days=random.randint(1, 25))
            if payment_date <= date.today():
                bank_account = self.accounts.get('1111') if hasattr(self, 'accounts') else None
                BillPayment.objects.create(
                    bill=bill,
                    date=payment_date,
                    amount=total,
                    payment_method=random.choice(['transfer', 'check']),
                    reference=fake.bothify('REF-####-????'),
                    bank_account=bank_account,
                )
                bill.amount_paid = total
                bill.status = 'paid'
                bill.save()

        return {'total': total, 'bill': bill}

    def _create_future_appointments(self):
        """Create upcoming appointments for the next 2 weeks."""
        from apps.appointments.models import Appointment, ServiceType

        self.stdout.write('  Creating future appointments...')

        if not self.all_pets:
            return

        services = list(ServiceType.objects.filter(is_active=True))
        if not services:
            return

        today = date.today()
        appointments_created = 0

        # Create 5-10 appointments per day for the next 14 days
        for day_offset in range(1, 15):
            appt_date = today + timedelta(days=day_offset)

            # Skip Sunday
            if appt_date.weekday() == 6:
                continue

            num_appointments = random.randint(5, 10)

            for _ in range(num_appointments):
                pet = random.choice(self.all_pets)
                service = random.choice(services)
                vet = random.choice(self.vets)

                hour = random.choice([9, 10, 11, 12, 14, 15, 16, 17])
                appt_datetime = timezone.make_aware(
                    datetime.combine(appt_date, time(hour, random.choice([0, 30])))
                )

                status = random.choices(
                    ['scheduled', 'confirmed'],
                    weights=[30, 70],
                    k=1
                )[0]

                Appointment.objects.create(
                    owner=pet.owner,
                    pet=pet,
                    veterinarian=vet,
                    service=service,
                    scheduled_start=appt_datetime,
                    scheduled_end=appt_datetime + timedelta(minutes=service.duration_minutes),
                    status=status,
                    confirmed_at=appt_datetime - timedelta(days=1) if status == 'confirmed' else None,
                    notes=f"Cita programada para {service.name}",
                )
                appointments_created += 1

        self.stdout.write(f'    Created {appointments_created} future appointments')

    # =========================================================================
    # ORIGINAL SCENARIO MODE
    # =========================================================================

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

        # Financial summary
        try:
            from apps.billing.models import Invoice, Payment
            from apps.accounting.models import Vendor, Bill, Account
            from apps.services.models import Service
            from apps.pharmacy.models import Medication, Prescription
            from apps.inventory.models import StockLocation, StockLevel, Supplier

            self.stdout.write('\n💰 Financial Summary:')
            self.stdout.write(f'  📄 Invoices: {Invoice.objects.count()}')
            self.stdout.write(f'  💳 Payments: {Payment.objects.count()}')
            self.stdout.write(f'  📋 Vendor Bills: {Bill.objects.count()}')

            total_revenue = Invoice.objects.filter(status='paid').aggregate(
                total=models.Sum('total')
            )['total'] or Decimal('0')
            total_ar = Invoice.objects.exclude(status='paid').aggregate(
                total=models.Sum('total')
            )['total'] or Decimal('0')
            total_expenses = Bill.objects.filter(status='paid').aggregate(
                total=models.Sum('total')
            )['total'] or Decimal('0')
            total_ap = Bill.objects.exclude(status='paid').aggregate(
                total=models.Sum('total')
            )['total'] or Decimal('0')

            self.stdout.write(f'  💵 Total Revenue (paid): ${total_revenue:,.2f} MXN')
            self.stdout.write(f'  📥 Accounts Receivable: ${total_ar:,.2f} MXN')
            self.stdout.write(f'  💸 Total Expenses (paid): ${total_expenses:,.2f} MXN')
            self.stdout.write(f'  📤 Accounts Payable: ${total_ap:,.2f} MXN')

            self.stdout.write('\n📦 Inventory & Pharmacy:')
            self.stdout.write(f'  🏪 Suppliers: {Supplier.objects.count()}')
            self.stdout.write(f'  📍 Stock Locations: {StockLocation.objects.count()}')
            self.stdout.write(f'  📊 Stock Levels: {StockLevel.objects.count()}')
            self.stdout.write(f'  💊 Medications: {Medication.objects.count()}')
            self.stdout.write(f'  📝 Prescriptions: {Prescription.objects.count()}')

            self.stdout.write('\n📚 Configuration:')
            self.stdout.write(f'  📊 Chart of Accounts: {Account.objects.count()} accounts')
            self.stdout.write(f'  🏢 Vendors: {Vendor.objects.count()}')
            self.stdout.write(f'  🩺 Services: {Service.objects.count()}')

        except Exception as e:
            self.stdout.write(f'  (Financial data not available: {e})')

        self.stdout.write('\n🔑 Test Credentials:')
        self.stdout.write('  Vets: dr_rodriguez/vet123, dra_martinez/vet123')
        self.stdout.write('  Staff: recepcion1/staff123')
        self.stdout.write('  Drivers: driver_carlos/driver123')
        self.stdout.write('  Customers: puppy_owner_1/customer123, etc.')
