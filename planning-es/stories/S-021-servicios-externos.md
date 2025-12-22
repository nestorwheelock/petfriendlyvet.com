# S-021: Servicios Externos (Estética, Hospedaje, etc.)

> **LECTURA OBLIGATORIA:** Antes de la implementación, revisar [ESTANDARES_CODIGO.md](../ESTANDARES_CODIGO.md) y [DECISIONES_ARQUITECTURA.md](../DECISIONES_ARQUITECTURA.md)

**Tipo de Historia:** Historia de Usuario
**Prioridad:** Media
**Época:** 2 (con Citas)
**Estado:** PENDIENTE
**Módulo:** django-vet-clinic + django-crm-lite

## Historia de Usuario

**Como** dueño de mascota
**Quiero** obtener recomendaciones de servicios de estética y hospedaje
**Para** poder encontrar proveedores confiables para las necesidades de mi mascota

**Como** miembro del personal de la clínica
**Quiero** rastrear referencias a proveedores de servicios externos
**Para** poder dar seguimiento al cuidado de mascotas y mantener relaciones con socios

**Como** dueño de clínica
**Quiero** gestionar relaciones con socios de servicios externos
**Para** poder ofrecer cuidado integral de mascotas a través de referencias confiables

## Nota Importante

**La estética y el hospedaje son SUBCONTRATADOS a negocios socios, no se realizan internamente.**

Esta historia cubre el rastreo de referencias y gestión de socios, NO la prestación directa de servicios.

## Criterios de Aceptación

### Directorio de Socios
- [ ] Mantener directorio de socios de servicios externos
- [ ] Categorías: Estética, Hospedaje, Guardería, Entrenamiento, etc.
- [ ] Información de contacto y ubicación del socio
- [ ] Servicios ofrecidos con precios (si se comparten)
- [ ] Horarios de operación y disponibilidad
- [ ] Calificaciones de calidad y notas
- [ ] Seguimiento de acuerdos con socios

### Seguimiento de Referencias
- [ ] Registrar cuando los clientes son referidos a socios
- [ ] Rastrear qué servicio fue recomendado
- [ ] Dar seguimiento a comentarios de clientes
- [ ] Seguimiento de comisiones/bonificaciones (si aplica)
- [ ] Reportes de volumen por socio

### Conveniencia del Cliente
- [ ] IA recomienda socios basándose en necesidades del cliente
- [ ] Proporcionar información de contacto del socio
- [ ] Opcional: Agendar en nombre del cliente (si el socio lo permite)
- [ ] Integración con registros de mascotas (anotar cuando la mascota está en hospedaje)

### Integración con Registro de Mascota
- [ ] Vincular referencias a perfiles de mascotas
- [ ] Anotar cuando la mascota está en hospedaje externo
- [ ] Documentación de entrega de medicamentos
- [ ] Instrucciones de cuidado especial para el socio

## Requisitos Técnicos

### Modelos

```python
class ExternalPartner(models.Model):
    """External service partner (grooming, boarding, etc.)"""
    PARTNER_TYPES = [
        ('grooming', 'Grooming'),
        ('boarding', 'Boarding'),
        ('daycare', 'Daycare'),
        ('training', 'Training'),
        ('walking', 'Dog Walking'),
        ('sitting', 'Pet Sitting'),
        ('transport', 'Pet Transport'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active Partner'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending Approval'),
    ]

    # Basic info
    name = models.CharField(max_length=200)
    partner_type = models.CharField(max_length=20, choices=PARTNER_TYPES)
    description = models.TextField(blank=True)

    # Contact
    contact_name = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=20)
    whatsapp = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)

    # Location
    address = models.TextField()
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    distance_km = models.FloatField(null=True, blank=True)  # From Pet-Friendly

    # Services
    services_offered = models.JSONField(default=list)
    # e.g., ["bath", "haircut", "nail_trim", "teeth_cleaning"]

    species_accepted = models.JSONField(default=list)
    # e.g., ["dog", "cat"]

    # Hours
    hours = models.JSONField(default=dict)
    # {"monday": {"open": "09:00", "close": "18:00"}, ...}

    # Pricing (if shared by partner)
    pricing = models.JSONField(default=dict, blank=True)
    # {"bath_small": 150, "bath_medium": 200, ...}

    # Quality tracking
    rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    # Internal rating 1-5

    total_referrals = models.IntegerField(default=0)
    positive_feedback = models.IntegerField(default=0)
    negative_feedback = models.IntegerField(default=0)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)  # Internal notes

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_referral_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_partner_type_display()})"


class PartnerAgreement(models.Model):
    """Business agreement with external partner"""
    AGREEMENT_TYPES = [
        ('informal', 'Informal Referral'),
        ('commission', 'Commission-Based'),
        ('discount', 'Client Discount'),
        ('mutual', 'Mutual Referral'),
    ]

    partner = models.ForeignKey(ExternalPartner, on_delete=models.CASCADE, related_name='agreements')

    agreement_type = models.CharField(max_length=20, choices=AGREEMENT_TYPES, default='informal')

    # Terms
    commission_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    # Commission Pet-Friendly receives per referral

    client_discount_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    # Discount clients get when referred

    terms_notes = models.TextField(blank=True)

    # Validity
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    # Documents
    contract_file = models.FileField(upload_to='partner_contracts/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ExternalReferral(models.Model):
    """Record of referral to external partner"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('contacted', 'Client Contacted Partner'),
        ('scheduled', 'Appointment Scheduled'),
        ('completed', 'Service Completed'),
        ('cancelled', 'Cancelled'),
        ('no_response', 'No Response'),
    ]

    # Who
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='external_referrals')
    pet = models.ForeignKey('vet_clinic.Pet', on_delete=models.CASCADE, related_name='external_referrals')
    partner = models.ForeignKey(ExternalPartner, on_delete=models.PROTECT, related_name='referrals')

    # What
    service_type = models.CharField(max_length=50)
    service_details = models.TextField(blank=True)

    # Special instructions
    special_instructions = models.TextField(blank=True)
    # e.g., "Luna is nervous with nail trims, please be patient"

    medications_to_handoff = models.JSONField(default=list)
    # Medications that need to be given during boarding

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Scheduling
    scheduled_date = models.DateField(null=True, blank=True)
    scheduled_time = models.TimeField(null=True, blank=True)

    # Follow-up
    follow_up_date = models.DateField(null=True, blank=True)
    follow_up_completed = models.BooleanField(default=False)

    # Feedback
    FEEDBACK_CHOICES = [
        ('positive', 'Positive'),
        ('neutral', 'Neutral'),
        ('negative', 'Negative'),
    ]
    client_feedback = models.CharField(max_length=20, choices=FEEDBACK_CHOICES, null=True, blank=True)
    feedback_notes = models.TextField(blank=True)

    # Commission (if applicable)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    commission_paid = models.BooleanField(default=False)
    commission_paid_date = models.DateField(null=True, blank=True)

    # Staff
    referred_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='referrals_made'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']


class BoardingStay(models.Model):
    """Track when pet is at external boarding"""
    pet = models.ForeignKey('vet_clinic.Pet', on_delete=models.CASCADE, related_name='boarding_stays')
    partner = models.ForeignKey(ExternalPartner, on_delete=models.PROTECT)
    referral = models.ForeignKey(ExternalReferral, on_delete=models.SET_NULL, null=True, blank=True)

    # Dates
    check_in_date = models.DateField()
    check_in_time = models.TimeField(null=True, blank=True)
    expected_checkout = models.DateField()
    actual_checkout = models.DateTimeField(null=True, blank=True)

    # Status
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('checked_in', 'Currently Boarding'),
        ('checked_out', 'Checked Out'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')

    # Care instructions
    feeding_instructions = models.TextField(blank=True)
    medication_schedule = models.JSONField(default=list)
    # [{"medication": "Apoquel", "dose": "1 tablet", "frequency": "daily", "time": "morning"}]

    special_needs = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=200, blank=True)
    emergency_phone = models.CharField(max_length=20, blank=True)

    # Handoff
    medications_provided = models.JSONField(default=list)
    belongings = models.JSONField(default=list)
    # ["bed", "favorite toy", "food (2kg bag)"]

    # Notes
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-check_in_date']
        verbose_name_plural = 'Boarding stays'
```

### Herramientas de IA

```python
EXTERNAL_SERVICES_TOOLS = [
    {
        "name": "find_partner",
        "description": "Find external service partners by type and availability",
        "parameters": {
            "type": "object",
            "properties": {
                "partner_type": {"type": "string", "enum": ["grooming", "boarding", "daycare", "training"]},
                "species": {"type": "string"},
                "date_needed": {"type": "string"},
                "service": {"type": "string"}
            },
            "required": ["partner_type"]
        }
    },
    {
        "name": "create_referral",
        "description": "Create a referral to an external partner",
        "parameters": {
            "type": "object",
            "properties": {
                "pet_id": {"type": "integer"},
                "partner_id": {"type": "integer"},
                "service_type": {"type": "string"},
                "special_instructions": {"type": "string"},
                "scheduled_date": {"type": "string"}
            },
            "required": ["pet_id", "partner_id", "service_type"]
        }
    },
    {
        "name": "record_boarding_stay",
        "description": "Record that a pet is staying at external boarding",
        "parameters": {
            "type": "object",
            "properties": {
                "pet_id": {"type": "integer"},
                "partner_id": {"type": "integer"},
                "check_in_date": {"type": "string"},
                "expected_checkout": {"type": "string"},
                "medications": {"type": "array"},
                "special_instructions": {"type": "string"}
            },
            "required": ["pet_id", "partner_id", "check_in_date", "expected_checkout"]
        }
    },
    {
        "name": "get_boarding_status",
        "description": "Check if a pet is currently at boarding",
        "parameters": {
            "type": "object",
            "properties": {
                "pet_id": {"type": "integer"}
            },
            "required": ["pet_id"]
        }
    },
    {
        "name": "record_referral_feedback",
        "description": "Record client feedback on external service",
        "parameters": {
            "type": "object",
            "properties": {
                "referral_id": {"type": "integer"},
                "feedback": {"type": "string", "enum": ["positive", "neutral", "negative"]},
                "notes": {"type": "string"}
            },
            "required": ["referral_id", "feedback"]
        }
    },
    {
        "name": "get_partner_stats",
        "description": "Get referral statistics for a partner",
        "parameters": {
            "type": "object",
            "properties": {
                "partner_id": {"type": "integer"},
                "date_range": {"type": "string"}
            },
            "required": ["partner_id"]
        }
    }
]
```

## Conversaciones de IA de Ejemplo

### Encontrar Servicios de Estética
```
Dueño: Luna necesita un baño y corte, ¿tienes recomendaciones?

IA: ¡Puedo recomendar algunas estéticas excelentes con las que trabajamos!

    Basado en las necesidades de Luna (perro mediano, pelaje estándar):

    🐕 ESTÉTICAS RECOMENDADAS
    ━━━━━━━━━━━━━━━━━━━━━━

    1. Pet Spa Puerto Morelos ⭐ 4.8
       📍 2 km de Pet-Friendly
       💰 Baño + corte: ~$350-450 MXN
       📞 998-555-1234
       ✨ Los clientes aman su manejo gentil

    2. Doggy Style Grooming ⭐ 4.6
       📍 3 km de distancia
       💰 Baño + corte: ~$300-400 MXN
       📞 998-555-5678
       ✨ Excelente para perros nerviosos

    ¿Te gustaría que:
    1. Te dé su información de contacto para llamar directamente
    2. Anote instrucciones especiales para Luna
    3. Agregue esto al registro de Luna para seguimiento

Dueño: ¿Puedes darme la información de Pet Spa y anotar que a Luna
       no le gusta el corte de uñas?

IA: ✅ Aquí está la información de Pet Spa Puerto Morelos:

    📞 Teléfono: 998-555-1234
    📱 WhatsApp: 998-555-1234
    📍 Av. Javier Rojo Gómez, Puerto Morelos
    🕐 Horario: Lun-Sáb 9am-6pm

    He anotado en la referencia de Luna:
    "Luna está nerviosa con el corte de uñas - por favor sean
    pacientes y gentiles, o omitir si está muy estresada."

    Cuando agendes, menciona que fuiste referido por
    Pet-Friendly para un 10% de descuento!

    ¿Quieres que programe un recordatorio para preguntar cómo fue?
```

### Coordinación de Hospedaje
```
Dueño: Voy a viajar la próxima semana. ¿Puedes recomendar
       dónde hospedar a Max?

IA: ¡Por supuesto! Déjame encontrar las mejores opciones para Max.

    Perfil de Max:
    • Golden Retriever, 5 años, 30kg
    • Medicamentos actuales: Apoquel (diario)
    • Sin dieta especial

    🏠 HOSPEDAJES RECOMENDADOS
    ━━━━━━━━━━━━━━━━━━━━━━━

    1. Happy Tails Boarding ⭐ 4.9
       📍 5 km de la clínica
       💰 $350/noche (incluye paseos)
       ✅ Puede administrar medicamentos
       📞 998-555-9999

    2. Casa Canina ⭐ 4.7
       📍 8 km de distancia
       💰 $280/noche
       ✅ Área exterior grande
       📞 998-555-8888

    Importante: Max toma Apoquel diariamente. Puedo preparar
    las dosis de medicamento para la estadía en hospedaje.

    ¿Cuáles son tus fechas de viaje?

Dueño: 26 de diciembre a 2 de enero

IA: ¡Perfecto! Para la estadía de 7 noches de Max (26 dic - 2 ene):

    📋 LISTA DE PREPARACIÓN PARA HOSPEDAJE
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    Preparación de medicamentos:
    ✅ 7 dosis de Apoquel preparadas
    ✅ Instrucciones: 1 tableta con el desayuno

    Recomiendo:
    1. Llamar a Happy Tails para reservar (998-555-9999)
    2. Recoger el paquete de medicamentos de Max del 24-25 dic
    3. Llevar su cama/manta para comodidad

    ¿Debería:
    1. Crear documento de entrega de medicamentos
    2. Programar recordatorio para 24 dic para recoger medicamentos
    3. Agendar chequeo post-hospedaje para 3 ene
```

### Vista del Personal - Gestión de Socios
```
Personal: Muéstrame las estadísticas de nuestros socios de estética

IA: 📊 Estadísticas de Socios de Estética (Últimos 90 Días)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    Pet Spa Puerto Morelos
    • Referencias: 28
    • Comentarios positivos: 26 (93%)
    • Comentarios negativos: 1 (4%)
    • Comisión ganada: $840 MXN

    Doggy Style Grooming
    • Referencias: 15
    • Comentarios positivos: 13 (87%)
    • Comentarios negativos: 0
    • Comisión ganada: $450 MXN

    Comentarios pendientes:
    • 5 referencias esperando comentarios de clientes

    📈 Tendencia: Referencias 20% arriba del trimestre pasado

    ¿Te gustaría:
    1. Ver comentarios detallados
    2. Actualizar información del socio
    3. Agregar un nuevo socio
```

## Definición de Terminado

- [ ] Modelo de socio con campos completos de directorio
- [ ] Seguimiento de acuerdos con socios
- [ ] Creación y seguimiento de referencias
- [ ] Seguimiento de estadías de hospedaje con entrega de medicamentos
- [ ] Herramientas de IA para recomendaciones de socios
- [ ] Recopilación de comentarios de clientes
- [ ] Seguimiento de comisiones (si aplica)
- [ ] Integración con registros de mascotas
- [ ] Vistas de gestión de socios para personal
- [ ] Pruebas escritas y pasando (>95% cobertura)

## Dependencias

- S-003: Perfiles de Mascotas (vincular referencias a mascotas)
- S-004: Sistema de citas (para agendar)
- S-007: CRM (perfiles de dueños)
- S-010: Farmacia (entrega de medicamentos)

## Notas

- Enfocarse en seguimiento de referencias, NO gestión directa de servicios
- Los socios gestionan su propia programación y operaciones
- El rol de Pet-Friendly es recomendación y coordinación
- La entrega de medicamentos es crítica para estadías de hospedaje
- El seguimiento de comisiones es opcional (depende de acuerdos)
- Considerar agregar portal de socios en versión futura

## Proceso de Desarrollo

**Antes de implementar esta historia**, revisar y seguir el **Ciclo TDD de 23 Pasos** en:
- `CLAUDE.md` - Flujo de trabajo de desarrollo global
- `planning/TASK_BREAKDOWN.md` - Tareas específicas para esta historia

Las pruebas deben escribirse antes de la implementación. Se requiere >95% de cobertura.
