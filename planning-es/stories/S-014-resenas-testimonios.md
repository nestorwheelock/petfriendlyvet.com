# S-014: Reseñas y Testimonios

> **LECTURA OBLIGATORIA:** Antes de la implementación, revisar [ESTANDARES_CODIGO.md](../ESTANDARES_CODIGO.md) y [DECISIONES_ARQUITECTURA.md](../DECISIONES_ARQUITECTURA.md)

**Tipo de Historia:** Historia de Usuario
**Prioridad:** Media
**Época:** 5 (con CRM)
**Estado:** PENDIENTE
**Módulo:** django-crm-lite

## Historia de Usuario

**Como** dueño de mascota
**Quiero** compartir mi experiencia con la clínica
**Para que** otros puedan conocer la calidad del cuidado

**Como** dueño de clínica
**Quiero** recopilar y mostrar testimonios de clientes
**Para que** pueda generar confianza con clientes potenciales

**Como** cliente potencial
**Quiero** leer reseñas de otros dueños de mascotas
**Para que** pueda tomar una decisión informada al elegir esta clínica

## Criterios de Aceptación

### Recopilación de Reseñas
- [ ] Solicitar reseñas después de las citas (automatizado)
- [ ] Sistema de calificación simple (1-5 estrellas)
- [ ] Reseña escrita con foto opcional
- [ ] Reseñar aspectos específicos (servicio, personal, instalaciones, valor)
- [ ] Reseñas específicas de mascotas (vincular con mascota y servicio)
- [ ] Soporte de reseñas multiidioma

### Visualización de Reseñas
- [ ] Mostrar reseñas en el sitio web
- [ ] Filtrar por calificación, fecha, tipo de servicio
- [ ] Reseñas destacadas/ancladas
- [ ] Galería de fotos de reseñas
- [ ] Mostrar calificación promedio
- [ ] Conteo y desglose de reseñas

### Integración con Google
- [ ] Enviar reseñas a Google Business Profile
- [ ] Importar reseñas de Google
- [ ] Responder a reseñas de Google desde el panel
- [ ] Monitorear nuevas reseñas de Google

### Gestión de Reseñas
- [ ] Aprobar reseñas antes de publicar
- [ ] Marcar contenido inapropiado
- [ ] Responder a reseñas públicamente
- [ ] Seguimiento privado para reseñas negativas
- [ ] Análisis y tendencias de reseñas

### Prueba Social
- [ ] Widgets de testimonios para el sitio web
- [ ] Compartir reseñas en redes sociales
- [ ] Insignias/certificados de reseñas
- [ ] Insignia de "Cliente verificado"

## Requisitos Técnicos

### Modelos

```python
class ReviewRequest(models.Model):
    """Seguimiento de solicitudes de reseñas automatizadas"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('completed', 'Completed'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    pet = models.ForeignKey('vet_clinic.Pet', on_delete=models.CASCADE)
    appointment = models.ForeignKey(
        'appointments.Appointment', on_delete=models.CASCADE
    )

    # Request tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    token = models.CharField(max_length=64, unique=True)

    # Timing
    send_after = models.DateTimeField()  # e.g., 24 hours after appointment
    sent_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()

    # Result
    review = models.ForeignKey(
        'Review', on_delete=models.SET_NULL, null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)


class Review(models.Model):
    """Reseña del cliente"""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('hidden', 'Hidden'),
    ]

    # Author
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    pet = models.ForeignKey(
        'vet_clinic.Pet', on_delete=models.SET_NULL, null=True, blank=True
    )
    is_verified = models.BooleanField(default=False)  # Verified client

    # Rating
    overall_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    service_rating = models.IntegerField(null=True, blank=True)
    staff_rating = models.IntegerField(null=True, blank=True)
    facility_rating = models.IntegerField(null=True, blank=True)
    value_rating = models.IntegerField(null=True, blank=True)

    # Content
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    language = models.CharField(max_length=10, default='es')

    # Context
    service_type = models.CharField(max_length=100, blank=True)
    # consultation, vaccination, surgery, grooming, etc.
    visit_date = models.DateField(null=True, blank=True)

    # Media
    photos = models.JSONField(default=list)  # List of photo URLs

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    moderated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='moderated_reviews'
    )
    moderated_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    # Display
    is_featured = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)

    # Engagement
    helpful_count = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']


class ReviewPhoto(models.Model):
    """Fotos adjuntas a reseñas"""
    review = models.ForeignKey(Review, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='reviews/photos/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class ReviewResponse(models.Model):
    """Respuesta de la clínica a una reseña"""
    review = models.OneToOneField(Review, on_delete=models.CASCADE)
    content = models.TextField()
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class GoogleReview(models.Model):
    """Reseñas de Google Business importadas"""
    google_review_id = models.CharField(max_length=100, unique=True)
    author_name = models.CharField(max_length=200)
    author_photo_url = models.URLField(blank=True)
    rating = models.IntegerField()
    text = models.TextField(blank=True)
    language = models.CharField(max_length=10)
    time = models.DateTimeField()

    # Response
    reply_text = models.TextField(blank=True)
    reply_time = models.DateTimeField(null=True, blank=True)
    reply_synced = models.BooleanField(default=False)

    # Matching
    matched_owner = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    # Sync tracking
    last_synced_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ReviewStats(models.Model):
    """Estadísticas agregadas de reseñas (en caché)"""
    date = models.DateField(unique=True)

    total_reviews = models.IntegerField(default=0)
    average_rating = models.FloatField(default=0)

    # By rating
    rating_5_count = models.IntegerField(default=0)
    rating_4_count = models.IntegerField(default=0)
    rating_3_count = models.IntegerField(default=0)
    rating_2_count = models.IntegerField(default=0)
    rating_1_count = models.IntegerField(default=0)

    # By aspect
    avg_service_rating = models.FloatField(null=True)
    avg_staff_rating = models.FloatField(null=True)
    avg_facility_rating = models.FloatField(null=True)
    avg_value_rating = models.FloatField(null=True)

    # By service type
    ratings_by_service = models.JSONField(default=dict)

    updated_at = models.DateTimeField(auto_now=True)


class TestimonialWidget(models.Model):
    """Widgets de visualización de testimonios configurables"""
    name = models.CharField(max_length=100)
    widget_type = models.CharField(max_length=50)
    # carousel, grid, single, sidebar

    # Content selection
    filter_min_rating = models.IntegerField(default=4)
    filter_verified_only = models.BooleanField(default=False)
    filter_with_photos = models.BooleanField(default=False)
    filter_service_types = models.JSONField(default=list)
    max_reviews = models.IntegerField(default=6)

    # Display options
    show_photos = models.BooleanField(default=True)
    show_pet_name = models.BooleanField(default=True)
    show_service_type = models.BooleanField(default=True)
    show_date = models.BooleanField(default=True)
    auto_rotate = models.BooleanField(default=True)
    rotation_speed_ms = models.IntegerField(default=5000)

    # Styling
    custom_css = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### Herramientas de IA

```python
REVIEW_TOOLS = [
    {
        "name": "get_review_stats",
        "description": "Obtener estadísticas de reseñas y resumen de calificaciones",
        "parameters": {
            "type": "object",
            "properties": {
                "date_range": {"type": "string"},
                "service_type": {"type": "string"}
            }
        }
    },
    {
        "name": "get_recent_reviews",
        "description": "Obtener reseñas recientes",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 10},
                "min_rating": {"type": "integer"},
                "status": {"type": "string"}
            }
        }
    },
    {
        "name": "respond_to_review",
        "description": "Responder a una reseña de cliente",
        "parameters": {
            "type": "object",
            "properties": {
                "review_id": {"type": "integer"},
                "response": {"type": "string"},
                "is_public": {"type": "boolean", "default": True}
            },
            "required": ["review_id", "response"]
        }
    },
    {
        "name": "moderate_review",
        "description": "Aprobar o rechazar una reseña pendiente",
        "parameters": {
            "type": "object",
            "properties": {
                "review_id": {"type": "integer"},
                "action": {"type": "string", "enum": ["approve", "reject", "hide"]},
                "reason": {"type": "string"}
            },
            "required": ["review_id", "action"]
        }
    },
    {
        "name": "feature_review",
        "description": "Marcar una reseña como destacada",
        "parameters": {
            "type": "object",
            "properties": {
                "review_id": {"type": "integer"},
                "featured": {"type": "boolean"}
            },
            "required": ["review_id", "featured"]
        }
    },
    {
        "name": "sync_google_reviews",
        "description": "Sincronizar reseñas de Google Business Profile",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "analyze_review_sentiment",
        "description": "Analizar tendencias de sentimiento en reseñas",
        "parameters": {
            "type": "object",
            "properties": {
                "date_range": {"type": "string"}
            }
        }
    }
]
```

## Ejemplos de Conversaciones con IA

### Solicitud de Reseña (Cliente)
```
IA (WhatsApp, 24 hrs después de la cita):
    Hola Maria! 🐕

    Gracias por traer a Luna ayer para su
    vacunación. ¡Esperamos que todo haya ido bien!

    ¿Te importaría compartir tu experiencia?
    Tu retroalimentación ayuda a otros dueños de mascotas
    y nos ayuda a mejorar nuestro servicio.

    [Dejar una Reseña ⭐] [Ahora no]

Dueño: [Hace clic en Dejar una Reseña]

IA: ¡Gracias por tomarte el tiempo!

    ¿Cómo calificarías tu experiencia?
    ⭐⭐⭐⭐⭐

Dueño: ⭐⭐⭐⭐⭐

IA: ¡Maravilloso! ¡5 estrellas!

    ¿Te gustaría añadir algunas palabras sobre tu
    experiencia? (Opcional pero muy apreciado!)

Dueño: El Dr. Pablo fue muy gentil con Luna. Ella normalmente
       odia al veterinario pero estuvo tranquila todo el tiempo.
       La clínica está limpia y el personal es muy amable.

IA: ¡Muchas gracias por tus amables palabras, Maria!

    📸 ¿Te gustaría añadir una foto de Luna?
    (Las fotos ayudan a otros dueños a conectar con tu historia)

    [Añadir Foto] [Omitir]

Dueño: [Añade foto]

IA: ¡Tu reseña ha sido enviada!

    ⭐⭐⭐⭐⭐
    "El Dr. Pablo fue muy gentil con Luna..."

    ¡Gracias por ser un cliente valioso de Pet-Friendly!
    Luna tiene suerte de tener un dueño tan cariñoso. 🐕💚
```

### Gestión de Reseñas (Administrador)
```
Dr. Pablo: Muéstrame las reseñas recientes

IA: Aquí están tus reseñas de los últimos 30 días:

    📊 Resumen:
    • Total: 12 reseñas
    • Promedio: 4.8 ⭐
    • Pendientes de moderación: 2

    ⭐⭐⭐⭐⭐ (8 reseñas)
    ⭐⭐⭐⭐ (3 reseñas)
    ⭐⭐⭐ (1 reseña)

    Reseñas Recientes:

    1. Maria G. - 5⭐ - Ayer
       "El Dr. Pablo fue muy gentil con Luna..."
       Estado: Aprobada ✓

    2. Carlos M. - 5⭐ - Hace 2 días
       "¡Mejor veterinario en Puerto Morelos!"
       Estado: Pendiente ⏳

    3. Susan T. - 3⭐ - Hace 5 días
       "Buen servicio pero tuve que esperar 30 minutos"
       Estado: Aprobada ✓ | Sin respuesta aún

    ¿Te gustaría:
    1. Aprobar reseñas pendientes
    2. Responder a una reseña
    3. Ver análisis detallado

Dr. Pablo: Responder a la reseña de Susan

IA: Aquí está la reseña completa de Susan:

    ⭐⭐⭐ (18 de enero, 2026)
    Mascota: Whiskers (gato)
    Servicio: Revisión

    "Buen servicio pero tuve que esperar 30 minutos después
    de la hora de mi cita. El Dr. Pablo fue excelente una vez
    que entramos, pero la espera fue frustrante con
    un gato nervioso."

    Respuesta sugerida:
    "Estimada Susan, gracias por tu retroalimentación y
    disculpas sinceras por la espera. Tuvimos una
    emergencia ese día que causó retrasos. Estamos
    trabajando en mejor comunicación cuando esto sucede.
    ¡Esperamos que Whiskers esté bien!"

    ¿Te gustaría:
    1. Usar esta respuesta
    2. Editar y personalizar
    3. Escribir la tuya propia
```

### Análisis de Reseñas
```
Dr. Pablo: ¿Cómo nos va con las reseñas?

IA: 📊 Análisis de Reseñas (Últimos 90 Días)

    Rendimiento General:
    ⭐ 4.8 promedio (de 45 reseñas)
    📈 Aumento de 4.6 el trimestre pasado

    Desglose de Calificaciones:
    ⭐⭐⭐⭐⭐  ████████████  34 (76%)
    ⭐⭐⭐⭐    ████          8 (18%)
    ⭐⭐⭐      █             2 (4%)
    ⭐⭐        -             1 (2%)
    ⭐         -             0 (0%)

    Calificaciones por Aspecto:
    • Amabilidad del personal: 4.9 ⭐
    • Atención veterinaria: 4.8 ⭐
    • Limpieza de instalaciones: 4.7 ⭐
    • Relación calidad-precio: 4.5 ⭐
    • Tiempo de espera: 4.2 ⭐ ⚠️

    Palabras Clave Más Mencionadas:
    ✓ "gentil" (12 menciones)
    ✓ "profesional" (10 menciones)
    ✓ "amable" (9 menciones)
    ⚠️ "esperar" (5 menciones)

    Insight: El tiempo de espera es tu aspecto con menor calificación.
    Considera mejorar la programación o comunicación
    sobre retrasos.

    Reseñas de Google:
    • 4.9 ⭐ en Google (66 reseñas)
    • Última sincronización: Hoy a las 9:00 AM
    • 2 nuevas reseñas de Google para responder
```

## Automatización de Solicitud de Reseñas

### Reglas de Activación
```python
REVIEW_REQUEST_RULES = {
    'vaccination': {
        'delay_hours': 24,
        'min_days_since_last_request': 90,
    },
    'consultation': {
        'delay_hours': 48,
        'min_days_since_last_request': 60,
    },
    'surgery': {
        'delay_hours': 72,  # Wait for recovery
        'min_days_since_last_request': 180,
    },
    'emergency': {
        'delay_hours': 72,
        'min_days_since_last_request': 90,
    },
}
```

## Definición de Hecho

- [ ] Automatización de solicitud de reseñas
- [ ] Flujo de envío de reseñas
- [ ] Calificaciones de múltiples aspectos
- [ ] Subida de fotos con reseñas
- [ ] Cola de moderación de reseñas
- [ ] Respuestas públicas
- [ ] Integración con Google Business
- [ ] Widgets de reseñas para sitio web
- [ ] Panel de análisis
- [ ] Análisis de sentimiento
- [ ] Pruebas escritas y aprobadas (>95% cobertura)

## Dependencias

- S-004: Citas (activar reseñas)
- S-006: Omnicanal (enviar solicitudes)
- S-007: CRM (perfiles de dueños)

## Notas

- La API de Google Business requiere verificación
- Considerar incentivos para reseñas (con cuidado - contra TOS de Google)
- Responder a reseñas negativas rápidamente
- Destacar reseñas diversas (diferentes mascotas, servicios)
- Considerar testimonios en video (futuro)

## Proceso de Desarrollo

**Antes de implementar esta historia**, revisar y seguir el **Ciclo TDD de 23 Pasos** en:
- `CLAUDE.md` - Flujo de trabajo de desarrollo global
- `planning/TASK_BREAKDOWN.md` - Tareas específicas para esta historia

Las pruebas deben escribirse antes de la implementación. Se requiere >95% de cobertura.
