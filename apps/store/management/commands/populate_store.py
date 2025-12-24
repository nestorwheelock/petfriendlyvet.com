"""Management command to populate store with initial products."""
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.store.models import Category, Product


class Command(BaseCommand):
    help = 'Populate store with initial categories and products'

    def handle(self, *args, **options):
        self.stdout.write('Creating categories...')
        categories = self.create_categories()

        self.stdout.write('Creating products...')
        self.create_products(categories)

        self.stdout.write(self.style.SUCCESS('Store populated successfully!'))

    def create_categories(self):
        """Create product categories."""
        category_data = [
            {
                'name': 'Alimento para Perros',
                'name_es': 'Alimento para Perros',
                'name_en': 'Dog Food',
                'slug': 'alimento-perros',
                'description_es': 'Alimentos de alta calidad para perros de todas las edades y tamaños',
                'description_en': 'High quality food for dogs of all ages and sizes',
                'order': 1,
            },
            {
                'name': 'Alimento para Gatos',
                'name_es': 'Alimento para Gatos',
                'name_en': 'Cat Food',
                'slug': 'alimento-gatos',
                'description_es': 'Alimentos nutritivos para gatos adultos y cachorros',
                'description_en': 'Nutritious food for adult cats and kittens',
                'order': 2,
            },
            {
                'name': 'Accesorios',
                'name_es': 'Accesorios',
                'name_en': 'Accessories',
                'slug': 'accesorios',
                'description_es': 'Correas, transportadoras, platos y más para tu mascota',
                'description_en': 'Leashes, carriers, bowls and more for your pet',
                'order': 3,
            },
            {
                'name': 'Higiene',
                'name_es': 'Higiene',
                'name_en': 'Hygiene',
                'slug': 'higiene',
                'description_es': 'Productos de limpieza e higiene para mascotas',
                'description_en': 'Cleaning and hygiene products for pets',
                'order': 4,
            },
        ]

        categories = {}
        for data in category_data:
            cat, created = Category.objects.get_or_create(
                slug=data['slug'],
                defaults=data
            )
            categories[data['slug']] = cat
            status = 'Created' if created else 'Exists'
            self.stdout.write(f'  {status}: {cat.name}')

        return categories

    def create_products(self, categories):
        """Create initial products."""
        products_data = [
            # Dog Food - Nupec
            {
                'name': 'Nupec Adulto Razas Pequeñas 2kg',
                'name_es': 'Nupec Adulto Razas Pequeñas 2kg',
                'name_en': 'Nupec Adult Small Breeds 2kg',
                'slug': 'nupec-adulto-pequenas-2kg',
                'category_slug': 'alimento-perros',
                'description_es': 'Alimento premium para perros adultos de razas pequeñas. Fórmula balanceada con proteínas de alta calidad.',
                'description_en': 'Premium food for adult small breed dogs. Balanced formula with high quality proteins.',
                'price': Decimal('285.00'),
                'sku': 'NUP-DOG-SML-2KG',
                'stock_quantity': 25,
                'suitable_for_species': ['dog'],
                'suitable_for_sizes': ['small'],
                'suitable_for_ages': ['adult'],
                'is_featured': True,
            },
            {
                'name': 'Nupec Cachorro Razas Pequeñas 2kg',
                'name_es': 'Nupec Cachorro Razas Pequeñas 2kg',
                'name_en': 'Nupec Puppy Small Breeds 2kg',
                'slug': 'nupec-cachorro-pequenas-2kg',
                'category_slug': 'alimento-perros',
                'description_es': 'Alimento especial para cachorros de razas pequeñas. Rico en DHA para desarrollo cerebral.',
                'description_en': 'Special food for small breed puppies. Rich in DHA for brain development.',
                'price': Decimal('295.00'),
                'sku': 'NUP-PUP-SML-2KG',
                'stock_quantity': 20,
                'suitable_for_species': ['dog'],
                'suitable_for_sizes': ['small'],
                'suitable_for_ages': ['puppy'],
            },
            # Dog Food - Hill's
            {
                'name': "Hill's Science Diet Adult Small Paws 2kg",
                'name_es': "Hill's Science Diet Adulto Razas Pequeñas 2kg",
                'name_en': "Hill's Science Diet Adult Small Paws 2kg",
                'slug': 'hills-adult-small-paws-2kg',
                'category_slug': 'alimento-perros',
                'description_es': 'Nutrición clínicamente probada para perros pequeños. Con antioxidantes y omega-6.',
                'description_en': 'Clinically proven nutrition for small dogs. With antioxidants and omega-6.',
                'price': Decimal('450.00'),
                'sku': 'HIL-DOG-SML-2KG',
                'stock_quantity': 15,
                'suitable_for_species': ['dog'],
                'suitable_for_sizes': ['small'],
                'suitable_for_ages': ['adult'],
                'is_featured': True,
            },
            # Dog Food - Maka
            {
                'name': 'Maka Adulto 4kg',
                'name_es': 'Maka Adulto 4kg',
                'name_en': 'Maka Adult 4kg',
                'slug': 'maka-adulto-4kg',
                'category_slug': 'alimento-perros',
                'description_es': 'Alimento económico y nutritivo para perros adultos de todas las razas.',
                'description_en': 'Affordable and nutritious food for adult dogs of all breeds.',
                'price': Decimal('180.00'),
                'sku': 'MAK-DOG-ADL-4KG',
                'stock_quantity': 30,
                'suitable_for_species': ['dog'],
                'suitable_for_sizes': ['small', 'medium', 'large'],
                'suitable_for_ages': ['adult'],
            },
            # Cat Food - Nupec
            {
                'name': 'Nupec Gato Adulto 1.5kg',
                'name_es': 'Nupec Gato Adulto 1.5kg',
                'name_en': 'Nupec Adult Cat 1.5kg',
                'slug': 'nupec-gato-adulto-1-5kg',
                'category_slug': 'alimento-gatos',
                'description_es': 'Alimento premium para gatos adultos. Fórmula con taurina para salud cardíaca.',
                'description_en': 'Premium food for adult cats. Formula with taurine for heart health.',
                'price': Decimal('220.00'),
                'sku': 'NUP-CAT-ADL-1.5KG',
                'stock_quantity': 20,
                'suitable_for_species': ['cat'],
                'suitable_for_ages': ['adult'],
                'is_featured': True,
            },
            # Cat Food - Hill's
            {
                'name': "Hill's Science Diet Adult Cat 1.8kg",
                'name_es': "Hill's Science Diet Gato Adulto 1.8kg",
                'name_en': "Hill's Science Diet Adult Cat 1.8kg",
                'slug': 'hills-gato-adulto-1-8kg',
                'category_slug': 'alimento-gatos',
                'description_es': 'Nutrición óptima para gatos adultos. Apoya digestión saludable.',
                'description_en': 'Optimal nutrition for adult cats. Supports healthy digestion.',
                'price': Decimal('380.00'),
                'sku': 'HIL-CAT-ADL-1.8KG',
                'stock_quantity': 12,
                'suitable_for_species': ['cat'],
                'suitable_for_ages': ['adult'],
            },
            # Cat Food - Maka
            {
                'name': 'Maka Gato Adulto 3kg',
                'name_es': 'Maka Gato Adulto 3kg',
                'name_en': 'Maka Adult Cat 3kg',
                'slug': 'maka-gato-adulto-3kg',
                'category_slug': 'alimento-gatos',
                'description_es': 'Alimento balanceado y económico para gatos adultos.',
                'description_en': 'Balanced and affordable food for adult cats.',
                'price': Decimal('165.00'),
                'sku': 'MAK-CAT-ADL-3KG',
                'stock_quantity': 25,
                'suitable_for_species': ['cat'],
                'suitable_for_ages': ['adult'],
            },
            # Accessories
            {
                'name': 'Correa Artesanal',
                'name_es': 'Correa Artesanal Hecha a Mano',
                'name_en': 'Handmade Artisan Leash',
                'slug': 'correa-artesanal',
                'category_slug': 'accesorios',
                'description_es': 'Correa artesanal hecha a mano con materiales de alta calidad. Diseño único mexicano.',
                'description_en': 'Handcrafted leash made with high quality materials. Unique Mexican design.',
                'price': Decimal('150.00'),
                'sku': 'ACC-LEASH-ART',
                'stock_quantity': 10,
                'suitable_for_species': ['dog'],
                'suitable_for_sizes': ['small', 'medium'],
                'is_featured': True,
            },
            {
                'name': 'Transportadora Pequeña',
                'name_es': 'Transportadora Pequeña',
                'name_en': 'Small Pet Carrier',
                'slug': 'transportadora-pequena',
                'category_slug': 'accesorios',
                'description_es': 'Transportadora resistente para mascotas pequeñas. Ideal para viajes y visitas al veterinario.',
                'description_en': 'Durable carrier for small pets. Ideal for travel and vet visits.',
                'price': Decimal('350.00'),
                'sku': 'ACC-CARRIER-SM',
                'stock_quantity': 8,
                'suitable_for_species': ['dog', 'cat'],
                'suitable_for_sizes': ['small'],
            },
            {
                'name': 'Transportadora Mediana',
                'name_es': 'Transportadora Mediana',
                'name_en': 'Medium Pet Carrier',
                'slug': 'transportadora-mediana',
                'category_slug': 'accesorios',
                'description_es': 'Transportadora espaciosa para mascotas medianas. Con ventilación adecuada.',
                'description_en': 'Spacious carrier for medium pets. With proper ventilation.',
                'price': Decimal('450.00'),
                'sku': 'ACC-CARRIER-MD',
                'stock_quantity': 6,
                'suitable_for_species': ['dog', 'cat'],
                'suitable_for_sizes': ['medium'],
            },
            {
                'name': 'Plato Doble Acero Inoxidable',
                'name_es': 'Plato Doble Acero Inoxidable',
                'name_en': 'Double Stainless Steel Bowl',
                'slug': 'plato-doble-acero',
                'category_slug': 'accesorios',
                'description_es': 'Plato doble de acero inoxidable para agua y comida. Fácil de limpiar.',
                'description_en': 'Double stainless steel bowl for water and food. Easy to clean.',
                'price': Decimal('85.00'),
                'sku': 'ACC-BOWL-DBL',
                'stock_quantity': 15,
                'suitable_for_species': ['dog', 'cat'],
            },
            # Hygiene
            {
                'name': 'Bolsas para Popó 1 Rollo',
                'name_es': 'Bolsas para Popó (1 Rollo)',
                'name_en': 'Poop Bags (1 Roll)',
                'slug': 'bolsas-popo-1-rollo',
                'category_slug': 'higiene',
                'description_es': 'Rollo de bolsas biodegradables para recoger desechos. 15 bolsas por rollo.',
                'description_en': 'Roll of biodegradable bags for waste pickup. 15 bags per roll.',
                'price': Decimal('10.00'),
                'sku': 'HYG-BAGS-1R',
                'stock_quantity': 100,
                'suitable_for_species': ['dog'],
            },
            {
                'name': 'Bolsas para Popó 15 Rollos',
                'name_es': 'Bolsas para Popó (15 Rollos)',
                'name_en': 'Poop Bags (15 Rolls)',
                'slug': 'bolsas-popo-15-rollos',
                'category_slug': 'higiene',
                'description_es': 'Paquete de 15 rollos de bolsas biodegradables. ¡Mejor precio!',
                'description_en': 'Pack of 15 rolls of biodegradable bags. Best value!',
                'price': Decimal('120.00'),
                'compare_at_price': Decimal('150.00'),
                'sku': 'HYG-BAGS-15R',
                'stock_quantity': 40,
                'suitable_for_species': ['dog'],
                'is_featured': True,
            },
            {
                'name': 'Shampoo Antipulgas 500ml',
                'name_es': 'Shampoo Antipulgas 500ml',
                'name_en': 'Flea Shampoo 500ml',
                'slug': 'shampoo-antipulgas-500ml',
                'category_slug': 'higiene',
                'description_es': 'Shampoo medicado para eliminar pulgas y garrapatas. Aroma agradable.',
                'description_en': 'Medicated shampoo to eliminate fleas and ticks. Pleasant scent.',
                'price': Decimal('95.00'),
                'sku': 'HYG-SHAMP-FLEA',
                'stock_quantity': 20,
                'suitable_for_species': ['dog', 'cat'],
            },
            {
                'name': 'Toallitas Húmedas para Mascotas',
                'name_es': 'Toallitas Húmedas para Mascotas (50 pzas)',
                'name_en': 'Pet Wet Wipes (50 pcs)',
                'slug': 'toallitas-humedas-mascotas',
                'category_slug': 'higiene',
                'description_es': 'Toallitas húmedas hipoalergénicas para limpieza diaria. Sin alcohol.',
                'description_en': 'Hypoallergenic wet wipes for daily cleaning. Alcohol-free.',
                'price': Decimal('65.00'),
                'sku': 'HYG-WIPES-50',
                'stock_quantity': 30,
                'suitable_for_species': ['dog', 'cat'],
            },
        ]

        for data in products_data:
            category_slug = data.pop('category_slug')
            category = categories[category_slug]

            product, created = Product.objects.get_or_create(
                slug=data['slug'],
                defaults={
                    **data,
                    'category': category,
                    'description': data.get('description_es', ''),
                }
            )
            status = 'Created' if created else 'Exists'
            self.stdout.write(f'  {status}: {product.name} - ${product.price} MXN')
