"""Bootstrap command for single-tenant clinic deployment.

Creates the initial Organization and optional default Location.
This is a one-time setup operation for new deployments.

Usage:
    python manage.py bootstrap_clinic --name "Pet Friendly Vet"
    python manage.py bootstrap_clinic --name "Pet Friendly Vet" --location "Main Clinic"
    python manage.py bootstrap_clinic --name "Pet Friendly Vet" --location "Main Clinic" --code MAIN
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.parties.models import Organization
from apps.locations.models import Location


class Command(BaseCommand):
    help = 'Bootstrap clinic with initial Organization and optional Location'

    def add_arguments(self, parser):
        parser.add_argument(
            '--name',
            type=str,
            required=True,
            help='Organization name (e.g., "Pet Friendly Vet")',
        )
        parser.add_argument(
            '--location',
            type=str,
            help='Default location name (e.g., "Main Clinic"). If provided, creates a Location.',
        )
        parser.add_argument(
            '--code',
            type=str,
            default='MAIN',
            help='Location code (default: MAIN). Only used if --location is provided.',
        )
        parser.add_argument(
            '--timezone',
            type=str,
            default='America/Cancun',
            help='Location timezone (default: America/Cancun)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Update existing Organization instead of failing',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        org_name = options['name']
        location_name = options.get('location')
        location_code = options['code']
        timezone = options['timezone']
        force = options['force']

        # Check if Organization already exists
        existing_org = Organization.objects.first()

        if existing_org and not force:
            raise CommandError(
                f'Organization already exists: "{existing_org.name}" (id={existing_org.pk})\n'
                f'This is a single-tenant deployment. Use --force to update the existing Organization.'
            )

        if existing_org and force:
            # Update existing organization
            existing_org.name = org_name
            existing_org.save(update_fields=['name'])
            org = existing_org
            self.stdout.write(
                self.style.WARNING(f'Updated existing Organization: "{org.name}" (id={org.pk})')
            )
        else:
            # Create new organization
            org = Organization.objects.create(
                name=org_name,
                is_active=True,
            )
            self.stdout.write(
                self.style.SUCCESS(f'Created Organization: "{org.name}" (id={org.pk})')
            )

        # Create Location if requested
        if location_name:
            location, created = Location.objects.get_or_create(
                organization=org,
                code=location_code,
                defaults={
                    'name': location_name,
                    'timezone': timezone,
                    'is_active': True,
                }
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created Location: "{location.name}" (code={location.code}, id={location.pk})'
                    )
                )
            else:
                # Update existing location
                location.name = location_name
                location.timezone = timezone
                location.save(update_fields=['name', 'timezone'])
                self.stdout.write(
                    self.style.WARNING(
                        f'Updated existing Location: "{location.name}" (code={location.code}, id={location.pk})'
                    )
                )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Bootstrap complete!'))
        self.stdout.write(f'  Organization: {org.name} (id={org.pk})')
        if location_name:
            location = Location.objects.filter(organization=org, code=location_code).first()
            self.stdout.write(f'  Location: {location.name} (code={location.code}, id={location.pk})')
