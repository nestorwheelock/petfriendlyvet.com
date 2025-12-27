# T-100: Universal Media Management with Image Galleries

> **REQUIRED READING:** Before implementation, review [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)

## AI Coding Brief

**Role**: Full-stack Django Developer
**Objective**: Add universal media management with image galleries for all models (Locations, Products, Pets, etc.) with UUID naming, SHA-256 hashing for deduplication and authenticity

### User Requirements (from conversation)

> "We should have image gallery for locations with the ability to choose a primary image that will be reflected in the system thumbnail"

> "Items likewise should have more than one image and a primary image"

> "Those images should follow the same uuid naming as all other images"

> "Likewise files are hashed to prevent duplication"

> "And to authenticate their originality"

## Feature Description

### Universal Media Storage (Application-Wide)

This system applies to ALL media uploads across the entire application:

**Affected Models:**
- `StockLocation` - Location photos
- `Product` - Product images
- `Pet` - Pet photos and documents
- `Staff` - Profile photos
- `Client` - Profile photos
- `Supplier` - Logo/images
- `Delivery` - Proof of delivery photos
- `PrescriptionFill` - Label images
- Any future models with image/file uploads

**Core Requirements:**
1. **UUID Naming**: All files renamed to UUID on upload
2. **SHA-256 Hashing**: Calculate and store file hash on upload
3. **Deduplication**: Reject duplicate uploads (same hash)
4. **Authenticity**: Verify file integrity via hash comparison
5. **Primary Image**: Each gallery has one primary image for thumbnails

### Image Gallery Features

For models that need multiple images (Locations, Products, Pets):
- Multiple images per record
- One designated as "primary" (used for thumbnails, lists)
- Sort order support
- Gallery display in detail views
- Add/remove/reorder via staff portal

## Technical Implementation

### Core Media Module (apps/media/)

Create a new `media` app to handle all file uploads centrally:

```python
# apps/media/models.py

import uuid
import hashlib
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class MediaFile(models.Model):
    """
    Universal media file model using GenericForeignKey.
    Can be attached to any model in the system.
    """
    MEDIA_TYPES = [
        ('image', 'Image'),
        ('document', 'Document'),
        ('video', 'Video'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Generic relation to any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    # File storage
    file = models.FileField(upload_to='media/')
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPES, default='image')

    # Metadata
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    mime_type = models.CharField(max_length=100, blank=True)
    alt_text = models.CharField(max_length=255, blank=True)

    # Hashing for deduplication and authenticity
    file_hash = models.CharField(
        max_length=64,
        db_index=True,
        help_text='SHA-256 hash'
    )

    # Gallery features
    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    # Audit
    uploaded_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_primary', 'sort_order', 'created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['file_hash']),
        ]

    @staticmethod
    def calculate_hash(file):
        """Calculate SHA-256 hash of file."""
        hasher = hashlib.sha256()
        file.seek(0)
        for chunk in file.chunks():
            hasher.update(chunk)
        file.seek(0)
        return hasher.hexdigest()

    def verify_integrity(self):
        """Verify file integrity via hash comparison."""
        current_hash = self.calculate_hash(self.file)
        return current_hash == self.file_hash
```

### Mixin for Models with Media

```python
# apps/media/mixins.py

from django.contrib.contenttypes.fields import GenericRelation

class MediaMixin(models.Model):
    """Add to any model that needs media attachments."""

    media_files = GenericRelation('media.MediaFile')

    class Meta:
        abstract = True

    @property
    def primary_image(self):
        """Get primary image or first image."""
        return (
            self.media_files.filter(is_primary=True, media_type='image').first()
            or self.media_files.filter(media_type='image').first()
        )

    @property
    def images(self):
        """Get all images."""
        return self.media_files.filter(media_type='image')

    @property
    def documents(self):
        """Get all documents."""
        return self.media_files.filter(media_type='document')
```

### Usage in Existing Models

```python
# apps/inventory/models.py
from apps.media.mixins import MediaMixin

class StockLocation(MediaMixin, models.Model):
    # Existing fields...
    pass  # Now has .images, .primary_image, .media_files


# apps/store/models.py
from apps.media.mixins import MediaMixin

class Product(MediaMixin, models.Model):
    # Existing fields...
    pass  # Now has .images, .primary_image, .media_files


# apps/crm/models.py
from apps.media.mixins import MediaMixin

class Pet(MediaMixin, models.Model):
    # Existing fields...
    pass  # Now has .images, .primary_image, .media_files
```

### UUID Image Naming & File Hashing

```python
# utils/storage.py

import uuid
import hashlib
from pathlib import Path
from django.core.files.uploadedfile import UploadedFile

def uuid_upload_path(instance, filename):
    """Generate UUID-based file path for uploaded images."""
    ext = Path(filename).suffix.lower()
    uuid_name = uuid.uuid4().hex
    model_name = instance.__class__.__name__.lower()
    return f'{model_name}/{uuid_name}{ext}'


def calculate_file_hash(file: UploadedFile) -> str:
    """Calculate SHA-256 hash of uploaded file for deduplication and authenticity."""
    hasher = hashlib.sha256()
    # Reset file pointer
    file.seek(0)
    # Read in chunks for memory efficiency
    for chunk in file.chunks():
        hasher.update(chunk)
    file.seek(0)  # Reset for subsequent reads
    return hasher.hexdigest()
```

### Image Model with Hashing

```python
class LocationImage(models.Model):
    """Image for a stock location."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    location = models.ForeignKey(
        'StockLocation',
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to=uuid_upload_path)
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    # File integrity and deduplication
    file_hash = models.CharField(
        max_length=64,
        db_index=True,
        help_text='SHA-256 hash for deduplication and authenticity verification'
    )
    original_filename = models.CharField(max_length=255, blank=True)
    file_size = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'created_at']
        # Prevent duplicate images for same location
        unique_together = ['location', 'file_hash']

    def save(self, *args, **kwargs):
        # Ensure only one primary image per location
        if self.is_primary:
            LocationImage.objects.filter(
                location=self.location, is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

    @classmethod
    def check_duplicate(cls, location, file_hash):
        """Check if image already exists for this location."""
        return cls.objects.filter(location=location, file_hash=file_hash).exists()

    def verify_integrity(self):
        """Verify file hash matches stored hash (authenticity check)."""
        current_hash = calculate_file_hash(self.image.file)
        return current_hash == self.file_hash
```

### Deduplication Logic in Form/View

```python
def handle_image_upload(location, uploaded_file):
    """Handle image upload with deduplication."""
    file_hash = calculate_file_hash(uploaded_file)

    # Check for duplicate
    if LocationImage.check_duplicate(location, file_hash):
        raise ValidationError('This image already exists for this location.')

    # Create image record
    return LocationImage.objects.create(
        location=location,
        image=uploaded_file,
        file_hash=file_hash,
        original_filename=uploaded_file.name,
        file_size=uploaded_file.size,
    )
```

### Benefits of File Hashing

1. **Deduplication**: Prevents uploading the same image twice
2. **Authenticity**: Verify file hasn't been tampered with
3. **Integrity**: Detect file corruption
4. **Storage Efficiency**: Reuse existing files if same hash (optional CDN dedup)

### Model Properties

```python
# Add to StockLocation
@property
def primary_image(self):
    """Return primary image or first image."""
    return self.images.filter(is_primary=True).first() or self.images.first()

# Add to Product
@property
def primary_image(self):
    """Return primary image or first image."""
    return self.images.filter(is_primary=True).first() or self.images.first()
```

### Staff Portal Views

1. **Image List/Upload**: Within location/product edit forms
2. **Set Primary**: Quick action to set primary image
3. **Delete Image**: With confirmation
4. **Reorder**: Drag-and-drop ordering (optional, can use sort_order field)

### Template Updates

```html
<!-- Location thumbnail in lists -->
{% if location.primary_image %}
<img src="{{ location.primary_image.image.url }}"
     alt="{{ location.primary_image.alt_text|default:location.name }}"
     class="w-16 h-16 object-cover rounded">
{% else %}
<div class="w-16 h-16 bg-gray-200 rounded flex items-center justify-center">
    <span class="text-2xl">📍</span>
</div>
{% endif %}

<!-- Product thumbnail in store -->
{% if product.primary_image %}
<img src="{{ product.primary_image.image.url }}"
     alt="{{ product.primary_image.alt_text|default:product.name }}"
     class="w-full h-48 object-cover">
{% else %}
<div class="w-full h-48 bg-gray-200 flex items-center justify-center">
    <span class="text-4xl">📦</span>
</div>
{% endif %}
```

## Definition of Done

- [ ] LocationImage model created with migrations
- [ ] ProductImage model created with migrations
- [ ] UUID-based file naming implemented
- [ ] Primary image selection logic works
- [ ] Image upload forms in staff portal
- [ ] Image management UI (add/delete/set primary)
- [ ] Thumbnails display in list views
- [ ] Gallery display in detail views
- [ ] Tests for image models and views (>95% coverage)
- [ ] Migration tested on existing data

## Test Cases

```python
class TestLocationImage:
    def test_uuid_naming(self):
        """Uploaded images use UUID filenames."""

    def test_primary_image_selection(self):
        """Only one image can be primary per location."""

    def test_primary_image_property(self):
        """primary_image returns primary or first."""

class TestProductImage:
    def test_uuid_naming(self):
        """Uploaded images use UUID filenames."""

    def test_primary_image_selection(self):
        """Only one image can be primary per product."""
```

## Related Files

- `apps/inventory/models.py` - LocationImage model
- `apps/store/models.py` - ProductImage model
- `apps/inventory/views.py` - Image management views
- `apps/inventory/forms.py` - Image upload forms
- `templates/inventory/location_form.html` - Gallery UI
- `templates/store/product_form.html` - Gallery UI

## Priority

Medium - Enhances user experience but not blocking core functionality

## Estimate

4-6 hours

## Dependencies

- None - can be implemented independently
