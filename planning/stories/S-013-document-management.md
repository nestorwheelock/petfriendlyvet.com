# S-013: Document Management

**Story Type:** User Story
**Priority:** Medium
**Epoch:** 2 (with Pet Profiles)
**Status:** PENDING
**Module:** django-vet-clinic

## User Story

**As a** pet owner
**I want to** upload and access documents for my pets
**So that** I have all their records in one place

**As a** veterinarian
**I want to** attach documents to pet records
**So that** I have complete medical documentation

**As a** pet owner
**I want to** upload documents via chat
**So that** I can easily share information with the clinic

## Acceptance Criteria

### Document Upload
- [ ] Upload documents via web interface
- [ ] Upload documents via AI chat (drag & drop)
- [ ] Upload via WhatsApp (forward documents)
- [ ] Support common formats (PDF, JPG, PNG, HEIC)
- [ ] File size limits with clear feedback
- [ ] Progress indicator for large files
- [ ] Bulk upload multiple documents

### Document Types
- [ ] Vaccination records
- [ ] Lab results
- [ ] X-rays and imaging
- [ ] Prescription records
- [ ] Adoption/purchase papers
- [ ] Travel certificates
- [ ] Insurance documents
- [ ] Previous vet records
- [ ] Photos (injury, condition progression)

### AI-Powered Processing
- [ ] OCR text extraction from documents
- [ ] Auto-categorize document type
- [ ] Extract key data (dates, vaccine names, results)
- [ ] Auto-link to relevant pet
- [ ] Identify and flag important findings
- [ ] Vision analysis for medical images

### Document Organization
- [ ] Organize by pet
- [ ] Organize by document type
- [ ] Organize by date
- [ ] Search across all documents
- [ ] Tags and labels
- [ ] Favorite/pin important documents

### Access Control
- [ ] Owner can view their pets' documents
- [ ] Staff can view all documents
- [ ] Share documents with other vets
- [ ] Temporary share links
- [ ] Download original files
- [ ] Print-friendly versions

### Document Security
- [ ] Encrypted storage
- [ ] Access logging
- [ ] Retention policies
- [ ] GDPR-compliant deletion
- [ ] Backup and recovery

## Technical Requirements

### Models

```python
class DocumentType(models.Model):
    """Types of documents that can be uploaded"""
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    name_es = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)

    # Allowed file types
    allowed_extensions = models.JSONField(default=list)
    # [".pdf", ".jpg", ".png", ".heic"]

    # Processing
    enable_ocr = models.BooleanField(default=True)
    enable_vision = models.BooleanField(default=False)

    # Retention
    retention_days = models.IntegerField(null=True, blank=True)
    # null = keep forever

    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']


class Document(models.Model):
    """Uploaded document"""
    STATUS_CHOICES = [
        ('uploading', 'Uploading'),
        ('processing', 'Processing'),
        ('ready', 'Ready'),
        ('failed', 'Failed'),
    ]

    # Identity
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    title = models.CharField(max_length=200)
    document_type = models.ForeignKey(DocumentType, on_delete=models.SET_NULL, null=True)

    # Ownership
    pet = models.ForeignKey(
        'vet_clinic.Pet', on_delete=models.CASCADE, null=True, blank=True
    )
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='uploaded_documents'
    )

    # File
    file = models.FileField(upload_to='documents/%Y/%m/')
    original_filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField()  # bytes
    mime_type = models.CharField(max_length=100)
    file_hash = models.CharField(max_length=64)  # SHA-256 for deduplication

    # Thumbnail/preview
    thumbnail = models.ImageField(upload_to='documents/thumbnails/', null=True, blank=True)
    preview_url = models.URLField(blank=True)  # For PDFs, generated preview

    # Metadata
    document_date = models.DateField(null=True, blank=True)  # Date on document
    source = models.CharField(max_length=50)  # web, chat, whatsapp, staff
    notes = models.TextField(blank=True)
    tags = models.JSONField(default=list)

    # Processing status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploading')
    processing_error = models.TextField(blank=True)

    # OCR/AI extracted data
    ocr_text = models.TextField(blank=True)
    extracted_data = models.JSONField(default=dict)
    # {"vaccine_name": "Rabies", "date": "2025-01-15", "vet_name": "Dr. Smith"}
    ai_summary = models.TextField(blank=True)
    ai_category_confidence = models.FloatField(null=True, blank=True)

    # Flags
    is_important = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Related records (can link to multiple)
    related_visits = models.ManyToManyField('appointments.Appointment', blank=True)
    related_vaccinations = models.ManyToManyField('vet_clinic.Vaccination', blank=True)
    related_prescriptions = models.ManyToManyField('pharmacy.Prescription', blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['pet', 'document_type']),
            models.Index(fields=['owner', 'status']),
        ]


class DocumentAccess(models.Model):
    """Track document access for audit"""
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20)  # view, download, share, print
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']


class DocumentShare(models.Model):
    """Temporary share links for documents"""
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    share_token = models.CharField(max_length=64, unique=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    # Access control
    expires_at = models.DateTimeField()
    max_views = models.IntegerField(null=True, blank=True)
    view_count = models.IntegerField(default=0)
    password_hash = models.CharField(max_length=128, blank=True)

    # Recipient (optional)
    recipient_email = models.EmailField(blank=True)
    recipient_name = models.CharField(max_length=100, blank=True)
    message = models.TextField(blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)


class DocumentBundle(models.Model):
    """Collection of documents for export/sharing"""
    name = models.CharField(max_length=200)
    pet = models.ForeignKey('vet_clinic.Pet', on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    documents = models.ManyToManyField(Document)

    # Export
    export_file = models.FileField(upload_to='bundles/', null=True, blank=True)
    export_format = models.CharField(max_length=10, blank=True)  # pdf, zip

    # Purpose
    purpose = models.CharField(max_length=100, blank=True)
    # travel, insurance, new_vet, etc.

    created_at = models.DateTimeField(auto_now_add=True)


class OCRResult(models.Model):
    """Detailed OCR extraction results"""
    document = models.OneToOneField(Document, on_delete=models.CASCADE)

    # Raw extraction
    raw_text = models.TextField()
    confidence_score = models.FloatField()

    # Structured extraction
    extracted_fields = models.JSONField(default=dict)
    # {
    #   "dates": ["2025-01-15"],
    #   "names": ["Luna", "Dr. Pablo"],
    #   "medications": ["Rabies vaccine"],
    #   "values": [{"label": "Weight", "value": "5.2kg"}]
    # }

    # Processing metadata
    ocr_engine = models.CharField(max_length=50)  # tesseract, google_vision, aws_textract
    processing_time_ms = models.IntegerField()
    language_detected = models.CharField(max_length=10)

    created_at = models.DateTimeField(auto_now_add=True)
```

### AI Tools

```python
DOCUMENT_TOOLS = [
    {
        "name": "upload_document",
        "description": "Process a document uploaded by the user",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "pet_id": {"type": "integer"},
                "document_type": {"type": "string"},
                "title": {"type": "string"}
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "get_pet_documents",
        "description": "Get documents for a pet",
        "parameters": {
            "type": "object",
            "properties": {
                "pet_id": {"type": "integer"},
                "document_type": {"type": "string"},
                "date_from": {"type": "string"},
                "date_to": {"type": "string"}
            },
            "required": ["pet_id"]
        }
    },
    {
        "name": "search_documents",
        "description": "Search across all documents",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "pet_id": {"type": "integer"},
                "document_type": {"type": "string"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "analyze_document",
        "description": "Get AI analysis of a document",
        "parameters": {
            "type": "object",
            "properties": {
                "document_id": {"type": "integer"}
            },
            "required": ["document_id"]
        }
    },
    {
        "name": "extract_document_data",
        "description": "Extract structured data from a document",
        "parameters": {
            "type": "object",
            "properties": {
                "document_id": {"type": "integer"},
                "fields_to_extract": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["document_id"]
        }
    },
    {
        "name": "create_document_bundle",
        "description": "Create a bundle of documents for export",
        "parameters": {
            "type": "object",
            "properties": {
                "pet_id": {"type": "integer"},
                "document_ids": {"type": "array", "items": {"type": "integer"}},
                "purpose": {"type": "string"},
                "format": {"type": "string", "enum": ["pdf", "zip"]}
            },
            "required": ["pet_id", "document_ids"]
        }
    },
    {
        "name": "share_document",
        "description": "Create a share link for a document",
        "parameters": {
            "type": "object",
            "properties": {
                "document_id": {"type": "integer"},
                "expires_in_hours": {"type": "integer", "default": 72},
                "recipient_email": {"type": "string"},
                "message": {"type": "string"}
            },
            "required": ["document_id"]
        }
    }
]
```

## Example AI Conversations

### Document Upload via Chat
```
Owner: [Uploads PDF file]

AI: I received Luna's document. Let me process it...

    📄 Document Analysis Complete

    Type: Vaccination Record (auto-detected)
    From: Veterinaria Central, CDMX
    Date: October 15, 2024

    Extracted Information:
    • Rabies vaccine - Expires Oct 2025
    • DHPP vaccine - Expires Oct 2025
    • Bordetella - Expires Apr 2025

    I've added this to Luna's records and updated her
    vaccination schedule.

    Would you like me to set reminders for the upcoming
    due dates?

Owner: Yes please

AI: Done! I've scheduled reminders:

    • Bordetella: Reminder on March 15, 2025
    • Rabies & DHPP: Reminder on September 15, 2025

    You can view all of Luna's documents in her profile.
```

### Document Search
```
Owner: Do you have Luna's x-ray from last year?

AI: Let me search Luna's documents...

    Found 2 X-ray documents:

    1. 📷 Hip X-ray - March 12, 2024
       Taken at Pet-Friendly
       Notes: "Mild hip dysplasia observed"

    2. 📷 Chest X-ray - January 5, 2024
       Taken at Emergency Vet Cancun
       Notes: "Clear, no abnormalities"

    Which one would you like to view?

Owner: The hip one

AI: Here's Luna's hip X-ray from March 2024:

    [Image Preview]

    Dr. Pablo's notes from that visit:
    "Mild bilateral hip dysplasia, grade 1. Recommend
    joint supplements and weight management. Follow-up
    X-ray in 12 months."

    Would you like to:
    • Download the full image
    • Share with another vet
    • Schedule the follow-up X-ray
```

### Document Bundle for Travel
```
Owner: I need Luna's records for traveling to the US

AI: I can prepare a travel document bundle for Luna.

    For US entry, you typically need:
    ✓ Current rabies vaccination (within 12 months)
    ✓ Health certificate (within 10 days of travel)
    ✓ Microchip documentation

    Luna's current documents:
    ✓ Rabies vaccine - Valid until Oct 2025
    ✗ Health certificate - Not on file
    ✓ Microchip registration

    Would you like me to:
    1. Create a bundle with existing documents
    2. Schedule an appointment for health certificate

Owner: Both please, I travel on February 1st

AI: I've created a partial bundle and scheduled an appointment:

    📦 Travel Bundle (Partial)
    • Rabies vaccination record
    • Microchip registration

    📅 Health Certificate Appointment
    • Date: January 25, 2025
    • Time: 10:00 AM
    • Note: Must be within 10 days of travel

    After the appointment, I'll add the health certificate
    to complete your travel bundle.

    [Download Current Bundle] [View Appointment]
```

### Vision Analysis (Staff)
```
Staff: [Uploads photo of skin condition]

AI: I've analyzed the image of Max's skin condition.

    🔍 AI Analysis:

    Observations:
    • Circular patch of hair loss (~3cm diameter)
    • Red, irritated skin at center
    • Scaling at edges
    • Location: Right flank

    Possible conditions (for vet review):
    1. Ringworm (dermatophytosis) - High match
    2. Bacterial skin infection - Moderate match
    3. Allergic reaction - Lower match

    ⚠️ This is an AI assessment for reference only.
    Dr. Pablo should confirm the diagnosis.

    Recommended tests:
    • Wood's lamp examination
    • Skin scraping/fungal culture
    • If ringworm suspected: Check for zoonotic risk

    Would you like me to add this to Max's chart?
```

## File Processing Pipeline

```
Upload → Virus Scan → Store → Generate Thumbnail
                          ↓
                    OCR Processing
                          ↓
                    AI Classification
                          ↓
                    Data Extraction
                          ↓
                    Link to Pet Record
                          ↓
                    Ready for Access
```

## Definition of Done

- [ ] Document upload (web, chat, WhatsApp)
- [ ] File type validation and virus scanning
- [ ] Thumbnail generation
- [ ] OCR text extraction
- [ ] AI auto-categorization
- [ ] Structured data extraction
- [ ] Document search (full-text)
- [ ] Access control and logging
- [ ] Share link generation
- [ ] Document bundles for export
- [ ] Vision analysis for images
- [ ] Tests written and passing (>95% coverage)

## Dependencies

- S-001: Foundation (file storage)
- S-002: AI Chat (upload via chat)
- S-003: Pet Profiles (link to pets)
- S-006: Omnichannel (WhatsApp uploads)

## Notes

- Consider AWS S3 for file storage
- Virus scanning with ClamAV
- OCR options: Tesseract, Google Vision, AWS Textract
- HEIC conversion for iPhone photos
- Consider document size limits (10MB default)
- PDF preview generation with pdf.js or similar
