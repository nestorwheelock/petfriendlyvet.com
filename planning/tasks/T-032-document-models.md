# T-032: Document Management Models

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement document upload and management system
**Related Story**: S-013
**Epoch**: 2
**Estimate**: 3 hours

### Constraints
**Allowed File Paths**: apps/documents/models/
**Forbidden Paths**: apps/store/

### Deliverables
- [ ] Document model
- [ ] DocumentCategory model
- [ ] OCR result storage
- [ ] Version tracking
- [ ] Access control

### Implementation Details

#### Models
```python
class DocumentCategory(models.Model):
    """Categories for organizing documents."""

    name = models.CharField(max_length=100)
    name_es = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = "Document Categories"
        ordering = ['order']


class Document(models.Model):
    """Uploaded document."""

    STATUS_CHOICES = [
        ('pending', 'Pending Processing'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Processing Failed'),
    ]

    DOCUMENT_TYPES = [
        ('medical_record', 'Medical Record'),
        ('vaccination_card', 'Vaccination Card'),
        ('lab_result', 'Lab Result'),
        ('prescription', 'Prescription'),
        ('consent_form', 'Consent Form'),
        ('insurance', 'Insurance Document'),
        ('health_certificate', 'Health Certificate'),
        ('adoption_papers', 'Adoption Papers'),
        ('photo', 'Photo'),
        ('other', 'Other'),
    ]

    # Ownership
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    pet = models.ForeignKey(
        'vet_clinic.Pet',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='documents'
    )

    # File info
    file = models.FileField(upload_to='documents/%Y/%m/')
    original_filename = models.CharField(max_length=255)
    file_size = models.IntegerField()  # bytes
    mime_type = models.CharField(max_length=100)
    file_hash = models.CharField(max_length=64, db_index=True)  # SHA-256

    # Classification
    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    # Processing status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    processing_error = models.TextField(blank=True)

    # OCR/Vision results
    ocr_text = models.TextField(blank=True)
    extracted_data = models.JSONField(default=dict)  # Structured data from AI
    ai_summary = models.TextField(blank=True)

    # Metadata
    document_date = models.DateField(null=True, blank=True)  # Date ON the document
    source = models.CharField(max_length=100, blank=True)  # "Lab XYZ", "Previous Vet"

    # Access control
    is_private = models.BooleanField(default=False)  # Staff only
    is_verified = models.BooleanField(default=False)  # Staff verified accuracy
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_documents'
    )

    # Links
    medical_record = models.ForeignKey(
        'vet_clinic.MedicalRecord',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='linked_documents'
    )

    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True)
    updated_at = models.DateTimeField(auto_now=True)
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_documents'
    )

    class Meta:
        ordering = ['-uploaded_at']

    def save(self, *args, **kwargs):
        if not self.file_hash and self.file:
            import hashlib
            self.file_hash = hashlib.sha256(self.file.read()).hexdigest()
            self.file.seek(0)
        super().save(*args, **kwargs)


class DocumentVersion(models.Model):
    """Version history for documents."""

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='versions'
    )
    version_number = models.IntegerField()
    file = models.FileField(upload_to='documents/versions/%Y/%m/')
    file_hash = models.CharField(max_length=64)
    notes = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ['document', 'version_number']
        ordering = ['-version_number']


class DocumentShare(models.Model):
    """Sharing documents with other users or externally."""

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='shares'
    )

    # Share with user
    shared_with = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    # Share via link
    share_token = models.CharField(max_length=64, unique=True, null=True)
    expires_at = models.DateTimeField(null=True)
    password_protected = models.BooleanField(default=False)
    password_hash = models.CharField(max_length=128, blank=True)

    # Permissions
    can_download = models.BooleanField(default=True)

    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_shares'
    )
    access_count = models.IntegerField(default=0)
    last_accessed = models.DateTimeField(null=True)
```

### Document Processing Pipeline
```python
class DocumentProcessor:
    """Process uploaded documents with OCR and AI."""

    async def process(self, document: Document):
        """Full processing pipeline."""

        try:
            document.status = 'processing'
            document.save()

            # 1. OCR if image or PDF
            if self.needs_ocr(document):
                document.ocr_text = await self.run_ocr(document)

            # 2. AI analysis
            if document.ocr_text or self.is_image(document):
                result = await self.ai_analyze(document)
                document.extracted_data = result.get('data', {})
                document.ai_summary = result.get('summary', '')

                # Auto-classify
                if not document.document_type:
                    document.document_type = result.get('type', 'other')

                # Extract date
                if not document.document_date:
                    document.document_date = result.get('date')

            document.status = 'completed'
            document.processed_at = timezone.now()

        except Exception as e:
            document.status = 'failed'
            document.processing_error = str(e)

        document.save()
```

### Test Cases
- [ ] Document upload works
- [ ] File hash calculated
- [ ] Categories assigned
- [ ] Version history tracks
- [ ] Sharing with tokens works
- [ ] Access control enforced
- [ ] OCR text stored

### Definition of Done
- [ ] All models migrated
- [ ] File handling secure
- [ ] Version control working
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-024: Pet Profile Models
- T-003: Authentication System
