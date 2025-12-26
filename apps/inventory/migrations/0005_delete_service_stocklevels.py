"""Data migration to delete StockLevels for service-type products."""
from django.db import migrations


def delete_service_stocklevels(apps, schema_editor):
    """Delete StockLevels for products with service type."""
    StockLevel = apps.get_model('inventory', 'StockLevel')
    ProductType = apps.get_model('store', 'ProductType')

    try:
        service_type = ProductType.objects.get(code='service')
    except ProductType.DoesNotExist:
        print("Service ProductType not found. Skipping.")
        return

    # Delete stock levels for service-type products
    deleted_count = StockLevel.objects.filter(
        product__product_type=service_type
    ).delete()[0]

    print(f"Deleted {deleted_count} StockLevels for service-type products")


def reverse_delete(apps, schema_editor):
    """Cannot reverse this migration - StockLevels for services shouldn't exist."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0004_inventorycategory'),
        ('store', '0009_classify_products_by_type'),
    ]

    operations = [
        migrations.RunPython(delete_service_stocklevels, reverse_delete),
    ]
