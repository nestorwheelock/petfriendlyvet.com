"""Data migration to classify existing products by type."""
from django.db import migrations


def classify_products(apps, schema_editor):
    """Classify existing products based on their category."""
    Product = apps.get_model('store', 'Product')
    ProductType = apps.get_model('store', 'ProductType')
    Category = apps.get_model('store', 'Category')

    # Get product types
    try:
        physical_type = ProductType.objects.get(code='physical')
        service_type = ProductType.objects.get(code='service')
    except ProductType.DoesNotExist:
        print("ProductType not populated yet. Run populate_product_types first.")
        return

    # Get Servicios category
    servicios_category = Category.objects.filter(name__icontains='servicio').first()

    # Classify products
    for product in Product.objects.all():
        if servicios_category and product.category_id == servicios_category.id:
            product.product_type = service_type
        else:
            product.product_type = physical_type
        product.save(update_fields=['product_type'])

    # Print summary
    physical_count = Product.objects.filter(product_type=physical_type).count()
    service_count = Product.objects.filter(product_type=service_type).count()
    print(f"Classified {physical_count} physical products and {service_count} service products")


def reverse_classify(apps, schema_editor):
    """Reverse the classification."""
    Product = apps.get_model('store', 'Product')
    Product.objects.update(product_type=None)


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0008_add_product_type_fk'),
    ]

    operations = [
        migrations.RunPython(classify_products, reverse_classify),
    ]
