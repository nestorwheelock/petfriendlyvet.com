# T-036: Product & Category Models

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement e-commerce product catalog models
**Related Story**: S-005
**Epoch**: 3
**Estimate**: 4 hours

### Constraints
**Allowed File Paths**: apps/store/models/
**Forbidden Paths**: apps/vet_clinic/

### Deliverables
- [ ] Category model with hierarchy
- [ ] Product model with variants
- [ ] ProductImage model
- [ ] Pricing and discounts
- [ ] Stock tracking basics
- [ ] Product search

### Implementation Details

#### Models
```python
class Category(models.Model):
    """Product category with hierarchy."""

    name = models.CharField(max_length=200)
    name_es = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )

    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', null=True, blank=True)
    icon = models.CharField(max_length=50, blank=True)

    # Display
    order = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # SEO
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['order', 'name']

    def get_ancestors(self):
        """Get parent categories."""
        ancestors = []
        current = self.parent
        while current:
            ancestors.insert(0, current)
            current = current.parent
        return ancestors


class Product(models.Model):
    """Store product."""

    PRODUCT_TYPES = [
        ('simple', 'Simple Product'),
        ('variable', 'Variable Product'),  # Has variants
        ('bundle', 'Bundle'),
    ]

    # Basic info
    name = models.CharField(max_length=500)
    name_es = models.CharField(max_length=500)
    name_en = models.CharField(max_length=500)
    slug = models.SlugField(unique=True)

    sku = models.CharField(max_length=100, unique=True)
    barcode = models.CharField(max_length=100, blank=True, db_index=True)

    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES, default='simple')

    # Categories
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products'
    )
    categories = models.ManyToManyField(
        Category,
        related_name='all_products',
        blank=True
    )

    # Description
    short_description = models.TextField(blank=True)
    short_description_es = models.TextField(blank=True)
    short_description_en = models.TextField(blank=True)
    description = models.TextField(blank=True)
    description_es = models.TextField(blank=True)
    description_en = models.TextField(blank=True)

    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Tax
    is_taxable = models.BooleanField(default=True)
    tax_category = models.CharField(max_length=50, default='standard')  # For CFDI

    # Inventory
    track_inventory = models.BooleanField(default=True)
    stock_quantity = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=5)
    allow_backorder = models.BooleanField(default=False)

    # Physical
    weight_kg = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    length_cm = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    width_cm = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    height_cm = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Pet species targeting
    for_species = models.JSONField(default=list)  # ["dog", "cat"]

    # Display
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_visible = models.BooleanField(default=True)

    # Pharmacy/prescription
    requires_prescription = models.BooleanField(default=False)
    is_controlled_substance = models.BooleanField(default=False)

    # SEO
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', 'name']

    @property
    def is_on_sale(self):
        return self.compare_at_price and self.compare_at_price > self.price

    @property
    def discount_percent(self):
        if self.is_on_sale:
            return int((1 - self.price / self.compare_at_price) * 100)
        return 0

    @property
    def in_stock(self):
        if not self.track_inventory:
            return True
        return self.stock_quantity > 0 or self.allow_backorder


class ProductVariant(models.Model):
    """Product variant (size, color, etc.)."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants'
    )

    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100, unique=True)
    barcode = models.CharField(max_length=100, blank=True)

    # Attributes
    attributes = models.JSONField(default=dict)
    # {"size": "500g", "flavor": "chicken"}

    # Pricing (overrides product if set)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    # Inventory
    stock_quantity = models.IntegerField(default=0)

    # Physical (overrides product if set)
    weight_kg = models.DecimalField(max_digits=10, decimal_places=3, null=True)

    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']


class ProductImage(models.Model):
    """Product images."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='images'
    )

    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.IntegerField(default=0)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ['order']


class ProductBundle(models.Model):
    """Bundle product items."""

    bundle_product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='bundle_items'
    )
    included_product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='in_bundles'
    )
    quantity = models.IntegerField(default=1)
```

### Search Index
```python
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex

class Product(models.Model):
    # ... existing fields ...

    search_vector = SearchVectorField(null=True)

    class Meta:
        indexes = [
            GinIndex(fields=['search_vector']),
        ]

# Management command or signal to update search vector
def update_search_vector(product):
    product.search_vector = (
        SearchVector('name', weight='A') +
        SearchVector('name_es', weight='A') +
        SearchVector('name_en', weight='A') +
        SearchVector('description', weight='B') +
        SearchVector('sku', weight='C')
    )
    product.save(update_fields=['search_vector'])
```

### Test Cases
- [ ] Categories nest correctly
- [ ] Products CRUD works
- [ ] Variants linked to products
- [ ] Images uploaded correctly
- [ ] Pricing calculations accurate
- [ ] Search returns results
- [ ] Stock tracking works

### Definition of Done
- [ ] All models migrated
- [ ] Admin interface complete
- [ ] Search functional
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-001: Django Project Setup
