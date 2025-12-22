# S-009: Inteligencia Competitiva

> **LECTURA OBLIGATORIA:** Antes de la implementación, revisar [ESTANDARES_CODIGO.md](../ESTANDARES_CODIGO.md) y [DECISIONES_ARQUITECTURA.md](../DECISIONES_ARQUITECTURA.md)

**Tipo de Historia:** Historia de Usuario
**Prioridad:** Baja
**Época:** 5 (junto con CRM)
**Estado:** PENDIENTE
**Módulo:** django-competitive-intel

## Historia de Usuario

**Como** dueño de clínica
**Quiero** monitorear las actividades, precios y presencia en el mercado de mis competidores
**Para que** pueda tomar decisiones de negocio informadas y mantener ventaja competitiva

**Como** dueño de clínica
**Quiero** saber cuando los competidores visitan mi sitio web
**Para que** pueda entender su interés en mi negocio y ajustar la estrategia en consecuencia

## Criterios de Aceptación

### Perfiles de Competidores
- [ ] Crear y gestionar perfiles de competidores
- [ ] Almacenar detalles de competidores (nombre, dirección, teléfono, horarios, servicios)
- [ ] Coordenadas GPS para visualización en mapa
- [ ] Vincular a perfiles de redes sociales
- [ ] Campo de notas y observaciones
- [ ] Marca de tiempo de última actualización

### Mapa de Competidores
- [ ] Mapa interactivo mostrando todos los competidores
- [ ] Ubicación de Pet-Friendly destacada diferentemente
- [ ] Clic en marcador para ver detalles del competidor
- [ ] Cálculo de distancia desde Pet-Friendly
- [ ] Visualización de área de servicio (opcional)

### Seguimiento de Precios
- [ ] Rastrear precios de competidores para servicios
- [ ] Datos históricos de precios con marcas de tiempo
- [ ] Gráficos de comparación de precios
- [ ] Alerta cuando un competidor cambia precios
- [ ] Exportar reportes de comparación de precios

### Rastreador de Publicidad
- [ ] Monitorear anuncios de competidores en Facebook/Instagram
- [ ] Rastrear presencia en Google Ads
- [ ] Registrar campañas publicitarias observadas
- [ ] Almacenamiento de capturas de pantalla/evidencia
- [ ] Estimaciones de gasto (si disponibles)

### Inteligencia de Visitantes del Sitio Web
- [ ] Rastrear direcciones IP que visitan el sitio web de Pet-Friendly
- [ ] Identificar IPs conocidas de competidores
- [ ] Registrar patrones de visita (páginas, duración, frecuencia)
- [ ] Alertar cuando un competidor visita
- [ ] Análisis geográfico de visitantes
- [ ] Implementación compatible con privacidad

### Panel e Informes
- [ ] Panel de inteligencia competitiva
- [ ] Insights y recomendaciones generados por IA
- [ ] Reportes de resumen semanal/mensual
- [ ] Análisis de tendencias
- [ ] Recomendaciones accionables

## Requisitos Técnicos

### Modelos

```python
# Competitor Profiles
class Competitor(models.Model):
    """Competitor business profile"""
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    address = models.TextField()
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)

    # Social media
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    google_maps_url = models.URLField(blank=True)

    # Business details
    hours = models.JSONField(default=dict)  # {mon: "9-5", tue: "9-5", ...}
    services = models.JSONField(default=list)  # ["consultations", "surgery", ...]

    # Metadata
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Known IP addresses for visitor tracking
    known_ips = models.JSONField(default=list)

    class Meta:
        ordering = ['name']


class CompetitorPricing(models.Model):
    """Track competitor service pricing over time"""
    competitor = models.ForeignKey(Competitor, on_delete=models.CASCADE)
    service_name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='MXN')
    source = models.CharField(max_length=100)  # "phone call", "website", "visit"
    observed_at = models.DateTimeField()
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-observed_at']


class CompetitorAd(models.Model):
    """Track competitor advertising campaigns"""
    competitor = models.ForeignKey(Competitor, on_delete=models.CASCADE)
    platform = models.CharField(max_length=50)  # facebook, instagram, google
    ad_type = models.CharField(max_length=50)  # image, video, carousel, search
    content = models.TextField(blank=True)  # Ad copy/description
    screenshot = models.ImageField(upload_to='competitor_ads/', null=True)
    landing_url = models.URLField(blank=True)
    estimated_spend = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    first_seen = models.DateTimeField()
    last_seen = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-first_seen']


# Website Visitor Intelligence
class WebsiteVisitor(models.Model):
    """Track website visitors with IP intelligence"""
    ip_address = models.GenericIPAddressField()

    # Geolocation (from IP lookup)
    country = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True)
    isp = models.CharField(max_length=200, blank=True)
    organization = models.CharField(max_length=200, blank=True)

    # Classification
    is_competitor = models.BooleanField(default=False)
    competitor = models.ForeignKey(
        Competitor, on_delete=models.SET_NULL, null=True, blank=True
    )
    is_bot = models.BooleanField(default=False)

    # Aggregated stats
    first_visit = models.DateTimeField()
    last_visit = models.DateTimeField()
    total_visits = models.IntegerField(default=1)
    total_pageviews = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_visit']


class PageView(models.Model):
    """Individual page view tracking"""
    visitor = models.ForeignKey(WebsiteVisitor, on_delete=models.CASCADE)
    path = models.CharField(max_length=500)
    referrer = models.URLField(blank=True)
    user_agent = models.TextField(blank=True)

    # Session data
    session_id = models.CharField(max_length=100, blank=True)
    duration_seconds = models.IntegerField(null=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']


class CompetitorAlert(models.Model):
    """Alerts for competitive intelligence events"""
    ALERT_TYPES = [
        ('competitor_visit', 'Competitor Website Visit'),
        ('price_change', 'Price Change Detected'),
        ('new_ad', 'New Advertisement'),
        ('social_activity', 'Social Media Activity'),
    ]

    alert_type = models.CharField(max_length=50, choices=ALERT_TYPES)
    competitor = models.ForeignKey(
        Competitor, on_delete=models.CASCADE, null=True, blank=True
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    severity = models.CharField(max_length=20, default='info')  # info, warning, important

    # Related objects
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    object_id = models.PositiveIntegerField(null=True)
    related_object = GenericForeignKey('content_type', 'object_id')

    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True)
    read_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class CompetitiveInsight(models.Model):
    """AI-generated competitive insights"""
    insight_type = models.CharField(max_length=50)  # pricing, advertising, traffic, opportunity
    title = models.CharField(max_length=200)
    summary = models.TextField()
    detailed_analysis = models.TextField()
    recommendations = models.JSONField(default=list)  # List of action items

    # Supporting data
    data_sources = models.JSONField(default=list)  # What data was analyzed
    confidence_score = models.FloatField(default=0.0)  # 0.0 to 1.0

    # Validity
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField(null=True)
    is_actionable = models.BooleanField(default=True)

    # Tracking
    is_dismissed = models.BooleanField(default=False)
    dismissed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    dismissed_at = models.DateTimeField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
```

### Herramientas de IA

```python
COMPETITIVE_INTEL_TOOLS = [
    {
        "name": "get_competitor_map",
        "description": "Get competitor locations for map display",
        "parameters": {
            "type": "object",
            "properties": {
                "include_inactive": {"type": "boolean", "default": False}
            }
        }
    },
    {
        "name": "get_competitor_details",
        "description": "Get detailed information about a competitor",
        "parameters": {
            "type": "object",
            "properties": {
                "competitor_id": {"type": "integer"}
            },
            "required": ["competitor_id"]
        }
    },
    {
        "name": "compare_pricing",
        "description": "Compare pricing between Pet-Friendly and competitors",
        "parameters": {
            "type": "object",
            "properties": {
                "service_name": {"type": "string"},
                "competitor_ids": {"type": "array", "items": {"type": "integer"}}
            }
        }
    },
    {
        "name": "get_competitor_visits",
        "description": "Get recent website visits from competitor IPs",
        "parameters": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "default": 30},
                "competitor_id": {"type": "integer"}
            }
        }
    },
    {
        "name": "get_competitive_insights",
        "description": "Get AI-generated competitive insights",
        "parameters": {
            "type": "object",
            "properties": {
                "insight_type": {
                    "type": "string",
                    "enum": ["pricing", "advertising", "traffic", "opportunity", "all"]
                },
                "limit": {"type": "integer", "default": 5}
            }
        }
    },
    {
        "name": "log_competitor_pricing",
        "description": "Log a competitor's pricing information",
        "parameters": {
            "type": "object",
            "properties": {
                "competitor_id": {"type": "integer"},
                "service_name": {"type": "string"},
                "price": {"type": "number"},
                "source": {"type": "string"}
            },
            "required": ["competitor_id", "service_name", "price", "source"]
        }
    },
    {
        "name": "log_competitor_ad",
        "description": "Log a competitor's advertisement",
        "parameters": {
            "type": "object",
            "properties": {
                "competitor_id": {"type": "integer"},
                "platform": {"type": "string", "enum": ["facebook", "instagram", "google"]},
                "ad_type": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["competitor_id", "platform"]
        }
    },
    {
        "name": "generate_competitive_report",
        "description": "Generate a competitive analysis report",
        "parameters": {
            "type": "object",
            "properties": {
                "report_type": {
                    "type": "string",
                    "enum": ["weekly_summary", "pricing_analysis", "market_position", "full_report"]
                },
                "format": {"type": "string", "enum": ["pdf", "html", "json"]}
            },
            "required": ["report_type"]
        }
    }
]
```

## Ejemplo de Conversaciones con IA

### Alerta de Visita de Competidor
```
IA: Alerta: Visita de competidor detectada en sitio web

    Un visitante desde la dirección IP conocida de Fauna Silvestre
    visitó tu sitio web hoy.

    Detalles de la Visita:
    - Hora: 2:34 PM
    - Páginas Vistas: Servicios, Precios, Sobre Nosotros
    - Duración: 4 minutos 23 segundos
    - Esta es su 3ª visita este mes

    Esto podría indicar que están monitoreando tus servicios
    y precios. Considera esto al planear promociones.

Dr. Pablo: ¿Qué páginas miran más?

IA: Basado en 8 visitas de Fauna Silvestre en los últimos 3 meses:

    Páginas Más Vistas:
    1. Página de Servicios (8 visitas, 100%)
    2. Precios/Tarifas (6 visitas, 75%)
    3. Sobre Nosotros (4 visitas, 50%)
    4. Productos de Tienda (2 visitas, 25%)

    Patrón: Revisan consistentemente tus servicios y
    precios, sugiriendo que te usan como referencia.

    Recomendación: Pueden estar ajustando sus ofertas
    para competir. Considera destacar tus servicios únicos
    (reserva con IA, soporte 24h) que no pueden copiar fácilmente.
```

### Comparación de Precios
```
Dr. Pablo: ¿Cómo se comparan mis precios con la competencia?

IA: Aquí está tu comparación de precios para servicios comunes:

    Servicio          | Pet-Friendly | Fauna S. | Miramar
    ------------------+--------------+----------+---------
    Consulta          | $350 MXN     | $400 MXN | $300 MXN
    Vacunación        | $250 MXN     | $280 MXN | $220 MXN
    Limpieza Dental   | $1,200 MXN   | $1,500 MXN | N/A
    Esterilización (gato) | $800 MXN | $900 MXN | $750 MXN

    Análisis:
    - Tienes precios competitivos en el medio
    - Fauna Silvestre tiene precios premium
    - Miramar se posiciona como económico

    Tu reserva con IA y sitio web moderno justifican un
    posicionamiento premium. Considera enfatizar el valor de conveniencia.
```

## Privacidad y Cumplimiento

### Cumplimiento de Rastreo de IP
- Mostrar política de privacidad clara en el sitio web
- Direcciones IP almacenadas por interés comercial legítimo
- Sin identificación personal sin consentimiento
- Política de retención de datos (90 días por defecto)
- Manejo de datos compatible con GDPR
- Opción para excluirse del rastreo (consentimiento de cookies)

### Directrices Éticas
- Solo rastrear información públicamente disponible
- Sin acceso no autorizado a sistemas de competidores
- Sin inteligencia de reclutamiento de empleados
- Transparencia sobre monitoreo competitivo
- Enfoque en mejorar servicios propios, no sabotaje

## Estructura del Paquete

```
django-competitive-intel/
├── competitive_intel/
│   ├── __init__.py
│   ├── models.py           # Competitor, Pricing, Ads, Visitors
│   ├── admin.py            # Admin interface
│   ├── views.py            # Dashboard, map, reports
│   ├── api/
│   │   ├── __init__.py
│   │   ├── serializers.py
│   │   └── views.py        # REST API
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ip_lookup.py    # IP geolocation
│   │   ├── visitor_tracking.py
│   │   ├── insights.py     # AI insight generation
│   │   └── reports.py      # Report generation
│   ├── middleware.py       # Visitor tracking middleware
│   ├── signals.py          # Alert generation
│   ├── templates/
│   │   └── competitive_intel/
│   │       ├── dashboard.html
│   │       ├── map.html
│   │       ├── competitor_detail.html
│   │       └── reports/
│   ├── static/
│   │   └── competitive_intel/
│   │       ├── js/
│   │       │   └── map.js
│   │       └── css/
│   └── management/
│       └── commands/
│           ├── import_competitors.py
│           └── generate_insights.py
├── tests/
├── setup.py
├── pyproject.toml
└── README.md
```

## Definición de Completado

- [ ] Modelo de competidor con operaciones CRUD
- [ ] Mapa interactivo de competidores (Leaflet.js)
- [ ] Seguimiento de precios con historial
- [ ] Rastreador de publicidad con capturas de pantalla
- [ ] Middleware de rastreo de visitantes por IP
- [ ] Identificación de IP de competidores
- [ ] Sistema de alertas para visitas de competidores
- [ ] Generación de insights con IA
- [ ] Panel con todas las métricas
- [ ] Implementación compatible con privacidad
- [ ] Exportar reportes (PDF, CSV)
- [ ] Pruebas escritas y pasando (>95% cobertura)
- [ ] Paquete instalable con pip

## Dependencias

- S-001: Fundación (modelos, autenticación)
- S-002: Chat de IA (para consultas de insights)
- S-007: CRM (comparte patrones de rastreo de visitantes)

## Reusabilidad

Este paquete está diseñado para funcionar con cualquier negocio:
- Reemplazar "Competidor" con terminología apropiada de la industria
- Parámetros de rastreo configurables
- Servicios de búsqueda de IP conectables
- Reglas de alerta personalizables
- Motor de insights independiente de la industria

## Notas

- Considerar IP2Location o MaxMind para geolocalización
- Limitar búsquedas de IP para gestionar costos de API
- Procesamiento por lotes de generación de insights (cron diario)
- Considerar monitoreo de API de redes sociales de competidores (futuro)
- Análisis de app móvil de competidores (mejora futura)

## Proceso de Desarrollo

**Antes de implementar esta historia**, revisar y seguir el **Ciclo TDD de 23 Pasos** en:
- `CLAUDE.md` - Flujo de trabajo de desarrollo global
- `planning/TASK_BREAKDOWN.md` - Tareas específicas para esta historia

Las pruebas deben escribirse antes de la implementación. Se requiere >95% de cobertura.
