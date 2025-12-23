"""File upload validators for secure file handling."""
import os
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from PIL import Image

MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB
ALLOWED_IMAGE_TYPES = ['JPEG', 'PNG', 'GIF', 'WEBP']


def validate_file_size(file):
    """Validate that uploaded file is under the size limit.

    Args:
        file: Django UploadedFile instance

    Raises:
        ValidationError: If file exceeds MAX_FILE_SIZE (2 MB)
    """
    if file.size > MAX_FILE_SIZE:
        raise ValidationError(
            _('File size must be no more than 2 MB. Your file is %(size)s.'),
            params={'size': f'{file.size / (1024 * 1024):.1f} MB'},
            code='file_too_large'
        )


def validate_image_type(file):
    """Validate that uploaded file is a valid image type.

    Uses Pillow to verify file content, not just extension or MIME type.
    This prevents attackers from uploading malicious files with renamed extensions.

    Args:
        file: Django UploadedFile instance

    Raises:
        ValidationError: If file is not a valid image or is not an allowed type
    """
    # Reset file pointer to beginning
    file.seek(0)

    try:
        img = Image.open(file)
        # Verify the image is actually readable
        img.verify()

        # Check format is in allowed list
        if img.format not in ALLOWED_IMAGE_TYPES:
            raise ValidationError(
                _('Unsupported image type. Allowed types: %(types)s.'),
                params={'types': ', '.join(ALLOWED_IMAGE_TYPES)},
                code='invalid_image_type'
            )
    except (IOError, SyntaxError) as e:
        # File is not a valid image
        raise ValidationError(
            _('Invalid image file. Please upload a valid image (JPEG, PNG, GIF, or WebP).'),
            code='invalid_image'
        )
    finally:
        # Reset file pointer for further processing
        file.seek(0)


def sanitize_filename(filename):
    """Sanitize uploaded filename to prevent directory traversal.

    Removes path components and special characters that could be used
    for malicious purposes.

    Args:
        filename: Original filename string

    Returns:
        Sanitized filename safe for storage
    """
    # Get just the filename, remove any path components
    filename = os.path.basename(filename)

    # Remove directory traversal attempts
    filename = filename.replace('..', '')

    # Split name and extension
    name, ext = os.path.splitext(filename)

    # Remove special characters from name, keep only alphanumeric, hyphen, underscore
    name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)

    # Ensure name is not empty
    if not name:
        name = 'upload'

    # Normalize extension (lowercase, remove extra dots)
    ext = ext.lower().lstrip('.')
    if ext:
        ext = '.' + re.sub(r'[^a-zA-Z0-9]', '', ext)

    return f"{name}{ext}"


def avatar_upload_path(instance, filename):
    """Generate secure upload path for avatar images.

    Args:
        instance: User model instance
        filename: Original filename

    Returns:
        Safe file path for storage
    """
    safe_name = sanitize_filename(filename)
    return f'avatars/user_{instance.pk}/{safe_name}'
