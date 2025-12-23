# T-071: File Upload Validation

> **Parent Story:** [S-027 Security Hardening](../stories/S-027-security-hardening.md)

**Task Type:** Security Implementation
**Priority:** MEDIUM
**Estimate:** 1 hour
**Status:** PENDING

---

## Objective

Implement secure file upload validation for user avatar uploads to prevent malicious file uploads, ensure proper file type validation, limit file sizes, and sanitize filenames.

---

## Background

File uploads present several security risks:
- **Malicious files**: Attackers could upload PHP shells, executables, or other dangerous files
- **Path traversal**: Malicious filenames could write files outside intended directories
- **Denial of service**: Very large files could exhaust disk space
- **XSS via filenames**: Unsanitized filenames could enable XSS attacks

---

## Current State

The User model has an `avatar` field but lacks validation for:
- File type (could upload non-images)
- File size (no maximum limit)
- Filename sanitization

---

## Implementation

### Step 1: Create Validators

```python
# apps/accounts/validators.py

import os
import magic
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from PIL import Image


# Allowed image MIME types
ALLOWED_IMAGE_TYPES = {
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
}

# Maximum file size (2MB)
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB in bytes

# Maximum image dimensions
MAX_IMAGE_DIMENSION = 4096  # pixels


def validate_image_file_type(file):
    """
    Validate that the uploaded file is actually an image.

    Uses python-magic to check file contents, not just extension.
    """
    # Read first 2048 bytes to determine file type
    file.seek(0)
    file_header = file.read(2048)
    file.seek(0)

    # Detect MIME type from file contents
    mime_type = magic.from_buffer(file_header, mime=True)

    if mime_type not in ALLOWED_IMAGE_TYPES:
        raise ValidationError(
            _('Unsupported file type: %(type)s. Allowed types: JPEG, PNG, GIF, WebP.'),
            code='invalid_image_type',
            params={'type': mime_type},
        )


def validate_file_size(file):
    """
    Validate that file size is within limits.
    """
    if file.size > MAX_FILE_SIZE:
        raise ValidationError(
            _('File size %(size)s exceeds maximum allowed size of %(max)s.'),
            code='file_too_large',
            params={
                'size': f'{file.size / (1024*1024):.1f}MB',
                'max': f'{MAX_FILE_SIZE / (1024*1024):.0f}MB',
            },
        )


def validate_image_dimensions(file):
    """
    Validate image dimensions are reasonable.

    Prevents denial of service via decompression bombs.
    """
    try:
        file.seek(0)
        img = Image.open(file)
        width, height = img.size
        file.seek(0)

        if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
            raise ValidationError(
                _('Image dimensions %(width)sx%(height)s exceed maximum of %(max)sx%(max)s.'),
                code='image_too_large',
                params={
                    'width': width,
                    'height': height,
                    'max': MAX_IMAGE_DIMENSION,
                },
            )

        # Check for decompression bombs
        # PIL has built-in protection, but we add explicit check
        pixel_count = width * height
        if pixel_count > 178956970:  # Max safe pixel count
            raise ValidationError(
                _('Image has too many pixels. Please use a smaller image.'),
                code='image_decompression_bomb',
            )

    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(
            _('Could not process image: %(error)s'),
            code='invalid_image',
            params={'error': str(e)},
        )


def validate_avatar(file):
    """
    Combined validator for avatar uploads.

    Runs all validation checks.
    """
    validate_file_size(file)
    validate_image_file_type(file)
    validate_image_dimensions(file)


def sanitize_filename(filename):
    """
    Sanitize uploaded filename to prevent path traversal.

    - Removes path components
    - Replaces dangerous characters
    - Ensures safe extension
    """
    import re
    import uuid

    # Get just the filename, remove any path
    filename = os.path.basename(filename)

    # Remove any null bytes
    filename = filename.replace('\x00', '')

    # Get extension
    _, ext = os.path.splitext(filename)
    ext = ext.lower()

    # Only allow safe extensions
    safe_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    if ext not in safe_extensions:
        ext = '.jpg'  # Default to jpg

    # Generate safe filename with UUID
    safe_name = f"{uuid.uuid4().hex}{ext}"

    return safe_name
```

### Step 2: Create Custom File Field

```python
# apps/accounts/fields.py

from django.db.models import ImageField
from django.db.models.fields.files import ImageFieldFile
from .validators import sanitize_filename


class SafeImageFieldFile(ImageFieldFile):
    """Custom ImageFieldFile that sanitizes filenames."""

    def save(self, name, content, save=True):
        # Sanitize the filename before saving
        name = sanitize_filename(name)
        super().save(name, content, save)


class SafeImageField(ImageField):
    """ImageField that sanitizes filenames and validates content."""

    attr_class = SafeImageFieldFile

    def __init__(self, *args, **kwargs):
        # Add default validators
        from .validators import validate_avatar

        validators = kwargs.get('validators', [])
        validators.append(validate_avatar)
        kwargs['validators'] = validators

        super().__init__(*args, **kwargs)
```

### Step 3: Update User Model

```python
# apps/accounts/models.py

from django.db import models
from .fields import SafeImageField
from .validators import validate_avatar


def user_avatar_path(instance, filename):
    """Generate upload path for user avatar."""
    from .validators import sanitize_filename
    safe_filename = sanitize_filename(filename)
    return f'avatars/{instance.id}/{safe_filename}'


class User(AbstractUser):
    # ... existing fields ...

    # Update avatar field with validation
    avatar = SafeImageField(
        upload_to=user_avatar_path,
        validators=[validate_avatar],
        blank=True,
        null=True,
        help_text='Profile photo (max 2MB, JPEG/PNG/GIF/WebP)',
    )
```

### Step 4: Configure Media Settings

```python
# config/settings/base.py

# Media files (uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5MB

# Pillow security settings (prevent decompression bombs)
from PIL import Image
Image.MAX_IMAGE_PIXELS = 178956970  # ~13400x13400
```

### Step 5: Nginx Configuration (Production)

```nginx
# Limit upload size at nginx level
client_max_body_size 3M;

# Serve media files with proper headers
location /media/ {
    alias /var/www/petfriendlyvet.com/media/;

    # Prevent execution of uploaded files
    location ~* \.(php|py|pl|cgi|sh|bash)$ {
        deny all;
    }

    # Set proper content types
    types {
        image/jpeg jpg jpeg;
        image/png png;
        image/gif gif;
        image/webp webp;
    }

    # Force download for non-image types
    default_type application/octet-stream;

    # Add security headers
    add_header X-Content-Type-Options nosniff;
}
```

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `apps/accounts/validators.py` | Create validators |
| `apps/accounts/fields.py` | Create SafeImageField |
| `apps/accounts/models.py` | Update avatar field |
| `config/settings/base.py` | Add upload settings |
| `requirements/base.txt` | Add python-magic |

---

## Dependencies

```
# requirements/base.txt
python-magic>=0.4.27
Pillow>=10.0.0  # Already present
```

---

## Tests Required

```python
# tests/test_file_uploads.py

import pytest
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from apps.accounts.validators import (
    validate_file_size,
    validate_image_file_type,
    validate_image_dimensions,
    sanitize_filename,
)


class TestFileValidation:
    """Test file upload validation."""

    def create_test_image(self, format='PNG', size=(100, 100)):
        """Create a test image file."""
        img = Image.new('RGB', size, color='red')
        buffer = BytesIO()
        img.save(buffer, format=format)
        buffer.seek(0)
        return buffer

    def test_valid_png_accepted(self):
        """Valid PNG should pass validation."""
        img_file = self.create_test_image('PNG')
        file = SimpleUploadedFile('test.png', img_file.read(), content_type='image/png')
        # Should not raise
        validate_image_file_type(file)

    def test_valid_jpeg_accepted(self):
        """Valid JPEG should pass validation."""
        img_file = self.create_test_image('JPEG')
        file = SimpleUploadedFile('test.jpg', img_file.read(), content_type='image/jpeg')
        validate_image_file_type(file)

    def test_php_file_rejected(self):
        """PHP files should be rejected."""
        content = b'<?php echo "hack"; ?>'
        file = SimpleUploadedFile('evil.php', content, content_type='image/png')

        with pytest.raises(ValidationError) as exc_info:
            validate_image_file_type(file)

        assert 'Unsupported file type' in str(exc_info.value)

    def test_fake_extension_rejected(self):
        """File with image extension but non-image content rejected."""
        content = b'This is not an image'
        file = SimpleUploadedFile('fake.png', content, content_type='image/png')

        with pytest.raises(ValidationError):
            validate_image_file_type(file)

    def test_large_file_rejected(self):
        """Files over 2MB should be rejected."""
        # Create file over 2MB
        content = b'x' * (3 * 1024 * 1024)  # 3MB
        file = SimpleUploadedFile('big.png', content)
        file.size = len(content)

        with pytest.raises(ValidationError) as exc_info:
            validate_file_size(file)

        assert 'exceeds maximum' in str(exc_info.value)

    def test_large_dimensions_rejected(self):
        """Images with huge dimensions should be rejected."""
        img_file = self.create_test_image('PNG', size=(5000, 5000))
        file = SimpleUploadedFile('huge.png', img_file.read())

        with pytest.raises(ValidationError) as exc_info:
            validate_image_dimensions(file)

        assert 'dimensions' in str(exc_info.value)


class TestFilenameSanitization:
    """Test filename sanitization."""

    def test_path_traversal_removed(self):
        """Path traversal attempts should be sanitized."""
        dangerous_names = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\config\\sam',
            '/etc/passwd',
            'C:\\Windows\\System32\\config\\SAM',
        ]

        for name in dangerous_names:
            safe = sanitize_filename(name)
            assert '/' not in safe
            assert '\\' not in safe
            assert '..' not in safe

    def test_null_bytes_removed(self):
        """Null bytes should be removed."""
        name = 'image\x00.php.png'
        safe = sanitize_filename(name)
        assert '\x00' not in safe

    def test_dangerous_extensions_changed(self):
        """Dangerous extensions should be changed to .jpg."""
        dangerous = ['shell.php', 'backdoor.py', 'exploit.exe']

        for name in dangerous:
            safe = sanitize_filename(name)
            assert safe.endswith('.jpg')

    def test_safe_extensions_preserved(self):
        """Safe image extensions should be preserved."""
        safe_names = [
            ('photo.jpg', '.jpg'),
            ('image.png', '.png'),
            ('animation.gif', '.gif'),
            ('modern.webp', '.webp'),
        ]

        for name, expected_ext in safe_names:
            safe = sanitize_filename(name)
            assert safe.endswith(expected_ext)

    def test_filename_is_uuid(self):
        """Sanitized filename should be a UUID."""
        import re
        safe = sanitize_filename('anything.png')
        # Should be 32 hex chars + extension
        assert re.match(r'^[a-f0-9]{32}\.png$', safe)
```

---

## Acceptance Criteria

- [ ] Avatar uploads validated for file type
- [ ] File size limited to 2MB
- [ ] Filenames sanitized (UUID + safe extension)
- [ ] Image dimensions checked
- [ ] Path traversal prevented
- [ ] Tests cover all validation scenarios
- [ ] Non-images rejected even with image extension

---

## Definition of Done

- [ ] Validators created in `apps/accounts/validators.py`
- [ ] SafeImageField created
- [ ] User model updated with validated avatar field
- [ ] Upload settings configured
- [ ] All tests pass
- [ ] python-magic added to requirements
- [ ] Manual testing confirms validation works

---

## Security Benefit

| Attack | Prevention |
|--------|------------|
| PHP shell upload | MIME type validation |
| Extension spoofing | Content-based detection |
| Decompression bomb | Dimension limits |
| Path traversal | Filename sanitization |
| XSS via filename | UUID replacement |
| DoS via large files | Size limits |

---

*Created: December 23, 2025*
