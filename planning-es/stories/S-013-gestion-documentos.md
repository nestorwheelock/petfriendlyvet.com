# S-013: Gestión de Documentos

> **LECTURA OBLIGATORIA:** Antes de la implementación, revisar [ESTANDARES_CODIGO.md](../ESTANDARES_CODIGO.md) y [DECISIONES_ARQUITECTURA.md](../DECISIONES_ARQUITECTURA.md)

**Tipo de Historia:** Historia de Usuario
**Prioridad:** Media
**Época:** 2 (con Perfiles de Mascotas)
**Estado:** PENDIENTE
**Módulo:** django-vet-clinic

## Historia de Usuario

**Como** dueño de mascota
**Quiero** subir y acceder a documentos de mis mascotas
**Para que** tenga todos sus registros en un solo lugar

**Como** veterinario
**Quiero** adjuntar documentos a registros de mascotas
**Para que** tenga documentación médica completa

**Como** dueño de mascota
**Quiero** subir documentos vía chat
**Para que** pueda compartir información fácilmente con la clínica

## Criterios de Aceptación

### Carga de Documentos
- [ ] Subir documentos vía interfaz web
- [ ] Subir documentos vía chat de IA (arrastrar y soltar)
- [ ] Subir vía WhatsApp (reenviar documentos)
- [ ] Soportar formatos comunes (PDF, JPG, PNG, HEIC)
- [ ] Límites de tamaño de archivo con retroalimentación clara
- [ ] Indicador de progreso para archivos grandes
- [ ] Carga masiva de múltiples documentos

### Tipos de Documentos
- [ ] Registros de vacunación
- [ ] Resultados de laboratorio
- [ ] Radiografías e imágenes
- [ ] Registros de recetas
- [ ] Papeles de adopción/compra
- [ ] Certificados de viaje
- [ ] Documentos de seguro
- [ ] Registros de veterinarios anteriores
- [ ] Fotos (lesión, progresión de condición)

### Procesamiento Potenciado por IA
- [ ] Extracción de texto OCR de documentos
- [ ] Auto-categorizar tipo de documento
- [ ] Extraer datos clave (fechas, nombres de vacunas, resultados)
- [ ] Auto-vincular a mascota relevante
- [ ] Identificar y marcar hallazgos importantes
- [ ] Análisis de visión para imágenes médicas

### Organización de Documentos
- [ ] Organizar por mascota
- [ ] Organizar por tipo de documento
- [ ] Organizar por fecha
- [ ] Buscar en todos los documentos
- [ ] Etiquetas y rótulos
- [ ] Marcar/anclar documentos importantes

### Control de Acceso
- [ ] El propietario puede ver documentos de sus mascotas
- [ ] El personal puede ver todos los documentos
- [ ] Compartir documentos con otros veterinarios
- [ ] Enlaces de compartir temporales
- [ ] Descargar archivos originales
- [ ] Versiones amigables para impresión

### Seguridad de Documentos
- [ ] Almacenamiento cifrado
- [ ] Registro de acceso
- [ ] Políticas de retención
- [ ] Eliminación compatible con GDPR
- [ ] Respaldo y recuperación

## Requisitos Técnicos

### Modelos

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

### Herramientas de IA

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

## Ejemplo de Conversaciones con IA

### Carga de Documento vía Chat
```
Dueño: [Sube archivo PDF]

IA: Recibí el documento de Luna. Déjame procesarlo...

    📄 Análisis de Documento Completo

    Tipo: Registro de Vacunación (auto-detectado)
    De: Veterinaria Central, CDMX
    Fecha: 15 de octubre de 2024

    Información Extraída:
    • Vacuna Antirrábica - Expira Oct 2025
    • Vacuna DHPP - Expira Oct 2025
    • Bordetella - Expira Abr 2025

    He agregado esto a los registros de Luna y actualizado
    su calendario de vacunación.

    ¿Te gustaría que configurara recordatorios para las
    fechas de vencimiento próximas?

Dueño: Sí por favor

IA: ¡Hecho! He programado recordatorios:

    • Bordetella: Recordatorio el 15 de marzo de 2025
    • Antirrábica y DHPP: Recordatorio el 15 de septiembre de 2025

    Puedes ver todos los documentos de Luna en su perfil.
```

### Búsqueda de Documentos
```
Dueño: ¿Tienes la radiografía de Luna del año pasado?

IA: Déjame buscar en los documentos de Luna...

    Encontré 2 documentos de radiografías:

    1. 📷 Radiografía de Cadera - 12 de marzo de 2024
       Tomada en Pet-Friendly
       Notas: "Displasia de cadera leve observada"

    2. 📷 Radiografía de Tórax - 5 de enero de 2024
       Tomada en Veterinaria de Emergencia Cancún
       Notas: "Despejado, sin anormalidades"

    ¿Cuál te gustaría ver?

Dueño: La de la cadera

IA: Aquí está la radiografía de cadera de Luna de marzo de 2024:

    [Vista Previa de Imagen]

    Notas del Dr. Pablo de esa visita:
    "Displasia bilateral de cadera leve, grado 1. Recomendar
    suplementos articulares y control de peso. Radiografía
    de seguimiento en 12 meses."

    ¿Te gustaría:
    • Descargar la imagen completa
    • Compartir con otro veterinario
    • Programar la radiografía de seguimiento
```

### Paquete de Documentos para Viaje
```
Dueño: Necesito los registros de Luna para viajar a EE.UU.

IA: Puedo preparar un paquete de documentos de viaje para Luna.

    Para entrada a EE.UU., típicamente necesitas:
    ✓ Vacunación antirrábica vigente (dentro de 12 meses)
    ✓ Certificado de salud (dentro de 10 días de viaje)
    ✓ Documentación de microchip

    Documentos actuales de Luna:
    ✓ Vacuna antirrábica - Válida hasta Oct 2025
    ✗ Certificado de salud - No en archivo
    ✓ Registro de microchip

    ¿Te gustaría que:
    1. Creara un paquete con documentos existentes
    2. Programara una cita para certificado de salud

Dueño: Ambos por favor, viajo el 1 de febrero

IA: He creado un paquete parcial y programado una cita:

    📦 Paquete de Viaje (Parcial)
    • Registro de vacunación antirrábica
    • Registro de microchip

    📅 Cita para Certificado de Salud
    • Fecha: 25 de enero de 2025
    • Hora: 10:00 AM
    • Nota: Debe estar dentro de 10 días de viaje

    Después de la cita, agregaré el certificado de salud
    para completar tu paquete de viaje.

    [Descargar Paquete Actual] [Ver Cita]
```

### Análisis de Visión (Personal)
```
Personal: [Sube foto de condición de piel]

IA: He analizado la imagen de la condición de piel de Max.

    🔍 Análisis de IA:

    Observaciones:
    • Parche circular de pérdida de pelo (~3cm diámetro)
    • Piel roja e irritada en el centro
    • Descamación en los bordes
    • Ubicación: Flanco derecho

    Posibles condiciones (para revisión del veterinario):
    1. Tiña (dermatofitosis) - Alta coincidencia
    2. Infección bacteriana de piel - Coincidencia moderada
    3. Reacción alérgica - Menor coincidencia

    ⚠️ Esta es una evaluación de IA solo para referencia.
    El Dr. Pablo debe confirmar el diagnóstico.

    Pruebas recomendadas:
    • Examen con lámpara de Wood
    • Raspado de piel/cultivo fúngico
    • Si se sospecha tiña: Verificar riesgo zoonótico

    ¿Te gustaría que agregara esto al expediente de Max?
```

## Pipeline de Procesamiento de Archivos

```
Carga → Escaneo de Virus → Almacenar → Generar Miniatura
                          ↓
                    Procesamiento OCR
                          ↓
                    Clasificación IA
                          ↓
                    Extracción de Datos
                          ↓
                    Vincular a Registro de Mascota
                          ↓
                    Listo para Acceso
```

## Definición de Completado

- [ ] Carga de documentos (web, chat, WhatsApp)
- [ ] Validación de tipo de archivo y escaneo de virus
- [ ] Generación de miniaturas
- [ ] Extracción de texto OCR
- [ ] Auto-categorización con IA
- [ ] Extracción de datos estructurados
- [ ] Búsqueda de documentos (texto completo)
- [ ] Control de acceso y registro
- [ ] Generación de enlaces compartidos
- [ ] Paquetes de documentos para exportación
- [ ] Análisis de visión para imágenes
- [ ] Pruebas escritas y pasando (>95% cobertura)

## Dependencias

- S-001: Fundación (almacenamiento de archivos)
- S-002: Chat de IA (carga vía chat)
- S-003: Perfiles de Mascotas (vincular a mascotas)
- S-006: Omnicanal (cargas de WhatsApp)

## Notas

- Considerar AWS S3 para almacenamiento de archivos
- Escaneo de virus con ClamAV
- Opciones de OCR: Tesseract, Google Vision, AWS Textract
- Conversión HEIC para fotos de iPhone
- Considerar límites de tamaño de documento (10MB por defecto)
- Generación de vista previa de PDF con pdf.js o similar

## Proceso de Desarrollo

**Antes de implementar esta historia**, revisar y seguir el **Ciclo TDD de 23 Pasos** en:
- `CLAUDE.md` - Flujo de trabajo de desarrollo global
- `planning/TASK_BREAKDOWN.md` - Tareas específicas para esta historia

Las pruebas deben escribirse antes de la implementación. Se requiere >95% de cobertura.
