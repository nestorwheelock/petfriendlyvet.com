"""Management command to populate default product types."""
from django.core.management.base import BaseCommand

from apps.store.models import ProductType


class Command(BaseCommand):
    """Populate default product types for store configuration."""

    help = 'Populate default product types (physical, service, bundle, dropship)'

    def handle(self, *args, **options):
        """Execute the command."""
        count = self._populate_product_types()

        self.stdout.write(
            self.style.SUCCESS(f'Created {count} product types')
        )

    def _populate_product_types(self) -> int:
        """Populate default product types."""
        types = [
            {
                'code': 'physical',
                'name': 'Physical Product',
                'name_es': 'Producto Fisico',
                'description': 'Tangible items that require inventory tracking',
                'requires_inventory': True,
                'requires_service_module': False,
                'allows_shipping': True,
            },
            {
                'code': 'service',
                'name': 'Service',
                'name_es': 'Servicio',
                'description': 'Intangible services delivered by staff',
                'requires_inventory': False,
                'requires_service_module': True,
                'allows_shipping': False,
            },
            {
                'code': 'bundle',
                'name': 'Bundle',
                'name_es': 'Paquete',
                'description': 'Combination of multiple products or services',
                'requires_inventory': False,
                'requires_service_module': False,
                'allows_shipping': True,
            },
            {
                'code': 'dropship',
                'name': 'Drop Ship',
                'name_es': 'Envio Directo',
                'description': 'Products shipped directly from supplier',
                'requires_inventory': False,
                'requires_service_module': False,
                'allows_shipping': True,
            },
            {
                'code': 'subscription',
                'name': 'Subscription',
                'name_es': 'Suscripcion',
                'description': 'Recurring products or services',
                'requires_inventory': False,
                'requires_service_module': False,
                'allows_shipping': True,
            },
            {
                'code': 'digital',
                'name': 'Digital Product',
                'name_es': 'Producto Digital',
                'description': 'Digital downloads or online access',
                'requires_inventory': False,
                'requires_service_module': False,
                'allows_shipping': False,
            },
        ]

        created = 0
        for type_data in types:
            code = type_data.pop('code')
            _, was_created = ProductType.objects.get_or_create(
                code=code,
                defaults=type_data
            )
            if was_created:
                created += 1

        return created
