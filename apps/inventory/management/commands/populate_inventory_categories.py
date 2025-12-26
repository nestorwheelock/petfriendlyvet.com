"""Management command to populate default inventory categories."""
from django.core.management.base import BaseCommand

from apps.inventory.models import InventoryCategory


class Command(BaseCommand):
    """Populate default inventory categories for veterinary clinic."""

    help = 'Populate default inventory categories (medication, food, accessory, supply)'

    def handle(self, *args, **options):
        """Execute the command."""
        count = self._populate_categories()

        self.stdout.write(
            self.style.SUCCESS(f'Created {count} inventory categories')
        )

    def _populate_categories(self) -> int:
        """Populate default inventory categories."""
        categories = [
            {
                'code': 'medication',
                'name': 'Medications',
                'name_es': 'Medicamentos',
                'description': 'Pharmaceutical products and vaccines',
                'requires_refrigeration': False,
                'requires_controlled_access': False,
                'is_pharmaceutical': True,
                'is_perishable': True,
                'icon': 'pill',
                'sort_order': 1,
            },
            {
                'code': 'controlled',
                'name': 'Controlled Substances',
                'name_es': 'Sustancias Controladas',
                'description': 'DEA-scheduled controlled medications',
                'requires_refrigeration': False,
                'requires_controlled_access': True,
                'is_pharmaceutical': True,
                'is_perishable': True,
                'icon': 'lock',
                'sort_order': 2,
            },
            {
                'code': 'vaccine',
                'name': 'Vaccines',
                'name_es': 'Vacunas',
                'description': 'Vaccines requiring cold chain storage',
                'requires_refrigeration': True,
                'requires_controlled_access': False,
                'is_pharmaceutical': True,
                'is_perishable': True,
                'icon': 'syringe',
                'sort_order': 3,
            },
            {
                'code': 'food',
                'name': 'Pet Food',
                'name_es': 'Alimentos',
                'description': 'Pet food and nutritional products',
                'requires_refrigeration': False,
                'requires_controlled_access': False,
                'is_pharmaceutical': False,
                'is_perishable': True,
                'icon': 'bowl-food',
                'sort_order': 4,
            },
            {
                'code': 'accessory',
                'name': 'Accessories',
                'name_es': 'Accesorios',
                'description': 'Pet accessories, toys, and supplies',
                'requires_refrigeration': False,
                'requires_controlled_access': False,
                'is_pharmaceutical': False,
                'is_perishable': False,
                'icon': 'shopping-bag',
                'sort_order': 5,
            },
            {
                'code': 'supply',
                'name': 'Medical Supplies',
                'name_es': 'Suministros Medicos',
                'description': 'Consumable medical supplies (syringes, bandages)',
                'requires_refrigeration': False,
                'requires_controlled_access': False,
                'is_pharmaceutical': False,
                'is_perishable': False,
                'icon': 'first-aid',
                'sort_order': 6,
            },
            {
                'code': 'hygiene',
                'name': 'Hygiene & Grooming',
                'name_es': 'Higiene y Aseo',
                'description': 'Shampoos, grooming tools, dental care',
                'requires_refrigeration': False,
                'requires_controlled_access': False,
                'is_pharmaceutical': False,
                'is_perishable': False,
                'icon': 'sparkles',
                'sort_order': 7,
            },
            {
                'code': 'equipment',
                'name': 'Equipment',
                'name_es': 'Equipo',
                'description': 'Durable medical equipment and tools',
                'requires_refrigeration': False,
                'requires_controlled_access': False,
                'is_pharmaceutical': False,
                'is_perishable': False,
                'icon': 'wrench',
                'sort_order': 8,
            },
        ]

        created = 0
        for cat_data in categories:
            code = cat_data.pop('code')
            _, was_created = InventoryCategory.objects.get_or_create(
                code=code,
                defaults=cat_data
            )
            if was_created:
                created += 1

        return created
