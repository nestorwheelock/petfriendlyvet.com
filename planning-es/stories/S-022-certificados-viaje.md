# S-022: Certificados de Viaje

> **LECTURA OBLIGATORIA:** Antes de la implementación, revisar [ESTANDARES_CODIGO.md](../ESTANDARES_CODIGO.md) y [DECISIONES_ARQUITECTURA.md](../DECISIONES_ARQUITECTURA.md)

**Tipo de Historia:** Historia de Usuario
**Prioridad:** Media
**Época:** 2 (con Mascotas)
**Estado:** PENDIENTE
**Módulo:** django-vet-clinic

## Historia de Usuario

**Como** dueño de mascota planeando viaje internacional
**Quiero** obtener certificados sanitarios adecuados para mi mascota
**Para** poder viajar sin problemas en aduanas/inmigración

**Como** veterinario
**Quiero** generar certificados sanitarios cumpliendo normativas
**Para** poder ayudar a clientes a viajar internacionalmente con sus mascotas

**Como** miembro del personal de la clínica
**Quiero** conocer los requisitos para cada destino
**Para** asegurar que las mascotas estén preparadas adecuadamente para viajar

## Criterios de Aceptación

### Base de Datos de Requisitos de Viaje
- [ ] Base de datos de requisitos por país de destino
- [ ] Vacunas requeridas por destino
- [ ] Requisitos de tiempo (ej. rabia 30 días antes)
- [ ] Requisitos de microchip
- [ ] Requisitos de tratamiento de parásitos
- [ ] Reglas de cuarentena
- [ ] Requisitos específicos de aerolíneas
- [ ] Actualizaciones regulares cuando cambien regulaciones

### Generación de Certificados Sanitarios
- [ ] Generación de PDF con formato oficial
- [ ] Soporte para certificados estilo USDA
- [ ] Formato de requisitos de Pasaporte de Mascota UE
- [ ] Código QR para verificación
- [ ] Múltiples idiomas (español, inglés)
- [ ] Capacidad de firma digital
- [ ] Seguimiento de expiración (usualmente 10 días para viaje)
- [ ] Membrete y marca de la clínica

### Flujo de Trabajo de Preparación de Viaje
- [ ] Cliente solicita certificado para destino
- [ ] El sistema muestra lista de requisitos
- [ ] Rastrear cumplimiento de cada requisito
- [ ] Veterinario verifica que se cumplan todos los requisitos
- [ ] Certificado generado y firmado
- [ ] Copia guardada en registros de mascota
- [ ] Entrega (impresión, correo electrónico, descarga)

### Recordatorios y Alertas
- [ ] Recordatorios de fecha de viaje próxima
- [ ] Advertencias de expiración de certificado
- [ ] Alertas de requisitos faltantes
- [ ] Recordatorios de tiempo de vacunación
- [ ] Programación de chequeo previo al viaje

### Integración
- [ ] Vincular a registros médicos de mascotas
- [ ] Verificación de vacunación desde registros
- [ ] Verificación de microchip
- [ ] Reserva de cita para examen de viaje
- [ ] Factura por servicios de certificado de viaje

## Requisitos Técnicos

### Modelos

```python
class TravelDestination(models.Model):
    """Country/region with travel requirements"""
    name = models.CharField(max_length=200)
    name_es = models.CharField(max_length=200)
    iso_code = models.CharField(max_length=3)  # ISO 3166-1 alpha-3

    # Requirements
    requirements = models.JSONField(default=dict)
    # {
    #     "rabies": {"required": true, "min_days_before": 30, "max_days_before": 365},
    #     "microchip": {"required": true, "iso_standard": "11784/11785"},
    #     "health_certificate": {"validity_days": 10},
    #     "parasite_treatment": {"required": true, "days_before": 5},
    #     "blood_tests": {"rabies_titer": {"required": false}},
    #     "quarantine": {"days": 0, "notes": "No quarantine for compliant pets"},
    # }

    # Species-specific
    species_requirements = models.JSONField(default=dict)
    # {"dog": {...}, "cat": {...}, "bird": {...}}

    # Banned breeds (if applicable)
    banned_breeds = models.JSONField(default=list)

    # Documents needed
    required_documents = models.JSONField(default=list)
    # ["health_certificate", "vaccination_record", "microchip_registration"]

    # Entry points
    entry_requirements = models.JSONField(default=dict)
    # Special requirements for specific ports of entry

    # Source & updates
    official_source_url = models.URLField(blank=True)
    last_verified = models.DateField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    notes = models.TextField(blank=True)
    notes_es = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class AirlineRequirement(models.Model):
    """Airline-specific pet travel requirements"""
    name = models.CharField(max_length=200)
    iata_code = models.CharField(max_length=3)

    # General policy
    allows_cabin = models.BooleanField(default=True)
    allows_cargo = models.BooleanField(default=True)
    max_weight_cabin_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Requirements
    requirements = models.JSONField(default=dict)
    # {
    #     "health_certificate_max_days": 10,
    #     "crate_requirements": "IATA compliant",
    #     "breed_restrictions": ["brachycephalic"],
    #     "temperature_restrictions": true,
    # }

    # Fees
    cabin_fee = models.JSONField(default=dict)
    # {"domestic": 125, "international": 200, "currency": "USD"}

    cargo_fee = models.JSONField(default=dict)

    # Booking
    booking_url = models.URLField(blank=True)
    booking_phone = models.CharField(max_length=50, blank=True)
    advance_notice_hours = models.IntegerField(default=48)

    notes = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    last_verified = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['name']


class TravelPlan(models.Model):
    """Pet travel plan and preparation tracking"""
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('preparing', 'In Preparation'),
        ('ready', 'Ready to Travel'),
        ('completed', 'Travel Completed'),
        ('cancelled', 'Cancelled'),
    ]

    # Who
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='travel_plans')
    pet = models.ForeignKey('vet_clinic.Pet', on_delete=models.CASCADE, related_name='travel_plans')

    # Where
    destination = models.ForeignKey(TravelDestination, on_delete=models.PROTECT)
    destination_address = models.TextField(blank=True)

    # When
    departure_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)

    # How
    airline = models.ForeignKey(AirlineRequirement, on_delete=models.SET_NULL, null=True, blank=True)
    travel_method = models.CharField(max_length=50, default='air')
    # air, land, sea

    cabin_or_cargo = models.CharField(max_length=20, blank=True)
    # cabin, cargo, checked

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')

    # Requirements tracking
    requirements_checklist = models.JSONField(default=dict)
    # {
    #     "rabies_vaccine": {"required": true, "completed": true, "date": "2025-11-15"},
    #     "microchip": {"required": true, "completed": true, "number": "123456789"},
    #     "health_exam": {"required": true, "completed": false, "due_date": "2025-12-18"},
    #     "certificate": {"required": true, "completed": false},
    # }

    # Related records
    health_certificate = models.ForeignKey(
        'HealthCertificate', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='travel_plans'
    )
    appointment = models.ForeignKey(
        'appointments.Appointment', on_delete=models.SET_NULL, null=True, blank=True
    )

    # Notes
    notes = models.TextField(blank=True)
    special_requirements = models.TextField(blank=True)

    # Staff
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='travel_plans_created'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-departure_date']


class HealthCertificate(models.Model):
    """International health certificate for travel"""
    CERTIFICATE_TYPES = [
        ('usda', 'USDA APHIS 7001'),
        ('eu', 'EU Pet Passport Style'),
        ('generic', 'Generic International'),
        ('domestic', 'Domestic Travel'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_review', 'Pending Vet Review'),
        ('signed', 'Signed'),
        ('delivered', 'Delivered to Client'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]

    # Certificate identification
    certificate_number = models.CharField(max_length=50, unique=True)
    certificate_type = models.CharField(max_length=20, choices=CERTIFICATE_TYPES)

    # Subject
    pet = models.ForeignKey('vet_clinic.Pet', on_delete=models.CASCADE, related_name='health_certificates')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='health_certificates')

    # Travel details
    destination = models.ForeignKey(TravelDestination, on_delete=models.PROTECT)
    departure_date = models.DateField()

    # Validity
    issue_date = models.DateField()
    expiry_date = models.DateField()

    # Examination
    examination_date = models.DateField()
    examining_vet = models.ForeignKey(
        'practice.StaffProfile', on_delete=models.PROTECT, related_name='certificates_issued'
    )

    # Health status
    health_status = models.TextField()
    # "The animal described above was examined and found to be healthy and
    # free from evidence of communicable disease..."

    # Verified requirements
    verified_requirements = models.JSONField(default=dict)
    # {
    #     "rabies_vaccine": {"verified": true, "date": "2025-11-15", "lot": "ABC123", "manufacturer": "Nobivac"},
    #     "microchip": {"verified": true, "number": "123456789012345", "location": "left shoulder"},
    #     "parasite_treatment": {"verified": true, "date": "2025-12-15", "product": "NexGard"},
    # }

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Signature
    signed_at = models.DateTimeField(null=True, blank=True)
    digital_signature = models.TextField(blank=True)  # Base64 signature image or digital signature

    # Documents
    pdf_file = models.FileField(upload_to='certificates/', null=True, blank=True)
    qr_code = models.ImageField(upload_to='certificates/qr/', null=True, blank=True)

    # Verification
    verification_code = models.CharField(max_length=20, unique=True)
    # Short code for QR/verification

    # Delivery
    delivered_at = models.DateTimeField(null=True, blank=True)
    delivery_method = models.CharField(max_length=20, blank=True)
    # email, print, pickup

    # Billing
    invoice = models.ForeignKey(
        'billing.Invoice', on_delete=models.SET_NULL, null=True, blank=True
    )

    # Notes
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-issue_date']

    def is_valid(self):
        from django.utils import timezone
        return self.status == 'signed' and self.expiry_date >= timezone.now().date()


class CertificateRequirement(models.Model):
    """Individual requirement verification for a certificate"""
    certificate = models.ForeignKey(
        HealthCertificate, on_delete=models.CASCADE, related_name='requirements'
    )

    REQUIREMENT_TYPES = [
        ('vaccination', 'Vaccination'),
        ('microchip', 'Microchip'),
        ('parasite', 'Parasite Treatment'),
        ('blood_test', 'Blood Test'),
        ('exam', 'Physical Examination'),
        ('other', 'Other'),
    ]

    requirement_type = models.CharField(max_length=20, choices=REQUIREMENT_TYPES)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Verification
    is_verified = models.BooleanField(default=False)
    verified_date = models.DateField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    # Details (varies by type)
    details = models.JSONField(default=dict)
    # Vaccination: {"vaccine": "Rabies", "date": "...", "lot": "...", "manufacturer": "..."}
    # Microchip: {"number": "...", "location": "...", "iso_compliant": true}
    # Blood test: {"test": "Rabies titer", "result": "...", "lab": "..."}

    # Related medical record
    medical_record = models.ForeignKey(
        'vet_clinic.MedicalRecord', on_delete=models.SET_NULL, null=True, blank=True
    )

    notes = models.TextField(blank=True)


class TravelReminder(models.Model):
    """Reminders for travel preparation"""
    travel_plan = models.ForeignKey(TravelPlan, on_delete=models.CASCADE, related_name='reminders')

    REMINDER_TYPES = [
        ('requirement', 'Requirement Due'),
        ('exam', 'Travel Exam'),
        ('certificate', 'Certificate Pickup'),
        ('departure', 'Departure'),
        ('expiry', 'Certificate Expiring'),
    ]

    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()

    due_date = models.DateField()

    # Notification
    sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    channel = models.CharField(max_length=20, blank=True)
    # email, sms, whatsapp

    created_at = models.DateTimeField(auto_now_add=True)
```

### Herramientas de IA

```python
TRAVEL_CERTIFICATE_TOOLS = [
    {
        "name": "check_travel_requirements",
        "description": "Get travel requirements for a destination country",
        "parameters": {
            "type": "object",
            "properties": {
                "destination": {"type": "string"},
                "species": {"type": "string"},
                "pet_id": {"type": "integer"},
                "travel_date": {"type": "string"}
            },
            "required": ["destination", "species"]
        }
    },
    {
        "name": "create_travel_plan",
        "description": "Create a travel preparation plan for a pet",
        "parameters": {
            "type": "object",
            "properties": {
                "pet_id": {"type": "integer"},
                "destination": {"type": "string"},
                "departure_date": {"type": "string"},
                "return_date": {"type": "string"},
                "airline": {"type": "string"}
            },
            "required": ["pet_id", "destination", "departure_date"]
        }
    },
    {
        "name": "get_travel_checklist",
        "description": "Get the current checklist status for a travel plan",
        "parameters": {
            "type": "object",
            "properties": {
                "travel_plan_id": {"type": "integer"}
            },
            "required": ["travel_plan_id"]
        }
    },
    {
        "name": "generate_health_certificate",
        "description": "Generate a health certificate for travel",
        "parameters": {
            "type": "object",
            "properties": {
                "pet_id": {"type": "integer"},
                "destination": {"type": "string"},
                "travel_date": {"type": "string"},
                "certificate_type": {"type": "string"}
            },
            "required": ["pet_id", "destination", "travel_date"]
        }
    },
    {
        "name": "verify_certificate_requirement",
        "description": "Verify a requirement for a health certificate",
        "parameters": {
            "type": "object",
            "properties": {
                "certificate_id": {"type": "integer"},
                "requirement_type": {"type": "string"},
                "details": {"type": "object"}
            },
            "required": ["certificate_id", "requirement_type"]
        }
    },
    {
        "name": "get_certificate_status",
        "description": "Check the status of a health certificate",
        "parameters": {
            "type": "object",
            "properties": {
                "certificate_id": {"type": "integer"}
            },
            "required": ["certificate_id"]
        }
    },
    {
        "name": "get_airline_requirements",
        "description": "Get pet travel requirements for a specific airline",
        "parameters": {
            "type": "object",
            "properties": {
                "airline": {"type": "string"},
                "pet_weight_kg": {"type": "number"},
                "species": {"type": "string"}
            },
            "required": ["airline"]
        }
    }
]
```

## Conversaciones de IA de Ejemplo

### Planear Viaje Internacional
```
Dueño: Voy a llevar a Luna a Estados Unidos el próximo mes.
       ¿Qué necesito?

IA: ¡Genial! Puedo ayudarte a preparar a Luna para viajar a EE.UU.

    🇺🇸 REQUISITOS DE ENTRADA A EE.UU. PARA PERROS
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    ✅ REQUERIDO:
    • Vacuna de rabia válida (30+ días antes del viaje)
    • Certificado sanitario (dentro de 10 días de la salida)
    • Microchip (ISO 11784/11785 recomendado)

    Déjame revisar los registros de Luna...

    📋 ESTADO DE LUNA:
    ✅ Vacuna de rabia: Vigente (expira marzo 2026)
    ✅ Microchip: 941000024681234 (compatible con ISO)
    ⏳ Certificado sanitario: Necesita ser emitido

    ¿Cuándo exactamente viajas?

Dueño: 15 de enero, regreso 5 de febrero

IA: ¡Perfecto! He creado un plan de viaje para Luna.

    📅 CRONOGRAMA DE PREPARACIÓN DE VIAJE
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    ✅ Ya completado:
    • Vacuna de rabia (vigente)
    • Microchip registrado

    📆 5-10 de enero (ventana para examen sanitario):
    • Agendar examen sanitario de viaje
    • Recomiendo 8 de enero (7 días antes)

    📆 8 de enero (en cita):
    • Examen físico
    • Certificado sanitario emitido
    • Certificado válido hasta 18 de enero

    📆 15 de enero:
    • Salida a EE.UU.
    • Llevar: Certificado sanitario, registros de vacunación

    ¿Te gustaría que:
    1. Reserve la cita de examen de viaje para el 8 de enero
    2. Revise requisitos de aerolínea (¿cuál aerolínea?)
    3. Te envíe por correo la lista completa
```

## Referencia Rápida de Destinos Comunes

### Estados Unidos (desde México)
- Vacuna de rabia: Requerida (30+ días antes)
- Microchip: Recomendado (ISO)
- Certificado sanitario: Dentro de 10 días
- Requisitos CDC varían por estado

### Unión Europea (desde México)
- Microchip: Requerido (antes de vacuna de rabia)
- Vacuna de rabia: 21+ días antes
- Prueba de titulación de rabia: A menudo requerida (país no favorable)
- Formato de certificado sanitario UE
- Aval de SENASICA

### Canadá
- Vacuna de rabia: Requerida (30+ días antes)
- Certificado sanitario: Dentro de 10 días
- Sin cuarentena si cumple requisitos

## Definición de Terminado

- [ ] Modelo TravelDestination con base de datos de requisitos
- [ ] Modelo AirlineRequirement
- [ ] Modelo TravelPlan con seguimiento de lista de verificación
- [ ] Modelo HealthCertificate con generación de PDF
- [ ] Generación de código QR para verificación
- [ ] Punto de verificación de certificados
- [ ] Herramientas de IA para consulta de requisitos
- [ ] Sistema de recordatorios para cronograma de preparación
- [ ] Integración con registros médicos de mascotas
- [ ] Soporte multiidioma (español/inglés)
- [ ] Pruebas escritas y pasando (>95% cobertura)

## Dependencias

- S-003: Perfiles de Mascotas (registros de mascotas, vacunaciones)
- S-004: Citas (reserva de examen de viaje)
- S-012: Notificaciones (recordatorios)
- S-020: Facturación (tarifas de certificados)

## Notas

- Mantener base de datos de requisitos de destinos actualizada regularmente
- Considerar integración con SENASICA (México) para aval oficial
- Requisitos UE son complejos - puede necesitar flujo especializado
- Validez del certificado típicamente 10 días - el tiempo es crítico
- Guardar historial de verificación para cumplimiento
- Considerar asociaciones con aerolíneas para proceso simplificado

## Proceso de Desarrollo

**Antes de implementar esta historia**, revisar y seguir el **Ciclo TDD de 23 Pasos** en:
- `CLAUDE.md` - Flujo de trabajo de desarrollo global
- `planning/TASK_BREAKDOWN.md` - Tareas específicas para esta historia

Las pruebas deben escribirse antes de la implementación. Se requiere >95% de cobertura.
