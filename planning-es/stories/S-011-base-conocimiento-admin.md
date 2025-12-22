# S-011: Administración de Base de Conocimiento

> **LECTURA OBLIGATORIA:** Antes de la implementación, revisar [ESTANDARES_CODIGO.md](../ESTANDARES_CODIGO.md) y [DECISIONES_ARQUITECTURA.md](../DECISIONES_ARQUITECTURA.md)

**Tipo de Historia:** Historia de Usuario
**Prioridad:** Alta
**Época:** 1 (Fundación)
**Estado:** PENDIENTE
**Módulo:** django-ai-assistant

## Historia de Usuario

**Como** dueño de clínica
**Quiero** gestionar el contenido de la base de conocimiento de la IA
**Para que** la IA proporcione respuestas precisas y personalizadas sobre mi clínica

**Como** veterinario
**Quiero** agregar consejos de cuidado de mascotas e información médica
**Para que** los dueños de mascotas reciban orientación experta de la IA

**Como** administrador
**Quiero** controlar lo que la IA puede y no puede decir
**Para que** las respuestas se alineen con las políticas de la clínica y requisitos legales

## Criterios de Aceptación

### Gestión de Contenido de Base de Conocimiento
- [ ] Crear, editar, eliminar entradas de base de conocimiento
- [ ] Organizar contenido por categoría (servicios, políticas, cuidado de mascotas, FAQs)
- [ ] Soportar formato de texto enriquecido (markdown)
- [ ] Historial de versiones para todos los cambios de contenido
- [ ] Vista previa de cómo la IA usará el contenido
- [ ] Capacidades de importación/exportación masiva

### Categorías de Contenido
- [ ] Información de Clínica (horarios, ubicación, contacto, personal)
- [ ] Servicios (descripciones, precios, duración)
- [ ] Políticas (cancelación, pago, emergencias)
- [ ] Consejos de Cuidado de Mascotas (por especie, condición, tema)
- [ ] Preguntas Frecuentes (preguntas y respuestas comunes)
- [ ] Productos (descripciones, uso, recomendaciones)
- [ ] Condiciones Médicas (síntomas, tratamientos, prevención)

### Contenido Multilingüe
- [ ] Ingresar contenido en idioma principal (Español)
- [ ] La IA auto-traduce a otros idiomas al guardar
- [ ] Revisar y editar traducciones
- [ ] Marcar contenido como revisado por traducción
- [ ] Anulaciones de contenido específicas por idioma

### Configuración de Comportamiento de IA
- [ ] Establecer personalidad y tono de la IA
- [ ] Definir plantillas de respuesta para escenarios comunes
- [ ] Configurar activadores de escalamiento (cuándo involucrar a humano)
- [ ] Establecer restricciones de tema (qué la IA no debe discutir)
- [ ] Definir texto de descargo para consejos médicos
- [ ] Configurar umbrales de confianza

### Flujo de Trabajo de Aprobación de Contenido
- [ ] Borrador → Revisión → Aprobado → Publicado
- [ ] Permisos de edición basados en roles
- [ ] Requerir aprobación para contenido sensible
- [ ] Publicación programada
- [ ] Fechas de expiración para contenido sensible al tiempo

### Analítica y Mejora
- [ ] Rastrear qué contenido se usa más
- [ ] Identificar preguntas que la IA no pudo responder
- [ ] Sugerir brechas de contenido
- [ ] Retroalimentación de usuarios sobre respuestas de IA
- [ ] Pruebas A/B para variaciones de respuesta

## Requisitos Técnicos

### Modelos

```python
class KnowledgeCategory(models.Model):
    """Categories for organizing knowledge base content"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True
    )
    icon = models.CharField(max_length=50, blank=True)  # Icon class
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Knowledge Categories'


class KnowledgeEntry(models.Model):
    """Individual knowledge base entry"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('review', 'In Review'),
        ('approved', 'Approved'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    # Identity
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(KnowledgeCategory, on_delete=models.CASCADE)

    # Content (primary language - Spanish)
    content = models.TextField()  # Markdown supported
    summary = models.TextField(blank=True)  # Short version for quick answers
    keywords = models.JSONField(default=list)  # For matching queries

    # Translations (auto-generated, editable)
    translations = models.JSONField(default=dict)
    # {"en": {"title": "...", "content": "...", "reviewed": true}, ...}

    # Metadata
    content_type = models.CharField(max_length=50)
    # faq, service, policy, pet_care, medical, product, general

    # Targeting
    species = models.JSONField(default=list)  # ["dog", "cat", "all"]
    applies_to = models.JSONField(default=list)  # ["customers", "staff", "all"]

    # Status & Workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    published_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    # Authorship
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='created_entries'
    )
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_entries'
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    # Analytics
    usage_count = models.IntegerField(default=0)
    last_used_at = models.DateTimeField(null=True, blank=True)
    helpfulness_score = models.FloatField(default=0.0)  # From user feedback

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']


class KnowledgeVersion(models.Model):
    """Version history for knowledge entries"""
    entry = models.ForeignKey(KnowledgeEntry, on_delete=models.CASCADE)
    version_number = models.IntegerField()
    title = models.CharField(max_length=200)
    content = models.TextField()
    translations = models.JSONField(default=dict)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    change_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-version_number']
        unique_together = ['entry', 'version_number']


class AIConfiguration(models.Model):
    """AI behavior and personality settings"""
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=False)  # Only one active at a time

    # Personality
    personality_prompt = models.TextField()  # System prompt for AI
    tone = models.CharField(max_length=50)  # friendly, professional, casual
    language_style = models.JSONField(default=dict)
    # {"formality": "informal", "emoji_usage": "minimal", ...}

    # Behavior
    confidence_threshold = models.FloatField(default=0.7)
    # Below this, escalate to human
    max_response_length = models.IntegerField(default=500)
    include_disclaimers = models.BooleanField(default=True)
    medical_disclaimer = models.TextField(blank=True)

    # Restrictions
    restricted_topics = models.JSONField(default=list)
    # ["competitor recommendations", "specific drug dosages", ...]
    escalation_triggers = models.JSONField(default=list)
    # ["angry customer", "legal threat", "emergency", ...]

    # Templates
    greeting_templates = models.JSONField(default=list)
    fallback_responses = models.JSONField(default=list)
    handoff_message = models.TextField(blank=True)

    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class UnansweredQuery(models.Model):
    """Queries the AI couldn't answer - for content gap analysis"""
    query = models.TextField()
    language = models.CharField(max_length=10)
    session_id = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    # AI's attempt
    attempted_response = models.TextField(blank=True)
    confidence_score = models.FloatField()

    # Resolution
    is_resolved = models.BooleanField(default=False)
    resolution_entry = models.ForeignKey(
        KnowledgeEntry, on_delete=models.SET_NULL, null=True, blank=True
    )
    resolution_notes = models.TextField(blank=True)

    # Frequency
    occurrence_count = models.IntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-occurrence_count', '-created_at']


class ContentFeedback(models.Model):
    """User feedback on AI responses"""
    RATING_CHOICES = [
        ('helpful', 'Helpful'),
        ('not_helpful', 'Not Helpful'),
        ('incorrect', 'Incorrect'),
        ('incomplete', 'Incomplete'),
    ]

    knowledge_entry = models.ForeignKey(
        KnowledgeEntry, on_delete=models.CASCADE, null=True, blank=True
    )
    query = models.TextField()
    response = models.TextField()
    rating = models.CharField(max_length=20, choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    # Staff review
    reviewed = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_feedback'
    )
    action_taken = models.TextField(blank=True)
```

### Herramientas de IA (Admin)

```python
KNOWLEDGE_ADMIN_TOOLS = [
    {
        "name": "search_knowledge_base",
        "description": "Search the knowledge base for content",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "category": {"type": "string"},
                "content_type": {"type": "string"},
                "status": {"type": "string"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "create_knowledge_entry",
        "description": "Create a new knowledge base entry",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "category": {"type": "string"},
                "content": {"type": "string"},
                "content_type": {"type": "string"},
                "keywords": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["title", "category", "content"]
        }
    },
    {
        "name": "update_knowledge_entry",
        "description": "Update an existing knowledge base entry",
        "parameters": {
            "type": "object",
            "properties": {
                "entry_id": {"type": "integer"},
                "title": {"type": "string"},
                "content": {"type": "string"},
                "status": {"type": "string"}
            },
            "required": ["entry_id"]
        }
    },
    {
        "name": "get_unanswered_queries",
        "description": "Get queries the AI couldn't answer",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 10},
                "min_occurrences": {"type": "integer", "default": 1}
            }
        }
    },
    {
        "name": "get_content_analytics",
        "description": "Get analytics on knowledge base usage",
        "parameters": {
            "type": "object",
            "properties": {
                "date_range": {"type": "string"},
                "category": {"type": "string"}
            }
        }
    },
    {
        "name": "preview_ai_response",
        "description": "Preview how AI would respond to a query",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "language": {"type": "string", "default": "es"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "translate_entry",
        "description": "Trigger translation of a knowledge entry",
        "parameters": {
            "type": "object",
            "properties": {
                "entry_id": {"type": "integer"},
                "target_languages": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["entry_id"]
        }
    }
]
```

## Ejemplo de Conversaciones con IA

### Agregar Contenido (Admin)
```
Dr. Pablo: Agregar información sobre nuestro nuevo servicio de terapia láser

IA: Te ayudaré a crear una entrada de base de conocimiento para terapia láser.

    Por favor proporciona la siguiente información:

    1. Descripción del Servicio:
       ¿Qué es la terapia láser y qué condiciones trata?

    2. Precios:
       ¿Costo por sesión o paquetes?

    3. Duración:
       ¿Cuánto dura cada sesión?

    4. Especies:
       ¿Disponible para perros, gatos o ambos?

    5. ¿Alguna contraindicación o nota especial?

Dr. Pablo: Es terapia láser fría para dolor e inflamación.
           $500 por sesión, 15-20 minutos. Perros y gatos.
           No para animales embarazadas o con cáncer.

IA: He creado la entrada de base de conocimiento:

    Título: Terapia Láser Fría
    Categoría: Servicios
    Estado: Borrador

    Vista Previa:
    "La terapia láser fría es un tratamiento no invasivo
    para el dolor y la inflamación. Cada sesión dura
    15-20 minutos y cuesta $500 MXN. Disponible para
    perros y gatos. No recomendado para animales
    embarazadas o con cáncer."

    También he auto-generado traducciones para:
    ✓ Inglés ✓ Alemán ✓ Francés ✓ Italiano

    ¿Te gustaría:
    1. Editar el contenido
    2. Revisar traducciones
    3. Publicar inmediatamente
    4. Guardar como borrador
```

### Análisis de Brechas de Contenido
```
Dr. Pablo: ¿Qué preguntas están haciendo los clientes que no podemos responder?

IA: Aquí están las consultas sin respuesta de los últimos 30 días:

    | Consulta | Ocurrencias | Brecha de Categoría |
    |----------|-------------|---------------------|
    | "¿Tienen hospedaje nocturno?" | 12 | Servicios |
    | "¿Qué vacunas necesita mi cachorro?" | 8 | Cuidado de Mascotas |
    | "¿Aceptan seguro de mascotas?" | 7 | Políticas |
    | "¿Cuánto cuesta esterilizar un gato?" | 6 | Precios |
    | "¿Puedo traer mi ave?" | 4 | Servicios |

    Recomendación:
    Crear entradas para las 3 principales abordaría el 57%
    de las consultas sin respuesta.

    ¿Te gustaría que redactara contenido para alguna de estas?
```

### Configurar Comportamiento de IA
```
Dr. Pablo: No quiero que la IA recomiende dosificaciones específicas

IA: Agregaré eso a las restricciones de IA. Actualmente la IA está
    configurada para:

    Temas Restringidos:
    ✓ Recomendaciones de competidores
    ✓ Dosificaciones específicas de medicamentos (NUEVO)
    ✓ Diagnósticos definitivos
    ✓ Asesoramiento legal/responsabilidad

    Cuando le pregunten sobre dosificaciones, la IA responderá:
    "Para dosificaciones específicas de medicamentos, por favor consulta
    directamente con Dr. Pablo durante tu cita. La dosificación depende
    del peso de tu mascota, condición y otros medicamentos."

    ¿Es esta la respuesta que te gustaría, o prefieres
    una redacción diferente?
```

## Interfaz de Administración

### Panel de Base de Conocimiento
- Contenido por categoría (vista de árbol)
- Estadísticas rápidas (entradas totales, publicadas, borradores)
- Línea de tiempo de cambios recientes
- Alertas de brechas de contenido
- Estado de traducción

### Editor de Entradas
- Editor de markdown enriquecido
- Vista de traducción lado a lado
- Panel de vista previa (cómo la IA lo usa)
- Historial de versiones
- Controles de publicación

### Vista de Analítica
- Contenido más usado
- Calificaciones de utilidad
- Tendencias de consultas sin respuesta
- Análisis de consultas de búsqueda
- Métricas de tiempo de respuesta

## Definición de Completado

- [ ] CRUD de entrada de conocimiento con categorías
- [ ] Historial de versiones para todos los cambios
- [ ] Auto-traducción al guardar
- [ ] Flujo de trabajo de revisión de traducción
- [ ] Panel de configuración de IA
- [ ] Seguimiento de consultas sin respuesta
- [ ] Recolección de retroalimentación de contenido
- [ ] Panel de analítica de uso
- [ ] Importación/exportación masiva (CSV, JSON)
- [ ] Vista previa de respuestas de IA
- [ ] Pruebas escritas y pasando (>95% cobertura)

## Dependencias

- S-001: Fundación (autenticación, multilingüe)
- S-002: Interfaz de Chat de IA (integración)

## Notas

- Considerar usar embeddings vectoriales para búsqueda semántica
- Puede querer integrar con fuentes externas de conocimiento
- Moderación de contenido para preguntas enviadas por usuarios
- Recordatorios regulares de revisión de contenido

## Proceso de Desarrollo

**Antes de implementar esta historia**, revisar y seguir el **Ciclo TDD de 23 Pasos** en:
- `CLAUDE.md` - Flujo de trabajo de desarrollo global
- `planning/TASK_BREAKDOWN.md` - Tareas específicas para esta historia

Las pruebas deben escribirse antes de la implementación. Se requiere >95% de cobertura.
