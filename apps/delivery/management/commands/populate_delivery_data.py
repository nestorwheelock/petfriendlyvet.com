"""Management command to populate sample delivery data for testing."""
from datetime import date, time, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.delivery.models import DeliveryZone, DeliverySlot, DeliveryDriver

User = get_user_model()


class Command(BaseCommand):
    """Populate database with sample delivery data."""

    help = 'Populate database with sample delivery zones, slots, and drivers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before populating',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            DeliveryDriver.objects.all().delete()
            DeliverySlot.objects.all().delete()
            DeliveryZone.objects.all().delete()

        self.create_zones()
        self.create_slots()
        self.create_drivers()

        self.stdout.write(self.style.SUCCESS('Sample delivery data created successfully!'))

    def create_zones(self):
        """Create delivery zones for CDMX."""
        zones = [
            {
                'code': 'CDMX-CENTRO',
                'name': 'Centro Historico',
                'description': 'Centro de la Ciudad de Mexico - Zocalo, Bellas Artes, Alameda',
                'delivery_fee': Decimal('50.00'),
                'estimated_minutes': 30,
            },
            {
                'code': 'CDMX-ROMA',
                'name': 'Roma / Condesa',
                'description': 'Colonias Roma Norte, Roma Sur, Condesa, Hipodromo',
                'delivery_fee': Decimal('45.00'),
                'estimated_minutes': 25,
            },
            {
                'code': 'CDMX-POLANCO',
                'name': 'Polanco',
                'description': 'Polanco I-V Seccion, Chapultepec',
                'delivery_fee': Decimal('55.00'),
                'estimated_minutes': 35,
            },
            {
                'code': 'CDMX-COYOACAN',
                'name': 'Coyoacan',
                'description': 'Centro de Coyoacan, Viveros, Ciudad Universitaria',
                'delivery_fee': Decimal('60.00'),
                'estimated_minutes': 40,
            },
            {
                'code': 'CDMX-SANTAFE',
                'name': 'Santa Fe',
                'description': 'Zona de Santa Fe, Interlomas',
                'delivery_fee': Decimal('75.00'),
                'estimated_minutes': 50,
            },
            {
                'code': 'CDMX-NARVARTE',
                'name': 'Narvarte / Del Valle',
                'description': 'Narvarte Oriente y Poniente, Del Valle',
                'delivery_fee': Decimal('50.00'),
                'estimated_minutes': 30,
            },
        ]

        for zone_data in zones:
            zone, created = DeliveryZone.objects.get_or_create(
                code=zone_data['code'],
                defaults=zone_data
            )
            status = 'Created' if created else 'Already exists'
            self.stdout.write(f'  Zone {zone.code}: {status}')

    def create_slots(self):
        """Create delivery slots for the next 7 days."""
        slot_times = [
            (time(9, 0), time(12, 0)),   # Morning
            (time(12, 0), time(15, 0)),  # Afternoon
            (time(15, 0), time(18, 0)),  # Late afternoon
        ]

        today = date.today()
        created_count = 0

        for day_offset in range(7):
            slot_date = today + timedelta(days=day_offset)

            for start_time, end_time in slot_times:
                slot, created = DeliverySlot.objects.get_or_create(
                    date=slot_date,
                    start_time=start_time,
                    end_time=end_time,
                    defaults={
                        'max_deliveries': 10,
                        'current_deliveries': 0,
                        'is_active': True,
                    }
                )
                if created:
                    created_count += 1

        self.stdout.write(f'  Created {created_count} delivery slots')

    def create_drivers(self):
        """Create sample delivery drivers."""
        drivers_data = [
            {
                'username': 'driver_carlos',
                'first_name': 'Carlos',
                'last_name': 'Rodriguez',
                'email': 'carlos@example.com',
                'driver_type': 'employee',
                'vehicle_type': 'motorcycle',
                'vehicle_plate': 'ABC-123',
                'phone': '555-0101',
                'max_deliveries_per_day': 15,
            },
            {
                'username': 'driver_maria',
                'first_name': 'Maria',
                'last_name': 'Lopez',
                'email': 'maria@example.com',
                'driver_type': 'employee',
                'vehicle_type': 'car',
                'vehicle_plate': 'XYZ-789',
                'phone': '555-0102',
                'max_deliveries_per_day': 12,
            },
            {
                'username': 'driver_contractor1',
                'first_name': 'Juan',
                'last_name': 'Hernandez',
                'email': 'juan@example.com',
                'driver_type': 'contractor',
                'vehicle_type': 'motorcycle',
                'vehicle_plate': 'MOT-456',
                'phone': '555-0103',
                'max_deliveries_per_day': 20,
                'rfc': 'HEJM850101AAA',
                'curp': 'HEJM850101HDFRNN01',
                'rate_per_delivery': Decimal('35.00'),
                'rate_per_km': Decimal('5.00'),
                'onboarding_status': 'approved',
            },
            {
                'username': 'driver_contractor2',
                'first_name': 'Ana',
                'last_name': 'Martinez',
                'email': 'ana@example.com',
                'driver_type': 'contractor',
                'vehicle_type': 'bicycle',
                'vehicle_plate': '',
                'phone': '555-0104',
                'max_deliveries_per_day': 8,
                'rfc': 'MAMA900515BBB',
                'curp': 'MAMA900515MDFRRN02',
                'rate_per_delivery': Decimal('25.00'),
                'rate_per_km': Decimal('3.00'),
                'onboarding_status': 'approved',
            },
        ]

        zones = list(DeliveryZone.objects.all()[:3])

        for driver_data in drivers_data:
            username = driver_data.pop('username')
            first_name = driver_data.pop('first_name')
            last_name = driver_data.pop('last_name')
            email = driver_data.pop('email')

            user, user_created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                }
            )
            if user_created:
                user.set_password('driver123')
                user.save()

            driver, driver_created = DeliveryDriver.objects.get_or_create(
                user=user,
                defaults=driver_data
            )

            if driver_created and zones:
                driver.zones.set(zones)

            status = 'Created' if driver_created else 'Already exists'
            self.stdout.write(f'  Driver {user.get_full_name()}: {status}')
