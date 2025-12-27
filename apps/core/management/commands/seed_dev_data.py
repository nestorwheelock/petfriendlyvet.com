"""Seed development data for testing EMR workflow.

Run: python manage.py seed_dev_data
Clear and reseed: python manage.py seed_dev_data --clear

Creates:
- 1 Organization
- 1 Location
- 3 Staff users (vet, tech, receptionist)
- 1 Customer + 3 Pets + PatientRecords
- 3 Appointments today (2 scheduled, 1 cancelled)
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import User
from apps.appointments.models import Appointment, ServiceType
from apps.locations.models import Location
from apps.parties.models import Organization
from apps.pets.models import Pet
from apps.practice.models import PatientRecord


class Command(BaseCommand):
    help = 'Seed development data: org, location, staff, patients, appointments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing seed data before creating new',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing seed data...')
            Appointment.objects.filter(notes__startswith='[SEED]').delete()
            Pet.objects.filter(name__startswith='[SEED]').delete()
            User.objects.filter(username__startswith='seed_').delete()
            ServiceType.objects.filter(name__startswith='[SEED]').delete()
            Location.objects.filter(name__startswith='[SEED]').delete()
            Organization.objects.filter(name__startswith='[SEED]').delete()

        self.stdout.write('Creating seed data...')

        # 1. Organization
        org, created = Organization.objects.get_or_create(
            name='[SEED] Pet Friendly Vet Clinic',
            defaults={'org_type': 'clinic'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'  Created organization: {org.name}'))
        else:
            self.stdout.write(f'  Organization exists: {org.name}')

        # 2. Location
        location, created = Location.objects.get_or_create(
            name='[SEED] Main Clinic',
            defaults={
                'organization': org,
                'address_line1': '123 Vet Street',
                'city': 'Pet City',
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'  Created location: {location.name}'))
        else:
            self.stdout.write(f'  Location exists: {location.name}')

        # 3. Staff users
        staff_data = [
            {'username': 'seed_vet', 'first_name': 'Dr. Sarah', 'last_name': 'Veterinarian', 'is_staff': True},
            {'username': 'seed_tech', 'first_name': 'Mike', 'last_name': 'Tech', 'is_staff': True},
            {'username': 'seed_reception', 'first_name': 'Jane', 'last_name': 'Reception', 'is_staff': True},
        ]
        staff_users = {}
        for data in staff_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': f"{data['username']}@example.com",
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'is_staff': data['is_staff'],
                }
            )
            if created:
                user.set_password('devpass123')
                user.save()
                self.stdout.write(self.style.SUCCESS(f'  Created staff: {user.get_full_name()}'))
            else:
                self.stdout.write(f'  Staff exists: {user.get_full_name()}')
            staff_users[data['username']] = user

        # 4. Customer with pets
        customer, created = User.objects.get_or_create(
            username='seed_customer',
            defaults={
                'email': 'customer@example.com',
                'first_name': 'John',
                'last_name': 'PetOwner',
            }
        )
        if created:
            customer.set_password('devpass123')
            customer.save()
            self.stdout.write(self.style.SUCCESS(f'  Created customer: {customer.get_full_name()}'))
        else:
            self.stdout.write(f'  Customer exists: {customer.get_full_name()}')

        # 5. Pets + PatientRecords
        pets_data = [
            {'name': '[SEED] Buddy', 'species': 'dog', 'breed': 'Golden Retriever'},
            {'name': '[SEED] Whiskers', 'species': 'cat', 'breed': 'Siamese'},
            {'name': '[SEED] Max', 'species': 'dog', 'breed': 'German Shepherd'},
        ]
        pets = []
        for data in pets_data:
            pet, created = Pet.objects.get_or_create(
                name=data['name'],
                owner=customer,
                defaults={
                    'species': data['species'],
                    'breed': data['breed'],
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created pet: {pet.name}'))
            else:
                self.stdout.write(f'  Pet exists: {pet.name}')
            pets.append(pet)

            # Create PatientRecord for EMR (required for encounters)
            patient, p_created = PatientRecord.objects.get_or_create(
                pet=pet,
                defaults={
                    'patient_number': f'SEED-{pet.id:04d}',
                    'primary_veterinarian': staff_users['seed_vet'],
                    'first_visit_date': timezone.now().date(),
                    'status': 'active',
                    'notes': f'[SEED] Patient record for {pet.name}',
                }
            )
            if p_created:
                self.stdout.write(self.style.SUCCESS(f'    Created patient record: {patient.patient_number}'))
            else:
                self.stdout.write(f'    Patient record exists: {patient.patient_number}')

        # 6. Service types
        services_data = [
            {'name': '[SEED] General Checkup', 'duration': 30, 'price': 50.00},
            {'name': '[SEED] Vaccination', 'duration': 15, 'price': 35.00},
            {'name': '[SEED] Dental Cleaning', 'duration': 60, 'price': 150.00},
        ]
        services = []
        for data in services_data:
            service, created = ServiceType.objects.get_or_create(
                name=data['name'],
                defaults={
                    'duration_minutes': data['duration'],
                    'price': data['price'],
                    'category': 'clinic',
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created service: {service.name}'))
            else:
                self.stdout.write(f'  Service exists: {service.name}')
            services.append(service)

        # 7. Today's appointments
        now = timezone.now()
        today_9am = now.replace(hour=9, minute=0, second=0, microsecond=0)
        vet = staff_users['seed_vet']

        appointments_data = [
            {'pet': pets[0], 'service': services[0], 'time': today_9am, 'status': 'scheduled'},
            {'pet': pets[1], 'service': services[1], 'time': today_9am + timedelta(hours=1), 'status': 'confirmed'},
            {'pet': pets[2], 'service': services[2], 'time': today_9am + timedelta(hours=2), 'status': 'scheduled'},
        ]

        for data in appointments_data:
            apt, created = Appointment.objects.get_or_create(
                pet=data['pet'],
                scheduled_start=data['time'],
                defaults={
                    'owner': customer,
                    'service': data['service'],
                    'location': location,
                    'veterinarian': vet,
                    'scheduled_end': data['time'] + timedelta(minutes=data['service'].duration_minutes),
                    'status': data['status'],
                    'notes': f"[SEED] Routine visit for {data['pet'].name}",
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(
                    f'  Created appointment: {data["pet"].name} @ {data["time"].strftime("%H:%M")}'
                ))
            else:
                self.stdout.write(
                    f'  Appointment exists: {data["pet"].name} @ {data["time"].strftime("%H:%M")}'
                )

        self.stdout.write(self.style.SUCCESS('\nSeed data complete!'))
        self.stdout.write(f'\nLogin credentials:')
        self.stdout.write(f'  Staff: seed_vet / devpass123')
        self.stdout.write(f'  Staff: seed_tech / devpass123')
        self.stdout.write(f'  Staff: seed_reception / devpass123')
        self.stdout.write(f'  Customer: seed_customer / devpass123')
