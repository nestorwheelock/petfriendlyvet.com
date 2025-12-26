"""Migrate service products to VetProcedure model."""
from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.practice.models import ProcedureCategory, VetProcedure
from apps.store.models import Product, ProductType
from apps.billing.models import SATProductCode, SATUnitCode


class Command(BaseCommand):
    """Migrate service products to VetProcedure model."""

    help = 'Create VetProcedures from service-type store products'

    def handle(self, *args, **options):
        """Execute the command."""
        categories_created = self._create_procedure_categories()
        procedures_created = self._create_vet_procedures()

        self.stdout.write(
            self.style.SUCCESS(
                f'Created {categories_created} categories and '
                f'{procedures_created} procedures'
            )
        )

    def _create_procedure_categories(self) -> int:
        """Create procedure categories."""
        categories = [
            {
                'code': 'consultation',
                'name': 'Consultation',
                'name_es': 'Consulta',
                'description': 'General and specialty consultations',
                'icon': 'stethoscope',
                'sort_order': 1,
            },
            {
                'code': 'vaccination',
                'name': 'Vaccination',
                'name_es': 'Vacunacion',
                'description': 'Vaccine administration services',
                'icon': 'syringe',
                'sort_order': 2,
            },
            {
                'code': 'surgery',
                'name': 'Surgery',
                'name_es': 'Cirugia',
                'description': 'Surgical procedures',
                'icon': 'scissors',
                'sort_order': 3,
            },
            {
                'code': 'dental',
                'name': 'Dental',
                'name_es': 'Dental',
                'description': 'Dental care and procedures',
                'icon': 'tooth',
                'sort_order': 4,
            },
            {
                'code': 'imaging',
                'name': 'Imaging',
                'name_es': 'Imagenologia',
                'description': 'X-rays, ultrasounds, and other imaging',
                'icon': 'film',
                'sort_order': 5,
            },
            {
                'code': 'laboratory',
                'name': 'Laboratory',
                'name_es': 'Laboratorio',
                'description': 'Blood work, urinalysis, and lab tests',
                'icon': 'flask',
                'sort_order': 6,
            },
        ]

        created = 0
        for cat_data in categories:
            code = cat_data.pop('code')
            _, was_created = ProcedureCategory.objects.get_or_create(
                code=code,
                defaults=cat_data
            )
            if was_created:
                created += 1

        return created

    def _create_vet_procedures(self) -> int:
        """Create VetProcedures from service products."""
        # Get SAT codes
        try:
            vet_service_code = SATProductCode.objects.get(code='85121800')
            service_unit = SATUnitCode.objects.get(code='E48')
        except (SATProductCode.DoesNotExist, SATUnitCode.DoesNotExist):
            self.stdout.write(self.style.WARNING(
                'SAT codes not found. Run populate_sat_codes first.'
            ))
            return 0

        # Get service type products
        try:
            service_type = ProductType.objects.get(code='service')
        except ProductType.DoesNotExist:
            self.stdout.write(self.style.WARNING(
                'Service ProductType not found. Run populate_product_types first.'
            ))
            return 0

        # Get categories
        categories = {cat.code: cat for cat in ProcedureCategory.objects.all()}

        # Service mapping to categories and codes
        service_mapping = {
            'Consulta General': {
                'category': 'consultation',
                'code': 'CONSULT-GEN',
                'duration': 30,
            },
            'Vacuna Antirrábica': {
                'category': 'vaccination',
                'code': 'VAC-RAB',
                'duration': 15,
            },
            'Vacuna Múltiple Canina': {
                'category': 'vaccination',
                'code': 'VAC-MULTI-CAN',
                'duration': 15,
            },
            'Esterilización Perro Pequeño': {
                'category': 'surgery',
                'code': 'SURG-SPAY-SM',
                'duration': 60,
                'requires_anesthesia': True,
            },
            'Limpieza Dental': {
                'category': 'dental',
                'code': 'DENT-CLEAN',
                'duration': 45,
                'requires_anesthesia': True,
            },
            'Radiografía': {
                'category': 'imaging',
                'code': 'IMG-XRAY',
                'duration': 20,
            },
            'Ultrasonido': {
                'category': 'imaging',
                'code': 'IMG-ULTRA',
                'duration': 30,
            },
            'Análisis de Sangre Completo': {
                'category': 'laboratory',
                'code': 'LAB-CBC',
                'duration': 15,
            },
        }

        # Get unique service names from products
        service_products = Product.objects.filter(product_type=service_type)
        unique_services = service_products.values('name', 'price').distinct()

        created = 0
        for service in unique_services:
            name = service['name']
            if name not in service_mapping:
                self.stdout.write(self.style.WARNING(
                    f'Unknown service: {name}. Skipping.'
                ))
                continue

            mapping = service_mapping[name]
            category = categories.get(mapping['category'])
            if not category:
                self.stdout.write(self.style.WARNING(
                    f'Category not found: {mapping["category"]}. Skipping.'
                ))
                continue

            # Get average price from products
            avg_price = service_products.filter(name=name).first()
            base_price = avg_price.price if avg_price else Decimal('500.00')

            _, was_created = VetProcedure.objects.get_or_create(
                code=mapping['code'],
                defaults={
                    'name': name,
                    'name_es': name,  # Already in Spanish
                    'category': category,
                    'base_price': base_price,
                    'duration_minutes': mapping.get('duration', 30),
                    'sat_product_code': vet_service_code,
                    'sat_unit_code': service_unit,
                    'requires_anesthesia': mapping.get('requires_anesthesia', False),
                    'requires_appointment': True,
                    'requires_vet_license': True,
                }
            )
            if was_created:
                created += 1

        return created
