"""
Custom storage backends for media file handling.

Features:
- UUID-based filenames for security and uniqueness
- Content hash-based deduplication
- Preserves original file extension
"""
import hashlib
import uuid
from pathlib import Path

from django.core.files.storage import FileSystemStorage
from django.conf import settings


class HashedFileSystemStorage(FileSystemStorage):
    """
    Storage backend that:
    1. Renames files to UUID-based names
    2. Computes content hash for deduplication
    3. Avoids storing duplicate files
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _get_content_hash(self, content):
        """Compute SHA-256 hash of file content."""
        hasher = hashlib.sha256()
        for chunk in content.chunks():
            hasher.update(chunk)
        # Reset file pointer for subsequent reads
        content.seek(0)
        return hasher.hexdigest()

    def _get_hash_path(self, hash_value, extension):
        """
        Generate path based on hash for deduplication.
        Uses first 2 chars as subdirectory for filesystem efficiency.
        Format: hashed/{ab}/{abcdef123456...}.ext
        """
        subdir = hash_value[:2]
        filename = f"{hash_value}{extension}"
        return Path('hashed') / subdir / filename

    def _find_existing_by_hash(self, content_hash, extension):
        """Check if a file with this hash already exists."""
        hash_path = self._get_hash_path(content_hash, extension)
        full_path = Path(self.location) / hash_path
        if full_path.exists():
            return str(hash_path)
        return None

    def save(self, name, content, max_length=None):
        """
        Save file with deduplication.

        If a file with identical content already exists, return its path
        instead of saving a duplicate.
        """
        # Get original extension
        original_path = Path(name)
        extension = original_path.suffix.lower()

        # Compute content hash
        content_hash = self._get_content_hash(content)

        # Check for existing file with same hash
        existing_path = self._find_existing_by_hash(content_hash, extension)
        if existing_path:
            return existing_path

        # Generate hash-based path for new file
        new_name = str(self._get_hash_path(content_hash, extension))

        # Ensure directory exists
        full_dir = Path(self.location) / Path(new_name).parent
        full_dir.mkdir(parents=True, exist_ok=True)

        # Save file with new name
        return super().save(new_name, content, max_length)

    def get_available_name(self, name, max_length=None):
        """
        Since we use content hashes, names are always unique.
        No need for Django's default _1, _2 suffix logic.
        """
        return name


def uuid_upload_path(instance, filename):
    """
    Generate UUID-based upload path preserving extension.

    Usage in models:
        photo = models.ImageField(upload_to=uuid_upload_path)

    Returns paths like: uploads/2024/12/a1b2c3d4-e5f6-7890-abcd-ef1234567890.jpg
    """
    from django.utils import timezone

    ext = Path(filename).suffix.lower()
    unique_name = f"{uuid.uuid4()}{ext}"
    date_path = timezone.now().strftime('%Y/%m')
    return f"uploads/{date_path}/{unique_name}"


def _uuid_path(folder, filename):
    """Helper to generate UUID-based path."""
    ext = Path(filename).suffix.lower()
    unique_name = f"{uuid.uuid4()}{ext}"
    return f"{folder}/{unique_name}"


# Pet-related paths
def pet_photo_path(instance, filename):
    """Generate path for pet photos."""
    return _uuid_path('pets', filename)


def pet_document_path(instance, filename):
    """Generate path for pet documents."""
    return _uuid_path('pet_documents', filename)


# Store paths
def product_image_path(instance, filename):
    """Generate path for product images."""
    return _uuid_path('products', filename)


def category_image_path(instance, filename):
    """Generate path for category images."""
    return _uuid_path('categories', filename)


# Account paths
def avatar_path(instance, filename):
    """Generate path for user avatars."""
    return _uuid_path('avatars', filename)


# Review paths
def review_photo_path(instance, filename):
    """Generate path for review photos."""
    return _uuid_path('reviews', filename)


def testimonial_photo_path(instance, filename):
    """Generate path for testimonial author photos."""
    return _uuid_path('testimonials', filename)


# Referral paths
def referral_file_path(instance, filename):
    """Generate path for referral files."""
    return _uuid_path('referrals', filename)


def visiting_report_path(instance, filename):
    """Generate path for visiting vet reports."""
    return _uuid_path('visiting_reports', filename)


# Delivery paths
def delivery_contract_path(instance, filename):
    """Generate path for delivery contractor documents."""
    return _uuid_path('delivery/contracts', filename)


def delivery_id_path(instance, filename):
    """Generate path for delivery ID documents."""
    return _uuid_path('delivery/ids', filename)


def delivery_proof_path(instance, filename):
    """Generate path for delivery proof images."""
    return _uuid_path('delivery/proofs', filename)


# Billing paths
def cfdi_path(instance, filename):
    """Generate path for CFDI PDF documents."""
    return _uuid_path('cfdi', filename)


def statement_path(instance, filename):
    """Generate path for account statements."""
    return _uuid_path('statements', filename)


# Practice paths
def clinic_logo_path(instance, filename):
    """Generate path for clinic logos."""
    return _uuid_path('clinic', filename)


# SEO/Blog paths
def blog_image_path(instance, filename):
    """Generate path for blog images."""
    return _uuid_path('blog', filename)


def og_image_path(instance, filename):
    """Generate path for Open Graph images."""
    return _uuid_path('blog/og', filename)


def landing_image_path(instance, filename):
    """Generate path for landing page images."""
    return _uuid_path('landing', filename)


# Travel paths
def travel_document_path(instance, filename):
    """Generate path for travel documents."""
    return _uuid_path('travel', filename)


# Report paths
def report_file_path(instance, filename):
    """Generate path for generated reports."""
    return _uuid_path('reports', filename)


# Deduplicating storage instance for media files
dedup_storage = HashedFileSystemStorage(location=settings.MEDIA_ROOT)
