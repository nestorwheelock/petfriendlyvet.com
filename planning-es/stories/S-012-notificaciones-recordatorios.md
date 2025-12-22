# S-012: Notificaciones y Recordatorios

> **LECTURA OBLIGATORIA:** Antes de la implementación, revisar [ESTANDARES_CODIGO.md](../ESTANDARES_CODIGO.md) y [DECISIONES_ARQUITECTURA.md](../DECISIONES_ARQUITECTURA.md)

**Tipo de Historia:** Historia de Usuario
**Prioridad:** Alta
**Época:** 2 (con Citas)
**Estado:** PENDIENTE
**Módulo:** django-omnichannel

## Historia de Usuario

**Como** dueño de mascota
**Quiero** recibir recordatorios oportunos sobre el cuidado de mi mascota
**Para que** nunca pierda citas importantes o cuidado preventivo

**Como** dueño de clínica
**Quiero** enviar recordatorios automáticamente a clientes
**Para que** reduzca ausencias y asegure que las mascotas reciban cuidado oportuno

**Como** dueño de mascota
**Quiero** elegir cómo recibo notificaciones
**Para que** obtenga información a través de mis canales preferidos

## Criterios de Aceptación

### Tipos de Recordatorios
- [ ] Recordatorios de citas (24h, 2h antes)
- [ ] Recordatorios de vacunaciones vencidas
- [ ] Recordatorios de resurtido de medicamentos
- [ ] Recordatorios de cuidado de seguimiento
- [ ] Recordatorios de chequeo anual
- [ ] Recordatorios de cuidado preventivo (pulgas/garrapatas, gusano del corazón)
- [ ] Felicitaciones de cumpleaños (cumpleaños de mascota)
- [ ] Seguimiento post-visita

### Canales de Entrega
- [ ] Notificaciones por correo electrónico
- [ ] Mensajes de texto SMS
- [ ] Mensajes de WhatsApp
- [ ] Notificaciones push (futuro)
- [ ] Notificaciones en la aplicación

### Preferencias de Usuario
- [ ] Elegir canal(es) preferido(s)
- [ ] Establecer horarios de silencio (sin notificaciones)
- [ ] Optar por no recibir tipos específicos de recordatorios
- [ ] Preferencias de frecuencia
- [ ] Preferencia de idioma por canal
- [ ] Cancelar suscripción con un clic

### Seguimiento de Confirmación
- [ ] Rastrear estado de entrega (enviado, entregado, leído)
- [ ] Rastrear respuestas (confirmado, reprogramado, cancelado)
- [ ] Seguimiento automático si no hay respuesta
- [ ] Escalamiento a llamada telefónica para recordatorios críticos

### Programación Inteligente
- [ ] Tiempo de envío óptimo basado en comportamiento del usuario
- [ ] Conciencia de zona horaria
- [ ] Evitar recordatorios duplicados entre canales
- [ ] Agrupar recordatorios similares juntos
- [ ] Respetar límites de tasa específicos del canal

### Plantillas y Personalización
- [ ] Plantillas de mensajes personalizables
- [ ] Personalizado con nombres de mascota/propietario
- [ ] Soporte multilingüe
- [ ] Incluir enlaces relevantes (reprogramar, direcciones)
- [ ] Marca de la clínica

## Requisitos Técnicos

### Modelos

```python
class NotificationPreference(models.Model):
    """User notification preferences"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Channel preferences
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)
    whatsapp_enabled = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=True)

    # Primary channel
    primary_channel = models.CharField(max_length=20, default='whatsapp')

    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_start = models.TimeField(null=True, blank=True)  # e.g., 22:00
    quiet_end = models.TimeField(null=True, blank=True)  # e.g., 08:00
    timezone = models.CharField(max_length=50, default='America/Cancun')

    # Reminder types (opt-out list)
    disabled_reminder_types = models.JSONField(default=list)
    # ["birthday", "marketing", ...]

    # Language
    preferred_language = models.CharField(max_length=10, default='es')

    updated_at = models.DateTimeField(auto_now=True)


class ReminderType(models.Model):
    """Types of reminders the system can send"""
    code = models.CharField(max_length=50, unique=True)
    # appointment_24h, vaccination_due, refill_reminder, etc.

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # Timing
    default_advance_days = models.IntegerField(default=0)
    default_advance_hours = models.IntegerField(default=0)

    # Priority
    priority = models.CharField(max_length=20, default='normal')
    # critical, high, normal, low
    is_transactional = models.BooleanField(default=True)
    # Transactional = always send, Marketing = respect opt-out

    # Escalation
    requires_confirmation = models.BooleanField(default=False)
    escalation_enabled = models.BooleanField(default=False)
    escalation_hours = models.IntegerField(default=4)  # Hours before escalating

    # Status
    is_active = models.BooleanField(default=True)


class NotificationTemplate(models.Model):
    """Message templates for notifications"""
    reminder_type = models.ForeignKey(ReminderType, on_delete=models.CASCADE)
    channel = models.CharField(max_length=20)  # email, sms, whatsapp
    language = models.CharField(max_length=10, default='es')

    # Content
    subject = models.CharField(max_length=200, blank=True)  # For email
    body = models.TextField()
    # Supports variables: {{pet_name}}, {{owner_name}}, {{appointment_date}}, etc.

    # For WhatsApp templates
    whatsapp_template_name = models.CharField(max_length=100, blank=True)
    whatsapp_template_id = models.CharField(max_length=100, blank=True)

    # Actions
    include_confirm_button = models.BooleanField(default=False)
    include_reschedule_link = models.BooleanField(default=False)
    include_cancel_link = models.BooleanField(default=False)
    include_directions_link = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['reminder_type', 'channel', 'language']


class ScheduledReminder(models.Model):
    """Reminders scheduled to be sent"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    # References
    reminder_type = models.ForeignKey(ReminderType, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pet = models.ForeignKey(
        'vet_clinic.Pet', on_delete=models.CASCADE, null=True, blank=True
    )

    # Related objects (polymorphic reference)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    object_id = models.PositiveIntegerField(null=True)
    related_object = GenericForeignKey('content_type', 'object_id')
    # Could be Appointment, Vaccination, Prescription, etc.

    # Scheduling
    scheduled_for = models.DateTimeField()
    channel = models.CharField(max_length=20)

    # Content (pre-rendered)
    subject = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    language = models.CharField(max_length=10)

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)

    # External IDs for tracking
    external_id = models.CharField(max_length=100, blank=True)
    # Message ID from Twilio, SendGrid, etc.

    # Retry tracking
    attempt_count = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    next_retry_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['scheduled_for']
        indexes = [
            models.Index(fields=['status', 'scheduled_for']),
            models.Index(fields=['user', 'status']),
        ]


class ReminderResponse(models.Model):
    """Responses to reminders that require confirmation"""
    RESPONSE_TYPES = [
        ('confirmed', 'Confirmed'),
        ('rescheduled', 'Rescheduled'),
        ('cancelled', 'Cancelled'),
        ('no_response', 'No Response'),
    ]

    reminder = models.ForeignKey(ScheduledReminder, on_delete=models.CASCADE)
    response_type = models.CharField(max_length=20, choices=RESPONSE_TYPES)
    response_text = models.TextField(blank=True)  # If they replied with text
    response_channel = models.CharField(max_length=20)

    # For rescheduled
    new_datetime = models.DateTimeField(null=True, blank=True)

    received_at = models.DateTimeField(auto_now_add=True)


class ReminderEscalation(models.Model):
    """Escalation when reminder not responded to"""
    ESCALATION_TYPES = [
        ('retry_same', 'Retry Same Channel'),
        ('try_alternate', 'Try Alternate Channel'),
        ('phone_call', 'Phone Call Required'),
        ('staff_alert', 'Alert Staff'),
    ]

    reminder = models.ForeignKey(ScheduledReminder, on_delete=models.CASCADE)
    escalation_type = models.CharField(max_length=20, choices=ESCALATION_TYPES)
    escalated_at = models.DateTimeField(auto_now_add=True)

    # Result
    result = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    handled_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    handled_at = models.DateTimeField(null=True, blank=True)


class VaccinationReminder(models.Model):
    """Specific tracking for vaccination due reminders"""
    pet = models.ForeignKey('vet_clinic.Pet', on_delete=models.CASCADE)
    vaccination_type = models.CharField(max_length=100)

    # Due date calculation
    last_vaccination_date = models.DateField(null=True)
    due_date = models.DateField()
    grace_period_days = models.IntegerField(default=14)
    overdue_date = models.DateField()

    # Reminder schedule
    reminder_30_days = models.ForeignKey(
        ScheduledReminder, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+'
    )
    reminder_7_days = models.ForeignKey(
        ScheduledReminder, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+'
    )
    reminder_due = models.ForeignKey(
        ScheduledReminder, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+'
    )
    reminder_overdue = models.ForeignKey(
        ScheduledReminder, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+'
    )

    # Status
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    appointment = models.ForeignKey(
        'appointments.Appointment', on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ['due_date']
```

### Herramientas de IA

```python
NOTIFICATION_TOOLS = [
    {
        "name": "get_notification_preferences",
        "description": "Get user's notification preferences",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"}
            }
        }
    },
    {
        "name": "update_notification_preferences",
        "description": "Update user's notification preferences",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
                "email_enabled": {"type": "boolean"},
                "sms_enabled": {"type": "boolean"},
                "whatsapp_enabled": {"type": "boolean"},
                "primary_channel": {"type": "string"},
                "quiet_hours_enabled": {"type": "boolean"},
                "quiet_start": {"type": "string"},
                "quiet_end": {"type": "string"}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "get_upcoming_reminders",
        "description": "Get upcoming scheduled reminders for a user",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
                "days_ahead": {"type": "integer", "default": 30}
            }
        }
    },
    {
        "name": "get_vaccination_schedule",
        "description": "Get vaccination due dates for a pet",
        "parameters": {
            "type": "object",
            "properties": {
                "pet_id": {"type": "integer"}
            },
            "required": ["pet_id"]
        }
    },
    {
        "name": "send_reminder_now",
        "description": "Send an immediate reminder (staff only)",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
                "reminder_type": {"type": "string"},
                "message": {"type": "string"},
                "channel": {"type": "string"}
            },
            "required": ["user_id", "reminder_type", "message"]
        }
    },
    {
        "name": "get_unconfirmed_appointments",
        "description": "Get appointments awaiting confirmation",
        "parameters": {
            "type": "object",
            "properties": {
                "date_range": {"type": "string"}
            }
        }
    },
    {
        "name": "escalate_reminder",
        "description": "Escalate an unresponded reminder",
        "parameters": {
            "type": "object",
            "properties": {
                "reminder_id": {"type": "integer"},
                "escalation_type": {"type": "string"}
            },
            "required": ["reminder_id", "escalation_type"]
        }
    }
]
```

## Ejemplo de Conversaciones con IA

### Configurar Preferencias (Cliente)
```
Dueño: No quiero mensajes de texto, solo WhatsApp

IA: Actualizaré tus preferencias de notificación.

    Configuración actual para María García:

    ✓ WhatsApp: Habilitado (Principal)
    ✗ SMS: Deshabilitado
    ✓ Correo: Habilitado
    ✗ Horario Silencio: No configurado

    Recibirás recordatorios a través de WhatsApp para:
    • Recordatorios de citas
    • Fechas de vacunación vencidas
    • Resurtidos de recetas
    • Cuidado de seguimiento

    ¿Hay algo más que te gustaría ajustar?

Dueño: En realidad, sin notificaciones después de las 9pm

IA: ¡Actualizado! He configurado horario silencio de 9:00 PM a 8:00 AM.

    Durante el horario silencio, retendremos notificaciones
    no urgentes y las enviaremos por la mañana.

    Las notificaciones de emergencia (como problemas urgentes
    de recetas) seguirán llegando inmediatamente.
```

### Recordatorio de Vacunación
```
IA (WhatsApp): ¡Hola María! 🐕

    La vacuna antirrábica de Luna vence en 30 días
    (15 de enero de 2026).

    ¿Te gustaría programar su cita ahora?

    [Reservar Cita] [Recordar Después] [Ya Programada]

Dueño: Reservar Cita

IA: Puedo ayudarte a reservar la cita de vacunación de Luna.

    Horarios disponibles para vacunación antirrábica:
    • Lun 13 Ene: 10:00 AM, 2:00 PM, 4:00 PM
    • Mar 14 Ene: 9:00 AM, 11:00 AM, 3:00 PM
    • Mié 15 Ene: 10:00 AM, 1:00 PM

    ¿Cuál funciona mejor para ti?
```

### Flujo de Confirmación de Cita
```
IA (WhatsApp, 24 horas antes):
    Recordatorio de cita 📅

    Mañana tienes cita en Pet-Friendly:

    Mascota: Luna
    Servicio: Vacunación antirrábica
    Fecha: Miércoles, 15 de enero
    Hora: 10:00 AM

    [Confirmar] [Reprogramar] [Cancelar]

--- Sin respuesta después de 4 horas ---

IA (SMS respaldo):
    Pet-Friendly: Cita mañana 10AM para Luna.
    Confirma respondiendo SI o llama 998-316-2438

--- Aún sin respuesta después de 2 horas más ---

IA → Alerta de Personal:
    ⚠️ Cita sin confirmar que requiere atención

    Propietario: María García
    Mascota: Luna
    Cita: Mañana 10:00 AM
    Recordatorios enviados: WhatsApp (no leído), SMS (entregado)

    Acción necesaria: Se recomienda llamada telefónica

    [Marcar Confirmada] [Cancelar Cita] [Llamar Ahora]
```

## Configuración de Programación de Recordatorios

### Temporización de Recordatorios Predeterminados

| Tipo de Recordatorio | Temporización | Canales |
|---------------------|--------------|---------|
| Cita | 24h, 2h antes | WhatsApp, SMS, Correo |
| Vacunación Vencida | 30 días, 7 días, fecha vencida, atrasado | WhatsApp, Correo |
| Recordatorio de Resurtido | 7 días antes de vacío | WhatsApp |
| Chequeo Anual | 11 meses después del último | Correo |
| Seguimiento | Según instrucciones del veterinario | WhatsApp |
| Cumpleaños | Día de | WhatsApp |

### Lógica de Escalamiento

```
Confirmación de Cita:
├── T-24h: Enviar recordatorio (canal principal)
│   └── Si no hay respuesta después de 4h:
│       ├── T-20h: Reintentar en canal alternativo
│       │   └── Si no hay respuesta después de 4h:
│       │       ├── T-16h: Alertar al personal para llamada telefónica
│       │       └── Si es crítico: Llamada automática con IVR
└── T-2h: Recordatorio final (siempre enviar)
```

## Definición de Completado

- [ ] Modelo NotificationPreference e interfaz de usuario
- [ ] Configuración de ReminderType
- [ ] Sistema de plantillas con variables
- [ ] Entrega multicanal (Correo, SMS, WhatsApp)
- [ ] Procesamiento de recordatorios programados (Celery)
- [ ] Seguimiento de confirmación y respuestas
- [ ] Flujo de trabajo de escalamiento
- [ ] Automatización de recordatorio de vacunación
- [ ] Respeto de horario silencio
- [ ] Funcionalidad de cancelar suscripción
- [ ] Webhooks de estado de entrega
- [ ] Pruebas escritas y pasando (>95% cobertura)

## Dependencias

- S-001: Fundación (modelo de usuario)
- S-003: Perfiles de Mascotas (referencia de mascota)
- S-004: Citas (recordatorios de citas)
- S-006: Omnicanal (canales de entrega)
- S-010: Farmacia (recordatorios de resurtido)

## Notas

- WhatsApp Business API requiere plantillas pre-aprobadas
- SMS cuesta por mensaje - considerar agrupación
- Celery Beat para procesamiento de recordatorios programados
- Considerar casos límite de zona horaria
- Requisitos de GDPR/consentimiento para mensajes de marketing

## Proceso de Desarrollo

**Antes de implementar esta historia**, revisar y seguir el **Ciclo TDD de 23 Pasos** en:
- `CLAUDE.md` - Flujo de trabajo de desarrollo global
- `planning/TASK_BREAKDOWN.md` - Tareas específicas para esta historia

Las pruebas deben escribirse antes de la implementación. Se requiere >95% de cobertura.
