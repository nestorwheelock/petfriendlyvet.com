# S-015: Servicios de Emergencia

> **LECTURA OBLIGATORIA:** Antes de la implementación, revisar [ESTANDARES_CODIGO.md](../ESTANDARES_CODIGO.md) y [DECISIONES_ARQUITECTURA.md](../DECISIONES_ARQUITECTURA.md)

**Tipo de Historia:** Historia de Usuario
**Prioridad:** Alta
**Época:** 4 (con Comunicaciones)
**Estado:** PENDIENTE
**Módulo:** django-omnichannel + django-appointments

## Historia de Usuario

**Como** dueño de mascota con una emergencia
**Quiero** comunicarme rápidamente con la clínica y obtener ayuda
**Para que** mi mascota reciba atención urgente cuando sea necesario

**Como** dueño de clínica
**Quiero** gestionar emergencias fuera de horario de manera eficiente
**Para que** pueda proporcionar atención de emergencia sin agotamiento

**Como** dueño de mascota
**Quiero** saber qué constituye una emergencia
**Para que** pueda tomar decisiones informadas sobre el cuidado de mi mascota

## Criterios de Aceptación

### Detección de Emergencias
- [ ] IA reconoce palabras clave de emergencia y urgencia
- [ ] Preguntas de triaje para evaluar gravedad
- [ ] Escalación automática de situaciones críticas
- [ ] Guía clara de emergencia vs. no emergencia
- [ ] Reconocimiento de emergencias específicas por especie

### Flujo de Contacto de Emergencia
- [ ] Botón/número de emergencia prominente en el sitio web
- [ ] Triaje de IA disponible 24/7
- [ ] Enrutamiento fuera de horario al veterinario de guardia
- [ ] Canal de emergencia de WhatsApp
- [ ] Devolución de llamada telefónica para emergencias críticas

### Triaje de Emergencias
- [ ] Cuestionario de evaluación de síntomas
- [ ] Clasificación de gravedad (Crítica/Urgente/Puede Esperar)
- [ ] Instrucciones de primeros auxilios mientras se traslada
- [ ] Subida de foto/video para evaluación
- [ ] Direcciones a la clínica basadas en ubicación

### Protocolo Fuera de Horario
- [ ] Gestión de horario de guardia
- [ ] Escalación a veterinario de respaldo
- [ ] Divulgación de tarifas de emergencia
- [ ] Apertura de clínica para emergencias
- [ ] Referencia a hospitales 24 horas

### Registros de Emergencia
- [ ] Registrar todos los contactos de emergencia
- [ ] Rastrear resultados
- [ ] Integrar con registros regulares
- [ ] Plantilla de notas de visita de emergencia
- [ ] Facturación para servicios fuera de horario

## Requisitos Técnicos

### Modelos

```python
class EmergencyContact(models.Model):
    """Intento de contacto de emergencia"""
    STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('triaging', 'Triaging'),
        ('escalated', 'Escalated to Staff'),
        ('resolved', 'Resolved'),
        ('referred', 'Referred Elsewhere'),
        ('no_response', 'No Response'),
    ]

    SEVERITY_CHOICES = [
        ('critical', 'Critical - Life Threatening'),
        ('urgent', 'Urgent - Needs Same-Day Care'),
        ('moderate', 'Moderate - Can Wait'),
        ('low', 'Low - Schedule Appointment'),
    ]

    # Contact info
    owner = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    pet = models.ForeignKey(
        'vet_clinic.Pet', on_delete=models.SET_NULL, null=True, blank=True
    )
    phone = models.CharField(max_length=20)
    channel = models.CharField(max_length=20)  # web, whatsapp, phone, sms

    # Emergency details
    reported_symptoms = models.TextField()
    pet_species = models.CharField(max_length=50)
    pet_age = models.CharField(max_length=50, blank=True)

    # Triage
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, null=True)
    triage_notes = models.TextField(blank=True)
    ai_assessment = models.JSONField(default=dict)

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='initiated')

    # Staff handling
    handled_by = models.ForeignKey(
        'practice.StaffProfile', on_delete=models.SET_NULL, null=True, blank=True
    )
    response_time_seconds = models.IntegerField(null=True)

    # Resolution
    resolution = models.TextField(blank=True)
    outcome = models.CharField(max_length=50, blank=True)
    # seen_at_clinic, referred, advice_given, false_alarm, etc.

    # Related records
    appointment = models.ForeignKey(
        'appointments.Appointment', on_delete=models.SET_NULL, null=True, blank=True
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    escalated_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']


class EmergencySymptom(models.Model):
    """Síntomas de emergencia conocidos para triaje"""
    keyword = models.CharField(max_length=100)
    keywords_es = models.JSONField(default=list)  # Spanish variations
    keywords_en = models.JSONField(default=list)  # English variations

    species = models.JSONField(default=list)  # ["dog", "cat", "all"]

    severity = models.CharField(max_length=20)
    description = models.TextField()

    # Triage questions
    follow_up_questions = models.JSONField(default=list)

    # First aid
    first_aid_instructions = models.TextField(blank=True)
    warning_signs = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)


class OnCallSchedule(models.Model):
    """Horario de guardia fuera de horario"""
    staff = models.ForeignKey('practice.StaffProfile', on_delete=models.CASCADE)
    date = models.DateField()

    start_time = models.TimeField()
    end_time = models.TimeField()

    # Contact methods in order
    contact_phone = models.CharField(max_length=20)
    backup_phone = models.CharField(max_length=20, blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    swap_requested = models.BooleanField(default=False)
    swap_with = models.ForeignKey(
        'practice.StaffProfile', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='swap_requests'
    )

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['date', 'start_time']
        unique_together = ['staff', 'date']


class EmergencyReferral(models.Model):
    """Hospitales de referencia de emergencia"""
    name = models.CharField(max_length=200)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    whatsapp = models.CharField(max_length=20, blank=True)

    # Location
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    distance_km = models.FloatField(null=True)  # From Pet-Friendly

    # Hours
    is_24_hours = models.BooleanField(default=False)
    hours = models.JSONField(default=dict)

    # Capabilities
    services = models.JSONField(default=list)
    # ["surgery", "xray", "blood_work", "oxygen", "icu"]

    species_treated = models.JSONField(default=list)

    # Status
    is_active = models.BooleanField(default=True)
    last_verified = models.DateField(null=True)

    notes = models.TextField(blank=True)


class EmergencyFirstAid(models.Model):
    """Instrucciones de primeros auxilios para emergencias comunes"""
    title = models.CharField(max_length=200)
    title_es = models.CharField(max_length=200)

    condition = models.CharField(max_length=100)
    species = models.JSONField(default=list)

    # Content
    description = models.TextField()
    description_es = models.TextField()

    steps = models.JSONField(default=list)
    # [{"step": 1, "instruction": "...", "instruction_es": "..."}, ...]

    warnings = models.JSONField(default=list)
    do_not = models.JSONField(default=list)  # What NOT to do

    # Media
    video_url = models.URLField(blank=True)
    images = models.JSONField(default=list)

    # Related
    related_symptoms = models.ManyToManyField(EmergencySymptom, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Herramientas de IA

```python
EMERGENCY_TOOLS = [
    {
        "name": "triage_emergency",
        "description": "Evaluar gravedad de emergencia basada en síntomas",
        "parameters": {
            "type": "object",
            "properties": {
                "symptoms": {"type": "string"},
                "species": {"type": "string"},
                "pet_age": {"type": "string"},
                "symptom_duration": {"type": "string"}
            },
            "required": ["symptoms", "species"]
        }
    },
    {
        "name": "escalate_to_oncall",
        "description": "Escalar emergencia al veterinario de guardia",
        "parameters": {
            "type": "object",
            "properties": {
                "emergency_contact_id": {"type": "integer"},
                "urgency": {"type": "string"},
                "callback_number": {"type": "string"}
            },
            "required": ["emergency_contact_id", "callback_number"]
        }
    },
    {
        "name": "get_first_aid_instructions",
        "description": "Obtener instrucciones de primeros auxilios para una condición",
        "parameters": {
            "type": "object",
            "properties": {
                "condition": {"type": "string"},
                "species": {"type": "string"}
            },
            "required": ["condition"]
        }
    },
    {
        "name": "get_oncall_status",
        "description": "Obtener veterinario de guardia actual",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_emergency_referrals",
        "description": "Obtener hospitales veterinarios de emergencia cercanos",
        "parameters": {
            "type": "object",
            "properties": {
                "is_24_hours": {"type": "boolean"},
                "species": {"type": "string"}
            }
        }
    },
    {
        "name": "create_emergency_appointment",
        "description": "Crear espacio de cita de emergencia",
        "parameters": {
            "type": "object",
            "properties": {
                "emergency_contact_id": {"type": "integer"},
                "time": {"type": "string"}
            },
            "required": ["emergency_contact_id"]
        }
    },
    {
        "name": "log_emergency_resolution",
        "description": "Registrar cómo se resolvió una emergencia",
        "parameters": {
            "type": "object",
            "properties": {
                "emergency_contact_id": {"type": "integer"},
                "outcome": {"type": "string"},
                "notes": {"type": "string"}
            },
            "required": ["emergency_contact_id", "outcome"]
        }
    }
]
```

## Ejemplos de Conversaciones con IA

### Detección de Emergencia Crítica
```
Dueño: ¡Mi perro no está respirando bien y se colapsó!

IA: 🚨 Esto suena como una emergencia crítica.

    Necesito respuestas rápidas para ayudarte:

    1. ¿Tu perro está consciente? (ojos abiertos, responde)
    2. ¿Hay alguna respiración?
    3. ¿De qué color están las encías? (rosa, blanco, azul)

Dueño: Apenas está consciente, la respiración es muy superficial,
       las encías se ven pálidas

IA: 🚨 CRÍTICO - Esto necesita atención veterinaria inmediata.

    📞 LLAMANDO AL DR. PABLO AHORA

    Mientras esperas (1-2 minutos para devolución de llamada):

    ✓ Mantén a tu perro acostado de lado
    ✓ Manténlo abrigado con una manta
    ✓ No le des comida ni agua
    ✓ Anota la hora en que comenzó

    Si no hay devolución de llamada en 2 minutos, llama directamente:
    📱 998-316-2438

    🏥 Hospital 24 horas más cercano (si no podemos contactarte):
    Hospital Veterinario Cancún
    Av. Tulum, Cancún (25 min en auto)
    📞 998-884-5678

    Mantén la calma - la ayuda está en camino.
```

### No Emergencia Fuera de Horario
```
Dueño (11:30 PM): Mi gato ha estado vomitando

IA: Entiendo tu preocupación. Déjame ayudar a evaluar
    la situación.

    Algunas preguntas rápidas:

    1. ¿Cuántas veces ha vomitado tu gato?
    2. ¿Cuándo comenzó?
    3. ¿Hay sangre en el vómito?
    4. ¿Tu gato todavía está comiendo/bebiendo?
    5. ¿Tu gato está actuando normal de lo contrario?

Dueño: Dos veces en la última hora. Sin sangre.
       Cenó normalmente. Parece cansado ahora.

IA: Basado en lo que has descrito, esto parece ser
    una preocupación moderada - no inmediatamente peligrosa,
    pero debe ser monitoreada.

    Mi Evaluación: ⚠️ MONITOREAR ESTA NOCHE

    Esto podría ser:
    • Comer demasiado rápido
    • Bola de pelo
    • Molestia estomacal leve

    ✅ Observar Esta Noche:
    • Retira comida por 2-3 horas
    • Ofrece pequeñas cantidades de agua
    • Monitorea más vómitos

    🚨 Ir a Emergencia Si:
    • El vómito continúa (>3 veces más)
    • Aparece sangre en el vómito
    • Se vuelve letárgico/no responde
    • El abdomen parece doloroso o hinchado

    📅 Recomendado: Programar revisión para mañana si
    el vómito continúa o no come en la mañana.

    ¿Te gustaría:
    1. Reservar primera cita disponible mañana
    2. Obtener devolución de llamada del Dr. Pablo esta noche
    3. Obtener direcciones al hospital 24 horas
```

### Gestión de Guardia (Personal)
```
Dr. Pablo: ¿Quién está de guardia este fin de semana?

IA: Horario de Guardia para este fin de semana:

    Viernes por la Noche (20 de dic):
    • 6 PM - 8 AM: Dr. Pablo (usted)
    • Respaldo: Dr. García (998-555-1234)

    Sábado (21 de dic):
    • 8 AM - 8 PM: Clínica Abierta (horario normal)
    • 8 PM - 8 AM: Dr. García

    Domingo (22 de dic):
    • Todo el día/noche: Dr. Pablo

    Estadísticas de Emergencia (Últimos 7 Días):
    • Total de contactos de emergencia: 4
    • Escalados al veterinario: 2
    • Vino a la clínica: 1
    • Referidos a otro lugar: 0
    • Tiempo de respuesta promedio: 3.2 minutos

    ¿Te gustaría:
    1. Intercambiar un turno
    2. Agregar cobertura de respaldo
    3. Ver emergencias recientes
```

## Base de Datos de Síntomas de Emergencia

### Crítico (Amenaza para la Vida)
- Dificultad para respirar / no respira
- Inconsciente / colapsado
- Sangrado severo
- Envenenamiento sospechado
- Convulsiones de más de 3 minutos
- Sospecha de hinchazón (abdomen distendido)
- Incapaz de orinar (especialmente gatos machos)
- Atropellado por auto / trauma mayor

### Urgente (Mismo Día)
- Vomitar sangre
- Diarrea con sangre
- Lesión ocular
- Cojera / incapaz de caminar
- No come más de 24 horas
- Dificultad para dar a luz
- Mordedura de serpiente/araña

### Moderado (Dentro de 24-48 Horas)
- Vómitos repetidos (sin sangre)
- Diarrea (sin sangre)
- Cojera leve
- Señales de infección de oído
- Heridas en la piel (sin sangrado abundante)

## Definición de Hecho

- [ ] Detección de palabras clave de emergencia en chat
- [ ] Flujo de cuestionario de triaje
- [ ] Clasificación de gravedad
- [ ] Auto-escalación para críticos
- [ ] Gestión de horario de guardia
- [ ] Base de datos de instrucciones de primeros auxilios
- [ ] Directorio de referencias de emergencia
- [ ] Integración de devolución de llamada telefónica
- [ ] Registro y seguimiento de emergencias
- [ ] Alertas al personal para emergencias
- [ ] Pruebas escritas y aprobadas (>95% cobertura)

## Dependencias

- S-002: Chat IA (detección de emergencias)
- S-006: Omnicanal (llamadas de escalación)
- S-008: Gestión de Práctica (horarios del personal)

## Notas

- Considerar integración con servicio de contestación
- Puede necesitar Twilio Voice para devoluciones de llamada automatizadas
- El contenido de primeros auxilios debe ser revisado por veterinario
- La información del hospital 24 horas debe verificarse regularmente
- Considerar botón de pánico en aplicación móvil (futuro)

## Proceso de Desarrollo

**Antes de implementar esta historia**, revisar y seguir el **Ciclo TDD de 23 Pasos** en:
- `CLAUDE.md` - Flujo de trabajo de desarrollo global
- `planning/TASK_BREAKDOWN.md` - Tareas específicas para esta historia

Las pruebas deben escribirse antes de la implementación. Se requiere >95% de cobertura.
