# S-007: CRM de Propietarios + Inteligencia

> **LECTURA OBLIGATORIA:** Antes de la implementación, revisar [ESTANDARES_CODIGO.md](../ESTANDARES_CODIGO.md) y [DECISIONES_ARQUITECTURA.md](../DECISIONES_ARQUITECTURA.md)

**Tipo de Historia:** Historia de Usuario
**Prioridad:** Media
**Época:** 5
**Estado:** PENDIENTE

## Historia de Usuario

**Como** miembro del personal de la clínica
**Quiero** tener perfiles detallados de los propietarios de mascotas con su historial y preferencias
**Para que** pueda proporcionar un servicio personalizado y marketing dirigido

**Como** dueño del negocio
**Quiero** entender el comportamiento y las tendencias de los clientes
**Para que** pueda tomar decisiones informadas sobre servicios e inventario

## Criterios de Aceptación

### Perfiles de Propietarios
- [ ] Información de contacto completa (teléfono, correo electrónico, dirección)
- [ ] Preferencias de comunicación e historial
- [ ] Todas las mascotas vinculadas al propietario
- [ ] Historial de citas
- [ ] Historial de compras
- [ ] Valor total de por vida calculado
- [ ] Notas y etiquetas para segmentación

### Inteligencia del Cliente
- [ ] Análisis de frecuencia de compra
- [ ] Seguimiento de productos preferidos
- [ ] Patrones de visita (estacional, regular, emergencia)
- [ ] Tasas de respuesta a comunicaciones
- [ ] Indicadores de riesgo de abandono

### Automatización de Marketing
- [ ] Segmentar clientes por criterios
- [ ] Mensajes automáticos de cumpleaños/aniversario
- [ ] Reactivación de clientes inactivos
- [ ] Anuncios de nuevos productos a segmentos relevantes
- [ ] Seguimiento de programa de lealtad

### Capacidades de IA
- [ ] La IA puede buscar y recuperar perfiles de propietarios
- [ ] La IA puede agregar notas y etiquetas
- [ ] La IA puede identificar clientes de alto valor
- [ ] La IA puede sugerir acciones de marketing
- [ ] La IA puede generar reportes

## Requisitos Técnicos

### Paquete: django-crm-lite

```python
# models.py

class OwnerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Contact info
    phone_primary = models.CharField(max_length=20, blank=True)
    phone_secondary = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    preferred_language = models.CharField(max_length=10, default='es')

    # Communication preferences
    contact_preference = models.CharField(max_length=20, default='whatsapp')
    marketing_opt_in = models.BooleanField(default=True)
    reminder_preference = models.CharField(max_length=20, default='24h')

    # Segmentation
    customer_type = models.CharField(max_length=50, blank=True)  # regular, vip, new, lapsed
    acquisition_source = models.CharField(max_length=100, blank=True)
    referral_source = models.ForeignKey('self', null=True, on_delete=models.SET_NULL)

    # Social
    instagram_handle = models.CharField(max_length=100, blank=True)
    facebook_url = models.URLField(blank=True)

    # Metadata
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class OwnerTag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#3B82F6')
    description = models.TextField(blank=True)


class OwnerProfileTag(models.Model):
    profile = models.ForeignKey(OwnerProfile, on_delete=models.CASCADE, related_name='tags')
    tag = models.ForeignKey(OwnerTag, on_delete=models.CASCADE)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    added_at = models.DateTimeField(auto_now_add=True)


class OwnerNote(models.Model):
    profile = models.ForeignKey(OwnerProfile, on_delete=models.CASCADE, related_name='notes_history')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    content = models.TextField()
    is_internal = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class CustomerMetrics(models.Model):
    """Calculated metrics, updated periodically"""
    profile = models.OneToOneField(OwnerProfile, on_delete=models.CASCADE)

    # Financial
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    order_count = models.IntegerField(default=0)

    # Engagement
    total_appointments = models.IntegerField(default=0)
    cancelled_appointments = models.IntegerField(default=0)
    no_show_count = models.IntegerField(default=0)
    last_visit_date = models.DateField(null=True)
    last_purchase_date = models.DateField(null=True)

    # Communication
    messages_sent = models.IntegerField(default=0)
    messages_responded = models.IntegerField(default=0)
    response_rate = models.FloatField(default=0)

    # Derived
    days_since_last_visit = models.IntegerField(default=0)
    churn_risk_score = models.FloatField(default=0)  # 0-1, higher = more likely to churn
    lifetime_value_estimate = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    updated_at = models.DateTimeField(auto_now=True)


class MarketingCampaign(models.Model):
    name = models.CharField(max_length=200)
    campaign_type = models.CharField(max_length=50)  # email, sms, whatsapp
    status = models.CharField(max_length=20, default='draft')

    # Targeting
    target_segment = models.JSONField(default=dict)  # Filters for who receives
    target_count = models.IntegerField(default=0)

    # Content
    subject = models.CharField(max_length=200, blank=True)
    body = models.TextField()

    # Scheduling
    scheduled_for = models.DateTimeField(null=True)
    sent_at = models.DateTimeField(null=True)

    # Results
    sent_count = models.IntegerField(default=0)
    delivered_count = models.IntegerField(default=0)
    opened_count = models.IntegerField(default=0)
    clicked_count = models.IntegerField(default=0)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class LoyaltyProgram(models.Model):
    profile = models.OneToOneField(OwnerProfile, on_delete=models.CASCADE)
    points_balance = models.IntegerField(default=0)
    tier = models.CharField(max_length=20, default='bronze')  # bronze, silver, gold, platinum
    points_earned_total = models.IntegerField(default=0)
    points_redeemed_total = models.IntegerField(default=0)


class LoyaltyTransaction(models.Model):
    loyalty = models.ForeignKey(LoyaltyProgram, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20)  # earn, redeem, expire
    points = models.IntegerField()
    description = models.CharField(max_length=200)
    related_order = models.ForeignKey('store.Order', null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
```

### Herramientas de IA (Época 5)

```python
CRM_TOOLS = [
    {
        "name": "get_owner_profile",
        "description": "Get detailed profile of a pet owner",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "search_owners",
        "description": "Search for owners by name, phone, email, or pet name",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "filters": {"type": "object"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "add_owner_note",
        "description": "Add a note to an owner's profile",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
                "note": {"type": "string"},
                "is_internal": {"type": "boolean", "default": True}
            },
            "required": ["user_id", "note"]
        }
    },
    {
        "name": "tag_owner",
        "description": "Add or remove tags from an owner profile",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
                "add_tags": {"type": "array", "items": {"type": "string"}},
                "remove_tags": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "get_customer_insights",
        "description": "Get analytics and insights about customers",
        "parameters": {
            "type": "object",
            "properties": {
                "insight_type": {
                    "type": "string",
                    "enum": ["top_customers", "at_risk", "new_customers", "lapsed", "high_value"]
                },
                "limit": {"type": "integer", "default": 10}
            },
            "required": ["insight_type"]
        }
    },
    {
        "name": "get_segment",
        "description": "Get list of customers matching criteria",
        "parameters": {
            "type": "object",
            "properties": {
                "filters": {
                    "type": "object",
                    "properties": {
                        "min_spent": {"type": "number"},
                        "days_since_visit": {"type": "integer"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "pet_species": {"type": "string"}
                    }
                }
            }
        }
    },
    {
        "name": "generate_report",
        "description": "Generate business reports",
        "parameters": {
            "type": "object",
            "properties": {
                "report_type": {
                    "type": "string",
                    "enum": ["revenue", "appointments", "products", "customers", "retention"]
                },
                "start_date": {"type": "string", "format": "date"},
                "end_date": {"type": "string", "format": "date"}
            },
            "required": ["report_type"]
        }
    }
]
```

## Ejemplo de Conversaciones con IA

### Búsqueda de Cliente
```
Dr. Pablo: Cuéntame sobre María García
IA: Aquí está el perfil de María García:

    👤 **María García**
    📱 998-123-4567 (Prefiere WhatsApp)
    📧 maria.garcia@email.com
    📍 Calle Coral 45, Puerto Morelos

    🐕 **Mascotas:** Max (Poodle, 5 años)

    💰 **Valor del Cliente:**
    • Total Gastado: $12,450 MXN
    • 8 órdenes, promedio $1,556 MXN
    • 15 citas (0 ausencias)
    • Cliente desde: Marzo 2023

    📊 **Actividad Reciente:**
    • Última visita: 15 Nov 2025 (Chequeo anual de Max)
    • Última compra: 15 Nov 2025 (Royal Canin)

    🏷️ Etiquetas: VIP, Regular, Dueño de Perro

    ¿Te gustaría ver más detalles?
```

### Clientes en Riesgo
```
Dr. Pablo: ¿A quiénes no hemos visto en un tiempo?
IA: Aquí están los clientes en riesgo de abandono:

    ⚠️ **Clientes en Riesgo** (sin visita en 90+ días)

    1. **Carlos Méndez** - Última visita hace 120 días
       Mascotas: Buddy (Labrador)
       Gastado: $8,200 MXN de por vida
       → Vacunación vence en 2 semanas

    2. **Sarah Johnson** - Última visita hace 95 días
       Mascotas: Mittens (Gato), Whiskers (Gato)
       Gastado: $5,400 MXN de por vida
       → Usualmente compra alimento mensualmente, sin orden en 45 días

    3. **Roberto Sánchez** - Última visita hace 92 días
       Mascotas: Thor (Pastor Alemán)
       Gastado: $15,800 MXN de por vida
       → Cliente VIP, debe hacerse seguimiento

    ¿Te gustaría que enviara mensajes de reactivación a alguno de ellos?
```

## Definición de Completado

- [ ] Perfiles de propietarios con información completa
- [ ] Métricas de clientes calculadas y actualizadas
- [ ] Sistema de etiquetas y notas funcionando
- [ ] Historial de compras y visitas agregado
- [ ] Puntuación de riesgo de abandono implementada
- [ ] La IA puede buscar y recuperar perfiles
- [ ] La IA puede generar reportes de negocio
- [ ] Se pueden crear campañas de marketing
- [ ] Seguimiento de puntos de lealtad (básico)
- [ ] Pruebas escritas y pasando (>95% cobertura)

## Dependencias

- S-001: Fundación + Núcleo de IA
- S-003: Perfiles de Mascotas
- S-004: Reserva de Citas
- S-005: Tienda de E-Commerce
- S-006: Comunicaciones Omnicanal

## Notas

- Las métricas deben recalcularse nocturnamente mediante trabajo cron
- Considerar cumplimiento GDPR/privacidad para marketing
- El enriquecimiento de redes sociales podría usar APIs o entrada manual
- El programa de lealtad es básico - podría expandirse en el futuro

## Proceso de Desarrollo

**Antes de implementar esta historia**, revisar y seguir el **Ciclo TDD de 23 Pasos** en:
- `CLAUDE.md` - Flujo de trabajo de desarrollo global
- `planning/TASK_BREAKDOWN.md` - Tareas específicas para esta historia

Las pruebas deben escribirse antes de la implementación. Se requiere >95% de cobertura.
