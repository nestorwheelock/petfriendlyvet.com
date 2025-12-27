# T-033: OCR and Vision Processing

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md and [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement OCR and AI vision processing for documents
**Related Story**: S-013
**Epoch**: 2
**Estimate**: 4 hours

### Constraints
**Allowed File Paths**: apps/documents/services/
**Forbidden Paths**: None

### Deliverables
- [ ] OCR service integration
- [ ] Vision API integration
- [ ] Document classification
- [ ] Data extraction (vaccinations, dates, etc.)
- [ ] Processing queue

### Implementation Details

#### OCR Service
```python
class OCRService:
    """OCR processing using Tesseract or cloud service."""

    def __init__(self):
        self.use_cloud = settings.OCR_USE_CLOUD

    async def extract_text(self, file_path: str) -> str:
        """Extract text from image or PDF."""

        if self.use_cloud:
            return await self._cloud_ocr(file_path)
        else:
            return await self._local_ocr(file_path)

    async def _local_ocr(self, file_path: str) -> str:
        """Use Tesseract for local OCR."""
        import pytesseract
        from PIL import Image
        import pdf2image

        if file_path.endswith('.pdf'):
            pages = pdf2image.convert_from_path(file_path)
            texts = []
            for page in pages:
                texts.append(pytesseract.image_to_string(page, lang='spa+eng'))
            return '\n\n'.join(texts)
        else:
            image = Image.open(file_path)
            return pytesseract.image_to_string(image, lang='spa+eng')

    async def _cloud_ocr(self, file_path: str) -> str:
        """Use Google Cloud Vision for OCR."""
        from google.cloud import vision

        client = vision.ImageAnnotatorClient()

        with open(file_path, 'rb') as f:
            content = f.read()

        image = vision.Image(content=content)
        response = client.text_detection(image=image)

        return response.full_text_annotation.text
```

#### Vision Analysis Service
```python
class VisionAnalysisService:
    """AI-powered document analysis using Claude."""

    def __init__(self):
        self.ai_service = AIService()

    async def analyze_document(
        self,
        document: Document,
        ocr_text: str = None
    ) -> dict:
        """Analyze document content with AI."""

        prompt = self._build_analysis_prompt(document, ocr_text)

        if self._is_image(document):
            # Use vision capability
            response = await self.ai_service.analyze_image(
                image_path=document.file.path,
                prompt=prompt
            )
        else:
            # Text-only analysis
            response = await self.ai_service.complete(prompt)

        return self._parse_response(response)

    def _build_analysis_prompt(self, document: Document, ocr_text: str) -> str:
        return f"""
Analyze this veterinary document and extract structured information.

Document type hint: {document.document_type}
OCR Text (if available): {ocr_text or 'N/A'}

Please extract:
1. Document type (medical_record, vaccination_card, lab_result, prescription, etc.)
2. Date on the document (if visible)
3. Pet information (name, species, breed if mentioned)
4. Clinic/vet information (if visible)
5. Key medical information:
   - Vaccinations with dates
   - Diagnoses
   - Medications prescribed
   - Lab values (if lab result)
   - Weight recorded
6. A brief summary in Spanish

Return as JSON:
{{
    "type": "document_type",
    "date": "YYYY-MM-DD or null",
    "pet_name": "name or null",
    "clinic": "clinic name or null",
    "vaccinations": [
        {{"name": "vaccine", "date": "YYYY-MM-DD"}}
    ],
    "diagnoses": ["diagnosis1", "diagnosis2"],
    "medications": [
        {{"name": "med", "dose": "dose", "frequency": "freq"}}
    ],
    "lab_values": {{}},
    "weight_kg": null,
    "summary": "Brief summary in Spanish"
}}
"""

    def _parse_response(self, response: str) -> dict:
        """Parse AI response to structured data."""
        import json
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            import re
            match = re.search(r'\{[\s\S]*\}', response)
            if match:
                return json.loads(match.group())
            return {}
```

#### Document Classifier
```python
class DocumentClassifier:
    """Classify document type from content."""

    PATTERNS = {
        'vaccination_card': [
            r'vacu(na|nación)',
            r'immunization',
            r'cartilla\s+de\s+vacunación',
        ],
        'lab_result': [
            r'hemograma',
            r'química\s+sanguínea',
            r'laboratorio',
            r'resultado',
        ],
        'prescription': [
            r'receta',
            r'prescripción',
            r'medicamento',
            r'dosis',
        ],
        'health_certificate': [
            r'certificado\s+de\s+salud',
            r'health\s+certificate',
            r'apto\s+para\s+viajar',
        ],
    }

    def classify(self, text: str) -> str:
        """Classify document type from text content."""
        import re

        text_lower = text.lower()

        scores = {}
        for doc_type, patterns in self.PATTERNS.items():
            score = sum(
                1 for pattern in patterns
                if re.search(pattern, text_lower)
            )
            scores[doc_type] = score

        if max(scores.values()) > 0:
            return max(scores, key=scores.get)

        return 'other'
```

#### Processing Queue
```python
@shared_task
def process_document(document_id: int):
    """Celery task to process uploaded document."""

    document = Document.objects.get(id=document_id)

    processor = DocumentProcessor()
    asyncio.run(processor.process(document))


@shared_task
def batch_process_pending():
    """Process all pending documents."""

    pending = Document.objects.filter(status='pending')[:10]

    for doc in pending:
        process_document.delay(doc.id)
```

#### Image Preprocessing
```python
class ImagePreprocessor:
    """Preprocess images for better OCR."""

    def preprocess(self, image_path: str) -> str:
        """Preprocess image and save to temp file."""
        from PIL import Image, ImageEnhance, ImageFilter

        image = Image.open(image_path)

        # Convert to grayscale
        image = image.convert('L')

        # Increase contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)

        # Sharpen
        image = image.filter(ImageFilter.SHARPEN)

        # Save to temp
        temp_path = f"/tmp/processed_{os.path.basename(image_path)}"
        image.save(temp_path)

        return temp_path
```

### Test Cases
- [ ] OCR extracts text from images
- [ ] OCR extracts text from PDFs
- [ ] AI analysis returns structured data
- [ ] Classification works
- [ ] Vaccination data extracted
- [ ] Date parsing works
- [ ] Processing queue runs
- [ ] Failed documents retry

### Definition of Done
- [ ] OCR service working
- [ ] AI vision analysis working
- [ ] Classification accurate
- [ ] Queue processing reliable
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-032: Document Management Models
- T-009: AI Service Layer

### Environment Variables
```
OCR_USE_CLOUD=false
GOOGLE_CLOUD_CREDENTIALS=
TESSERACT_CMD=/usr/bin/tesseract
```
